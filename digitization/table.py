"""Layout-aware table cell extraction for scanned pages."""

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
    confidence: float | None = None


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
        if not self.cells:
            return ()
        return tuple(
            tuple(
                next((cell.text for cell in self.cells if cell.row == row and cell.column == column), "")
                for column in range(self.column_count)
            )
            for row in range(self.row_count)
        )

    def confidence(self) -> float | None:
        """Return mean cell confidence when every non-empty cell has one."""
        non_empty = [cell for cell in self.cells if cell.text.strip()]
        if not non_empty or any(cell.confidence is None for cell in non_empty):
            return None
        return sum(cell.confidence for cell in non_empty if cell.confidence is not None) / len(non_empty)


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
    """Extract cells and optionally OCR them with per-cell confidence."""
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
                    left=grid.columns[column], top=grid.rows[row],
                    right=grid.columns[column + 1], bottom=grid.rows[row + 1],
                )
                crop = _crop_region(source_image, region, padding=padding)
                crop_path = destination / f"cell-r{row + 1:02d}-c{column + 1:02d}.png"
                crop.save(crop_path, format="PNG")

                confidence = None
                if ocr_engine is not None:
                    confidence_method = getattr(ocr_engine, "ocr_image_with_confidence", None)
                    if confidence_method is not None:
                        text, confidence = confidence_method(crop_path)
                    else:
                        text = ocr_engine.ocr_image(crop_path)
                else:
                    text = ""
                cells.append(TableCell(row, column, region, text.strip(), confidence))

    return ExtractedTable(tuple(cells))
