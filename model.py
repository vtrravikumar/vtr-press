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

    paper: str = ""
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