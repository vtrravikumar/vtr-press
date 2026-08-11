# Document Model Design — Phase D, Task D0

## Status: Design validation only. No production code changes.

This note is the D0 deliverable (`VP-009`, `docs/MIGRATIONPLAN.md` /
`docs/ENGINEERING_PLAN.md`): validate a proposed generic Document
Model against real book and technical-document structural rules,
*before* any dataclasses, parser, or renderer code is written for
Phase D. Per the Engineering Plan's own words, this is the
highest-leverage step in the whole migration — getting it wrong here
is what would let book-shaped assumptions leak back into the new
model one layer removed, the same way they leaked into today's
parser in the first place.

**This note does not implement anything.** D1 (adding the model as
new code) is explicitly **blocked** until the two open decisions in
§6 are resolved — see the constraints in this document's own charge.

---

## 1. Proposed model shape: flat, ordered block stream

No recursive tree. No pre-built `Part`/`Chapter`/`Scene` nesting.
Structure comes from **document order plus heading level**, exactly
the way Markdown, Pandoc's own AST, and DocBook already represent it
— this isn't a novel design, it's converging on a well-trodden shape
for exactly this class of problem.

```
DocumentBlock = Heading | Paragraph | Verse | ...(future: Table, Image, CodeBlock)

Heading(level: int, title: str)
Paragraph(children: list[Inline])      # reused from model.py, unchanged
Verse(lines: list[str])                # reused from model.py, unchanged

Document(metadata: Metadata, blocks: list[DocumentBlock])
```

A few deliberate choices, each checked against current behavior in
§§3–4:

- **`Heading` has no `kind` field.** It records only what the
  manuscript's Markdown syntax actually says: a level and a title.
  Whether a given heading *means* Part, Chapter, Section, Subsection,
  Copyright, or something else entirely is not a parsing fact — it's
  a convention, and conventions vary by `metadata.type`. Baking `kind`
  into the parser's own output would smuggle interpretation back into
  the parser, which is exactly the coupling this migration exists to
  remove.
- **The top-level `# Title` heading is *not* special-cased away by
  the parser.** Today's parser silently discards `# Title` lines
  (title comes from front matter). Under this model, a `# ` line
  becomes an ordinary `Heading(level=1, title=...)` like any other —
  "ignore the first level-1 heading, title comes from metadata"
  becomes a *book-type convention* applied by interpretation, not a
  parser special case. This is a small but real simplification: the
  parser gets more mechanical, not less.
- **`:::verse:::` fencing stays a parser concern.** Recognizing a
  fenced verse block is about Markdown *syntax* shape, not document
  semantics — it doesn't vary by type, so it belongs with blank-line
  and heading recognition, not with interpretation.
- **`Metadata` is unchanged**, reused as-is, sitting outside the flat
  block list exactly as it does on `Book` today.

This directly satisfies `SPECIFICATION.md`'s "these document types
will reuse the same manuscript format" and `PUBLISHING_PRINCIPLES.md`'s
"a manuscript should be written once" — nothing about the manuscript
syntax changes; only how it's *interpreted* differs by type.

---

## 2. Layer ownership

| Decision | Owned by |
|---|---|
| Is this line blank / a heading / a verse fence / prose? | **Parser** |
| What level and title does this heading have? | **Parser** |
| Is this heading a Part, Chapter, Section, Subsection, Copyright, Appendix, …? | **Interpretation** |
| Does this heading participate in the outline (`outlined`)? | **Interpretation** |
| Where does Contents/main-matter begin? | **Interpretation** |
| Does this document type conventionally want a cover? | **Interpretation** (type-level fact) |
| Does *this render pass* actually emit a cover? | **Renderer** (type-level fact **+** `RenderOptions.print_mode`, which is a render-time concern interpretation has no business deciding) |
| Is "Chapter without a Part" valid for this type? | **Interpretation** (structural validation, type-specific) |
| What does a numbered heading look like on the page? | **Renderer / Theme** |
| Page size, typography, margins | **Theme** |

