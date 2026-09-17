from pathlib import Path

from PIL import Image, ImageDraw

from digitization.layout import VisualAnalysis, analyze_page


def test_visual_analysis_handles_missing_image(tmp_path: Path):
    missing = tmp_path / "missing.png"
    try:
        analyze_page(missing)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected missing image error")


def test_visual_analysis_detects_ruled_table(tmp_path: Path):
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
