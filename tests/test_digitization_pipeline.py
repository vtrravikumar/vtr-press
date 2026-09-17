from pathlib import Path

from digitization.pipeline import DigitizationPipeline, MarkdownAssembler
from digitization.structure import PageStructure


class FakeRenderer:
    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        pages = [output / "page-1.png", output / "page-2.png"]
        for page in pages:
            page.write_bytes(b"image")
        return pages


class FakeOCR:
    def ocr_image(self, image: str | Path) -> str:
        return f"OCR for {Path(image).name}"


class CodeOCR:
    def ocr_image(self, image: str | Path) -> str:
        return "#include <stdio.h>\nint main(void) {\n    return 0;\n}"


def test_pipeline_preserves_page_provenance(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    result = DigitizationPipeline(FakeRenderer(), FakeOCR()).run(pdf, tmp_path / "work")

    assert [page.page_number for page in result.pages] == [1, 2]
    assert [page.source_pdf for page in result.pages] == [pdf, pdf]
    assert [page.text for page in result.pages] == [
        "OCR for page-1.png",
        "OCR for page-2.png",
    ]
    assert all(page.structure is PageStructure.PROSE for page in result.pages)


def test_pipeline_can_assemble_traceable_markdown(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    markdown = DigitizationPipeline(FakeRenderer(), FakeOCR()).run_to_markdown(
        pdf, tmp_path / "work"
    )

    assert "<!-- source: source.pdf; page: 1 -->" in markdown
    assert "<!-- source: source.pdf; page: 2 -->" in markdown
    assert "<!-- structure: prose; confidence: 0.50 -->" in markdown
    assert "OCR for page-1.png" in markdown
    assert "OCR for page-2.png" in markdown


def test_pipeline_allows_classification_to_be_disabled(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    result = DigitizationPipeline(
        FakeRenderer(), FakeOCR(), classifier=None
    ).run(pdf, tmp_path / "work")

    assert all(page.structure is None for page in result.pages)


def test_code_page_is_marked_for_review_without_language_hint(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    markdown = DigitizationPipeline(FakeRenderer(), CodeOCR()).run_to_markdown(
        pdf, tmp_path / "work"
    )

    assert "<!-- structure: code;" in markdown
    assert "<!-- review: OCR code listing requires verification against the source scan -->" in markdown
    assert "````\n#include <stdio.h>" in markdown
    assert "````" in markdown
    assert "```c" not in markdown


def test_markdown_assembler_does_not_modify_ocr_text():
    from digitization.pipeline import DigitizationResult, PageOCR

    result = DigitizationResult(
        source_pdf=Path("source.pdf"),
        pages=(
            PageOCR(
                source_pdf=Path("source.pdf"),
                page_number=1,
                image=Path("page-1.png"),
                text="Original punctuation: {} [] ; : #",
            ),
        ),
    )

    markdown = MarkdownAssembler().assemble(result)
    assert "Original punctuation: {} [] ; : #" in markdown