**A terminology note, because it matters for §6's open questions.**
`PUBLISHING_PRINCIPLES.md`'s Separation of Responsibilities lists six
components — Manuscript, Parser, Document Model, Renderer, Theme,
Output — and `ARCHITECTURE.md` attributes "document conventions" to
**Theme**, not to any separately named "interpretation" component.
Neither document names an interpretation layer as a distinct,
first-class component. The three-way split above (parser /
interpretation / renderer+theme) is the shape this migration's own
prior architecture review recommended, and it's what this ticket's
own task description asks for explicitly — but it is not yet a
literal commitment in the frozen docs. This is flagged as Gap 2 in
§6: where interpretation *lives* as code needs an explicit decision,
not an assumption.

---

## 3. Book rules, walked through against the model

Using real syntax exactly as it appears in `examples/sample-manuscript.md`
and as implemented in the current `parser/structure.py` / `renderer/typst.py`.

**Part → Chapter → Scene.**
```
## Part I - Getting Started
### Chapter 1 - Welcome
#### Opening
Body text.
```
Flat stream: `Heading(2, "Part I...")`, `Heading(3, "Chapter 1...")`,
`Heading(4, "Opening")`, `Paragraph(...)`. Book interpretation: a
level-2 heading whose title matches `/^part\s/i` → `kind=PART`
(exact same regex-equivalent check `parser/structure.py` already does
via `key.startswith("part ")`); the level-3 heading immediately
following, before the next level-2 heading, → `kind=CHAPTER`,
associated with that Part *by position in the stream*, not by a
nested field; level-4 under that → `kind=SCENE`. **Clean fit** — level
maps directly to the existing depth convention.

**Scene requires Chapter (validation).**
Today: `_ensure_scene()` raises if `current_chapter is None`.
Under the model: a level-4 `Heading` is only valid, for `type: book`,
if the nearest preceding level-3 heading (with no intervening
level-2) was itself classified `CHAPTER`. This is exactly the kind of
type-specific structural rule interpretation must own — it requires
the same stateful, ordered walk `parser/structure.py` already
performs, just relocated and made conditional on `metadata.type`
rather than hardcoded. **Clean fit**, same shape of logic, different
owner.

**Copyright / Dedication / Thirukkural / Back Cover / front matter.**
Today: `SECTION_MAP` (a fixed title → `SectionKind` lookup, lowercase
exact match) lives in `parser/structure.py`. Under the model:
`Heading(2, "Copyright")` → book interpretation checks the *same*
lookup table, assigns `kind=COPYRIGHT`, `outlined=False` — matching
today's `outlined = section.kind not in {COPYRIGHT, DEDICATION,
THIRUKKURAL}` computation exactly. `SECTION_MAP` itself simply moves
from a parser-level constant to a book-interpretation-level constant.
**Clean fit**, direct 1:1 relocation.

**Contents / main-matter trigger.**
Today (post-VP-005): the first section with `outlined=True` triggers
both Contents insertion and main-matter numbering start —
`renderer/typst.py`'s `_render_section` computes this *during
rendering*. Under the model: interpretation, having already tagged
every heading with `kind`/`outlined`, can compute "the first
top-level heading with `outlined=True`" once, up front, and mark it
with a single `starts_main_matter` flag the renderer just reads.
**Clean fit — and an improvement**, not just a lateral move: see the
concrete evidence in the box below.

> **Found while researching this note, not hypothetical:**
> `renderer/epub.py`'s `_render_section` *still* hardcodes
> `section.kind == SectionKind.PROLOGUE` for its own contents-index
> logic (line ~441) — it never received VP-005's "first outlined
> section" generalization, because that fix only touched
> `renderer/typst.py`. A technical document with no Prologue gets
> correct Typst/PDF Contents behavior today, but the *EPUB* build of
> the same document still silently never sets `_contents_index`. This
> is exactly the class of bug centralizing this logic in one
> interpretation pass — computed once, consumed identically by every
> renderer — makes structurally harder to reintroduce. Not a Phase D
> blocker (book/technical-document stay on the current parallel path
> during Phase D), but worth fixing on its own regardless, and cited
> here as concrete, present-tense evidence for why this design
> direction is worth the migration cost.

**Cover behavior.**
Today: `render()` emits a cover only when `not print_mode and
metadata.type == "book"`. Under the model, this is a **two-part**
decision, not a single interpretation output: interpretation states
the type-level convention ("book conventionally has a cover" — a fact
about the *type*), and the renderer combines that with
`RenderOptions.print_mode` (a render-time publishing variant,
orthogonal to what kind of document this is) to decide whether *this*
render pass actually emits one. Interpretation should not need to
know about `print_mode` at all. **Clean fit**, with the ownership
split made explicit rather than collapsed into one flag.

---

## 4. Technical-document rules, walked through against the model

**Numbered sections.**
Today: purely a **theme** concern — `themes/technical/headings.typ`'s
`show heading.where(level: 2, outlined: true): set heading(numbering: ...)`,
driven by the `outlined` flag the renderer already threads through
`_render_heading(level, title, outlined=...)`. Under the model:
interpretation assigns `kind=SECTION` + `outlined=True` to top-level
technical-document headings (mirroring book's `PROLOGUE`/`OTHER` +
`outlined` assignment above); the theme still does the actual number
*rendering*. Interpretation decides *which* headings are numbered;
presentation decides what the number *looks like*. **Clean fit, no
change needed** to the theme layer at all.

**Subsections.**
Today: the `Subheading(title, level)` block exists specifically
because the parser has to special-case `###`/`####` depending on
whether `current_part` is set. Under the model, this **disappears as
a special case entirely** — a `###` line is just `Heading(level=3,
...)`, indistinguishable at parse time from a Chapter heading. The
parser no longer needs to know whether level-3 means "Chapter" (book)
or "Subsection" (technical-document); that branching moves entirely
into interpretation, conditioned on `metadata.type` and context (is
the enclosing level-2 heading a Part?). **This is a genuine
simplification of the parser**, not just an equivalent restatement —
worth calling out as validating evidence for the whole model, not
just a "fits fine" result.

