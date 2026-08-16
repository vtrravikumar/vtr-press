# VTR Press Specification

## Purpose

This document defines the manuscript specification supported by VTR Press.

The specification describes the information an author may provide and the publishing conventions that VTR Press applies during rendering.

Implementation details such as parsers, document models, renderers, themes, and output formats are intentionally excluded.

The manuscript specification is the stable public contract between authors and VTR Press.

---

# Supported Document Types

VTR Press supports multiple document types.

Currently supported:

- book
- technical-document

If the document type is omitted, VTR Press assumes:

```yaml
type: book
```

Additional document types may be introduced without changing the manuscript format.

---

# Metadata

A manuscript begins with an optional YAML metadata block.

Example:

```yaml
---
title: Building RideTogether
subtitle: Solution Architecture

author: VTR Ravi Kumar

type: technical-document

project: RideTogether
category: Solution Architecture
identifier: RT-SAD-001

version: 1.0
status: Draft
date: 2026-08-06

keywords:
  - architecture
  - ride together
---
```

Metadata describes the document.

It does not describe how the document should be rendered.

Publishing decisions remain the responsibility of VTR Press.

---

# Document Structure

A manuscript consists of Markdown content following the metadata block.

Typical elements include:

- headings
- paragraphs
- lists
- images
- tables
- code blocks
- hyperlinks
- appendices

The same manuscript may be rendered into multiple publication formats.

---

# Publishing Conventions

Publishing conventions are determined automatically from the document type.

Examples include:

| Document Type | Default Behaviour |
|--------------|-------------------|
| book | A5 layout, cover page, chapter-oriented structure |
| technical-document | A4 layout, numbered sections, appendix support |

Authors should not configure layout, typography, or page settings unless explicitly supported by the specification.

## Print Book PDF

When a book is rendered as a print PDF interior, VTR Press applies print-book pagination conventions automatically:

- Front matter, including Prologue, displays no page numbers.
- Front matter, including Prologue, is omitted from the Contents page.
- Main-matter numbering begins at Part I, where Part I displays page 1.
- Every Part opens on a right-hand page.
- The first Chapter after every Part opens on a right-hand page.
- Blank pages inserted for right-hand alignment are genuinely blank and display no page numbers.

These requirements apply only to print PDF book output. EPUB output and non-book document types are unaffected.

---

# Compatibility

The manuscript format is considered the stable public interface of VTR Press.

Internal implementation may evolve without affecting compliant manuscripts.

Existing manuscripts should continue to render without modification wherever possible.

When new metadata fields are introduced, sensible defaults should preserve existing behaviour.

---

# Future Evolution

Future document types may include:

- white-paper
- user-guide
- design-specification
- api-reference
- research-paper

These document types will reuse the same manuscript format while applying different publishing conventions.

The introduction of new document types should not require changes to existing manuscripts.
