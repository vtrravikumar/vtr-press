# VTR Press Publishing Principles

## Purpose

VTR Press is a publishing platform that transforms a simple, human-readable manuscript into professionally published documents.

The author's responsibility is to describe the content.

The publishing system's responsibility is to understand the document and determine its presentation.

---

# Convention over Configuration

Authors should not be required to understand page layouts, typography, or rendering engines.

Document conventions are selected automatically based on the document type.

Example:

```yaml
type: technical-document
```

should automatically apply the appropriate publishing conventions.

---

# Single Source of Truth

A manuscript should be written once and published in multiple formats without modification.

Supported outputs include:

- PDF
- EPUB

Additional formats may be introduced without changing the manuscript.

---

# Separation of Responsibilities

The publishing pipeline separates syntax, document structure, meaning, and presentation.

- **Manuscript** — human-readable content and supported metadata
- **Parser** — understands manuscript syntax
- **Document Model** — represents logical document structure
- **Interpretation** — determines document meaning and document-type conventions
- **Common Renderer** — provides reusable format-level rendering behaviour
- **Document-Type Renderer** — applies Book or Technical presentation conventions
- **Theme** — controls visual identity and presentation details
- **Output** — final published document

The current renderer architecture is deliberately layered:

```text
                    Interpretation
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

Common format behaviour should be implemented once. Document-type-specific publication conventions should remain in the appropriate Book or Technical renderer.

Each responsibility should remain independently understandable and replaceable where practical.

---

# Meaning Before Presentation

A renderer should not have to rediscover what a document means from raw Markdown.

The preferred flow is:

```text
Manuscript
   ↓
Parser
   ↓
Document Model
   ↓
Interpretation
   ↓
Common Format Rendering
   ↓
Document-Type Rendering
   ↓
Output
```

Parsing answers **what the manuscript syntax contains**.

Interpretation answers **what those constructs mean for the document**.

Rendering answers **how that meaning is presented in a particular publication format**.

---

# Backward Compatibility

Existing manuscripts should continue to render without modification.

Where new metadata is introduced, sensible defaults should preserve previous behaviour.

Internal implementation may evolve without requiring authors to rewrite compliant manuscripts.

---

# Readability First

Manuscripts are intended to be read and maintained by people.

Publishing features should never compromise the readability of the source document.

Complexity should remain inside the publishing engine rather than inside the manuscript.

---

# Incremental Evolution

VTR Press evolves through small, releasable improvements.

Architectural improvements should be delivered alongside new capabilities rather than through large rewrites.

Each release should leave the publishing platform cleaner, more maintainable, and more extensible than before.

Existing implementation structures should be migrated or removed only when there is a concrete benefit in doing so.

---

# Extensibility

VTR Press is designed to support multiple document types.

Currently:

- Book
- Technical Document

Future document types should be introduced by extending the publishing engine rather than changing the manuscript format.

Similarly, additional output formats should build on the existing document and interpretation architecture rather than introduce parallel manuscript pipelines.

---

# Minimalism

Every feature should solve a real publishing problem.

Complexity should remain inside the publishing engine, not inside the manuscript.

Architectural abstraction should be introduced when it reduces duplication, clarifies responsibility, or enables a real publishing capability—not simply for theoretical purity.
