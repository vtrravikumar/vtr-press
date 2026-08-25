# VTR Press

VTR Press is an open-source publishing engine created by V.T.R. Ravi Kumar for producing professionally typeset books and technical documents from structured Markdown manuscripts.

It separates content from presentation through a shared document model, allowing the same manuscript to be rendered into multiple publication formats without modification.

## Features

- PDF generation using Typst
- EPUB 3 generation
- Generic document model
- Support for Parts, Chapters and optional Scenes
- Technical-document publishing
- Technical-document asset resolution and persistent generated asset staging
- Ordered and unordered lists
- Deeper heading hierarchies
- Code blocks and JSON
- External image assets in PDF and EPUB
- Front matter (Copyright, Dedication, Preface, Prologue, etc.)
- Verse blocks
- Inline formatting (bold, italic, code, links)
- Format-independent architecture

## Project Status

Current release: **v0.9.1**

Stable:

- PDF
- EPUB
- `book` documents
- `technical-document` documents

The v0.9.1 release completes the D3/D4 generic technical-document
publishing pipeline. The full regression suite contains **207 passing
tests**.

Known limitation:

- Markdown tables are currently not rendered as native tables in the
  technical-document PDF/Typst output. This is the next isolated
  capability being developed.

## Prerequisites

VTR Press requires **Typst** to generate PDF output.

Typst is an external system dependency and is **not** installed via `requirements.txt` or `requirements-dev.txt`. You must install it separately:

- **Install Typst:** https://typst.app/docs/guide/install/
- EPUB generation works without Typst.
- PDF generation requires Typst to be available on your system PATH.

## Quick Start

```bash
git clone https://github.com/<username>/vtr-press.git
cd vtr-press

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python run.py memoir
```

or

```bash
python run.py engineering
```

## Repository Structure

```text
vtr-press/

├── parser/
├── renderer/
├── writer/
├── themes/

├── model.py
├── publish.py
├── run.py

├── docs/
├── assets/
├── generated/
└── output/
```
## Your First Book

Start by copying the sample manuscript.

```bash
cp examples/sample-manuscript.md mybook.md
```

Update the metadata.

Create a cover image.

Add an entry to `books.yaml`.

Run:

```bash
python run.py mybook
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


## Quality

VTR Press includes an automated regression test suite covering:

- Markdown parser
- Document structure
- YAML front matter
- Typst renderer
- EPUB renderer
- End-to-end publishing pipeline

Run the suite with:
```bash
pytest tests/ -v
```

### Generate a standard edition

```bash
python run.py memoir
```

Produces:
- PDF (with publisher branding)
- EPUB

### Generate a publisher-ready print interior

```bash
python run.py memoir print
```

Produces:
- Interior PDF suitable for print-on-demand submission
- EPUB (unchanged)

## Philosophy

Books are content.

Publishing formats are presentation.

The manuscript should never change simply because a new output format is added.

VTR Press keeps those concerns separate through a shared document model and independent renderers.


## License

MIT License
