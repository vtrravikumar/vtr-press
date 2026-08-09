"""
Document model for the publication engine.

This module defines the canonical in-memory representation of a book.

The model is intentionally independent of Markdown, Typst, HTML,
or any other file format.

Parsers create this model.
Renderers consume this model.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum, auto


# ============================================================================
# Metadata
# ============================================================================

# The document types the publishing engine currently understands. Any
# other value in a manuscript's `type` front matter field is rejected
# at parse time (see parser/reader.py) rather than silently falling
# back to a default -- this is also the single source of truth for
# renderer/typst.py's THEME_IMPORT_BY_TYPE, which must have exactly
# these keys.
SUPPORTED_DOCUMENT_TYPES = ("book", "technical-document")


@dataclass(slots=True)
class Metadata:
    """Book metadata extracted from YAML."""

    title: str = ""
    subtitle: str = ""
    author: str = ""

    type: str = "book"

    edition: str = ""
    version: str = ""

    copyright_year: str = ""

    language: str = ""


# ============================================================================
# Inline Elements
# ============================================================================

class Inline(ABC):
    """Base class for all inline elements."""


@dataclass(slots=True)
class Text(Inline):
    """Plain text."""

    text: str


@dataclass(slots=True)
class Bold(Inline):
    """Bold text."""

    children: list[Inline] = field(default_factory=list)


@dataclass(slots=True)
class Italic(Inline):
    """Italic text."""

    children: list[Inline] = field(default_factory=list)


@dataclass(slots=True)
class Code(Inline):
    """Inline code."""

    text: str


@dataclass(slots=True)
class Link(Inline):
    """Hyperlink."""

    text: str
    url: str


@dataclass(slots=True)
class LineBreak(Inline):
    """Explicit line break."""


# ============================================================================
# Block Elements
# ============================================================================

class Block(ABC):
    """Base class for all block elements."""


@dataclass(slots=True)
class Paragraph(Block):
    """A paragraph consisting of inline elements."""

    children: list[Inline] = field(default_factory=list)

@dataclass(slots=True)
class Verse(Block):
    """A block that preserves line breaks exactly."""

    lines: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Subheading(Block):
    """
    A heading (level 3 or deeper) that appears directly within a
    Section rather than within a Part/Chapter. Used for numbered
    subsections in non-narrative documents (e.g. "1.1 Purpose" under
    "1. Introduction"), where the manuscript has no Part context for
    the existing Chapter/Scene grammar to attach to.

    This is an additive, flat block -- it does not introduce nesting.
    Subsequent Paragraph/Verse/Subheading blocks in the same Section's
    `blocks` list simply follow it in document order, the same way
    Paragraph and Verse already coexist there.
    """

    title: str = ""
    level: int = 3

# ============================================================================
# Section Kinds
# ============================================================================

class SectionKind(Enum):
    """Supported non-part level-2 sections."""

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
    OTHER = auto()


# ============================================================================
# Sections
# ============================================================================

@dataclass(slots=True)
class Section:
    """
    A top-level section that is not a Part.
    """

    kind: SectionKind
    title: str
    blocks: list[Block] = field(default_factory=list)


# ============================================================================
# Scenes
# ============================================================================


@dataclass(slots=True)
class Scene:
    """
    A logical subdivision within a chapter.

    Scenes are rendered inline and are intentionally excluded
    from the Table of Contents.
    """

    title: str | None = None
    blocks: list[Block] = field(default_factory=list)

# ============================================================================
# Chapters
# ============================================================================


@dataclass(slots=True)
class Chapter:
    """
    A chapter within a Part.

    A chapter contains one or more scenes. Older manuscripts
    without explicit scene headings automatically receive a
    single untitled scene during parsing.
    """

    number: int
    title: str
    scenes: list[Scene] = field(default_factory=list)


# ============================================================================
# Parts
# ============================================================================

@dataclass(slots=True)
class Part:
    """A book part containing one or more chapters."""

    title: str
    chapters: list[Chapter] = field(default_factory=list)


# ============================================================================
# Book
# ============================================================================

@dataclass(slots=True)
class Book:
    """The root document."""

    metadata: Metadata
    sections: list[Section | Part] = field(default_factory=list)