**Appendices.**
Today: no special handling at all — `## Appendix A - Glossary` falls
through `SECTION_MAP` to `SectionKind.OTHER`, renders as an ordinary
numbered section. Under the model: same story, unchanged — technical
interpretation's convention table can optionally recognize
"appendix"-prefixed titles as a distinct `kind=APPENDIX` later, or
leave it generic exactly as today. **Clean fit, confirms
"appendix-ready" needs no new abstraction**, consistent with the
architecture review's original finding.

**First outlined section / TOC / page numbering.**
Same algorithm as book's, run over a differently-kind-tagged stream —
"first top-level heading with `outlined=True`" is type-agnostic
*machinery*, even though *which* headings end up `outlined=True` is
type-specific. This is the strongest piece of evidence in this note
that the split is real: one algorithm, two conventions, and (per the
EPUB/PROLOGUE finding above) currently two *inconsistent*
implementations that a shared interpretation pass would naturally
prevent.

**No required cover.**
Same two-part split as book: interpretation states technical-document
doesn't conventionally want a cover; the renderer already doesn't
need `print_mode` to further gate this, since it's already off by
convention. **Clean fit.**

---

## 5. Fit for future types, without parser changes

Per the Migration Plan's explicit scope: white-paper, tutorial, and
(with caveats) API reference. Documentation websites and notebooks
remain **explicitly out of scope for Phase D** — different output
paradigm (multi-file, navigable) and different input paradigm
(executable cells) respectively; this note doesn't re-argue that,
only restates it so this design isn't quietly bent to accommodate
them.

- **White paper** — structurally close to technical-document
  (numbered or unnumbered sections, no Part/Chapter/Scene). Needs its
  own interpretation convention table and its own theme; zero parser
  changes. Cover convention may differ from both book and
  technical-document (e.g. required-but-different-style) — that's a
  convention-table detail, not a model-shape question.
- **Tutorial** — likely wants "Step 1 / Step 2" style numbering rather
  than generic section numbers. Still purely an interpretation
  (which headings get tagged as steps) + theme (how a step number
  displays) concern. Zero parser changes.
- **API reference (caveat, restated from the prior architecture
  review, not re-litigated here)** — the flat block stream mechanically
  represents it fine (headings + paragraphs per endpoint), but real
  API references are usually generated from a machine-readable spec
  (OpenAPI/Swagger), not hand-authored prose. That's a caveat about
  the *authoring source*, not a limitation of this model — a
  spec-to-Markdown conversion step, if ever built, would sit entirely
  outside VTR Press and simply hand the parser ordinary Markdown like
  any other manuscript.

In all three cases, the pattern is the same and is the entire point
of this migration: a new type is a new interpretation convention
table plus a new theme. The parser does not change.

---

## 6. Gaps and open decisions — must be resolved before D1

Two of these are genuine blockers, not just notes for later; the rest
are confirmable non-gaps worth recording so they aren't re-litigated.

