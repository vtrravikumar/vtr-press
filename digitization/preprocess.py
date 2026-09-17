"""Image preprocessing adapters for scanned-document digitization.

Preprocessing is deliberately conservative. The default behavior is to copy the
source image unchanged; stronger transformations can be introduced behind the
same adapter without changing the OCR pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class PreprocessConfig:
    """Controls conservative preprocessing behavior."""

    copy_unchanged: bool = True


class PassthroughPreprocessor:
    """Preserve the raster page exactly as extracted from the source."""

    def __init__(self, config: PreprocessConfig | None = None):
        self.config = config or PreprocessConfig()
        if not self.config.copy_unchanged:
            raise ValueError("PassthroughPreprocessor requires copy_unchanged=True")

    def process(self, image: str | Path, output_dir: str | Path) -> Path:
        source = Path(image)
        if not source.is_file():
            raise FileNotFoundError(source)

        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / source.name
        shutil.copy2(source, target)
        return target
