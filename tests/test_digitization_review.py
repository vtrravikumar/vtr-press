from digitization.layout import VisualAnalysis
from digitization.review import build_review_markers
from digitization.structure import PageStructure, StructureClassification


def test_code_pages_require_code_verification():
    classification = StructureClassification(PageStructure.CODE, 0.9, ("signal",))
    assert build_review_markers("int main(void) {}", classification) == (
        "code-ocr-verification",
    )


def test_layout_pages_require_visual_verification():
    classification = StructureClassification(PageStructure.LAYOUT, 0.8, ("sparse",))
    assert build_review_markers("A PROJECT REPORT", classification) == (
        "layout-visual-verification",
    )


def test_low_confidence_non_prose_is_marked():
    classification = StructureClassification(PageStructure.LAYOUT, 0.5, ("sparse",))
    assert build_review_markers("TITLE", classification) == (
        "layout-visual-verification",
        "low-structure-confidence",
    )


def test_visual_table_requires_verification():
    visual = VisualAnalysis(table_likely=True, confidence=0.75, reasons=("ruled-grid-signals",))
    assert build_review_markers("row one", None, visual) == (
        "table-visual-verification",
    )


def test_visual_diagram_and_figure_markers_are_distinct():
    visual = VisualAnalysis(
        diagram_likely=True,
        figure_likely=True,
        confidence=0.7,
        reasons=("line-structure-signals", "non-text-visual-density"),
    )
    assert build_review_markers("visual page", None, visual) == (
        "diagram-visual-verification",
        "figure-visual-verification",
    )


def test_normal_prose_baseline_is_not_flagged_for_confidence():
    classification = StructureClassification(PageStructure.PROSE, 0.5, ())
    assert build_review_markers("Ordinary running text.", classification) == ()


def test_suspicious_replacement_character_is_marked():
    assert build_review_markers("Text � here", None) == ("suspicious-ocr-glyphs",)


def test_review_markers_never_change_text():
    text = "Il. General text"
    classification = StructureClassification(PageStructure.PROSE, 0.5, ())
    build_review_markers(text, classification)
    assert text == "Il. General text"
