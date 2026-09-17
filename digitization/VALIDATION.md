# Digitization Validation — College Project

This document records real-document validation of the VTR Press digitization layer using the historical college project report.

## Source used

The validation source is the scanned report **Analysis of Artificial Neural Network (Using Back Propagation & Genetic Algorithm)**.

The source report contains ordinary prose, title/certificate material, tables, diagrams, numerical results and source-code listings. This makes it a useful validation case for the reusable digitization pipeline.

## Runtime used for experiments

For validation experiments, PDF pages were rasterized and OCR was executed in a temporary Linux/container environment providing:

- `pdftoppm`
- Tesseract OCR 5.5.0

This runtime is an experiment environment, not a VTR Press installation requirement. The VTR Press code keeps PDF rendering and OCR behind adapter boundaries.

## Pages sampled

### Report pages

- Page 1 — title page
- Page 3 — submission/title material
- Page 4 — viva voce material
- Page 5 — certificate
- Page 6 — acknowledgement
- Page 7 — abstract
- Page 8 — introduction/general
- Page 9 — state of the art
- Page 10 — historical background/motivation/scope

### Source-code pages

- `Code-01.pdf`, pages 1–6

The sample deliberately includes both prose and source code because they have materially different OCR requirements.

## Observations

### 1. Ordinary prose is viable as an OCR draft

The introduction, abstract and acknowledgement pages produced readable OCR with the existing Tesseract adapter. Paragraph structure and technical terminology were substantially recoverable, although errors remain.

Examples of observed OCR defects include:

- `inpatterns` instead of `in patterns`;
- `novell` instead of the scanned word;
- occasional missing punctuation or spacing;
- confusion between similar characters such as `Il.` / `11.`;
- page-edge artefacts and stray scan marks.

This confirms the architectural assumption that OCR output should be treated as a **reviewable manuscript draft**, not authoritative text.

### 2. Title and certificate pages need stronger preprocessing

The title page contains large display typography, uneven illumination, page curvature and scan artefacts. OCR recovered much of the meaningful content but also produced substantial noise.

The certificate/viva pages similarly contain layout elements, signatures and isolated text regions that should not simply be concatenated into prose.

### 3. Source code is a separate problem

The scanned C source listings were significantly less reliable than ordinary prose. Tesseract introduced errors in characters that are syntactically meaningful, including:

- `#` and include directives;
- `/` and comment delimiters;
- braces and brackets;
- pointer/declaration punctuation;
- digits and variable names;
- operators and comparison expressions.

For example, a scanned `#include` line can be emitted with the leading character confused or omitted. Similar errors occur in braces, array declarations and operators.

A code listing therefore **cannot be accepted as source code merely because OCR produced plausible-looking text**.

### 4. Tables and diagrams cannot be solved by plain OCR text

The report contains tables and diagrams whose meaning depends on spatial layout. Plain page OCR does not preserve that structure reliably.

The digitization pipeline therefore needs structure-aware handling rather than treating every page as one text block.

## Preprocessing validation

The conservative preprocessing implementation provides grayscale conversion, automatic contrast normalization and optional fixed-level thresholding while leaving the source raster untouched.

A controlled comparison used the same representative report pages for passthrough OCR versus grayscale/autocontrast and then compared fixed thresholding as an additional variant.

The result was deliberately **not** treated as an accuracy claim:

- grayscale/autocontrast produced modest changes in OCR output on prose pages, including some punctuation/spacing differences, but no consistent improvement across the sampled pages;
- fixed thresholding introduced additional recognition changes on prose pages and did not make source-code OCR reliable;
- source-code OCR remained unreliable under all tested variants.

Therefore grayscale/autocontrast is available as a conservative derived preprocessing path, while thresholding remains opt-in. Geometry-changing operations such as deskewing and cropping remain deferred until separately validated.

## OCR profiles

The OCR adapter provides named configuration profiles for:

- `prose`;
- `layout`;
- `code`.

These are configuration presets, not automatic page classification. Different page types have materially different OCR risks, so the pipeline now adds a separate conservative classification step.

## Structure classification validation

The structure classifier operates on OCR text and currently distinguishes three broad page types:

