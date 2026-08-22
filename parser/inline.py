"""
Parse inline Markdown into Inline AST nodes.

This module transforms Paragraph objects from plain Text nodes into
rich inline structures such as Bold, Italic, Code and Link.
"""

from __future__ import annotations

from model import (
    Book,
    Document,
    Block,
    ListBlock,
    ListItem,
    Paragraph,
    Part,
    Section,
    Table,
    TableCell,
    Text,
    Bold,
    Italic,
    Code,
    Link,
)


def parse_inline(book: Book) -> None:
    """Parse inline Markdown throughout the document."""

    for item in book.sections:

        if isinstance(item, Section):
            _walk_blocks(item.blocks)

        elif isinstance(item, Part):
            for chapter in item.chapters:
                for scene in chapter.scenes:
                    _walk_blocks(scene.blocks)


def parse_inline_document(document: Document) -> None:
    """Parse inline Markdown throughout a generic Document."""
    _walk_blocks(document.blocks)


def _walk_blocks(blocks: list[Block]) -> None:
    """Parse inline Markdown in all paragraph blocks."""

    for block in blocks:

        if isinstance(block, ListBlock):
            for item in block.items:
                _walk_inlines(item)
            continue

        if isinstance(block, Table):
            for cell in block.header.cells:
                _walk_inlines(cell)
            for row in block.rows:
                for cell in row.cells:
                    _walk_inlines(cell)
            continue

        if not isinstance(block, Paragraph):
            continue

        _walk_inlines(block)


def _walk_inlines(block: Paragraph | ListItem | TableCell) -> None:
    """Parse inline Markdown in a paragraph or list item."""

    new_children = []

    for child in block.children:
        if isinstance(child, Text):
            new_children.extend(_expand(child.text))
        else:
            new_children.append(child)

    block.children = new_children


def _expand(text: str):
    """Expand one Markdown string into Inline nodes."""

    result = []
    buffer = []

    i = 0
    n = len(text)

    def flush():
        if buffer:
            result.append(Text("".join(buffer)))
            buffer.clear()

    while i < n:

        # ----------------------------------------------------------
        # Bold
        # ----------------------------------------------------------

        if text.startswith("**", i):

            end = text.find("**", i + 2)

            if end != -1:

                flush()

                result.append(
                    Bold(
                        children=[
                            Text(text[i + 2:end])
                        ]
                    )
                )

                i = end + 2
                continue

        # ----------------------------------------------------------
        # Italic
        # ----------------------------------------------------------

        if text[i] == "*":

            end = text.find("*", i + 1)

            if end != -1:

                flush()

                result.append(
                    Italic(
                        children=[
                            Text(text[i + 1:end])
                        ]
                    )
                )

                i = end + 1
                continue

        # ----------------------------------------------------------
        # Code
        # ----------------------------------------------------------

        if text[i] == "`":

            end = text.find("`", i + 1)

            if end != -1:

                flush()

                result.append(
                    Code(
                        text=text[i + 1:end]
                    )
                )

                i = end + 1
                continue

        # ----------------------------------------------------------
        # Link
        # ----------------------------------------------------------

        if text[i] == "[":

            close = text.find("]", i + 1)

            if (
                close != -1
                and close + 1 < n
                and text[close + 1] == "("
            ):

                end = text.find(")", close + 2)

                if end != -1:

                    flush()

                    result.append(
                        Link(
                            text=text[i + 1:close],
                            url=text[close + 2:end],
                        )
                    )

                    i = end + 1
                    continue

        buffer.append(text[i])
        i += 1

    flush()

    return result
