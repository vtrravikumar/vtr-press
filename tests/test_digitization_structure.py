from pathlib import Path

from digitization.structure import PageStructure, classify_structure

FIXTURES = Path(__file__).parent / "fixtures" / "digitization"


def test_empty_text_is_layout():
    result = classify_structure("   \n")
    assert result.structure is PageStructure.LAYOUT
    assert result.confidence >= 0.5


def test_plain_technical_prose_defaults_to_prose():
    text = (
        "Artificial neural network models have been studied for many years. "
        "These models are composed of computational elements operating in parallel."
    )
    result = classify_structure(text)
    assert result.structure is PageStructure.PROSE


def test_c_source_with_multiple_signals_is_code():
    text = """#include <stdio.h>
int main(void) {
    int count = 0;
    if (count == 0) {
        return 1;
    }
}
"""
    result = classify_structure(text)
    assert result.structure is PageStructure.CODE
    assert result.confidence >= 0.7
    assert len(result.reasons) >= 2


def test_single_generic_semicolon_does_not_make_code():
    text = "The algorithm has three stages; training, validation and testing are performed separately."
    result = classify_structure(text)
    assert result.structure is PageStructure.PROSE


def test_sparse_display_text_is_layout():
    text = """ANALYSIS OF ARTIFICIAL NEURAL NETWORK

USING BACK PROPAGATION & GENETIC ALGORITHM

A PROJECT REPORT
"""
    result = classify_structure(text)
    assert result.structure is PageStructure.LAYOUT


def test_code_like_text_without_multiple_signals_remains_conservative():
    text = "for better performance; the network adapts its weights during training."
    result = classify_structure(text)
    assert result.structure is PageStructure.PROSE


def test_realistic_regression_fixtures_keep_broad_structure_classes():
    expected = {
        "prose.txt": PageStructure.PROSE,
        "code.txt": PageStructure.CODE,
        "layout.txt": PageStructure.LAYOUT,
    }

    for filename, structure in expected.items():
        result = classify_structure((FIXTURES / filename).read_text(encoding="utf-8"))
        assert result.structure is structure
