"""Conservative Markdown serialization for digitized tables."""

from __future__ import annotations

from dataclasses import dataclass

from .table import ExtractedTable


@dataclass(frozen=True)
class TableMarkdownResult:
    """Markdown candidate plus the reasons it is or is not publishable."""
    markdown: str | None
    confidence: float
    reasons: tuple[str, ...] = ()

    @property
    def publishable(self) -> bool:
        return self.markdown is not None


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def to_markdown_table(
    table: ExtractedTable,
    *,
    minimum_confidence: float = 0.80,
    require_complete: bool = True,
) -> TableMarkdownResult:
    """Serialize an extracted table only when conservative gates pass.

    The first row is emitted as a Markdown header only when the caller's
    workflow has established that it is a header. This function does not infer
    semantic headers, merged cells, or spanning cells.
    """
    if not table.cells:
        return TableMarkdownResult(None, 0.0, ("table-empty",))

    rows = table.rows()
    if not rows or table.row_count < 2 or table.column_count < 1:
        return TableMarkdownResult(None, 0.0, ("table-structure-insufficient",))

    complete = all(cell.strip() for row in rows for cell in row)
    if require_complete and not complete:
        return TableMarkdownResult(None, 0.40, ("table-incomplete-cells",))

    confidence = table.confidence()
    if confidence is None:
        return TableMarkdownResult(None, 0.0, ("table-ocr-confidence-unavailable",))
    if confidence < minimum_confidence:
        return TableMarkdownResult(None, confidence, ("table-ocr-confidence-low",))

    header = "| " + " | ".join(_escape_cell(value) for value in rows[0]) + " |"
    separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
    body = [
        "| " + " | ".join(_escape_cell(value) for value in row) + " |"
        for row in rows[1:]
    ]
    return TableMarkdownResult("\n".join([header, separator, *body]), confidence)
