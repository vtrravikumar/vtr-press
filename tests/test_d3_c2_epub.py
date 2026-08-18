"""D3-C2 tests for the native technical-document EPUB path."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from publish import publish_all, publish_epub


def _technical_path(tmp_path: Path) -> Path:
    path = tmp_path / "technical.md"
    path.write_text(
        """---
title: Test Technical Document
subtitle: Architecture
author: VTR Ravi Kumar
type: technical-document
---

# Test Technical Document

## Introduction

This is **bold** text.

### Purpose

This is the purpose.

## Architecture

Architecture details.
""",
        encoding="utf-8",
    )
    return path


def test_publish_epub_technical_document_uses_generic_path(tmp_path):
    epub = publish_epub(_technical_path(tmp_path))

    with ZipFile(BytesIO(epub)) as archive:
        names = set(archive.namelist())
        nav = archive.read("OEBPS/nav.xhtml").decode("utf-8")
        opf = archive.read("OEBPS/content.opf").decode("utf-8")
        introduction = archive.read(
            "OEBPS/section-001.xhtml"
        ).decode("utf-8")

    assert "OEBPS/contents.xhtml" in names
    assert "Introduction" in nav
    assert "Architecture" in nav
    assert "cover-image" not in opf
    assert "OEBPS/images/cover" not in names
    assert "<strong>bold</strong>" in introduction


def test_publish_all_technical_document_uses_generic_epub(tmp_path):
    typst, epub = publish_all(_technical_path(tmp_path))

    assert "technical/theme.typ" in typst

    with ZipFile(BytesIO(epub)) as archive:
        opf = archive.read("OEBPS/content.opf").decode("utf-8")
        assert "cover-image" not in opf
        assert "OEBPS/contents.xhtml" in archive.namelist()


def test_book_epub_path_remains_legacy(tmp_path):
    path = tmp_path / "book.md"
    path.write_text(
        """---
title: Test Book
type: book
---

## Prologue

A book document.
""",
        encoding="utf-8",
    )

    epub = publish_epub(path)

    with ZipFile(BytesIO(epub)) as archive:
        assert "OEBPS/cover.xhtml" in archive.namelist()
        assert "OEBPS/title.xhtml" in archive.namelist()
