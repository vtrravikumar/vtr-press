"""Image preprocessing adapters for scanned-document digitization.

Preprocessing is deliberately conservative and always writes a derived image;
the source raster is never modified. The pipeline can therefore retain the
original scan as the authoritative reference while experimenting with OCR-
friendly transformations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class PreprocessConfig:
    """Controls deterministic, OCR-oriented preprocessing."""

    grayscale: bool = True
    autocontrast: bool = True
    threshold: int | None = None

    def __post_init__(self) -> None:
        if self.threshold is not None and not 0 <= self.threshold <= 255:
            raise ValueError("threshold must be between 0 and 255")


class PassthroughPreprocessor:
    """Preserve the raster page exactly as extracted from the source."""

    def process(self, image: str | Path, output_dir: str | Path) -> Path:
        source = Path(image)
        if not source.is_file():
            raise FileNotFoundError(source)

        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / source.name
        shutil.copy2(source, target)
        return target


class PillowPreprocessor:
    """Apply conservative grayscale, contrast and threshold transformations.

    The implementation intentionally avoids deskew, cropping, denoising and
    other geometry-changing operations for now. Those transformations require
    validation against real documents before becoming part of the default
    digitization contract.
    """

    def __init__(self, config: PreprocessConfig | None = None):
        self.config = config or PreprocessConfig()

    def process(self, image: str | Path, output_dir: str | Path) -> Path:
        source = Path(image)
        if not source.is_file():
            raise FileNotFoundError(source)

        from PIL import Image, ImageOps

        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / f"{source.stem}.png"

        with Image.open(source) as original:
            image_obj = original.copy()

        if self.config.grayscale:
            image_obj = ImageOps.grayscale(image_obj)
        if self.config.autocontrast:
            image_obj = ImageOps.autocontrast(image_obj)
        if self.config.threshold is not None:
            if image_obj.mode != "L":
                image_obj = ImageOps.grayscale(image_obj)
            threshold = self.config.threshold
            image_obj = image_obj.point(lambda value: 255 if value >= threshold else 0)

        image_obj.save(target, format="PNG")
        image_obj.close()
        return target
