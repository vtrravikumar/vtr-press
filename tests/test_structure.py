"""
Regression tests for parser/structure.py.
"""

from __future__ import annotations

import pytest

from exceptions import StructureError
from model import Metadata, Part, Section, SectionKind, Subheading, Verse, Paragraph
from parser.structure import parse_structure


def _parse(body: str, metadata: Metadata | None = None):
    return parse_structure(metadata or Metadata(), body)


# ============================================================================
# Full manuscript shape
# ============================================================================

def test_valid_manuscript_produces_expected_shape(valid_manuscript_text, sample_metadata):
    from parser.reader import read

    # Strip front matter manually via reader semantics is overkill here;
    # just split on the closing delimiter the fixture uses.
    body = valid_manuscript_text.split("---\n", 2)[-1]

    book = _parse(body, sample_metadata)

    kinds = [
        s.kind for s in book.sections if isinstance(s, Section)
    ]
    assert SectionKind.COPYRIGHT in kinds
    assert SectionKind.DEDICATION in kinds
    assert SectionKind.THIRUKKURAL in kinds
    assert SectionKind.PROLOGUE in kinds
    assert SectionKind.EPILOGUE in kinds
    assert SectionKind.ABOUT_AUTHOR in kinds
    assert SectionKind.BACK_COVER in kinds

    parts = [s for s in book.sections if isinstance(s, Part)]
    assert len(parts) == 1
    assert parts[0].title == "Part I - Getting Started"
    assert len(parts[0].chapters) == 3

    ch1, ch2, ch3 = parts[0].chapters
    assert ch1.number == 1
    assert ch2.number == 2
    assert ch3.number == 3
    assert ch1.scenes[0].title == "First Scene"

    # Chapter 3 has no explicit '#### ' heading -> auto untitled scene.
    assert len(ch3.scenes) == 1
    assert ch3.scenes[0].title is None
    assert len(ch3.scenes[0].blocks) >= 1


def test_unknown_section_title_maps_to_other():
    body = "## Some Unrecognized Heading\n\nBody text.\n"

    book = _parse(body)

    assert len(book.sections) == 1
    section = book.sections[0]
    assert isinstance(section, Section)
    assert section.kind == SectionKind.OTHER
    assert section.title == "Some Unrecognized Heading"


def test_section_kind_matching_is_case_insensitive():
    body = "## COPYRIGHT\n\nBody.\n"

    book = _parse(body)

    assert book.sections[0].kind == SectionKind.COPYRIGHT


def test_book_title_line_is_ignored():
    body = "# The Book Title\n\n## Prologue\n\nText.\n"

    book = _parse(body)

    assert len(book.sections) == 1
    assert book.sections[0].kind == SectionKind.PROLOGUE


# ============================================================================
# Verse blocks
# ============================================================================

def test_verse_block_preserves_lines():
    body = (
        "## Prologue\n\n"
        ":::verse\n"
        "Line one.\n"
        "Line two.\n"
        ":::\n"
    )

    book = _parse(body)
    blocks = book.sections[0].blocks

    assert len(blocks) == 1
    assert isinstance(blocks[0], Verse)
    assert blocks[0].lines == ["Line one.", "Line two."]


def test_unterminated_verse_raises():
    body = "## Prologue\n\n:::verse\nLine one.\n"

    with pytest.raises(StructureError):
        _parse(body)


def test_verse_inside_chapter_attaches_to_current_scene():
    body = (
        "## Part I\n\n"
        "### Chapter 1\n\n"
        "#### Scene\n\n"
        ":::verse\nA line.\n:::\n"
    )

    book = _parse(body)
    part = book.sections[0]
    scene = part.chapters[0].scenes[0]

    assert isinstance(scene.blocks[0], Verse)


# ============================================================================
# Structural errors
# ============================================================================

def test_paragraph_outside_section_or_chapter_raises():
    body = "Just a stray paragraph with no heading above it.\n"

    with pytest.raises(StructureError):
        _parse(body)


