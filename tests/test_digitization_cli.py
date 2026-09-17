from pathlib import Path

from PIL import Image

from digitization import cli


class FakeRenderer:
    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        page = output / "page-1.png"
        Image.new("RGB", (16, 16), "white").save(page, format="PNG")
        return [page]


class FakeOCR:
    def __init__(self, executable=None, config=None):
        self.config = config

    def ocr_image(self, image: str | Path) -> str:
        return "TITLE\n\nA PROJECT REPORT"


def test_cli_writes_markdown_and_source_pages(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "PdftoppmRenderer", FakeRenderer)
    monkeypatch.setattr(cli, "TesseractOCR", FakeOCR)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")
    output = tmp_path / "manuscript.md"

    assert cli.main([str(pdf), str(output), "--include-source-images"]) == 0
    text = output.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "type: technical-document" in text
    assert "title: \"TITLE\"" in text
    assert "<!-- source-document: source.pdf; profile: prose -->" in text
    assert "<!-- source: source.pdf; page: 1 -->" in text
    assert (tmp_path / "pages" / "01-source-page-1.png").is_file()
    captured = capsys.readouterr().out
    assert "VTR Press — Document Digitization" in captured
    assert "[ 1/1] OCR complete" in captured
    assert "VTR Press compatibility: OK" in captured


def test_cli_supports_default_manuscript_output_for_single_pdf(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli, "PdftoppmRenderer", FakeRenderer)
    monkeypatch.setattr(cli, "TesseractOCR", FakeOCR)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    assert cli.main([str(pdf)]) == 0
    output = tmp_path / "manuscript.md"
    assert output.exists()
    assert "<!-- source: source.pdf; page: 1 -->" in output.read_text(encoding="utf-8")
    assert (tmp_path / "pages" / "01-source-page-1.png").is_file()


def test_cli_supports_passthrough_preprocessing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli, "PdftoppmRenderer", FakeRenderer)
    monkeypatch.setattr(cli, "TesseractOCR", FakeOCR)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")
    output = tmp_path / "manuscript.md"

    assert cli.main([str(pdf), str(output), "--preprocess", "none"]) == 0
    assert output.exists()


def test_cli_discovers_report_and_optional_code_into_one_root_manuscript(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setattr(cli, "PdftoppmRenderer", FakeRenderer)
    monkeypatch.setattr(cli, "TesseractOCR", FakeOCR)
    source = tmp_path / "source"
    report = source / "report"
    code = source / "code"
    report.mkdir(parents=True)
    code.mkdir()
    for name in ("College-project-01.pdf", "College-project-02.pdf", "College-project-03.pdf"):
        (report / name).write_bytes(b"pdf")
    for name in ("Code-01.pdf", "Code-02.pdf", "Code-03.pdf"):
        (code / name).write_bytes(b"pdf")

    assert cli.main([str(source)]) == 0
    output = tmp_path / "manuscript.md"
    text = output.read_text(encoding="utf-8")
    assert text.count("<!-- source-document:") == 6
    assert text.index("College-project-01.pdf") < text.index("College-project-02.pdf")
    assert text.index("College-project-03.pdf") < text.index("Code-01.pdf")
    assert text.index("Code-02.pdf") < text.index("Code-03.pdf")
    assert "profile: prose" in text
    assert "profile: code" in text
    assert len(list((tmp_path / "pages").glob("*.png"))) == 6
    assert (tmp_path / "pages" / "01-College-project-01-page-1.png").is_file()
    assert (tmp_path / "pages" / "06-Code-03-page-1.png").is_file()


def test_cli_allows_report_without_code_folder(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli, "PdftoppmRenderer", FakeRenderer)
    monkeypatch.setattr(cli, "TesseractOCR", FakeOCR)
    source = tmp_path / "source"
    (source / "report").mkdir(parents=True)
    (source / "report" / "report.pdf").write_bytes(b"pdf")

    assert cli.main([str(source)]) == 0
    text = (tmp_path / "manuscript.md").read_text(encoding="utf-8")
    assert text.count("<!-- source-document:") == 1
    assert "profile: prose" in text


def test_cli_allows_single_report_pdf_with_any_filename(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli, "PdftoppmRenderer", FakeRenderer)
    monkeypatch.setattr(cli, "TesseractOCR", FakeOCR)
    source = tmp_path / "source"
    (source / "report").mkdir(parents=True)
    (source / "report" / "final-report.pdf").write_bytes(b"pdf")

    assert cli.main([str(source)]) == 0
    assert "final-report.pdf" in (tmp_path / "manuscript.md").read_text(encoding="utf-8")


def test_cli_rejects_missing_report_sequence(tmp_path: Path):
    source = tmp_path / "source"
    report = source / "report"
    report.mkdir(parents=True)
    (report / "report-01.pdf").write_bytes(b"pdf")
    (report / "report-03.pdf").write_bytes(b"pdf")

    try:
        cli.main([str(source)])
    except SystemExit as exc:
        assert "continuous starting at 01" in str(exc)
    else:
        raise AssertionError("expected report sequence error")


def test_cli_rejects_unnumbered_multi_part_code(tmp_path: Path):
    source = tmp_path / "source"
    report = source / "report"
    code = source / "code"
    report.mkdir(parents=True)
    code.mkdir()
    (report / "report-01.pdf").write_bytes(b"pdf")
    (code / "Code-A.pdf").write_bytes(b"pdf")
    (code / "Code-B.pdf").write_bytes(b"pdf")

    try:
        cli.main([str(source)])
    except SystemExit as exc:
        assert "Multiple code PDFs must be numbered" in str(exc)
    else:
        raise AssertionError("expected code numbering error")
