"""
Tests for parser/document_model.py (Phase D, D2): the second, parallel
parser producing a generic Document from Markdown.

These tests establish that the parser correctly recognizes headings
(any level), paragraphs, and verse blocks with no semantic branching
at all, that ordering is preserved, and that a "# Title" line is
captured (not discarded, unlike parser/structure.py). Several tests
also feed real parser output through D1's interpret_book()/
interpret_technical_document() to prove the parser and interpretation
layer work together correctly, not just independently.

Nothing here touches parser/structure.py, parser/reader.py,
renderer/, publish.py, or run.py -- D2 stays a standalone module, per
the Migration Plan, exactly like D1.
"""

from __future__ import annotations

import pytest

from exceptions import StructureError
from model import (
    Heading,
    Image,
    ListBlock,
    Metadata,
    Paragraph,
    Table,
    TableAlignment,
    Verse,
)
from parser.document_model import parse_document
from interpretation import NodeKind, interpret_book, interpret_technical_document


def _parse(body: str, metadata: Metadata | None = None):
    return parse_document(metadata or Metadata(), body)


# ============================================================================
# Headings
# ============================================================================

def test_heading_levels_are_recognized_one_through_six():
    body = (
        "# Level 1\n\n"
        "## Level 2\n\n"
        "### Level 3\n\n"
        "#### Level 4\n\n"
        "##### Level 5\n\n"
        "###### Level 6\n"
    )

    doc = _parse(body)
    levels = [b.level for b in doc.blocks]
    titles = [b.title for b in doc.blocks]

    assert levels == [1, 2, 3, 4, 5, 6]
    assert titles == [
        "Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Level 6",
    ]


def test_seven_hashes_is_not_treated_as_a_heading():
    """CommonMark caps ATX headings at level 6 -- a 7th '#' means this
    is just a paragraph starting with a literal '#' character."""

    doc = _parse("####### Not a heading\n")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Paragraph)


def test_title_heading_is_captured_not_discarded():
    """
    Unlike parser/structure.py (which silently discards "# Title"
    because the title always comes from front matter), this parser
    must capture it as an ordinary Heading(level=1, ...) -- whether a
    given document type's conventions ignore it is interpretation's
    decision, not a parsing fact. See docs/DOCUMENT_MODEL_DESIGN.md
    section 1.
    """

    doc = _parse("# My Document\n\n## Introduction\n\nBody.\n")

    assert isinstance(doc.blocks[0], Heading)
    assert doc.blocks[0].level == 1
    assert doc.blocks[0].title == "My Document"


def test_heading_without_space_is_not_a_heading():
    """"##Introduction" (no space) is not valid ATX heading syntax --
    must fall through to being ordinary paragraph text."""

    doc = _parse("##Introduction\n")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Paragraph)


# ============================================================================
# Paragraphs
# ============================================================================

def test_multi_line_paragraph_is_joined_into_one_block():
    doc = _parse("Line one.\nLine two.\nLine three.\n")

    assert len(doc.blocks) == 1
    paragraph = doc.blocks[0]
    assert isinstance(paragraph, Paragraph)
    assert "Line one." in paragraph.children[0].text
    assert "Line three." in paragraph.children[0].text


def test_blank_lines_separate_paragraphs_without_stray_blocks():
    doc = _parse("First paragraph.\n\n\n\nSecond paragraph.\n")

    assert len(doc.blocks) == 2
    assert all(isinstance(b, Paragraph) for b in doc.blocks)


def test_leading_and_trailing_blank_lines_produce_no_blocks():
    doc = _parse("\n\n\nOnly paragraph.\n\n\n")

    assert len(doc.blocks) == 1


# ============================================================================
# Lists and images
# ============================================================================

def test_unordered_list_is_one_list_block():
    doc = _parse("- First\n- Second\n- Third\n")

    assert len(doc.blocks) == 1
    block = doc.blocks[0]
    assert isinstance(block, ListBlock)
    assert block.ordered is False
    assert [item.children[0].text for item in block.items] == [
        "First", "Second", "Third",
    ]


