# Layout Analysis

The digitization pipeline now performs a conservative visual pass over each **original rendered source page** in addition to OCR text classification.

## Purpose

OCR text alone cannot reliably represent tables, diagrams, plots, or other spatial structures. The visual pass therefore records signals for human review without attempting to reconstruct the source incorrectly.

Detected signals are:

- `table` — strong ruled-grid signals from horizontal and vertical page lines;
- `diagram` — line-structure signals without a strong ruled grid;
- `figure` — substantial non-white visual density without the preceding signals.

These are deliberately named `*_likely` in the API. They are review hints, not semantic recognition claims.

## Markdown output

When a signal is detected, the generated manuscript receives a provenance comment such as:

```markdown
<!-- visual-structure: table; confidence: 0.70; reasons: ruled-grid-signals -->
<!-- review-marker: table-visual-verification -->
```

The original source page remains available through the existing `source-image` reference. No OCR text is changed and no source raster is modified.

## Why extraction is not automatic yet

A reliable figure/table extractor needs spatial OCR regions and stronger document-layout analysis. The current increment intentionally establishes the review boundary first. Individual figures and tables should only be emitted as Markdown image/table elements after the extraction algorithm has been validated against real scanned pages.

The college project remains the regression document for this work because it contains prose, tables, diagrams, numerical results, and source code in one historical report.
