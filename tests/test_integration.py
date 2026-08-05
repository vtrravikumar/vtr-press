"""
End-to-end regression tests for the full publish pipeline
(reader -> structure -> inline -> renderers).
"""

from __future__ import annotations

import zipfile
from io import BytesIO

import pytest

from publish import publish, publish_all, publish_epub, read_book
from renderer.typst import RenderOptions
from renderer.typst import render as render_typst
from renderer.epub import render as render_epub
from model import Book, Metadata, Paragraph, Section, SectionKind, Text


def test_publish_produces_typst_source(valid_manuscript_path):
    typst_source = publish(valid_manuscript_path)

    assert typst_source.startswith('#import "../themes/classic/theme.typ": *')
    assert "The Sample Book" in typst_source


def test_publish_epub_produces_valid_zip(valid_manuscript_path, tmp_path):
    epub_bytes = publish_epub(valid_manuscript_path)

    zf = zipfile.ZipFile(BytesIO(epub_bytes))
    assert zf.testzip() is None


def test_publish_all_returns_consistent_typst_and_epub(valid_manuscript_path):
    typst_source, epub_bytes = publish_all(valid_manuscript_path)

    assert "The Sample Book" in typst_source
    zf = zipfile.ZipFile(BytesIO(epub_bytes))
    assert zf.testzip() is None


def test_publish_all_accepts_print_render_options(valid_manuscript_path):
    typst_source, epub_bytes = publish_all(
        valid_manuscript_path,
        render_options=RenderOptions(print_mode=True),
    )

    assert "#render-cover(" not in typst_source
    assert "show-publisher-logo: false" in typst_source

    zf = zipfile.ZipFile(BytesIO(epub_bytes))
    assert zf.testzip() is None


def test_read_book_builds_full_ast(valid_manuscript_path):
    book = read_book(valid_manuscript_path)

    assert book.metadata.title == "The Sample Book"
    assert len(book.sections) > 0


# ============================================================================
# Shipped example manuscript
# ============================================================================

def test_shipped_example_manuscript_parses(repo_root):
    """
    examples/sample-manuscript.md is meant to be a working demonstration
    of every supported manuscript feature, runnable via `publish()`.
    """

    example_path = repo_root / "examples" / "sample-manuscript.md"

    if not example_path.exists():
        pytest.skip("examples/sample-manuscript.md not found")

    # Should not raise.
    typst_source = publish(example_path)

    assert "The Sample Book" in typst_source


# ============================================================================
# Cross-renderer: BACK_COVER section (print-only marketing matter)
# ============================================================================

def test_back_cover_appears_in_typst_but_not_in_epub(sample_metadata):
    """
    The Back Cover section is required for print workflows (cover
    generation) but must never surface in the EPUB, which should end
    with the last real reading content (e.g. Epilogue / About the
    Author) instead.
    """

    epilogue = Section(
        kind=SectionKind.EPILOGUE,
        title="Epilogue",
        blocks=[Paragraph(children=[Text("Thank you for reading.")])],
    )
    back_cover = Section(
        kind=SectionKind.BACK_COVER,
        title="Back Cover",
        blocks=[Paragraph(children=[Text("A gripping tale of loss and hope.")])],
    )
    book = Book(metadata=sample_metadata, sections=[epilogue, back_cover])

    typst_source = render_typst(book)
    assert "#back-cover-page[" in typst_source

    epub_bytes = render_epub(book)
    zf = zipfile.ZipFile(BytesIO(epub_bytes))
    epub_text = b"".join(
        zf.read(n) for n in zf.namelist() if n.endswith(".xhtml")
    )

    assert b"Back Cover" not in epub_text
    assert b"A gripping tale of loss and hope." not in epub_text
    assert b"Thank you for reading." in epub_text
