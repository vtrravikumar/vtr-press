"""Utilities for combining multi-part source PDFs into one digitization session."""

from __future__ import annotations

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
    """Route sequential OCR calls to engines according to source page ranges.

    The pipeline calls OCR once per rendered page in order. This adapter keeps
    that ordering while allowing a physically combined PDF to retain the
    original per-document OCR profiles.
    """

    def __init__(
        self,
        engines: dict[str, OCREngine],
        segments: tuple[SourceSegment, ...],
    ) -> None:
        self._engines = engines
        self._segments = segments
        self._page_index = 0

    def ocr_image(self, image: str | Path) -> str:
        self._page_index += 1
        for segment in self._segments:
            if segment.start_page <= self._page_index <= segment.end_page:
                return self._engines[segment.profile].ocr_image(image)
        raise RuntimeError(
            f"Combined PDF page {self._page_index} is outside the configured source segments"
        )


def combine_pdfs(
    sources: list[tuple[Path, str]],
    output_pdf: str | Path,
) -> tuple[Path, tuple[SourceSegment, ...]]:
    """Combine source PDFs and return the logical source/page mapping.

    PyMuPDF is imported lazily because combining is an optional optimization;
    normal digitization does not require it.
    """
    if not sources:
        raise ValueError("At least one source PDF is required")

    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "--combine-sources requires PyMuPDF (package: pymupdf)"
        ) from exc

    destination = Path(output_pdf)
    destination.parent.mkdir(parents=True, exist_ok=True)
    combined = fitz.open()
    segments: list[SourceSegment] = []
    next_page = 1
    try:
        for source_pdf, profile in sources:
            document = fitz.open(source_pdf)
            try:
                page_count = len(document)
                if page_count == 0:
                    continue
                combined.insert_pdf(document)
            finally:
                document.close()
            segments.append(
                SourceSegment(
                    source_pdf=source_pdf,
                    profile=profile,
                    start_page=next_page,
                    end_page=next_page + page_count - 1,
                )
            )
            next_page += page_count
        combined.save(destination)
    finally:
        combined.close()

    return destination, tuple(segments)


def remap_result_pages(
    result: DigitizationResult,
    segments: tuple[SourceSegment, ...],
) -> tuple[PageOCR, ...]:
    """Restore original PDF/page provenance after combined processing."""
    remapped: list[PageOCR] = []
    for page in result.pages:
        segment = next(
            (
                item
                for item in segments
                if item.start_page <= page.page_number <= item.end_page
            ),
            None,
        )
        if segment is None:
            raise RuntimeError(
                f"No source mapping exists for combined PDF page {page.page_number}"
            )
        original_page = page.page_number - segment.start_page + 1
        remapped.append(
            replace(
                page,
                source_pdf=segment.source_pdf,
                page_number=original_page,
            )
        )
    return tuple(remapped)


def split_page_durations(
    page_durations: list[float],
    segments: tuple[SourceSegment, ...],
) -> dict[Path, list[float]]:
    """Split combined-run page timings back into logical source documents."""
    result: dict[Path, list[float]] = {}
    for segment in segments:
        start = segment.start_page - 1
        end = segment.end_page
        result[segment.source_pdf] = page_durations[start:end]
    return result
