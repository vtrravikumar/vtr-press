from pathlib import Path

from PIL import Image, ImageDraw

from digitization.layout import TableGrid, VisualAnalysis, VisualRegion, analyze_page


def test_visual_analysis_handles_missing_image(tmp_path: Path):
    missing = tmp_path / "missing.png"
    try:
        analyze_page(missing)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected missing image error")


def test_visual_analysis_detects_ruled_table_and_candidate_region(tmp_path: Path):
    image = Image.new("L", (800, 600), 255)
    draw = ImageDraw.Draw(image)
    for y in (100, 200, 300, 400):
        draw.line((100, y, 700, y), fill=0, width=3)
    for x in (100, 300, 500, 700):
        draw.line((x, 100, x, 400), fill=0, width=3)
    path = tmp_path / "table.png"
    image.save(path)

    result = analyze_page(path)

    assert result.table_likely is True
    assert result.diagram_likely is False
    assert "ruled-grid-signals" in result.reasons
    assert result.confidence > 0
    assert len(result.regions) == 1
    region = result.regions[0]
    assert isinstance(region, VisualRegion)
    assert region.kind == "table"
    assert 90 <= region.left <= 110
    assert 690 <= region.right <= 710
    assert 90 <= region.top <= 110
    assert 390 <= region.bottom <= 410

    assert isinstance(result.table_grid, TableGrid)
    assert result.table_grid.columns == (100, 300, 500, 700)
    assert result.table_grid.rows == (100, 200, 300, 400)
    assert result.table_grid.column_count == 3
    assert result.table_grid.row_count == 3

    cells = result.table_grid.cell_regions(confidence=result.regions[0].confidence)
    assert len(cells) == 9
    assert cells[0] == VisualRegion("table-cell", 100, 100, 300, 200, result.regions[0].confidence)
    assert cells[-1] == VisualRegion("table-cell", 500, 300, 700, 400, result.regions[0].confidence)


def test_visual_analysis_maps_candidate_grid_to_original_coordinates(tmp_path: Path):
    image = Image.new("L", (3200, 2400), 255)
    draw = ImageDraw.Draw(image)
    for y in (400, 800, 1200, 1600):
        draw.line((400, y, 2800, y), fill=0, width=5)
    for x in (400, 1200, 2000, 2800):
        draw.line((x, 400, x, 1600), fill=0, width=5)
    path = tmp_path / "large-table.png"
    image.save(path)

    result = analyze_page(path)

    assert len(result.regions) == 1
    region = result.regions[0]
    assert 380 <= region.left <= 420
    assert 2780 <= region.right <= 2820
    assert 380 <= region.top <= 420
    assert 1580 <= region.bottom <= 1620
    assert result.table_grid is not None
    assert result.table_grid.columns == (400, 1200, 2000, 2800)
    assert result.table_grid.rows == (400, 800, 1200, 1600)


def test_visual_analysis_returns_no_semantic_claim_for_plain_page(tmp_path: Path):
    image = Image.new("L", (800, 600), 255)
    path = tmp_path / "blank.png"
    image.save(path)

    result = analyze_page(path)

    assert isinstance(result, VisualAnalysis)
    assert result.table_likely is False
    assert result.diagram_likely is False
    assert result.figure_likely is False
    assert result.confidence == 0.0
    assert result.regions == ()
    assert result.table_grid is None


def test_table_grid_without_boundaries_has_no_cells():
    assert TableGrid().cell_regions() == ()
