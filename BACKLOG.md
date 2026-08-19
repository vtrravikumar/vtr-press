# VTR Press Backlog

This document tracks ideas, improvements and future capabilities that are
intentionally deferred from the current VTR Press migration.

The current architectural migration is tracked separately in:

- `docs/MIGRATIONPLAN.md`
- `docs/ENGINEERING_PLAN.md`

Phase D work must not be duplicated here.

---

# Current / Near-Term

## Test Automation

**Status: Substantially Complete**

The VTR Press test suite currently includes:

- Parser unit tests
- Renderer tests
- Regression tests
- Technical-document tests
- Book regression coverage
- End-to-end manuscript validation
- Fresh-clone verification

The current suite has been repeatedly validated as part of the migration.

**Remaining:**

- GitHub Actions automated test workflow

---

## Markdown Compatibility

**Status: Backlog**

Improve Markdown compatibility and CommonMark support.

Potential improvements:

- Escaped Markdown characters
- Nested emphasis
- Additional CommonMark-compatible syntax
- Other Markdown constructs identified through real manuscript usage

New Markdown support should be evaluated against the VTR Press manuscript
contract rather than added as isolated renderer-specific features.

---

## Line Break Support

**Status: Backlog**

Complete and verify support for the `LineBreak` AST node across:

- Parser
- Document Model
- Typst renderer
- EPUB renderer

The exact implementation should be verified against the current code before
work begins, as the current repository state may already contain partial
support.

---

## Performance

**Status: Backlog**

Performance improvements should be driven by measurement rather than
premature optimization.

Potential work:

- Profile parser performance
- Profile rendering performance
- Reduce unnecessary string allocations
- Reduce repeated document traversal
- Improve PDF/EPUB generation performance where measurable

---

# Publishing Capabilities

## Kindle Output

**Status: Future**

Investigate Kindle publishing support, including:

- KPF generation
- Kindle Previewer compatibility
- Kindle-specific EPUB requirements
- Whether VTR Press should generate Kindle-ready EPUB or directly generate
  KPF

This should be evaluated against the existing PDF/EPUB publishing pipeline
rather than becoming a separate publishing architecture.

---

## HTML Renderer

**Status: Future**

Investigate an HTML renderer for technical documents and other supported
document types.

Potential future use cases:

- Standalone HTML documentation
- Web publishing
- Documentation previews

The renderer should consume the same interpreted Document Model used by the
other output formats.

---

## DOCX Renderer

**Status: Future**

Research feasibility of generating DOCX output.

The investigation should determine:

- Required Document Model capabilities
- Mapping of headings and structural elements
- Typography and layout limitations
- Whether DOCX is a worthwhile supported output format

---

## PDF Theme Gallery

**Status: Future**

Expand the built-in theme collection beyond the current themes.

Potential future themes include:

- Paperback
- Modern
- Additional technical/documentation themes
- Other print-oriented themes

Theme selection should continue to be driven by document type/convention
rather than requiring manual renderer configuration.

---

# Document Features

## Footnotes

**Status: Future**

Support footnotes as a first-class manuscript/document feature.

---

## Index Generation

**Status: Future**

Investigate automatic index generation for book-length documents.

---

## Glossary Generation

**Status: Future**

Investigate glossary support and automatic glossary generation.

---

## Bibliography

**Status: Future**

Investigate bibliography and reference-management support.

Potential future considerations:

- Bibliography metadata
- Citation syntax
- Reference rendering
- Output-specific formatting

---

## Image Captions

**Status: Future**

Support captions for manuscript images and define consistent rendering
across PDF, EPUB and future output formats.

---

## Cross References

**Status: Future**

Support references between document sections, figures, tables and other
structural elements.

Potential requirements:

- Stable identifiers
- Internal links
- Output-specific reference rendering

---

## Syntax-Highlighted Code Blocks

**Status: Partially implemented**

Basic fenced code blocks are now supported by the generic technical-document
pipeline, including JSON/code content validation in D4.

Remaining future work:

- Language identification
- Syntax highlighting
- More sophisticated Typst rendering
- More sophisticated EPUB rendering


This is particularly relevant to technical-document manuscripts and VTR
Press's own technical documentation.

Potential requirements:

- Fenced code blocks
- Language identification
- Syntax highlighting
- Typst rendering
- EPUB rendering
- Future HTML rendering

The generic Document Model introduced by Phase D should be evaluated for its
ability to accommodate this feature without parser-specific coupling.

---

# Extensibility

## Custom Theme Support

**Status: Future**

Theme architecture and responsibilities are already documented as part of
the current VTR Press architecture.

Future work may provide a clearer workflow for creating and registering
custom themes.

Potential documentation:

- Theme structure
- Theme file responsibilities
- Theme registration
- Creating a custom theme
- Theme testing

No additional theme framework should be introduced unless real use cases
justify it.

