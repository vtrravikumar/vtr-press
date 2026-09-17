"""Conservative extraction of reviewable visual candidates from scanned pages.

This module deliberately extracts candidates, not publication-ready figures.
Every extracted image remains traceable to the source page and requires human
review before semantic use in a manuscript.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from .layout import VisualAnalysis, VisualRegion


def _ink_bounds(image: Image.Image) -> tuple[int, int, int, int] | None:
    """Return the bounding box of sufficiently dark pixels."""
    gray = ImageOps.grayscale(image)
    mask = gray.point(lambda value: 255 if value < 150 else 0, mode="L")
    return mask.getbbox()


def _expand_bounds(bounds: tuple[int, int, int, int], size: tuple[int, int], margin: int = 24) -> tuple[int, int, int, int]:
    left, top, right, bottom = bounds
    width, height = size
    return (
        max(left - margin, 0),
        max(top - margin, 0),
        min(right + margin, width),
        min(bottom + margin, height),
    )


def extract_visual_candidates(
    image: str | Path,
    analysis: VisualAnalysis,
    output_dir: str | Path,
    *,
    minimum_area_ratio: float = 0.03,
    maximum_area_ratio: float = 0.90,
) -> tuple[VisualRegion, ...]:
    """Extract conservative visual candidates and return their source regions.

    Table regions come directly from the detected grid. Diagram/figure
    candidates use the page's dark-ink bounds only when the resulting region is
    neither trivially small nor effectively the entire page. The source image
    is never modified.
    """
    source_path = Path(image)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as source:
        source_image = source.convert("RGB")
        width, height = source_image.size
        page_area = width * height
        regions: list[VisualRegion] = []

        if analysis.table_grid is not None:
            for index, region in enumerate(
                analysis.table_grid.cell_regions(analysis.confidence), start=1
            ):
                crop = source_image.crop((region.left, region.top, region.right, region.bottom))
                crop.save(destination / f"table-cell-{index:03d}.png", format="PNG")
            if analysis.regions:
                table = next((r for r in analysis.regions if r.kind == "table"), None)
                if table is not None:
                    regions.append(table)

        if not analysis.table_likely and (analysis.diagram_likely or analysis.figure_likely):
            bounds = _ink_bounds(source_image)
            if bounds is not None:
                candidate = _expand_bounds(bounds, source_image.size)
                left, top, right, bottom = candidate
                area_ratio = ((right - left) * (bottom - top)) / max(page_area, 1)
                if minimum_area_ratio <= area_ratio <= maximum_area_ratio:
                    kind = "diagram" if analysis.diagram_likely else "figure"
                    region = VisualRegion(kind, left, top, right, bottom, analysis.confidence)
                    crop = source_image.crop((left, top, right, bottom))
                    crop.save(destination / f"{kind}-candidate.png", format="PNG")
                    regions.append(region)

    return tuple(regions)
