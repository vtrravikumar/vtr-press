# VTR Press Publishing Principles

## Purpose

VTR Press is a publishing platform that transforms a simple, human-readable manuscript into professionally published documents.

The author's responsibility is to describe the content.

The publisher's responsibility is to determine its presentation.

---

## Convention over Configuration

Authors should not be required to understand page layouts, typography, or rendering engines.

Document conventions are selected automatically based on the document type.

Example:

```yaml
type: technical-document
```

should automatically apply the appropriate publishing conventions.

---

## Single Source of Truth

A manuscript should be written once and published in multiple formats without modification.

Supported outputs include:

- PDF
- EPUB

Additional formats may be introduced without changing the manuscript.

---

## Separation of Responsibilities

The publishing pipeline consists of independent responsibilities.

- Manuscript — content
- Parser — interpretation
- Renderer — presentation
- Theme — visual identity
- Output — published document

Each component should remain independently replaceable.

---

## Backward Compatibility

Existing manuscripts should continue to render without modification.

Where new metadata is introduced, sensible defaults should preserve previous behaviour.

---

## Readability First

Manuscripts are intended to be read and maintained by people.

Publishing features should never compromise the readability of the source document.

---

## Extensibility

VTR Press is designed to support multiple document types.

Initially:

- Book
- Technical Document

Future document types should be introduced by extending the publishing engine rather than changing the manuscript format.

---

## Minimalism

Every feature should solve a real publishing problem.

Complexity should remain inside the publishing engine, not inside the manuscript.