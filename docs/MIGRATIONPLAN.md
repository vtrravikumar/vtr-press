# VTR Press Migration Plan

## Status

**COMPLETE — v2.0**

This document records the migration that established the generic document publishing architecture in VTR Press.

The migration is complete. Future work should be tracked as product or architectural evolution rather than as continuation of this migration.

---

# 1. Migration Objective

The objective was to evolve VTR Press from a primarily book-oriented publishing engine into a generic document publishing engine capable of supporting multiple document types and publication formats.

The target separation was:

```text
Manuscript
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
    ▼
Format-specific common rendering
    │
    ▼
Document-type rendering
    │
    ▼
Output
```

The migration was successful when document semantics no longer depended on a renderer-specific or output-specific implementation.

---

# 2. Migration Phases

| Phase | Status | Outcome |
|---|---|---|
| A — Unblock RideTogether | **Complete** | Established the foundation required for technical-document publishing. |
| B — Renderer gaps | **Complete** | Closed the renderer capabilities required by the target technical documents. |
| C — Automatic theme selection | **Complete** | Established document-type-driven publishing conventions. |
| D0 — Design validation | **Complete** | Validated the generic architecture against Book and Technical Document requirements. |
| D1 — Generic Document Model | **Complete** | Introduced the generic `Document` / block-stream model and interpretation layer. |
| D2 — Generic Markdown parser | **Complete** | Added generic Markdown parsing for the supported document structures. |
| D3 — Technical-document migration | **Complete** | Wired Technical Documents into the generic pipeline with Typst and EPUB output and asset handling. |
| D4 — Real-world validation | **Complete** | Validated the generic pipeline against representative technical manuscripts and generated PDF/EPUB output. |
| D5 — Architectural adoption | **Complete — v2.0** | Established the generic document architecture and shared rendering infrastructure as the production direction. |

---

# 3. D5 — Final Migration Decision

D5 was deliberately a decision point rather than an automatic requirement to rewrite every existing Book implementation.

After D1–D4 were implemented and validated against real documents, the evidence supported adopting the generic architecture as the production direction.

The migration therefore does **not** require immediate deletion of every historical Book dataclass.

Structures such as `Part`, `Chapter`, and `Scene` may remain where they continue to provide useful compatibility or interpretation behaviour.

Their continued existence does not change the architectural contract.

The important result is that:

- one manuscript remains the source of truth;
- document structure is represented independently of output format;
- document semantics are interpreted independently of presentation;
- Typst and EPUB have shared common rendering infrastructure;
- Book and Technical rendering remain document-type-specific where appropriate;
- the same publishing system produces multiple output formats;
- new document capabilities do not require duplicating structural logic across independent publishing pipelines.

---

# 4. Final Renderer Architecture

The migration resulted in a shared renderer architecture for each output format.

```text
Typst
├── Common
├── Book
└── Technical

EPUB
├── Common
├── Book
└── Technical
```

In the implementation this corresponds to the common renderer modules and their Book/Technical specializations.

The common layer owns reusable format-level rendering primitives.

The document-type renderers own publication conventions specific to Books or Technical Documents.

This is an important part of the v2.0 migration outcome and should not be interpreted as two independent publishing stacks.

---

# 5. Migration Outcome

V2.0 established the following production architecture:

```text
                  Manuscript
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
             ┌────────┴────────┐
             ▼                 ▼
       Common Typst       Common EPUB
             │                 │
       ┌─────┴─────┐     ┌─────┴─────┐
       ▼           ▼     ▼           ▼
     Book      Technical Book      Technical
     Typst       Typst    EPUB        EPUB
       │           │       │           │
       └─────┬─────┘       └─────┬─────┘
             ▼                   ▼
            PDF                 EPUB
```

The manuscript remains independent of the final publication format.

---

# 6. What the Migration Does Not Mean

Migration completion does not mean that every historical implementation detail must be removed.

It does not require:

- deleting every Book-specific class;
- rewriting proven Book behaviour solely for architectural purity;
- replacing working renderer code without a concrete benefit;
- introducing additional output formats immediately;
- completing future document capabilities as part of v2.0.

Remaining legacy structures are implementation details and may be retired incrementally when there is a demonstrated benefit.

---

# 7. Post-Migration Work

The following are intentionally post-migration improvements:

- retirement of remaining legacy Book structures where useful;
- richer Markdown block types;
- richer table capabilities;
- EPUB presentation refinements;
- additional themes;
- additional document types;
- additional output formats;
- stronger schema validation;
- renderer or theme registries where justified.

These should be managed through the current engineering plan and roadmap, not added to this completed migration.

---

# 8. Historical Record

The migration phases were executed incrementally and validated against real publishing requirements.

D5 was originally left as an explicit decision because the generic architecture did not require an immediate rewrite of the established Book path.

The final v2.0 decision was to adopt the unified architecture while retaining useful Book-specific implementation structures where appropriate.

That decision marks the completion of this migration.

---

## Revision History

| Date | Change |
|---|---|
| Initial draft | Defined Phases A–D following the parser architecture and generic-model migration reviews. |
| 2026-08-28 | Updated for v2.0. D0–D4 confirmed complete and D5 marked complete following adoption of the unified generic document publishing architecture. |
| 2026-08-30 | Consolidated the document around the completed migration outcome and clarified the shared Common Typst/EPUB renderer architecture. |
