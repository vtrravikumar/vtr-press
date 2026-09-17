# VTR Press Backlog

This is the **post-v2 engineering backlog** for VTR Press.

The v2 architectural migration is complete. Architectural history and migration decisions are documented separately in `docs/MIGRATIONPLAN.md`, `docs/ARCHITECTURE.md`, and `docs/ENGINEERING_PLAN.md`.

This backlog contains only work that remains meaningful against the current implementation. Completed migration work, obsolete proposals, and historical handover items are intentionally excluded.

## Priority

- **P0 — Next:** strong candidates for the next engineering cycle
- **P1 — Important:** valuable capabilities after P0
- **P2 — Later:** worthwhile, but not currently blocking the product
- **P3 — Future:** productization or exploratory work

---

# P0 — Next Engineering Candidates

## BL-001 — Simplify Manuscript Discovery and Publishing Input

**Priority:** P0  
**Status:** Ready for design

### Problem

The current CLI is driven by an explicit `books.yaml` entry and a named publishing target. The same mechanism is used for Books and Technical Documents even though Technical Documents already carry their document type and metadata in manuscript front matter.

The current implementation still requires the manifest to identify each manuscript and its output name.

### Desired outcome

Support a simpler publishing input model without changing the core publishing pipeline.

Potential modes:

- publish one manuscript directly;
- publish a directory of manuscripts;
- retain `books.yaml` for explicit/legacy workflows;
- derive appropriate metadata from manuscript front matter where possible.

### Constraints

This is an input/discovery improvement, **not another publishing architecture**. The existing parser → Document Model → interpretation → renderer pipeline remains the foundation. The current manifest must remain supported until a replacement is proven.

---

## BL-002 — Markdown Compatibility Improvements

**Priority:** P0  
**Status:** Backlog

Improve the supported Markdown manuscript contract based on real manuscript usage and CommonMark-compatible behaviour.

Potential scope:

- escaped Markdown characters;
- nested emphasis;
- additional CommonMark constructs;
- parser edge cases discovered through real manuscripts.

New syntax should enter the generic Document Model rather than being implemented independently by individual renderers.

---

## BL-003 — Cross References

**Priority:** P0  
**Status:** Backlog

Add first-class references between document structures such as sections, figures and tables.

Potential requirements:

- stable identifiers;
- reference syntax in the manuscript;
- internal links;
- output-specific reference rendering;
- consistent behaviour in PDF and EPUB.

The current model already has generic headings, images, tables and links, making this a natural post-v2 document capability.

---

## BL-004 — Image Captions

**Priority:** P0  
**Status:** Backlog

Add captions to block images and define consistent rendering across PDF and EPUB.

The current generic `Image` model contains only `source` and `alt_text`; there is no caption field.

The feature should be implemented at the document-model level so both output formats consume the same semantic information.

---

## BL-005 — Language-Aware Syntax Highlighting

**Priority:** P0  
**Status:** Partially implemented

Basic fenced code blocks are already represented by `CodeBlock` with an optional language and are rendered by both common Typst and EPUB infrastructure.

Remaining scope:

- language-aware syntax highlighting;
- supported-language policy;
- consistent PDF/EPUB presentation;
- graceful fallback for unknown languages.

Do not duplicate the basic fenced-code implementation.

---

# P1 — Document and Publishing Capabilities

## BL-006 — Footnotes

**Priority:** P1  
**Status:** Backlog

Support footnotes as a first-class manuscript/document feature with output-specific rendering for PDF and EPUB.

---

## BL-007 — Bibliography and Citations

**Priority:** P1  
**Status:** Backlog

Support references and bibliography for technical and book documents.

Potential scope:

- reference metadata;
- citation syntax;
- bibliography sections;
- output-specific formatting.

The design should avoid coupling the manuscript to one bibliography engine prematurely.

---

## BL-008 — Glossary

**Priority:** P1  
**Status:** Backlog

Support glossary entries and, where justified, generated glossary output.

The feature should be useful for technical documents without forcing Books to adopt technical-document conventions.

