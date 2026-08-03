"""
Regression tests for parser/reader.py.
"""

from __future__ import annotations

import pytest

from exceptions import FrontMatterError
from parser.reader import read


# ============================================================================
# Happy path
# ============================================================================

def test_reads_valid_front_matter(write_manuscript):
    path = write_manuscript(
        "---\n"
        "title: My Book\n"
        "subtitle: A Subtitle\n"
        "author: An Author\n"
        "edition: First Edition\n"
        'version: "2.0"\n'
        "copyright_year: 2025\n"
        "paper: a5\n"
        "language: en\n"
        "---\n"
        "\n"
        "## Prologue\n"
        "\n"
        "Body text.\n"
    )

    metadata, body = read(path)

    assert metadata.title == "My Book"
    assert metadata.subtitle == "A Subtitle"
    assert metadata.author == "An Author"
    assert metadata.edition == "First Edition"
    assert metadata.version == "2.0"
    assert metadata.paper == "a5"
    assert metadata.language == "en"
    assert body.startswith("## Prologue")


def test_copyright_year_is_coerced_to_string(write_manuscript):
    """copyright_year is often written as a bare YAML int; must come out as str."""

    path = write_manuscript(
        "---\ntitle: T\ncopyright_year: 2025\n---\nBody\n"
    )

    metadata, _ = read(path)

    assert metadata.copyright_year == "2025"
    assert isinstance(metadata.copyright_year, str)


def test_missing_front_matter_returns_default_metadata(write_manuscript):
    """A manuscript with no '---' delimiters is valid: defaults + full body."""

    path = write_manuscript("## Prologue\n\nJust body text, no front matter.\n")

    metadata, body = read(path)

    assert metadata.title == ""
    assert metadata.author == ""
    assert "Just body text" in body


def test_leading_html_comment_is_skipped(write_manuscript):
    path = write_manuscript(
        "<!-- editorial note -->\n"
        "---\n"
        "title: T\n"
        "---\n"
        "Body\n"
    )

    metadata, body = read(path)

    assert metadata.title == "T"
    assert body.strip() == "Body"


def test_multiple_leading_html_comments_are_skipped(write_manuscript):
    path = write_manuscript(
        "<!-- note one -->\n"
        "<!-- note two -->\n"
        "---\ntitle: T\n---\nBody\n"
    )

    metadata, body = read(path)

    assert metadata.title == "T"


def test_leading_whitespace_is_stripped(write_manuscript):
    path = write_manuscript("\n\n   ---\ntitle: T\n---\nBody\n")

    metadata, body = read(path)

    assert metadata.title == "T"


# ============================================================================
# Error handling
# ============================================================================

def test_missing_file_raises_file_not_found(tmp_path):
    missing = tmp_path / "does-not-exist.md"

    with pytest.raises(FileNotFoundError):
        read(missing)


def test_unterminated_html_comment_raises(write_manuscript):
    path = write_manuscript("<!-- never closed\n---\ntitle: T\n---\nBody\n")

    with pytest.raises(FrontMatterError):
        read(path)


def test_malformed_front_matter_missing_closing_delimiter_raises(write_manuscript):
    path = write_manuscript("---\ntitle: T\nno closing delimiter here\n")

    with pytest.raises(FrontMatterError):
        read(path)


def test_invalid_yaml_syntax_raises(write_manuscript):
    path = write_manuscript(
        "---\n"
        "title: [unclosed list\n"
        "---\n"
        "Body\n"
    )

    with pytest.raises(FrontMatterError):
        read(path)


def test_non_dict_yaml_front_matter_raises(write_manuscript):
    """A front matter block that parses to a list/scalar, not a mapping."""

    path = write_manuscript(
        "---\n"
        "- just\n"
        "- a\n"
        "- list\n"
        "---\n"
        "Body\n"
    )

    with pytest.raises(FrontMatterError):
        read(path)


def test_empty_front_matter_block_returns_default_metadata(write_manuscript):
    """An empty '---\\n---\\n' block is valid YAML (None) and should not crash."""

    path = write_manuscript("---\n---\nBody\n")

    metadata, body = read(path)

    assert metadata.title == ""
    assert body.strip() == "Body"
