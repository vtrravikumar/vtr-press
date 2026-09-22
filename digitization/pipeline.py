"""Deterministic orchestration for source-document digitization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Callable, Protocol

from .compatibility import normalize_ocr_headings
from .layout import VisualAnalysis, analyze_page
from .review import build_review_markers
from .structure import PageStructure, StructureClassification, classify_structure
from .visual_extract import extract_visual_candidates


class PageRenderer(Protocol):
    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]: ...


class ImagePreprocessor(Protocol):
    def process(self, image: str | Path, output_dir: str | Path) -> Path: ...


class OCREngine(Protocol):
    def ocr_image(self, image: str | Path) -> str: ...


class StructureClassifier(Protocol):
    def __call__(self, text: str) -> StructureClassification: ...


ProgressCallback = Callable[[int, int, float], None]
StageCallback = Callable[[str], None]


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
    visual_analysis: VisualAnalysis | None = None
    visual_assets: tuple[str, ...] = ()


@dataclass(frozen=True)
class DigitizationResult:
    """Complete intermediate result before Markdown assembly."""

    source_pdf: Path
    pages: tuple[PageOCR, ...]


class MarkdownAssembler:
    """Assemble page-level OCR results into a VTR Press-compatible draft."""

    def __init__(
        self,
        include_source_images: bool = False,
        source_image_prefix: str = "pages",
        image_structures: tuple[PageStructure, ...] = (PageStructure.LAYOUT,),
        visual_asset_prefix: str = "assets",
    ):
        self.include_source_images = include_source_images
        self.source_image_prefix = source_image_prefix.strip("/")
        self.image_structures = image_structures
        self.visual_asset_prefix = visual_asset_prefix.strip("/")

    def assemble(self, result: DigitizationResult) -> str:
        blocks: list[str] = []
        for page in result.pages:
            blocks.append(f"<!-- source: {page.source_pdf.name}; page: {page.page_number} -->")
            source_image = page.source_image or page.image
            blocks.append(f"<!-- source-image: {self.source_image_prefix}/{source_image.name} -->")
            if page.structure is not None:
                confidence = f"{page.structure_confidence:.2f}" if page.structure_confidence is not None else "unknown"
                blocks.append(f"<!-- structure: {page.structure.value}; confidence: {confidence} -->")
            if page.visual_analysis is not None and page.visual_analysis.reasons:
                visual = page.visual_analysis
                signals = []
                if visual.table_likely:
                    signals.append("table")
                if visual.diagram_likely:
                    signals.append("diagram")
                if visual.figure_likely:
                    signals.append("figure")
                blocks.append(
                    f"<!-- visual-structure: {','.join(signals) or 'unknown'}; "
                    f"confidence: {visual.confidence:.2f}; reasons: {','.join(visual.reasons)} -->"
                )
            for asset in page.visual_assets:
                reference = f"{self.visual_asset_prefix}/{asset}" if self.visual_asset_prefix else asset
                blocks.append(f"<!-- visual-candidate: {reference}; review: required -->")
                blocks.append(f"![Visual candidate]({reference})")
            for marker in page.review_markers:
                blocks.append(f"<!-- review-marker: {marker} -->")

            if self.include_source_images and page.structure in self.image_structures:
                blocks.extend(["", f"![Source page {page.page_number}]({self.source_image_prefix}/{source_image.name})", ""])

            if page.structure is PageStructure.CODE:
                blocks.extend([
                    "",
                    "<!-- review: OCR code listing requires verification against the source scan -->",
                    "",
                    "````",
                    page.text.rstrip("\n"),
                    "````",
                    "",
                    "---",
                    "",
                ])
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
        visual_analyzer: Callable[[str | Path], VisualAnalysis] | None = analyze_page,
        visual_extractor: Callable[..., tuple] | None = extract_visual_candidates,
    ):
        self.renderer = renderer
        self.ocr = ocr
        self.preprocessor = preprocessor
        self.classifier = classifier
        self.visual_analyzer = visual_analyzer
        self.visual_extractor = visual_extractor


    @staticmethod
    def _source_fingerprint(pdf: Path) -> str:
        digest = hashlib.sha256()
        with pdf.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _renderer_cache_key(self) -> str:
        return f"{type(self.renderer).__module__}.{type(self.renderer).__qualname__}:{self.renderer!r}"

    def _load_render_cache(self, pages_dir: Path, pdf: Path) -> list[Path] | None:
        manifest_path = pages_dir / "manifest.json"
        if not manifest_path.is_file():
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("source_sha256") != self._source_fingerprint(pdf):
                return None
            if manifest.get("renderer") != self._renderer_cache_key():
                return None
            pages = [pages_dir / name for name in manifest.get("pages", [])]
            if not pages or not all(page.is_file() for page in pages):
                return None
            return pages
        except (OSError, ValueError, TypeError):
            return None

    def _write_render_cache(self, pages_dir: Path, pdf: Path, images: list[Path]) -> None:
        manifest = {
            "source_sha256": self._source_fingerprint(pdf),
            "renderer": self._renderer_cache_key(),
            "pages": [image.name for image in images],
        }
        (pages_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    def run(
        self,
        pdf: str | Path,
        work_dir: str | Path,
        *,
        progress_callback: ProgressCallback | None = None,
        stage_callback: StageCallback | None = None,
    ) -> DigitizationResult:
        source_pdf = Path(pdf)
        if not source_pdf.is_file():
            raise FileNotFoundError(source_pdf)

        root = Path(work_dir)
        pages_dir = root / "pages"
        processed_dir = root / "processed"
        visuals_dir = root / "visuals" / source_pdf.stem

        images = self._load_render_cache(pages_dir, source_pdf)
        if images is not None:
            if stage_callback is not None:
                stage_callback(f"rendering-cached:{len(images)}")
                stage_callback("ocr-start")
        else:
            if stage_callback is not None:
                stage_callback("rendering-start")
            images = self.renderer.render(source_pdf, pages_dir)
            self._write_render_cache(pages_dir, source_pdf, images)
            if stage_callback is not None:
                stage_callback(f"rendering-complete:{len(images)}")
                stage_callback("ocr-start")

        page_results: list[PageOCR] = []
        for page_number, image in enumerate(images, start=1):
            source_image = image
            ocr_image = image
            if self.preprocessor is not None:
                ocr_image = self.preprocessor.process(image, processed_dir)
            text = self.ocr.ocr_image(ocr_image)
            classification = self.classifier(text) if self.classifier is not None else None
            visual = self.visual_analyzer(source_image) if self.visual_analyzer is not None else None
            visual_assets: tuple[str, ...] = ()
            if (
                visual is not None
                and self.visual_extractor is not None
                and (visual.table_likely or visual.diagram_likely or visual.figure_likely)
            ):
                page_visual_dir = visuals_dir / f"page-{page_number:03d}"
                regions = self.visual_extractor(source_image, visual, page_visual_dir)
                visual_assets = tuple(
                    str(path.relative_to(root)).replace("\\", "/")
                    for path in sorted(page_visual_dir.glob("*.png"))
                ) if regions else ()
            review_markers = build_review_markers(text, classification, visual)
            page_results.append(PageOCR(
                source_pdf=source_pdf,
                page_number=page_number,
                image=ocr_image,
                text=text,
                structure=classification.structure if classification else None,
                structure_confidence=classification.confidence if classification else None,
                source_image=source_image,
                review_markers=review_markers,
                visual_analysis=visual,
                visual_assets=visual_assets,
            ))
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
        stage_callback: StageCallback | None = None,
    ) -> str:
        """Run digitization and return a page-traceable Markdown draft."""
        result = self.run(
            pdf,
            work_dir,
            progress_callback=progress_callback,
            stage_callback=stage_callback,
        )
        return MarkdownAssembler(include_source_images=include_source_images).assemble(result)