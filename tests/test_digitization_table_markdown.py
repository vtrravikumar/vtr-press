from digitization.table import ExtractedTable, TableCell
from digitization.layout import VisualRegion
from digitization.table_markdown import to_markdown_table


def _table(rows: list[list[str]]) -> ExtractedTable:
    cells = []
    for row, values in enumerate(rows):
        for column, text in enumerate(values):
            cells.append(
                TableCell(
                    row=row,
                    column=column,
                    region=VisualRegion("table-cell", column * 100, row * 100, (column + 1) * 100, (row + 1) * 100),
                    text=text,
                )
            )
    return ExtractedTable(tuple(cells))


def test_table_markdown_requires_explicit_confidence_gate():
    result = to_markdown_table(_table([["Name", "Value"], ["A", "10"]]))
    assert result.publishable is False
    assert result.markdown is None
    assert "table-ocr-confidence-unavailable" in result.reasons


def test_table_markdown_can_serialize_when_caller_sets_low_threshold():
    result = to_markdown_table(
        _table([["Name", "Value"], ["A", "10"], ["B | C", "20"]]),
        minimum_confidence=0.70,
    )
    assert result.publishable is True
    assert result.markdown == (
        "| Name | Value |\n"
        "| --- | --- |\n"
        "| A | 10 |\n"
        "| B \\| C | 20 |"
    )


def test_table_markdown_rejects_incomplete_cells():
    result = to_markdown_table(_table([["Name", "Value"], ["A", ""]]), minimum_confidence=0.0)
    assert result.publishable is False
    assert result.markdown is None
    assert "table-incomplete-cells" in result.reasons
