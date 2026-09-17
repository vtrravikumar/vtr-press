"""Conservative visual analysis for scanned technical-document pages.

This module detects strong visual signals and records candidate regions so a
later layout-aware extractor can work from explicit coordinates rather than
treating the whole page as one image. It deliberately does not OCR or rewrite
source content.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps


@dataclass(frozen=True)
class VisualRegion:
    """A candidate visual region in source-image pixel coordinates."""

    kind: str
    left: int
    top: int
    right: int
    bottom: int
    confidence: float = 0.0

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True)
class TableGrid:
    """Detected table grid boundaries in source-image pixel coordinates."""

    columns: tuple[int, ...] = ()
    rows: tuple[int, ...] = ()

    @property
    def column_count(self) -> int:
        return max(len(self.columns) - 1, 0)

    @property
    def row_count(self) -> int:
        return max(len(self.rows) - 1, 0)


@dataclass(frozen=True)
class VisualAnalysis:
    """Conservative visual signals detected from an unmodified source page."""

    table_likely: bool = False
    diagram_likely: bool = False
    figure_likely: bool = False
    confidence: float = 0.0
    reasons: tuple[str, ...] = ()
    regions: tuple[VisualRegion, ...] = ()
    table_grid: TableGrid | None = None


def _dark_mask(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    return gray.point(lambda value: 0 if value < 150 else 255, mode="1")


def _projection_runs(mask: Image.Image, horizontal: bool) -> list[tuple[int, int, int]]:
    """Return (position, start, end) for long dark runs."""
    width, height = mask.size
    pixels = mask.load()
    runs: list[tuple[int, int, int]] = []
    minimum = max(30, (width if horizontal else height) // 5)

    if horizontal:
        for y in range(height):
            start = None
            for x in range(width + 1):
                dark = x < width and pixels[x, y] == 0
                if dark and start is None:
                    start = x
                elif not dark and start is not None:
                    if x - start >= minimum:
                        runs.append((y, start, x))
                    start = None
    else:
        for x in range(width):
            start = None
            for y in range(height + 1):
                dark = y < height and pixels[x, y] == 0
                if dark and start is None:
                    start = y
                elif not dark and start is not None:
                    if y - start >= minimum:
                        runs.append((x, start, y))
                    start = None
    return runs


def _cluster_positions(positions: list[int], tolerance: int = 4) -> tuple[int, ...]:
    """Collapse thick/anti-aliased line positions into representative boundaries."""
    if not positions:
        return ()
    ordered = sorted(positions)
    clusters: list[list[int]] = [[ordered[0]]]
    for position in ordered[1:]:
        if position - clusters[-1][-1] <= tolerance:
            clusters[-1].append(position)
        else:
            clusters.append([position])
    return tuple(round(sum(cluster) / len(cluster)) for cluster in clusters)


def _grid_region(
    image_size: tuple[int, int],
    horizontal: list[tuple[int, int, int]],
    vertical: list[tuple[int, int, int]],
) -> tuple[VisualRegion, TableGrid] | None:
    """Build a conservative table region and its row/column boundaries."""
    if len(horizontal) < 3 or len(vertical) < 2:
        return None

    width, height = image_size
    left = min(run[0] for run in vertical)
    right = max(run[0] for run in vertical) + 1
    top = min(run[0] for run in horizontal)
    bottom = max(run[0] for run in horizontal) + 1

    if right - left < width // 5 or bottom - top < height // 20:
        return None

    columns = _cluster_positions([run[0] for run in vertical])
    rows = _cluster_positions([run[0] for run in horizontal])
    if len(columns) < 3 or len(rows) < 3:
        return None

    # Only treat the area as a grid when the detected boundaries span the
    # table region. This avoids turning isolated page rules into tables.
    if columns[0] > left + 8 or columns[-1] < right - 9:
        return None
    if rows[0] > top + 8 or rows[-1] < bottom - 9:
        return None

    confidence = min(
        0.60 + 0.04 * min(len(rows), 5) + 0.04 * min(len(columns), 4),
        0.90,
    )
    return VisualRegion("table", left, top, right, bottom, confidence), TableGrid(
        columns=columns,
        rows=rows,
    )


def analyze_page(image: str | Path) -> VisualAnalysis:
    """Detect strong visual signals and conservative candidate regions."""
    path = Path(image)
    if not path.is_file():
        raise FileNotFoundError(path)

    try:
        source = Image.open(path).convert("L")
    except Exception:
        return VisualAnalysis(reasons=("visual-analysis-unavailable",))

    original_size = source.size
    source.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    mask = _dark_mask(source)
    width, height = mask.size
    if width < 40 or height < 40:
        return VisualAnalysis(reasons=("page-too-small",))

    horizontal = _projection_runs(mask, horizontal=True)
    vertical = _projection_runs(mask, horizontal=False)
    histogram = mask.histogram()
    dark_ratio = histogram[0] / max(width * height, 1)

    reasons: list[str] = []
    regions: list[VisualRegion] = []
    table_grid: TableGrid | None = None

    table_result = _grid_region((width, height), horizontal, vertical)
    table = table_result is not None
    if table_result is not None:
        table_region, table_grid = table_result
        reasons.append("ruled-grid-signals")
        regions.append(table_region)

    diagram = not table and (len(horizontal) + len(vertical) >= 5) and dark_ratio < 0.35
    if diagram:
        reasons.append("line-structure-signals")

    figure = not table and not diagram and 0.02 <= dark_ratio <= 0.45
    if figure:
        reasons.append("non-text-visual-density")

    signals = sum((table, diagram, figure))
    confidence = min(0.50 + 0.10 * signals + 0.05 * min(len(horizontal) + len(vertical), 4), 0.80)

    if table_grid is not None and original_size != source.size:
        sx = original_size[0] / source.size[0]
        sy = original_size[1] / source.size[1]
        regions = [
            VisualRegion(
                kind=region.kind,
                left=round(region.left * sx),
                top=round(region.top * sy),
                right=round(region.right * sx),
                bottom=round(region.bottom * sy),
                confidence=region.confidence,
            )
            for region in regions
        ]
        table_grid = TableGrid(
            columns=tuple(round(value * sx) for value in table_grid.columns),
            rows=tuple(round(value * sy) for value in table_grid.rows),
        )

    return VisualAnalysis(
        table_likely=table,
        diagram_likely=diagram,
        figure_likely=figure,
        confidence=confidence if signals else 0.0,
        reasons=tuple(reasons),
        regions=tuple(regions),
        table_grid=table_grid,
    )
