"""PDF page rendering through PyMuPDF.

This adapter is intended for local macOS use where installing Poppler is
undesirable. PyMuPDF is installed as a Python wheel and has no mandatory
external runtime dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PyMuPDFRenderConfig:
    """Configuration for rendering PDF pages through PyMuPDF."""

    dpi: int = 300
    image_format: str = "png"


class PyMuPDFRenderer:
    """Render PDF pages using the PyMuPDF Python package."""

    def __init__(self, config: PyMuPDFRenderConfig | None = None):
        self.config = config or PyMuPDFRenderConfig()

    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]:
        """Render all pages of *pdf* into *output_dir* and return their paths."""
        if self.config.dpi <= 0:
            raise ValueError("dpi must be greater than zero")
        if self.config.image_format.lower() != "png":
            raise ValueError("PyMuPDFRenderer currently supports only PNG output")

        pdf_path = Path(pdf)
        if not pdf_path.is_file():
            raise FileNotFoundError(pdf_path)

        try:
            import pymupdf
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF is required for the pymupdf renderer; "
                "install it with: python -m pip install pymupdf"
            ) from exc

        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)

        pages: list[Path] = []
        with pymupdf.open(pdf_path) as document:
            for number, page in enumerate(document, start=1):
                output = destination / f"page-{number}.png"
                pixmap = page.get_pixmap(dpi=self.config.dpi, alpha=False)
                pixmap.save(output)
                pages.append(output)

        if not pages:
            raise RuntimeError(f"PDF renderer produced no pages: {pdf_path}")
        return pages

    def version(self) -> str:
        """Return the installed PyMuPDF version."""
        try:
            import pymupdf
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF is required for the pymupdf renderer; "
                "install it with: python -m pip install pymupdf"
            ) from exc
        return getattr(pymupdf, "__version__", "unknown")
