# VTR Press Roadmap

## Vision

VTR Press is evolving from a book publishing toolkit into a general-purpose publishing platform capable of producing multiple document types from a single manuscript.

The long-term goal is to allow authors to focus entirely on writing while VTR Press automatically applies appropriate publishing conventions.

---

# Current Status

Current capabilities include:

- Markdown manuscript support
- PDF publishing
- EPUB publishing
- Book publishing workflow
- Technical-document publishing
- Generic Document Model
- Native technical-document Typst and EPUB rendering
- Technical-document asset resolution and persistent generated asset staging
- Ordered and unordered lists
- Deeper heading hierarchy
- Code blocks and JSON
- External image assets in PDF and EPUB

The v0.9.1 release completes the D3/D4 generic technical-document
publishing pipeline. The next isolated implementation task is native
Markdown table rendering for technical documents.

---

# Near-Term Goals

## Document Types

Introduce support for multiple document classes while preserving a common manuscript format.

Initial support includes:

- Book
- Technical Document

---

## Publishing Engine

Continue evolving the publishing engine through:

- Common document model
- Shared publishing pipeline
- Automatic theme selection
- Backward compatibility

---

## Architecture Evolution

Continue improving the architecture through small, incremental refactorings.

Every architectural improvement should:

- deliver user value
- preserve a releasable product
- reduce technical debt
- improve extensibility
- avoid unnecessary rewrites

The objective is continuous architectural improvement rather than large redesign efforts.

---

## Reference Manuscripts

Maintain representative manuscripts that validate the publishing workflow.

Current reference manuscripts include:

- Engineering Memoir
- RideTogether Solution Architecture Document

These manuscripts serve as regression tests for architectural evolution and publishing capabilities.

---

### Architecture Review Pack

Generate a concise Architecture Review Pack directly from a Solution Architecture manuscript.

The Review Pack is a derived artifact generated from the technical document and is intended for architecture reviews, steering committees, and technical governance meetings.

Goals:

- Single source of truth.
- No duplicated presentation.
- Approximately 10-page executive architecture summary.
- Automatically generated from the Solution Architecture manuscript.
- PDF output initially.
- Additional outputs (HTML, speaker notes, executive summaries) may follow.

# Future Direction

Future document types may include:

- White Paper
- User Guide
- Design Specification
- API Reference
- Research Paper

Future output formats may include:

- HTML
- DOCX

These additions should extend the publishing platform without changing the manuscript specification.

---

# Guiding Principle

A manuscript should be written once and published anywhere.

As VTR Press evolves, the manuscript remains the stable public contract while the publishing engine continues to expand its capabilities through incremental evolution.