"""
Interpretation layer for the generic Document Model (Phase D).

Per docs/DOCUMENT_MODEL_DESIGN.md: the parser (once built in D2)
describes what the author wrote -- headings by level and title,
paragraphs, verse. This module is where document-type conventions
decide what a given heading MEANS: is a level-2 heading a Part, a
Section, a Copyright page, something else? Does it participate in
the outline? Where does main matter begin?

This is a small, dedicated module -- Gap 2 in the D0 design note,
resolved: interpretation lives here, not inside renderer/typst.py or
renderer/epub.py.

Scope note (D1): the interpret_book() / interpret_technical_document()
functions below are deliberately minimal and illustrative -- just
enough to prove, with real executable code and tests rather than only
prose, that the model can represent both current document types'
structural rules (docs/DOCUMENT_MODEL_DESIGN.md sections 3-4). They
are NOT the production D2/D3 interpretation layer: they don't cover
every SECTION_MAP entry, don't perform structural validation (e.g.
"Scene requires Chapter"), and are never called by parser/, renderer/,
publish.py, or run.py. Building that out is D2/D3 work.

Nothing in this module is wired into the current publishing pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from model import Block, Document, Heading, Metadata


class NodeKind(Enum):
    """
    The semantic role a heading can play, generalized across every
    document type this migration currently supports. Not every kind
    applies to every type -- PART/CHAPTER/SCENE are book-only
    conventions; SECTION/SUBSECTION/APPENDIX are technical-document
    conventions. Which apply, and how a heading is matched to one, is
    decided per-type by the interpret_*() functions below.
    """

    # Book conventions (docs/DOCUMENT_MODEL_DESIGN.md section 3)
    PART = auto()
    CHAPTER = auto()
    SCENE = auto()
    COPYRIGHT = auto()
    DEDICATION = auto()
    THIRUKKURAL = auto()
    PROLOGUE = auto()
    PREFACE = auto()
    FOREWORD = auto()
    ACKNOWLEDGEMENTS = auto()
    EPILOGUE = auto()
    ABOUT_AUTHOR = auto()
    BACK_COVER = auto()

    # Technical-document conventions (docs/DOCUMENT_MODEL_DESIGN.md section 4)
    SECTION = auto()
    SUBSECTION = auto()
    APPENDIX = auto()

    # Shared fallback for either type
    OTHER = auto()


# Headings whose kind excludes them from the outline, for book
# interpretation -- the exact set renderer/typst.py's existing
# `outlined = section.kind not in {...}` already uses, relocated here
# rather than duplicated with different membership by accident.
_BOOK_FRONT_MATTER_KINDS = frozenset(
    {NodeKind.COPYRIGHT, NodeKind.DEDICATION, NodeKind.THIRUKKURAL}
)

# Title -> NodeKind, for book interpretation's top-level (non-Part,
# non-Chapter) headings. Mirrors parser/structure.py's SECTION_MAP,
# relocated to where D0 says this kind of lookup belongs: an
# interpretation-layer convention table, not a parser constant.
_BOOK_SECTION_MAP: dict[str, NodeKind] = {
    "copyright": NodeKind.COPYRIGHT,
    "dedication": NodeKind.DEDICATION,
    "thirukkural": NodeKind.THIRUKKURAL,
    "prologue": NodeKind.PROLOGUE,
    "preface": NodeKind.PREFACE,
    "foreword": NodeKind.FOREWORD,
    "acknowledgements": NodeKind.ACKNOWLEDGEMENTS,
    "epilogue": NodeKind.EPILOGUE,
    "about the author": NodeKind.ABOUT_AUTHOR,
    "back cover": NodeKind.BACK_COVER,
}


@dataclass(slots=True)
class InterpretedNode:
    """
    One raw parsed block, annotated with the semantic meaning
    interpretation assigned it for a given document type. A parallel,
    still-flat structure -- not a tree. This is the "annotate in
    place" shape from Gap 1 of docs/DOCUMENT_MODEL_DESIGN.md, chosen
    over reconstructing a grouped Section/Part-like structure, so
    that interpretation's output stays exactly as flat as its input.
    """

    block: Block
    kind: NodeKind | None = None
    outlined: bool = False


@dataclass(slots=True)
class InterpretedDocument:
    """
    The fully-interpreted Document Model: metadata plus an ordered,
    flat list of InterpretedNode entries. Per
    docs/DOCUMENT_MODEL_DESIGN.md section 2, both the Typst and EPUB
    renderers are intended to eventually consume this same structure
    -- not built yet; that's D3.
    """

    metadata: Metadata = field(default_factory=Metadata)
    nodes: list[InterpretedNode] = field(default_factory=list)

    def first_outlined_node(self) -> InterpretedNode | None:
        """
        The first node with outlined=True, if any -- the same
        type-agnostic "first outlined section" computation
        renderer/typst.py (VP-005/B1) and renderer/epub.py (B3) each
        independently implement today, one triggering Contents
        insertion and main-matter numbering. Under this model, it's
        computed once, here, regardless of document type -- exactly
        the kind of per-renderer drift docs/DOCUMENT_MODEL_DESIGN.md
        cites as concrete evidence for this design (the EPUB/Typst
        PROLOGUE divergence found while researching D0).
        """

        for node in self.nodes:
            if node.outlined:
                return node

        return None


def interpret_book(document: Document) -> InterpretedDocument:
    """
    Minimal, illustrative book interpretation (see module docstring
    for scope). Walks a flat Document and assigns NodeKind to each
    Heading, following the rules validated in
    docs/DOCUMENT_MODEL_DESIGN.md section 3:

    - A level-2 heading titled "Part ..." -> PART.
    - A level-3 heading, when the nearest preceding top-level heading
      (with no intervening level-2) was a PART -> CHAPTER.
    - A level-4 heading under a CHAPTER -> SCENE.
    - A level-2 heading matching _BOOK_SECTION_MAP -> that kind.
    - Any other level-2 heading -> OTHER.
    - outlined is False only for COPYRIGHT/DEDICATION/THIRUKKURAL,
      matching renderer/typst.py's existing computation exactly.

    Does not perform structural validation (e.g. "Scene requires
    Chapter") -- that's D2/D3 scope, not D1's.
    """

    nodes: list[InterpretedNode] = []
    current_top_level_kind: NodeKind | None = None

    for block in document.blocks:

        if not isinstance(block, Heading):
            nodes.append(InterpretedNode(block=block))
            continue

        if block.level == 2:

            if block.title.lower().startswith("part "):
                kind = NodeKind.PART
            else:
                key = block.title.strip().lower()
                kind = _BOOK_SECTION_MAP.get(key, NodeKind.OTHER)

            current_top_level_kind = kind
            outlined = kind not in _BOOK_FRONT_MATTER_KINDS
            nodes.append(
                InterpretedNode(block=block, kind=kind, outlined=outlined)
            )
            continue

        if block.level == 3 and current_top_level_kind == NodeKind.PART:
            nodes.append(
                InterpretedNode(
                    block=block, kind=NodeKind.CHAPTER, outlined=True
                )
            )
            continue

        if block.level == 4:
            nodes.append(
                InterpretedNode(
                    block=block, kind=NodeKind.SCENE, outlined=True
                )
            )
            continue

        nodes.append(InterpretedNode(block=block, kind=NodeKind.OTHER))

    return InterpretedDocument(metadata=document.metadata, nodes=nodes)


def interpret_technical_document(document: Document) -> InterpretedDocument:
    """
    Minimal, illustrative technical-document interpretation (see
    module docstring for scope). Walks a flat Document and assigns
    NodeKind following the rules validated in
    docs/DOCUMENT_MODEL_DESIGN.md section 4:

    - Every level-2 heading -> SECTION, outlined=True (numbered
      sections; no front-matter-kind exclusions exist for this type
      today).
    - Every level-3+ heading -> SUBSECTION, not outlined (mirrors
      Subheading's existing, non-outlined rendering).
    - "Appendix"-titled sections are not special-cased -- they remain
      ordinary SECTION nodes, exactly as SECTION_MAP already treats
      them (falls through to SectionKind.OTHER today).
    """

    nodes: list[InterpretedNode] = []

    for block in document.blocks:

        if not isinstance(block, Heading):
            nodes.append(InterpretedNode(block=block))
            continue

        if block.level == 2:
            nodes.append(
                InterpretedNode(
                    block=block, kind=NodeKind.SECTION, outlined=True
                )
            )
            continue

        nodes.append(
            InterpretedNode(
                block=block, kind=NodeKind.SUBSECTION, outlined=False
            )
        )

    return InterpretedDocument(metadata=document.metadata, nodes=nodes)
