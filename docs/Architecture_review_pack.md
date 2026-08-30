# Architecture Review Pack

## Status

**Proposed capability — not implemented**

This document describes a potential future VTR Press capability: generating a concise Architecture Review Pack from an authoritative Solution Architecture manuscript.

It is a product/design proposal, not part of the current v2.0 publishing pipeline.

---

# Problem

A Solution Architecture Document can be comprehensive and authoritative, but it is not always the ideal format for an Architecture Review Board, Steering Committee, or Technical Design Authority meeting.

Reviewers may need a concise, high-level summary that can be read quickly while remaining faithful to the underlying architecture.

Maintaining a separate presentation creates duplication and creates the risk that review material diverges from the authoritative Solution Architecture Document.

---

# Proposed Solution

VTR Press could generate an Architecture Review Pack directly from a Solution Architecture manuscript.

The Review Pack would be a **derived artifact**, not a second source document.

```text
Solution Architecture.md
          │
          ▼
       VTR Press
          │
     ┌────┼─────────────┐
     ▼    ▼             ▼
    PDF  EPUB   Architecture Review
                              PDF
```

The Solution Architecture manuscript remains the single source of truth.

---

# Design Principles

The feature should follow the established VTR Press principles:

- Single Source of Truth
- Convention over Configuration
- Separation of Content and Presentation
- No Information Duplication
- Renderer Owns Presentation
- Reuse the existing document and interpretation architecture

The feature should not introduce a second manuscript or parallel publishing pipeline.

---

# Proposed Output

The Review Pack would be an additional publication target derived from the same technical manuscript.

Conceptually:

```text
Solution Architecture manuscript
            │
            ▼
      Document Model
            │
            ▼
       Interpretation
            │
            ▼
   Architecture Review renderer
            │
            ▼
   Architecture Review PDF
```

A possible command-line interface might be:

```text
vtr-press render Solution Architecture.md --pdf
vtr-press render Solution Architecture.md --epub
vtr-press review Solution Architecture.md
```

The exact CLI is intentionally **not specified yet**.

---

# Proposed Review Structure

A generated review might contain approximately ten pages:

1. Cover
2. Executive Summary
3. Business Vision
4. Business Architecture
5. Domain Architecture
6. High-Level Architecture
7. Technology Overview
8. Key Architecture Decisions
9. Deployment & Security Summary
10. Conclusions / Questions

The exact structure should be determined by the requirements of real architecture-review workflows.

The renderer should extract and summarize relevant material from the Solution Architecture Document without requiring the author to maintain a second document.

---

# Author Experience

The intended workflow is:

```text
Architect writes one manuscript
            │
            ▼
Solution Architecture.md
            │
            ▼
        VTR Press
       /    |     \
      PDF  EPUB  Review Pack
```

The architect does not maintain a separate presentation solely for the review process.

---

# Relationship to Current Architecture

The Architecture Review Pack should be implemented as an extension of the current VTR Press architecture rather than as an independent renderer stack.

The preferred future direction is:

```text
                    Interpretation
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        Common Typst  Common EPUB  Review Output
              │            │            │
        Book / Tech   Book / Tech   Architecture
                                      Review
```

The exact renderer decomposition is a future design decision.

The important architectural constraint is that the Review Pack consumes the same interpreted document information and does not create a parallel manuscript model.

---

# Future Enhancements

Potential future extensions include:

- executive summaries;
- speaker notes;
- interactive HTML review;
- design-review mode;
- printable handouts;
- architecture posters;
- audience-specific review views.

These should be considered only after the core Review Pack requirements are established.

---

# Open Questions

Before implementation, the following should be resolved:

- Which document sections are required?
- How should summaries be generated?
- How much content may be transformed versus directly rendered?
- Should diagrams be reused, transformed, or regenerated?
- What output formats are required initially?
- Is a fixed ten-page target appropriate?
- What level of user control is necessary?
- How should the Review Pack remain traceable to its source sections?

No implementation should begin until these questions have sufficient answers.

---

# Guiding Idea

> **One manuscript. Many audiences.**

Books can be rendered differently from technical documents.

Technical documents can be rendered differently for architecture-review audiences.

The author should not have to rewrite the underlying information simply because the audience or presentation changes.

The renderer adapts the presentation while preserving the manuscript as the authoritative source.
