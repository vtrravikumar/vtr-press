"""Shared EPUB rendering primitives.

This module contains rendering behavior shared by the Book and
Technical-document EPUB renderers.

Document-type-specific structure remains in the concrete renderers.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from model import (
    Block,
    Bold,
    Code,
    CodeBlock,
    Image,
    Inline,
    Italic,
    LineBreak,
    Link,
    ListBlock,
    Paragraph,
    Table,
    TableAlignment,
    TableCell,
    Text,
    Verse,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGO = ROOT / "assets" / "publisher" / "logo.png"

EPUB_CSS = """
html {
  margin: 0;
  padding: 0;
}

body {
  color: #161616;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1em;
  line-height: 1.45;
  margin: 0;
  padding: 1.4em;
}

.cover {
  margin: 0;
  padding: 0;
  text-align: center;
}

.cover img {
  height: auto;
  max-height: 100%;
  max-width: 100%;
  width: auto;
}

.title-page {
  margin-top: 18%;
  text-align: center;
}

.title-page p {
  text-align: center;
}

.title-page h1 {
  font-size: 2em;
  line-height: 1.15;
  margin: 0 0 0.45em;
}

.subtitle {
  font-size: 1.2em;
  margin: 0 0 3em;
}

.author {
  font-size: 1.15em;
  margin: 0 0 6em;
}

.copyright {
  font-size: 0.9em;
  margin-top: 1em;
}

.publisher-logo {
  display: block;
  height: auto;
  margin: 4em auto 0.8em;
  max-width: 24mm;
  width: 24mm;
}

h1,
h2,
h3 {
  font-weight: bold;
  line-height: 1.2;
  margin: 0 0 1.2em;
}

h1 {
  font-size: 1.8em;
  margin-top: 35%;
  text-align: center;
}

h2 {
  font-size: 1.55em;
  margin-top: 1.2em;
}

h3.scene {
  font-size: 1.05em;
  margin: 1.6em 0 0.8em;
}

.contents h1 {
  margin-top: 0;
  text-align: left;
}

p {
  margin: 0 0 1em;
  text-align: justify;
}

.verse {
  margin: 1em 0 1.2em 1.5em;
}

.verse p {
  margin: 0;
  text-align: left;
}

pre {
  white-space: pre;
  overflow-x: auto;
}

code {
  font-family: "Courier New", monospace;
  font-size: 0.92em;
}

a {
  color: inherit;
}

nav ol {
  list-style-type: none;
  margin: 0;
  padding-left: 0;
}

nav ol ol {
  margin-top: 0.35em;
  padding-left: 1.4em;
}

nav li {
  margin: 0.35em 0;
}

.contents ol {
  list-style-type: none;
  margin: 0;
  padding-left: 0;
}

.contents ol ol {
  margin-top: 0.35em;
  padding-left: 1.4em;
}

