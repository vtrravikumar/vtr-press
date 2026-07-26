# VTR Press

VTR Press is a lightweight publishing engine for transforming structured Markdown manuscripts into professional publishing formats.

The engine is designed to be independent of any specific book. A single manuscript can be rendered into multiple publication formats without modification.

## Quick Start

```bash
git clone ...

cd vtr-press

source .venv/bin/activate

pip install -r requirements.txt

python publish.py

## Current Capabilities

- ✅ Markdown parser
- ✅ Book abstract syntax tree (AST)
- ✅ Typst renderer
- ✅ PDF generation

## In Progress

- EPUB renderer
- EPUB writer

## Planned

- HTML renderer
- DOCX renderer
- Kindle support

---

## Repository Structure

```
vtr-press/

├── parser/
├── renderer/
├── writer/
├── theme/

├── model.py
├── publish.py
├── exceptions.py

├── docs/
├── assets/
├── generated/
└── output/
```

---

## Development Environment

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it (macOS/Linux):

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Deactivate:

```bash
deactivate
```

---

## Running

The publishing engine is currently under active development.

Eventually the primary entry point will be:

```bash
python publish.py
```

---

## Philosophy

Books are content.

VTR Press transforms manuscripts into professional publication formats.

Adding a new output format should never require changing the manuscript itself.