from pathlib import Path

import pytest

from digitization.combined import (
    ProfileRoutingOCR,
    SourceSegment,
    combine_pdfs,
    combined_cache_valid,
    load_cached_segments,
    remap_result_pages,
    split_page_durations,
)
from digitization.pipeline import DigitizationResult, PageOCR


class FakeOCR:
    def __init__(self, label: str):
        self.label = label
        self.calls = []

    def ocr_image(self, image):
        self.calls.append(Path(image))
        return self.label


def test_profile_routing_ocr_routes_pages_in_order(tmp_path):
    prose = FakeOCR("prose")
    code = FakeOCR("code")
    segments = (
        SourceSegment(Path("report-01.pdf"), "prose", 1, 2),
        SourceSegment(Path("code-01.pdf"), "code", 3, 4),
    )
    router = ProfileRoutingOCR({"prose": prose, "code": code}, segments)
    assert [router.ocr_image(tmp_path / f"p{i}.png") for i in range(1, 5)] == ["prose", "prose", "code", "code"]
    assert len(prose.calls) == 2
    assert len(code.calls) == 2


def test_remap_result_pages_restores_original_provenance():
    segments = (
        SourceSegment(Path("report-01.pdf"), "prose", 1, 2),
        SourceSegment(Path("report-02.pdf"), "prose", 3, 4),
    )
    pages = tuple(PageOCR(Path("combined.pdf"), number, Path(f"p{number}.png"), f"page {number}") for number in range(1, 5))
    remapped = remap_result_pages(DigitizationResult(Path("combined.pdf"), pages), segments)
    assert [(page.source_pdf.name, page.page_number) for page in remapped] == [
        ("report-01.pdf", 1), ("report-01.pdf", 2), ("report-02.pdf", 1), ("report-02.pdf", 2)
    ]


def test_split_page_durations_preserves_source_boundaries():
    first = Path("report-01.pdf")
    second = Path("code-01.pdf")
    segments = (SourceSegment(first, "prose", 1, 2), SourceSegment(second, "code", 3, 5))
    result = split_page_durations([1.0, 2.0, 3.0, 4.0, 5.0], segments)
    assert result[first] == [1.0, 2.0]
    assert result[second] == [3.0, 4.0, 5.0]


def test_combine_pdfs_creates_one_pdf_and_page_map(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    first = tmp_path / "report-01.pdf"
    second = tmp_path / "code-01.pdf"
    for path, pages in ((first, 2), (second, 3)):
        document = pymupdf.open()
        for _ in range(pages):
            document.new_page()
        document.save(path)
        document.close()

    manifest = tmp_path / "manifest.json"
    combined, segments = combine_pdfs([(first, "prose"), (second, "code")], tmp_path / "combined.pdf", manifest)
    document = pymupdf.open(combined)
    try:
        assert len(document) == 5
    finally:
        document.close()
    assert segments[0].start_page == 1 and segments[0].end_page == 2
    assert segments[1].start_page == 3 and segments[1].end_page == 5
    assert combined_cache_valid(combined, manifest, [(first, "prose"), (second, "code")])
    assert load_cached_segments(manifest, [(first, "prose"), (second, "code")]) == segments


def test_combined_cache_invalidates_when_source_changes(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    source = tmp_path / "report-01.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(source)
    document.close()
    combined = tmp_path / "combined.pdf"
    manifest = tmp_path / "manifest.json"
    combine_pdfs([(source, "prose")], combined, manifest)
    assert combined_cache_valid(combined, manifest, [(source, "prose")])
    with source.open("ab") as handle:
        handle.write(b"changed")
    assert not combined_cache_valid(combined, manifest, [(source, "prose")])
