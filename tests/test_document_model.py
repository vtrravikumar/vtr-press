"""
Tests for the generic Document Model (Phase D, D1): Heading and
Document, added to model.py.

These tests establish that the new, additive types can represent the
required generic blocks, preserve ordering, and represent heading
levels without carrying any book-specific (or any type-specific)
semantics -- a raw Heading is just a level and a title.

Nothing here touches the existing Book/Part/Chapter/Scene/Section
model, and nothing here goes through parsing or rendering -- these
are direct constructions, matching D1's explicit scope (no parser,
no renderer wiring).
"""

from __future__ import annotations

from model import (
    Block,
    Document,
    Heading,
    Image,
    ListBlock,
    ListItem,
    Metadata,
    Paragraph,
    Text,
    Verse,
)


def test_heading_is_a_block():
    """Heading reuses the existing Block ABC, so it composes with
    Paragraph/Verse in a single flat list, exactly like Section.blocks
    already does for Paragraph/Verse/Subheading."""

    heading = Heading(level=2, title="Introduction")

    assert isinstance(heading, Block)


def test_heading_carries_only_level_and_title():
    """No kind, no outlined, no semantic fields at all -- a raw
    Heading records only what the manuscript's Markdown syntax says."""

    heading = Heading(level=3, title="Purpose")

    assert heading.level == 3
    assert heading.title == "Purpose"
    assert not hasattr(heading, "kind")
    assert not hasattr(heading, "outlined")


def test_generic_list_and_image_blocks_are_blocks():
    assert isinstance(ListBlock(), Block)
    assert isinstance(Image(), Block)


def test_list_item_and_list_block_preserve_structure():
    item = ListItem(children=[Text("Item")])
    block = ListBlock(ordered=True, items=[item])

    assert block.ordered is True
    assert block.items == [item]
    assert block.items[0].children[0].text == "Item"


def test_image_preserves_source_and_alt_text():
    image = Image(
        source="../../assets/images/diagram.png",
        alt_text="Architecture diagram",
    )

    assert image.source == "../../assets/images/diagram.png"
    assert image.alt_text == "Architecture diagram"


def test_document_can_represent_a_mix_of_generic_blocks():
    """A single flat Document.blocks list can hold Heading, Paragraph,
    and Verse together, in any combination."""

    doc = Document(
        metadata=Metadata(title="T"),
        blocks=[
            Heading(level=1, title="T"),
            Heading(level=2, title="Introduction"),
            Paragraph(children=[Text("Body text.")]),
            Verse(lines=["Line one.", "Line two."]),
            Heading(level=3, title="Subsection"),
        ],
    )

    assert len(doc.blocks) == 5
    assert isinstance(doc.blocks[0], Heading)
    assert isinstance(doc.blocks[2], Paragraph)
    assert isinstance(doc.blocks[3], Verse)


def test_document_preserves_block_order():
    """Structure comes from document order, not nesting -- the model
    must preserve exactly the sequence blocks were constructed in."""

    doc = Document(
        blocks=[
            Heading(level=2, title="First"),
            Heading(level=2, title="Second"),
            Heading(level=2, title="Third"),
        ],
    )

    titles = [b.title for b in doc.blocks]

    assert titles == ["First", "Second", "Third"]


def test_document_has_no_recursive_nesting():
    """Document.blocks is a flat list[Block] -- headings do not have
    children, parents, or any nested container of their own. Depth
    is expressed by Heading.level, not by structure."""

    heading = Heading(level=2, title="Section")

    assert not hasattr(heading, "children")
    assert not hasattr(heading, "blocks")
    assert not hasattr(heading, "sections")


def test_heading_level_carries_no_book_specific_semantics():
    """
    A level-2 Heading titled "Part I" and a level-2 Heading titled
    "Introduction" are structurally identical at the model level --
    the model does not know, and must not encode, that one of these
    is conventionally a book Part and the other a technical-document
    Section. That distinction belongs to interpretation
    (see tests/test_interpretation.py), not to the raw model.
    """

    part_like = Heading(level=2, title="Part I")
    section_like = Heading(level=2, title="Introduction")

    assert type(part_like) is type(section_like)
    assert part_like.level == section_like.level


def test_document_defaults_are_empty_not_none():
    """Matches the existing model.py convention (e.g. Section.blocks,
    Part.chapters) of empty-list defaults via default_factory, not
    None, so callers don't need to null-check before iterating."""

    doc = Document()

    assert doc.blocks == []
    assert isinstance(doc.metadata, Metadata)


def test_document_and_book_are_independent_root_types():
    """Document is a new, separate root type -- constructing one must
    not require or affect Book in any way."""

    from model import Book

    doc = Document(metadata=Metadata(title="Doc"), blocks=[])
    book = Book(metadata=Metadata(title="Book"), sections=[])

    assert type(doc) is not type(book)
    assert doc.metadata.title == "Doc"
    assert book.metadata.title == "Book"
