# New VTR Press Capability
## Architecture Review Pack
### Problem
A Solution Architecture Document is comprehensive and authoritative, but it is not the ideal format for an Architecture Review Board, Steering Committee, or Technical Design Authority meeting.
Reviewers typically require a concise, high-level summary that can be read within 10–15 minutes while still remaining faithful to the underlying architecture.
Maintaining a separate presentation introduces duplication and creates the risk of the review material diverging from the authoritative Solution Architecture Document.
### Solution
VTR Press shall support generation of an Architecture Review Pack directly from a Solution Architecture manuscript.
The Review Pack is a derived artifact, not a separate source document.

Solution Architecture.md
        │
        ▼
    VTR Press
        │
        ├── Solution Architecture.pdf
        ├── Solution Architecture.epub
        └── Architecture Review.pdf

The Solution Architecture Document remains the single source of truth.

### Engineering Principles
The feature shall follow the same engineering principles already established for VTR Press.
Single Source of Truth
Convention over Configuration
Separation of Content and Presentation
No Information Duplication
Renderer Owns Presentation

### Proposed Document Type
Rather than introducing another manuscript, the renderer should expose another output target.
Example:
vtr-press render Solution Architecture.md --pdf

vtr-press render Solution Architecture.md --epub

vtr-press review Solution Architecture.md

The input remains unchanged.
Only the output differs.
Default Review Structure

The generated review should contain approximately ten pages.
Cover
Executive Summary
Business Vision
Business Architecture
Domain Architecture
High-Level Architecture
Technology Overview
Key Architecture Decisions
Deployment & Security Summary
Conclusions / Questions
The renderer should automatically extract the relevant sections from the Solution Architecture Document.
Author Experience

The architect writes only one document.
Solution Architecture.md

The Review Pack is generated automatically.
No presentation needs to be maintained.

## Future Enhancements
The Architecture Review Pack may later support:
Executive Summary
Speaker Notes
Interactive HTML Review
Design Review Mode
Printable Handouts
Architecture Posters
All generated from the same manuscript.
Why I like this
This is much bigger than a PDF.
It establishes a philosophy for VTR Press:
One manuscript. Many audiences.

Books are rendered differently from technical documents.
Technical documents are rendered differently from architecture reviews.
The author does not rewrite content for each audience.
The renderer adapts the presentation while preserving the underlying information.