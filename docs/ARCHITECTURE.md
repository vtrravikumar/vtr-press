# VTR Press Architecture

## Status

**Current production architecture — v2.0**

This is the authoritative architecture document for VTR Press. It describes the architecture implemented in the repository and incorporates the architectural changes introduced during the v2.0 migration.

VTR Press evolves incrementally through small, releasable improvements rather than large architectural rewrites.

---

# 1. Architectural Objective

VTR Press transforms a single human-readable Markdown manuscript into one or more publication formats.

The fundamental architectural principle is:

> **The manuscript describes the document. The publishing system interprets the document. Renderers determine how it is presented.**

The manuscript remains independent of PDF, EPUB, Typst, CSS, page size, theme implementation, and renderer-specific details.

---

# 2. Current Architecture

The current architecture separates manuscript syntax, document representation, interpretation, common format rendering, and document-type-specific presentation.

```text
                         Markdown Manuscript
                                  │
                                  ▼
                         Metadata / Reader
                                  │
                                  ▼
                           Markdown Parser
                                  │
                                  ▼
                       Generic Document Model
                                  │
                                  ▼
                        Interpretation Layer
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
              Common Typst                Common EPUB
                    │                           │
             ┌──────┴──────┐             ┌──────┴──────┐
             │             │             │             │
             ▼             ▼             ▼             ▼
        Book Typst   Technical Typst  Book EPUB  Technical EPUB
             │             │             │             │
             ▼             ▼             │             │
            Typst         Typst          │             │
             │             │             │             │
             └──────┬──────┘             └──────┬──────┘
                    ▼                           ▼
              Typst Compiler              EPUB Writer
                    │                           │
                    ▼                           ▼
                   PDF                         EPUB
```

The important architectural boundary is the document representation and interpretation layer between manuscript parsing and publication rendering.

Common rendering infrastructure is shared by Book and Technical renderers within each output format, while document-type-specific presentation remains in the concrete renderers.

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

Interpretation is where document-type semantics and conventions belong.

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

The two document classes may have different structural conventions, but they share the generic publishing and rendering architecture.

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

Document-type differences belong to interpretation and document conventions, not to the output format itself.

Legacy book-specific classes such as `Part`, `Chapter`, and `Scene` may still exist in the implementation. Their continued existence is not considered an architectural failure. They are internal implementation structures that can be retired incrementally when doing so provides a concrete benefit.

---

# 8. Common Rendering Infrastructure

V2.0 deliberately separates common format-level rendering behaviour from document-type-specific presentation.

### Typst

```text
renderer/typst_common.py
        │
        ├── renderer/typst_book.py
        │
        └── renderer/typst_technical.py
```

### EPUB

```text
renderer/epub_common.py
        │
        ├── renderer/epub_book.py
        │
        └── renderer/epub_technical.py
```

The common modules provide reusable rendering primitives for document elements. The Book and Technical renderers add the presentation and structural behaviour specific to their document type.

This prevents the same semantic capability from being independently reimplemented in every renderer path while still allowing books and technical documents to have genuinely different publication conventions.

---

# 9. Typst / PDF Pipeline

The Typst path converts the interpreted document representation into Typst source.

```text
Document / Interpretation
          │
          ▼
    Common Typst
          │
     ┌────┴────┐
     ▼         ▼
 Book Typst  Technical Typst
     │         │
     └────┬────┘
          ▼
      .typ source
          │
          ▼
     Typst compiler
          │
          ▼
         PDF
```

Themes and renderer configuration determine visual presentation.

---

# 10. EPUB Pipeline

The EPUB path converts the interpreted document representation into XHTML and packages the publication into an EPUB archive.

```text
Document / Interpretation
          │
          ▼
     Common EPUB
          │
     ┌────┴────┐
     ▼         ▼
 Book EPUB  Technical EPUB
     │         │
     └────┬────┘
          ▼
 XHTML + navigation + OPF
          │
          ▼
      EPUB Writer
          │
          ▼
         EPUB
```

The EPUB renderer and writer are separate concerns.

The renderer produces publication content. The writer packages XHTML, navigation, metadata, CSS, images, and other publication assets.

---

# 11. Asset Architecture

Publication assets are resolved through the document asset system.

```text
Manuscript asset reference
          │
          ▼
     DocumentAssets
          │
          ├── resolve source
          ├── stage asset
          └── provide publication path
                    │
                    ▼
               PDF / EPUB
```

`DocumentAssets` is responsible for locating and staging assets.

Renderers should not independently search the manuscript filesystem for images.

For EPUB, staged assets are packaged into the EPUB archive.

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

Current supported types are:

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
      │
      ▼
document interpretation
      │
      ▼
publication pipeline
      │
      ├── Typst
      │      ├── Book
      │      └── Technical
      │
      └── EPUB
             ├── Book
             └── Technical
```

Document-type decisions belong at the interpretation/dispatch boundary rather than being scattered throughout individual renderers.

---

# 15. One Manuscript, Multiple Outputs

A fundamental v2.0 capability is:

```text
                  One Manuscript
                       │
              ┌────────┴────────┐
              ▼                 ▼
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

Validation included:

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

V2.0 establishes the generic document architecture and shared rendering infrastructure as the production direction.

The major changes are:

- generic document representation;
- generic Markdown parsing;
- interpretation separated from parsing;
- document-type-aware interpretation;
- common Typst rendering;
- Book and Technical Typst renderers;
- common EPUB rendering;
- Book and Technical EPUB renderers;
- shared asset handling;
- technical-document publishing;
- book and technical-document support in one architecture;
- multiple publication formats from the same manuscript.

---

# 18. What v2.0 Does Not Mean

V2.0 does not mean that every historical class or module has been deleted.

In particular, book-specific implementation structures may remain.

V2.0 means that these structures are no longer the sole architectural contract of the publishing system.

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

If a document element behaves consistently across Book and Technical documents within an output format, implement the shared behaviour once in the appropriate common renderer layer.

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
   │
   ▼
Document Model
   │
   ▼
Interpretation
   │
   ▼
Common Format Rendering
   │
   ▼
Document-Type Rendering
   │
   ▼
Output
```

If a proposed feature crosses these boundaries, the architecture should be reviewed before implementation.

---

# 21. Architectural Summary

The v2.0 architecture can be reduced to one sentence:

> **VTR Press is a document interpretation and publishing engine that transforms one human-readable manuscript into multiple publication formats through a shared document model and common format-level rendering infrastructure.**

The manuscript is the source of truth.

The parser understands syntax.

The document model represents structure.

The interpretation layer understands meaning and document conventions.

Common renderers provide reusable format-level rendering behaviour.

Book and Technical renderers determine document-type-specific presentation.

The publication writer creates the final artifact.

This separation is the foundation for future VTR Press development.
