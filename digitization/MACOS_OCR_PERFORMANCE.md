# macOS Vision OCR performance model

The macOS digitization path uses one `MacOSVisionOCR` instance for a complete multi-PDF CLI run.

The adapter lazily creates one `VNRecognizeTextRequest` and reuses that request for every rendered page. The CLI also creates the adapter once, before iterating over report and code PDFs, so the same Vision request survives PDF boundaries.

This is important because the college-project run previously created a new OCR adapter for every PDF. The observed run showed a large first-page startup cost on each of the six PDFs. The new architecture removes that deliberate per-PDF request reinitialization.

## What remains per page

A new `VNImageRequestHandler` is created for each image because each page is a separate image input. This is expected Vision usage; the recognition request is the reusable component.

## What remains per document

PDF rendering, preprocessing, page-level visual analysis, and provenance handling still happen per document. These are independent of the OCR request lifecycle.

## Validation

- Unit tests verify that one Vision recognition request is initialized and reused across multiple images.
- CLI tests verify that macOS Vision OCR is built once and shared across multiple PDFs.
- A future real college-project run should compare first-page timings before and after this change. The expected signature is one initial Vision startup cost followed by normal page processing, rather than a repeated startup spike at every PDF boundary.

The source scan remains authoritative; this optimization changes only OCR engine lifecycle, not OCR text handling or provenance.
