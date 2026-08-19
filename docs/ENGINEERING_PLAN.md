> **Current status: Phase D through D4 is complete.**
>
> D3 and D4 shipped as part of v0.9.1. The current follow-up is native
> Markdown table support for technical documents. Historical task and
> release-planning entries below are retained as engineering history and
> should not be interpreted as outstanding work.
>
# VTR Press Engineering Plan

## Purpose

This document translates `docs/MIGRATION_PLAN.md` into executable
engineering work. Where the Migration Plan says *what* changes and
*why*, this document says *how*: implementation strategy, affected
modules, sequencing, testing, regression checks, definition of done,
commit boundaries, release checkpoints, rollback plans, and risks —
for every task in every phase.

This is an execution guide, not a design document. It assumes
`ARCHITECTURE.md`, `SPECIFICATION.md`, `PUBLISHING_PRINCIPLES.md`,
`LEARNINGS.md`, and `MIGRATION_PLAN.md` as given and doesn't re-argue
them.

**Ground rule, inherited from `ROADMAP.md`'s Architecture Evolution
section**: every task below is only "done" if it simultaneously
(1) delivers user value, (2) preserves a releasable product,
(3) reduces technical debt, (4) improves extensibility, and
(5) avoids unnecessary rewrite. These five criteria are the spine of
every "Definition of Done" section in this document — not a separate
checklist, but the actual bar.

---

## Terminology note (read before Phase D)

