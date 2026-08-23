"""
Regression tests for run.py's cover-requirement logic (C2 decision 2).

A cover is required for type: book; optional for every other type.
These tests stub out the heavy parts of the pipeline (Typst
compilation, EPUB/PDF writing) so they run fast and without requiring
the `typst` binary -- the goal is to lock in *whether* a cover is
staged/required, not to re-verify rendering (that's covered in
test_typst_renderer.py and test_epub_renderer.py).
"""

from __future__ import annotations
import subprocess
from pathlib import Path

import pytest

import run


@pytest.fixture
def fake_pipeline(monkeypatch, tmp_path):
    """
    Stub out load_books(), publish_all(), and the Typst compile
    subprocess. Captures whether a cover was passed through to
    publish_all() and whether a cover file was staged on disk.
    """

    captured: dict = {}

    def make_manuscript(doc_type: str) -> Path:
        path = tmp_path / f"{doc_type}.md"
        front_matter = f"type: {doc_type}\n" if doc_type else ""
        path.write_text(
            f"---\ntitle: T\n{front_matter}---\n\n## Section\n\nBody.\n",
            encoding="utf-8",
        )
        return path

    def configure(doc_type: str, with_cover: bool):
        manuscript = make_manuscript(doc_type)
        config = {
            "bookpath": str(tmp_path),
            "manuscript": manuscript.name,
            "output_name": "TestBook",
        }

        if with_cover:
            cover = tmp_path / "cover.png"
            cover.write_bytes(b"\x89PNG\r\n")
            config["cover"] = str(cover)

        monkeypatch.setattr(
            run, "load_books", lambda: {"testbook": config}
        )

    def fake_publish_all(
        manuscript_path,
        cover_path,
        typst_cover_path,
        render_options=None,
        assets_root=None,
        assets=None,
    ):
        captured["cover_path"] = cover_path
        captured["typst_cover_path"] = typst_cover_path
        captured["assets_root"] = assets_root
        captured["assets"] = assets
        return "TYPST SOURCE", b"EPUB BYTES"

    def fake_typst_compile(*args, **kwargs):
        pdf_out = Path(args[0][-1])
        pdf_out.parent.mkdir(parents=True, exist_ok=True)
        pdf_out.write_bytes(b"%PDF-FAKE")
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(run, "publish_all", fake_publish_all)
    monkeypatch.setattr(run.subprocess, "run", fake_typst_compile)
    monkeypatch.setattr(run, "GENERATED_DIR", tmp_path / "generated")
    monkeypatch.setattr(run, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(run, "ROOT", tmp_path)
    captured["root"] = tmp_path

    return {"configure": configure, "captured": captured}


def test_book_with_cover_succeeds(monkeypatch, fake_pipeline):
    fake_pipeline["configure"]("book", with_cover=True)
    monkeypatch.setattr("sys.argv", ["run.py", "testbook"])

    run.main()

    assert fake_pipeline["captured"]["cover_path"] is not None
    assert fake_pipeline["captured"]["typst_cover_path"] is not None

    manifest = (
        fake_pipeline["captured"]["root"]
        / "isbn"
        / "TestBook"
        / "publication-manifest.md"
    )
    manifest_text = manifest.read_text(encoding="utf-8")

    assert "TestBook Publication Manifest" in manifest_text
    assert "TestBook.pdf" in manifest_text
    assert "TestBook.epub" in manifest_text
    assert "SHA256:" in manifest_text


def test_book_without_cover_exits_with_clear_error(
    monkeypatch, fake_pipeline, capsys
):
    fake_pipeline["configure"]("book", with_cover=False)
    monkeypatch.setattr("sys.argv", ["run.py", "testbook"])

    with pytest.raises(SystemExit) as exc_info:
        run.main()

    assert exc_info.value.code == 1
    assert "cover_path" not in fake_pipeline["captured"]

    output = capsys.readouterr().out
    assert "book" in output.lower()
    assert "cover" in output.lower()


def test_technical_document_without_cover_succeeds(monkeypatch, fake_pipeline):
    fake_pipeline["configure"]("technical-document", with_cover=False)
    monkeypatch.setattr("sys.argv", ["run.py", "testbook"])

    run.main()

    assert fake_pipeline["captured"]["cover_path"] is None
    assert fake_pipeline["captured"]["typst_cover_path"] is None


def test_technical_document_with_cover_also_succeeds(monkeypatch, fake_pipeline):
    """
    Providing a cover for a technical document must not be an error --
    it should be staged and passed through (EPUB uses it; the PDF
    path ignores it per VP-006/B2, unaffected by this change).
    """

    fake_pipeline["configure"]("technical-document", with_cover=True)
    monkeypatch.setattr("sys.argv", ["run.py", "testbook"])

    run.main()

    assert fake_pipeline["captured"]["cover_path"] is not None
    assert fake_pipeline["captured"]["typst_cover_path"] is not None


def test_omitted_type_is_treated_as_book_and_requires_cover(
    monkeypatch, fake_pipeline
):
    """type defaults to "book" -- the cover requirement must follow
    that same default, not just apply to an explicit `type: book`."""

    fake_pipeline["configure"]("", with_cover=False)
    monkeypatch.setattr("sys.argv", ["run.py", "testbook"])

    with pytest.raises(SystemExit) as exc_info:
        run.main()

    assert exc_info.value.code == 1