"""Conservative visual analysis for scanned technical-document pages.

This module does not attempt to reconstruct tables or figures. It detects a few
strong visual signals and reports them as review metadata so a later
layout-aware extractor can build on the same page-level pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


@dataclass(frozen=True)
class VisualAnalysis:
    """Conservative visual signals detected from an unmodified source page."""

    table_likely: bool = False
    diagram_likely: bool = False
    figure_likely: bool = False
    confidence: float = 0.0
    reasons: tuple[str, ...] = ()


def _dark_mask(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    # A deliberately conservative threshold: this is a signal detector, not
    # OCR preprocessing, and therefore never changes the source image on disk.
    return gray.point(lambda value: 0 if value < 150 else 255, mode="1")


def _projection_runs(mask: Image.Image, horizontal: bool) -> int:
    width, height = mask.size
    pixels = mask.load()
    runs = 0
    if horizontal:
        for y in range(height):
            run = 0
            for x in range(width):
                if pixels[x, y] == 0:
                    run += 1
                else:
                    if run >= max(30, width // 5):
                        runs += 1
                    run = 0
            if run >= max(30, width // 5):
                runs += 1
    else:
        for x in range(width):
            run = 0
            for y in range(height):
                if pixels[x, y] == 0:
                    run += 1
                else:
                    if run >= max(30, height // 5):
                        runs += 1
                    run = 0
            if run >= max(30, height // 5):
                runs += 1
    return runs


def analyze_page(image: str | Path) -> VisualAnalysis:
    """Detect strong table/diagram/figure visual signals without extraction."""
    path = Path(image)
    if not path.is_file():
        raise FileNotFoundError(path)

    try:
        source = Image.open(path).convert("L")
    except Exception:
        # Test doubles and unsupported images should not make digitization fail.
        return VisualAnalysis(reasons=("visual-analysis-unavailable",))

    # Downsample for inexpensive, deterministic signal detection.
    source.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    mask = _dark_mask(source)
    width, height = mask.size
    if width < 40 or height < 40:
        return VisualAnalysis(reasons=("page-too-small",))

    horizontal = _projection_runs(mask, horizontal=True)
    vertical = _projection_runs(mask, horizontal=False)
    dark_ratio = 1.0 - (mask.getbbox() is None) * 0.0
    histogram = mask.histogram()
    dark_ratio = histogram[0] / max(width * height, 1)

    reasons: list[str] = []
    table = horizontal >= 3 and vertical >= 2
    if table:
        reasons.append("ruled-grid-signals")

    # A diagram often contains long strokes in one or both directions but not
    # the dense ruled grid expected of a table. This is intentionally only a
    # routing hint and never an extraction claim.
    diagram = not table and (horizontal + vertical >= 5) and dark_ratio < 0.35
    if diagram:
        reasons.append("line-structure-signals")

    # Pages with substantial non-white artwork and comparatively little line
    # structure are worth a visual check. This includes figures, plots and
    # raster illustrations without pretending to identify their semantics.
    figure = not table and not diagram and 0.02 <= dark_ratio <= 0.45
    if figure:
        reasons.append("non-text-visual-density")

    signals = sum((table, diagram, figure))
    confidence = min(0.50 + 0.10 * signals + 0.05 * min(horizontal + vertical, 4), 0.80)
    return VisualAnalysis(
        table_likely=table,
        diagram_likely=diagram,
        figure_likely=figure,
        confidence=confidence if signals else 0.0,
        reasons=tuple(reasons),
    )