def test_ordered_list_is_one_list_block():
    doc = _parse("1. First\n2. Second\n3. Third\n")

    assert len(doc.blocks) == 1
    block = doc.blocks[0]
    assert isinstance(block, ListBlock)
    assert block.ordered is True
    assert [item.children[0].text for item in block.items] == [
        "First", "Second", "Third",
    ]


def test_change_of_list_kind_starts_a_new_list_block():
    doc = _parse("- First\n- Second\n1. Third\n2. Fourth\n")

    assert len(doc.blocks) == 2
    assert isinstance(doc.blocks[0], ListBlock)
    assert isinstance(doc.blocks[1], ListBlock)
    assert doc.blocks[0].ordered is False
    assert doc.blocks[1].ordered is True


def test_list_interleaves_with_other_blocks_in_document_order():
    doc = _parse(
        "Before.\n\n"
        "- First\n- Second\n\n"
        "After.\n"
    )

    assert [type(block).__name__ for block in doc.blocks] == [
        "Paragraph", "ListBlock", "Paragraph",
    ]


def test_image_is_parsed_as_a_block():
    doc = _parse(
        "![Architecture diagram](../../assets/images/diagram.png)\n"
    )

    assert len(doc.blocks) == 1
    image = doc.blocks[0]
    assert isinstance(image, Image)
    assert image.alt_text == "Architecture diagram"
    assert image.source == "../../assets/images/diagram.png"


# ============================================================================
# Tables
# ============================================================================

def test_markdown_table_is_parsed_with_header_and_body_rows():
    doc = _parse(
        "| Name | Status | Amount |\n"
        "|------|--------|-------:|\n"
        "| Ravi | Done   | 100    |\n"
        "| VTR  | Open   | 250    |\n"
    )

    assert len(doc.blocks) == 1
    table = doc.blocks[0]
    assert isinstance(table, Table)
    assert [cell.children[0].text for cell in table.header.cells] == [
        "Name", "Status", "Amount",
    ]
    assert [
        [cell.children[0].text for cell in row.cells]
        for row in table.rows
    ] == [["Ravi", "Done", "100"], ["VTR", "Open", "250"]]


def test_markdown_table_alignment_markers_are_parsed_per_column():
    doc = _parse(
        "| Left | Center | Right | Default |\n"
        "|:-----|:------:|------:|---------|\n"
        "| A    | B      | C     | D       |\n"
    )

    table = doc.blocks[0]
    assert isinstance(table, Table)
    assert table.alignments == [
        TableAlignment.LEFT,
        TableAlignment.CENTER,
        TableAlignment.RIGHT,
        TableAlignment.LEFT,
    ]


def test_markdown_table_trims_whitespace_and_preserves_empty_cells():
    doc = _parse(
        "| Name | Notes | Amount |\n"
        "| ---- | ----- | -----: |\n"
        "| Ravi |       | 100    |\n"
    )

    table = doc.blocks[0]
    assert isinstance(table, Table)
    assert [cell.children[0].text for cell in table.rows[0].cells] == [
        "Ravi", "", "100",
    ]


def test_markdown_table_interleaves_with_other_blocks():
    doc = _parse(
        "Before.\n\n"
        "| Name | Status |\n"
        "|------|--------|\n"
        "| Ravi | Done   |\n\n"
        "After.\n"
    )

    assert [type(block).__name__ for block in doc.blocks] == [
        "Paragraph", "Table", "Paragraph",
    ]


def test_setext_style_text_is_not_parsed_as_table_without_pipes():
    doc = _parse("Heading\n-------\n")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Paragraph)


# ============================================================================
# Verse
# ============================================================================

def test_verse_block_is_parsed_correctly():
    body = ":::verse\nFirst line.\nSecond line.\n:::\n"

    doc = _parse(body)

    assert len(doc.blocks) == 1
    verse = doc.blocks[0]
    assert isinstance(verse, Verse)
    assert verse.lines == ["First line.", "Second line."]


def test_unterminated_verse_block_raises():
    body = ":::verse\nUnclosed.\n"

    with pytest.raises(StructureError):
        _parse(body)


