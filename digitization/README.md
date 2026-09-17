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

The first increment provides a small Tesseract adapter in `ocr.py`. PDF page rendering, preprocessing, manuscript assembly, and source-type-aware extraction will be added incrementally after they are validated against real scanned documents.

## Design principles

1. Keep digitization separate from parsing and rendering.
2. Prefer deterministic, reproducible processing.
3. Preserve the source faithfully; do not silently normalize content.
4. Treat OCR as an imperfect acquisition step, not as authoritative text.
5. Keep OCR engines behind a small adapter boundary so alternatives can be added later.
6. Test the pipeline with real-world documents containing prose, tables, diagrams, and code.
