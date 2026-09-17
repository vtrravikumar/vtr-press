"""macOS-native OCR adapter using Apple's Vision framework via PyObjC."""

from __future__ import annotations

from pathlib import Path

from .ocr import OCRConfig


class MacOSVisionOCR:
    """Run Apple's Vision OCR with one reusable recognition request.

    The request is initialized lazily on the first page and then reused for
    every subsequent image. When the same adapter instance is shared by the
    CLI, it is also reused across every PDF in a multi-document run.
    """

    def __init__(self, config: OCRConfig | None = None):
        self.config = config or OCRConfig()
        if self.config.language not in {"eng", "en", "en-US"}:
            raise ValueError(
                "MacOSVisionOCR currently supports English only; "
                f"received language={self.config.language!r}"
            )
        self._vision = None
        self._foundation = None
        self._objc = None
        self._request = None

    def _initialize_request(self) -> None:
        if self._request is not None:
            return

        try:
            import objc
            import Vision
            from Foundation import NSData
        except ImportError as exc:
            raise RuntimeError(
                "macOS Vision dependencies are required; install ocrmac "
                "with: python -m pip install ocrmac"
            ) from exc

        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(0)  # accurate
        request.setRecognitionLanguages_(["en-US"])

        self._vision = Vision
        self._foundation = NSData
        self._objc = objc
        self._request = request

    def _recognize(self, image: str | Path):
        image_path = Path(image)
        if not image_path.is_file():
            raise FileNotFoundError(image_path)

        self._initialize_request()
        image_data = image_path.read_bytes()

        with self._objc.autorelease_pool():
            data = self._foundation.dataWithBytes_length_(image_data, len(image_data))
            handler = self._vision.VNImageRequestHandler.alloc().initWithData_options_(
                data, None
            )
            result = handler.performRequests_error_([self._request], None)
            if isinstance(result, tuple):
                ok, error = result
            else:
                ok, error = bool(result), None
            if not ok or error is not None:
                raise RuntimeError(f"macOS Vision OCR failed: {error}")

            annotations = []
            for observation in self._request.results() or []:
                candidates = observation.topCandidates_(1)
                if not candidates:
                    continue
                item = candidates[0]
                bbox = observation.boundingBox()
                annotations.append(
                    (
                        str(item.string()),
                        float(item.confidence()),
                        [
                            float(bbox.origin.x),
                            float(bbox.origin.y),
                            float(bbox.size.width),
                            float(bbox.size.height),
                        ],
                    )
                )
            return annotations

    @staticmethod
    def _ordered(annotations):
        return sorted(annotations, key=lambda item: (-float(item[2][1]), float(item[2][0])))

    def ocr_image(self, image: str | Path) -> str:
        """Return text in top-to-bottom, left-to-right reading order."""
        ordered = self._ordered(self._recognize(image))
        return "\n".join(str(item[0]).strip() for item in ordered if str(item[0]).strip())

    def ocr_image_with_confidence(self, image: str | Path) -> tuple[str, float | None]:
        """Return OCR text and mean Vision confidence for non-empty annotations."""
        ordered = self._ordered(self._recognize(image))
        non_empty = [item for item in ordered if str(item[0]).strip()]
        text = "\n".join(str(item[0]).strip() for item in non_empty)
        if not non_empty:
            return text, None
        confidence = sum(float(item[1]) for item in non_empty) / len(non_empty)
        return text, confidence

    def version(self) -> str:
        """Return the OCR backend identifier."""
        return "macOS Vision"
