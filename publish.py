"""
Publication pipeline.

Convert a Markdown manuscript into Typst source.
"""

from __future__ import annotations

from pathlib import Path

from model import Book
from parser.reader import read
from parser.structure import parse_structure
from parser.inline import parse_inline
from renderer.typst import render


def publish(path: str | Path) -> str:
    """
    Compile a Markdown manuscript into Typst.

    Parameters
    ----------
    path:
        Path to the Markdown manuscript.

    Returns
    -------
    str
        Typst source.
    """

    metadata, body = read(path)

    book = parse_structure(metadata, body)

    return publish_book(book)


def publish_book(book: Book) -> str:
    """
    Compile a parsed Book into Typst.

    Parameters
    ----------
    book:
        Parsed document AST.

    Returns
    -------
    str
        Typst source.
    """

    parse_inline(book)

    return render(book)