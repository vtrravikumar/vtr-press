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

The current implementation still requires the manifest to identify each manuscript and its output name. fileciteturn72file0L2-L2

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

The current model already has generic headings, images, tables and links, making this a natural post-v2 document capability. fileciteturn76file0L2-L2

---

## BL-004 — Image Captions

**Priority:** P0  
**Status:** Backlog

Add captions to block images and define consistent rendering across PDF and EPUB.

The current generic `Image` model contains only `source` and `alt_text`; there is no caption field. fileciteturn76file0L2-L2

The feature should be implemented at the document-model level so both output formats consume the same semantic information.

---

## BL-005 — Language-Aware Syntax Highlighting

**Priority:** P0  
**Status:** Partially implemented

Basic fenced code blocks are already represented by `CodeBlock` with an optional language and are rendered by both common Typst and EPUB infrastructure. fileciteturn74file0L2-L2 fileciteturn75file0L2-L2

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

The generic Document Model already supports tables with headers, rows and column alignment, and the Technical Typst/EPUB renderers consume them. fileciteturn76file0L2-L2 fileciteturn85file0L2-L2

Remaining work should therefore focus on genuine publishing gaps rather than basic table support.

Potential scope:

- richer cell content;
- multiline cells;
- spanning cells where practical;
- improved print pagination;
- EPUB presentation refinements;
- regression coverage for real-world tables.

---

# P2 — Output and Presentation

## BL-011 — HTML Output

**Priority:** P2  
**Status:** Future

Add HTML output using the same interpreted document information used by the existing renderers.

Potential use cases:

- standalone technical documentation;
- web publishing;
- local previews.

HTML should be a new output format, not a second document-processing pipeline.

---

## BL-012 — Kindle Publishing Output

**Priority:** P2  
**Status:** Future

Investigate Kindle publishing support.

Determine whether the appropriate product is:

- Kindle-ready EPUB;
- KPF generation;
- or a documented external conversion workflow.

The decision should be based on actual distribution requirements rather than assuming direct KPF generation is necessary.

---

## BL-013 — DOCX Output

**Priority:** P2  
**Status:** Future

Investigate DOCX as an additional output format.

The investigation should establish the required Document Model capabilities and whether DOCX quality is sufficient to justify official support.

---

## BL-014 — Theme and Custom Theme Workflow

**Priority:** P2  
**Status:** Future

The current architecture already separates common rendering from Book and Technical rendering, with theme-specific presentation in the renderer/theme layer. fileciteturn74file0L2-L2 fileciteturn85file0L2-L2

Future work should therefore focus on:

- documenting the theme contract;
- simplifying creation of custom themes;
- theme validation/testing;
- adding additional built-in themes where real use cases justify them.

Do not introduce another theme framework without a concrete need.

---

## BL-015 — Performance Measurement and Optimization

**Priority:** P2  
**Status:** Backlog

Measure before optimizing.

Potential scope:

- parser profiling;
- rendering profiling;
- repeated document traversal;
- unnecessary allocations;
- PDF/EPUB generation time;
- regression benchmarks for representative manuscripts.

No performance rewrite should be undertaken without evidence of a meaningful bottleneck.

---

# P3 — Productization and Exploration

## BL-016 — Release Readiness / 1.0 Criteria

**Priority:** P3  
**Status:** Future

Define release-readiness criteria for a stable public VTR Press release.

The criteria should reflect the current v2 product rather than the obsolete V1 migration terminology.

Potential areas:

- manuscript contract;
- supported document types;
- supported output formats;
- renderer/theme stability;
- error handling;
- test coverage;
- documentation;
- installation and distribution.

---

## BL-017 — PyPI Distribution

**Priority:** P3  
**Status:** Future

Package VTR Press for installation through PyPI once the CLI, package structure and resource handling are stable.

---

## BL-018 — Documentation Website

**Priority:** P3  
**Status:** Future

Publish the VTR Press documentation as a web-based documentation site when the supported manuscript and CLI contracts are mature enough to document publicly.

---

## BL-019 — Homebrew Installation

**Priority:** P3  
**Status:** Future

Investigate Homebrew distribution after the CLI and package structure have stabilized.

---

## BL-020 — Additional Document Types

**Priority:** P3  
**Status:** Exploratory

Evaluate additional document types only when a real publishing use case exists.

New document types should fit the established pattern of document-type interpretation and Book/Technical-style rendering specialization without creating another publishing stack.

---

## BL-021 — Plugin Architecture

**Priority:** P3  
**Status:** Deferred

Revisit third-party extension mechanisms only after the core architecture has demonstrated sufficient stability and there is a concrete need for external extensions.

Possible future extension points include:

- renderers;
- themes;
- document conventions;
- output formats.

The existing Interpretation layer is **not** a plugin architecture.

---

# Explicitly Removed / Already Implemented

These are intentionally not backlog items anymore.

| Historical item | Decision | Reason |
|---|---|---|
| GitHub Actions automated tests | **Removed** | CI workflow already exists. |
| Generic Document Model migration | **Removed** | v2 architecture is established. |
| D1/D2/D3/D4 migration work | **Removed** | Migration is complete and recorded in `docs/MIGRATIONPLAN.md`. |
| V2-001 / V2-002 / V2-003 labels | **Replaced** | Their surviving ideas are consolidated into BL-001. |
| Basic fenced code blocks | **Removed** | Already implemented in the generic technical-document pipeline. |
| Basic generic tables | **Removed** | Already implemented; remaining work is richer table capability. |
| Basic technical-document Typst/EPUB publishing | **Removed** | Already part of the current architecture. |
| LineBreak as a standalone backlog item | **Removed** | The generic model and EPUB renderer already contain `LineBreak`; remaining gaps should be tracked only if a concrete defect is found. fileciteturn75file0L2-L2 |
| V1 migration wording | **Removed** | Superseded by the completed v2 architecture. |

---

# Backlog Rules

1. **Do not add migration work here.** The v2 migration is complete.
2. **Verify implementation before creating an item.** Do not backlog functionality that already exists.
3. **Prefer one clear item over several historical fragments.** Related discovery/input work is consolidated under BL-001.
4. **Document-model capabilities belong in the generic model.** Do not add renderer-specific implementations when the feature is semantic.
5. **Common format behaviour belongs in Common Typst / Common EPUB.** Book and Technical renderers should contain document-type-specific publication behaviour.
6. **Promote only when ready.** A backlog item becomes active engineering work only after its scope and acceptance criteria are defined.
7. **Delete obsolete ideas.** The backlog is not an archive of every feature ever discussed.

---

# Current Recommendation

The backlog should now be **held** rather than immediately implemented.

When engineering resumes, the first candidates to evaluate are:

1. **BL-001 — Simplify Manuscript Discovery and Publishing Input**
2. **BL-003 — Cross References**
3. **BL-004 — Image Captions**
4. **BL-005 — Language-Aware Syntax Highlighting**
5. **BL-002 — Markdown Compatibility Improvements**

These are the items most directly aligned with the capabilities and gaps exposed by the current v2 architecture.
