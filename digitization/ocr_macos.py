"""macOS-native OCR adapter using Apple's Vision framework via ``ocrmac``.

This adapter exists so local macOS digitization does not require a separate
Tesseract installation. CI and non-macOS environments can continue to use the
Tesseract adapter.
"""

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

    def ocr_image(self, image: str | Path) -> str:
        """Return text in top-to-bottom, left-to-right reading order."""
        image_path = Path(image)
        if not image_path.is_file():
            raise FileNotFoundError(image_path)

        ocrmac = self._engine()
        annotations = ocrmac.OCR(
            str(image_path),
            recognition_level="accurate",
            language_preference=["en-US"],
        ).recognize()

        # ocrmac returns (text, confidence, normalized bounding-box) tuples.
        # Vision's normalized origin is at the lower-left, so sorting by
        # descending y and then ascending x gives a stable reading order.
        ordered = sorted(
            annotations,
            key=lambda item: (-float(item[2][1]), float(item[2][0])),
        )
        return "\n".join(str(item[0]).strip() for item in ordered if str(item[0]).strip())

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
