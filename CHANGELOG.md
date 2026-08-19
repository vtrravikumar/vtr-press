# VTR Press
## Changelog

All significant VTR Press engineering and release changes are recorded here.

The format loosely follows Keep a Changelog.

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

### Known limitation

- Markdown tables currently do not render as native tables in the
  technical-document PDF/Typst output.

## v0.9.0

Completed the technical-document rendering capability used as the
foundation for the generic D3/D4 pipeline, including technical
subheadings and renderer support.

---

## Historical manuscript development notes

# VTR Press
## Changelog

All significant VTR Press engineering and release changes are recorded here.

The format loosely follows Keep a Changelog.

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

### Known limitation

- Markdown tables currently do not render as native tables in the
  technical-document PDF/Typst output.

## v0.9.0

Completed the technical-document rendering capability used as the
foundation for the generic D3/D4 pipeline, including technical
subheadings and renderer support.

---

## Historical manuscript development notes


All significant manuscript changes are recorded here.

The format loosely follows Keep a Changelog while remaining focused on manuscript development.

---

## [Unreleased]

### Added

-

### Changed

-

### Improved

-

### Removed

-

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