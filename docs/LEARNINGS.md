# Learnings from VTR Press

## Purpose

This document captures the engineering lessons learned while designing, implementing, and publishing real documents using VTR Press.

These lessons form the foundation for future architectural decisions and guide the continued evolution of the publishing platform.

Every significant architectural decision should be traceable to one or more of these lessons.

---

# Lesson 001 — Build from Experience, Not Assumptions

VTR Press has demonstrated that a lightweight Markdown-based publishing workflow can produce high-quality publications.

Future architectural improvements should build upon that experience rather than attempting to redesign publishing from theory.

Every major architectural decision should be supported by real experience gained while building or using VTR Press.

---

# Lesson 002 — Documents Are More Than Books

VTR Press began as a book publishing toolkit.

During the development of the RideTogether Solution Architecture Document it became clear that the same publishing engine should also support technical documents and other structured publications.

Books are one class of publication.

They should not define the architecture of the publishing engine.

---

# Lesson 003 — The Manuscript Is the Source of Truth

The manuscript describes the document.

It should remain simple, human-readable, and focused on content.

Rendering decisions should never leak into the manuscript unless explicitly overridden.

---

# Lesson 004 — Metadata Describes Intent

Metadata should describe what the document is.

It should not describe how the document is rendered.

Examples include:

- document type
- title
- author
- version
- publication status

Page size, typography, themes, and layout belong to the publishing engine.

---

# Lesson 005 — Convention Over Configuration

Authors should not be expected to understand the rendering engine.

Reasonable publishing conventions should be applied automatically.

Configuration should exist only when there is a genuine need to override defaults.

---

# Lesson 006 — Opinionated, Not Fragile

The publishing engine should encourage consistent authoring conventions.

However, authors should not be required to memorise parser-specific rules.

Well-structured manuscripts should be interpreted intelligently wherever possible.

Errors should indicate genuinely ambiguous or invalid documents rather than rigid implementation assumptions.

---

# Lesson 007 — Separate Syntax from Semantics

Markdown provides document structure.

Publishing semantics are a separate concern.

The parser should understand the manuscript.

The publishing engine should interpret the document.

The renderer should determine presentation.

---

# Lesson 008 — One Document Model

Every supported publication should ultimately share a common document model.

Books, technical documents, and future publication types differ primarily in interpretation and presentation rather than fundamental structure.

---

# Lesson 009 — Themes Control Presentation

Themes define how documents look.

They should not determine document structure.

Changing a theme should never require changes to the manuscript.

---

# Lesson 010 — Renderers Own Publishing Workflows

Different publication types have different publishing conventions.

Examples include:

- cover pages
- title pages
- page numbering
- front matter
- appendices
- revision history

These behaviours belong to the publishing workflow rather than the manuscript.

---

# Lesson 011 — One Source, Multiple Outputs

Every publication should be written once.

All output formats should be generated from the same document model.

PDF, EPUB, and future formats should represent different renderers rather than different authoring workflows.

---

# Lesson 012 — Architecture Before Implementation

Significant architectural changes should be understood before implementation begins.

Engineering principles, document models, publishing pipelines, and component responsibilities should be agreed before major architectural work is undertaken.

The objective is to minimise architectural drift while allowing the implementation to evolve incrementally.

---

# Closing Thoughts

VTR Press has proven that a focused publishing toolkit can successfully produce professional-quality publications.

As the platform evolves, these lessons ensure that architectural improvements remain grounded in practical experience rather than theoretical design.

The objective is not to pursue architectural perfection through large rewrites.

The objective is to continuously evolve VTR Press into a publishing platform capable of supporting multiple classes of publications while preserving a simple and enjoyable authoring experience.

Every future architectural decision should be guided by these lessons.