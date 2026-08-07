# Learnings from VTR Press v1

## Purpose

VTR Press v2 is not a rewrite of VTR Press v1.

It is the result of the engineering experience gained while designing, implementing and publishing real books using VTR Press v1.

This document captures the important lessons learned during that journey. These lessons form the foundation of every architectural decision in VTR Press v2.

---

# Lesson 001 — Build from Experience, Not Assumptions

VTR Press v1 successfully proved that a lightweight Markdown-based publishing workflow can produce high-quality books.

VTR Press v2 should build upon that experience rather than attempting to redesign publishing from theory.

Every major architectural decision should be traceable to a real lesson learned while building or using VTR Press v1.

---

# Lesson 002 — Documents Are More Than Books

VTR Press began as a book publishing toolkit.

During the development of the RideTogether Solution Architecture Document it became clear that the same publishing engine should also support technical documents and other structured publications.

Books are one class of publication.

They should not define the architecture of the publishing engine.

---

# Lesson 003 — The Manuscript Is the Source of Truth

The manuscript describes the document.

It should remain simple, human-readable and focused on content.

Rendering decisions should never leak into the manuscript unless explicitly overridden.

---

# Lesson 004 — Metadata Describes Intent

Metadata should describe what the document is.

It should not describe how the document is rendered.

Examples include:

* document type
* title
* author
* version
* publication status

Page size, typography, themes and layout belong to the publishing engine.

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

Books, technical documents and future publication types differ primarily in interpretation and presentation rather than fundamental structure.

---

# Lesson 009 — Themes Control Presentation

Themes define how documents look.

They should not determine document structure.

Changing a theme should never require changes to the manuscript.

---

# Lesson 010 — Renderers Own Publishing Workflows

Different publication types have different publishing conventions.

Examples include:

* cover pages
* title pages
* page numbering
* front matter
* appendices
* revision history

These behaviours belong to the publishing workflow rather than the manuscript.

---

# Lesson 011 — One Source, Multiple Outputs

Every publication should be written once.

All output formats should be generated from the same document model.

PDF, EPUB and future formats should represent different renderers rather than different authoring workflows.

---

# Lesson 012 — Architecture Before Implementation

The architecture of VTR Press v2 should be defined before implementation begins.

Engineering principles, document model, publishing pipeline and component responsibilities should be agreed before writing production code.

The objective is to minimise architectural drift and allow implementation to follow a clear design.

---

# Closing Thoughts

VTR Press v1 demonstrated that a focused publishing toolkit could successfully produce professional-quality books.

VTR Press v2 builds upon those achievements with a broader vision.

The objective is not to replace VTR Press v1.

The objective is to create a publishing engine capable of supporting multiple document classes while preserving a simple and enjoyable authoring experience.

Every decision in VTR Press v2 should be guided by these lessons.
