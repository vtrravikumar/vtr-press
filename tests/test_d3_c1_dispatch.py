"""D3-C1 tests for production dispatch to the generic Typst pipeline."""

from pathlib import Path

from publish import publish
from parser.document_model import parse_document
from parser.inline import parse_inline_document
from model import Metadata, Paragraph, Bold


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


def test_generic_inline_parser_preserves_bold():
    metadata = Metadata(title="T", type="technical-document")
    document = parse_document(
        metadata,
        "## Introduction\n\nThis is **bold** text.",
    )
    parse_inline_document(document)

    paragraph = document.blocks[1]
    assert isinstance(paragraph, Paragraph)
    assert any(isinstance(child, Bold) for child in paragraph.children)


def test_publish_routes_technical_document_to_generic_typst(tmp_path):
    path = _technical_path(tmp_path)

    output = publish(path)

    assert '#import "../themes/technical/theme.typ": *' in output
    assert "== Introduction" in output
    assert "=== Purpose" in output
    assert "#render-contents()" in output


def test_publish_routes_markdown_table_to_native_typst_table(tmp_path):
    path = tmp_path / "technical-table.md"
    path.write_text(
        """---
title: Test Technical Document
subtitle: Architecture
author: VTR Ravi Kumar
type: technical-document
---

# Test Technical Document

## Revision History

| Version | Status | Amount |
|:--------|:------:|-------:|
| 0.1     | Draft  | 100    |
| 1.0     | Done   | 250    |
""",
        encoding="utf-8",
    )

    output = publish(path)

    assert "#table(" in output
    assert "  align: (left, center, right)," in output
    assert "    [Version]," in output
    assert "  [Draft]," in output
    assert "  [250]," in output


def test_book_dispatch_remains_legacy(tmp_path):
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

    output = publish(path)

    assert '#import "../themes/classic/theme.typ": *' in output
    assert '#import "../themes/technical/theme.typ": *' not in output
