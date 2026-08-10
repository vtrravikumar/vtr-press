"""
Regression tests for renderer/epub.py.

These tests inspect the produced .epub (a zip archive) structurally,
without needing any external EPUB-reading tool.
"""

from __future__ import annotations

import base64
import zipfile
from io import BytesIO

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
from renderer.epub import _attr, _text, render


# A minimal valid 1x1 transparent PNG, so tests don't depend on the
# real repo assets (which may be large, missing, or change over time).
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture
def tiny_cover(tmp_path):
    path = tmp_path / "cover.png"
    path.write_bytes(_TINY_PNG)
    return path


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


# ============================================================================
# Package structure
# ============================================================================

def test_render_produces_a_valid_zip(sample_metadata, tiny_cover):
    data = render(_minimal_book(sample_metadata), tiny_cover)

    zf = zipfile.ZipFile(BytesIO(data))
    assert zf.testzip() is None  # None means no corrupt entries


def test_mimetype_is_first_entry_and_uncompressed(sample_metadata, tiny_cover):
    data = render(_minimal_book(sample_metadata), tiny_cover)

    zf = zipfile.ZipFile(BytesIO(data))
    infos = zf.infolist()

    assert infos[0].filename == "mimetype"
    assert infos[0].compress_type == zipfile.ZIP_STORED
    assert zf.read("mimetype") == b"application/epub+zip"


def test_container_xml_references_opf(sample_metadata, tiny_cover):
    data = render(_minimal_book(sample_metadata), tiny_cover)

    zf = zipfile.ZipFile(BytesIO(data))
    container = zf.read("META-INF/container.xml").decode("utf-8")

    assert "rootfile" in container
    assert ".opf" in container


def test_opf_main_title_is_explicitly_refined_as_main(sample_metadata, tiny_cover):
    """
    Kindle Previewer (E20006/E21011) rejects an OPF with more than one
    dc:title unless one of them is explicitly refined with
    title-type="main". The subtitle was already refined as "subtitle";
    the main title must be refined as "main" the same way, or Kindle
    Previewer can't tell which dc:title is the actual book title.
    """

    data = render(_minimal_book(sample_metadata), tiny_cover)

    zf = zipfile.ZipFile(BytesIO(data))
    opf = zf.read("OEBPS/content.opf").decode("utf-8")

    assert '<dc:title id="title">' in opf
    assert (
        '<meta property="title-type" refines="#title">main</meta>' in opf
    )

    # The refines target must actually match the title element's id --
    # not just happen to contain the right substrings independently.
    title_idx = opf.index('<dc:title id="title">')
    refines_idx = opf.index(
        '<meta property="title-type" refines="#title">main</meta>'
    )
    assert refines_idx > title_idx


def test_opf_subtitle_is_still_refined_as_subtitle(sample_metadata, tiny_cover):
    """Guards the existing, correct subtitle behavior against regression
    while fixing the main title -- both must be able to coexist."""

    data = render(_minimal_book(sample_metadata), tiny_cover)

    zf = zipfile.ZipFile(BytesIO(data))
    opf = zf.read("OEBPS/content.opf").decode("utf-8")

    assert '<dc:title id="subtitle">' in opf
    assert (
        '<meta property="title-type" refines="#subtitle">subtitle</meta>'
        in opf
    )


def test_render_without_cover_file_does_not_crash(sample_metadata, tmp_path):
    """Missing cover/logo files must degrade gracefully, not raise."""

    missing_cover = tmp_path / "does-not-exist.png"

    data = render(_minimal_book(sample_metadata), missing_cover)

    zf = zipfile.ZipFile(BytesIO(data))
    assert zf.testzip() is None


# ============================================================================
# HTML escaping
# ============================================================================

def test_text_helper_escapes_html_special_characters():
    assert _text("Tom & Jerry <3") == "Tom &amp; Jerry &lt;3"


def test_attr_helper_escapes_quotes_for_attributes():
    out = _attr('a "quoted" value')

    assert '"' not in out.replace("&quot;", "")


def test_section_title_with_ampersand_is_escaped(sample_metadata, tiny_cover):
    book = _minimal_book(sample_metadata)
    book.sections[1].title = "Prologue & Preface"

    data = render(book, tiny_cover)
    zf = zipfile.ZipFile(BytesIO(data))

    matches = [n for n in zf.namelist() if n.startswith("OEBPS/front-") or "front" in n]
    found_escaped = any(
        b"Prologue &amp; Preface" in zf.read(n)
        for n in zf.namelist()
        if n.endswith(".xhtml")
    )
    assert found_escaped


