# VTR Press Architecture — v2.0

## Status

**Current production architecture — v2.0**

This document describes the architecture actually implemented in VTR Press as of v2.0.

It supersedes the earlier target-state description in `docs/ARCHITECTURE.md` for purposes of understanding the current implementation.

---

# 1. Architectural Objective

VTR Press transforms a single human-readable Markdown manuscript into one or more publication formats.

The fundamental architectural principle is:

> **The manuscript describes the document. The publishing system interprets the document. Renderers determine how it is presented.**

The manuscript must remain independent of PDF, EPUB, Typst, CSS, page size, theme implementation, and renderer-specific details.

---

# 2. Current Architecture

The v2.0 architecture is:

```text
Markdown Manuscript
        |
        v
Metadata / Reader
        |
        v
Markdown Parser
        |
        v
Generic Document Model
        |
        v
Interpretation Layer
        |
        +-------------------+
        |                   |
        v                   v
Common Typst          Common EPUB
Renderer              Renderer
        |                   |
        v                   v
      Typst              XHTML
        |                   |
        v                   v
       PDF              EPUB Writer
                            |
                            v
                          EPUB
```

The important architectural boundary is the document representation between parsing/interpretation and rendering.

---

# 3. The Manuscript

The manuscript is the single source of truth.

It contains document content, Markdown structure, and minimal publication metadata.

The manuscript does not contain renderer-specific instructions.

Those decisions belong to the publishing system.

---

# 4. Parsing

The parser is responsible for understanding Markdown syntax.

Its responsibilities include:

- reading front matter;
- recognizing headings;
- recognizing paragraphs;
- recognizing lists;
- recognizing images;
- recognizing tables;
- recognizing code blocks;
- recognizing verse blocks;
- preserving document order.

The parser should not decide how a heading looks, what font is used, what page size is selected, how EPUB XHTML is structured, or how Typst is generated.

Those are downstream concerns.

---

# 5. Generic Document Model

The generic `Document` model represents the logical document as an ordered collection of blocks.

Conceptually:

```text
Document
 |-- Heading
 |-- Paragraph
 |-- Image
 |-- Paragraph
 |-- List
 |-- CodeBlock
 |-- Table
 `-- ...
```

The model is deliberately independent of the final output format.

A new block type should be introduced as a semantic document capability rather than independently implemented in every renderer.

---

# 6. Interpretation

Parsing answers:

> "What Markdown construct is this?"

Interpretation answers:

> "What does this construct mean for this document type?"

This separation is one of the principal architectural changes introduced during the Phase D migration.

Interpretation is where document-type semantics belong.

Examples include:

- book structure;
- technical-document structure;
- section semantics;
- document conventions;
- numbering meaning;
- which elements form the main outline.

The renderer should receive already-understood document information rather than rediscovering document semantics from raw Markdown.

---

# 7. Books and Technical Documents

V2.0 supports both books and technical documents within the same publishing architecture.

The two document classes may have different structural conventions, but they share the generic publishing model.

For example:

```text
Book
  Part
    Chapter
      Scene
        Paragraph

Technical Document
  Heading
  Paragraph
  Heading
  CodeBlock
  Table
```

These differences belong to interpretation and document conventions, not to the output format.

Legacy book-specific classes such as `Part`, `Chapter`, and `Scene` may still exist in the implementation.

Their continued existence is not considered an architectural failure. They are internal implementation structures that can be retired incrementally when doing so provides a concrete benefit.

---

# 8. Common Rendering Infrastructure

V2.0 introduced a deliberate separation between common rendering behaviour and document-specific presentation.

Important modules include:

- `renderer/typst_common.py`
- `renderer/epub_common.py`

These provide reusable rendering behaviour for document elements.

The purpose is to prevent the same semantic capability from being implemented independently in multiple renderer paths.

For example:

```text
Image
  |
  +-- common Typst rendering
  |
  `-- common EPUB rendering
```

---

# 9. Typst / PDF Pipeline

The Typst path converts the document representation into Typst source.

```text
Document
   |
   v
Typst Renderer
   |
   v
.typ
   |
   v
Typst compiler
   |
   v
PDF
```

Themes determine visual presentation.

---

# 10. EPUB Pipeline

The EPUB path converts the document representation into XHTML documents and packages them into an EPUB archive.

```text
Document
   |
   v
EPUB Renderer
   |
   v
XHTML + navigation + OPF
   |
   v
EPUB Writer
   |
   v
EPUB
```

The EPUB renderer and writer are separate concerns.

The renderer produces publication content.

The writer packages XHTML, navigation, metadata, CSS, images, and other publication assets.

---

# 11. Asset Architecture

Publication assets are resolved through the document asset system.

```text
Manuscript asset reference
          |
          v
     DocumentAssets
          |
          +-- resolve source
          +-- stage asset
          `-- provide publication path
                    |
                    v
             PDF / EPUB
