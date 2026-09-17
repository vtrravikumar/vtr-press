"""Layout-aware table cell extraction for scanned pages.

This module deliberately stops short of deciding whether OCR text is correct.
It turns a detected :class:`TableGrid` into cell images and optionally OCRs
those cells through the existing engine adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PIL import Image

from .layout import TableGrid, VisualRegion


class CellOCREngine(Protocol):
    """Minimal OCR contract required by table extraction."""

    def ocr_image(self, image: str | Path) -> str: ...


@dataclass(frozen=True)
class TableCell:
    """One table cell with its row/column position and OCR text."""

    row: int
    column: int
    region: VisualRegion
    text: str = ""


@dataclass(frozen=True)
class ExtractedTable:
    """Reviewable table extraction result; no Markdown is generated here."""

    cells: tuple[TableCell, ...] = ()

    @property
    def row_count(self) -> int:
        return max((cell.row for cell in self.cells), default=-1) + 1

    @property
    def column_count(self) -> int:
        return max((cell.column for cell in self.cells), default=-1) + 1

    def rows(self) -> tuple[tuple[str, ...], ...]:
        """Return OCR text arranged by detected row and column."""
        if not self.cells:
            return ()
        return tuple(
            tuple(
                next(
                    (cell.text for cell in self.cells if cell.row == row and cell.column == column),
                    "",
                )
                for column in range(self.column_count)
            )
            for row in range(self.row_count)
        )


def _crop_region(image: Image.Image, region: VisualRegion, padding: int = 2) -> Image.Image:
    """Crop a cell while excluding its grid lines where possible."""
    left = max(region.left + padding, 0)
    top = max(region.top + padding, 0)
    right = min(region.right - padding, image.width)
    bottom = min(region.bottom - padding, image.height)
    if right <= left or bottom <= top:
        raise ValueError("table cell region is too small after grid-line padding")
    return image.crop((left, top, right, bottom))


def extract_table_cells(
    image: str | Path,
    grid: TableGrid,
    output_dir: str | Path,
    *,
    ocr_engine: CellOCREngine | None = None,
    padding: int = 2,
) -> ExtractedTable:
    """Extract detected cells from an original source image.

    Cell crops are written as deterministic PNG assets. If ``ocr_engine`` is
    supplied, each crop is OCR'd independently. No source image is modified,
    and OCR output is kept as reviewable text rather than converted to a
    semantic Markdown table.
    """
    image_path = Path(image)
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path) as source:
        source_image = source.convert("RGB")
        cells: list[TableCell] = []
        for row in range(grid.row_count):
            for column in range(grid.column_count):
                region = VisualRegion(
                    kind="table-cell",
                    left=grid.columns[column],
                    top=grid.rows[row],
                    right=grid.columns[column + 1],
                    bottom=grid.rows[row + 1],
                )
                crop = _crop_region(source_image, region, padding=padding)
                crop_path = destination / f"cell-r{row + 1:02d}-c{column + 1:02d}.png"
                crop.save(crop_path, format="PNG")
                text = ocr_engine.ocr_image(crop_path).strip() if ocr_engine else ""
                cells.append(TableCell(row, column, region, text))

    return ExtractedTable(tuple(cells))
