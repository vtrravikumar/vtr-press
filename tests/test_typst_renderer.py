"""
Regression tests for renderer/typst.py.

These tests inspect the generated Typst *source text*. They do not
require the `typst` binary and do not compile anything -- they lock
in the string-level contract between the Python renderer and the
themes/classic/*.typ templates.
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from model import (
    Book,
    Chapter,
    Link,
    Metadata,
    Paragraph,
    Part,
    Scene,
    Section,
    SectionKind,
    Subheading,
    Text,
)
from renderer.typst import RenderOptions, THEME_IMPORT_BY_TYPE, _Renderer, render


def _renderer() -> _Renderer:
    return _Renderer(cover_path="/assets/books/current/cover.png")


# ============================================================================
# Escaping
# ============================================================================

def test_escape_text_escapes_hash():
    r = _renderer()

    assert r._escape_text("price: #1") == r"price: \#1"


def test_escape_text_escapes_backslash():
    r = _renderer()

    assert r._escape_text("a\\b") == "a\\\\b"


def test_escape_string_escapes_quotes():
    r = _renderer()

    assert r._escape_string('He said "hi"') == 'He said \\"hi\\"'


def test_escape_string_escapes_backslash():
    r = _renderer()

    assert r._escape_string("C:\\path") == "C:\\\\path"


def test_plain_handles_none():
    r = _renderer()

    assert r._plain(None) == ""


# ============================================================================
# Link URL escaping (regression: was previously unescaped)
# ============================================================================

def test_link_url_with_quote_is_escaped():
    r = _renderer()

    out = r._render_inline(
        Link(text="a link", url='https://example.com/"; malicious')
    )

    # The quote inside the URL must be escaped, not break out of the
    # Typst string literal.
    assert out == r'link("https://example.com/\"; malicious")[a link]'
    # Sanity: the number of unescaped, unbackslashed quotes delimiting
    # the string must be exactly two (open + close).
    unescaped_quotes = re.findall(r'(?<!\\)"', out)
    assert len(unescaped_quotes) == 2


def test_link_url_with_backslash_is_escaped():
    r = _renderer()

    out = r._render_inline(Link(text="t", url="https://example.com/\\evil"))

    assert out == r'link("https://example.com/\\evil")[t]'


def test_link_text_is_markup_escaped_not_string_escaped():
    r = _renderer()

    out = r._render_inline(Link(text="a # sign", url="https://example.com"))

    assert r"\#" in out


# ============================================================================
# Running header title stripping
# ============================================================================

@pytest.mark.parametrize(
    "title,expected",
    [
        ("Chapter 1: Homecoming", "Homecoming"),
        ("Chapter One - The Beginning", "The Beginning"),
        ("Chapter 3 — Em Dash", "Em Dash"),
        ("Interlude: A Pause", "Interlude: A Pause"),
    ],
)
def test_running_title_strips_recognized_chapter_prefixes(title, expected):
    r = _renderer()

    assert r._running_title(title) == expected


def test_running_title_known_limitation_no_separator():
    """
    Known limitation: without a separator ('-', an en/em dash, or ':')
    between the chapter number and the title, the prefix is not stripped.
    If this starts passing, the regex was improved -- update the test.
    """

    r = _renderer()

    assert r._running_title("Chapter 12 Homecoming") == "Chapter 12 Homecoming"


# ============================================================================
# Full render(): structural wiring
# ============================================================================

def _minimal_book(metadata: Metadata) -> Book:
    copyright_section = Section(
        kind=SectionKind.COPYRIGHT,
        title="Copyright",
        blocks=[Paragraph(children=[Text("All rights reserved.")])],
    )
    prologue = Section(
        kind=SectionKind.PROLOGUE,
        title="Prologue",
        blocks=[Paragraph(children=[Text("Prologue text.")])],
    )
    chapter = Chapter(
        number=1,
        title="Chapter 1 - Welcome",
        scenes=[
            Scene(
                title="Opening",
                blocks=[Paragraph(children=[Text("Chapter body.")])],
            )
        ],
    )
    part = Part(title="Part I - Getting Started", chapters=[chapter])
    back_cover = Section(
        kind=SectionKind.BACK_COVER,
        title="Back Cover",
        blocks=[Paragraph(children=[Text("Back cover blurb.")])],
    )

    return Book(
        metadata=metadata,
        sections=[copyright_section, prologue, part, back_cover],
    )


def _print_book(metadata: Metadata) -> Book:
    copyright_section = Section(
        kind=SectionKind.COPYRIGHT,
        title="Copyright",
        blocks=[
            Paragraph(children=[Text("First Edition - 2026")]),
            Paragraph(children=[Text("Copyright (c) 2026 Jane Doe.")]),
            Paragraph(children=[Text("ISBN: 978-1-2345-6789-0")]),
        ],
    )
    prologue = Section(
        kind=SectionKind.PROLOGUE,
        title="Prologue",
        blocks=[Paragraph(children=[Text("Prologue text.")])],
    )
    back_cover = Section(
        kind=SectionKind.BACK_COVER,
        title="Back Cover",
        blocks=[Paragraph(children=[Text("Published by\nVTR Press")])],
    )

    return Book(
        metadata=metadata,
        sections=[copyright_section, prologue, back_cover],
    )


def _multi_part_print_book(metadata: Metadata) -> Book:
    copyright_section = Section(
        kind=SectionKind.COPYRIGHT,
        title="Copyright",
        blocks=[Paragraph(children=[Text("All rights reserved.")])],
    )
    prologue = Section(
        kind=SectionKind.PROLOGUE,
        title="Prologue",
        blocks=[Paragraph(children=[Text("Prologue text.")])],
    )
    first_part = Part(
        title="Part I - Foundations",
        chapters=[
            Chapter(
                number=1,
                title="Chapter 1 - First",
                scenes=[
                    Scene(
                        title="Opening",
                        blocks=[Paragraph(children=[Text("First body.")])],
                    )
                ],
            ),
            Chapter(
                number=2,
                title="Chapter 2 - Second",
                scenes=[
                    Scene(
                        title="Next",
                        blocks=[Paragraph(children=[Text("Second body.")])],
                    )
                ],
            ),
        ],
    )
    second_part = Part(
        title="Part II - Practice",
        chapters=[
            Chapter(
                number=3,
                title="Chapter 3 - Third",
                scenes=[
                    Scene(
                        title="Again",
                        blocks=[Paragraph(children=[Text("Third body.")])],
                    )
                ],
            )
        ],
    )

    return Book(
        metadata=metadata,
        sections=[copyright_section, prologue, first_part, second_part],
    )


def test_render_includes_preamble_with_title_and_author(sample_metadata):
    out = render(_minimal_book(sample_metadata))

    assert '#import "../themes/classic/theme.typ": *' in out
    assert f'book-title: "{sample_metadata.title}"' in out
    assert f'book-author: "{sample_metadata.author}"' in out


def test_render_wraps_front_matter_sections_in_front_matter_page(sample_metadata):
    out = render(_minimal_book(sample_metadata))

    assert "#front-matter-page[" in out


def test_render_wraps_copyright_content_in_centered_front_matter(sample_metadata):
    out = render(_minimal_book(sample_metadata))

    assert "#centered-front-matter[" in out


def test_render_starts_main_matter_at_prologue(sample_metadata):
    out = render(_minimal_book(sample_metadata))

    lines = out.splitlines()
    main_matter_idx = next(i for i, l in enumerate(lines) if l == "#main-matter[")
    prologue_idx = next(
        i for i, l in enumerate(lines) if "running-section-page" in l and "Prologue" in l
    )

    assert main_matter_idx < prologue_idx


def test_render_inserts_contents_exactly_once_before_prologue(sample_metadata):
    out = render(_minimal_book(sample_metadata))

    assert out.count("#render-contents()") == 1

    contents_idx = out.index("#render-contents()")
    prologue_idx = out.index("running-section-page")

    assert contents_idx < prologue_idx


def test_render_chapter_uses_running_title_for_header_state(sample_metadata):
    out = render(_minimal_book(sample_metadata))

    # "Chapter 1 - Welcome" should have its prefix stripped for the
    # running header, while the on-page heading keeps the full title.
    assert '#chapter-page("Welcome")[' in out
    assert "== Chapter 1 - Welcome" in out


def test_render_back_cover_uses_back_cover_page_and_no_heading(sample_metadata):
    out = render(_minimal_book(sample_metadata))

    assert "#back-cover-page[" in out
    # No '== Back Cover' heading should be emitted for the back cover.
    assert "== Back Cover" not in out


def test_render_closes_all_open_brackets_evenly(sample_metadata):
    """A structural smoke test: every '[' block opener should be matched."""

    out = render(_minimal_book(sample_metadata))

    opens = out.count("[")
    closes = out.count("]")

    assert opens == closes


def test_render_first_page_has_no_leading_pagebreak(sample_metadata):
    out = render(_minimal_book(sample_metadata))

    # The very first content-producing call is the cover; nothing
    # before it should trigger a #pagebreak().
    cover_idx = out.index("#render-cover(")
    preceding = out[:cover_idx]

    assert "#pagebreak()" not in preceding


def test_render_normal_mode_keeps_cover_and_default_title_page(sample_metadata):
    out = render(_print_book(sample_metadata))

    assert "#render-cover(" in out
    assert "#back-cover-page[" in out
    assert "show-publisher-logo" not in out
    assert "#render-publisher-imprint()" in out


def test_render_print_mode_skips_cover_and_hides_title_page_logo(sample_metadata):
    out = render(
        _print_book(sample_metadata),
        options=RenderOptions(print_mode=True),
    )

    assert "#render-cover(" not in out
    assert "#back-cover-page[" not in out
    assert "show-publisher-logo: false" in out
    assert "#render-publisher-imprint()" not in out


def test_render_print_mode_leaves_copyright_body_unchanged(sample_metadata):
    out = render(
        _print_book(sample_metadata),
        options=RenderOptions(print_mode=True),
    )
    copyright_idx = out.index("#front-matter-page[")
    prologue_idx = out.index(")[Prologue]")
    copyright_page = out[copyright_idx:prologue_idx]

    assert "Copyright (c) 2026 Jane Doe." in copyright_page
    assert "ISBN: 978-1-2345-6789-0" in copyright_page


def test_render_omits_empty_isbn_placeholder(sample_metadata):
    copyright_section = Section(
        kind=SectionKind.COPYRIGHT,
        title="Copyright",
        blocks=[
            Paragraph(children=[Text("First Edition - 2026")]),
            Paragraph(children=[Text("ISBN:")]),
        ],
    )
    prologue = Section(
        kind=SectionKind.PROLOGUE,
        title="Prologue",
        blocks=[Paragraph(children=[Text("Prologue text.")])],
    )

    out = render(
        Book(metadata=sample_metadata, sections=[copyright_section, prologue])
    )

    assert "First Edition - 2026" in out
    assert "ISBN:" not in out


def test_render_keeps_populated_isbn(sample_metadata):
    out = render(_print_book(sample_metadata))

    assert "ISBN: 978-1-2345-6789-0" in out


@pytest.mark.parametrize(
    "publisher_text",
    [
        "Published by VTR Press",
        "VTR Press.",
        "VTR Press\nChennai, India",
    ],
)
def test_render_print_mode_does_not_sniff_copyright_text(
    sample_metadata,
    publisher_text,
):
    copyright_section = Section(
        kind=SectionKind.COPYRIGHT,
        title="Copyright",
        blocks=[
            Paragraph(children=[Text("First Edition - 2026")]),
            Paragraph(children=[Text(publisher_text)]),
            Paragraph(children=[Text("Copyright (c) 2026 Jane Doe.")]),
        ],
    )
    prologue = Section(
        kind=SectionKind.PROLOGUE,
        title="Prologue",
        blocks=[Paragraph(children=[Text("Prologue text.")])],
    )

    out = render(
        Book(metadata=sample_metadata, sections=[copyright_section, prologue]),
        options=RenderOptions(print_mode=True),
    )

    copyright_idx = out.index("#front-matter-page[")
    prologue_idx = out.index(")[Prologue]")
    copyright_page = out[copyright_idx:prologue_idx]

    assert publisher_text in copyright_page
    assert "#render-publisher-imprint()" not in copyright_page


def test_print_book_starts_main_matter_at_first_part(sample_metadata):
    out = render(
        _multi_part_print_book(sample_metadata),
        options=RenderOptions(print_mode=True),
    )

    contents_idx = out.index("#render-contents()")
    prologue_idx = out.index(")[Prologue]")
    main_matter_idx = out.index("#main-matter[")
    part_idx = out.index("= Part I - Foundations")

    assert contents_idx < prologue_idx < main_matter_idx < part_idx
    assert "#print-part-page[" in out


def test_print_book_uses_recto_breaks_for_parts_and_first_chapters(
    sample_metadata,
):
    out = render(
        _multi_part_print_book(sample_metadata),
        options=RenderOptions(print_mode=True),
    )
    lines = out.splitlines()

    part_lines = [
        i for i, line in enumerate(lines) if line == "#print-part-page["
    ]
    chapter_lines = [
        i for i, line in enumerate(lines) if line.startswith("#chapter-page(")
    ]
    recto_lines = [
        i for i, line in enumerate(lines)
        if line == "#blank-recto-pagebreak()"
    ]

    assert len(part_lines) == 2
    assert len(chapter_lines) == 3
    assert len(recto_lines) == 4

    for part_line in part_lines:
        assert max(i for i in recto_lines if i < part_line)

    assert max(i for i in recto_lines if i < chapter_lines[0]) > part_lines[0]
    assert max(i for i in recto_lines if i < chapter_lines[2]) > part_lines[1]
    assert not any(chapter_lines[0] < i < chapter_lines[1] for i in recto_lines)


def test_print_book_prologue_is_unnumbered_front_matter(sample_metadata):
    out = render(
        _multi_part_print_book(sample_metadata),
        options=RenderOptions(print_mode=True),
    )

    prologue_idx = out.index(")[Prologue]")
    main_matter_idx = out.index("#main-matter[")
    prologue_page_idx = out.rindex("#front-matter-page[", 0, prologue_idx)
    prologue_source = out[prologue_page_idx:main_matter_idx]

    assert "#front-matter-page[" in prologue_source
    assert "running-section-page" not in prologue_source
    assert "outlined: false" in prologue_source
    assert "== Prologue" not in prologue_source


def test_print_book_front_matter_headings_are_not_outlined(sample_metadata):
    out = render(
        _minimal_book(sample_metadata),
        options=RenderOptions(print_mode=True),
    )
    main_matter_idx = out.index("#main-matter[")
    front_matter_source = out[:main_matter_idx]

    assert "== Copyright" not in front_matter_source
    assert "== Prologue" not in front_matter_source
    assert front_matter_source.count("outlined: false") == 2


def test_recto_alignment_helpers_are_print_book_only(sample_metadata):
    normal_out = render(_multi_part_print_book(sample_metadata))
    technical_metadata = replace(sample_metadata, type="technical-document")
    technical_out = render(
        _technical_document_book(technical_metadata),
        options=RenderOptions(print_mode=True),
    )

    assert "#blank-recto-pagebreak()" not in normal_out
    assert "#print-part-page[" not in normal_out
    assert "#blank-recto-pagebreak()" not in technical_out
    assert "#print-part-page[" not in technical_out


# ============================================================================
# Subheading rendering
# ============================================================================

def test_subheading_renders_as_outlined_heading_at_its_level(sample_metadata):
    section = Section(
        kind=SectionKind.OTHER,
        title="Introduction",
        blocks=[
            Subheading(title="Purpose", level=3),
            Paragraph(children=[Text("Explains why.")]),
            Subheading(title="ADR-001", level=4),
        ],
    )
    book = Book(metadata=sample_metadata, sections=[section])

    out = render(book)

    assert "=== Purpose" in out
    assert "==== ADR-001" in out


# ============================================================================
# B1 -- Contents/main-matter trigger generalized to "first outlined section"
# ============================================================================

def _technical_document_book(metadata: Metadata) -> Book:
    """
    A technical-document-shaped book: ordinary (SectionKind.OTHER)
    sections only, no Prologue at all. Before this change, such a
    document never opened main-matter and never got a Contents page,
    because the trigger was hardcoded to SectionKind.PROLOGUE.
    """

    intro = Section(
        kind=SectionKind.OTHER,
        title="Introduction",
        blocks=[Paragraph(children=[Text("Intro text.")])],
    )
    overview = Section(
        kind=SectionKind.OTHER,
        title="System Overview",
        blocks=[Paragraph(children=[Text("Overview text.")])],
    )

    return Book(metadata=metadata, sections=[intro, overview])


def test_technical_document_without_prologue_gets_contents_and_main_matter(
    sample_metadata,
):
    out = render(_technical_document_book(sample_metadata))

    assert out.count("#render-contents()") == 1
    assert "#main-matter[" in out

    lines = out.splitlines()
    main_matter_idx = next(
        i for i, l in enumerate(lines) if l == "#main-matter["
    )
    contents_idx = next(
        i for i, l in enumerate(lines) if l == "#render-contents()"
    )
    intro_idx = next(
        i for i, l in enumerate(lines)
        if "running-section-page" in l and "Introduction" in l
    )

    # Contents, then main-matter opens, then the first section renders
    # inside it -- in that order.
    assert contents_idx < main_matter_idx < intro_idx


def test_book_with_front_matter_before_prologue_still_triggers_at_prologue(
    sample_metadata,
):
    """
    Regression guard for the exact real-world shape found in the
    RideTogether manuscript: a document type: book whose FIRST
    outlined section legitimately isn't Prologue (e.g. an ordinary
    section like "Document Philosophy" comes first). This must now
    open Contents/main-matter at that first outlined section, not
    silently wait for a Prologue that may come later or never.
    """

    document_philosophy = Section(
        kind=SectionKind.OTHER,
        title="Document Philosophy",
        blocks=[Paragraph(children=[Text("Philosophy text.")])],
    )
    prologue = Section(
        kind=SectionKind.PROLOGUE,
        title="Prologue",
        blocks=[Paragraph(children=[Text("Prologue text.")])],
    )

    book = Book(
        metadata=sample_metadata,
        sections=[document_philosophy, prologue],
    )

    out = render(book)

    assert out.count("#render-contents()") == 1

    lines = out.splitlines()
    main_matter_idx = next(
        i for i, l in enumerate(lines) if l == "#main-matter["
    )
    philosophy_idx = next(
        i for i, l in enumerate(lines)
        if "running-section-page" in l and "Document Philosophy" in l
    )

    # main-matter must open BEFORE the first outlined section, so that
    # section renders with correct (reset) page numbering rather than
    # the raw pre-main-matter counter.
    assert main_matter_idx < philosophy_idx


def test_copyright_dedication_thirukkural_still_precede_contents(
    sample_metadata,
):
    """
    Front-matter-kind sections (not outlined) must still render before
    Contents/main-matter opens -- confirms the "first outlined section"
    trigger doesn't accidentally fire on non-outlined sections.
    """

    out = render(_minimal_book(sample_metadata))

    lines = out.splitlines()
    copyright_idx = next(
        i for i, l in enumerate(lines) if "#front-matter-page[" in l
    )
    contents_idx = next(
        i for i, l in enumerate(lines) if l == "#render-contents()"
    )

    assert copyright_idx < contents_idx


# ============================================================================
# Contents pagebreak must not collide with the title page's own pagebreak
# ============================================================================

def test_contents_pagebreak_suppressed_when_nothing_precedes_it(
    sample_metadata,
):
    """
    When the very first section is also the one that triggers Contents
    (no front matter in between -- a technical document with no
    Prologue), the title page's own trailing #pagebreak() and
    _render_contents()'s leading pagebreak must not both fire: that
    produces two consecutive #pagebreak() calls with nothing rendered
    between them, which Typst then renders as an extra, empty page at
    its own default page size rather than the theme's.
    """

    out = render(_technical_document_book(sample_metadata))
    lines = out.splitlines()

    title_page_idx = next(
        i for i, l in enumerate(lines) if l == "#render-title-page("
    )
    contents_idx = next(
        i for i, l in enumerate(lines) if l == "#render-contents()"
    )

    between = [
        l for l in lines[title_page_idx:contents_idx] if l.strip()
    ]

    assert between.count("#pagebreak()") == 1


def test_contents_pagebreak_still_present_when_front_matter_precedes_it(
    sample_metadata,
):
    """
    For a book (front matter -- Copyright etc. -- before Contents),
    the pagebreak immediately before #render-contents() must still be
    emitted, exactly as before this fix.
    """

    out = render(_minimal_book(sample_metadata))
    lines = out.splitlines()

    contents_idx = next(
        i for i, l in enumerate(lines) if l == "#render-contents()"
    )

    # The nearest non-blank line before #render-contents() must be a
    # pagebreak -- Contents still gets its own page.
    preceding = next(
        l for l in reversed(lines[:contents_idx]) if l.strip()
    )
    assert preceding == "#pagebreak()"


# ============================================================================
# B2 -- cover only rendered for type: book (and only outside print mode)
# ============================================================================

def test_book_normal_mode_still_gets_cover(sample_metadata):
    """type: book (the default) is unaffected by this change."""

    out = render(_minimal_book(sample_metadata))

    assert "#render-cover(" in out


def test_technical_document_normal_mode_gets_no_cover(sample_metadata):
    """
    Non-print-mode rendering previously called render-cover()
    unconditionally. For a technical document, the theme's
    render-cover is a no-op, but the renderer's own trailing
    #pagebreak() still produced a genuinely blank leading page. The
    renderer must now skip the call entirely for this type.
    """

    technical_metadata = replace(sample_metadata, type="technical-document")
    out = render(_technical_document_book(technical_metadata))

    assert "#render-cover(" not in out


def test_technical_document_print_mode_still_gets_no_cover(sample_metadata):
    """Print mode already skipped cover for every type; must still."""

    technical_metadata = replace(sample_metadata, type="technical-document")
    out = render(
        _technical_document_book(technical_metadata),
        options=RenderOptions(print_mode=True),
    )

    assert "#render-cover(" not in out


# ============================================================================
# C1 -- automatic theme selection from metadata.type
# ============================================================================

def test_technical_document_type_selects_technical_theme(sample_metadata):
    technical_metadata = replace(sample_metadata, type="technical-document")
    out = render(_technical_document_book(technical_metadata))

    assert out.splitlines()[0] == '#import "../themes/technical/theme.typ": *'


def test_explicit_book_type_selects_classic_theme(sample_metadata):
    book_metadata = replace(sample_metadata, type="book")
    out = render(_minimal_book(book_metadata))

    assert out.splitlines()[0] == '#import "../themes/classic/theme.typ": *'


def test_omitted_type_defaults_to_classic_theme(sample_metadata):
    """
    metadata.type defaults to "book" (see model.py / VP-001), so a
    manuscript with no `type` field at all must resolve identically
    to an explicit `type: book` -- this is the path every existing
    manuscript actually relies on, not just the explicit-book case.
    """

    assert sample_metadata.type == "book"

    out = render(_minimal_book(sample_metadata))

    assert out.splitlines()[0] == '#import "../themes/classic/theme.typ": *'


def test_renderer_theme_lookup_still_falls_back_for_directly_constructed_metadata(
    sample_metadata,
):
    """
    Decision Log item 1 is now resolved: an unrecognized `type` must
    be a hard error -- but that validation lives at the parse
    boundary (parser/reader.py), the sole entry point for every real
    manuscript. renderer/typst.py's own THEME_IMPORT_BY_TYPE.get(...)
    fallback is intentionally left permissive below that boundary, so
    that a Metadata constructed directly (as this test, and any other
    test in this file, does -- bypassing the parser entirely) doesn't
    require every such fixture to use a supported type. This is not
    the "unknown type" user-facing behavior; that's covered in
    tests/test_reader.py.
    """

    unknown_metadata = replace(sample_metadata, type="white-paper")
    out = render(_minimal_book(unknown_metadata))

    assert out.splitlines()[0] == '#import "../themes/classic/theme.typ": *'


def test_theme_import_by_type_is_the_single_source_of_dispatch():
    """
    Guards against a future edit adding a second, inconsistent
    dispatch mechanism -- there should be exactly one place that maps
    type to theme.
    """

    assert THEME_IMPORT_BY_TYPE["book"] == "../themes/classic/theme.typ"
    assert (
        THEME_IMPORT_BY_TYPE["technical-document"]
        == "../themes/technical/theme.typ"
    )
