from pathlib import Path

from digitization import cli


class FakeRenderer:
    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        page = output / "page-1.png"
        page.write_bytes(b"page")
        return [page]


class FakeOCR:
    def __init__(self, executable=None, config=None):
        self.config = config

    def ocr_image(self, image: str | Path) -> str:
        return "TITLE\n\nA PROJECT REPORT"


def test_cli_writes_markdown_and_source_pages(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli, "PdftoppmRenderer", FakeRenderer)
    monkeypatch.setattr(cli, "TesseractOCR", FakeOCR)

    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")
    output = tmp_path / "manuscript.md"

    assert cli.main([str(pdf), str(output), "--include-source-images"]) == 0

    assert output.read_text(encoding="utf-8").startswith(
        "<!-- source: source.pdf; page: 1 -->"
    )
    assert "![Source page 1](pages/page-1.png)" in output.read_text(encoding="utf-8")
    assert (tmp_path / "pages" / "page-1.png").read_bytes() == b"page"


def test_cli_supports_passthrough_preprocessing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli, "PdftoppmRenderer", FakeRenderer)
    monkeypatch.setattr(cli, "TesseractOCR", FakeOCR)

    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")
    output = tmp_path / "manuscript.md"

    assert cli.main([str(pdf), str(output), "--preprocess", "none"]) == 0
    assert output.exists()