.contents li {
  margin: 0.35em 0;
}
""".strip()

class EpubCommonMixin:
    """Shared EPUB rendering primitives."""

    # ------------------------------------------------------------------
    # Block
    # ------------------------------------------------------------------

    def _render_block(self, block: Block) -> str:
        if isinstance(block, Paragraph):
            return self._render_paragraph(block)

        if isinstance(block, Verse):
            return self._render_verse(block)

        if isinstance(block, ListBlock):
            return self._render_list(block)

        if isinstance(block, Image):
            return self._render_image(block)

        if isinstance(block, CodeBlock):
            return self._render_code_block(block)

        if isinstance(block, Table):
            return self._render_table(block)

        raise TypeError(f"Unsupported block: {type(block).__name__}")

    # ------------------------------------------------------------------
    # Paragraph
    # ------------------------------------------------------------------

    def _render_paragraph(self, paragraph: Paragraph) -> str:
        """Render a paragraph, preserving numbered reference-list lines."""

        content = "".join(
            self._render_inline(node)
            for node in paragraph.children
        )

        lines = content.split("\n")

        if (
            len(lines) > 1
            and all(
                not line.strip()
                or line.lstrip().split(".", 1)[0].isdigit()
                and line.lstrip().split(".", 1)[1].startswith(" ")
                for line in lines
            )
        ):
            content = "<br/>".join(lines)

        return f"<p>{content}</p>"

    # ------------------------------------------------------------------
    # Verse
    # ------------------------------------------------------------------

    def _render_verse(self, verse: Verse) -> str:
        """Render a verse preserving line breaks."""

        lines = ['<div class="verse">']

        for line in verse.lines:
            lines.append(f"<p>{_text(line)}</p>")

        lines.append("</div>")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    def _render_list(self, block: ListBlock) -> str:
        """Render an ordered or unordered list."""

        tag = "ol" if block.ordered else "ul"
        lines = [f"<{tag}>"]

        for item in block.items:
            content = "".join(
                self._render_inline(node)
                for node in item.children
            )
            lines.append(f"<li>{content}</li>")

        lines.append(f"</{tag}>")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Image
    # ------------------------------------------------------------------

    def _render_image(self, block: Image) -> str:
        """Render an image using the shared document asset resolver."""

        if self.document_assets is None:
            raise ValueError("Image rendering requires document assets.")

        asset = self.document_assets.resolve(block.source)

        if asset is None:
            return (
                f'<p class="missing-image">'
                f"{_text(block.alt_text)}"
                "</p>"
            )

        return (
            "<figure>"
            f'<img src="{_attr(asset.epub_href)}" '
            f'alt="{_attr(block.alt_text)}"/>'
            "</figure>"
        )

    # ------------------------------------------------------------------
    # Code Block
    # ------------------------------------------------------------------

    def _render_code_block(self, block: CodeBlock) -> str:
        """Render a fenced code block as an EPUB preformatted block."""

        language = _attr(block.language.strip())
        class_attr = f' class="language-{language}"' if language else ""

        content = _text("\n".join(block.lines))

        return f"<pre{class_attr}><code>{content}</code></pre>"

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _render_table(self, table: Table) -> str:
        """Render a generic table using native HTML table elements."""

        lines = [
            "<table>",
            "<thead>",
            "<tr>",
        ]

        for index, cell in enumerate(table.header.cells):
            alignment = table.alignments[index]
            lines.append(
                f'<th style="text-align: '
                f'{self._render_table_alignment(alignment)}">'
                f"{self._render_table_cell(cell)}</th>"
            )

        lines.extend(
            [
                "</tr>",
                "</thead>",
                "<tbody>",
            ]
        )

        for row in table.rows:
            lines.append("<tr>")

            for index, cell in enumerate(row.cells):
                alignment = table.alignments[index]
                lines.append(
                    f'<td style="text-align: '
                    f'{self._render_table_alignment(alignment)}">'
                    f"{self._render_table_cell(cell)}</td>"
                )

            lines.append("</tr>")

        lines.extend(
            [
                "</tbody>",
                "</table>",
            ]
        )

        return "\n".join(lines)

    def _render_table_alignment(
        self,
        alignment: TableAlignment,
    ) -> str:
        """Return the HTML text-alignment value."""

        return alignment.value

    def _render_table_cell(self, cell: TableCell) -> str:
        """Render the inline contents of a table cell."""

        return "".join(
            self._render_inline(node)
            for node in cell.children
        )

    # ------------------------------------------------------------------
    # Inline
    # ------------------------------------------------------------------

    def _render_inline(self, node: Inline) -> str:
        """Render an inline element."""

        if isinstance(node, Text):
            return _text(node.text)

        if isinstance(node, Bold):
            return (
                "<strong>"
                + "".join(
                    self._render_inline(child)
                    for child in node.children
                )
                + "</strong>"
            )

        if isinstance(node, Italic):
            return (
                "<em>"
                + "".join(
                    self._render_inline(child)
                    for child in node.children
                )
                + "</em>"
            )

        if isinstance(node, Code):
            return f"<code>{_text(node.text)}</code>"

        if isinstance(node, Link):
            return (
                f'<a href="{_attr(node.url)}">'
                f"{_text(node.text)}</a>"
            )

        if isinstance(node, LineBreak):
            return "<br/>"

        raise TypeError(
            f"Unsupported inline: {type(node).__name__}"
        )

    # ------------------------------------------------------------------
    # Plain-text inspection
    # ------------------------------------------------------------------

    def _inline_plain_text(self, node: Inline) -> str:
        """Return plain text for renderer-level publication checks."""

        return _inline_plain_text(node)

    def _is_empty_isbn_paragraph(self, block: Block) -> bool:
        """Return whether a paragraph is only an empty ISBN placeholder."""

        if not isinstance(block, Paragraph):
            return False

        text = "".join(
            self._inline_plain_text(node)
            for node in block.children
        )

        return text.strip().casefold() in {"isbn", "isbn:"}


def _inline_plain_text(node: Inline) -> str:
    """Return plain text from an inline node."""

    if isinstance(node, Text):
        return node.text

    if isinstance(node, (Bold, Italic)):
        return "".join(
            _inline_plain_text(child)
            for child in node.children
        )

    if isinstance(node, Code):
        return node.text

    if isinstance(node, Link):
        return node.text

    if isinstance(node, LineBreak):
        return "\n"

    return ""


def _text(value: object) -> str:
    """Escape text for XML content."""

    return escape(_plain(value), quote=False)


def _attr(value: object) -> str:
    """Escape text for XML attributes."""

    return escape(_plain(value), quote=True)


def _plain(value: object) -> str:
    """Return a safe string value for metadata and content."""

    if value is None:
        return ""

    return str(value)