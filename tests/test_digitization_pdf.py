from pathlib import Path
from unittest.mock import patch

import pytest

from digitization.pdf import PDFRenderConfig, PdftoppmRenderer


def test_pdf_renderer_builds_expected_command(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"placeholder")
    output = tmp_path / "pages"
    output.mkdir()
    (output / "page-1.png").write_bytes(b"image")
    (output / "page-2.png").write_bytes(b"image")

    renderer = PdftoppmRenderer(
        executable="pdftoppm-test",
        config=PDFRenderConfig(dpi=400),
    )

    with patch("digitization.pdf.subprocess.run") as run:
        pages = renderer.render(pdf, output)

    run.assert_called_once_with(
        [
            "pdftoppm-test",
            "-r",
            "400",
            "-png",
            str(pdf),
            str(output / "page"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert pages == [output / "page-1.png", output / "page-2.png"]


def test_pdf_renderer_rejects_missing_pdf(tmp_path: Path):
    renderer = PdftoppmRenderer(executable="pdftoppm-test")
    with pytest.raises(FileNotFoundError):
        renderer.render(tmp_path / "missing.pdf", tmp_path / "pages")


def test_pdf_renderer_rejects_invalid_dpi(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"placeholder")
    renderer = PdftoppmRenderer(
        executable="pdftoppm-test",
        config=PDFRenderConfig(dpi=0),
    )

    with pytest.raises(ValueError, match="dpi"):
        renderer.render(pdf, tmp_path / "pages")


def test_pdf_renderer_requires_rendered_pages(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"placeholder")
    renderer = PdftoppmRenderer(executable="pdftoppm-test")

    with patch("digitization.pdf.subprocess.run"):
        with pytest.raises(RuntimeError, match="produced no png pages"):
            renderer.render(pdf, tmp_path / "pages")
