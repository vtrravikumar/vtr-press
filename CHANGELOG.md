# HomeLab Engineering
## Changelog

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