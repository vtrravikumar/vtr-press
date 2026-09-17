from pathlib import Path

from PIL import Image, ImageDraw

from digitization.layout import TableGrid, VisualAnalysis, VisualRegion
from digitization.visual_extract import extract_visual_candidates


def test_extracts_table_region_and_cells(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image = Image.new("RGB", (600, 400), "white")
    draw = ImageDraw.Draw(image)
    for x in (100, 250, 400):
        draw.line((x, 80, x, 320), fill="black", width=3)
    for y in (80, 160, 240, 320):
        draw.line((100, y, 400, y), fill="black", width=3)
    image.save(image_path)

    analysis = VisualAnalysis(
        table_likely=True,
        confidence=0.8,
        regions=(VisualRegion("table", 100, 80, 401, 321, 0.8),),
        table_grid=TableGrid(columns=(100, 250, 400), rows=(80, 160, 240, 320)),
    )
    output = tmp_path / "assets"
    regions = extract_visual_candidates(image_path, analysis, output)

    assert regions[0].kind == "table"
    assert len(list(output.glob("table-cell-*.png"))) == 6


def test_extracts_diagram_candidate_without_modifying_source(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((220, 180, 580, 420), outline="black", width=5)
    draw.line((300, 300, 500, 300), fill="black", width=5)
    original = image.tobytes()
    image.save(image_path)

    analysis = VisualAnalysis(
        diagram_likely=True,
        confidence=0.7,
        reasons=("line-structure-signals",),
    )
    output = tmp_path / "assets"
    regions = extract_visual_candidates(image_path, analysis, output)

    assert regions
    assert regions[0].kind == "diagram"
    assert (output / "diagram-candidate.png").is_file()
    with Image.open(image_path) as unchanged:
        assert unchanged.tobytes() == original
