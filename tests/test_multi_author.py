"""
Regression coverage for multi-author metadata (BL-011 / v2.1).
"""

from __future__ import annotations

from io import BytesIO
import zipfile

import pytest

from exceptions import FrontMatterError
from model import (
    Book,
    Chapter,
    Metadata,
    Paragraph,
    Part,
    Scene,
    Section,
    SectionKind,
    Text,
)
from parser.reader import read
from renderer.epub import _book_uid, render as render_epub
from renderer.typst_book import render as render_typst


def _book(metadata: Metadata) -> Book:
    section = Section(
        kind=SectionKind.OTHER,
        title="Introduction",
        blocks=[Paragraph(children=[Text("Body text.")])],
    )
    return Book(metadata=metadata, sections=[section])


def test_single_author_scalar_remains_backward_compatible(write_manuscript):
    path = write_manuscript(
        "---\n"
        "title: T\n"
        "author: Jane Doe\n"
        "---\n"
        "Body\n"
    )

    metadata, _ = read(path)

    assert metadata.author == "Jane Doe"
    assert metadata.authors == ("Jane Doe",)


def test_multiple_authors_are_parsed_and_order_preserved(write_manuscript):
    path = write_manuscript(
        "---\n"
        "title: T\n"
        "author:\n"
        "  - Jane Doe\n"
        "  - John Doe\n"
        "  - Ravi Kumar\n"
        "---\n"
        "Body\n"
    )

    metadata, _ = read(path)

    assert metadata.author == ["Jane Doe", "John Doe", "Ravi Kumar"]
    assert metadata.authors == ("Jane Doe", "John Doe", "Ravi Kumar")


@pytest.mark.parametrize(
    "value",
    [
        "author: 123\n",
        "author:\n  - Jane Doe\n  - 123\n",
        "author:\n  - Jane Doe\n  - \"\"\n",
    ],
)
def test_invalid_author_metadata_is_rejected(write_manuscript, value):
    path = write_manuscript(
        "---\n"
        "title: T\n"
        + value
        + "---\n"
        "Body\n"
    )

    with pytest.raises(FrontMatterError, match="author"):
        read(path)


def test_typst_title_page_preserves_author_order():
    metadata = Metadata(
        title="College Project",
        author=["Ravi Kumar", "Arun", "Meena"],
        type="technical-document",
    )

    output = render_typst(_book(metadata))

    assert 'authors: ("Ravi Kumar", "Arun", "Meena"),' in output
    assert output.index('"Ravi Kumar"') < output.index('"Arun"') < output.index('"Meena"')


def test_typst_single_author_still_uses_authors_array():
    metadata = Metadata(title="Book", author="Jane Doe")

    output = render_typst(_book(metadata))

    assert 'authors: ("Jane Doe",),' in output


def test_epub_title_page_renders_each_author_separately():
    metadata = Metadata(
        title="College Project",
        author=["Ravi Kumar", "Arun", "Meena"],
    )

    data = render_epub(_book(metadata))
    zf = zipfile.ZipFile(BytesIO(data))
    title = zf.read("OEBPS/title.xhtml").decode("utf-8")

    assert '<p class="author">Ravi Kumar</p>' in title
    assert '<p class="author">Arun</p>' in title
    assert '<p class="author">Meena</p>' in title
    assert title.index("Ravi Kumar") < title.index("Arun") < title.index("Meena")


def test_epub_opf_contains_one_creator_per_author_in_order():
    metadata = Metadata(
        title="College Project",
        author=["Ravi Kumar", "Arun", "Meena"],
    )

    data = render_epub(_book(metadata))
    zf = zipfile.ZipFile(BytesIO(data))
    opf = zf.read("OEBPS/content.opf").decode("utf-8")

    creators = [
        '<dc:creator>Ravi Kumar</dc:creator>',
        '<dc:creator>Arun</dc:creator>',
        '<dc:creator>Meena</dc:creator>',
    ]

    positions = [opf.index(value) for value in creators]
    assert positions == sorted(positions)


def test_epub_uid_changes_when_author_order_changes():
    first = _book(
        Metadata(title="T", author=["First Author", "Second Author"])
    )
    second = _book(
        Metadata(title="T", author=["Second Author", "First Author"])
    )

    assert _book_uid(first) != _book_uid(second)
