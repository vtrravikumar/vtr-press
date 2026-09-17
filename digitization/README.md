# VTR Press Digitization

The `digitization` package is the upstream source-conversion layer of VTR Press.

Its purpose is to convert scanned or otherwise image-based source material into a **reviewable Markdown manuscript draft**. The existing VTR Press publishing pipeline remains responsible for parsing, interpreting, and rendering that manuscript.

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
        +-- figures / diagrams
        +-- tables
        +-- source-code handling
        |
        v
 Markdown draft
        |
        v
Existing VTR Press publishing pipeline
```

Digitization must not silently rewrite, modernize, or correct the source. OCR output is a draft and requires review, particularly for tables, technical terminology, diagrams, and source code.

## Current implementation

The current increment establishes the core, adapter-based pipeline:

- `pdf.py` — PDF-to-page rendering through a `pdftoppm` adapter.
- `preprocess.py` — conservative preprocessing with both an unchanged passthrough and a Pillow-based grayscale/contrast/threshold path.
- `ocr.py` — Tesseract OCR adapter with configurable language, page segmentation mode, and named profiles for prose, layout-heavy pages and code.
- `structure.py` — conservative OCR-text classification into broad `prose`, `code` and `layout` page types, with bounded confidence and reasons.
- `pipeline.py` — deterministic orchestration from PDF pages through preprocessing, OCR and optional structure classification, with page-level provenance.
- `MarkdownAssembler` — produces a reviewable Markdown draft with source-PDF/page markers and, when classification is enabled, structure/confidence markers.

Structure classification is deliberately conservative. It is a page-level routing and review aid, not a claim that OCR text can reconstruct tables or diagrams. Those require image/layout-aware handling in later increments.

The adapters intentionally depend on external executables rather than bundling an OCR/PDF runtime into VTR Press. This keeps the publishing engine portable and allows the runtime environment to be selected separately.

## Runtime requirements

The current concrete adapters expect these dependencies in the execution environment:

- Tesseract OCR (`tesseract`)
- Poppler's `pdftoppm`
- Python Pillow for image preprocessing

VTR Press does not prescribe how Tesseract or Poppler are installed. A future reproducible runtime may use a container or another managed environment. The important boundary is that the Python pipeline talks to small adapters, not directly to a specific operating-system package manager.

## Preprocessing policy

The original raster page is never modified. `PassthroughPreprocessor` preserves it byte-for-byte, while `PillowPreprocessor` writes a separate derived PNG.

The initial Pillow path deliberately limits transformations to:

- grayscale conversion;
- automatic contrast normalization;
- optional fixed-level thresholding.

Geometry-changing operations such as deskewing and cropping are intentionally deferred until they are validated against real scanned documents.

## Validation strategy

The first real-document validation used the historical college project report, including prose, title/certificate pages and source-code listings. That experiment showed that ordinary prose is viable as an OCR draft, while code, tables and diagrams require structure-aware handling and explicit review.

A controlled comparison of representative report and code pages found that grayscale/autocontrast can change OCR output modestly but does not establish a universal accuracy improvement. Fixed thresholding introduced additional recognition changes and therefore remains opt-in rather than a default transformation.

Validation should compare generated Markdown against the original scan after each preprocessing or classification change. A transformation or classifier is useful only if it supports faithful transcription and review without silently changing source meaning.

## Design principles

1. Keep digitization separate from parsing and rendering.
2. Prefer deterministic, reproducible processing.
3. Preserve the source faithfully; do not silently normalize content.
4. Treat OCR as an imperfect acquisition step, not as authoritative text.
5. Keep OCR engines behind a small adapter boundary so alternatives can be added later.
6. Keep external runtime dependencies outside the publishing engine's core model.
7. Never modify the authoritative source raster during preprocessing.
8. Use structure classification as a conservative review/routing aid, not as a substitute for visual inspection.
9. Test the pipeline with real-world documents containing prose, tables, diagrams, and code.
