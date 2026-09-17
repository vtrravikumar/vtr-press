"""OCR engine adapters used by the VTR Press digitization pipeline.

The digitization layer is deliberately separate from the publishing pipeline.
Its job is to turn source material into a reviewable manuscript draft; it does
not parse or render the resulting Markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil
import subprocess


@dataclass(frozen=True)
class OCRConfig:
    """Configuration passed to an OCR engine.

    ``language`` and ``psm`` map directly to Tesseract concepts, but the
    surrounding pipeline depends only on this configuration object.
    """

    language: str = "eng"
    psm: int | None = None
    extra_args: tuple[str, ...] = field(default_factory=tuple)


# Conservative starting profiles for the document classes observed during
# real scanned-document validation. They are configuration presets only;
# structure classification belongs to a later digitization layer.
OCR_PROFILES: dict[str, OCRConfig] = {
    "prose": OCRConfig(psm=6),
    "layout": OCRConfig(psm=11),
    "code": OCRConfig(psm=6),
}


def get_ocr_profile(name: str) -> OCRConfig:
    """Return a named OCR profile configuration.

    The returned configuration is immutable. Unknown profile names fail early
    so a typo cannot silently select an unsuitable OCR strategy.
    """

    try:
        return OCR_PROFILES[name]
    except KeyError as exc:
        available = ", ".join(sorted(OCR_PROFILES))
        raise ValueError(f"unknown OCR profile {name!r}; choose from: {available}") from exc


class TesseractOCR:
    """Run the locally installed Tesseract executable on an image."""

    def __init__(self, executable: str | None = None, config: OCRConfig | None = None):
        self.executable = executable or shutil.which("tesseract") or "tesseract"
        self.config = config or OCRConfig()

    def ocr_image(self, image: str | Path) -> str:
        """Return OCR text for one image.

        Tesseract writes its text result to stdout when the output target is
        ``stdout``. Errors are surfaced unchanged so callers can distinguish
        an OCR failure from a successful, but potentially imperfect, result.
        """

        image_path = Path(image)
        if not image_path.is_file():
            raise FileNotFoundError(image_path)

        command: list[str] = [
            self.executable,
            str(image_path),
            "stdout",
            "-l",
            self.config.language,
        ]
        if self.config.psm is not None:
            command.extend(["--psm", str(self.config.psm)])
        command.extend(self.config.extra_args)

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def version(self) -> str:
        """Return the installed Tesseract version string."""

        result = subprocess.run(
            [self.executable, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return (result.stdout or result.stderr).splitlines()[0]