### Gap 1 — Interpretation's output shape (blocks D1)

Two candidate shapes, and this note has a recommendation but not a
decision:

- **(A) Annotate in place.** Interpretation walks the raw flat stream
  and produces a second, parallel flat structure — e.g.
  `InterpretedNode(block: DocumentBlock, kind: NodeKind | None,
  outlined: bool)` — one entry per raw block, in the same order. The
  renderer walks *this*, never the raw stream directly.
- **(B) Reconstruct a grouped structure.** Interpretation builds
  something Section/Part-shaped as its output, and the renderer's
  code stays closer to today's shape.

**Recommendation: (A).** The task's own constraint is explicit — "no
recursive tree, no pre-built nesting" — and (B) would quietly
reintroduce a tree one step later, undermining the reason to migrate
at all even though it keeps D1's letter. (A) also keeps "parser
output" and "interpretation output" as two distinct, clearly-owned
types rather than overloading the parser's own `Heading` dataclass
with type-specific fields. This needs explicit confirmation — not an
assumption — before D1 defines any dataclasses, since it determines
whether D1 needs one flat type or two.

### Gap 2 — Where interpretation lives as code (blocks D1)

Per §2's terminology note: `ARCHITECTURE.md`/`PUBLISHING_PRINCIPLES.md`
don't name a separate interpretation component; "document conventions"
is attributed to Theme. Does interpretation become its own new module
(e.g. `interpretation/` or `conventions/`), or does it live as a
clearly-bounded function/class inside `renderer/`, keeping the
six-component list technically accurate? Either is workable, but this
is a real module-boundary decision, not a detail to improvise during
D1 implementation. **Recommendation: a new, small, dedicated module**
— folding type-conditional logic into `renderer/` risks exactly the
kind of renderer-owned `if metadata.type ==` branching this migration
exists to remove (see B2/C1, which currently do have direct type
checks in the renderer as a deliberate, labeled stopgap) — but this
is a naming/placement call worth a second opinion before committing,
not something this note should decide unilaterally.

### Confirmable non-gaps (recorded, not blocking)

- **Does interpretation need a book profile during Phase D**, given
  book stays on the old parser/parallel path per the Migration Plan?
  This note's §3 walkthrough already validates one on paper.
  Recommendation: write and test a book interpretation profile
  alongside the technical-document one in D1–D2 (cheap, and it's the
  strongest ongoing proof the model generalizes), but do **not** wire
  it into production parsing — that stays D5's decision entirely,
  unaffected by whether the profile exists for testing.
- **Extensibility to Table/Image/CodeBlock** — `ARCHITECTURE.md`
  already lists these as "typical" Document Model elements, and none
  exist in the codebase today. The flat block-stream shape
  accommodates new block *types* by construction (add a new variant
  to the `DocumentBlock` union) — this is not a gap, just confirmed
  headroom, restated here because the architecture doc raises it and
  a reviewer would reasonably ask.
- **Validation-timing shift** — today's parser raises structural
  errors (`"Chapter found outside a Part"`) immediately, mid-parse.
  Under this model, that check moves to interpretation, which runs
  immediately after parsing completes, before any rendering — so the
  practical "fails before publishing anything" guarantee is
  unchanged, even though the error now originates from a different
  module. Not a regression in practice; worth stating as an explicit
  requirement for D2's implementation (interpretation errors must
  stay at least as precise as today's) rather than an unstated
  assumption.
- **EPUB/Typst PROLOGUE divergence** (§3 box) — real, present-tense,
  found during this note's research. Not a Phase D blocker; flagged
  as independently worth fixing, and as supporting evidence for why
  this migration is worth the cost.

---

## Summary for sign-off

The proposed flat block-stream model holds up against every current
book rule and every current technical-document rule, with one
genuine simplification found (subsections no longer need a special
parser case) and one piece of concrete evidence found in favor of the
design (the EPUB/Typst PROLOGUE divergence). Three future types were
checked against it without requiring parser changes, consistent with
`PUBLISHING_PRINCIPLES.md`'s Extensibility principle.

**D1 is blocked** pending explicit resolution of Gap 1 (interpretation
output shape — recommend annotate-in-place) and Gap 2 (where
interpretation lives as code — recommend a new, small, dedicated
module). Everything else in §6 is recorded, not blocking.

No `type: book` behavior changes as a result of this note — nothing
in this document has been implemented.
