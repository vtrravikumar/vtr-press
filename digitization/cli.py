"""Command-line entry point for repeatable PDF-to-Markdown digitization."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import re
import shutil
import time

from .compatibility import build_front_matter, extract_metadata, validate_vtr_press_markdown
from .ocr import TesseractOCR, get_ocr_profile
from .pdf import PdftoppmRenderer
from .pipeline import DigitizationPipeline, DigitizationResult, MarkdownAssembler
from .preprocess import PassthroughPreprocessor, PillowPreprocessor, PreprocessConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a scanned PDF, or a report/code source folder, "
            "into a VTR Press-compatible, page-traceable Markdown manuscript."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="input PDF or source folder containing report/ and optional code/ folders",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="output Markdown file (default: manuscript.md one level above a source folder, or beside a PDF)",
    )
    parser.add_argument("--work-dir", type=Path, help="working directory for rendered pages")
    parser.add_argument(
        "--profile",
        choices=("prose", "layout", "code"),
        default="prose",
        help="OCR profile for a single PDF input (default: prose)",
    )
    parser.add_argument(
        "--preprocess",
        choices=("none", "conservative"),
        default="conservative",
        help="image preprocessing mode (default: conservative)",
    )
    parser.add_argument(
        "--pdf-renderer",
        choices=("pdftoppm", "pymupdf"),
        default="pdftoppm",
        help="PDF rendering backend; use pymupdf for a pip-only local macOS setup",
    )
    parser.add_argument(
        "--ocr-engine",
        choices=("tesseract", "macos-vision"),
        default="tesseract",
        help="OCR backend; macos-vision uses Apple's Vision framework via ocrmac",
    )
    parser.add_argument(
        "--include-source-images",
        action="store_true",
        help="embed source images for layout-classified pages",
    )
    return parser


def _numbered_sort_key(path: Path) -> tuple[int, str]:
    """Sort PDFs by the final numeric component, with name as a tiebreaker."""
    match = re.search(r"(?:^|[-_ ])(\d+)(?=\.pdf$)", path.name, re.IGNORECASE)
    return (int(match.group(1)) if match else 10**9, path.name.lower())


def _ordered_pdfs(directory: Path, kind: str, *, required: bool) -> list[Path]:
    """Return PDFs in numbered order and reject gaps in multi-part inputs."""
    pdfs = sorted(
        (p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"),
        key=_numbered_sort_key,
    )
    if not pdfs:
        if required:
            raise SystemExit(f"No PDF files found in {kind} source folder: {directory}")
        return []

    numbered = []
    unnumbered = []
    for pdf in pdfs:
        match = re.search(r"(?:^|[-_ ])(\d+)(?=\.pdf$)", pdf.name, re.IGNORECASE)
        (numbered if match else unnumbered).append((pdf, int(match.group(1)) if match else 0))

    if len(pdfs) == 1:
        return pdfs
    if unnumbered:
        names = ", ".join(p.name for p, _ in unnumbered)
        raise SystemExit(
            f"Multiple {kind} PDFs must be numbered 01, 02, 03, ...; unnumbered: {names}"
        )

    numbers = [number for _, number in numbered]
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        raise SystemExit(
            f"{kind} PDF sequence must be continuous starting at 01; found: "
            + ", ".join(f"{number:02d}" for number in numbers)
        )
    return pdfs


def _discover_sources(source_dir: Path) -> list[tuple[Path, str]]:
    """Discover report PDFs and optional code PDFs in a standard source tree."""
    report_dir = source_dir / "report"
    code_dir = source_dir / "code"
    if not report_dir.is_dir():
        raise SystemExit(f"Report source folder not found: {report_dir}")

    report_pdfs = _ordered_pdfs(report_dir, "report", required=True)
    code_pdfs = _ordered_pdfs(code_dir, "code", required=False) if code_dir.is_dir() else []
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


def _build_renderer(name: str):
    if name == "pymupdf":
        from .pdf_pymupdf import PyMuPDFRenderer

        return PyMuPDFRenderer()
    return PdftoppmRenderer()


def _build_ocr(engine: str, profile: str):
    config = get_ocr_profile(profile)
    if engine == "macos-vision":
        from .ocr_macos import MacOSVisionOCR

        return MacOSVisionOCR(config=config)
    return TesseractOCR(config=config)


def _format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = args.input.resolve()
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    if input_path.is_dir():
        sources = _discover_sources(input_path)
        default_output_dir = input_path.parent
    else:
        if input_path.suffix.lower() != ".pdf":
            raise SystemExit(f"Input must be a PDF or source folder: {input_path}")
        sources = [(input_path, args.profile)]
        default_output_dir = input_path.parent

    output = (args.output or default_output_dir / "manuscript.md").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    work_root = (args.work_dir or output.parent / ".digitization-work").resolve()
    output_pages = output.parent / "pages"

    renderer = _build_renderer(args.pdf_renderer)
    preprocessor = _build_preprocessor(args.preprocess)
    assembler = MarkdownAssembler(include_source_images=args.include_source_images)
    manuscript_parts: list[str] = []
    first_report_page_text: str | None = None
    overall_start = time.monotonic()

    print("VTR Press — Document Digitization")
    print(f"Source: {input_path}")
    print(f"Documents: {len(sources)}")
    print(f"Renderer: {args.pdf_renderer}")
    print(f"OCR: {args.ocr_engine}")
    print(f"Preprocessing: {args.preprocess}")
    print()

    for source_index, (pdf, profile) in enumerate(sources, start=1):
        source_work = work_root / f"{source_index:02d}-{_safe_stem(pdf.stem)}"
        if source_work.exists():
            shutil.rmtree(source_work)

        ocr = _build_ocr(args.ocr_engine, profile)
        pipeline = DigitizationPipeline(renderer, ocr, preprocessor=preprocessor)
        source_start = time.monotonic()

        def report_progress(page_number: int, total_pages: int, _unused: float) -> None:
            elapsed = time.monotonic() - source_start
            average = elapsed / page_number
            remaining = max(0.0, average * (total_pages - page_number))
            print(
                f"[{page_number:>2}/{total_pages}] OCR complete "
                f"({elapsed / page_number:.1f}s/page) | "
                f"elapsed {_format_duration(elapsed)} | "
                f"ETA ~{_format_duration(remaining)}"
            )

        result = pipeline.run(pdf, source_work, progress_callback=report_progress)
        result = _copy_source_pages(result, output_pages, source_index)
        if first_report_page_text is None and profile == "prose" and result.pages:
            first_report_page_text = result.pages[0].text

        manuscript_parts.append(
            f"<!-- source-document: {pdf.name}; profile: {profile} -->\n"
            + assembler.assemble(result).rstrip()
        )
        print(
            f"Completed {pdf.name}: {len(result.pages)} pages in "
            f"{_format_duration(time.monotonic() - source_start)}"
        )
        print()

    metadata = extract_metadata(first_report_page_text or "")
    body = "\n\n".join(manuscript_parts).strip()
    manuscript = build_front_matter(metadata) + "\n\n" + body + "\n"
    errors = validate_vtr_press_markdown(manuscript)
    if errors:
        raise SystemExit("VTR Press manuscript compatibility check failed:\n- " + "\n- ".join(errors))

    output.write_text(manuscript, encoding="utf-8")
    print(f"Wrote Markdown: {output}")
    print(f"Source pages:   {output_pages}")
    print(f"Documents:      {len(sources)}")
    print(f"Elapsed:        {_format_duration(time.monotonic() - overall_start)}")
    print("VTR Press compatibility: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
