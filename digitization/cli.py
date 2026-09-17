"""Command-line entry point for repeatable PDF-to-Markdown digitization."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import shutil
import time

from .combined import (
    ProfileRoutingOCR,
    combine_pdfs,
    combined_cache_valid,
    load_cached_segments,
    remap_result_pages,
    split_page_durations,
)
from .compatibility import build_front_matter, extract_metadata, validate_vtr_press_markdown
from .ocr import TesseractOCR, get_ocr_profile
from .pdf import PdftoppmRenderer
from .pipeline import DigitizationPipeline, DigitizationResult, MarkdownAssembler
from .preprocess import PassthroughPreprocessor, PillowPreprocessor, PreprocessConfig
from .stats import DocumentStats, RunStats, utc_timestamp, write_run_stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert scanned PDFs or source folders into VTR Press-compatible Markdown.")
    parser.add_argument("input", type=Path, help="input PDF or source folder containing report/ and optional code/ folders")
    parser.add_argument("output", type=Path, nargs="?", default=None, help="output Markdown file")
    parser.add_argument("--work-dir", type=Path, help="working directory for rendered pages")
    parser.add_argument("--profile", choices=("prose", "layout", "code"), default="prose", help="OCR profile for a single PDF input")
    parser.add_argument("--preprocess", choices=("none", "conservative"), default="conservative", help="image preprocessing mode")
    parser.add_argument("--pdf-renderer", choices=("pdftoppm", "pymupdf"), default="pdftoppm", help="PDF rendering backend")
    parser.add_argument("--ocr-engine", choices=("tesseract", "macos-vision"), default="tesseract", help="OCR backend")
    parser.add_argument("--include-source-images", action="store_true", help="embed source images for layout-classified pages")
    parser.add_argument("--combine-sources", action="store_true", help="combine all source PDFs into a persistent cached PDF and process them in one sequential session (requires pymupdf)")
    parser.add_argument("--rebuild-combined", action="store_true", help="force regeneration of the cached combined PDF")
    return parser


def _numbered_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(?:^|[-_ ])(\d+)(?=\.pdf$)", path.name, re.IGNORECASE)
    return (int(match.group(1)) if match else 10**9, path.name.lower())


def _ordered_pdfs(directory: Path, kind: str, *, required: bool) -> list[Path]:
    pdfs = sorted((p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"), key=_numbered_sort_key)
    if not pdfs:
        if required:
            raise SystemExit(f"No PDF files found in {kind} source folder: {directory}")
        return []
    numbered, unnumbered = [], []
    for pdf in pdfs:
        match = re.search(r"(?:^|[-_ ])(\d+)(?=\.pdf$)", pdf.name, re.IGNORECASE)
        (numbered if match else unnumbered).append((pdf, int(match.group(1)) if match else 0))
    if len(pdfs) == 1:
        return pdfs
    if unnumbered:
        raise SystemExit(f"Multiple {kind} PDFs must be numbered 01, 02, 03, ...; unnumbered: " + ", ".join(p.name for p, _ in unnumbered))
    numbers = [number for _, number in numbered]
    if numbers != list(range(1, len(numbers) + 1)):
        raise SystemExit(f"{kind} PDF sequence must be continuous starting at 01; found: " + ", ".join(f"{number:02d}" for number in numbers))
    return pdfs


def _discover_sources(source_dir: Path) -> list[tuple[Path, str]]:
    report_dir, code_dir = source_dir / "report", source_dir / "code"
    if not report_dir.is_dir():
        raise SystemExit(f"Report source folder not found: {report_dir}")
    report_pdfs = _ordered_pdfs(report_dir, "report", required=True)
    code_pdfs = _ordered_pdfs(code_dir, "code", required=False) if code_dir.is_dir() else []
    return [(pdf, "prose") for pdf in report_pdfs] + [(pdf, "code") for pdf in code_pdfs]


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "source"


def _copy_source_pages(result: DigitizationResult, output_pages: Path, source_index: int) -> DigitizationResult:
    output_pages.mkdir(parents=True, exist_ok=True)
    updated_pages = []
    prefix = f"{source_index:02d}-{_safe_stem(result.source_pdf.stem)}"
    for page in result.pages:
        destination = output_pages / f"{prefix}-page-{page.page_number}.png"
        shutil.copy2(page.source_image or page.image, destination)
        updated_pages.append(replace(page, source_image=destination))
    return replace(result, pages=tuple(updated_pages))


def _build_preprocessor(mode: str):
    return PillowPreprocessor(PreprocessConfig()) if mode == "conservative" else PassthroughPreprocessor()


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


def _timestamp_after(started_at: str, seconds: float) -> str:
    timestamp = datetime.fromisoformat(started_at.replace("Z", "+00:00")) + timedelta(seconds=seconds)
    return timestamp.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _build_combined_ocr(engine: str, segments):
    profiles = tuple(dict.fromkeys(segment.profile for segment in segments))
    if engine == "macos-vision":
        shared = _build_ocr(engine, "prose")
        engines = {profile: shared for profile in profiles}
    else:
        engines = {profile: _build_ocr(engine, profile) for profile in profiles}
    return ProfileRoutingOCR(engines, segments)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.rebuild_combined and not args.combine_sources:
        raise SystemExit("--rebuild-combined requires --combine-sources")
    input_path = args.input.resolve()
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")
    if input_path.is_dir():
        sources = _discover_sources(input_path)
        default_output_dir = input_path.parent
    else:
        if args.combine_sources:
            raise SystemExit("--combine-sources requires a source folder input")
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
    manuscript_parts, document_stats = [], []
    first_report_page_text = None
    overall_start = time.monotonic()
    run_started_at = utc_timestamp()

    print("VTR Press — Document Digitization")
    print(f"Source: {input_path}")
    print(f"Documents: {len(sources)}")
    print(f"Renderer: {args.pdf_renderer}")
    print(f"OCR: {args.ocr_engine}")
    print(f"Preprocessing: {args.preprocess}")

    if args.combine_sources:
        cache_dir = input_path / "combined"
        combined_pdf = cache_dir / "source.pdf"
        manifest_path = cache_dir / "manifest.json"
        cache_valid = (not args.rebuild_combined) and combined_cache_valid(combined_pdf, manifest_path, sources)
        if cache_valid:
            segments = load_cached_segments(manifest_path, sources)
            print(f"Source PDFs: using cached combined PDF {combined_pdf}")
        else:
            cache_dir.mkdir(parents=True, exist_ok=True)
            print("Source PDFs: building cached combined PDF...")
            combine_start = time.monotonic()
            combined_pdf, segments = combine_pdfs(sources, combined_pdf, manifest_path)
            print(f"Source PDFs: combined in {_format_duration(time.monotonic() - combine_start)} -> {combined_pdf}")
        print("OCR session: single sequential session with profile routing")
        print()
        combined_work = work_root / "combined-run"
        if combined_work.exists():
            shutil.rmtree(combined_work)
        ocr = _build_combined_ocr(args.ocr_engine, segments)
        pipeline = DigitizationPipeline(renderer, ocr, preprocessor=preprocessor)
        combined_start = time.monotonic()
        page_started = combined_start
        page_durations = []
        recent_durations: list[float] = []

        def report_progress(page_number: int, total_pages: int, _unused: float) -> None:
            nonlocal page_started
            now = time.monotonic()
            duration = now - page_started
            page_durations.append(duration)
            recent_durations.append(duration)
            if len(recent_durations) > 10:
                recent_durations.pop(0)
            page_started = now
            elapsed = now - combined_start
            rate = sum(recent_durations) / len(recent_durations)
            remaining = rate * (total_pages - page_number)
            print(f"[{page_number:>3}/{total_pages}] OCR complete ({duration:.1f}s/page; recent {rate:.1f}s/page) | elapsed {_format_duration(elapsed)} | ETA ~{_format_duration(remaining)}")

        combined_result = pipeline.run(combined_pdf, combined_work, progress_callback=report_progress)
        remapped_pages = remap_result_pages(combined_result, segments)
        timings_by_source = split_page_durations(page_durations, segments)
        elapsed_before = 0.0
        for source_index, segment in enumerate(segments, start=1):
            source_pages = tuple(page for page in remapped_pages if page.source_pdf == segment.source_pdf)
            result = _copy_source_pages(DigitizationResult(segment.source_pdf, source_pages), output_pages, source_index)
            durations = timings_by_source[segment.source_pdf]
            source_duration = sum(durations)
            source_started_at = _timestamp_after(run_started_at, elapsed_before)
            elapsed_before += source_duration
            source_ended_at = _timestamp_after(run_started_at, elapsed_before)
            if first_report_page_text is None and segment.profile == "prose" and result.pages:
                first_report_page_text = result.pages[0].text
            manuscript_parts.append(f"<!-- source-document: {segment.source_pdf.name}; profile: {segment.profile} -->\n" + assembler.assemble(result).rstrip())
            document_stats.append(DocumentStats(segment.source_pdf.name, segment.profile, len(result.pages), source_started_at, source_ended_at, round(source_duration, 3), round(source_duration / len(result.pages), 3) if result.pages else 0.0, [round(value, 3) for value in durations]))
            print(f"Completed {segment.source_pdf.name}: {len(result.pages)} pages in {_format_duration(source_duration)}")
        print()
    else:
        shared_ocr = _build_ocr(args.ocr_engine, "prose") if args.ocr_engine == "macos-vision" else None
        if shared_ocr is not None:
            print("OCR session: persistent across documents")
        print()
        for source_index, (pdf, profile) in enumerate(sources, start=1):
            source_work = work_root / f"{source_index:02d}-{_safe_stem(pdf.stem)}"
            if source_work.exists():
                shutil.rmtree(source_work)
            ocr = shared_ocr or _build_ocr(args.ocr_engine, profile)
            pipeline = DigitizationPipeline(renderer, ocr, preprocessor=preprocessor)
            source_start = time.monotonic()
            source_started_at = utc_timestamp()
            page_started = source_start
            page_durations = []

            def report_progress(page_number: int, total_pages: int, _unused: float) -> None:
                nonlocal page_started
                now = time.monotonic()
                page_durations.append(now - page_started)
                page_started = now
                elapsed = now - source_start
                recent = sum(page_durations[-10:]) / len(page_durations[-10:])
                remaining = recent * (total_pages - page_number)
                print(f"[{page_number:>2}/{total_pages}] OCR complete ({page_durations[-1]:.1f}s/page; recent {recent:.1f}s/page) | elapsed {_format_duration(elapsed)} | ETA ~{_format_duration(remaining)}")

            result = _copy_source_pages(pipeline.run(pdf, source_work, progress_callback=report_progress), output_pages, source_index)
            source_duration = time.monotonic() - source_start
            source_ended_at = utc_timestamp()
            if first_report_page_text is None and profile == "prose" and result.pages:
                first_report_page_text = result.pages[0].text
            manuscript_parts.append(f"<!-- source-document: {pdf.name}; profile: {profile} -->\n" + assembler.assemble(result).rstrip())
            document_stats.append(DocumentStats(pdf.name, profile, len(result.pages), source_started_at, source_ended_at, round(source_duration, 3), round(source_duration / len(result.pages), 3) if result.pages else 0.0, [round(value, 3) for value in page_durations]))
            print(f"Completed {pdf.name}: {len(result.pages)} pages in {_format_duration(source_duration)}")
            print()

    metadata = extract_metadata(first_report_page_text or "")
    manuscript = build_front_matter(metadata) + "\n\n" + "\n\n".join(manuscript_parts).strip() + "\n"
    errors = validate_vtr_press_markdown(manuscript)
    if errors:
        raise SystemExit("VTR Press manuscript compatibility check failed:\n- " + "\n- ".join(errors))
    output.write_text(manuscript, encoding="utf-8")
    total_duration = time.monotonic() - overall_start
    total_pages = sum(item.pages for item in document_stats)
    stats = RunStats(run_started_at, utc_timestamp(), str(input_path), len(document_stats), total_pages, args.pdf_renderer, args.ocr_engine, args.preprocess, str(output), round(total_duration, 3), round(total_duration / total_pages, 3) if total_pages else 0.0, document_stats, args.combine_sources)
    stats_path = write_run_stats(stats, output.parent / "digitization" / "runs")
    print(f"Wrote Markdown: {output}")
    print(f"Source pages:   {output_pages}")
    print(f"Run statistics: {stats_path}")
    print(f"Documents:      {len(sources)}")
    print(f"Elapsed:        {_format_duration(total_duration)}")
    print("VTR Press compatibility: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
