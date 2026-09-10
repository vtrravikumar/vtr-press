# VTR Press Status

Current milestone: **v2.0 architecture complete**

Branch: `main`

Status: **Post-v2 development baseline**

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

The production pipeline is:

`Manuscript → Parser → Generic Document Model → Interpretation → Common Typst / Common EPUB → Book / Technical renderers → PDF / EPUB`

The proven Book publishing path is retained where Book-specific structures remain useful. This is intentional and is not considered incomplete migration work.

## Current Engineering Position

- The v2 architecture migration is complete.
- `main` is the current development baseline.
- Technical-document publishing is operational through the generic pipeline.
- Markdown tables are implemented as native tables in technical Typst and EPUB output.
- Current work is incremental publishing-platform evolution, not further architectural migration.
- The latest repository work is focused on theme and print-layout refinement.

## Next

The engineering backlog is intentionally at the post-v2 feature stage.

When feature work resumes, the leading candidates are:

1. BL-001 — Simplify Manuscript Discovery and Publishing Input
2. BL-003 — Cross References
3. BL-004 — Image Captions
4. BL-005 — Language-aware syntax highlighting
5. BL-002 — Markdown Compatibility

No current architectural rewrite is planned.

## Validation

GitHub Actions runs the regression suite on pushes and pull requests.

The repository status should remain synchronized with the implementation, engineering plan, roadmap, and backlog.
