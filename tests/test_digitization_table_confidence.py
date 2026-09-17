from pathlib import Path

from PIL import Image

from digitization.layout import TableGrid
from digitization.table import extract_table_cells
from digitization.table_markdown import to_markdown_table


class FakeConfidenceOCR:
    def __init__(self, confidence=0.92):
        self.confidence = confidence

    def ocr_image(self, image: str | Path) -> str:
        return "unused"

    def ocr_image_with_confidence(self, image: str | Path):
        return Path(image).stem.replace("-", " "), self.confidence


def test_table_confidence_is_aggregated_from_cells(tmp_path: Path):
    image = Image.new("RGB", (200, 200), "white")
    source = tmp_path / "source.png"
    image.save(source)
    table = extract_table_cells(
        source,
        TableGrid(columns=(0, 100, 200), rows=(0, 100, 200)),
        tmp_path / "cells",
        ocr_engine=FakeConfidenceOCR(0.92),
        padding=2,
    )
    assert table.confidence() == 0.92


def test_high_confidence_table_can_be_serialized(tmp_path: Path):
    image = Image.new("RGB", (200, 200), "white")
    source = tmp_path / "source.png"
    image.save(source)
    table = extract_table_cells(
        source,
        TableGrid(columns=(0, 100, 200), rows=(0, 100, 200)),
        tmp_path / "cells",
        ocr_engine=FakeConfidenceOCR(0.95),
        padding=2,
    )
    result = to_markdown_table(table, minimum_confidence=0.90, require_complete=True)
    assert result.publishable is True
    assert result.confidence == 0.95


def test_low_confidence_table_is_rejected(tmp_path: Path):
    image = Image.new("RGB", (200, 200), "white")
    source = tmp_path / "source.png"
    image.save(source)
    table = extract_table_cells(
        source,
        TableGrid(columns=(0, 100, 200), rows=(0, 100, 200)),
        tmp_path / "cells",
        ocr_engine=FakeConfidenceOCR(0.62),
        padding=2,
    )
    result = to_markdown_table(table, minimum_confidence=0.80)
    assert result.publishable is False
    assert result.reasons == ("table-ocr-confidence-low",)
