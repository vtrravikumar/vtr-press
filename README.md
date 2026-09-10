# VTR Press

VTR Press is an open-source publishing engine created by V.T.R. Ravi Kumar for producing professionally typeset books and technical documents from structured Markdown manuscripts.

It separates content from presentation through a shared document model, allowing the same manuscript to be rendered into multiple publication formats without modification.

## Features

- PDF generation using Typst
- EPUB 3 generation
- Generic Document Model
- Book publishing with Parts, Chapters and optional Scenes
- Technical-document publishing
- Document-type-aware interpretation
- Common rendering infrastructure for Typst and EPUB
- Technical-document asset resolution and persistent generated asset staging
- Ordered and unordered lists
- Heading hierarchies up to Markdown level 6
- Code blocks with optional language metadata
- JSON code blocks
- Markdown tables with column alignment
- External image assets in PDF and EPUB
- Front matter (Copyright, Dedication, Preface, Prologue, etc.)
- Verse blocks
- Inline formatting (bold, italic, code, links)
- Format-independent architecture

## Project Status

The current `main` branch represents the **post-v2 development baseline**.

The v2.0 architecture is complete and establishes the generic document architecture and shared rendering infrastructure as the production foundation. The existing Book publishing path is intentionally retained where its proven Book-specific structures remain useful.

Stable capabilities include:

- PDF and EPUB generation
- `book` documents
- `technical-document` documents
- Generic document parsing and representation
- Document interpretation
- Native Typst technical-document rendering
- Native EPUB technical-document rendering
- Markdown tables in technical-document output
- Lists, deeper headings, code blocks and images
- Shared publication asset handling
- Automated regression coverage

The latest repository work is focused on theme and print-layout refinement. The engineering backlog is now in the post-v2 feature stage rather than the migration stage.

See `STATUS.md`, `docs/ARCHITECTURE.md`, `docs/ENGINEERING_PLAN.md`, `docs/ROADMAP.md`, and `BACKLOG.md` for the current engineering position and planned evolution.

## Prerequisites

VTR Press requires **Typst** to generate PDF output.

Typst is an external system dependency and is **not** installed via `requirements.txt` or `requirements-dev.txt`. You must install it separately.

- Install Typst from the official Typst documentation.
- EPUB generation works without Typst.
- PDF generation requires Typst to be available on your system PATH.

## Quick Start

Clone the repository:

```bash
git clone https://github.com/vtrravikumar/vtr-press.git
cd vtr-press
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the runtime dependencies:

```bash
pip install -r requirements.txt
```

Publish one of the configured targets:

```bash
python run.py memoir
```

or:

```bash
python run.py engineering
```

The current publishing runner uses `books.yaml` to identify manuscripts and output names. This manifest-driven workflow remains the supported input mechanism while simpler manuscript discovery is evaluated as BL-001.

## Repository Structure

```text
vtr-press/
│
├── parser/          # Markdown and document parsing
├── renderer/        # Common, Book and Technical renderers
├── writer/          # Publication writers/package generation
├── themes/          # Presentation and theme definitions
│
├── model.py         # Generic and Book document models
├── interpretation.py
├── publish.py       # Publication dispatch and pipeline
├── run.py           # Development publishing runner
│
├── docs/            # Architecture and engineering documentation
├── examples/        # Sample manuscripts
├── assets/          # Publication assets
├── generated/       # Generated intermediate artifacts
└── output/          # Generated PDF/EPUB output
```

## Your First Book

Start with the sample manuscript:

```bash
cp examples/sample-manuscript.md mybook.md
```

Update its front matter and content, then add an entry to `books.yaml` describing the manuscript and output name.

Run:

```bash
python run.py mybook
```

The current runner also supports a print mode for Book publications:

```bash
python run.py mybook print
```

## Running Tests

Install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the regression suite:

```bash
pytest tests/ -v
```

GitHub Actions runs the regression suite automatically on pushes and pull requests.

## Quality

VTR Press includes regression coverage across the publishing pipeline, including:

- Markdown parsing
- Generic document structure
- YAML front matter
- Document interpretation
- Book publishing
- Technical-document publishing
- Typst rendering
- EPUB rendering
- Lists and heading hierarchy
- Code blocks and JSON
- Markdown tables
- Images and asset staging
- End-to-end PDF and EPUB generation

The project follows a layered architecture:

```text
Markdown Manuscript
        ↓
      Parser
        ↓
Generic Document Model
        ↓
  Interpretation
        ↓
 ┌──────┴──────┐
 ↓             ↓
Common Typst  Common EPUB
 ↓             ↓
Book/Technical Book/Technical
 ↓             ↓
PDF           EPUB
```

## Publication Workflows

### Generate a standard Book edition

```bash
python run.py memoir
```

Produces:

- PDF
- EPUB

### Generate a publisher-ready print interior

```bash
python run.py memoir print
```

Produces:

- Interior PDF
- EPUB

### Publish a Technical Document

Technical documents use the same runner and manifest-driven workflow. The manuscript declares its document type in front matter:

```yaml
type: technical-document
```

The publishing pipeline then routes the manuscript through the generic Document Model, interpretation layer, and native Technical renderers.

## Engineering Direction

VTR Press is no longer in architectural migration. The v2.0 foundation is established and future work should evolve it incrementally.

The current post-v2 backlog includes areas such as:

- simpler manuscript discovery and publishing input;
- Markdown compatibility improvements;
- cross-references;
- image captions;
- language-aware syntax highlighting;
- richer tables;
- footnotes, citations and other publishing capabilities;
- additional output formats when justified by real use cases.

New semantic document capabilities should enter through the generic Document Model and interpretation layer before renderer-specific presentation is added.

## Philosophy

Books are content.

Publishing formats are presentation.

The manuscript should never change simply because a new output format is added.

VTR Press keeps those concerns separate through a shared document model, interpretation layer, common format rendering, and document-type-specific renderers.

> **A manuscript should be written once and published anywhere.**

## License

MIT License
