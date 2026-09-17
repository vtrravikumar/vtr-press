# VTR Press Digitization

The `digitization` package is the upstream source-conversion layer of VTR Press.

Its purpose is to convert scanned or otherwise image-based source material into a **reviewable, VTR Press-compatible Markdown manuscript**. The existing VTR Press publishing pipeline remains responsible for parsing, interpreting, and rendering that manuscript.

## Architectural boundary

```text
Source PDF / scans
        |
        v
   Digitization
        |
        +-- page extraction
        +-- image preprocessing
        +-- OCR
        +-- structure classification
        +-- VTR Press metadata
        +-- Markdown heading normalization
        +-- compatibility validation
        +-- source-image preservation
        +-- figures / diagrams
        +-- tables
        |     +-- table detection
        |     +-- grid boundaries
        |     +-- cell crops / OCR
        |     +-- later Markdown conversion
        +-- source-code handling
        |
        v
 VTR Press-compatible manuscript.md
        |
        v
Existing VTR Press publishing pipeline
```

Digitization must not silently rewrite, modernize, or correct the source. OCR output is a draft and requires review, particularly for tables, technical terminology, diagrams, and source code.

## Current implementation

The current increment establishes the core, adapter-based pipeline:

- `pdf.py` — PDF-to-page rendering through a `pdftoppm` adapter.
- `pdf_pymupdf.py` — pip-installable PyMuPDF renderer for local macOS use without Poppler.
- `preprocess.py` — conservative preprocessing with both an unchanged passthrough and a Pillow-based grayscale/contrast/threshold path.
- `ocr.py` — Tesseract OCR adapter with configurable language, page segmentation mode, and named profiles for prose, layout-heavy pages and code.
- `ocr_macos.py` — macOS-native Apple Vision OCR through the pip-installable `ocrmac` package.
- `structure.py` — conservative OCR-text classification into broad `prose`, `code` and `layout` page types, with bounded confidence and reasons.
- `compatibility.py` — VTR Press metadata template generation, conservative heading normalization and manuscript compatibility validation.
- `assets.py` — byte-preserving helper for copying rendered source-page images into a stable asset directory.
- `review.py` — conservative review-marker generation for structure-sensitive pages and a small set of suspicious OCR glyph patterns.
- `layout.py` — conservative visual analysis that detects ruled-table signals and records source-image regions, row boundaries and column boundaries.
- `table.py` — layout-aware table cell extraction that crops individual cells from the original source image and can send each crop through an existing OCR adapter. It intentionally does not yet promote OCR output to semantic Markdown.
- `pipeline.py` — deterministic orchestration from PDF pages through preprocessing, OCR and structure classification, with page-level provenance and heading normalization.
- `stats.py` — machine-readable timestamped run statistics, including per-document and per-page timing data.
- `cli.py` / `__main__.py` — repeatable command-line PDF-to-Markdown workflow, including multi-PDF project-source batching and compatibility validation.
- `MarkdownAssembler` — produces a reviewable Markdown draft with source-PDF/page markers, structure/confidence markers and review markers. It can optionally embed the original rendered page image for layout-heavy pages.

Structure classification is deliberately conservative. It is a page-level routing and review aid, not a claim that OCR text can reconstruct tables or diagrams. Tables now have a separate spatial-analysis path: detected grids can be decomposed into cell regions, and those regions can be OCR'd independently. This still requires review before semantic Markdown generation.

## Table extraction path

For a detected ruled table, `TableGrid` records the source-image column and row boundaries. Its cell regions are derived deterministically from those boundaries. `extract_table_cells()` then writes stable PNG crops such as:

```text
cells/
    cell-r01-c01.png
    cell-r01-c02.png
    cell-r02-c01.png
    ...
```

An OCR adapter can be supplied to obtain text independently for each cell. The resulting `ExtractedTable` keeps the row/column relationship intact. This is deliberately an intermediate representation: **it does not silently invent headers, merge cells, infer alignment, or emit Markdown yet**.

The eventual target is standard Markdown table syntax consumed by the existing VTR Press table model. If spatial confidence is insufficient, the source-page image remains the authoritative fallback.
