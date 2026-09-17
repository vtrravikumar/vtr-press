"""macOS-native OCR adapter using Apple's Vision framework via ``ocrmac``."""

from __future__ import annotations

from pathlib import Path

from .ocr import OCRConfig


class MacOSVisionOCR:
    """Run Apple's Vision OCR through the pip-installable ``ocrmac`` package."""

    def __init__(self, config: OCRConfig | None = None):
        self.config = config or OCRConfig()
        if self.config.language not in {"eng", "en", "en-US"}:
            raise ValueError(
                "MacOSVisionOCR currently supports English only; "
                f"received language={self.config.language!r}"
            )

    def _engine(self):
        try:
            from ocrmac import ocrmac
        except ImportError as exc:
            raise RuntimeError(
                "ocrmac is required for the macos-vision OCR engine; "
                "install it with: python -m pip install ocrmac"
            ) from exc
        return ocrmac

    def _recognize(self, image: str | Path):
        image_path = Path(image)
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        ocrmac = self._engine()
        return ocrmac.OCR(
            str(image_path), recognition_level="accurate", language_preference=["en-US"]
        ).recognize()

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
        """Return the installed ocrmac version."""
        try:
            import importlib.metadata
            return importlib.metadata.version("ocrmac")
        except importlib.metadata.PackageNotFoundError as exc:
            raise RuntimeError(
                "ocrmac is required for the macos-vision OCR engine; "
                "install it with: python -m pip install ocrmac"
            ) from exc
