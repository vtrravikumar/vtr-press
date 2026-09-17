"""Command-line entry point for repeatable PDF-to-Markdown digitization."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from .ocr import TesseractOCR, get_ocr_profile
from .pdf import PdftoppmRenderer
from .pipeline import DigitizationPipeline
from .preprocess import PassthroughPreprocessor, PillowPreprocessor, PreprocessConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a scanned PDF into a page-traceable Markdown draft."
    )
    parser.add_argument("pdf", type=Path, help="input PDF")
    parser.add_argument("output", type=Path, help="output Markdown file")
    parser.add_argument("--work-dir", type=Path, help="working directory for rendered pages")
    parser.add_argument(
        "--profile",
        choices=("prose", "layout", "code"),
        default="prose",
        help="Tesseract OCR profile (default: prose)",
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    pdf = args.pdf.resolve()
    if not pdf.is_file():
        raise SystemExit(f"Input PDF not found: {pdf}")

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    work_dir = (args.work_dir or output.parent / ".digitization-work").resolve()

    renderer = PdftoppmRenderer()
    ocr = TesseractOCR(config=get_ocr_profile(args.profile))
    if args.preprocess == "conservative":
        preprocessor = PillowPreprocessor(PreprocessConfig())
    else:
        preprocessor = PassthroughPreprocessor()

    pipeline = DigitizationPipeline(renderer, ocr, preprocessor=preprocessor)
    markdown = pipeline.run_to_markdown(
        pdf,
        work_dir,
        include_source_images=args.include_source_images,
    )
    output.write_text(markdown, encoding="utf-8")

    # Keep the original rendered page images alongside the manuscript so the
    # source-image Markdown references remain usable after the command exits.
    source_pages = work_dir / "pages"
    output_pages = output.parent / "pages"
    if source_pages.is_dir():
        output_pages.mkdir(parents=True, exist_ok=True)
        for image in source_pages.glob("*"):
            if image.is_file():
                shutil.copy2(image, output_pages / image.name)

    print(f"Wrote Markdown: {output}")
    print(f"Source pages:   {output_pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
