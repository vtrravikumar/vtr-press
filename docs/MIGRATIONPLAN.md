# VTR Press Migration Plan

## Purpose

This document tracks the incremental migration of VTR Press from a
book-specific engine toward the generic, multi-document-class
publishing engine described in `ARCHITECTURE.md`, `SPECIFICATION.md`,
`PUBLISHING_PRINCIPLES.md`, and `LEARNINGS.md`.

It is the execution companion to those documents: they describe the
target state and the principles; this document tracks the approved
phases, their status, and the decisions made (or still open) while
getting there.

**Ground rule**: no large rewrite. Every phase must leave the product
in a releasable state. `type: book` manuscripts must never regress,
at any point in this plan, for any phase.

---

## How to read this document

Each phase has:
- **Goal** — what becomes true once it ships.
- **Status** — Not started / In progress / Shipped / Superseded.
- **Tasks** — the concrete increments within the phase.
- **Depends on** — what must already be shipped.
- **Note** — anything about the phase's durability (e.g. "this is a
  deliberate stopgap, expected to be superseded").

Update status and notes as work lands. This document should always
reflect reality, not the original plan — if a phase's approach
changes during implementation, edit it here rather than letting this
file drift out of sync with the code.

---

## Phase A — Unblock the RideTogether manuscript

**Goal**: the RideTogether Solution Architecture Document parses and
renders end-to-end on the current (book-shaped) parser, using the
technical theme.

**Status**: Shipped

| Task | Status | Outcome |
|---|---|---|
| A1 | Superseded | The expected "Paragraph found outside a Section or Chapter" error did not occur against the real RideTogether manuscript. No manuscript-only fix was required. |
| A2 | Shipped | Added `Subheading` block support for technical-document subsection structure. |
| A3 | Shipped | Added `Subheading` rendering support to Typst and EPUB. |


### Phase A Implementation Note

The original A1 assumption was invalidated when the real RideTogether
manuscript was tested.

The manuscript reached a different heading-hierarchy failure. Investigation
of the actual parser and manuscript showed that technical-document
subsections required a `Subheading` block.

The implementation therefore proceeded directly to the A2/A3 capability,
including parser, model, Typst renderer, EPUB renderer, and regression
coverage.

Validation completed with:
- 94/94 tests passing
- RideTogether PDF generated successfully
- RideTogether EPUB generated successfully
- Fresh-clone verification successful

This is an intentional example of the migration plan being updated to
reflect implementation reality rather than preserving an incorrect
original assumption.


**Note**: A2's `Subheading` design is an *interleaved block*, not a
nested tree — it is expected to carry forward into Phase D's flat
block-stream model largely as-is, possibly generalizing directly into
that model's `Heading` block type. (Earlier drafts of this plan
described A2 as likely throwaway work once Phase D lands — that was
incorrect and is corrected here.)

---

## Phase B — Close renderer gaps found while building the technical theme

**Goal**: technical documents get a working Table of Contents, correct
page numbering, and no stray blank leading page.

**Status**: Shipped (B1 + B2 + B3 + B4)

