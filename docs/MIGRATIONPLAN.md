## Phase D — Generic document model migration

**Goal**: new document types stop requiring parser changes. Structure
comes from a shared model; interpretation (per type) and
presentation (per theme) differ.

**Status**: Complete through D5 — v2.0

Phase D established the generic document architecture and brought it
into production use.

The original D5 was deliberately optional: after D1–D4 had proven the
generic model against real content, decide whether the book publishing
path should also participate in the generic architecture.

That decision has now been made.

**Decision: proceed with the unified architecture.**

The v2.0 implementation establishes the intended architectural
direction: a manuscript is interpreted into a document representation
that can be consumed by the common publishing infrastructure and
rendered into multiple output formats.

The migration does not require the immediate deletion of every
book-specific internal dataclass. `Part`, `Chapter`, and `Scene` may
remain as compatibility or interpretation structures where they are
still useful. Their continued existence does not change the
architectural contract.

The important boundary is that document semantics are no longer
defined by a renderer-specific or output-specific implementation.

---

| Task | Status | Outcome | Depends on |
|---|---|---|---|
| D0 | **Shipped** | Validated the generic document architecture against both book and technical-document structural requirements and established the parser → document model → interpretation → renderer separation. | Phase C |
| D1 | **Shipped** | Introduced the generic `Document` / block-stream model and interpretation layer. | D0 |
| D2 | **Shipped** | Added the generic Markdown document parser supporting headings, paragraphs, verse and extensible block types. | D1 |
| D3 | **Shipped** | Wired technical documents into the generic document pipeline and added native Typst and EPUB rendering, including document asset handling. | D2 |
| D4 | **Shipped** | Validated the generic pipeline against real technical manuscripts, including RideTogether EngineeringDesign and APIEngineeringReference, with PDF and EPUB output. | D3 |
| D5 | **Shipped — v2.0** | Unified the publishing architecture around the generic document approach. The common Typst and EPUB rendering infrastructure now provides the shared publishing boundary for manuscripts and output formats. Book-specific structural classes may remain internally where useful; they are no longer the architectural boundary of the publishing system. | D4 |

---

## D5 — Final migration decision

D5 was originally defined as an explicit decision point rather than
an automatic commitment to rewrite the book pipeline.

After D1–D4 were implemented and validated against real documents,
the evidence supported continuing with the generic architecture.

### Decision

**The generic document architecture is now the production direction
for VTR Press.**

The architectural objective of D5 is therefore considered achieved
in v2.0.

The objective is not "remove every historical Book dataclass."

The objective is:

- one manuscript remains the source of truth;
- document structure is represented independently of output format;
- document semantics are interpreted independently of presentation;
- Typst and EPUB share common rendering concepts;
- the same publishing system can produce multiple output formats;
- adding document capabilities should not require duplicating
  renderer-specific structural logic.

The remaining book-specific structures are implementation details and
may be retired incrementally when there is a demonstrated benefit.

---

## v2.0 Migration Outcome

Phase D has changed VTR Press from a primarily book-oriented
publishing engine into a generic document publishing engine.

The resulting conceptual pipeline is:

    Manuscript
        │
        ▼
    Markdown Parser
        │
        ▼
    Generic Document Model
        │
        ▼
    Interpretation
        │
        ▼
    Common Publishing Infrastructure
        │
        ├──────────────► Typst ─────► PDF
        │
        └──────────────► EPUB ──────► EPUB

The manuscript therefore remains independent of the final publication
format.

This is the architectural milestone represented by **v2.0**.

---

## Migration Status at v2.0

| Phase | Status |
|---|---|
| A — Unblock RideTogether | **Complete** |
| B — Renderer gaps | **Complete** |
| C — Automatic theme selection | **Complete** |
| D0 — Design validation | **Complete** |
| D1 — Generic Document Model | **Complete** |
| D2 — Generic Markdown parser | **Complete** |
| D3 — Technical-document migration | **Complete** |
| D4 — Real-world validation | **Complete** |
| D5 — Book unification / architectural adoption | **Complete — v2.0** |

**Migration Plan status: COMPLETE.**

Future work should now be tracked as product/architecture evolution
rather than as continuation of the original migration.

---

## What remains intentionally incremental

Completion of the migration does not mean the codebase is frozen.

The following may continue to evolve independently:

- retirement of remaining legacy book-specific structures;
- richer Markdown block types;
- native table rendering improvements;
- EPUB presentation refinements;
- additional themes;
- additional document types;
- additional output formats;
- stronger schema validation;
- renderer/theme registries where justified.

These are post-migration improvements, not unfinished migration phases.

---

## Revision history

| Date | Change |
|---|---|
| Initial draft | Phases A–D defined following the parser architecture review and generic-model migration review. |
| 2026-08-28 | Updated for v2.0. D0–D4 confirmed complete and D5 marked complete based on the achieved unified document publishing architecture. The original D5 wording is retained as historical context; remaining legacy book structures are treated as implementation details rather than a blocker to architectural completion. |