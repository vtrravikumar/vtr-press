"""
Shared fixtures for the VTR Press regression test suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from model import Metadata


# ============================================================================
# Manuscript text fixtures
# ============================================================================

# NOTE: heading levels here are deliberately chosen to match what
# parser/structure.py actually expects:
#   "# "    -> book title (ignored; title comes from front matter)
#   "## "   -> Part / Section
#   "### "  -> Chapter
#   "#### " -> Scene
# This is ONE LEVEL DEEPER than the headings used in the shipped
# examples/sample-manuscript.md, which is why that file currently
# fails to parse (see test_integration.py::test_shipped_example_manuscript_parses).
VALID_MANUSCRIPT_BODY = """\
## Copyright

Copyright (c) 2026 Jane Doe.

All rights reserved.

## Dedication

For everyone who loves books.

## Thirukkural

akara mudala ezhuthellaam.

*As the letter A is the first of all letters.*

## Prologue

This sample manuscript demonstrates the supported features of VTR Press.

## Part I - Getting Started

### Chapter 1 - Welcome

#### First Scene

This is a normal paragraph.

This paragraph contains **bold text**.

This paragraph contains *italic text*.

This paragraph contains `inline code`.

Visit [VTR Press](https://github.com/example/vtr-press).

:::verse
Roses are red.
Violets are blue.
Books are forever.
:::

Another paragraph.

### Chapter 2 - A Second Chapter

#### Another Scene

Scenes can contain multiple paragraphs.

This one has no explicit heading before it in the next chapter.

### Chapter 3 - No Explicit Scene

This chapter has no #### scene heading at all, so an
untitled scene should be created automatically.

## Epilogue

Thank you for reading.

## About the Author

Jane Doe is a fictional author used for testing.

## Back Cover

This text should appear on the back cover.
"""

VALID_FRONT_MATTER = """\
---
title: The Sample Book
subtitle: A VTR Press Demonstration
author: Jane Doe
edition: First Edition
version: "1.0"
copyright_year: 2026
language: en
---
"""


@pytest.fixture
def valid_manuscript_text() -> str:
    """Full manuscript text (front matter + body) that should parse cleanly."""

    return VALID_FRONT_MATTER + "\n" + VALID_MANUSCRIPT_BODY


@pytest.fixture
def valid_manuscript_path(tmp_path: Path, valid_manuscript_text: str) -> Path:
    """Write the valid manuscript fixture to disk and return its path."""

    path = tmp_path / "manuscript.md"
    path.write_text(valid_manuscript_text, encoding="utf-8")
    return path


@pytest.fixture
def write_manuscript(tmp_path: Path):
    """Factory fixture: write arbitrary manuscript text to a temp file."""

    def _write(text: str, name: str = "manuscript.md") -> Path:
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def sample_metadata() -> Metadata:
    """A representative Metadata instance for renderer-level tests."""

    return Metadata(
        title="The Sample Book",
        subtitle="A VTR Press Demonstration",
        author="Jane Doe",
        edition="First Edition",
        version="1.0",
        copyright_year="2026",
        language="en",
    )


@pytest.fixture
def repo_root() -> Path:
    """Path to the repository root (parent of the tests/ directory)."""

    return Path(__file__).resolve().parent.parent