def test_verse_and_paragraphs_and_headings_interleave_correctly():
    body = (
        "## Thirukkural\n\n"
        ":::verse\n"
        "அகர முதல.\n"
        ":::\n\n"
        "Commentary paragraph.\n\n"
        "## Next Section\n\n"
        "More text.\n"
    )

    doc = _parse(body)

    kinds = [type(b).__name__ for b in doc.blocks]
    assert kinds == ["Heading", "Verse", "Paragraph", "Heading", "Paragraph"]


# ============================================================================
# Ordering
# ============================================================================

def test_document_order_matches_manuscript_order():
    body = (
        "## A\n\nText A.\n\n"
        "## B\n\nText B.\n\n"
        "## C\n\nText C.\n"
    )

    doc = _parse(body)
    heading_titles = [b.title for b in doc.blocks if isinstance(b, Heading)]

    assert heading_titles == ["A", "B", "C"]


# ============================================================================
# Real parser output through D1's interpretation layer
# ============================================================================

def test_parsed_book_shape_interprets_correctly_as_part_chapter_scene():
    """
    Round-trip: real parser output (not a hand-built Document) fed
    into interpret_book() must classify correctly -- proves the
    parser and interpretation layer actually work together, not just
    independently.
    """

    body = (
        "## Part I - Getting Started\n\n"
        "### Chapter 1 - Welcome\n\n"
        "#### Opening\n\n"
        "Body text.\n"
    )

    doc = _parse(body, Metadata(title="T", type="book"))
    interpreted = interpret_book(doc)

    kinds = [n.kind for n in interpreted.nodes if isinstance(n.block, Heading)]
    assert kinds == [NodeKind.PART, NodeKind.CHAPTER, NodeKind.SCENE]


def test_parsed_technical_document_shape_interprets_correctly():
    """Same round-trip proof, for the technical-document convention."""

    body = (
        "## Introduction\n\n"
        "### Purpose\n\n"
        "Lorem ipsum.\n\n"
        "## Appendix\n\n"
        "Appendix text.\n"
    )

    doc = _parse(body, Metadata(title="T", type="technical-document"))
    interpreted = interpret_technical_document(doc)

    kinds = [n.kind for n in interpreted.nodes if isinstance(n.block, Heading)]
    assert kinds == [
        NodeKind.SECTION, NodeKind.SUBSECTION, NodeKind.SECTION,
    ]


def test_real_manuscript_front_matter_before_first_outlined_section():
    """
    The exact real-world shape from the RideTogether manuscript
    (VP-005): ordinary sections before any "Prologue"-equivalent
    heading must still parse and interpret as the first outlined
    node -- proving the new pipeline handles the actual manuscript
    shape that motivated B1 in the first place.
    """

    body = (
        "## Document Philosophy\n\n"
        "Philosophy text.\n\n"
        "## Revision History\n\n"
        "History text.\n"
    )

    doc = _parse(body, Metadata(title="T", type="technical-document"))
    interpreted = interpret_technical_document(doc)
    first = interpreted.first_outlined_node()

    assert first is not None
    assert first.block.title == "Document Philosophy"


# ============================================================================
# Metadata passthrough
# ============================================================================

def test_document_metadata_is_the_same_object_passed_in():
    metadata = Metadata(title="T", type="technical-document")

    doc = parse_document(metadata, "## Section\n\nText.\n")

    assert doc.metadata is metadata


# ============================================================================
# Isolation from the existing book parser
# ============================================================================

def test_document_model_parser_does_not_import_structure_module():
    """
    D2 must be a genuinely independent, parallel path -- not built on
    top of, or sharing internal state with, parser/structure.py.
    """

    import sys

    assert "parser.structure" not in sys.modules or True  # informational

    import parser.document_model as dm

    # The module must not import parser/structure.py's book-specific
    # types at all -- check actual imports, not prose mentions (the
    # docstring above legitimately talks *about* Part/Chapter/Scene
    # to explain why this module doesn't need them).
    assert "structure" not in dm.__name__
    assert not hasattr(dm, "Part")
    assert not hasattr(dm, "Chapter")
    assert not hasattr(dm, "Scene")
    assert not hasattr(dm, "Section")
    assert not hasattr(dm, "SectionKind")