def test_link_href_is_attribute_escaped(sample_metadata, tiny_cover):
    book = _minimal_book(sample_metadata)
    book.sections[2].chapters[0].scenes[0].blocks[0] = Paragraph(
        children=[Link(text="click", url='https://example.com/"onmouseover="evil')]
    )

    data = render(book, tiny_cover)
    zf = zipfile.ZipFile(BytesIO(data))

    chapter_html = b"".join(
        zf.read(n) for n in zf.namelist() if "chapter-001" in n
    )

    assert b'onmouseover="evil"' not in chapter_html
    assert b"&quot;onmouseover=&quot;evil" in chapter_html


# ============================================================================
# Cross-renderer note: BACK_COVER section
# ============================================================================

def test_back_cover_section_is_omitted_from_epub(sample_metadata, tiny_cover):
    """
    The Back Cover section is print-only marketing matter (see
    renderer/typst.py, which still renders it via #back-cover-page[).
    The EPUB must omit it entirely: no heading, no body text, and no
    stray empty page in the reading order.
    """

    data = render(_minimal_book(sample_metadata), tiny_cover)
    zf = zipfile.ZipFile(BytesIO(data))

    all_text = b"".join(
        zf.read(n) for n in zf.namelist() if n.endswith(".xhtml")
    )

    assert b"Back Cover" not in all_text
    assert b"Back cover blurb." not in all_text


def test_back_cover_omission_leaves_no_empty_document_in_spine(
    sample_metadata, tiny_cover
):
    """
    Omitting the Back Cover section must remove it from the spine
    entirely -- not leave behind an empty chapter/page placeholder.
    """

    with_back_cover = render(_minimal_book(sample_metadata), tiny_cover)

    prologue_only_book = _minimal_book(sample_metadata)
    prologue_only_book.sections = [
        section
        for section in prologue_only_book.sections
        if not isinstance(section, Section)
        or section.kind != SectionKind.BACK_COVER
    ]
    without_back_cover_section = render(prologue_only_book, tiny_cover)

    zf_with = zipfile.ZipFile(BytesIO(with_back_cover))
    zf_without = zipfile.ZipFile(BytesIO(without_back_cover_section))

    docs_with = [n for n in zf_with.namelist() if n.endswith(".xhtml")]
    docs_without = [n for n in zf_without.namelist() if n.endswith(".xhtml")]

    # A book with a Back Cover section (skipped by the renderer) must
    # produce the exact same set of documents as a book that never had
    # one -- proving nothing is rendered in its place.
    assert docs_with == docs_without


def test_empty_isbn_placeholder_is_omitted(sample_metadata, tiny_cover):
    book = _minimal_book(sample_metadata)
    book.sections[0].blocks.append(Paragraph(children=[Text("ISBN:")]))

    data = render(book, tiny_cover)
    zf = zipfile.ZipFile(BytesIO(data))
    all_text = b"".join(
        zf.read(n) for n in zf.namelist() if n.endswith(".xhtml")
    )

    assert b"All rights reserved." in all_text
    assert b"ISBN:" not in all_text


def test_populated_isbn_is_kept(sample_metadata, tiny_cover):
    book = _minimal_book(sample_metadata)
    book.sections[0].blocks.append(
        Paragraph(children=[Text("ISBN: 978-1-2345-6789-0")])
    )

    data = render(book, tiny_cover)
    zf = zipfile.ZipFile(BytesIO(data))
    all_text = b"".join(
        zf.read(n) for n in zf.namelist() if n.endswith(".xhtml")
    )

    assert b"ISBN: 978-1-2345-6789-0" in all_text


# ============================================================================
# Subheading rendering
# ============================================================================

def test_subheading_renders_as_matching_heading_level(sample_metadata, tiny_cover):
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

    data = render(book, tiny_cover)
    zf = zipfile.ZipFile(BytesIO(data))
    all_text = b"".join(
        zf.read(n) for n in zf.namelist() if n.endswith(".xhtml")
    )

    assert b"<h3>Purpose</h3>" in all_text
    assert b"<h4>ADR-001</h4>" in all_text