The finalized `PUBLISHING_PRINCIPLES.md` now lists **Document Model**
as its own component in Separation of Responsibilities, distinct from
Parser ("Parser — interpretation", "Document Model — logical
structure"). This is a real formalization, but it's worth being
precise: the finalized docs establish the Document Model as a
**named artifact** sitting between parser and renderer — they do not
mandate a strict three-stage *processing pipeline* with parsing and
interpretation as fully separate passes, which was one framing
explored during the architecture review. Phase D's design-validation
work (D0) should target what's actually written down — a clean,
shared Document Model artifact, assembled by the Parser, consumed
unchanged by every Renderer — rather than assume a specific internal
pipeline shape that isn't yet a documented commitment. Where this plan
refers to an "interpretation" concern, it means logic that decides
what a piece of structure *means* for a given `metadata.type` — it
does not presuppose that logic lives in its own separate module.

---

## Git & Release Conventions Used Throughout

- **Ticket numbering**: continues the existing `VP-00x` convention
  (VP-001 was Document Type Metadata). Each task below gets one
  ticket number; sub-tasks within a task share it unless noted.
- **Branching**: one short-lived branch per ticket, off `main`,
  merged via a single squash or fast-forward merge — matching the
  repo's existing history (small, focused commits per change).
- **Tags**: one tag per **phase-level release checkpoint**, continuing
  the existing `v0.8.1`-style sequence — not one tag per task. Tasks
  within a phase land on `main` sequentially; the tag marks the point
  the phase's Definition of Done is fully met.
- **Reference manuscripts as regression harness**: per `ROADMAP.md`
  ("these manuscripts serve as regression tests for architectural
  evolution"), the Engineering Memoir, HomeLab Engineering, and
  RideTogether SAD manuscripts are re-published and spot-checked
  after every task that touches parser, model, or renderer code —
  not just at phase boundaries. This is called out explicitly per
  task below, not left implicit.

---

# Phase A — Unblock the RideTogether Manuscript

**Phase objective**: RideTogether parses and renders end-to-end on
the current parser, using the technical theme, with zero change to
`type: book` behavior.

**Phase-level release checkpoint**: tag `v0.9.0` once A1–A3 are all
merged and RideTogether publishes successfully via `run.py`.

**Phase-level rollback plan**: A1 is a manuscript edit — trivially
revertible (undo the edit). A2/A3 are additive (new block type, new
render-dispatch cases); rollback is a straight revert of each
commit, since nothing existing is modified, only extended.

---

### Phase A Execution Note

The original VP-002/A1 hypothesis was invalidated by testing the real
RideTogether manuscript.

The anticipated preamble error did not occur. Instead, the first real
blocker was a heading-hierarchy incompatibility requiring the Subheading
capability described in A2.

As a result, the implementation of VP-002 expanded beyond the original
A1 scope and delivered the effective A2/A3 capability in one validated
increment.

No separate manuscript-only A1 change was required.

## Task A1 — Manuscript preamble fix

| | |
|---|---|
| **Ticket** | VP-002 |
| **Objective** | Resolve the exact `"Paragraph found outside a Section or Chapter"` error by adding a leading `##` heading to the RideTogether manuscript before its preamble content. |
| **Implementation strategy** | Content edit only. Add an appropriate heading (e.g. `## Overview`) immediately before the first block of prose in the manuscript, matching the convention every existing book manuscript already follows. |
| **Affected modules** | None in this repository — the manuscript lives outside it (`../../Projects/RideTogether/...` per `books.yaml`). This task is tracked here because it's a precondition for A2/A3's validation, not because it touches VTR Press code. |
| **Recommended order** | First — must land before A2/A3 can be validated against real content, since it's what reveals the *next* actual error (the `###`-under-`##`-Section case A2 exists to fix). |
| **Testing strategy** | Manual: run `python run.py ride` and confirm the specific error message disappears. No automated test — there's no code change to test. |
| **Regression checks** | None required — no code path touched. |
| **Definition of done** | `python run.py ride` no longer raises `"Paragraph found outside a Section or Chapter."` (it will still fail on the next structural issue until A2/A3 land — that's expected and confirms this task's scope is complete). |
| **Commit boundary** | No commit in this repository. Tracked here for sequencing only. |
| **Release checkpoint** | N/A — contributes to Phase A's `v0.9.0`, not a standalone release. |
| **Rollback** | Revert the manuscript edit if needed; zero blast radius. |
| **Risks** | Low. The only risk is discovering RideTogether has *multiple* preamble-like gaps, not just one — worth a full read-through of the manuscript before declaring this "done," rather than fixing the first error and assuming it's the only one. |

---

## Task A2 — `Subheading` block type + parser branch

| | |
|---|---|
| **Ticket** | VP-003 |
| **Objective** | Allow `###` to mean "subsection of a `##` Section" (not only "Chapter of a Part"), so a realistic numbered-section technical document can parse. |
| **Implementation strategy** | Add one new `Block` variant (`Subheading`, a `title`-only dataclass, same shape as `Paragraph`/`Verse`) to `model.py`. Add one new conditional branch to the `### ` handler in `parser/structure.py`: when `current_part is None` **and** `current_section is not None`, flush any pending paragraph and append a `Subheading` to the current section's `blocks`, instead of raising. When both are `None` (no heading at all yet), the existing `"Chapter found outside a Part"` error is unchanged. |
| **Affected modules** | `model.py` (new dataclass), `parser/structure.py` (one new branch), `tests/test_structure.py` (new cases). |
| **Recommended order** | Second, after A1 confirms this is genuinely the next blocker. Model change first (so the parser change has something to construct), then the parser branch. |
| **Testing strategy** | Unit tests in `test_structure.py`: (1) `##` Section followed directly by `###` Subsection succeeds and the `Subheading` attaches to the section's `blocks` in the right position; (2) the existing "no heading at all" case (`test_chapter_outside_part_raises`) still raises identically — confirmed by direct code inspection that this test's scenario has `current_section is None` too, so it's untouched by the new branch, but re-run it explicitly, don't just reason about it; (3) a `###` under an actual `## Part` still produces a `Chapter`, not a `Subheading` — confirms the existing book path is genuinely unaffected, not just theoretically unaffected. |
| **Regression checks** | Full existing test suite must stay green. Re-publish the Engineering Memoir and HomeLab Engineering manuscripts (both `type: book`, both use Part/Chapter/Scene) and confirm identical output — this is the concrete check that "additive" claim actually holds, not just an assertion. |
| **Definition of done** | New tests pass; full suite green; both existing book manuscripts produce byte-identical (or at minimum structurally identical) Typst/EPUB output to before this change; RideTogether's manuscript parses past the subsection structure (may still fail at render time — that's A3's job, expected here). |
| **Commit boundary** | One commit (or two: model change, then parser change) — small enough that a single PR/ticket is appropriate. Don't bundle with A3; a parse-time change and a render-time change are different enough failure surfaces to want independently revertible commits. |
| **Release checkpoint** | Contributes to Phase A's `v0.9.0`. Not tagged standalone. |
| **Rollback** | Revert the parser branch and the model addition together — both are purely additive, so reverting removes the capability without touching anything else. No data migration concerns (nothing is persisted). |
| **Risks** | Low technical risk (evidenced non-breaking, per the regression check above). The real risk is scope creep: if RideTogether's manuscript reveals it needs *nested* subsections (`####` under `###` under `##`) rather than one flat level, this task's scope should **not** silently expand to cover that — flag it as a follow-up rather than generalizing further inside this ticket. |

---

## Task A3 — Renderer support for `Subheading`

| | |
|---|---|
| **Ticket** | VP-004 |
| **Objective** | Prevent the `TypeError("Unsupported block: Subheading")` that would otherwise fire the moment A2's new block type reaches either renderer — both `renderer/typst.py` and `renderer/epub.py` currently hard-fail on unrecognized block types by design (confirmed by direct inspection; this is intentional fail-loud behavior, not a bug to work around). |
| **Implementation strategy** | Add one matching `isinstance` case to `_render_block` in each renderer, emitting a level-3 heading (Typst: native `### ` heading syntax or `#heading(level: 3)[...]`; EPUB: an `<h3>` element). Both the classic and technical themes already have level-3 heading styling in `headings.typ`, so no theme changes are needed for this task. |
| **Affected modules** | `renderer/typst.py`, `renderer/epub.py`, `tests/test_typst_renderer.py`, `tests/test_epub_renderer.py`. |
| **Recommended order** | Third, immediately after A2 — A2 without A3 leaves technical documents unable to actually render, only parse, which isn't a usable intermediate state to release on its own. |
| **Testing strategy** | Unit tests in both renderer test files: a `Section` containing a `Subheading` followed by a `Paragraph` renders both correctly, in order, at the expected heading level. Compile-verify at least once against the real Typst compiler (as done for prior theme/renderer tickets) rather than relying on string-matching the generated Typst source alone — string output can be syntactically well-formed and still fail to compile. |
| **Regression checks** | Full suite green. Re-publish Engineering Memoir and HomeLab Engineering (no `Subheading` blocks present — output must be identical). Compile RideTogether end-to-end and visually/structurally confirm subsections render as expected (correct heading level, correct position, no duplicate or missing content). |
| **Definition of done** | RideTogether publishes successfully via `python run.py ride`, using the technical theme, with subsections visibly rendered; both renderer test suites cover the new block type; no change to output for any existing manuscript. |
| **Commit boundary** | One commit per renderer (Typst, EPUB) — independently revertible, since EPUB and PDF output are genuinely separate concerns and a defect in one shouldn't block shipping the other. |
| **Release checkpoint** | **This task completes Phase A.** Tag `v0.9.0` here, once RideTogether is confirmed publishing end-to-end. |
| **Rollback** | Revert the renderer cases independently per format if a defect is found in only one. Since A2 is additive and doesn't require A3 to exist for existing manuscripts, reverting A3 alone (leaving A2 in place) is safe — it just means `Subheading` blocks can't render again, reverting to the pre-A2 failure mode for any manuscript that uses them. |
| **Risks** | Low-Medium. The specific risk worth naming: TOC/outline behavior for `Subheading` isn't yet decided (should a subsection appear in the Contents page, and if so, numbered or not?). Don't let this ambiguity block the ticket — pick the simpler default (subsection appears in outline, unnumbered, consistent with how the technical theme already scopes numbering to `outlined: true` sections) and document the decision in the commit message so it's revisitable, not silently baked in as an assumption. |

---

# Phase B — Close Renderer Gaps Found While Building the Technical Theme

**Phase objective**: technical documents get a working Table of
Contents, correct page numbering, and no stray blank leading page.

**Phase-level release checkpoint**: tag `v0.9.1` once B1 and B2 are
both merged and verified against RideTogether.

**Phase-level rollback plan**: both tasks touch shared renderer logic
that book manuscripts also pass through (the `PROLOGUE`-triggered
logic, the cover/pagebreak call). Rollback for either task is a
straight revert, but **must be verified against both existing book
manuscripts before considering the revert complete** — these are the
first two tasks in the whole plan that modify code book manuscripts
actively depend on, not just code that happens to be adjacent to it.

**Explicit labeling reminder** (from `MIGRATION_PLAN.md`): both B1 and
B2 are deliberate stopgaps, expected to be superseded once Phase D's
Document Model work lands. Say so in both commit messages, so nobody
later mistakes either for permanent architecture.

---

## Task B1 — Generalize the Contents/main-matter trigger

| | |
|---|---|
| **Ticket** | VP-005 |
| **Objective** | Stop gating Table of Contents insertion and main-matter page-numbering reset exclusively on `SectionKind.PROLOGUE` (a book-only concept), so technical documents (which have no Prologue) get both. |
| **Implementation strategy** | Generalize the trigger condition in `renderer/typst.py`'s `_render_section` from "this section's kind is `PROLOGUE`" to something broader — e.g. "this is the first `outlined` section encountered." For every existing book manuscript, `PROLOGUE` is normally already the first outlined section, so this is expected to be behavior-preserving for `type: book` — but that expectation must be *verified*, not assumed (see regression checks). |
| **Affected modules** | `renderer/typst.py`, `tests/test_typst_renderer.py`. |
| **Recommended order** | First in Phase B — B2 doesn't depend on it, but B1 is the more structurally central of the two (page numbering affects every page in the document), so it's worth landing and stabilizing before layering B2 on top. |
| **Testing strategy** | Unit tests: (1) a technical-document-shaped book (Copyright + `SectionKind.OTHER` sections, no Prologue) gets a Contents page and page numbers starting at 1 for the first content section; (2) a book-shaped manuscript (Copyright, Prologue, Part/Chapter) triggers Contents/main-matter at the *same point* it did before this change — this needs an explicit "before vs. after" comparison, not just "does it still work," since the whole point is proving the trigger condition change is a no-op for books. |
| **Regression checks** | Full suite green. Re-publish Engineering Memoir and HomeLab Engineering and diff the generated Typst source against pre-change output — not just "does it compile," but confirm the Contents page and page-numbering start appear on the identical page as before. This is the single most important regression check in Phase B, since it's the first task that could plausibly change book output. |
| **Definition of done** | RideTogether gets a Contents page and correctly-reset page numbers; both book manuscripts produce identical Typst output (confirmed via diff, not inspection); new tests cover both the technical-document and book cases explicitly. |
| **Commit boundary** | Single commit — the change itself is small (one trigger condition), most of the diff will be tests. |
| **Release checkpoint** | Contributes to `v0.9.1`, not standalone. |
| **Rollback** | Revert to the `SectionKind.PROLOGUE`-only trigger. Before considering rollback complete, re-verify both book manuscripts still produce their pre-B1 output (i.e. confirm the revert is a true no-op, not just an assumed one). |
| **Risks** | **Medium** — this is the first task in the plan that touches a code path with real, currently-correct, ISBN-published output riding on it. The "PROLOGUE is normally the first outlined section anyway" assumption needs to be checked against the *actual* manuscripts, not just the test fixtures, before merging. If either published book's manuscript has some other `outlined` section before its Prologue (unlikely, but unverified until checked), this task's approach needs rethinking before it ships, not after. |

---

## Task B2 — Decouple cover/pagebreak from unconditional execution

| | |
|---|---|
| **Ticket** | VP-006 |
| **Objective** | Stop the renderer from unconditionally calling `render-cover()` followed by `#pagebreak()` regardless of document type — today this produces one blank leading page for technical documents even though the technical theme's `render-cover` is already a no-op. |
| **Implementation strategy** | Introduce a renderer-level decision (not yet a full convention-profile system — that's Phase D territory) for whether to call `render-cover`/`pagebreak` at all, keyed off `metadata.type` for now. This is intentionally a narrower, more mechanical fix than the "proper" long-term shape (a convention-profile flag the renderer reads generically) — the narrower version is appropriate here because Phase C/D don't exist yet to hang a cleaner mechanism off of. |
| **Affected modules** | `renderer/typst.py`, `tests/test_typst_renderer.py`. |
| **Recommended order** | Second in Phase B, after B1. Independent in principle, but sequencing after B1 keeps the two page-numbering-adjacent changes from landing simultaneously and complicating any regression triage. |
| **Testing strategy** | Unit tests: technical-document-typed input produces no leading blank page (confirmed by checking the compiled PDF's page count and page 0 content, not just the generated Typst source — the source alone won't reveal the blank-page artifact, only compilation will). Book-typed input still gets its cover exactly as before. |
| **Regression checks** | Full suite green. Compile (not just generate Typst for) both existing book manuscripts and confirm identical page count and cover placement to pre-change output. Compile RideTogether and confirm the leading blank page is gone. |
| **Definition of done** | RideTogether's compiled PDF has no leading blank page; both book manuscripts compile to identical page counts and cover placement as before; the commit message explicitly labels this as a stopgap superseded by Phase D. |
| **Commit boundary** | Single commit. |
| **Release checkpoint** | **This task completes Phase B.** Tag `v0.9.1` here. |
| **Rollback** | Revert to unconditional cover/pagebreak. Re-verify book manuscript page counts post-revert, same discipline as B1. |
| **Risks** | Medium, same category as B1 — real published output depends on the code path being touched. Additional specific risk: this task is explicitly a "good enough for now" mechanism (a direct `metadata.type` check in the renderer) that Phase D is expected to replace. There's a real temptation to over-engineer this into a mini version of the convention-profile system prematurely — resist that; the smallest correct fix here is a single conditional, not a new abstraction. Over-building this task would itself violate the "avoid unnecessary rewrite" criterion this whole plan is measured against. |

---

# Phase C — Automatic Theme Selection

**Phase objective**: `python run.py <book>` selects the correct theme
automatically from `metadata.type`; no manual theme-path edits.

**Phase-level release checkpoint**: tag `v0.9.2` once C1 is merged and
C2's decisions are recorded (not necessarily all *implemented* — see
below).

**Phase-level rollback plan**: C1 replaces one hardcoded constant with
a lookup; reverting restores the constant. Zero risk to book output,
since `book` remains the default/fallback in the lookup, identical to
today's only behavior.

---

## Task C1 — Type → theme dispatch

| | |
|---|---|
| **Ticket** | VP-007 |
| **Objective** | Replace the hardcoded `DEFAULT_THEME_IMPORT` constant in `renderer/typst.py` with a lookup from `book.metadata.type` to a theme import path, defaulting to `themes/classic` for `book` and any omitted/unrecognized value (pending C2's decision on whether "unrecognized" should instead be a hard error — see below). |
| **Implementation strategy** | A small `dict[str, str]` mapping type → theme import path, consulted where `DEFAULT_THEME_IMPORT` is currently used directly. No new abstraction beyond the dict — a registry/plugin mechanism is explicitly Phase-D-or-later territory (see Decision Log item 6 in `MIGRATION_PLAN.md`), not needed for two themes. |
| **Affected modules** | `renderer/typst.py`, `tests/test_typst_renderer.py`. |
| **Recommended order** | Only task in this phase with code; sequenced after Phase B so technical documents are genuinely publication-ready (TOC, page numbering, no blank cover page) before they're reachable by default rather than by manual override. |
| **Testing strategy** | Unit tests: `metadata.type == "technical-document"` resolves to the technical theme's import path in generated Typst source; `metadata.type == "book"` and omitted `type` both resolve to classic's path (three explicit cases, not two — "book" and "omitted" going through the same code path is exactly the thing worth asserting directly, not inferring). |
| **Regression checks** | Full suite green. Re-publish both book manuscripts with no `type` field and confirm classic theme is still selected (i.e. confirm the *default* path, not just the explicit-`book` path, since real existing manuscripts rely on the default). Publish RideTogether and confirm the technical theme is now selected automatically, with no manual override needed. |
| **Definition of done** | `python run.py ride` uses the technical theme without any code-level override; both existing books are unaffected; new tests cover all three type-resolution cases explicitly. |
| **Commit boundary** | Single commit. |
| **Release checkpoint** | Tag `v0.9.2` once this lands and C2 is recorded. |
| **Rollback** | Revert to the hardcoded constant — trivial, since the dict's `"book"` entry is identical to what the constant always pointed to. |
| **Risks** | Low. The main risk is masking C2's open questions rather than actually resolving them — see below. |

---

## Task C2 — Record open decisions before they calcify

| | |
|---|---|
| **Ticket** | VP-008 (tracking/decision ticket, not necessarily a code ticket) |
| **Objective** | Resolve, or explicitly defer with a reason, the open questions C1 surfaces: (1) is `metadata.type` a validated/closed set of values, or does it stay an open string forever — confirmed today it silently accepts *any* string; (2) is a cover image mandatory for technical documents, given `run.py`/`books.yaml` currently assume yes for every type; (3) formalize or retire the dead `Metadata.paper` field now that `type` drives page size instead. |
| **Implementation strategy** | This is a decision-making task, not necessarily an implementation one. If (1) is resolved as "validated," that's a small follow-up ticket (raise on unrecognized `type` at read time, in `parser/reader.py`) — genuinely small, but deliberately **not bundled into C1**, so C1's shippability isn't gated on a product decision about error-handling strictness. |
| **Affected modules** | Decision-dependent. Most likely `parser/reader.py` (if type validation is added) and `docs/SPECIFICATION.md` (to document the accepted values, if closed). |
| **Recommended order** | Can happen in parallel with C1 as a decision-making conversation; any resulting code change should land as its own ticket, after C1, once the decision is made — not speculatively before. |
| **Testing strategy** | If type validation is added: a test asserting an unrecognized `type` value raises a clear, actionable error rather than silently falling back to classic. |
| **Regression checks** | If validation is added, confirm it doesn't reject `"book"`, `"technical-document"`, or the omitted case — the three values every current manuscript actually uses. |
| **Definition of done** | Each of the three questions has either a recorded decision (in `MIGRATION_PLAN.md`'s Decision Log) or an explicit "deferred, revisit when X happens" note — not left silently unresolved and undocumented. |
| **Commit boundary** | Documentation-only commit for the decisions themselves; separate commit(s) for any resulting code change. |
| **Release checkpoint** | Contributes to `v0.9.2` if resolved in time; otherwise doesn't block the tag — these are real but non-blocking decisions. |
| **Rollback** | N/A for the decision itself; any resulting code change follows its own task's rollback plan. |
| **Risks** | The main risk is this task quietly never happening — decision-only tickets are the easiest kind to let slide once the "more interesting" code tasks are available. Recommend genuinely scheduling this, not treating it as ambient background work. |

---

# Phase D — Generic Document Model Migration

**Phase objective**: new document types stop requiring parser
changes. Structure comes from a shared Document Model; only
interpretation (per type) and presentation (per theme) differ.

**Phase-level release checkpoint**: **no single tag for all of Phase
D.** Unlike Phases A–C, D's tasks are sequential *within* a still-experimental
path and shouldn't all be bundled behind one release gate — see D3's
entry for why the recommended approach is to tag incrementally as
each sub-milestone proves itself, rather than holding the tag until
everything (including D5) is settled.

**Phase-level rollback plan**: D0–D2 are additive and reversible in
the ordinary sense (revert the commits). D3 is the first point where
rollback has real consequence — see D3 specifically.

**Scope reminder** (from `MIGRATION_PLAN.md`): this phase targets
books, technical documents, white papers, tutorials, and (with
caveats) API references. Documentation websites and notebooks are
explicitly out of scope for this phase's design — don't let them
influence D0–D4's shape.

---

## Task D0 — Design-validation checkpoint

| | |
|---|---|
| **Ticket** | VP-009 |
| **Objective** | Before writing any Phase D code, validate — on paper or as a throwaway spike, not as production code — that a proposed Document Model contract can express both book's structural rules (Part → Chapter → Scene, Scene requires Chapter) and technical-document's rules (numbered sections, subsections, appendices), and that it's consistent with the finalized `PUBLISHING_PRINCIPLES.md` wording (Parser — interpretation; Document Model — logical structure; see Terminology note above). |
| **Implementation strategy** | Not implementation. Concretely: write out, in a design note, (a) the exact shape of the proposed Document Model (per the architecture review's revised recommendation: a flat, ordered block stream rather than a recursive tree — `Heading(level, title)`, `Paragraph`, `Verse`, etc.), (b) which layer decides that a given heading "is" a Chapter vs. a Section vs. a Subsection for a given `metadata.type`, and (c) walk both book's and technical-document's actual current manuscripts through that design by hand, checking every existing structural rule has a home. If any rule doesn't fit cleanly, that's a finding to resolve *before* D1, not during it. |
| **Affected modules** | None — this task produces a design artifact (a markdown doc or equivalent), not code. Recommend `docs/DOCUMENT_MODEL_DESIGN.md` or similar as the artifact, so it's reviewable the same way `MIGRATION_PLAN.md` is. |
| **Recommended order** | First in Phase D, strictly before D1. This is the highest-leverage step in the entire plan — it's the exact place the architecture review found the original migration proposal under-specified, and getting it wrong here is what would let book-shaped assumptions leak back into the new model one layer removed. |
| **Testing strategy** | N/A — no code. The "test" is the manual walk-through against both document types' actual rules, and ideally a second reviewer checking the design note before D1 begins. |
| **Regression checks** | N/A. |
| **Definition of done** | A written design note exists, covering the Document Model's shape and the type-to-structure decision logic, explicitly checked against both book's and technical-document's real structural rules, with any gaps found resolved or explicitly flagged as follow-up before D1 starts. |
| **Commit boundary** | One commit adding the design document. |
| **Release checkpoint** | Not a release checkpoint — no code ships. |
| **Rollback** | N/A. |
| **Risks** | The main risk is skipping or rushing this step because it doesn't feel like "real progress" compared to writing code. It is real progress — it's the step that makes D1–D4 cheap instead of expensive. Treat a rushed or skipped D0 as the single most likely cause of Phase D needing rework later. |

---

## Task D1 — Introduce the Document Model as new, additive code

| | |
|---|---|
| **Ticket** | VP-010 |
| **Objective** | Add the flat block-stream Document Model (per D0's validated design) to `model.py`, as new code that doesn't touch `Part`/`Chapter`/`Scene`/`Section`. |
| **Implementation strategy** | New dataclasses only, following D0's design note exactly — this task should not involve any new design decisions, only implementing decisions D0 already made. If implementing D1 reveals a gap in D0's design, that's a signal to go back and fix the design note, not to improvise a fix inline. |
| **Affected modules** | `model.py`, `tests/test_structure.py` or a new `tests/test_document_model.py`. |
| **Recommended order** | Immediately after D0. |
| **Testing strategy** | Unit tests constructing the new model types directly (no parser involved yet) and asserting their shape matches D0's design — this is closer to a spec-compliance test than a behavior test, since nothing consumes this model yet. |
| **Regression checks** | Full suite green — trivially true, since nothing existing references the new types yet. This is the safest task in the entire plan from a regression standpoint. |
| **Definition of done** | New model types exist, match D0's design note, have unit test coverage, and are entirely unreferenced by any existing parser or renderer code. |
| **Commit boundary** | Single commit. |
| **Release checkpoint** | Can ship as part of a minor tag (e.g. `v0.9.3`) purely as "new, inert code" — safe to release since it changes no behavior. |
| **Rollback** | Trivial — delete the new code; nothing depends on it yet. |
| **Risks** | Low. The one real risk is drift between D0's design note and D1's implementation if enough time passes between them — keep them close together, ideally same contributor, same week. |

---

## Task D2 — Parallel parser producing the Document Model

| | |
|---|---|
| **Ticket** | VP-011 |
| **Objective** | Build a second, independent parser path that produces the new Document Model from Markdown headings, without touching the existing Part/Chapter/Scene parser at all. |
| **Implementation strategy** | New module (e.g. `parser/document_model.py`), following D0's design for how heading depth + `metadata.type` combine to assign structure. Genuinely parallel — the existing `parser/structure.py` is not modified, not refactored, not shared with, in this task. Sharing genuinely common concerns (front-matter reading, inline formatting) is fine and expected — `parser/reader.py` and `parser/inline.py` are already type-agnostic and can be reused as-is. |
| **Affected modules** | New parser module; possibly light touches to `parser/reader.py` if the dispatch point needs adjusting (see D3) — but D2 itself should not yet be *reachable* by any real manuscript. |
| **Recommended order** | After D1. Before D3 — this task builds the capability; D3 is what makes it reachable. |
| **Testing strategy** | Unit tests feeding synthetic Markdown directly into the new parser and asserting the resulting Document Model structure — mirroring the style of `test_structure.py`'s existing unit tests, but targeting the new model. |
| **Regression checks** | Full suite green. Since this parser isn't wired into any real code path yet, there's nothing to regress — same low-risk profile as D1. |
| **Definition of done** | The new parser correctly produces Document Model structures for representative synthetic inputs covering book-shaped and technical-document-shaped content, per D0's design; not yet reachable from `run.py` or `publish.py`. |
| **Commit boundary** | Single commit, or split by sub-concern (heading-depth logic, type-to-structure logic) if the diff is large enough to benefit from smaller review units. |
| **Release checkpoint** | Can ship inertly alongside D1, same reasoning — new, unreachable code is safe to release. |
| **Rollback** | Trivial — same as D1, nothing depends on it yet. |
| **Risks** | Low-Medium. The risk worth naming: it's tempting to validate this parser only against clean, hand-crafted synthetic input. Push at least one messy, real-shaped test through it before calling this task done — even though full validation against real manuscripts is D4's job, catching an obviously wrong design choice here is far cheaper than catching it in D4. |

---

## Task D3 — Wire dispatch for `type: technical-document`

| | |
|---|---|
| **Ticket** | VP-012 |
| **Objective** | Route `type: technical-document` manuscripts through the new parallel parser; `type: book` (including omitted) continues through the existing parser, completely unaffected. |
| **Implementation strategy** | A dispatch point in `parser/reader.py` or `publish.py` (wherever parsing is invoked) branching on `metadata.type`. This is the first point in Phase D where the new path becomes *reachable* by a real manuscript — treat it accordingly. |
| **Affected modules** | `parser/reader.py` or `publish.py` (dispatch point), `tests/test_integration.py`. |
| **Recommended order** | After D2. This task is the boundary between "Phase D is inert, low-risk new code" and "Phase D is live for at least one real document type" — everything before this point could be reverted with zero user-facing consequence; this task is where that stops being true. |
| **Testing strategy** | Integration tests: a `type: technical-document` manuscript now produces output via the new parser (verifiable by checking for the new model's structural signature in the result); a `type: book` manuscript's output is byte-identical to before this change. |
| **Regression checks** | Full suite green. Re-publish both existing book manuscripts and confirm identical output to the pre-D3 baseline — this is non-negotiable, since D3 is the first task that changes which code path a real manuscript's type resolves to. Re-publish RideTogether through the *new* path and compare its output against the version produced by the *old* path (post-A2/A3/B1/B2) — differences are expected (that's the point) but should be reviewed deliberately, not just accepted as "different, therefore fine." |
| **Definition of done** | RideTogether publishes via the new Document Model path; both book manuscripts are unaffected; the dispatch point has explicit test coverage for all three `type` values, not just the new one. |
| **Commit boundary** | Single commit for the dispatch logic itself, kept small and easy to revert independently of D1/D2's larger diffs. |
| **Release checkpoint** | **Tag here** (e.g. `v0.10.0`) — this is a genuinely user-visible milestone (RideTogether now runs on the new model) distinct from D1/D2's inert groundwork, and distinct from D4's validation work. Don't wait for D4 to tag this; D4 is about building *confidence* in what D3 already shipped, not a precondition for shipping it. |
| **Rollback** | Revert the dispatch point back to routing everything through the existing parser. Because D1/D2's code remains inert once un-dispatched, this is a clean, low-risk rollback — but unlike D1/D2, this rollback has a real consequence (RideTogether stops using the new path), so it should be a deliberate decision, not a reflexive one, if something's found wrong post-release. |
| **Risks** | **Medium-High** — this is the highest-risk task in Phase D, because it's the first one with a live consequence. Two specific risks: (1) a subtle bug in the dispatch condition accidentally routing a `book`-typed manuscript through the new path — guard explicitly against this with the "book output is byte-identical" regression check, not just "book output looks fine"; (2) declaring this task done based on RideTogether alone, without D4's broader validation — resist that; D3's Definition of Done is deliberately scoped to "reachable and correct for RideTogether," not "proven," because D4 is where "proven" actually gets established. |

---

## Task D4 — Validate against structurally different manuscripts

| | |
|---|---|
| **Ticket** | VP-013 |
| **Objective** | Establish real confidence in the new Document Model by validating it against 2–3 real manuscripts, **including at least one structurally different from RideTogether** (table-heavy, unusually deep nesting, or similar) — not just another similarly-shaped prose document, per the architecture review's explicit strengthening of this step. |
| **Implementation strategy** | Not a code task primarily — a validation exercise. If a genuinely different-shaped manuscript doesn't exist yet, this task includes creating one deliberately (even a synthetic reference manuscript under `examples/`) rather than declaring the model validated on the strength of one real-world example. |
| **Affected modules** | Possibly `examples/` (new reference manuscript), plus any fixes to D1–D3's code that this validation surfaces. |
| **Recommended order** | After D3. This is explicitly a *finding* task, not a *building* task — expect it to generate follow-up work, don't expect it to be a clean pass. |
| **Testing strategy** | End-to-end: publish each validation manuscript, inspect output for correctness (not just "it compiled"), and add each as a permanent regression fixture once it passes, per `ROADMAP.md`'s framing of reference manuscripts as regression tests. |
| **Regression checks** | Every manuscript used in this validation becomes a standing regression check for all future Phase D (and eventually Phase D5) work — this task's real output is as much "new permanent regression coverage" as it is "confidence that D1–D3 are correct." |
| **Definition of done** | At least one structurally-different-from-RideTogether manuscript has been validated end-to-end through the new Document Model path; any defects found are either fixed or explicitly tracked; all validation manuscripts are added as reference fixtures for ongoing regression checking. |
| **Commit boundary** | Separate commits per fix found, plus one commit adding the new reference manuscript(s) if created. Resist bundling unrelated fixes into one large commit just because they were found in the same validation pass. |
| **Release checkpoint** | Tag once this task's findings are resolved (e.g. `v0.10.1`) — this is what turns D3's "shipped" into "trustworthy," and is worth its own checkpoint rather than being silently folded into D3's tag. |
| **Rollback** | Any individual fix found here follows its own task-level rollback; there's no single "rollback D4" action since it's a validation exercise, not a feature. |
| **Risks** | The risk worth naming explicitly: settling for "found nothing wrong" as success, when the more valuable outcome is genuinely finding gaps while the blast radius is still one document type and zero published content depending on it. If this task comes back clean on the first try, treat that as a reason to try harder to break it, not as confirmation there's nothing to find. |

---

## Task D5 — *(Optional, deferred)* Migrate `book` onto the Document Model

| | |
|---|---|
| **Ticket** | Not yet assigned — explicitly not scheduled |
| **Objective** | Decide whether to retire `Part`/`Chapter`/`Scene` as separate dataclasses in favor of a book-specific interpretation over the shared Document Model. |
| **Implementation strategy** | Not defined yet, deliberately. This is a **decision point**, not a task ready for execution. |
| **Recommended order** | Only after D4 has genuinely landed, and only within the fixed revisit window recorded in `MIGRATION_PLAN.md`'s Decision Log (item 8) — the point of that window is to prevent this from either happening prematurely (before the model is proven) or lingering indefinitely (dual-model debt accumulating with no decision ever made). |
| **Definition of done (of the decision, not the migration)** | Either: a scoped D5 implementation plan exists, written with the same rigor as D0 was for the original Document Model work, or a documented decision to *not* migrate book, with the reasoning recorded in `MIGRATION_PLAN.md`. Either outcome is a valid, complete result for this task — "we decided not to" is not a failure state. |
| **Risks** | The core risk is exactly what `MIGRATION_PLAN.md` already names: migrating book purely for architectural tidiness, without a concrete problem it solves, when book already works and has real published output riding on it. If nobody can articulate a concrete benefit beyond symmetry when this window arrives, that's a legitimate reason to close this out as "not now," not a reason to force it through. |

---

## Summary — Release Checkpoints at a Glance

| Tag | Phase / Task | What it certifies |
|---|---|---|
| `v0.9.0` | Phase A complete (A1–A3) | RideTogether publishes end-to-end on the current parser, technical theme. |
| `v0.9.1` | Phase B complete (B1–B2) | Technical documents get correct TOC, page numbering, no blank leading page. |
| `v0.9.2` | Phase C complete (C1, C2 recorded) | Theme selection is automatic from `metadata.type`. |
| `v0.9.3` | D1+D2 (inert) | Document Model exists and is unit-tested; not yet live. |
| `v0.10.0` | D3 | RideTogether runs on the new Document Model path; books unaffected. |
| `v0.10.1` | D4 | New model validated against a structurally different manuscript; regression fixtures established. |
| *(unassigned)* | D5 | Decision recorded — implementation scoped separately if pursued. |

Every tag above corresponds to a state where `type: book` manuscripts
are provably unaffected and the product is fully releasable — per
`PUBLISHING_PRINCIPLES.md`'s Incremental Evolution principle, no tag
in this sequence depends on a later one to be complete and shippable
on its own terms.