| Task | Status | Description | Depends on |
|---|---|---|---|
| B1 | **Shipped** (`113f1e3`) | Generalized the Contents/page-numbering trigger, previously hardcoded to `SectionKind.PROLOGUE` (book-only), to "first outlined section." | Phase A |
| B2 | **Shipped** | Decoupled the cover/pagebreak call from unconditional execution — the renderer now only calls `render-cover()` + `#pagebreak()` outside print mode for `type: book`. | Phase A |
| B3 | **Shipped** | EPUB/Typst parity: `renderer/epub.py`'s own Contents-index trigger was still hardcoded to `SectionKind.PROLOGUE`, never having received B1's fix (B1 only touched `renderer/typst.py`). Generalized to the same "first outlined section" condition. Discovered while researching Phase D's D0 design note; fixed as its own narrowly-scoped ticket, no new architecture introduced. | B1 |
| B4 | **Shipped** | EPUB TOC was empty for any document with no Parts (every technical-document, since it's all top-level Sections). Root cause: `_render_section` never added a `nav_points` entry at all — only `_render_part` did, a gap that predates B1/B3 entirely and also silently affected books (Prologue/Epilogue/etc. were missing from the TOC, just masked by Part/Chapter entries still appearing). Fixed by having `_render_section` append a nav point for outlined sections, matching `renderer/typst.py`'s `#outline()` treatment (Copyright/Dedication/Thirukkural excluded). Verified against the real RideTogether manuscript: all 15 sections now populate `nav.xhtml`, `toc.ncx`, and `contents.xhtml` correctly. **Known follow-up, not implemented**: `Subheading`-level entries don't nest under their parent section in the EPUB TOC yet, unlike the PDF outline, which does include them — a separate, smaller enhancement, not part of this fix. | B3 |

**Finding discovered while validating B1, fixed separately (`114f6b7`)**:
generalizing the Contents trigger to "first outlined section" made a
previously-unreachable code path reachable — a document whose very
first section is also the one that triggers Contents (no front matter
in between, e.g. a technical document with no Prologue) hit two
consecutive `#pagebreak()` calls with nothing rendered between them
(the title page's own trailing pagebreak, immediately followed by
`_render_contents()`'s own leading pagebreak). That produced a
genuinely empty page with no enclosing page-styling function active,
which Typst rendered at its own built-in default page size rather
than the theme's — surfacing as an anomalous A4 page inside an
otherwise-A5 (classic theme) or otherwise-A4 (technical theme,
harmless there since it already matched) document. Fixed by routing
`_render_contents()`'s pagebreak through the same `_page_break()`
method every other section already uses, so the existing
`_first_page` suppression applies here too. Confirmed pre-existing
(not introduced by B1's diff) but only reachable once B1 shipped;
confirmed unrelated to theme selection (reproduced with classic theme
alone, no technical-theme involvement). Verified byte-identical book
output before/after, both themes uniform page size after.

**Note — read before touching B2**: both B1 and B2 are
**deliberate stopgaps**, not final architecture. Once Phase D's
interpretation layer exists, "where does main matter begin" and
"does this document get a cover" should become convention-profile
properties the renderer reads generically, not renderer `if`-branches.
Label B2 as a stopgap in its own commit so it isn't mistaken for
permanent design later.

---

## Phase C — Automatic theme selection

**Goal**: `python run.py <book>` selects the correct theme
automatically from `metadata.type`, with no manual theme-path edits.

**Status**: Shipped (C1 + C2)

| Task | Status | Description | Depends on |
|---|---|---|---|
| C1 | **Shipped** | Replaced the hardcoded `DEFAULT_THEME_IMPORT` in `renderer/typst.py` with `THEME_IMPORT_BY_TYPE`, a type→theme lookup, defaulting to classic for `book`/omitted/unrecognized. | Phase B |
| C2 | **Shipped** | Decided and implemented the three open questions this exposed — see Decision Log items 1–3. | — |

**Verified**: `python run.py ride` (RideTogether, `type: technical-document`)
now generates and compiles via the technical theme automatically, with
zero manual override — uniform A4 throughout, no orphan pages, cover
correctly present/absent per B2's rule. Book manuscript output
(`examples/sample-manuscript.md`) confirmed byte-identical before/after.

---

## Phase D — Generic document model migration

**Goal**: new document types stop requiring parser changes. Structure
comes from a shared model; only interpretation (per type) and
presentation (per theme) differ.

**Status**: In progress (D0 + D1 + D2 shipped; D3 not started)

**Design artifact**: `docs/DOCUMENT_MODEL_DESIGN.md` — validates the
proposed flat block-stream model against every current book rule and
every current technical-document rule. Found one genuine
simplification (subsections no longer need a special parser case)
and one piece of concrete supporting evidence (renderer/epub.py still
hardcodes `SectionKind.PROLOGUE` for its own contents-index logic,
never having received VP-005/B1's "first outlined section" fix —
independent, present-tense evidence of exactly the kind of
per-renderer drift a shared interpretation layer prevents).

**Scope note**: this phase is designed to comfortably support **books,
technical documents, white papers, tutorials, and API references**
(the last with caveats — see Decision Log). **Documentation websites
and notebooks are explicitly out of scope for this phase** — they
imply a different output paradigm (multi-file, navigable) or a
different input paradigm (executable cells) respectively, and are
tracked as separate future architectural questions, not solved as a
side effect of this migration.

| Task | Status | Description | Depends on |
|---|---|---|---|
| D0 | **Design note complete; two decisions pending sign-off** | Design-validation checkpoint — see `docs/DOCUMENT_MODEL_DESIGN.md`. Two open, D1-blocking decisions found: (1) interpretation's output shape — recommend "annotate in place" over reconstructing a grouped structure; (2) where interpretation lives as code — recommend a new, small, dedicated module rather than folding into `renderer/`. **D1 must not start until both are explicitly confirmed**, not assumed from the recommendation alone. | Phase C |
| D1 | **Shipped** | Introduced the generic Document Model: `Heading`/`Document` in `model.py` (raw, syntax-only, additive), plus a new, small, dedicated `interpretation.py` module (Gap 2, resolved) with `NodeKind`, `InterpretedNode`, `InterpretedDocument` (Gap 1's "annotate in place" shape, resolved), and minimal illustrative `interpret_book()`/`interpret_technical_document()` functions proving — with executable tests, not just prose — that the same model represents both current document types' structural rules from `docs/DOCUMENT_MODEL_DESIGN.md` sections 3–4. Not wired into parsing, rendering, `publish.py`, or `run.py`. Verified byte-identical output for both `type: book` (`examples/sample-manuscript.md`) and `type: technical-document` (the real RideTogether manuscript, via `run.py ride` end-to-end) before/after. 20 new tests; full suite 155/155. | D0 |
| D2 | **Shipped** | Built `parser/document_model.py`, a second, fully independent parser producing a `Document` from Markdown — headings (any level 1–6), paragraphs, `:::verse:::` blocks, with no Part/Chapter/Scene/`SectionKind` concept anywhere in it (structurally verified, not just by inspection). Validated against the real RideTogether manuscript (462 blocks) parsed and interpreted end-to-end via D1's `interpret_technical_document()`. Round-trip tests prove the parser and D1's interpretation functions work together correctly, not just independently. Zero existing tracked files modified — `parser/structure.py`, `renderer/`, `publish.py`, `run.py` untouched, so book/technical-document pipelines are unaffected by construction, not just by diff. 16 new tests; full suite 171/171. Not wired into `publish.py`/`run.py` — still unreachable, per D3's scope. | D1 |
| D3 | Not started | Wire dispatch so `type: technical-document` (only, initially) routes through the new parser; `type: book` (including omitted) is unaffected. | D2 |
| D4 | Not started | Validate against 2–3 real manuscripts, **including at least one that is structurally different from RideTogether** (table-heavy, unusually deep, etc.) — not just another similarly-shaped prose document. | D3 |
| D5 | Not started | *(Explicitly optional — revisit with evidence, not a foregone next step.)* Decide whether to migrate `book` onto the generic model too, retiring `Part`/`Chapter`/`Scene` as dataclasses. Only worth evaluating once D1–D4 have proven themselves against real content. | D4 (+ a fixed revisit window — see Decision Log) |

---

## Decision Log

Decisions that need to be made explicitly, on purpose, rather than
falling out as accidents of whatever gets built first. Update this
table as each is resolved — record the decision and the date, don't
delete the row.

| # | Decision needed | Status | Resolution |
|---|---|---|---|
| 1 | Is `metadata.type` an open string forever, or a validated/closed set? Confirmed today it accepts any string silently — no validation exists. | **Resolved** | Closed set: `book`, `technical-document` (`SUPPORTED_DOCUMENT_TYPES` in `model.py`). Unrecognized values now raise `FrontMatterError` at parse time, identifying the bad value and the supported types. Omitted `type` still defaults to `book`. |
| 2 | Is a cover image mandatory for technical documents? `run.py`/`books.yaml` currently assume yes for all types. | **Resolved** | Cover is required only for `type: book`. `books.yaml`'s `cover:` key is now optional; `run.py` reads the manuscript's declared type before deciding whether to require/stage it. Consistent with VP-006/B2, which already makes cover *rendering* book-only. **Follow-up found and fixed**: `renderer/epub.py`'s `_Renderer.__init__` fell back to `DEFAULT_COVER` (a single, static, repo-committed asset shared by every book) whenever `cover_path=None` was passed — meaning a technical-document's EPUB silently reused whatever image happened to be sitting at that shared path from an unrelated book's previous publication run. `cover_path=None` now always means "no cover," full stop; `DEFAULT_COVER` removed. |
| 3 | Formalize or retire the dead `Metadata.paper` field now that `type` drives page size. | **Resolved** | Retired outright — field removed from `Metadata`, extraction removed from `parser/reader.py`, and the now-meaningless key removed from `examples/sample-manuscript.md`. A leftover `paper:` key in an older manuscript is silently ignored (unknown YAML key), not an error. |
| 4 | Does metadata schema validation become type-aware (e.g. technical-document requires an `identifier`), or stay permissively open forever? | Open | — |
| 5 | What error classes does the parser own vs. the interpretation layer, in writing, before more convention profiles make this expensive to untangle? | Open | — |
| 6 | Is a lightweight (type, format) → renderer/theme registry worth introducing alongside Phase C's dispatch, before renderer files grow further? | Open | — |
| 7 | Does every document type owe the same "must render identically forever" guarantee that published, ISBN-registered books do, or is that guarantee specific to book until other types accumulate real published content? | Open | — |
| 8 | Fixed revisit window for D5 (book unification) — decide within how long of D4 landing, so dual-model debt doesn't linger indefinitely by default. | Open | — |

---

## Architectural principles this plan must honor

Pulled from `docs/LEARNINGS.md`, restated here as constraints on every
phase above — if a task in this plan would violate one of these, stop
and revisit the task, don't proceed and hope it's fine:

- **Lesson 003 / 005 / 006**: the manuscript stays simple and
  human-readable; conventions apply automatically; authors are never
  expected to understand the rendering engine.
- **Lesson 004**: metadata describes *what* the document is, never
  *how* it's rendered.
- **Lesson 007**: parser understands syntax; the publishing engine
  (interpretation layer) interprets the document; the renderer
  determines presentation. Three layers, not two — this is the
  principle Phase D exists to actually implement.
- **Lesson 008**: one document model, shared by every publication
  type — differences are in interpretation and presentation, not
  fundamental structure.
- **Lesson 009**: themes control presentation only, never document
  structure. Changing a theme must never require a manuscript change.
- **Lesson 011**: one manuscript, multiple output formats via
  different renderers — not different authoring workflows per format.

---

## Success Criteria

How to tell, objectively, whether this migration is working — not
"the docs feel complete," but checkable outcomes:

- **Parser**: zero book-specific concepts outside a convention
  profile. Adding document type N+1 requires zero parser changes.
  Structural errors are caught before render time. Zero
  `if metadata.type ==` branches in parser code.
- **Renderer**: adding a new document *type* requires zero renderer
  changes (only a new convention profile + theme). Adding a new
  *output format* requires one new renderer that works across all
  existing types. Zero direct `metadata.type` string comparisons in
  renderer code.
- **Extensibility**: a new type touches exactly one convention
  profile, one theme, one example manuscript — nothing else.
  Time-to-add-a-type trends down, not flat or up, as more types ship.
- **Coupling/cohesion**: `metadata.type` is read in exactly one
  dispatch point. Book-specific code is fully contained in its
  convention profile. Themes contain zero structural decisions.
- **Maintainability**: a reusable "manuscript + type → expected
  structure" test harness exists, not per-type one-off tests.
  Hard-won implementation gotchas get written down as they're found.
- **Onboarding**: a new contributor, from the docs alone, can name
  which of the three layers owns any given decision. "Where do I add
  a new document type" has one canonical documented answer.

---

## Revision history

| Date | Change |
|---|---|
| Initial draft | Phases A–D defined following the parser architecture review and the "generic model / migration strategy" architectural review. D1 revised from a recursive `Node` tree to a flat block-stream model; D0 (design-validation checkpoint) added; B1/B2 explicitly labeled as stopgaps; documentation websites and notebooks descoped from Phase D; Decision Log items 1, 4, 6, 7, 8 added. |
