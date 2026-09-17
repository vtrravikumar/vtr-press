"""Source-image preservation helpers for digitization output."""

from __future__ import annotations

import shutil
from pathlib import Path


def preserve_page_image(image: str | Path, output_dir: str | Path) -> Path:
    """Copy a rendered source page into a stable digitization asset directory."""

    source = Path(image)
    if not source.is_file():
        raise FileNotFoundError(source)

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / source.name
    shutil.copy2(source, target)
    return target
