"""PDF page extraction for the VTR Press digitization pipeline.

PDF extraction is intentionally kept behind a small adapter boundary. VTR Press
must not require a particular PDF utility merely to represent the digitization
workflow; the concrete renderer can be selected by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Sequence


@dataclass(frozen=True)
class PDFRenderConfig:
    """Configuration for rendering PDF pages to raster images."""

    dpi: int = 300
    image_format: str = "png"
    extra_args: tuple[str, ...] = ()


class PdftoppmRenderer:
    """Render PDF pages using the locally installed ``pdftoppm`` utility."""

    def __init__(self, executable: str | None = None, config: PDFRenderConfig | None = None):
        self.executable = executable or shutil.which("pdftoppm") or "pdftoppm"
        self.config = config or PDFRenderConfig()

    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]:
        """Render all pages of *pdf* into *output_dir* and return their paths."""

        pdf_path = Path(pdf)
        if not pdf_path.is_file():
            raise FileNotFoundError(pdf_path)
        if self.config.dpi <= 0:
            raise ValueError("dpi must be greater than zero")

        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        prefix = destination / "page"

        command: list[str] = [
            self.executable,
            "-r",
            str(self.config.dpi),
            "-png" if self.config.image_format.lower() == "png" else f"-{self.config.image_format}",
            str(pdf_path),
            str(prefix),
            *self.config.extra_args,
        ]

        subprocess.run(command, check=True, capture_output=True, text=True)

        extension = self.config.image_format.lower()
        pages = sorted(destination.glob(f"page-*.{extension}"))
        if not pages:
            raise RuntimeError(f"PDF renderer produced no {extension} pages: {pdf_path}")
        return pages

    def version(self) -> str:
        """Return the installed ``pdftoppm`` version string."""

        result = subprocess.run(
            [self.executable, "-v"],
            check=False,
            capture_output=True,
            text=True,
        )
        return (result.stdout or result.stderr).splitlines()[0]