- `prose` — the safe default for ordinary running text;
- `code` — selected only when multiple independent code signals are present;
- `layout` — selected conservatively for sparse, display-like or otherwise layout-heavy OCR.

The classifier reports bounded confidence and reasons so downstream review can see why a page was classified. It does **not** attempt to infer tables or diagrams from text alone.

The classifier is integrated into the page-level pipeline and Markdown assembler. Each classified page receives a source/page marker plus a structure/confidence marker. Classification can also be disabled for callers that want the earlier page-only behaviour.

## Code-safe handling

When a page is classified as `code`, the generated Markdown preserves the OCR text in an unlabelled fenced code block and adds an explicit review marker stating that the listing must be verified against the source scan.

No programming-language hint is assigned automatically. This avoids presenting uncertain OCR as authoritative or executable source code while preserving the OCR text for human correction.

## Source-image preservation

The pipeline keeps the original rendered page image separately from any preprocessed image used for OCR. Generated Markdown records a `source-image` comment for every page so reviewers can return to the source page even when preprocessing was enabled.

For layout-classified pages, the assembler can optionally embed the source page image as a visual fallback. This is intentionally a page-level fallback rather than an attempted semantic extraction of a figure, diagram or table.

This preserves information that plain OCR cannot safely represent: spatial relationships, signatures, diagrams, and table geometry. It also avoids silently inventing Markdown tables or figure boundaries from uncertain OCR.

## Review markers

The review layer never edits OCR text. It can add machine-readable Markdown comments for:

- `code-ocr-verification`;
- `layout-visual-verification`;
- `low-structure-confidence` for weak non-prose classification;
- `suspicious-ocr-glyphs` for a small set of recognizable OCR artefacts.

These markers are conservative review signals, not proof that a particular character or word is wrong.

## Regression fixtures

The repository now contains small text snapshots derived from the actual college-project scan validation:

- `prose-page-08.txt` — representative introduction OCR;
- `code-page-03.txt` — representative C source OCR, including observed OCR corruption;
- `layout-page-01.txt` — representative title-page OCR.

These fixtures exercise structure classification and review-marker behaviour in CI without storing duplicate large binary scans inside VTR Press. The authoritative scanned pages remain in the `college-project` source repository. The fixture tests therefore protect the reusable classification/review contract while real-image validation remains an integration-level activity.

## End-to-end workflow

A repeatable command-line path is now available:

```text
python -m digitization source.pdf manuscript.md
```

The CLI supports explicit `prose`, `layout` and `code` OCR profiles, conservative or passthrough preprocessing, an optional working directory, and optional source-image embedding for layout pages. It writes the Markdown draft and copies rendered source pages beside it so the generated `source-image` references remain usable.

The CLI does not modify the input PDF and does not claim that OCR output is final publication text.

## Current result

The architecture is validated at the adapter, orchestration, structure-awareness, visual-fallback, review-marker and repeatable-workflow boundaries:

```text
scanned source
      ↓
page rendering
      ↓
derived preprocessing
      ↓
OCR profile
      ↓
page-level text
      ↓
conservative structure classification
      ↓
source-image provenance / optional visual fallback
      ↓
review markers
      ↓
reviewable Markdown draft
```

The real document establishes that reliable digitization requires more than raw OCR. The remaining work is increasingly about validation against additional real documents and about only adding semantic table/figure extraction where fidelity can be demonstrated.

## Next implementation increment

The remaining digitization work should address these areas in order:

1. **Broader end-to-end validation** — run the workflow against the college project and a second document such as the Accupressure validation case in an environment with the required OCR/PDF tools.
2. **Real-image regression strategy** — decide how to maintain a small, representative set of binary page fixtures without bloating the publishing repository; the source project scans remain the current integration source.
3. **Image/layout-aware table and figure extraction** — investigate semantic extraction only where spatial relationships can be preserved faithfully; keep the page-image fallback when they cannot.

## Fidelity rule

The goal of digitization is **faithful transcription of the source**, not modernization or correction. When OCR is uncertain, the pipeline should preserve the uncertainty and the original page reference rather than silently guessing.
