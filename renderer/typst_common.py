"""
Common Typst rendering primitives shared by document renderers.

This module contains rendering behavior that operates on the generic
Document Model rather than on Book-specific structure.

Document-type-specific structure and publication behavior remain in
the individual renderers.
"""

from __future__ import annotations
from pathlib import Path
from model import (
    Block,
    Bold,
    Code,
    CodeBlock,
    Image,
    Inline,
    Italic,
    Link,
    Paragraph,
    Text,
    Verse,
    ListBlock,
)


class TypstCommonMixin:
    """Common Typst rendering primitives."""

    # ------------------------------------------------------------------
    # Generic blocks
    # ------------------------------------------------------------------

    def _render_paragraph(self, paragraph: Paragraph) -> str:
        """Render a paragraph."""

        return "".join(
            self._render_inline(node)
            for node in paragraph.children
        )

    def _render_verse(self, verse: Verse) -> None:
        """Render a verse preserving line breaks."""

        self.lines.append("#block[")

        for index, line in enumerate(verse.lines):
            self.lines.append(self._escape_text(line))

            if index < len(verse.lines) - 1:
                self.lines.append("#linebreak()")

        self.lines.append("]")
        self.lines.append("")

    def _render_code_block(self, code: CodeBlock) -> None:
        """Render a fenced code block as a Typst raw block."""

        content = "\n".join(code.lines)
        language = code.language.strip()

        if language:
            self.lines.append(
                f'#raw(lang: "{self._escape_string(language)}", '
                f'block: true, '
                f'"{self._escape_string(content)}")'
            )
        else:
            self.lines.append(
                f'#raw(block: true, '
                f'"{self._escape_string(content)}")'
            )

        self.lines.append("")

    def _render_list(self, block: ListBlock) -> None:
        """Render a generic ordered or unordered list using native Typst."""

        marker = "+" if block.ordered else "-"

        for item in block.items:
            rendered = "".join(
                self._render_inline(child)
                for child in item.children
            )
            self.lines.append(f"{marker} {rendered}")

        self.lines.append("")

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------
    def _render_image(self, block: Image) -> None:
        """Render an image using the generic document asset layout."""

        if self.document_assets is None:
            raise ValueError(
                "Image rendering requires document assets."
            )

        asset = self.document_assets.resolve(block.source)

        if asset is None:
            self.lines.append(
                f'#text("[Missing image: '
                f'{self._escape_string(block.alt_text)}]")'
            )
            self.lines.append("")
            return

        staging_root = self.document_assets.staging_root
        assets_index = staging_root.parts.index("assets")

        typst_asset_path = Path(
            *staging_root.parts[assets_index:],
            "images",
            asset.staged_path.name,
        )

        self.lines.append(
            f'#image("{self._escape_string(str(typst_asset_path))}")'
        )
        self.lines.append("")
    # ------------------------------------------------------------------
    # Inline
    # ------------------------------------------------------------------

    def _render_inline(self, node: Inline) -> str:
        """Render a generic inline element."""

        if isinstance(node, Text):
            return self._escape_text(node.text)

        if isinstance(node, Bold):
            return (
                "*"
                + "".join(
                    self._render_inline(child)
                    for child in node.children
                )
                + "*"
            )

        if isinstance(node, Italic):
            return (
                "_"
                + "".join(
                    self._render_inline(child)
                    for child in node.children
                )
                + "_"
            )

        if isinstance(node, Code):
            return f"`{self._escape_text(node.text)}`"

        if isinstance(node, Link):
            return (
                f'link("{self._escape_string(node.url)}")'
                f"[{self._escape_text(node.text)}]"
            )

        raise TypeError(
            f"Unsupported inline: {type(node).__name__}"
        )

    # ------------------------------------------------------------------
    # Generic text helpers
    # ------------------------------------------------------------------

    def _inline_plain_text(self, node: Inline) -> str:
        """Return the plain text represented by an inline node."""

        if isinstance(node, Text):
            return node.text

        if isinstance(node, Bold):
            return "".join(
                self._inline_plain_text(child)
                for child in node.children
            )

        if isinstance(node, Italic):
            return "".join(
                self._inline_plain_text(child)
                for child in node.children
            )

        if isinstance(node, Code):
            return node.text

        if isinstance(node, Link):
            return node.text

        return ""

    def _is_empty_isbn_paragraph(self, block: Block) -> bool:
        """Return whether a paragraph is only an empty ISBN placeholder."""

        if not isinstance(block, Paragraph):
            return False

        text = "".join(
            self._inline_plain_text(node)
            for node in block.children
        )

        return text.strip().casefold() in {"isbn", "isbn:"}