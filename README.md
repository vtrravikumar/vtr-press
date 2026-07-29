# VTR Press

VTR Press is a lightweight publishing engine for transforming structured Markdown manuscripts into professional publishing formats.

The engine is designed to be independent of any specific book. A single manuscript can be rendered into multiple publication formats without modification.

# Quick Start

## 1. Open a terminal

```bash
cd ~/Documents/Projects/vtr-press
```

> Adjust the path if your Projects directory is elsewhere.

---

## 2. Activate the virtual environment

```bash
source .venv/bin/activate
```

---

## 3. Install dependencies (first time only)

```bash
pip install -r requirements.txt
```

---

## 4. Verify the available books

Open:

```text
books.yaml
```

Example:

```yaml
books:

  engineering:
    manuscript: ../HomeLab-Engineering/manuscript.md
    cover: ../HomeLab-Engineering/assets/cover.png
    output_name: HomeLab-Engineering

  memoir:
    manuscript: ../Project-memoir/manuscript.md
    cover: ../Project-memoir/assets/cover.png
    output_name: Project-Memoir
```

---

## 5. Generate a PDF

Engineering Home

```bash
python run.py engineering
```

Project Memoir

```bash
python run.py memoir
```

---

## Output

Generated Typst source:

```text
generated/
```

Generated PDF:

```text
output/
```

Example:

```text
output/
    HomeLab-Engineering.pdf
    Project-Memoir.pdf
```

## Typical Daily Workflow

```bash
cd ~/Documents/Projects/vtr-press

source .venv/bin/activate

git pull

python run.py engineering
```

or

```bash
python run.py memoir
```

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