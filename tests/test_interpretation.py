"""
Tests for interpretation.py (Phase D, D1): NodeKind, InterpretedNode,
InterpretedDocument, and the minimal interpret_book() /
interpret_technical_document() functions.

These tests establish that the SAME generic Document Model can
represent both current document types' structural rules, per
docs/DOCUMENT_MODEL_DESIGN.md sections 3-4 -- with real, executable
proof rather than only prose walkthroughs. They do not touch parsing,
rendering, or the existing publishing pipeline.
"""

from __future__ import annotations

from model import Document, Heading, Metadata, Paragraph, Text
from interpretation import (
    InterpretedDocument,
    InterpretedNode,
    NodeKind,
    interpret_book,
    interpret_technical_document,
)


# ============================================================================
# Book interpretation
# ============================================================================

def test_book_part_chapter_scene_are_assigned_correctly():
    """docs/DOCUMENT_MODEL_DESIGN.md section 3: Part -> Chapter -> Scene."""

    doc = Document(
        metadata=Metadata(title="T", type="book"),
        blocks=[
            Heading(level=2, title="Part I - Getting Started"),
            Heading(level=3, title="Chapter 1 - Welcome"),
            Heading(level=4, title="Opening"),
            Paragraph(children=[Text("Body text.")]),
        ],
    )

    interpreted = interpret_book(doc)
    kinds = [n.kind for n in interpreted.nodes if isinstance(n.block, Heading)]

    assert kinds == [NodeKind.PART, NodeKind.CHAPTER, NodeKind.SCENE]


def test_book_front_matter_kinds_are_not_outlined():
    """Copyright/Dedication/Thirukkural must be excluded from the
    outline, matching renderer/typst.py's existing computation."""

    doc = Document(
        metadata=Metadata(title="T", type="book"),
        blocks=[
            Heading(level=2, title="Copyright"),
            Heading(level=2, title="Dedication"),
            Heading(level=2, title="Thirukkural"),
            Heading(level=2, title="Prologue"),
        ],
    )

    interpreted = interpret_book(doc)
    outlined_by_title = {
        n.block.title: n.outlined
        for n in interpreted.nodes
        if isinstance(n.block, Heading)
    }

    assert outlined_by_title["Copyright"] is False
    assert outlined_by_title["Dedication"] is False
    assert outlined_by_title["Thirukkural"] is False
    assert outlined_by_title["Prologue"] is True


def test_book_first_outlined_node_skips_front_matter():
    """Mirrors VP-005/B1's "first outlined section" -- Copyright must
    not be picked, Prologue (the first real outlined heading) must be."""

    doc = Document(
        metadata=Metadata(title="T", type="book"),
        blocks=[
            Heading(level=2, title="Copyright"),
            Paragraph(children=[Text("c.")]),
            Heading(level=2, title="Prologue"),
            Paragraph(children=[Text("p.")]),
        ],
    )

    interpreted = interpret_book(doc)
    first = interpreted.first_outlined_node()

    assert first is not None
    assert first.block.title == "Prologue"


def test_book_first_outlined_node_handles_front_matter_before_first_section():
    """
    The exact real-world shape found in the RideTogether manuscript
    (via VP-005): an ordinary section before any Prologue must still
    be found correctly as the first outlined node.
    """

    doc = Document(
        metadata=Metadata(title="T", type="book"),
        blocks=[
            Heading(level=2, title="Document Philosophy"),
            Paragraph(children=[Text("text")]),
        ],
    )

    interpreted = interpret_book(doc)
    first = interpreted.first_outlined_node()

    assert first is not None
    assert first.block.title == "Document Philosophy"
    assert first.kind == NodeKind.OTHER


def test_book_chapter_only_assigned_when_preceded_by_part():
    """A level-3 heading not preceded by a Part-kind level-2 heading
    must not be classified CHAPTER."""

    doc = Document(
        metadata=Metadata(title="T", type="book"),
        blocks=[
            Heading(level=2, title="Introduction"),
            Heading(level=3, title="Purpose"),
        ],
    )

    interpreted = interpret_book(doc)
    purpose_node = next(
        n for n in interpreted.nodes
        if isinstance(n.block, Heading) and n.block.title == "Purpose"
    )

    assert purpose_node.kind != NodeKind.CHAPTER


# ============================================================================
# Technical-document interpretation
# ============================================================================

