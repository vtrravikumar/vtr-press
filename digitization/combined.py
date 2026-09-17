"""Utilities for combining multi-part source PDFs into one digitization session."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from .pipeline import DigitizationResult, OCREngine, PageOCR


@dataclass(frozen=True)
class SourceSegment:
    """Logical source document and its page range in a combined PDF."""

    source_pdf: Path
    profile: str
    start_page: int
    end_page: int

    @property
    def pages(self) -> int:
        return self.end_page - self.start_page + 1


class ProfileRoutingOCR:
    """Route sequential OCR calls to engines according to source page ranges."""

    def __init__(self, engines: dict[str, OCREngine], segments: tuple[SourceSegment, ...]) -> None:
        self._engines = engines
        self._segments = segments
        self._page_index = 0

    def ocr_image(self, image: str | Path) -> str:
        self._page_index += 1
        for segment in self._segments:
            if segment.start_page <= self._page_index <= segment.end_page:
                return self._engines[segment.profile].ocr_image(image)
        raise RuntimeError(f"Combined PDF page {self._page_index} is outside the configured source segments")


def _source_fingerprints(sources: list[tuple[Path, str]]) -> list[dict[str, str]]:
    fingerprints = []
    for source_pdf, profile in sources:
        digest = hashlib.sha256()
        with source_pdf.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        fingerprints.append({"path": str(source_pdf.resolve()), "sha256": digest.hexdigest(), "profile": profile})
    return fingerprints


def combined_cache_valid(output_pdf: str | Path, manifest_path: str | Path, sources: list[tuple[Path, str]]) -> bool:
    """Return whether a cached combined PDF matches the current source set."""
    pdf = Path(output_pdf)
    manifest = Path(manifest_path)
    if not pdf.is_file() or not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return data.get("sources") == _source_fingerprints(sources) and data.get("combined_pdf") == pdf.name
    except (OSError, ValueError, TypeError):
        return False


def combine_pdfs(
    sources: list[tuple[Path, str]],
    output_pdf: str | Path,
    manifest_path: str | Path | None = None,
) -> tuple[Path, tuple[SourceSegment, ...]]:
    """Combine source PDFs and persist a manifest containing source fingerprints."""
    if not sources:
        raise ValueError("At least one source PDF is required")
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("--combine-sources requires PyMuPDF (package: pymupdf)") from exc

    destination = Path(output_pdf)
    destination.parent.mkdir(parents=True, exist_ok=True)
    combined = pymupdf.open()
    segments: list[SourceSegment] = []
    next_page = 1
    try:
        for source_pdf, profile in sources:
            document = pymupdf.open(source_pdf)
            try:
                page_count = len(document)
                if page_count == 0:
                    continue
                combined.insert_pdf(document)
            finally:
                document.close()
            segments.append(SourceSegment(source_pdf, profile, next_page, next_page + page_count - 1))
            next_page += page_count
        combined.save(destination)
    finally:
        combined.close()

    if manifest_path is not None:
        manifest = Path(manifest_path)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "combined_pdf": destination.name,
            "page_count": next_page - 1,
            "sources": _source_fingerprints(sources),
            "segments": [
                {"source": str(s.source_pdf.resolve()), "profile": s.profile, "start_page": s.start_page, "end_page": s.end_page}
                for s in segments
            ],
        }
        manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination, tuple(segments)


def load_cached_segments(manifest_path: str | Path, sources: list[tuple[Path, str]]) -> tuple[SourceSegment, ...]:
    """Load source/page mapping from a valid combined-cache manifest."""
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if data.get("sources") != _source_fingerprints(sources):
        raise ValueError("Combined PDF cache manifest does not match current sources")
    return tuple(
        SourceSegment(Path(item["source"]), item["profile"], int(item["start_page"]), int(item["end_page"]))
        for item in data["segments"]
    )


def remap_result_pages(result: DigitizationResult, segments: tuple[SourceSegment, ...]) -> tuple[PageOCR, ...]:
    remapped: list[PageOCR] = []
    for page in result.pages:
        segment = next((item for item in segments if item.start_page <= page.page_number <= item.end_page), None)
        if segment is None:
            raise RuntimeError(f"No source mapping exists for combined PDF page {page.page_number}")
        original_page = page.page_number - segment.start_page + 1
        remapped.append(replace(page, source_pdf=segment.source_pdf, page_number=original_page))
    return tuple(remapped)


def split_page_durations(page_durations: list[float], segments: tuple[SourceSegment, ...]) -> dict[Path, list[float]]:
    result: dict[Path, list[float]] = {}
    for segment in segments:
        result[segment.source_pdf] = page_durations[segment.start_page - 1:segment.end_page]
    return result