```

`DocumentAssets` is responsible for locating and staging assets.

Renderers should not independently search the manuscript filesystem for images.

For EPUB, staged assets are packaged into the EPUB archive.

Example:

```text
assets/images/fig1.png
        |
        v
generated staging
        |
        v
OEBPS/images/fig1.png
```

---

# 12. Themes

Themes control presentation.

Typical responsibilities include:

- typography;
- page size;
- spacing;
- heading appearance;
- page layout;
- cover treatment;
- visual hierarchy.

Themes must not redefine document structure.

The document type determines conventions; the theme determines how those conventions are presented.

---

# 13. Document Type

`metadata.type` describes what the manuscript is.

Current supported types:

```text
book
technical-document
```

An omitted type defaults to `book`.

An unrecognized type is rejected during front-matter processing.

The manuscript therefore declares what it is, rather than how it should be rendered.

---

# 14. Publication Dispatch

Document type is interpreted at the publishing boundary.

```text
metadata.type
      |
      v
document interpretation
      |
      v
publication pipeline
      |
      +-- Typst
      `-- EPUB
```

Document-type decisions belong at the interpretation/dispatch boundary rather than being scattered throughout individual renderers.

---

# 15. One Manuscript, Multiple Outputs

A fundamental v2.0 capability is:

```text
                  One Manuscript
                       |
              +--------+--------+
              v                 v
             PDF               EPUB
```

The author does not maintain separate PDF and EPUB manuscripts.

The same source document supplies both outputs.

---

# 16. Validation

The architecture is protected by automated regression tests.

At the v2.0 release milestone:

```text
224 tests passed
```

Validation has included:

- book manuscripts;
- technical documents;
- headings;
- subheadings;
- lists;
- code blocks;
- JSON;
- images;
- asset staging;
- PDF generation;
- EPUB generation;
- EPUB image packaging;
- renderer regression behaviour.

Real manuscripts were used during the migration rather than relying only on synthetic unit-test documents.

---

# 17. What v2.0 Changed

Before the migration, the publishing engine was primarily shaped around the book model.

V2.0 establishes the generic document architecture as the production direction.

The major changes are:

- generic document representation;
- generic Markdown parsing;
- interpretation separated from parsing;
- document-type-aware interpretation;
- common Typst rendering;
- common EPUB rendering;
- shared asset handling;
- technical-document publishing;
- book and technical-document support in one architecture;
- multiple publication formats from the same manuscript.

---

# 18. What v2.0 Does Not Mean

V2.0 does not mean that every historical class or module has been deleted.

In particular, book-specific implementation structures may remain.

V2.0 means that these structures are no longer the architectural contract of the publishing system.

They can be simplified or removed later without redefining the manuscript format or the publishing architecture.

---

# 19. Rules for Future Development

### Rule 1 — Extend the document model first

If a capability is a property of the document itself, represent it in the document model.

Do not add renderer-specific parsing for it.

### Rule 2 — Keep interpretation separate

If behaviour depends on what kind of document something is, it belongs in interpretation/conventions rather than the Markdown parser.

### Rule 3 — Keep renderers format-specific

Typst code should solve Typst presentation.

EPUB code should solve EPUB presentation.

Neither should become responsible for understanding raw manuscript structure.

### Rule 4 — Reuse common rendering behaviour

If a document element behaves consistently across book and technical documents, implement the shared behaviour once.

### Rule 5 — Assets go through `DocumentAssets`

Do not introduce renderer-specific filesystem searches for manuscript assets.

### Rule 6 — Preserve the manuscript contract

Authors should not need to change a manuscript merely because a new renderer or theme is introduced.

### Rule 7 — Test before declaring architectural work complete

New document capabilities require regression coverage across the affected parsing, interpretation and rendering layers.

---

# 20. Future Extension

The architecture is intentionally capable of supporting additional document types and formats.

Potential future document types include:

- white papers;
- tutorials;
- API references;
- other structured technical publications.

Potential future output formats may be added without changing the manuscript itself.

New capabilities should be evaluated against the existing separation:

```text
Syntax
   |
   v
Document Model
   |
   v
Interpretation
   |
   v
Presentation
   |
   v
Output
```

If a proposed feature crosses these boundaries, the architecture should be reviewed before implementation.

---

# 21. Architectural Summary

The v2.0 architecture can be reduced to one sentence:

> **VTR Press is a document interpretation and publishing engine that transforms one human-readable manuscript into multiple publication formats through a shared document model and common rendering infrastructure.**

The manuscript is the source of truth.

The parser understands syntax.

The document model represents structure.

The interpretation layer understands meaning and document conventions.

The renderer determines presentation.

The publication writer creates the final artifact.

This separation is the foundation for future VTR Press development.
