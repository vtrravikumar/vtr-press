# VTR Press Digitization

The `digitization` package is the upstream source-conversion layer of VTR Press.

Its purpose is to convert scanned or otherwise image-based source material into a **reviewable Markdown manuscript draft**. The existing VTR Press publishing pipeline remains responsible for parsing, interpreting, and rendering that manuscript.

## Architectural boundary

```text
Source PDF / scans
        |
        v
   Digitization
        |
        +-- page extraction
        +-- image preprocessing
        +-- OCR
        +-- structure classification
        +-- source-image preservation
        +-- review markers
        +-- figures / diagrams
        +-- tables
        +-- source-code handling
        |
        v
 Markdown draft
        |
        v
Existing VTR Press publishing pipeline
```

Digitization must not silently rewrite, modernize, or correct the source. OCR output is a draft and requires review, particularly for tables, technical terminology, diagrams, and source code.

## Current implementation

The current increment establishes the core, adapter-based pipeline:

- `pdf.py` — PDF-to-page rendering through a `pdftoppm` adapter.
- `preprocess.py` — conservative preprocessing with both an unchanged passthrough and a Pillow-based grayscale/contrast/threshold path.
- `ocr.py` — Tesseract OCR adapter with configurable language, page segmentation mode, and named profiles for prose, layout-heavy pages and code.
- `structure.py` — conservative OCR-text classification into broad `prose`, `code` and `layout` page types, with bounded confidence and reasons.
- `assets.py` — byte-preserving helper for copying rendered source-page images into a stable asset directory.
- `review.py` — conservative review-marker generation for structure-sensitive pages and a small set of suspicious OCR glyph patterns.
- `pipeline.py` — deterministic orchestration from PDF pages through preprocessing, OCR and optional structure classification, with page-level provenance.
- `cli.py` / `__main__.py` — repeatable command-line PDF-to-Markdown workflow, including multi-PDF project-source batching.
- `MarkdownAssembler` — produces a reviewable Markdown draft with source-PDF/page markers, structure/confidence markers and review markers. It can optionally embed the original rendered page image for layout-heavy pages.

Structure classification is deliberately conservative. It is a page-level routing and review aid, not a claim that OCR text can reconstruct tables or diagrams. Those require image/layout-aware handling in later increments.

## Runtime requirements

The current concrete adapters expect these dependencies in the execution environment:

- Tesseract OCR (`tesseract`)
- Poppler's `pdftoppm`
- Python Pillow for image preprocessing

VTR Press does not prescribe how Tesseract or Poppler are installed. A future reproducible runtime may use a container or another managed environment. The important boundary is that the Python pipeline talks to small adapters, not directly to a specific operating-system package manager.

## Command-line workflow

The normal user-facing workflow is intentionally simple: provide a source PDF and get a `manuscript.md` draft plus the rendered source pages used for review.

```text
python -m digitization source.pdf
```

This writes `manuscript.md` beside the input PDF. An explicit output path is also supported:

```text
python -m digitization source.pdf manuscript.md
```

### Project source-folder workflow

For a project whose source material is organized as:

```text
project/
├── source/
│   ├── report/
│   │   ├── report-01.pdf
│   │   └── report-02.pdf
│   └── code/                 # optional; may be absent or empty
│       ├── code-01.pdf
│       └── code-02.pdf
└── manuscript.md             # generated one level above source/
```

run one command from the project root:

```text
python -m digitization source/
```

The command automatically:

1. requires one or more PDFs in `report/`;
2. accepts zero or more PDFs in `code/`, including no `code/` folder at all;
3. processes report PDFs in numbered order using the `prose` OCR profile;
4. processes code PDFs in numbered order using the `code` OCR profile;
5. requires multi-part PDFs to be numbered continuously from `01` (`01`, `02`, `03`, ...), preventing an accidentally missing part from going unnoticed;
6. collates all page results into **one `manuscript.md` at the project root**;
7. preserves the originating PDF and page number for every page;
8. keeps rendered source pages under the project-root `pages/` directory with collision-safe names;
9. keeps report/code document boundaries as Markdown metadata rather than treating each PDF as a separate manuscript.

A single report PDF may use any filename because there is no sequence to validate. Once a source category contains multiple PDFs, each must carry a numeric suffix and the sequence must be continuous from `01`.

