"""
Custom exceptions for the publication engine.

All publication-specific exceptions derive from PublicationError.
"""

from __future__ import annotations


class PublicationError(Exception):
    """Base class for all publication engine errors."""


class ParseError(PublicationError):
    """Base class for parsing errors."""


class FrontMatterError(ParseError):
    """Raised when the YAML front matter is missing or invalid."""


class StructureError(ParseError):
    """Raised when the document structure is invalid."""