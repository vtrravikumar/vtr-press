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

## P0 — Engineering Maintenance

## BL-013 — Migrate Deprecated PyMuPDF `fitz` API Usage

**Priority:** P0  
**Status:** Backlog — next change

Remove remaining use of the deprecated `fitz` API in the digitization/PyMuPDF integration and migrate to the supported `pymupdf` import/API surface.

### Requirement

The digitization command currently emits a deprecation warning indicating that the `fitz` API will be removed in a future release. The next engineering change touching the relevant PDF rendering code must address this rather than carrying the warning forward.

### Scope

- locate all `fitz` imports/usages in VTR Press;
- replace them with the supported `pymupdf` API;
- preserve existing PDF rendering behaviour;
- update tests and documentation where imports/examples are affected;
- verify the digitization CLI no longer emits the deprecation warning on supported environments;
- keep compatibility with the current PyMuPDF versions supported by the project.

### Constraint

This is a maintenance/API migration only. Do not change PDF rendering semantics or use it as an opportunity for unrelated refactoring.

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
**Status:** In progress — final scope for v2.2

Add a reusable upstream digitization pipeline that converts scanned or image-based source material into a reviewable Markdown manuscript suitable for the existing VTR Press publishing pipeline.

### Use case

Support faithful digitization of historical technical reports, books, manuals and other scanned documents where the source is a physical document or scanned PDF rather than an existing Markdown manuscript.

The pipeline is intentionally a **text-first reconstruction aid**. Its purpose is to save manual character transcription while leaving document reconstruction and editorial judgement to the author.

### Implemented so far

- PDF/page image extraction;
- pluggable OCR engines including Tesseract and macOS Vision;
- conservative image preprocessing;
- deterministic page-level processing with source/page provenance;
- reviewable Markdown assembly;
- page-level structure classification into prose, code and layout;
- code-aware OCR handling with explicit verification treatment;
- source-image preservation;
- OCR review markers and run statistics;
- persistent combined-source caching and sequential OCR processing;
- stage-aware rendering/OCR progress reporting;
- real scanned college-report validation;
- unit/regression and end-to-end CLI coverage.

### Final scope

- **Characters/prose OCR:** primary supported outcome.
- **Tables:** optional, only where reliable structured extraction can be demonstrated; otherwise preserve OCR text for manual reconstruction.
- **Spellcheck:** review-only assistance for OCR output. Spellcheck must never silently modify source text.
- **Images and diagrams:** out of scope for automatic reconstruction. Original scans remain authoritative and can be handled manually.
- **Code:** out of scope for automatic reconstruction. Code source scans will be handled as a separate manual reconstruction workflow.
- preserve source/page provenance;
- deterministic, repeatable processing;
- final production-readiness review.

### Spellcheck requirements

Spellcheck is a review aid, not an editorial correction engine.

It should:

- identify possible misspellings without changing OCR text;
- provide suggestions where available;
- support a configurable custom/technical vocabulary;
- avoid code blocks and Markdown syntax;
- avoid treating names, abbreviations, URLs and paths as ordinary prose words where practical;
- produce reviewable findings suitable for manual correction.

### Constraints

This is an **upstream digitization capability**, not a replacement for the publishing pipeline. Digitization should produce a Markdown manuscript; the existing parser → Document Model → interpretation → renderer pipeline remains responsible for publishing.

The system must not silently modernize, correct, rewrite or infer source content during faithful digitization. Automatic image/diagram reconstruction and automatic code reconstruction are deliberately excluded from this scope.

The implementation should remain incremental, deterministic and validated against representative scanned documents.

---

---
