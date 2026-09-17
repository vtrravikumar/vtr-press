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
- `preprocess.py` — conservative image preprocessing boundary; the initial implementation preserves pages unchanged.
- `ocr.py` — Tesseract OCR adapter with configurable language, page segmentation mode, and extra arguments.
- `pipeline.py` — deterministic orchestration from PDF pages through preprocessing and OCR, with page-level provenance.
- `MarkdownAssembler` — produces a reviewable Markdown draft with source-PDF/page markers so every OCR fragment can be traced back to the scan.

The adapters intentionally depend on external executables rather than bundling an OCR/PDF runtime into VTR Press. This keeps the publishing engine portable and allows the runtime environment to be selected separately.

## Runtime requirements

The current concrete adapters expect these external tools to be available in the execution environment:

- Tesseract OCR (`tesseract`)
- Poppler's `pdftoppm`

VTR Press does not currently prescribe how those tools are installed. A future reproducible runtime may use a container or another managed environment. The important boundary is that the Python pipeline talks to small adapters, not directly to a specific operating-system package manager.

## Validation strategy

The next validation step is a small real-document run against representative scanned pages containing different source characteristics. The college project is particularly useful because it contains prose, tables, diagrams, numerical material, and source code.

Validation should compare the generated Markdown against the original scan before stronger preprocessing or source-type-specific extraction is introduced.

## Design principles

1. Keep digitization separate from parsing and rendering.
2. Prefer deterministic, reproducible processing.
3. Preserve the source faithfully; do not silently normalize content.
4. Treat OCR as an imperfect acquisition step, not as authoritative text.
5. Keep OCR engines behind a small adapter boundary so alternatives can be added later.
6. Keep external runtime dependencies outside the publishing engine's core model.
7. Test the pipeline with real-world documents containing prose, tables, diagrams, and code.