---

## Plugin Architecture

**Status: Future**

Investigate whether VTR Press should support third-party extensions such
as:

- Custom renderers
- Custom themes
- Additional document conventions
- Additional output formats

This is intentionally deferred until the core architecture has proven
stable.

The internal Interpretation layer being introduced in Phase D is NOT a
plugin architecture. It is a core VTR Press component.

---

# Productization

## VTR Press 1.0 Release Criteria

**Status: Future**

Define the criteria required for a stable VTR Press 1.0 release.

Potential areas:

- Supported manuscript contract
- Supported document types
- Supported output formats
- Theme stability
- Error handling
- Test coverage
- Documentation
- Installation and distribution

---

## Documentation Website

**Status: Future**

Consider publishing VTR Press documentation as a web-based documentation
site.

The technical-document manuscript format should remain reusable regardless
of the eventual web publishing mechanism.

---

## PyPI Package

**Status: Future**

Investigate packaging VTR Press for installation through PyPI.

Potential requirements:

- Package structure
- CLI entry point
- Theme/resource packaging
- Version management
- Installation documentation

---

## Homebrew Installation

**Status: Future**

Investigate providing VTR Press through Homebrew once the CLI and package
structure are stable.

---

# V2 / Future Input and Discovery

These items are deliberately parked for a future evolution of VTR Press.

They do NOT imply creating a separate VTR Press V2 product or rewriting the
core publishing pipeline.

The current `books.yaml` mechanism remains valid for the current migration.

---

## V2-001 — Reduce `books.yaml` Dependency

**Status: Backlog**

### Problem

The current `run.py` workflow depends on `books.yaml` containing an explicit
entry for each manuscript, including its name, filepath, type, cover and
other publishing details.

This works well for a small number of books, but becomes unnecessary
administrative overhead as the number of technical documents grows.

Technical documents already contain their own front-matter metadata and
should not require a separate manifest entry merely to identify the
manuscript.

### Future Direction

Explore a simpler manuscript-discovery mechanism in which VTR Press can
discover manuscripts from configured directories and use the manuscript's
front matter as the authoritative source for document metadata.

The existing `books.yaml` mechanism should remain supported until a
replacement is designed, implemented and validated.

---

## V2-002 — Directory-Level Publishing

**Status: Backlog**

### Problem

For a directory containing multiple technical-document manuscripts, it is
unnecessary to maintain an explicit filename/path entry for every document.

### Future Direction

Allow VTR Press to discover and process all valid technical-document
manuscripts within a designated directory and generate the corresponding
PDF/EPUB outputs without requiring an individual manifest entry for every
file.

The exact discovery rules, CLI syntax, output conventions and interaction
with `books.yaml` are intentionally left open for future design.

---

## V2-003 — Simplified Publishing Input Model

**Status: Backlog**

### Problem

The current publishing workflow couples manuscript discovery with the
publishing manifest (`books.yaml`).

As VTR Press evolves to support many technical documents, manuscript
discovery, document metadata and publishing configuration should be
separated more cleanly.

### Future Direction

Explore a simpler input model that could eventually support publishing:

- A single manuscript directly
- A directory of manuscripts
- A collection of manuscripts discovered by convention

while retaining the existing publishing pipeline:

    Manuscript
        ↓
    Reader / Parser
        ↓
    Interpretation
        ↓
    Document Model
        ↓
    Renderer
        ↓
    PDF / EPUB

This is an evolution of the input/discovery layer, not a reason to create a
separate VTR Press V2 product or rewrite the publishing pipeline.

---

## V2 Scope Decision

These items are deliberately parked for future work.

They are NOT part of the current Phase D migration and must not influence
D1–D4 implementation.

For the current migration:

- `books.yaml` remains the publishing input mechanism.
- `run.py` continues to use the existing manifest.
- No automatic manuscript discovery is introduced.
- No directory-level publishing is introduced.
- No CLI/input-model redesign is undertaken.

The future objective is to simplify manuscript discovery and publishing
management without requiring a rewrite of the core VTR Press architecture.

---

# Deferred Ideas

The following ideas are intentionally retained without committing to a
specific implementation or priority.

- Advanced typography controls
- More sophisticated table support
- Advanced image handling
- Multiple output profiles
- Additional publishing workflows
- Additional document conventions/types
- Other features identified through real manuscript usage

New ideas should be evaluated against the current architecture before being
added to the implementation roadmap.

---

# Backlog Governance

The backlog is intentionally separate from the active migration plan.

Items should be:

- Removed when they are implemented or superseded
- Updated when architectural decisions change their scope
- Promoted into `MIGRATIONPLAN.md` when they become active migration work
- Kept as backlog items when they are useful but not currently justified
- Avoided as speculative architecture unless a real use case requires it

The goal is to keep the backlog small, current and useful rather than
turning it into a historical list of every idea ever discussed.