def test_chapter_outside_part_raises():
    body = "### Chapter 1\n\nText.\n"

    with pytest.raises(StructureError):
        _parse(body)


def test_scene_outside_chapter_raises():
    body = "## Part I\n\n#### A Scene\n\nText.\n"

    with pytest.raises(StructureError):
        _parse(body)


def test_starting_a_new_part_resets_current_section():
    """Switching from a Section to a Part must not leak content into the old section."""

    body = (
        "## Prologue\n\nProloge text.\n\n"
        "## Part I\n\n"
        "### Chapter 1\n\nChapter text.\n"
    )

    book = _parse(body)

    prologue = book.sections[0]
    part = book.sections[1]

    assert isinstance(prologue, Section)
    assert isinstance(part, Part)
    assert len(prologue.blocks) == 1
    assert len(part.chapters[0].scenes[0].blocks) == 1


def test_starting_a_new_section_resets_current_part():
    body = (
        "## Part I\n\n"
        "### Chapter 1\n\n#### Scene\n\nChapter text.\n\n"
        "## Epilogue\n\nEpilogue text.\n"
    )

    book = _parse(body)

    part = book.sections[0]
    epilogue = book.sections[1]

    assert len(part.chapters[0].scenes[0].blocks) == 1
    assert epilogue.blocks[0].children[0].text == "Epilogue text."


def test_part_detection_requires_leading_part_keyword():
    """'## Parts of a Whole' is NOT a Part -- must literally start with 'part '."""

    body = "## Parts of a Whole\n\nText.\n"

    book = _parse(body)

    assert isinstance(book.sections[0], Section)


# ============================================================================
# Paragraphs
# ============================================================================

def test_blank_lines_separate_paragraphs():
    body = "## Prologue\n\nFirst paragraph.\n\nSecond paragraph.\n"

    book = _parse(body)
    blocks = book.sections[0].blocks

    assert len(blocks) == 2
    assert all(isinstance(b, Paragraph) for b in blocks)


def test_multiline_paragraph_is_joined_with_newline():
    body = "## Prologue\n\nLine one\nLine two continues.\n"

    book = _parse(body)
    text = book.sections[0].blocks[0].children[0].text

    assert text == "Line one\nLine two continues."


# ============================================================================
# Subheadings (### / #### outside a Part)
# ============================================================================

def test_subsection_under_section_produces_subheading():
    body = (
        "## Introduction\n\n"
        "### Purpose\n\n"
        "Explains why.\n\n"
        "### Scope\n\n"
        "Explains what.\n"
    )

    book = _parse(body)
    section = book.sections[0]

    assert [type(b).__name__ for b in section.blocks] == [
        "Subheading", "Paragraph", "Subheading", "Paragraph",
    ]
    assert section.blocks[0].title == "Purpose"
    assert section.blocks[0].level == 3
    assert section.blocks[2].title == "Scope"


def test_level_four_under_section_also_produces_subheading():
    body = (
        "## Appendix\n\n"
        "### Architecture Decision Records\n\n"
        "#### ADR-001\n\n"
        "Some decision text.\n"
    )

    book = _parse(body)
    section = book.sections[0]

    assert section.blocks[0].title == "Architecture Decision Records"
    assert section.blocks[0].level == 3
    assert section.blocks[1].title == "ADR-001"
    assert section.blocks[1].level == 4


def test_chapter_and_scene_inside_a_part_are_unaffected():
    """
    The pre-existing Part -> Chapter -> Scene grammar must be completely
    untouched: ### and #### inside a Part still produce Chapter/Scene,
    never Subheading.
    """

    body = (
        "## Part I\n\n"
        "### Chapter 1\n\n"
        "#### Scene One\n\n"
        "Body text.\n"
    )

    book = _parse(body)
    part = book.sections[0]

    assert isinstance(part, Part)
    assert part.chapters[0].title == "Chapter 1"
    assert part.chapters[0].scenes[0].title == "Scene One"


def test_subheading_outside_any_section_or_part_raises():
    body = "### Purpose\n\nText.\n"

    with pytest.raises(StructureError):
        _parse(body)
