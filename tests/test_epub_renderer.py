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

def test_back_cover_section_still_renders_a_heading_in_epub(sample_metadata, tiny_cover):
    """
    Documents a current asymmetry: the Typst renderer suppresses the
    heading for SectionKind.BACK_COVER (see test_typst_renderer.py),
    but the EPUB renderer has no special case for it and renders the
    normal '<h2>{title}</h2>' like any other section.

    If EPUB gains a matching special case, update this test alongside
    the change -- don't just delete it.
    """

    data = render(_minimal_book(sample_metadata), tiny_cover)
    zf = zipfile.ZipFile(BytesIO(data))

    back_cover_html = b"".join(
        zf.read(n)
        for n in zf.namelist()
        if n.endswith(".xhtml") and b"Back cover blurb" in zf.read(n)
    )

    assert b"<h2>Back Cover</h2>" in back_cover_html
