"""
Parse inline Markdown into Inline AST nodes.

This module transforms Paragraph objects from plain Text nodes into
rich inline structures such as Bold, Italic, Code and Link.
"""

from __future__ import annotations

from model import (
    Book,
    Block,
    Paragraph,
    Part,
    Section,
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
                _walk_blocks(chapter.blocks)


def _walk_blocks(blocks: list[Block]) -> None:
    """Parse inline Markdown in all paragraph blocks."""

    for block in blocks:

        if not isinstance(block, Paragraph):
            continue

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