"""Render the generic Document Model to Typst.

This renderer is the native Typst consumer for the Phase D generic
Document Model. It consumes an InterpretedDocument directly; it never
reconstructs the legacy Book/Part/Chapter/Section tree.

D3 scope: technical-document only. The existing book renderer remains
unchanged and continues to consume Book.
"""

from __future__ import annotations

from pathlib import Path

from interpretation import InterpretedDocument, InterpretedNode, NodeKind
from model import Heading, Image, Metadata
from renderer.document_assets import DocumentAssets
from renderer.typst import RenderOptions, _Renderer


def render_document(
    document: InterpretedDocument,
    options: RenderOptions | None = None,
    assets: DocumentAssets | None = None,
) -> str:
    """Render an interpreted technical document to Typst source."""
    renderer = _DocumentRenderer(options, assets)
    return renderer.render_document(document)


class _DocumentRenderer(_Renderer):
    """Native Typst renderer for the generic Document Model."""

    def __init__(
        self,
        options: RenderOptions | None = None,
        assets: DocumentAssets | None = None,
    ) -> None:
        # Technical documents have no cover. The inherited renderer helpers
        # use this value only if the legacy cover path is invoked, which this
        # renderer never does.
        super().__init__(
            cover_path="",
            options=options,
            document_assets=assets,
        )
        self._document_section_open = False

    def _render_image(self, block: Image) -> None:
        """Render a technical-document image from staged assets."""
        if self.document_assets is None:
            raise ValueError("Image rendering requires document assets.")

        asset = self.document_assets.resolve(block.source)

        if asset is None:
            self.lines.append(
                f'#text("[Missing image: {self._escape_string(block.alt_text)}]")'
            )
            self.lines.append("")
            return

        typst_asset_path = (
            Path("assets")
            / "documents"
            / self.document_assets.staging_root.name
            / "images"
            / asset.staged_path.name
        )

        self.lines.append(
            f'#image("{self._escape_string(str(typst_asset_path))}")'
        )
        self.lines.append("")

    def render_document(self, document: InterpretedDocument) -> str:
        if document.metadata.type != "technical-document":
            raise ValueError(
                "render_document() currently supports only technical-document"
            )

        self._render_document_preamble(document.metadata)
        self._render_title_page_from_metadata(document.metadata)

        # Contents is deliberately emitted before main matter so the
        # technical theme's outline can collect the sections that follow.
        self._render_contents()
        self.lines.append("#pagebreak()")
        self.lines.append("")

        self._start_main_matter()

        for node in document.nodes:
            self._render_interpreted_node(node)

        if self._document_section_open:
            self.lines.append("]")
            self.lines.append("")

        if self._main_matter_open:
            self.lines.append("]")

        return "\n".join(self.lines).rstrip() + "\n"

    def _render_document_preamble(self, metadata: Metadata) -> None:
        self.lines.append('#import "../themes/technical/theme.typ": *')
        self.lines.append("")
        self.lines.append("#show: initialize-theme.with(")
        self.lines.append(
            f'  book-title: "{self._escape_string(metadata.title)}",'
        )
        self.lines.append(
            f'  book-author: "{self._escape_string(metadata.author)}",'
        )
        self.lines.append(")")
        self.lines.append("")

    def _render_title_page_from_metadata(self, metadata: Metadata) -> None:
        self.lines.append("#render-title-page(")
        self.lines.append(
            f'  title: "{self._escape_string(metadata.title)}",'
        )
        self.lines.append(
            f'  subtitle: "{self._escape_string(metadata.subtitle)}",'
        )
        self.lines.append(
            f'  author: "{self._escape_string(metadata.author)}",'
        )
        self.lines.append(
            f'  copyright-year: '
            f'"{self._escape_string(metadata.copyright_year)}",'
        )
        self.lines.append("  show-publisher-logo: true,")
        self.lines.append(")")
        self.lines.append("")
        self.lines.append("#pagebreak()")
        self.lines.append("")

    def _render_interpreted_node(self, node: InterpretedNode) -> None:
        block = node.block

        if isinstance(block, Heading):
            self._render_document_heading(block, node.kind, node.outlined)
            return

        if node.kind == NodeKind.SECTION:
            raise TypeError("SECTION nodes must wrap Heading blocks")

        if self._document_section_open:
            self._render_block(block)
        else:
            # The technical-document contract normally begins with a
            # section. Preserve any leading paragraph/verse rather than
            # silently discarding it.
            self._render_block(block)

    def _render_document_heading(
        self,
        heading: Heading,
        kind: NodeKind,
        outlined: bool,
    ) -> None:
        if kind == NodeKind.OTHER and heading.level == 1:
            # The publication title is already rendered by the metadata
            # title page. The level-1 Markdown heading remains in the
            # generic model for structural fidelity but is not duplicated.
            return

        if kind == NodeKind.SECTION:
            if self._document_section_open:
                self.lines.append("]")
                self.lines.append("")
                self.lines.append("#pagebreak()")
                self.lines.append("")

            self.lines.append(
                f'#running-section-page("{self._escape_string(heading.title)}")['
            )
            self.lines.append("")
            self._render_heading(
                heading.level,
                heading.title,
                outlined=outlined,
            )
            self.lines.append("")
            self._document_section_open = True
            return

        self._render_heading(
            heading.level,
            heading.title,
            outlined=outlined,
        )
        self.lines.append("")