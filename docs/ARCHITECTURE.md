# VTR Press Architecture

## Overview

VTR Press is a publishing platform that transforms a single manuscript into one or more published document formats.

The architecture separates content, presentation, and output so that manuscripts remain stable while publishing capabilities continue to evolve.

## Architecture Status

This document describes the target architecture toward which VTR Press is evolving.

The current implementation may differ in some areas.

VTR Press evolves incrementally through small, releasable improvements rather than large architectural rewrites.

---

```
Markdown Manuscript
        │
        ▼
      Parser
        │
        ▼
 Document Model
        │
 ┌──────┴─────────┐
 ▼                ▼
Typst          EPUB
Renderer       Renderer
 ▼                ▼
PDF          XHTML Documents
                 │
                 ▼
            EPUB Writer
                 │
                 ▼
               EPUB
```

---

# Components

## Manuscript

The manuscript is the single source of truth.

It contains the document content together with minimal metadata describing the document.

The manuscript should remain human-readable and independent of any rendering technology.

---

## Parser

The parser reads the manuscript and extracts:

- metadata
- document structure
- content elements

The parser produces a document model that is independent of any output format.

---

## Document Model

The document model represents the logical structure of the manuscript.

Typical elements include:

- metadata
- sections
- paragraphs
- images
- tables
- code blocks
- appendices
- references

All renderers consume the same document model.

The internal implementation of the document model may evolve over time without affecting the manuscript specification.

---

## Renderer

A renderer transforms the document model into a publishable format.

Renderers determine *how* the document is produced but never modify the manuscript itself.

Current renderers include:

- PDF
- EPUB

Additional renderers may be introduced without changing the manuscript format.

---

## Theme

Themes define the visual presentation of a document.

Typical responsibilities include:

- page layout
- typography
- heading styles
- spacing
- numbering
- document conventions

Themes are selected automatically based on the document type.

---

## Output

The final published artifact.

Examples include:

- PDF
- EPUB

Future output formats may be supported as the publishing platform evolves.

---

# Design Principles

The architecture is guided by five principles:

- Single source of truth
- Convention over configuration
- Separation of responsibilities
- Backward compatibility
- Incremental evolution

These principles ensure that manuscripts remain stable while the publishing engine continues to evolve.

---

# Non-Goals

The architecture does not attempt to:

- expose renderer-specific features within manuscripts
- require authors to understand publishing internals
- optimise for every possible document type from day one
- replace working components without demonstrated value
- perform large-scale architectural rewrites

Architectural improvements should always preserve a working, releasable publishing platform.