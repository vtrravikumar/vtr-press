"""Conservative Markdown serialization for digitized tables.

The serializer only converts an extracted table when its structural and OCR
quality gates are satisfied. Otherwise callers should retain the source-page
image and review the extraction manually.
"""

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
    """Escape Markdown table syntax without changing ordinary OCR text."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def to_markdown_table(
    table: ExtractedTable,
    *,
    minimum_confidence: float = 0.80,
    require_complete: bool = True,
) -> TableMarkdownResult:
    """Serialize an extracted table only when conservative gates pass.

    The first detected row is emitted as the Markdown header because Markdown
    requires a header row. This is intentionally a policy decision rather than
    an attempt to infer semantic headers. Callers should therefore use this
    only when the source layout/review process establishes that row 1 is a
    header.
    """
    if not table.cells:
        return TableMarkdownResult(None, 0.0, ("table-empty",))

    rows = table.rows()
    if not rows or table.row_count < 2 or table.column_count < 1:
        return TableMarkdownResult(None, 0.0, ("table-structure-insufficient",))

    complete = all(cell.strip() for row in rows for cell in row)
    if require_complete and not complete:
        return TableMarkdownResult(None, 0.40, ("table-incomplete-cells",))

    # Extraction currently carries no OCR confidence score. Until one exists,
    # only complete tables with structurally valid dimensions can pass. The
    # fixed score is deliberately below the default publication threshold.
    confidence = 0.70 if complete else 0.40
    if confidence < minimum_confidence:
        return TableMarkdownResult(
            None,
            confidence,
            ("table-ocr-confidence-unavailable",),
        )

    header = "| " + " | ".join(_escape_cell(value) for value in rows[0]) + " |"
    separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
    body = [
        "| " + " | ".join(_escape_cell(value) for value in row) + " |"
        for row in rows[1:]
    ]
    return TableMarkdownResult("\n".join([header, separator, *body]), confidence)
