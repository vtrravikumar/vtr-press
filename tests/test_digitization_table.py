from pathlib import Path

from PIL import Image, ImageDraw

from digitization.layout import TableGrid
from digitization.table import ExtractedTable, extract_table_cells


class FakeOCR:
    def __init__(self):
        self.images: list[str] = []

    def ocr_image(self, image: str | Path) -> str:
        self.images.append(Path(image).name)
        return f"text-{len(self.images)}"


def _make_table(path: Path) -> None:
    image = Image.new("RGB", (600, 400), "white")
    draw = ImageDraw.Draw(image)
    for y in (50, 150, 250, 350):
        draw.line((50, y, 550, y), fill="black", width=3)
    for x in (50, 300, 550):
        draw.line((x, 50, x, 350), fill="black", width=3)
    image.save(path)


def test_extract_table_cells_writes_deterministic_crops(tmp_path: Path):
    source = tmp_path / "page.png"
    output = tmp_path / "cells"
    _make_table(source)

    result = extract_table_cells(
        source,
        TableGrid(columns=(50, 300, 550), rows=(50, 150, 250, 350)),
        output,
    )

    assert isinstance(result, ExtractedTable)
    assert result.row_count == 3
    assert result.column_count == 2
    assert [path.name for path in sorted(output.glob("*.png"))] == [
        "cell-r01-c01.png",
        "cell-r01-c02.png",
        "cell-r02-c01.png",
        "cell-r02-c02.png",
        "cell-r03-c01.png",
        "cell-r03-c02.png",
    ]
    assert all(path.stat().st_size > 0 for path in output.glob("*.png"))


def test_extract_table_cells_ocr_is_row_column_ordered(tmp_path: Path):
    source = tmp_path / "page.png"
    output = tmp_path / "cells"
    _make_table(source)
    ocr = FakeOCR()

    result = extract_table_cells(
        source,
        TableGrid(columns=(50, 300, 550), rows=(50, 150, 250, 350)),
        output,
        ocr_engine=ocr,
    )

    assert result.rows() == (
        ("text-1", "text-2"),
        ("text-3", "text-4"),
        ("text-5", "text-6"),
    )
    assert ocr.images == [
        "cell-r01-c01.png",
        "cell-r01-c02.png",
        "cell-r02-c01.png",
        "cell-r02-c02.png",
        "cell-r03-c01.png",
        "cell-r03-c02.png",
    ]


def test_extract_table_cells_does_not_modify_source(tmp_path: Path):
    source = tmp_path / "page.png"
    output = tmp_path / "cells"
    _make_table(source)
    before = source.read_bytes()

    extract_table_cells(
        source,
        TableGrid(columns=(50, 300, 550), rows=(50, 150, 250, 350)),
        output,
    )

    assert source.read_bytes() == before