---

## BL-009 — Index Generation

**Priority:** P1  
**Status:** Backlog

Investigate automatic index generation, initially for book-length documents.

The implementation should be based on stable semantic anchors rather than renderer-specific text scanning.

---

## BL-010 — Richer Table Support

**Priority:** P1  
**Status:** Backlog

The generic Document Model already supports tables with headers, rows and column alignment, and the Technical Typst/EPUB renderers consume them.

Remaining work should therefore focus on genuine publishing gaps rather than basic table support.

Potential scope:

- richer cell content;
- multiline cells;
- spanning cells where practical;
- improved print pagination;
- EPUB presentation refinements;
- regression coverage for real-world tables.

---

## BL-011 — Multiple Authors / Author Metadata

**Priority:** P1  
**Status:** Backlog — v2.1

Extend the manuscript and publishing metadata model to support more than one author, preserving author information consistently across document parsing, the generic Document Model, and all supported output formats.

### Use case

Support books and technical documents created by multiple authors, including historical project reports and other collaborative manuscripts.

### Potential scope

- accept an ordered list of authors in manuscript/front-matter metadata;
- preserve author order and names through the generic Document Model;
- render multiple authors correctly in title pages and other Book/Technical publication metadata;
- ensure PDF and EPUB output remain consistent;
- define compatibility behaviour for existing single-author manuscripts;
- add parser, model, and renderer regression tests.

### Constraints

This is a metadata capability, **not a new publishing architecture**. The solution should extend the existing document model and interpretation pipeline rather than introduce document-type-specific author handling. Existing single-author manuscripts must continue to work unchanged.

---

## BL-012 — Document Digitization / OCR Pipeline

**Priority:** P1  
**Status:** In progress — candidate for v2.2

Add a reusable upstream digitization pipeline that converts scanned or image-based source material into a reviewable Markdown manuscript suitable for the existing VTR Press publishing pipeline.

### Use case

Support faithful digitization of historical technical reports, books, manuals and other scanned documents where the source is a physical document or scanned PDF rather than an existing Markdown manuscript.

The pipeline should be reusable across projects. Project repositories should retain the original source scans and the generated/reviewed Markdown, while reusable OCR and digitization machinery belongs in VTR Press.

### Implemented so far

- PDF/page image extraction through a `pdftoppm` adapter;
- Tesseract OCR adapter with named `prose`, `layout` and `code` profiles;
- conservative Pillow preprocessing with unchanged passthrough and optional grayscale, autocontrast and thresholding;
- deterministic page-level pipeline with source/page provenance;
- reviewable Markdown assembly;
- conservative page-level structure classification into `prose`, `code` and `layout` with bounded confidence and reasons;
- real scanned college-report validation and controlled preprocessing comparison.

### Remaining scope

- code-safe handling and explicit review treatment for OCR'd source listings;
- table and figure preservation/extraction support;
- confidence and review markers beyond the current structure marker;
- representative regression fixtures from real scanned pages;
- final CLI/API workflow and broader end-to-end validation.

### Potential scope

- PDF/page image extraction;
- image preprocessing for OCR quality;
- Tesseract or another pluggable OCR engine;
- OCR-to-Markdown generation;
- page and section boundary preservation;
- detection/handling of figures and diagrams;
- table extraction or structured table review support;
- source-code-aware OCR handling for technical documents;
- preservation of technical punctuation and symbols;
- OCR confidence/review markers where practical;
- deterministic, repeatable processing;
- validation and regression tests using representative scanned documents.

### Constraints

This is an **upstream digitization capability**, not a replacement for the publishing pipeline. Digitization should produce a Markdown manuscript; the existing parser → Document Model → interpretation → renderer pipeline remains responsible for publishing.

The system must distinguish ordinary prose from code, tables and other structures where OCR errors can materially change meaning. It must not silently modernize, correct or rewrite source content during faithful digitization.

The first implementation should be deliberately incremental and validated against real scanned documents before the CLI/API and broader feature set are finalized.

---
