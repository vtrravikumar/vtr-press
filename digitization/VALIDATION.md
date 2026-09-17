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

## Preprocessing increment

The first implementation increment after the baseline validation now provides a conservative Pillow-based preprocessing adapter.

The preprocessing stage can independently produce a derived PNG using:

- grayscale conversion;
- automatic contrast normalization;
- optional fixed-level thresholding.

The original raster is never modified. Geometry-changing operations such as deskewing and cropping remain deliberately deferred until they are validated against the real scans.

This increment establishes the preprocessing mechanism, but it does **not** yet establish that a particular transformation improves OCR for the college report. That requires another controlled OCR comparison using the same representative pages.

## OCR profile increment

The OCR adapter now provides named configuration profiles for:

- `prose`;
- `layout`;
- `code`.

These are configuration presets, not automatic page classification. The real document validation showed that different page types have materially different OCR risks, so automatic structure classification remains a later step.

## Current result

The architecture is validated at the adapter and orchestration boundary:

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
reviewable Markdown draft
```

The real document also establishes the requirements for the next layer: **document-aware acquisition**.

## Next implementation increment

The next digitization work should address these areas in order:

1. **Controlled preprocessing comparison** — run the same representative pages with passthrough versus conservative preprocessing and record the effect on OCR.
2. **Structure classification** — distinguish prose, headings, code, tables and figure/diagram regions before Markdown assembly.
3. **Code-safe handling** — preserve code listings as source material requiring explicit review; do not silently transform uncertain OCR into executable-looking code.
4. **Table/figure preservation** — retain the source image and provenance when reliable structural extraction is not available.
5. **Review markers** — make uncertain or structure-sensitive regions visible in the generated manuscript.
6. **Regression fixtures** — retain representative page-level examples so improvements can be measured against the same historical source.

## Fidelity rule

The goal of digitization is **faithful transcription of the source**, not modernization or correction. When OCR is uncertain, the pipeline should preserve the uncertainty and the original page reference rather than silently guessing.
