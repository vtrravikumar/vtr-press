# VTR Press
## Changelog

All significant VTR Press engineering and release changes are recorded here.

The format loosely follows Keep a Changelog.

---

## [Unreleased]

This section records post-v0.9.1 work that is present on `main` but has not been assigned a new release version.

### Changed

- Completed the v2.0 generic document architecture and shared rendering foundation.
- Established the production pipeline from Markdown manuscript through the generic document model, interpretation, format-level rendering, and document-type renderers.
- Preserved the established Book publishing path while adding the generic Technical Document path.
- Refined print-book page dimensions and cover/theme presentation.

### Added

- Native Markdown table support in technical-document Typst output.
- Native Markdown table support in technical-document EPUB output.
- Generic document-model support for tables, images, lists, and deeper heading structures.
- Persistent generated asset staging for technical-document publishing.

### Improved

- Technical-document asset resolution and external image handling.
- Technical-document PDF and EPUB rendering.
- Regression coverage for the generic model, interpretation layer, tables, images, lists, and technical publishing paths.

### Current engineering position

- v2.0 architecture is complete.
- `main` is the current post-v2 development baseline.
- Current work is incremental publishing-platform evolution rather than further architectural migration.

---

## v0.9.1

Completed the D3/D4 generic technical-document publishing pipeline.

### Added

- Generic Document Model support for technical documents
- Technical-document dispatch
- Native Typst technical-document rendering
- Native EPUB technical-document rendering
- Technical-document asset resolution
- Persistent generated asset staging
- External image assets in PDF and EPUB
- Ordered and unordered lists
- Deeper heading hierarchy
- Code blocks and JSON
- Validation using multiple technical documents
- PDF and EPUB publication artifacts
- ISBN publication artifacts

### Validation

- `RideTogether EngineeringDesign.md`
- `APIEngineeringReference.md`
- Full regression suite: **207 passed**

### Note

The former release documentation described Markdown tables as a limitation. Native Markdown table support has since been added in the post-v0.9.1 development line.

## v0.9.0

Completed the technical-document rendering capability used as the foundation for the generic D3/D4 pipeline, including technical subheadings and renderer support.

---

## Historical manuscript development notes

The entries below preserve the earlier manuscript-development history.

---

## [v0.5 Reader Draft]

### Added

- Complete manuscript
- Editorial review
- Reader review
- External review

### Changed

- Repository organization
- Chapter structure
- Reading draft assembly

---

## v0.6.0 - 2026-07-30

### Added

- EPUB renderer
- Scene support for memoir-style manuscripts

### Improved

- Escaped Typst text and string literals
- Escaped metadata, headings, scenes and verses
- Hardened Typst renderer against special characters
- Validated YAML front matter structure
- Improved overall publishing robustness

### Fixed

- Prevented invalid Typst generation from unescaped manuscript content
- Invalid YAML mappings now raise FrontMatterError

## v0.7.1 - 2026-07-31

### Fixed

- Fixed front matter rendering regression introduced by theme externalization.
- Corrected Dedication page rendering.
- Restored consistent A5 layout across all front matter pages.
