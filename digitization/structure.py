"""Conservative page-level structure classification for digitization.

The classifier operates on OCR text only and deliberately recognizes a small
set of broad page types. It is a routing/review aid, not a claim that OCR text
can reliably reconstruct tables or figures.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re


class PageStructure(StrEnum):
    """Broad structure classes used by the digitization pipeline."""

    PROSE = "prose"
    CODE = "code"
    LAYOUT = "layout"


@dataclass(frozen=True)
class StructureClassification:
    """Classification result with a bounded confidence and reasons."""

    structure: PageStructure
    confidence: float
    reasons: tuple[str, ...] = ()


_CODE_PATTERNS = (
    re.compile(r"^\s*#\s*(?:include|define|ifdef|ifndef|endif|pragma)\b", re.MULTILINE),
    re.compile(r"\b(?:int|char|float|double|void|long|short)\s+[A-Za-z_]\w*\s*(?:[=;(,\[])"),
    re.compile(r"\b(?:if|else|for|while|switch|return)\s*\([^\n]*\)"),
    re.compile(r"\b[A-Za-z_]\w*\s*\([^\n]*\)\s*[;{]"),
)


def classify_structure(text: str) -> StructureClassification:
    """Classify OCR text conservatively as prose, code, or layout.

    Code requires multiple independent signals so ordinary technical prose is
    not easily promoted to a code page. Sparse, title-like text is classified
    as layout only when it has strong display or multi-line layout signals.
    Everything else defaults to prose.
    """

    if not text.strip():
        return StructureClassification(PageStructure.LAYOUT, 0.60, ("empty-text",))

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    words = re.findall(r"\b\w+\b", text)
    code_signals: list[str] = []

    for pattern, reason in zip(
        _CODE_PATTERNS,
        ("preprocessor-directive", "typed-declaration", "control-statement", "function-like-statement"),
    ):
        if pattern.search(text):
            code_signals.append(reason)

    punctuation_density = sum(text.count(ch) for ch in "{}[];=") / max(len(text), 1)
    if punctuation_density >= 0.018:
        code_signals.append("code-punctuation-density")

    if len(code_signals) >= 2:
        confidence = min(0.60 + 0.10 * len(code_signals), 0.90)
        return StructureClassification(PageStructure.CODE, confidence, tuple(code_signals))

    uppercase_words = sum(1 for word in words if len(word) >= 3 and word.isupper())
    short_lines = sum(1 for line in lines if len(line.split()) <= 5)
    layout_signals: list[str] = []
    if len(words) <= 45:
        layout_signals.append("sparse-text")
    if lines and short_lines / len(lines) >= 0.70:
        layout_signals.append("short-lines")
    if uppercase_words >= 2:
        layout_signals.append("display-uppercase")

    strong_layout = "display-uppercase" in layout_signals or len(lines) >= 2
    if len(layout_signals) >= 2 and len(words) <= 80 and strong_layout:
        confidence = min(0.55 + 0.10 * len(layout_signals), 0.80)
        return StructureClassification(PageStructure.LAYOUT, confidence, tuple(layout_signals))

    return StructureClassification(PageStructure.PROSE, 0.50, ())
