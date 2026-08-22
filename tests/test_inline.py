"""
Regression tests for parser/inline.py.

These tests exercise the hand-rolled inline scanner directly via
`_expand`, plus `parse_inline` end-to-end against a Book.
"""

from __future__ import annotations

from model import (
    Bold,
    Book,
    Chapter,
    Code,
    Document,
    Italic,
    Link,
    ListBlock,
    ListItem,
    Metadata,
    Paragraph,
    Part,
    Scene,
    Section,
    SectionKind,
    Table,
    TableAlignment,
    TableCell,
    TableRow,
    Text,
)
from parser.inline import _expand, parse_inline, parse_inline_document


# ============================================================================
# _expand: individual markers
# ============================================================================

def test_plain_text_is_untouched():
    nodes = _expand("just plain text")

    assert len(nodes) == 1
    assert isinstance(nodes[0], Text)
    assert nodes[0].text == "just plain text"


def test_bold_is_extracted():
    nodes = _expand("before **bold** after")

    assert [type(n) for n in nodes] == [Text, Bold, Text]
    assert nodes[0].text == "before "
    assert nodes[1].children[0].text == "bold"
    assert nodes[2].text == " after"


def test_italic_is_extracted():
    nodes = _expand("before *italic* after")

    assert [type(n) for n in nodes] == [Text, Italic, Text]
    assert nodes[1].children[0].text == "italic"


def test_inline_code_is_extracted():
    nodes = _expand("before `code` after")

    assert [type(n) for n in nodes] == [Text, Code, Text]
    assert nodes[1].text == "code"


def test_link_is_extracted():
    nodes = _expand("see [VTR Press](https://example.com) here")

    assert [type(n) for n in nodes] == [Text, Link, Text]
    assert nodes[1].text == "VTR Press"
    assert nodes[1].url == "https://example.com"


def test_multiple_markers_in_sequence():
    nodes = _expand("**b** and *i* and `c`")

    assert [type(n) for n in nodes] == [Bold, Text, Italic, Text, Code]


# ============================================================================
# _expand: known limitations (pin current behavior so changes are deliberate)
# ============================================================================

def test_unterminated_bold_marker_falls_through_to_empty_italic():
    """
    Known quirk: when '**' has no closing pair, the bold check fails
    and falls through to the italic check at the SAME position, which
    then finds the second '*' of the pair as its own closer. The net
    result is an empty Italic node swallowing both asterisks, not a
    literal '**' in the output. This is surprising but is the current
    behavior -- pin it so a future refactor doesn't silently change it
    without a conscious decision either way.
    """

    nodes = _expand("this has **no closing marker")

    assert [type(n) for n in nodes] == [Text, Italic, Text]
    assert nodes[0].text == "this has "
    assert nodes[1].children[0].text == ""
    assert nodes[2].text == "no closing marker"


def test_unterminated_link_bracket_is_literal():
    nodes = _expand("a [broken link with no closing")

    assert len(nodes) == 1
    assert isinstance(nodes[0], Text)
    assert nodes[0].text == "a [broken link with no closing"


def test_nested_inline_does_not_actually_nest():
    """
    Known limitation: the scanner does not recursively parse inside
    Bold/Italic, so italics inside bold stay as literal asterisks.
    If this test starts failing because nesting was implemented,
    update it (that would be a real improvement, not a regression).
    """

    nodes = _expand("**bold with *italic* inside**")

    assert len(nodes) == 1
    assert isinstance(nodes[0], Bold)
    assert nodes[0].children[0].text == "bold with *italic* inside"


def test_no_backslash_escape_mechanism():
    """
    Known limitation: there is no backslash-escape syntax, so a
    literal '\\*' does not suppress italic parsing.
    """

    nodes = _expand(r"a \*not italic\* here")

    # The backslash is preserved verbatim and '*...*' is still parsed as italic.
    assert any(isinstance(n, Italic) for n in nodes)


# ============================================================================
# parse_inline: end-to-end over a Book
# ============================================================================

def _book_with_paragraph(text: str) -> Book:
    section = Section(
        kind=SectionKind.PROLOGUE,
        title="Prologue",
        blocks=[Paragraph(children=[Text(text)])],
    )
    return Book(metadata=Metadata(), sections=[section])


def test_parse_inline_expands_section_paragraphs():
    book = _book_with_paragraph("Some **bold** text.")

    parse_inline(book)

    children = book.sections[0].blocks[0].children
    assert any(isinstance(c, Bold) for c in children)


def test_parse_inline_expands_chapter_scene_paragraphs():
    chapter = Chapter(
        number=1,
        title="Chapter 1",
        scenes=[
            Scene(
                title=None,
                blocks=[Paragraph(children=[Text("Some *italic* text.")])],
            )
        ],
    )
    part = Part(title="Part I", chapters=[chapter])
    book = Book(metadata=Metadata(), sections=[part])

    parse_inline(book)

    children = book.sections[0].chapters[0].scenes[0].blocks[0].children
    assert any(isinstance(c, Italic) for c in children)


def test_parse_inline_expands_list_item_text():
    document = Document(
        metadata=Metadata(type="technical-document"),
        blocks=[
            ListBlock(
                items=[
                    ListItem(children=[Text("Some **bold** text.")]),
                ]
            )
        ],
    )

    parse_inline_document(document)

    children = document.blocks[0].items[0].children
    assert any(isinstance(c, Bold) for c in children)


def test_parse_inline_expands_table_cell_text():
    document = Document(
        metadata=Metadata(type="technical-document"),
        blocks=[
            Table(
                alignments=[TableAlignment.LEFT],
                header=TableRow(
                    cells=[TableCell(children=[Text("Status")])]
                ),
                rows=[
                    TableRow(
                        cells=[
                            TableCell(children=[Text("Some **bold** text.")])
                        ]
                    )
                ],
            )
        ],
    )

    parse_inline_document(document)

    children = document.blocks[0].rows[0].cells[0].children
    assert any(isinstance(c, Bold) for c in children)


def test_parse_inline_is_idempotent():
    """
    Calling parse_inline twice on the same Book must not double-expand
    or corrupt already-expanded nodes, since already-built Bold/Italic/
    Code/Link nodes are left untouched by the walker.
    """

    book = _book_with_paragraph("A **bold** and *italic* and `code` and "
                                 "[a link](https://example.com).")

    parse_inline(book)
    first_pass = list(book.sections[0].blocks[0].children)

    parse_inline(book)
    second_pass = book.sections[0].blocks[0].children

    assert [type(n) for n in first_pass] == [type(n) for n in second_pass]
    assert len(first_pass) == len(second_pass)
