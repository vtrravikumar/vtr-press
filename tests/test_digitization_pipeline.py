from pathlib import Path

from digitization.pipeline import DigitizationPipeline, MarkdownAssembler
from digitization.structure import PageStructure


class CountingRenderer:
    def __init__(self):
        self.calls = 0

    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]:
        self.calls += 1
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        page = output / "page-1.png"
        page.write_bytes(b"image")
        return [page]


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


class PreprocessedOCR:
    def ocr_image(self, image: str | Path) -> str:
        return f"OCR from {Path(image).name}"


class FakePreprocessor:
    def process(self, image: str | Path, output_dir: str | Path) -> Path:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        target = output / f"processed-{Path(image).name}"
        target.write_bytes(b"processed")
        return target


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
    assert [page.source_image.name for page in result.pages] == [
        "page-1.png",
        "page-2.png",
    ]
    assert all(page.structure is PageStructure.PROSE for page in result.pages)
    assert all(page.review_markers == () for page in result.pages)


def test_pipeline_can_assemble_traceable_markdown(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    markdown = DigitizationPipeline(FakeRenderer(), FakeOCR()).run_to_markdown(
        pdf, tmp_path / "work"
    )

    assert "<!-- source: source.pdf; page: 1 -->" in markdown
    assert "<!-- source: source.pdf; page: 2 -->" in markdown
    assert "<!-- source-image: pages/page-1.png -->" in markdown
    assert "<!-- structure: prose; confidence: 0.50 -->" in markdown
    assert "OCR for page-1.png" in markdown
    assert "OCR for page-2.png" in markdown
    assert "![Source page" not in markdown


def test_pipeline_allows_classification_to_be_disabled(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    result = DigitizationPipeline(
        FakeRenderer(), FakeOCR(), classifier=None
    ).run(pdf, tmp_path / "work")

    assert all(page.structure is None for page in result.pages)
    assert all(page.review_markers == () for page in result.pages)


def test_preprocessing_keeps_original_source_image_reference(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    result = DigitizationPipeline(
        FakeRenderer(), PreprocessedOCR(), preprocessor=FakePreprocessor()
    ).run(pdf, tmp_path / "work")

    assert result.pages[0].image.name == "processed-page-1.png"
    assert result.pages[0].source_image.name == "page-1.png"


def test_layout_page_can_embed_visual_source_fallback(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    class LayoutOCR:
        def ocr_image(self, image: str | Path) -> str:
            return "TITLE\n\nA PROJECT REPORT"

    markdown = DigitizationPipeline(FakeRenderer(), LayoutOCR()).run_to_markdown(
        pdf, tmp_path / "work", include_source_images=True
    )

    assert "<!-- structure: layout;" in markdown
    assert "<!-- review-marker: layout-visual-verification -->" in markdown
    assert "![Source page 1](pages/page-1.png)" in markdown
    assert "![Source page 2](pages/page-2.png)" in markdown


def test_code_page_is_marked_for_review_without_language_hint(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    markdown = DigitizationPipeline(FakeRenderer(), CodeOCR()).run_to_markdown(
        pdf, tmp_path / "work"
    )

    assert "<!-- structure: code;" in markdown
    assert "<!-- review-marker: code-ocr-verification -->" in markdown
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


def test_pipeline_reports_render_and_ocr_stages(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")
    stages = []

    result = DigitizationPipeline(FakeRenderer(), FakeOCR()).run(
        pdf,
        tmp_path / "work",
        stage_callback=stages.append,
    )

    assert len(result.pages) == 2
    assert stages == ["rendering-start", "rendering-complete:2", "ocr-start"]


def test_pipeline_reuses_valid_render_cache(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")
    work = tmp_path / "work"
    renderer = CountingRenderer()

    first = DigitizationPipeline(renderer, FakeOCR()).run(pdf, work)
    second = DigitizationPipeline(renderer, FakeOCR()).run(pdf, work)

    assert renderer.calls == 1
    assert first.pages[0].source_image == second.pages[0].source_image
    assert (work / "pages" / "manifest.json").is_file()


def test_pipeline_invalidates_render_cache_when_source_changes(tmp_path: Path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")
    work = tmp_path / "work"
    renderer = CountingRenderer()
    pipeline = DigitizationPipeline(renderer, FakeOCR())

    pipeline.run(pdf, work)
    pdf.write_bytes(b"changed")
    pipeline.run(pdf, work)

    assert renderer.calls == 2
