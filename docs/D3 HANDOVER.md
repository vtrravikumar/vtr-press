> **Historical handover — superseded by v0.9.1.**
>
> This document records the pre-implementation D3 state. D3 was subsequently
> completed and released as part of v0.9.1. The analysis below is retained as
> engineering history and should not be read as the current implementation
> status.
>
# VTR Press — D3 Engineering Handover

**Prepared from repository state at commit `0e1d2fe`** ("Bug: Prologue
rendered unoutlined print-book front matter"), branch `main`,
`github.com/vtrravikumar/vtr-press`. This document makes no code
changes and creates no commits — it is a snapshot and analysis only.

---

## 1. D3 Objective

**What D3 accomplishes**: wires `type: technical-document` manuscripts
to route through the new, generic Document Model pipeline (parser +
interpretation, built in D1/D2) instead of the existing
book-shaped parser (`parser/structure.py`). `type: book` (including
omitted `type`) must continue through the existing, unmodified path
with **zero behavioral change**.

**User-facing behavior once D3 is complete**: running the publishing
pipeline (`run.py <book>` or `publish_all()`) against a
`technical-document` manuscript produces output via the new pipeline,
and that output is at least as correct as what the *current*
technical-document path already produces (technical-document already
works today, via `parser/structure.py` + its `Subheading` block type
— D3 does not "add" technical-document support, it **replaces the
plumbing underneath already-working support**). A `book` manuscript's
output — PDF and EPUB — must be byte-identical to pre-D3 output.

**What D3 is explicitly not**: it is not the point where `book` gains
any new behavior. It is not full validation (that's D4). It is not
where document types beyond `book`/`technical-document` get added.

---

## 2. Requirements / Acceptance Criteria

Quoted from `docs/MIGRATIONPLAN.md`, Phase D task table:

> **D3** — Wire dispatch so `type: technical-document` (only,
> initially) routes through the new parser; `type: book` (including
> omitted) is unaffected.

Quoted from `docs/ENGINEERING_PLAN.md`, Task D3 (ticket `VP-012`):

> **Objective**: Route `type: technical-document` manuscripts through
> the new parallel parser; `type: book` (including omitted) continues
> through the existing parser, completely unaffected.
>
> **Definition of done**: RideTogether publishes via the new Document
> Model path; both book manuscripts are unaffected; the dispatch point
> has explicit test coverage for all three `type` values, not just the
> new one.
>
> **Risks**: Medium-High — the highest-risk task in Phase D, because
> it's the first one with a live consequence. (1) A subtle bug in the
> dispatch condition accidentally routing a `book`-typed manuscript
> through the new path — guard explicitly with a byte-identical
> regression check, not "looks fine." (2) Declaring this done based on
> RideTogether alone, without D4's broader validation — resist that;
> D3's DoD is "reachable and correct for RideTogether," not "proven."

**Concrete acceptance conditions**:

1. A `technical-document` manuscript, published through the normal
   entry points (`publish_all()`, and `run.py <name>` for a book
   configured in `books.yaml`), produces output via the new
   parser (`parser/document_model.py`) + interpretation
   (`interpretation.py`) pipeline — verifiably, not just "it still
   compiles."
2. A `book` manuscript (including one with **no** `type` field at
   all) produces **byte-identical** Typst source and EPUB content
   (excluding the EPUB OPF's `dcterms:modified` timestamp, which
   always differs run-to-run regardless of code changes) to pre-D3
   output.
3. Dispatch logic has explicit test coverage for all three cases:
   `book`, omitted, `technical-document`.
4. Full existing test suite remains green (176 tests as of this
   handover — see §7).
5. The real RideTogether manuscript publishes successfully through
   the new path end-to-end (PDF-source generation and EPUB
   generation both).
6. Unknown-type hard-error behavior (C2 decision 1, already
   implemented in `parser/reader.py`) continues to work — dispatch
   must not bypass or duplicate that validation.

---

## 3. Current Status

**Implemented (D1, D2 — both shipped, both verified on `main`)**:

- `model.py`: `Heading(Block)` (level + title, no semantics) and
  `Document(metadata, blocks)` (flat root type). Additive; `Book` and
  its existing tree (`Part`/`Chapter`/`Scene`/`Section`/`Subheading`)
  are completely untouched.
- `interpretation.py` (new top-level module): `NodeKind` enum,
  `InterpretedNode(block, kind, outlined)`,
  `InterpretedDocument(metadata, nodes)` with a
  `first_outlined_node()` method, and two **minimal, illustrative**
  functions — `interpret_book(document) -> InterpretedDocument` and
  `interpret_technical_document(document) -> InterpretedDocument`.
- `parser/document_model.py` (new module): `parse_document(metadata,
  body) -> Document`. A second, fully independent parser — headings
  any level 1–6, paragraphs, `:::verse:::` blocks, zero references to
  `Part`/`Chapter`/`Scene`/`Section`/`SectionKind` (verified by a
  dedicated test, not just code review).

**Not implemented (D3's actual job)**:

- **Nothing calls `parse_document()`, `interpret_book()`, or
  `interpret_technical_document()` from production code.** Confirmed
  by grep: zero matches for `document_model`, `interpretation`,
  `InterpretedNode`, or `NodeKind` in `publish.py`, `run.py`,
  `renderer/typst.py`, or `renderer/epub.py`.
- No dispatch point exists anywhere that reads `metadata.type` to
  decide *which parser* to use. (A dispatch point reading
  `metadata.type` to decide *which theme* to use already exists —
  see `renderer/typst.py`'s `THEME_IMPORT_BY_TYPE` — but that's C1's
  theme-selection work, unrelated to parser dispatch.)
- **No renderer code path exists that can consume an
  `InterpretedDocument` at all.** `render_typst()` and `render_epub()`
  are both hard-typed to accept a `Book` (see §4 for why this is the
  central open question of D3).

**Partial/incomplete work**: none. D1 and D2 are cleanly finished and
isolated — there is no half-started D3 code to find or clean up.

**Important context discovered during this handover, not part of D3
itself**: two commits landed on `main` *after* D2 (`1c9e321`,
`0e1d2fe`, both dated after D2's merge) adding a "print-book"
pagination feature to the **existing** book renderer path — recto
(right-hand) page starts for Parts and the first Chapter after each
Part, unnumbered front matter through Prologue, documented in
`docs/SPECIFICATION.md` under a new "Print Book PDF" section. This is
entirely independent of Phase D and does not touch `model.py`,
`interpretation.py`, or `parser/document_model.py` (confirmed by
diff). **It matters for D3 only in this sense**: the book renderer
(`renderer/typst.py`) is not a frozen, stable target — it has grown
new conditional logic (`self._print_book`, `_recto_page_break()`)
since D2's regression baseline was established. Anyone doing D3's
"book output must be byte-identical" check needs to diff against
**current** `main`, not against a D2-era snapshot.

---

## 4. Architecture and Design Decisions

**Intended architecture (from `docs/DOCUMENT_MODEL_DESIGN.md`, the D0
design note)**:

```
Markdown text
     │
     ▼
parser/document_model.py::parse_document()   →  Document (flat, raw)
     │
     ▼
interpretation.py::interpret_book() /
  interpret_technical_document()             →  InterpretedDocument (flat, annotated)
     │
     ▼
renderer/typst.py, renderer/epub.py          →  Typst source / EPUB bytes
  (NOT YET BUILT: a path that consumes InterpretedDocument)
```

**Design decisions already made and settled** (do not reopen):

1. Flat, ordered block stream — no recursive tree, no rebuilding
   Part→Chapter→Scene nesting. (D0 decision 1, `model.py`.)
2. The parser describes syntax only, never semantics. (D0 decision 2,
   `parser/document_model.py` — confirmed zero book-specific
   vocabulary in that module.)
3. Interpretation is a separate responsibility living in its own
   small module, not inside either renderer. (D0 decision 3,
   `interpretation.py` — this was "Gap 2" in the original design note
   and is now resolved/built, not still open.)
4. Interpretation annotates the parsed stream in place — an
   `InterpretedNode` wraps each raw block with `kind` and `outlined`,
   rather than reconstructing a grouped/nested structure. (D0
   decision 4, was "Gap 1," now resolved/built.)
5. Both Typst and EPUB should ultimately consume the *same*
   interpreted Document Model. (D0 decision 5 — **this is the
   decision D3 has to actually make real**, and it is not yet
   satisfied by any code.)
6. The model must represent both `book` and `technical-document`.
   (D0 decision 6 — validated on paper in
   `docs/DOCUMENT_MODEL_DESIGN.md` §§3–4, and validated with
   executable tests in D1/D2 via `interpret_book()`/
   `interpret_technical_document()` and round-trip tests against real
   parser output.)
7. `technical-document` is a reusable manuscript contract, not a
   RideTogether-specific convention. (D0 decision 7 — relevant to D3
   in that dispatch must key off `metadata.type ==
   "technical-document"` generically, not off any manuscript-specific
   heuristic.)

**Explicitly rejected / should NOT be used**:

- Reconstructing a Section/Part-like grouped structure as
  interpretation's output. This was "Approach B" in the D0 note and
  was rejected in favor of the flat "annotate in place" shape — see
  `docs/DOCUMENT_MODEL_DESIGN.md` §6, Gap 1.
- Folding interpretation logic into `renderer/typst.py` or
  `renderer/epub.py` directly (e.g., more `if metadata.type ==`
  branches inside the renderers, extending the existing pattern from
  B2/C1). This was explicitly rejected as Gap 2's resolution — those
  existing renderer-level type checks (B2's cover logic, C1's theme
  selection) are **labeled stopgaps**, not a precedent to extend.
- Migrating `book` onto the new model as part of D3. That's D5,
  explicitly optional, explicitly deferred, and explicitly not a
  foregone conclusion — see `docs/MIGRATIONPLAN.md` Decision Log item
  8 (still open) and D5's row in the phase table.
- Treating D1's `interpret_book()`/`interpret_technical_document()`
  as production-ready. Their own docstrings say so explicitly: "not
  the production D2/D3 interpretation layer... never called by
  anything in the real pipeline." D3 needs to decide whether to
  extend these functions to production quality or design new ones —
  see the open question below.

**The one genuinely unresolved architectural question — flagged, not
guessed at**:

`render_typst(book: Book, ...)` and `render_epub(book, cover_path)`
are both hard-typed to `Book`. There is currently **no way** to hand
either renderer an `InterpretedDocument`. D3 has to resolve this one
way or another, and the two paths differ significantly in size and in
how faithfully they honor D0 decision 5:

- **(A) Native consumption.** Write genuinely new code in both
  renderers that walks `InterpretedNode` lists directly and emits
  Typst/XHTML. This is what D0 decision 5 actually describes. It's
  more code, but it's the real target architecture, not a bridge.
- **(B) Adapter/bridge.** Convert an `InterpretedDocument` back into
  `Book`-shaped objects (synthesizing `Section` instances with
  `SectionKind` values from `NodeKind`) so the **existing** renderer
  code runs unchanged. Meaningfully smaller and faster to land, but
  it's throwaway code that has to be discarded later if/when native
  consumption is eventually built — and it means Typst/EPUB are
  *not* actually consuming the same interpreted model, they're
  consuming a reconstruction of the old model derived from it,
  which arguably doesn't satisfy decision 5 at all.

**This was not decided during D0, D1, or D2.** Whoever picks up D3
needs to make this call explicitly and record it in
`docs/MIGRATIONPLAN.md`'s Decision Log, the same way Gap 1/Gap 2 were
recorded and resolved before D1 began. Proceeding without deciding
this is very likely to produce inconsistent or throwaway work.

**Dependencies on D1/D2**: D3 depends on both being present exactly as
shipped — `Document`/`Heading` (D1, `model.py`),
`InterpretedDocument`/`NodeKind`/`interpret_*()` (D1,
`interpretation.py`), and `parse_document()` (D2,
`parser/document_model.py`). All three are confirmed present,
unmodified since their respective landings, and fully covered by
their own test suites (see §7).

---

## 5. Relevant Code

| File | Relevance |
|---|---|
| `model.py` | `Heading`, `Document` — D1's raw parser-output types. D3 doesn't need to modify this file, only import from it. |
| `interpretation.py` | `NodeKind`, `InterpretedNode`, `InterpretedDocument`, `interpret_book()`, `interpret_technical_document()`. D3 will likely need to **extend** `interpret_technical_document()` toward production quality (see §8's note on the level-1 heading misclassification) — decide whether that happens here or in new code. |
| `parser/document_model.py` | `parse_document(metadata, body) -> Document`. D3 calls this for `technical-document` manuscripts; does not need modification itself. |
| `parser/reader.py` | `read(path) -> (Metadata, str)` — already type-agnostic, already validates `type` against `SUPPORTED_DOCUMENT_TYPES` (C2 decision 1) and defaults omitted `type` to `"book"`. D3's dispatch reads `metadata.type` from this function's output; no change needed here. |
| `parser/structure.py` | The existing book parser (`parse_structure`). Must remain completely untouched by D3 — it's the "unaffected" side of the dispatch. |
| `publish.py` | **The dispatch chokepoint.** `read_book(path)` is the single function every public entry point (`publish`, `publish_epub`, `publish_all`) funnels through, and it unconditionally calls `parse_structure(metadata, body)` today. This is where D3's `if metadata.type == "technical-document": ... else: ...` branch almost certainly belongs — see `ENGINEERING_PLAN.md`'s own suggestion of "`parser/reader.py` or `publish.py`." |
| `renderer/typst.py` | `render(book: Book, ...) -> str` and `_Renderer.render(self, book: Book)`. Hard-typed to `Book` — this is where the Approach A vs. B decision (§4) has to be resolved. Also contains `THEME_IMPORT_BY_TYPE` (C1, theme dispatch — already type-aware, unrelated to parser dispatch but in the same file) and the new `_print_book` pagination logic (post-D2, unrelated to D3 but must not regress). |
| `renderer/epub.py` | `render(book: Book, cover_path=None) -> bytes`. Same hard-typing issue as Typst. Also contains the cover-required-only-for-book logic (C2 decision 2) and the Contents/nav-points logic (B3, B4 fixes) — all `Book`-shaped today, all need an equivalent for whatever D3 builds. |
| `run.py` | CLI entry point. Calls `publish_all()`; if the dispatch lands correctly in `publish.py`, `run.py` likely needs zero changes — worth confirming rather than assuming. |
| `books.yaml` | Configuration — the `ride` entry is the real technical-document manuscript's config (`type: technical-document`, no `cover:` key — see C2 decision 2). Also has a `genz` entry (another real book, added independently, unrelated to Phase D). |
| `tests/test_document_model.py` | D1's tests for `Heading`/`Document` — representability, ordering, level-neutrality. |
| `tests/test_interpretation.py` | D1's tests for `NodeKind`/`InterpretedNode`/`interpret_book()`/`interpret_technical_document()`. |
| `tests/test_document_model_parser.py` | D2's tests for `parse_document()`, including round-trips through D1's interpretation functions and a structural-isolation test confirming zero coupling to `parser/structure.py`. |
| `tests/test_integration.py` | Where D3's own new dispatch tests almost certainly belong — this file already tests `publish`/`publish_all`/`read_book` end-to-end. |
| `docs/DOCUMENT_MODEL_DESIGN.md` | The D0 design note. Sections 3–4 are the walkthrough of book and technical-document rules the interpretation functions are validated against. |
| `docs/MIGRATIONPLAN.md` | Phase D task table and Decision Log — update D3's row and add an entry for the Approach A/B decision once made. |
| `docs/SPECIFICATION.md` | Documents the print-book pagination convention (post-D2) and the two supported document types' conventions (A5/cover for book, A4/no-cover/numbered-sections for technical-document) — the correctness bar for whatever D3's technical-document rendering produces. |

**Templates/config**: `themes/classic/` and `themes/technical/` (Typst
theme packages) are unaffected by D3 regardless of which architecture
(A/B) is chosen — theme selection (C1) is already type-driven and
independent of parser/interpretation dispatch.

---

## 6. Git History

Commits directly relevant to D3, in order, with what each changed and
why it matters even where the connection isn't obvious:

| Commit | Summary | Relevance to D3 |
|---|---|---|
| `09d0579` | Add `type` metadata field (VP-001) | The field D3's dispatch reads. |
| `6d59d5a` | `Subheading` block + parser support | Proves technical-document *already renders* through the old pipeline today — this is the working baseline D3's new path has to match or exceed, not a green field. |
| `113f1e3`, `114f6b7` | VP-005/B1: Contents/main-matter trigger generalized to "first outlined section" | The exact algorithm D1's `InterpretedDocument.first_outlined_node()` reimplements generically. D3's renderer work needs to reproduce this behavior for technical-document, however Approach A/B shakes out. |
| `e41293c` | B2: cover required only for `type: book` | Precedent for a renderer-level `metadata.type` check — explicitly labeled a stopgap, not a pattern to extend in D3. |
| `c5e3cad` | C1: `THEME_IMPORT_BY_TYPE` dispatch | Proves a `metadata.type`-keyed dispatch dict pattern already exists and works in `renderer/typst.py` — a plausible model for D3's *parser* dispatch too, even though it solves a different problem (theme, not parser). |
| `908e5fd` | C2: three decisions (hard-error unknown type, cover optional, retire `Metadata.paper`) | The unknown-type hard error now lives in `parser/reader.py`, upstream of where D3's dispatch will sit — confirmed still correct and must not be duplicated or bypassed by new dispatch logic. |
| `cd6d133`, `087712b`, `f14bce2` | B3/B4: EPUB Contents/cover/TOC parity fixes | **Read these closely before starting D3.** Three separate, real bugs were found in `renderer/epub.py` by testing the *existing* pipeline against the real RideTogether manuscript, each one a case of "implemented for Typst, EPUB silently diverged." This pattern is highly likely to repeat during D3's renderer work — budget for it rather than being surprised by it. |
| `106d089` | **D1**: `Document`/`Heading`/`interpretation.py` | The model D3 wires in. |
| `ccab44e` | **D2**: `parser/document_model.py` | The parser D3 wires in. |
| `1c9e321`, `0e1d2fe` | Post-D2: print-book pagination feature | Unrelated to Phase D, but changes the shape of `renderer/typst.py`'s book path (`_print_book`, `_recto_page_break()`) after D2's regression baseline was taken. Re-diff against **current** `main`, not against `ccab44e`. |

No branches or prior D3 implementation attempts exist — `main` is the
only branch, and grep confirms zero production references to the new
D1/D2 code, so there is nothing partially built to discover, undo, or
reconcile.

---

## 7. Testing

**Existing tests covering D3's prerequisites** (all currently passing,
176 total as of this handover):

- `tests/test_document_model.py`, `tests/test_interpretation.py`,
  `tests/test_document_model_parser.py` — cover D1/D2, not D3 itself,
  but must stay green throughout.
- `tests/test_integration.py` — covers `publish`/`publish_all`/
  `read_book` today; this is where dispatch behavior needs new
  coverage.
- `tests/test_typst_renderer.py`, `tests/test_epub_renderer.py` — the
  existing renderer test suites; whichever Approach (A/B) is chosen,
  new tests analogous to these (but exercising the new path) will be
  needed for technical-document.

**Tests that should be added for D3**:

1. Dispatch correctness for all three `type` values (`book`, omitted,
   `technical-document`) — asserting *which* parser/pipeline actually
   ran, not just that output was produced. A reasonable technique:
   assert the resulting structure contains (or doesn't contain) a
   `Document`/`InterpretedDocument`-specific marker, or monkeypatch
   `parse_document`/`parse_structure` to confirm which was called.
2. Byte-identical book regression — diff `publish_all()` output for
   `examples/sample-manuscript.md` before/after, exactly as done for
   every prior ticket in this migration (B1, B2, C1, C2, D1, D2 all
   used this exact technique).
3. Byte-identical output for the *unknown-type hard error* — confirm
   dispatch doesn't accidentally swallow or duplicate C2 decision 1's
   validation.
4. Whatever renderer test suite results from the Approach A/B
   decision — new tests exercising technical-document through the
   *new* pipeline specifically, checking the same properties B1/B3/B4
   established for the old pipeline (Contents populated, correct
   page/nav structure, no cover, correct theme).

**Expected regression-test result**: full suite must stay green
throughout — 176 passing today, growing by however many new tests D3
adds, with **zero** existing test needing modification for `type:
book` behavior. If a book-related existing test needs to change to
make D3 pass, that is a signal something is wrong with the dispatch,
not a normal part of D3.

**Exact commands**:

```bash
# Baseline, before any change
git clone https://github.com/vtrravikumar/vtr-press.git
cd vtr-press
pip install -r requirements.txt --break-system-packages
pip install -r requirements-dev.txt --break-system-packages
python -m pytest tests/ -q
# Expect: 176 passed

# After D3 changes
python -m pytest tests/ -q
# Expect: 176 + N passed, 0 failed

# Byte-identical book regression check (pattern used throughout this migration)
python3 -c "
from publish import publish_all
before, _ = publish_all('examples/sample-manuscript.md')
open('/tmp/before.typ', 'w').write(before)
"
# (apply D3 changes)
python3 -c "
from publish import publish_all
after, _ = publish_all('examples/sample-manuscript.md')
open('/tmp/after.typ', 'w').write(after)
"
diff /tmp/before.typ /tmp/after.typ
# Expect: no output (exit code 0)
```

**Manual verification required**: the real RideTogether manuscript is
not present in this repository — it lives at
`../../Projects/RideTogether/docs/architecture/SolutionArchitecture.md`
relative to the repo root, per `books.yaml`'s `ride` entry, and must
be supplied/staged separately (it has been shared directly with the
previous implementer in prior sessions, not committed to this repo).
Running `python run.py ride` (and, since this environment may lack the
`typst` CLI binary, compiling the resulting `.typ` via the `typst`
PyPI package as a fallback, as done throughout this migration) is the
closest thing to a true end-to-end check and should be done before
calling D3 complete for RideTogether specifically. Full production
`typst compile` verification (not just Python-package compilation)
should also happen wherever the actual `typst` CLI is available.

---

## 8. Risks / Edge Cases

- **The Approach A/B question (§4) is the single biggest risk.**
  Starting to write renderer code before deciding this will likely
  produce work that has to be partially discarded. Decide and record
  it first.
- **EPUB lagging Typst is not a hypothetical risk — it has happened
  three times already** (B1→B3 for Contents trigger, the cover bug,
  the TOC bug). Plan D3's renderer work as Typst-then-EPUB explicitly,
  with its own verification pass for EPUB, not "should be the same."
- **D1's `interpret_technical_document()` is known-incomplete.**
  Confirmed directly against the real manuscript during D2: the `#
  Title` line (level-1 heading, correctly *captured* by the parser
  per D0's design) gets classified `SUBSECTION` by the current
  minimal interpretation function, which only special-cases level-2
  headings. This is not a D2 bug — the parser did its job correctly —
  but D3 will surface it as a real behavioral gap the moment
  technical-document actually renders through the new path. Decide
  whether to fix this in `interpretation.py` directly or design new
  interpretation code as part of D3.
- **`Metadata.paper` is retired (C2 decision 3) — don't reintroduce
  it** if any old reference or habit resurfaces while building
  renderer support for the new path.
- **Unknown-type hard error must not be bypassed.** `parser/reader.py`
  already raises `FrontMatterError` for unrecognized `type` values.
  Whatever dispatch D3 adds sits *downstream* of that check (by the
  time `metadata.type` is available for dispatch, `read()` has
  already validated it) — don't add a second, potentially
  inconsistent validation.
- **The post-D2 print-book feature (`_print_book`,
  `_recto_page_break()`) must not regress.** It's real, documented
  (`docs/SPECIFICATION.md`), tested, and entirely orthogonal to D3 —
  but it's new enough that it's easy to forget when reasoning about
  "the book path," since most of this migration's documentation
  predates it.
- **`books.yaml` now has a `genz` entry** (a third real book, added
  independently of this migration) — irrelevant to D3's logic, but
  worth knowing it exists so it isn't mistaken for migration-related
  work if encountered.
- **No `typst` CLI binary may be available** in whatever environment
  D3 is implemented in — the `typst` PyPI package (`import typst;
  typst.Compiler(...)`) was used as a substitute compiler throughout
  this migration when the CLI wasn't present, and produces equivalent
  output for verification purposes.
- **Backward compatibility scope is exactly two types.** `book` and
  `technical-document` are the closed set (C2 decision 1) — D3 should
  not need to anticipate white-paper, tutorial, or API-reference
  conventions; those are explicitly out of scope until a future type
  is actually added.

---

## 9. Recommended Implementation Order

1. **Decide Approach A vs. B (§4) explicitly**, and record the
   decision in `docs/MIGRATIONPLAN.md`'s Decision Log, the same way
   Gap 1/Gap 2 were recorded before D1. Do not start writing renderer
   code before this is settled.
2. **Add the dispatch point in `publish.py`'s `read_book()`** (or
   wherever the decision in step 1 implies it should live) —
   `if metadata.type == "technical-document": ... else: ...` — with
   the `book`/omitted branch calling the exact same
   `parse_structure()` path unchanged.
3. **Test dispatch in isolation** before touching any renderer code:
   confirm the right parser is invoked for all three `type` values,
   and confirm `book` output is still byte-identical with the
   dispatch point added but the new path still producing something
   (even a stub) for technical-document.
4. **Build Typst rendering support first** (matches this project's
   established pattern of Typst-then-EPUB) for whatever the Approach
   A/B decision implies — either new `InterpretedDocument`-consuming
   code, or an adapter back to `Book`-shaped objects.
5. **Extend or replace `interpret_technical_document()`** to handle
   the level-1 title heading correctly (§8) and any other gaps found
   while wiring real output.
6. **Verify Typst output for the real RideTogether manuscript** —
   compile it, check page count/size, Contents, numbering — against
   the *current* technical-document output (produced by the *old*
   pipeline right now) as the correctness bar, not just "it compiles."
7. **Build EPUB support second**, explicitly budgeting a separate
   verification pass — check Contents/nav population, cover
   correctness, given the three-times-repeated pattern of this
   diverging from Typst.
8. **Run the full byte-identical book regression check** (both PDF
   source and EPUB, both `type: book` explicit and omitted) before
   considering D3 done.
9. **Update `docs/MIGRATIONPLAN.md`**: mark D3 shipped, document what
   was actually built (including the Approach A/B decision and its
   consequences), note any new gaps found for D4 to pick up.

---

## 10. Definition of Done

- [ ] Approach A vs. B decision made and recorded in
      `docs/MIGRATIONPLAN.md`'s Decision Log.
- [ ] `metadata.type == "technical-document"` routes through
      `parser/document_model.py` + `interpretation.py`; `book`
      (including omitted `type`) routes through the unmodified
      `parser/structure.py`.
- [ ] Full test suite green — 176 existing tests unmodified and
      passing, plus new D3-specific tests.
- [ ] Explicit test coverage for all three `type` dispatch cases.
- [ ] `examples/sample-manuscript.md` (`type: book`) produces
      byte-identical Typst source and EPUB content (excluding OPF
      timestamp) before/after D3, verified by direct diff, not visual
      inspection.
- [ ] The real RideTogether manuscript compiles successfully through
      the new path — PDF source and EPUB both — with output at least
      as correct as the current (pre-D3) technical-document path:
      uniform A4, correct theme, correct Contents/TOC, no cover.
- [ ] `parser/reader.py`'s unknown-type hard error (C2 decision 1)
      still fires correctly and isn't duplicated or bypassed by the
      new dispatch.
- [ ] Post-D2 print-book pagination feature (`_print_book`,
      `_recto_page_break()`) unaffected — confirmed via the book
      regression check, not assumed safe because it's "unrelated."
- [ ] `docs/MIGRATIONPLAN.md` updated: D3 row marked shipped with an
      accurate description of what was actually built, any newly
      discovered gaps flagged for D4.
- [ ] **Not required for D3 completion** (explicitly deferred, do not
      let scope creep here): migrating `book` onto the new model
      (D5), validating against a structurally different
      manuscript (D4), adding any document type beyond the current
      two.