For the college project, the three report PDFs and three source-code PDFs therefore become one reviewable manuscript without manually concatenating six OCR files. If the project contains only the report PDFs, the same command works without code sources.

Useful options include:

```text
--profile prose|layout|code
--preprocess none|conservative
--include-source-images
--work-dir <directory>
```

The `--profile` option applies to a single-PDF input. Project source folders select `prose` for `report/` and `code` for `code/` automatically.

The command writes the Markdown draft and copies rendered source pages into a sibling `pages/` directory so `source-image` references remain usable. It does not modify the input PDFs.

### What the command produces

For a single input such as:

```text
old-report.pdf
```

the default workflow produces:

```text
manuscript.md
pages/
    01-old-report-page-1.png
    01-old-report-page-2.png
    ...
```

For a project source folder, the output is:

```text
project/
├── source/
│   ├── report/
│   └── code/
├── manuscript.md
└── pages/
    ├── 01-College-project-01-page-1.png
    ├── 01-College-project-01-page-2.png
    ├── ...
    ├── 04-Code-01-page-1.png
    └── ...
```

The Markdown contains page provenance and review metadata, allowing the manuscript to be checked back against the original scans. Layout-sensitive pages can optionally include their source image directly in the Markdown.

This is the intended boundary: **PDF in → reviewable `manuscript.md` out**. Human review remains necessary before the manuscript is treated as publication-ready.

## Preprocessing policy

The original raster page is never modified. `PassthroughPreprocessor` preserves it byte-for-byte, while `PillowPreprocessor` writes a separate derived PNG.

The initial Pillow path deliberately limits transformations to:

- grayscale conversion;
- automatic contrast normalization;
- optional fixed-level thresholding.

Geometry-changing operations such as deskewing and cropping are intentionally deferred until they are validated against real scanned documents.

## Source-image preservation

Digitization keeps the rendered source-page path separately from the image actually passed to OCR. This matters when preprocessing is enabled: review must always be able to return to the unmodified page image.

Every generated page carries a `source-image` Markdown comment. By default this is metadata only, so the manuscript is not cluttered with page images. For layout-classified pages, `MarkdownAssembler(include_source_images=True)` can embed the source image as a visual fallback. This is intended for title pages, diagrams and uncertain spatial structures where plain OCR is insufficient.

The fallback is deliberately page-level. It does **not** claim to have extracted a table or figure into semantic Markdown. When a table or diagram depends on spatial relationships that OCR cannot preserve, the source image remains the authoritative visual reference until a later image/layout-aware extraction step is implemented.

## Review markers

The review layer never edits OCR text. It adds machine-readable Markdown comments when a page needs additional human attention:

- `code-ocr-verification` for code-like pages;
- `layout-visual-verification` for layout-heavy pages;
- `low-structure-confidence` when a non-prose classification is weak;
- `suspicious-ocr-glyphs` for a small set of recognizable OCR artefacts.

These markers are intentionally conservative. They are review signals, not proof that a particular character or word is wrong, and they are not a substitute for checking the original scan.

## Validation strategy

The first real-document validation used the historical college project report, including prose, title/certificate pages and source-code listings. That experiment showed that ordinary prose is viable as an OCR draft, while code, tables and diagrams require structure-aware handling and explicit review.

A controlled comparison of representative report and code pages found that grayscale/autocontrast can change OCR output modestly but does not establish a universal accuracy improvement. Fixed thresholding introduced additional recognition changes and therefore remains opt-in rather than a default transformation.

Validation should compare generated Markdown against the original scan after each preprocessing or classification change. A transformation or classifier is useful only if it supports faithful transcription and review without silently changing source meaning.

## Design principles

1. Keep digitization separate from parsing and rendering.
2. Prefer deterministic, reproducible processing.
3. Preserve the source faithfully; do not silently normalize content.
4. Treat OCR as an imperfect acquisition step, not as authoritative text.
5. Keep OCR engines behind a small adapter boundary so alternatives can be added later.
6. Keep external runtime dependencies outside the publishing engine's core model.
7. Never modify the authoritative source raster during preprocessing.
8. Use structure classification as a conservative review/routing aid, not as a substitute for visual inspection.
9. Preserve a visual source fallback when spatial structure cannot be represented safely as text.
10. Test the pipeline with real-world documents containing prose, tables, diagrams, and code.
