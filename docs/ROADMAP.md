# VTR Press Roadmap

## Vision

VTR Press is evolving from a book publishing toolkit into a general-purpose publishing platform capable of producing multiple document types from a single manuscript.

The long-term goal is to allow authors to focus on writing while VTR Press automatically applies appropriate publishing conventions.

---

# Current Status — v2.0

VTR Press v2.0 establishes the generic document architecture and shared rendering infrastructure as the production foundation for the publishing platform.

Current capabilities include:

- Markdown manuscript support
- Book publishing workflow
- Technical-document publishing
- Generic Document Model
- Interpretation layer for document semantics and conventions
- PDF publishing through Typst
- EPUB publishing
- Common Typst rendering infrastructure
- Book and Technical Typst renderers
- Common EPUB rendering infrastructure
- Book and Technical EPUB renderers
- Technical-document asset resolution and persistent generated asset staging
- Ordered and unordered lists
- Deeper heading hierarchy
- Code blocks and JSON
- Markdown tables
- External image assets in PDF and EPUB
- Shared publication asset handling

The v2.0 migration is complete. The generic document architecture is established, while proven book-specific implementation structures remain where they continue to provide value.

The renderer architecture intentionally separates common format-level behaviour from document-type-specific publication behaviour.

```text
                 Document / Interpretation
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        Common Typst              Common EPUB
              │                         │
        ┌─────┴─────┐             ┌─────┴─────┐
        ▼           ▼             ▼           ▼
      Book      Technical       Book      Technical
      Typst       Typst         EPUB        EPUB
```

---

# Near-Term Goals

The next phase should build on the v2.0 foundation rather than repeat the migration work.

## 1. Publishing Quality

Continue improving the quality and consistency of published output.

Focus areas include:

- PDF typography and layout
- EPUB structure and reading experience
- cross-format consistency
- metadata handling
- image and asset behaviour
- regression coverage for real manuscripts

---

## 2. Document Capabilities

Extend the generic document model when a capability represents a genuine document-level concept.

Potential areas include:

- richer tables
- additional block types
- links and cross-references
- footnotes and endnotes
- references and citations
- callouts or admonitions

New capabilities should be added to the document model and interpretation layer before being implemented independently in renderers.

---

## 3. Book and Technical Rendering

Continue refining the document-type-specific renderers while keeping common format behaviour centralized.

The guiding structure is:

```text
Typst
├── Common
├── Book
└── Technical

EPUB
├── Common
├── Book
└── Technical
```

Common rendering code should remain genuinely shared. Document-type-specific conventions should remain in the corresponding Book or Technical renderer.

---

## 4. Architecture Evolution

Continue improving the architecture through small, incremental refactorings.

Every architectural improvement should:

- deliver user value
- preserve a releasable product
- reduce technical debt
- improve extensibility
- avoid unnecessary rewrites

The objective is continuous architectural improvement rather than large redesign efforts.

Legacy book-specific structures may be simplified or migrated when there is a concrete benefit, but their removal is not a goal in itself.

---

## 5. Reference Manuscripts

Maintain representative manuscripts that validate the publishing workflow.

Current reference manuscripts include:

- Engineering Memoir
- RideTogether Solution Architecture Document

These manuscripts serve as regression references for architectural evolution and publishing capabilities.

---

# Proposed Capability — Architecture Review Pack

Generate a concise Architecture Review Pack directly from a Solution Architecture manuscript.

The Review Pack would be a derived artifact generated from the technical document and intended for architecture reviews, steering committees, and technical governance meetings.

Goals:

- Single source of truth
- No duplicated presentation
- Approximately 10-page executive architecture summary
- Automatically generated from the Solution Architecture manuscript
- PDF output initially
- Additional outputs such as HTML, speaker notes, or executive summaries may follow

**Status: Proposed — not part of the current v2.0 publishing pipeline.**

---

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

> **A manuscript should be written once and published anywhere.**

As VTR Press evolves, the manuscript remains the stable public contract while the publishing engine continues to expand its capabilities through incremental evolution.
