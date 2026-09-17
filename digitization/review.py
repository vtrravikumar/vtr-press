"""Review markers for uncertain or structure-sensitive OCR output."""

from __future__ import annotations

import re

from .layout import VisualAnalysis
from .structure import PageStructure, StructureClassification


SUSPICIOUS_PATTERNS = (
    re.compile(r"[\uFFFD]"),
    re.compile(r"\b(?:Il|lI|11)\.[A-Za-z]"),
)


def build_review_markers(
    text: str,
    classification: StructureClassification | None,
    visual_analysis: VisualAnalysis | None = None,
) -> tuple[str, ...]:
    """Return conservative review reasons without altering OCR text."""
    markers: list[str] = []

    if classification is not None:
        if classification.structure is PageStructure.CODE:
            markers.append("code-ocr-verification")
        elif classification.structure is PageStructure.LAYOUT:
            markers.append("layout-visual-verification")
        if classification.structure is not PageStructure.PROSE and classification.confidence < 0.65:
            markers.append("low-structure-confidence")

    if visual_analysis is not None:
        if visual_analysis.table_likely:
            markers.append("table-visual-verification")
        if visual_analysis.diagram_likely:
            markers.append("diagram-visual-verification")
        if visual_analysis.figure_likely:
            markers.append("figure-visual-verification")

    if any(pattern.search(text) for pattern in SUSPICIOUS_PATTERNS):
        markers.append("suspicious-ocr-glyphs")

    return tuple(dict.fromkeys(markers))
