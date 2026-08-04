"""
Regression tests for renderer/typst.py.

These tests inspect the generated Typst *source text*. They do not
require the `typst` binary and do not compile anything -- they lock
in the string-level contract between the Python renderer and the
themes/classic/*.typ templates.
"""

from __future__ import annotations

import re

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
    Text,
)
from renderer.typst import RenderOptions, _Renderer, render


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
            Paragraph(children=[Text("Published by")]),
            Paragraph(children=[Text("VTR Press\nChennai, India")]),
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
    assert "Published by" in out
    assert "VTR Press" in out


def test_render_print_mode_skips_cover_and_hides_title_page_logo(sample_metadata):
    out = render(
        _print_book(sample_metadata),
        options=RenderOptions(print_mode=True),
    )

    assert "#render-cover(" not in out
    assert "#back-cover-page[" not in out
    assert "show-publisher-logo: false" in out


def test_render_print_mode_removes_only_copyright_publisher_branding(sample_metadata):
    out = render(
        _print_book(sample_metadata),
        options=RenderOptions(print_mode=True),
    )
    copyright_idx = out.index("#front-matter-page[")
    prologue_idx = out.index("running-section-page")
    copyright_page = out[copyright_idx:prologue_idx]

    assert "Published by" not in copyright_page
    assert "VTR Press" not in copyright_page
    assert "Chennai, India" not in copyright_page
    assert "Copyright (c) 2026 Jane Doe." in copyright_page
    assert "ISBN: 978-1-2345-6789-0" in copyright_page