def test_technical_document_sections_and_subsections_are_assigned_correctly():
    """docs/DOCUMENT_MODEL_DESIGN.md section 4: numbered sections and
    subsections, without any Part/Chapter/Scene concept at all."""

    doc = Document(
        metadata=Metadata(title="T", type="technical-document"),
        blocks=[
            Heading(level=2, title="Introduction"),
            Heading(level=3, title="Purpose"),
            Heading(level=3, title="Scope"),
            Heading(level=2, title="Appendix"),
        ],
    )

    interpreted = interpret_technical_document(doc)
    kinds = [n.kind for n in interpreted.nodes]

    assert kinds == [
        NodeKind.SECTION,
        NodeKind.SUBSECTION,
        NodeKind.SUBSECTION,
        NodeKind.SECTION,
    ]


def test_technical_document_sections_are_all_outlined():
    """Unlike book, technical-document has no front-matter exclusion
    set today -- every top-level section is numbered/outlined."""

    doc = Document(
        metadata=Metadata(title="T", type="technical-document"),
        blocks=[
            Heading(level=2, title="Document Philosophy"),
            Heading(level=2, title="Revision History"),
        ],
    )

    interpreted = interpret_technical_document(doc)

    assert all(n.outlined for n in interpreted.nodes)


def test_technical_document_first_outlined_node_is_the_first_section():
    """Same algorithm as book's first_outlined_node(), applied to a
    technical-document-shaped, differently-kind-tagged stream."""

    doc = Document(
        metadata=Metadata(title="T", type="technical-document"),
        blocks=[
            Heading(level=2, title="Document Philosophy"),
            Heading(level=2, title="Revision History"),
        ],
    )

    interpreted = interpret_technical_document(doc)
    first = interpreted.first_outlined_node()

    assert first is not None
    assert first.block.title == "Document Philosophy"


def test_appendix_is_an_ordinary_section_no_special_kind_needed():
    """Matches SECTION_MAP's existing behavior: "Appendix" falls
    through to a generic kind, no dedicated APPENDIX assignment
    required to represent it correctly."""

    doc = Document(
        metadata=Metadata(title="T", type="technical-document"),
        blocks=[Heading(level=2, title="Appendix")],
    )

    interpreted = interpret_technical_document(doc)

    assert interpreted.nodes[0].kind == NodeKind.SECTION
    assert interpreted.nodes[0].outlined is True


# ============================================================================
# Same algorithm, both types (docs/DOCUMENT_MODEL_DESIGN.md section 4's
# central claim: "first outlined section" is type-agnostic machinery)
# ============================================================================

def test_first_outlined_node_is_the_same_method_for_both_types():
    """InterpretedDocument.first_outlined_node() is not type-specific
    -- both interpret_book() and interpret_technical_document() call
    the same method on their output, just with differently-tagged
    nodes. This is the concrete proof behind the design note's claim
    that this is "one algorithm, two conventions.\""""

    book_doc = Document(
        metadata=Metadata(title="B", type="book"),
        blocks=[Heading(level=2, title="Prologue")],
    )
    tech_doc = Document(
        metadata=Metadata(title="D", type="technical-document"),
        blocks=[Heading(level=2, title="Introduction")],
    )

    book_interpreted = interpret_book(book_doc)
    tech_interpreted = interpret_technical_document(tech_doc)

    assert type(book_interpreted) is type(tech_interpreted) is InterpretedDocument
    assert book_interpreted.first_outlined_node().block.title == "Prologue"
    assert tech_interpreted.first_outlined_node().block.title == "Introduction"


def test_non_heading_blocks_pass_through_uninterpreted():
    """Paragraph/Verse blocks get an InterpretedNode wrapper with
    kind=None, outlined=False -- interpretation only assigns meaning
    to headings, never fabricates one for prose."""

    doc = Document(
        metadata=Metadata(title="T", type="book"),
        blocks=[Paragraph(children=[Text("orphan text")])],
    )

    interpreted = interpret_book(doc)

    assert len(interpreted.nodes) == 1
    assert interpreted.nodes[0].kind is None
    assert interpreted.nodes[0].outlined is False


def test_interpreted_node_wraps_the_original_block_unchanged():
    """InterpretedNode must not copy or mutate the underlying block --
    it wraps the exact same object, matching the "annotate in place"
    design from Gap 1."""

    heading = Heading(level=2, title="Prologue")
    doc = Document(metadata=Metadata(title="T"), blocks=[heading])

    interpreted = interpret_book(doc)

    assert interpreted.nodes[0].block is heading
