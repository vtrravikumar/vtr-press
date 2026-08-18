"""
Build the generic Document Model from Markdown (Phase D, D2).

Unlike parser/structure.py, this module has no concept of Part,
Chapter, Scene, or Section -- it doesn't need one. Per
docs/DOCUMENT_MODEL_DESIGN.md: the parser describes what the author
wrote (a heading's level and title), not what that heading means.
Deciding whether a level-2 heading is a Part, a Section, or a
Copyright page is interpretation's job (see interpretation.py), not
this module's.

This is a second, parallel parsing path. It does not replace, modify,
or share any state with parser/structure.py, which continues to
handle `type: book` manuscripts entirely unchanged. Nothing in the
current publishing pipeline (publish.py, run.py) calls into this
module yet -- wiring `type: technical-document` to use it is D3, not
D2.
"""

from __future__ import annotations

import re

from exceptions import StructureError
from model import (
    Document,
    Heading,
    Image,
    ListBlock,
    ListItem,
    Metadata,
    Paragraph,
    Text,
    Verse,
)


# Any Markdown ATX heading, level 1-6 (standard CommonMark depth) --
# not capped at 4 the way parser/structure.py's explicit "## "/"### "/
# "#### " checks are, since this parser assigns no meaning to depth
# and has no reason to reject a heading level it doesn't recognize.
_HEADING_PATTERN = re.compile(r"^(#{1,6}) (.*)$")
_UNORDERED_LIST_PATTERN = re.compile(r"^\s*[-*+] (.+)$")
_ORDERED_LIST_PATTERN = re.compile(r"^\s*(\d+)\. (.+)$")
_IMAGE_PATTERN = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")


def parse_document(metadata: Metadata, body: str) -> Document:
    """
    Parse the Markdown body into a generic, flat Document.

    Recognizes exactly the same manuscript-level syntax
    parser/structure.py does -- headings, blank-line-delimited
    paragraphs, and :::verse::: fenced blocks -- but assigns no
    semantic meaning to any of it: every heading becomes an ordinary
    Heading(level, title) in document order.

    Notably, a "# Title" line is NOT discarded here the way
    parser/structure.py discards it (which assumes the title always
    comes from front matter). It becomes an ordinary
    Heading(level=1, ...), like any other heading -- whether a given
    document type's conventions ignore the first heading is an
    interpretation-layer decision, not a parsing fact.

    Parameters
    ----------
    metadata
        Already-parsed manuscript metadata (see parser/reader.py).
    body
        The Markdown body, front matter already stripped.

    Returns
    -------
    Document
        A flat, ordered Document -- no recursive nesting.

    Raises
    ------
    StructureError
        If a :::verse block is never closed. This is a syntax error
        (an unclosed fence), not a semantic one, so it stays a
        parser-level concern exactly as it does in
        parser/structure.py.
    """

    document = Document(metadata=metadata)

    paragraph: list[str] = []
    verse: list[str] = []
    list_items: list[ListItem] = []
    list_ordered = False
    in_verse = False

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def flush_paragraph() -> None:
        nonlocal paragraph

        if not paragraph:
            return

        text = "\n".join(paragraph).strip()
        paragraph = []

        if not text:
            return

        document.blocks.append(Paragraph(children=[Text(text=text)]))

    def flush_verse() -> None:
        nonlocal verse

        if not verse:
            return

        document.blocks.append(Verse(lines=verse.copy()))
        verse.clear()

    def flush_list() -> None:
        nonlocal list_items

        if not list_items:
            return

        document.blocks.append(
            ListBlock(ordered=list_ordered, items=list_items.copy())
        )
        list_items.clear()

    # ----------------------------------------------------------
    # Parse document
    # ----------------------------------------------------------

    for raw_line in body.splitlines():

        line = raw_line.rstrip()

        # ----------------------------------------------------------
        # Verse block
        # ----------------------------------------------------------

        if line == ":::verse":
            flush_paragraph()
            in_verse = True
            verse.clear()
            continue

        if line == ":::" and in_verse:
            flush_verse()
            verse.clear()
            in_verse = False
            continue

        if in_verse:
            verse.append(line)
            continue

        # ----------------------------------------------------------
        # Blank line
        # ----------------------------------------------------------

        if not line:
            flush_paragraph()
            flush_list()
            continue

        # ----------------------------------------------------------
        # Heading -- any level, no semantic branching whatsoever
        # ----------------------------------------------------------

        match = _HEADING_PATTERN.match(line)

        if match:
            flush_paragraph()
            flush_list()
            flush_verse()

            level = len(match.group(1))
            title = match.group(2).strip()

            document.blocks.append(Heading(level=level, title=title))
            continue

        # ----------------------------------------------------------
        # Image
        # ----------------------------------------------------------

        image_match = _IMAGE_PATTERN.match(line)

        if image_match:
            flush_paragraph()
            flush_list()
            flush_verse()

            document.blocks.append(
                Image(
                    alt_text=image_match.group(1),
                    source=image_match.group(2),
                )
            )
            continue

        # ----------------------------------------------------------
        # Markdown list
        # ----------------------------------------------------------

        unordered_match = _UNORDERED_LIST_PATTERN.match(line)
        ordered_match = _ORDERED_LIST_PATTERN.match(line)

        if unordered_match or ordered_match:
            flush_paragraph()
            flush_verse()

            ordered = ordered_match is not None
            item_text = (
                ordered_match.group(2)
                if ordered_match
                else unordered_match.group(1)
            )

            if list_items and ordered != list_ordered:
                flush_list()

            list_ordered = ordered
            list_items.append(
                ListItem(children=[Text(text=item_text)])
            )
            continue

        flush_list()

        # ----------------------------------------------------------
        # Regular paragraph
        # ----------------------------------------------------------

        paragraph.append(line)

    if in_verse:
        raise StructureError("Unterminated :::verse block.")

    flush_paragraph()
    flush_list()
    flush_verse()

    return document
