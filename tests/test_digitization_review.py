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
