"""Command-line entry point for repeatable PDF-to-Markdown digitization."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import re
import shutil

from .ocr import TesseractOCR, get_ocr_profile
from .pdf import PdftoppmRenderer
from .pipeline import DigitizationPipeline, DigitizationResult, MarkdownAssembler
from .preprocess import PassthroughPreprocessor, PillowPreprocessor, PreprocessConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a scanned PDF, or a report/code source folder, "
            "into a page-traceable Markdown draft."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="input PDF or source folder containing report/ and code/ folders",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="output Markdown file (default: manuscript.md beside the input)",
    )
    parser.add_argument("--work-dir", type=Path, help="working directory for rendered pages")
    parser.add_argument(
        "--profile",
        choices=("prose", "layout", "code"),
        default="prose",
        help="Tesseract OCR profile for a single PDF input (default: prose)",
    )
    parser.add_argument(
        "--preprocess",
        choices=("none", "conservative"),
        default="conservative",
        help="image preprocessing mode (default: conservative)",
    )
    parser.add_argument(
        "--include-source-images",
        action="store_true",
        help="embed source images for layout-classified pages",
    )
    return parser


def _discover_sources(source_dir: Path) -> list[tuple[Path, str]]:
    """Discover report and source-code PDFs in a standard project source tree."""

    report_dir = source_dir / "report"
    code_dir = source_dir / "code"
    if not report_dir.is_dir():
        raise SystemExit(f"Report source folder not found: {report_dir}")
    if not code_dir.is_dir():
        raise SystemExit(f"Code source folder not found: {code_dir}")

    report_pdfs = sorted(
        p for p in report_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"
    )
    code_pdfs = sorted(
        p for p in code_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"
    )
    if not report_pdfs:
        raise SystemExit(f"No PDF files found in report source folder: {report_dir}")
    if not code_pdfs:
        raise SystemExit(f"No PDF files found in code source folder: {code_dir}")

    return [(pdf, "prose") for pdf in report_pdfs] + [(pdf, "code") for pdf in code_pdfs]


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "source"


def _copy_source_pages(
    result: DigitizationResult,
    output_pages: Path,
    source_index: int,
) -> DigitizationResult:
    """Copy rendered pages with collision-safe names and update provenance paths."""

    output_pages.mkdir(parents=True, exist_ok=True)
    updated_pages = []
    prefix = f"{source_index:02d}-{_safe_stem(result.source_pdf.stem)}"
    for page in result.pages:
        destination = output_pages / f"{prefix}-page-{page.page_number}.png"
        shutil.copy2(page.source_image or page.image, destination)
        updated_pages.append(replace(page, source_image=destination))
    return replace(result, pages=tuple(updated_pages))


def _build_preprocessor(mode: str):
    if mode == "conservative":
        return PillowPreprocessor(PreprocessConfig())
    return PassthroughPreprocessor()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    input_path = args.input.resolve()
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    if input_path.is_dir():
        sources = _discover_sources(input_path)
        default_output_dir = input_path
    else:
        if input_path.suffix.lower() != ".pdf":
            raise SystemExit(f"Input must be a PDF or source folder: {input_path}")
        sources = [(input_path, args.profile)]
        default_output_dir = input_path.parent

    output = (args.output or default_output_dir / "manuscript.md").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    work_root = (args.work_dir or output.parent / ".digitization-work").resolve()
    output_pages = output.parent / "pages"

    renderer = PdftoppmRenderer()
    preprocessor = _build_preprocessor(args.preprocess)
    assembler = MarkdownAssembler(include_source_images=args.include_source_images)
    manuscript_parts: list[str] = []

    for source_index, (pdf, profile) in enumerate(sources, start=1):
        source_work = work_root / f"{source_index:02d}-{_safe_stem(pdf.stem)}"
        if source_work.exists():
            shutil.rmtree(source_work)

        ocr = TesseractOCR(config=get_ocr_profile(profile))
        pipeline = DigitizationPipeline(renderer, ocr, preprocessor=preprocessor)
        result = pipeline.run(pdf, source_work)
        result = _copy_source_pages(result, output_pages, source_index)

        manuscript_parts.append(
            f"<!-- source-document: {pdf.name}; profile: {profile} -->\n"
            + assembler.assemble(result).rstrip()
        )
        print(f"Processed {pdf.name} ({profile}, {len(result.pages)} pages)")

    output.write_text("\n\n".join(manuscript_parts) + "\n", encoding="utf-8")

    print(f"Wrote Markdown: {output}")
    print(f"Source pages:   {output_pages}")
    print(f"Documents:      {len(sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
