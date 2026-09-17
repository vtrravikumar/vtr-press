"""Deterministic orchestration for source-document digitization.

The pipeline deliberately depends on small adapters rather than concrete OCR or
image-processing implementations. It preserves the relationship between every
Markdown fragment and its source PDF page so the generated manuscript can be
reviewed against the original scan.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from .compatibility import normalize_ocr_headings
from .review import build_review_markers
from .structure import PageStructure, StructureClassification, classify_structure


class PageRenderer(Protocol):
    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]: ...


class ImagePreprocessor(Protocol):
    def process(self, image: str | Path, output_dir: str | Path) -> Path: ...


class OCREngine(Protocol):
    def ocr_image(self, image: str | Path) -> str: ...


class StructureClassifier(Protocol):
    def __call__(self, text: str) -> StructureClassification: ...


ProgressCallback = Callable[[int, int, float], None]


@dataclass(frozen=True)
class PageOCR:
    """OCR text, structure classification and provenance for one source page."""

    source_pdf: Path
    page_number: int
    image: Path
    text: str
    structure: PageStructure | None = None
    structure_confidence: float | None = None
    source_image: Path | None = None
    review_markers: tuple[str, ...] = ()


@dataclass(frozen=True)
class DigitizationResult:
    """Complete intermediate result before Markdown assembly."""

    source_pdf: Path
    pages: tuple[PageOCR, ...]


class MarkdownAssembler:
    """Assemble page-level OCR results into a VTR Press-compatible draft.

    Source-page images are referenced only when explicitly requested. This
    keeps the normal manuscript readable while allowing layout-heavy pages to
    retain a visual fallback for figures, diagrams and uncertain tables.
    """

    def __init__(
        self,
        include_source_images: bool = False,
        source_image_prefix: str = "pages",
        image_structures: tuple[PageStructure, ...] = (PageStructure.LAYOUT,),
    ):
        self.include_source_images = include_source_images
        self.source_image_prefix = source_image_prefix.strip("/")
        self.image_structures = image_structures

    def assemble(self, result: DigitizationResult) -> str:
        blocks: list[str] = []
        for page in result.pages:
            blocks.append(
                f"<!-- source: {page.source_pdf.name}; page: {page.page_number} -->"
            )
            source_image = page.source_image or page.image
            blocks.append(f"<!-- source-image: {self.source_image_prefix}/{source_image.name} -->")
            if page.structure is not None:
                confidence = (
                    f"{page.structure_confidence:.2f}"
                    if page.structure_confidence is not None
                    else "unknown"
                )
                blocks.append(
                    f"<!-- structure: {page.structure.value}; confidence: {confidence} -->"
                )
            for marker in page.review_markers:
                blocks.append(f"<!-- review-marker: {marker} -->")

            if self.include_source_images and page.structure in self.image_structures:
                blocks.extend(
                    [
                        "",
                        f"![Source page {page.page_number}]({self.source_image_prefix}/{source_image.name})",
                        "",
                    ]
                )

            if page.structure is PageStructure.CODE:
                blocks.extend(
                    [
                        "",
                        "<!-- review: OCR code listing requires verification against the source scan -->",
                        "",
                        "````",
                        page.text.rstrip("\n"),
                        "````",
                        "",
                        "---",
                        "",
                    ]
                )
            else:
                text = normalize_ocr_headings(page.text.rstrip(), page.structure)
                blocks.extend(["", text, "", "---", ""])
        return "\n".join(blocks).rstrip() + "\n"


class DigitizationPipeline:
    """Convert a PDF into page-traceable OCR results and Markdown."""

    def __init__(
        self,
        renderer: PageRenderer,
        ocr: OCREngine,
        preprocessor: ImagePreprocessor | None = None,
        classifier: StructureClassifier | None = classify_structure,
    ):
        self.renderer = renderer
        self.ocr = ocr
        self.preprocessor = preprocessor
        self.classifier = classifier

    def run(
        self,
        pdf: str | Path,
        work_dir: str | Path,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> DigitizationResult:
        source_pdf = Path(pdf)
        if not source_pdf.is_file():
            raise FileNotFoundError(source_pdf)

        root = Path(work_dir)
        pages_dir = root / "pages"
        processed_dir = root / "processed"
        images = self.renderer.render(source_pdf, pages_dir)

        page_results: list[PageOCR] = []
        for page_number, image in enumerate(images, start=1):
            source_image = image
            ocr_image = image
            if self.preprocessor is not None:
                ocr_image = self.preprocessor.process(image, processed_dir)
            text = self.ocr.ocr_image(ocr_image)
            classification = self.classifier(text) if self.classifier is not None else None
            review_markers = build_review_markers(text, classification)
            page_results.append(
                PageOCR(
                    source_pdf=source_pdf,
                    page_number=page_number,
                    image=ocr_image,
                    text=text,
                    structure=classification.structure if classification else None,
                    structure_confidence=classification.confidence if classification else None,
                    source_image=source_image,
                    review_markers=review_markers,
                )
            )
            if progress_callback is not None:
                progress_callback(page_number, len(images), 0.0)

        return DigitizationResult(source_pdf=source_pdf, pages=tuple(page_results))

    def run_to_markdown(
        self,
        pdf: str | Path,
        work_dir: str | Path,
        *,
        include_source_images: bool = False,
        progress_callback: ProgressCallback | None = None,
    ) -> str:
        """Run digitization and return a page-traceable Markdown draft."""

        result = self.run(pdf, work_dir, progress_callback=progress_callback)
        return MarkdownAssembler(
            include_source_images=include_source_images,
        ).assemble(result)

