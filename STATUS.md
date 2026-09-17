# VTR Press Status

Current milestone: **v2.0 architecture complete**

Branch: `main`

Status: **Post-v2 development baseline — digitization in progress**

## Current State

VTR Press v2 establishes the generic document architecture and shared rendering infrastructure as the production foundation.

Stable capabilities include:

- `book` documents
- `technical-document` documents
- Generic Document Model
- Document interpretation layer
- Technical-document dispatch
- Native Typst technical-document rendering
- Native EPUB technical-document rendering
- Shared format-level rendering infrastructure
- Technical-document asset resolution and persistent generated asset staging
- Ordered and unordered lists
- Deeper heading hierarchy
- Code blocks / JSON
- Markdown tables
- External image assets in PDF and EPUB
- PDF and EPUB generation
- Print-book PDF pagination conventions
- ISBN publication artifacts
- Automated regression coverage

## Architecture

The production publishing pipeline remains:

`Manuscript → Parser → Generic Document Model → Interpretation → Common Typst / Common EPUB → Book / Technical renderers → PDF / EPUB`

Digitization is an upstream acquisition layer:

`Scanned source → page rendering → preprocessing → OCR → structure classification → reviewable Markdown → publishing pipeline`

The proven Book publishing path is retained where Book-specific structures remain useful. This is intentional and is not considered incomplete migration work.

## Current Engineering Position

- The v2 architecture migration is complete.
- `main` is the current development baseline.
- Technical-document publishing is operational through the generic pipeline.
- Markdown tables are implemented as native tables in technical Typst and EPUB output.
- Digitization now has PDF rendering, OCR, conservative preprocessing, page provenance, structure classification and code-safe review handling.
- Real scanned college-project validation has been completed, including controlled preprocessing comparison.
- The digitization work remains incremental and is not yet considered a complete production CLI/API feature.

## Active Work — BL-012

**Document Digitization / OCR Pipeline — P1, candidate for v2.2**

Completed in the current increment:

1. PDF/page rendering adapter
2. Tesseract OCR adapter and OCR profiles
3. Conservative preprocessing
4. Page-level provenance
5. `prose` / `code` / `layout` classification with bounded confidence
6. Code-safe Markdown review treatment
7. Regression fixtures for broad structure classification
8. Real-document validation documentation

Remaining:

1. Table/figure preservation and extraction strategy
2. Expanded review/confidence markers
3. Stronger real-image regression fixtures
4. Practical end-to-end CLI/API workflow
5. Validation against the second document case
6. Final production-readiness review

## Other Backlog Candidates

After digitization work reaches a stable handover point, the broader post-v2 backlog remains available, including:

- BL-001 — Simplify Manuscript Discovery and Publishing Input
- BL-003 — Cross References
- BL-004 — Image Captions
- BL-005 — Language-aware syntax highlighting
- BL-002 — Markdown Compatibility
- BL-011 — Multiple Authors / Author Metadata (v2.1)

No architectural rewrite is planned.

## Validation

GitHub Actions runs the regression suite on pushes and pull requests. The repository status should remain synchronized with the implementation, engineering plan, roadmap, and backlog.
