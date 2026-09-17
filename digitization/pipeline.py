"""Deterministic orchestration for source-document digitization.

The pipeline deliberately depends on small adapters rather than concrete OCR or
image-processing implementations. It preserves the relationship between every
Markdown fragment and its source PDF page so the generated manuscript can be
reviewed against the original scan.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


class PageRenderer(Protocol):
    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]: ...


class ImagePreprocessor(Protocol):
    def process(self, image: str | Path, output_dir: str | Path) -> Path: ...


class OCREngine(Protocol):
    def ocr_image(self, image: str | Path) -> str: ...


@dataclass(frozen=True)
class PageOCR:
    """OCR text and provenance for one source page."""

    source_pdf: Path
    page_number: int
    image: Path
    text: str


@dataclass(frozen=True)
class DigitizationResult:
    """Complete intermediate result before Markdown assembly."""

    source_pdf: Path
    pages: tuple[PageOCR, ...]


class MarkdownAssembler:
    """Assemble page-level OCR results into a reviewable Markdown draft."""

    def assemble(self, result: DigitizationResult) -> str:
        blocks: list[str] = []
        for page in result.pages:
            blocks.extend(
                [
                    f"<!-- source: {page.source_pdf.name}; page: {page.page_number} -->",
                    "",
                    page.text.rstrip(),
                    "",
                    "---",
                    "",
                ]
            )
        return "\n".join(blocks).rstrip() + "\n"


class DigitizationPipeline:
    """Convert a PDF into page-traceable OCR results and Markdown."""

    def __init__(
        self,
        renderer: PageRenderer,
        ocr: OCREngine,
        preprocessor: ImagePreprocessor | None = None,
    ):
        self.renderer = renderer
        self.ocr = ocr
        self.preprocessor = preprocessor

    def run(self, pdf: str | Path, work_dir: str | Path) -> DigitizationResult:
        source_pdf = Path(pdf)
        if not source_pdf.is_file():
            raise FileNotFoundError(source_pdf)

        root = Path(work_dir)
        pages_dir = root / "pages"
        processed_dir = root / "processed"
        images = self.renderer.render(source_pdf, pages_dir)

        page_results: list[PageOCR] = []
        for page_number, image in enumerate(images, start=1):
            ocr_image = image
            if self.preprocessor is not None:
                ocr_image = self.preprocessor.process(image, processed_dir)
            text = self.ocr.ocr_image(ocr_image)
            page_results.append(
                PageOCR(
                    source_pdf=source_pdf,
                    page_number=page_number,
                    image=ocr_image,
                    text=text,
                )
            )

        return DigitizationResult(source_pdf=source_pdf, pages=tuple(page_results))

    def run_to_markdown(self, pdf: str | Path, work_dir: str | Path) -> str:
        """Run digitization and return a page-traceable Markdown draft."""

        result = self.run(pdf, work_dir)
        return MarkdownAssembler().assemble(result)
