from pathlib import Path

from digitization.review import build_review_markers
from digitization.structure import PageStructure, classify_structure


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "digitization" / "college"


def read_fixture(name: str) -> str:
    return (FIXTURE_ROOT / name).read_text(encoding="utf-8")


def test_real_scan_prose_fixture_remains_prose():
    text = read_fixture("prose-page-08.txt")
    result = classify_structure(text)
    assert result.structure is PageStructure.PROSE


def test_real_scan_code_fixture_is_reviewed_as_code():
    text = read_fixture("code-page-03.txt")
    result = classify_structure(text)
    assert result.structure is PageStructure.CODE
    assert "code-ocr-verification" in build_review_markers(text, result)


def test_real_scan_layout_fixture_keeps_visual_review_marker():
    text = read_fixture("layout-page-01.txt")
    result = classify_structure(text)
    assert result.structure is PageStructure.LAYOUT
    assert "layout-visual-verification" in build_review_markers(text, result)
