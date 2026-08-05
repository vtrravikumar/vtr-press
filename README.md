# VTR Press

VTR Press is an open-source publishing engine created by V.T.R. Ravi Kumar for producing professionally typeset books from structured Markdown manuscripts.

It separates content from presentation through a shared document model, allowing the same manuscript to be rendered into multiple publication formats without modification.

## Features

- PDF generation using Typst
- EPUB 3 generation
- Shared document model (AST)
- Support for Parts, Chapters and optional Scenes
- Front matter (Copyright, Dedication, Preface, Prologue, etc.)
- Verse blocks
- Inline formatting (bold, italic, code, links)
- Format-independent architecture

## Project Status

Current release: **v0.5.0**

Stable:

- PDF
- EPUB

Planned:

- HTML renderer
- Print-ready PDF
- Themes
- Accessibility improvements

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

Current Release: **v0.6.0**

## License

MIT License
