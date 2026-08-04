"""
Publication pipeline.

Convert a Markdown manuscript into publication outputs.
"""

from __future__ import annotations

from pathlib import Path

from model import Book
from parser.reader import read
from parser.structure import parse_structure
from parser.inline import parse_inline
from renderer.epub import render as render_epub
from renderer.typst import RenderOptions, render as render_typst


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

    book = read_book(path)

    return render_typst(book)


def publish_epub(
    path: str | Path,
    cover_path: str | Path | None = None,
) -> bytes:
    """
    Compile a Markdown manuscript into EPUB.

    Parameters
    ----------
    path:
        Path to the Markdown manuscript.

    cover_path:
        Path to the cover image.

    Returns
    -------
    bytes
        EPUB package bytes.
    """

    book = read_book(path)

    return render_epub(book, cover_path)


def publish_all(
    path: str | Path,
    cover_path: str | Path | None = None,
    typst_cover_path: str | None = None,
    render_options: RenderOptions | None = None,
) -> tuple[str, bytes]:
    """
    Compile a Markdown manuscript into Typst and EPUB.

    Parameters
    ----------
    path:
        Path to the Markdown manuscript.

    cover_path:
        Path to the cover image.

    typst_cover_path:
        Cover image path as it should appear in the generated Typst source.

    render_options:
        Options for Typst rendering. EPUB rendering is unaffected.

    Returns
    -------
    tuple[str, bytes]
        Typst source and EPUB package bytes.
    """

    book = read_book(path)

    if typst_cover_path is None:
        typst_cover_path = "/assets/books/current/cover.png"

    return (
        render_typst(book, typst_cover_path, render_options),
        render_epub(book, cover_path),
    )


def read_book(path: str | Path) -> Book:
    """
    Read and parse a Markdown manuscript into a Book AST.
    """

    metadata, body = read(path)

    book = parse_structure(metadata, body)

    parse_inline(book)

    return book


def publish_book(
    book: Book,
    render_options: RenderOptions | None = None,
) -> str:
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

    return render_typst(book, options=render_options)


def publish_epub_book(
    book: Book,
    cover_path: str | Path | None = None,
) -> bytes:
    """
    Compile a parsed Book into EPUB.

    Parameters
    ----------
    book:
        Parsed document AST.

    cover_path:
        Path to the cover image.

    Returns
    -------
    bytes
        EPUB package bytes.
    """

    parse_inline(book)

    return render_epub(book, cover_path)
