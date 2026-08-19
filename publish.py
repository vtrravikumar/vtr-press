"""
Publication pipeline.

Convert a Markdown manuscript into publication outputs.
"""

from __future__ import annotations

from pathlib import Path

from interpretation import InterpretedDocument, interpret_technical_document
from model import Book, Document
from parser.document_model import parse_document
from parser.inline import parse_inline, parse_inline_document
from parser.reader import read
from parser.structure import parse_structure
from renderer.document_assets import DocumentAssets
from renderer.document_epub import render_document as render_document_epub
from renderer.document_typst import render_document as render_document_typst
from renderer.epub import render as render_epub
from renderer.typst import RenderOptions
from renderer.typst import render as render_typst


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

    metadata, _ = read(path)

    if metadata.type == "technical-document":
        with DocumentAssets(path) as assets:
            return render_document_typst(
                read_document(path),
                assets=assets,
            )

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

    metadata, _ = read(path)

    if metadata.type == "technical-document":
        with DocumentAssets(path) as assets:
            return render_document_epub(
                read_document(path),
                assets=assets,
            )

    book = read_book(path)

    return render_epub(book, cover_path)


def publish_all(
    path: str | Path,
    cover_path: str | Path | None = None,
    typst_cover_path: str | None = None,
    render_options: RenderOptions | None = None,
    assets_root: str | Path | None = None,
    assets: DocumentAssets | None = None,
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

    assets_root:
        Root directory containing technical-document assets.

    assets:
        Existing DocumentAssets resolver supplied by the caller.
        When provided, its lifetime remains under the caller's control.

    Returns
    -------
    tuple[str, bytes]
        Typst source and EPUB package bytes.
    """

    metadata, _ = read(path)

    if metadata.type == "technical-document":
        document = read_document(path)

        if assets is not None:
            return (
                render_document_typst(
                    document,
                    render_options,
                    assets=assets,
                ),
                render_document_epub(
                    document,
                    assets=assets,
                ),
            )

        with DocumentAssets(
            path,
            assets_root=assets_root,
        ) as document_assets:
            return (
                render_document_typst(
                    document,
                    render_options,
                    assets=document_assets,
                ),
                render_document_epub(
                    document,
                    assets=document_assets,
                ),
            )

    book = read_book(path)

    if typst_cover_path is None:
        typst_cover_path = "/assets/books/current/cover.png"

    return (
        render_typst(book, typst_cover_path, render_options),
        render_epub(book, cover_path),
    )


def read_document(path: str | Path) -> InterpretedDocument:
    """
    Read a technical-document manuscript through the generic Document Model.
    """

    metadata, body = read(path)

    if metadata.type != "technical-document":
        raise ValueError(
            "read_document() currently supports only technical-document"
        )

    document: Document = parse_document(metadata, body)
    parse_inline_document(document)

    return interpret_technical_document(document)


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

    Returns
    -------
    bytes
        EPUB package bytes.
    """

    parse_inline(book)

    return render_epub(book, cover_path)