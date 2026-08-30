# VTR Press Engineering Plan

## Status

**Current engineering plan — post-v2.0**

VTR Press v2.0 established the generic document architecture and shared rendering infrastructure. This document describes engineering work from that baseline onward.

The detailed Phase A–D migration plan and execution history are preserved in the repository history and should not be treated as the current work plan.

---

# 1. Engineering Principles

VTR Press should evolve through small, testable, releasable changes.

Every change should aim to:

- preserve the manuscript as the stable author-facing contract;
- keep parsing separate from document semantics;
- keep document semantics separate from presentation;
- reuse common rendering behaviour within an output format;
- preserve existing Book publishing behaviour unless intentionally changed;
- add regression coverage before declaring work complete;
- avoid architectural rewrites without a concrete user or engineering benefit.

---

# 2. Current Architecture Baseline

The current publishing architecture is:

```text
Markdown Manuscript
        │
        ▼
      Reader
        │
        ▼
     Parser
        │
        ▼
 Generic Document Model
        │
        ▼
  Interpretation
        │
   ┌────┴────┐
   ▼         ▼
Common    Common
Typst     EPUB
   │         │
 ┌─┴─┐     ┌─┴─┐
 ▼   ▼     ▼   ▼
Book Technical Book Technical
Typst Typst    EPUB EPUB
```

Common format-level rendering belongs in `typst_common.py` and `epub_common.py`.

Document-type-specific presentation belongs in the corresponding Book and Technical renderers.

The existing book-specific model structures may remain where they provide value. Their removal is not an engineering objective by itself.

---

# 3. Near-Term Engineering Priorities

## 3.1 Publishing Quality

Improve the quality and consistency of generated publications.

Focus on:

- PDF typography and layout;
- EPUB reading experience;
- metadata correctness;
- image and asset behaviour;
- cross-format consistency;
- edge cases in real manuscripts.

Changes should be validated against representative manuscripts as well as unit tests.

---

## 3.2 Document Model Capabilities

Extend the generic document model when a new feature represents a genuine document-level concept.

Potential areas include:

- richer tables;
- links and cross-references;
- footnotes and endnotes;
- references and citations;
- callouts/admonitions;
- additional structured blocks.

The preferred implementation sequence is:

```text
Manuscript syntax
       ↓
Parser
       ↓
Document Model
       ↓
Interpretation
       ↓
Common renderer support
       ↓
Document-type renderer support
```

A capability should not be implemented independently in each renderer when it is fundamentally a document-level concept.

---

## 3.3 Renderer Refinement

Continue improving the renderer layers without weakening their boundaries.

### Typst

```text
Typst Common
     ├── Book Typst
     └── Technical Typst
```

### EPUB

```text
EPUB Common
     ├── Book EPUB
     └── Technical EPUB
```

Shared behaviour should remain in the common layer. Book and Technical conventions should remain in their respective renderers.

---

## 3.4 Book Compatibility

Book publishing is an established VTR Press capability and must remain protected during architectural evolution.

When modifying common rendering or document infrastructure:

- run Book regression tests;
- validate representative book output;
- avoid unnecessary changes to existing book presentation;
- migrate legacy book structures only when there is a measurable benefit.

---

## 3.5 Technical Documents

Continue developing Technical Document support on the generic document architecture.

Priority areas should be driven by actual publishing requirements rather than by architectural completeness for its own sake.

Possible areas include:

- richer technical tables;
- cross-references;
- technical callouts;
- citations/references;
- improved navigation;
- additional document conventions.

---

# 4. Testing Strategy

Every substantive change should be validated at the appropriate levels.

### Unit tests

Validate individual parser, document-model, interpretation, asset, and renderer behaviours.

### Integration tests

Validate complete publishing paths from manuscript to PDF and EPUB.

### Reference manuscripts

Use representative real manuscripts to detect regressions that synthetic tests may miss.

At minimum, validation should cover:

- a Book manuscript;
- a Technical Document manuscript;
- headings and hierarchy;
- lists;
- code blocks;
- tables;
- images/assets;
- PDF output;
- EPUB output.

---

# 5. Architectural Decision Rules

Before introducing a new feature, ask:

### Is it syntax?

Implement it in the parser.

### Is it document structure?

Represent it in the generic document model where appropriate.

### Is it document meaning or convention?

Implement it in interpretation/document-type logic.

### Is it shared Typst or EPUB behaviour?

Implement it in the corresponding common renderer.

### Is it specific to books or technical documents?

Implement it in that document-type renderer.

### Is it visual presentation?

Implement it through the appropriate renderer/theme mechanisms.

This keeps the architecture understandable as the feature set grows.

---

# 6. Deferred / Conditional Work

The following are not automatic migration requirements:

- removing legacy `Part`, `Chapter`, or `Scene` classes;
- rewriting the established book pipeline solely for architectural purity;
- introducing additional output formats before there is a concrete need;
- building the Architecture Review Pack before its requirements are defined;
- broad refactoring without corresponding user value or reduction in meaningful technical debt.

These may become worthwhile later, but should be justified independently.

---

# 7. Future Engineering Direction

Potential future work includes:

- additional document types;
- HTML output;
- DOCX output;
- richer technical publishing conventions;
- automated document analysis and derived publication artifacts;
- further consolidation of shared publishing infrastructure.

Future work should extend the existing architecture rather than introduce parallel publishing systems.

---

# 8. Definition of Done

Engineering work is complete when:

- the implementation matches the intended architectural boundary;
- existing supported publishing paths remain functional;
- relevant regression tests pass;
- representative manuscripts have been validated where appropriate;
- documentation reflects the resulting behaviour;
- no obsolete architectural claim is left behind.

The goal is not architectural perfection. The goal is a publishing platform that remains reliable, understandable, and extensible as it evolves.
