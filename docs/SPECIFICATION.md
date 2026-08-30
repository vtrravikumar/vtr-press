# VTR Press Specification

## Purpose

This document defines the manuscript specification supported by VTR Press.

The specification describes the information an author may provide and the publishing conventions that VTR Press applies during rendering.

Implementation details such as parsers, document models, renderers, themes, and output formats are intentionally excluded except where they affect the author-facing manuscript contract.

The manuscript specification is the stable public contract between authors and VTR Press.

---

# Supported Document Types

VTR Press supports multiple document types.

Currently supported:

- `book`
- `technical-document`

If the document type is omitted, VTR Press assumes:

```yaml
type: book
```

An unrecognized document type is rejected.

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

Supported document elements include:

- headings and subheadings
- paragraphs
- ordered and unordered lists
- images
- tables
- code blocks
- hyperlinks
- verse blocks
- appendices and other document-type-specific structures where supported

The same manuscript may be rendered into multiple publication formats.

---

# Tables

Markdown tables are part of the manuscript structure supported by VTR Press.

Table content is represented in the document model and rendered by the applicable publication renderers.

Authors should use standard Markdown table syntax. Presentation details such as column widths, typography, borders, and page layout remain publishing concerns rather than manuscript concerns.

---

# Publishing Conventions

Publishing conventions are determined automatically from the document type.

Examples include:

| Document Type | Default Behaviour |
|--------------|-------------------|
| book | A5 layout, cover page, chapter-oriented structure |
| technical-document | A4 layout, numbered sections, technical-document structure |

Authors should not configure layout, typography, or page settings unless explicitly supported by the specification.

---

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

# Technical Documents

Technical documents use the generic manuscript and document architecture while applying technical-document conventions.

A typical technical document may contain:

- hierarchical headings;
- subheadings;
- numbered sections;
- paragraphs;
- lists;
- code blocks;
- JSON or other code content;
- images;
- Markdown tables;
- appendices.

The technical-document type is intended for structured publications such as solution architecture documents, design specifications, technical guides, and similar material.

---

# Assets

Images and other supported manuscript assets are referenced from the manuscript rather than embedded with renderer-specific instructions.

VTR Press resolves and stages assets as part of publication generation.

Authors should reference assets using the supported Markdown syntax and should not rely on renderer-specific filesystem paths in the manuscript.

---

# Compatibility

The manuscript format is considered the stable public interface of VTR Press.

Internal implementation may evolve without affecting compliant manuscripts.

Existing manuscripts should continue to render without modification wherever possible.

When new metadata fields are introduced, sensible defaults should preserve existing behaviour.

---

# Future Evolution

Future document types may include:

- `white-paper`
- `user-guide`
- `design-specification`
- `api-reference`
- `research-paper`

These document types will reuse the same manuscript format while applying different publishing conventions.

The introduction of new document types should not require changes to existing manuscripts.
