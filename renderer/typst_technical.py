"""Render Technical Document → Typst

This renderer is the native Typst consumer for the Phase D generic
Document Model. It consumes an InterpretedDocument directly; it never
reconstructs the legacy Book/Part/Chapter/Section tree.

D3 scope: technical-document only. The existing book renderer remains
unchanged and continues to consume Book.
"""

from __future__ import annotations

from pathlib import Path

from interpretation import InterpretedDocument, InterpretedNode, NodeKind
from model import (
    Block,
    Heading,
    Metadata,
    Table,
    TableAlignment,
    TableCell,
)
from renderer.document_assets import DocumentAssets
from renderer.typst_book import RenderOptions, TypstBookRenderer


def render_document(
    document: InterpretedDocument,
    options: RenderOptions | None = None,
    assets: DocumentAssets | None = None,
) -> str:
    """Render an interpreted technical document to Typst source."""
    renderer = TypstTechnicalRenderer(options, assets)
    return renderer.render_document(document)


class TypstTechnicalRenderer(TypstBookRenderer):
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
        self._current_front_matter_kind = None


    def _render_block(self, block: Block) -> None:
        if isinstance(block, Table):
            self._render_table(block)
            return

        super()._render_block(block)

    def _render_table(self, table: Table) -> None:
        """Render a generic table using native Typst table syntax."""
        column_count = len(table.alignments)

        self.lines.append("#table(")
        self.lines.append(f"  columns: {column_count},")
        self.lines.append(
            "  align: ("
            + ", ".join(
                self._render_table_alignment(alignment)
                for alignment in table.alignments
            )
            + "),"
        )
        self.lines.append("  table.header(")

        for cell in table.header.cells:
            self.lines.append(f"    [{self._render_table_cell(cell)}],")

        self.lines.append("  ),")

        for row in table.rows:
            for cell in row.cells:
                self.lines.append(f"  [{self._render_table_cell(cell)}],")

        self.lines.append(")")
        self.lines.append("")

    def _render_table_alignment(self, alignment: TableAlignment) -> str:
        return alignment.value

    def _render_table_cell(self, cell: TableCell) -> str:
        return "".join(self._render_inline(child) for child in cell.children)

    def render_document(self, document: InterpretedDocument) -> str:
        if document.metadata.type != "technical-document":
            raise ValueError(
                "render_document() currently supports only technical-document"
            )

        self._render_document_preamble(document.metadata)
        self._render_title_page_from_metadata(document.metadata)

        # Render optional front matter before the Contents page.
        # The first outlined heading marks the beginning of main matter.
        first_outlined_index = next(
            (
                index
                for index, node in enumerate(document.nodes)
                if node.outlined
            ),
            None,
        )

        if first_outlined_index is None:
            pre_main = document.nodes
            main_matter = []
        else:
            pre_main = document.nodes[:first_outlined_index]
            main_matter = document.nodes[first_outlined_index:]

        for node in pre_main:
            self._render_interpreted_node(node)

        if self._document_section_open:
            if self._current_front_matter_kind == NodeKind.ABSTRACT:
                self.lines.append("#v(1em)")
                self.lines.append("")
            if self._current_front_matter_kind in {
                NodeKind.CERTIFICATE,
                NodeKind.VIVA_VOCE,
            }:
                self.lines.append("]")
                self.lines.append("")
            self.lines.append("]")
            self.lines.append("")
            self._document_section_open = False
            self._current_front_matter_kind = None

        # Contents is emitted after optional front matter and before
        # the first outlined main-matter section.
        if main_matter:
            self._render_contents()

            for node in main_matter:
                self._render_interpreted_node(node)

        if self._document_section_open:
            if self._current_front_matter_kind in {
                NodeKind.CERTIFICATE,
                NodeKind.VIVA_VOCE,
            }:
                self.lines.append("]")
                self.lines.append("")
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
            "  book-author: "
            f'"{self._escape_string(", ".join(metadata.authors))}",'
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
            "  authors: "
            f"{self._typst_author_array(metadata.authors)}, "
        )
        self.lines.append(
            f'  copyright-year: '
            f'"{self._escape_string(metadata.copyright_year)}",'
        )

        logo_path = None
        if metadata.publisher_logo:
            if self.document_assets is None:
                raise ValueError("Publisher logo requires document assets.")

            asset = self.document_assets.resolve(metadata.publisher_logo)
            if asset is None:
                raise ValueError(
                    f"Publisher logo not found: {metadata.publisher_logo}"
                )

            staging_root = self.document_assets.staging_root
            assets_index = staging_root.parts.index("assets")
            logo_path = str(
                Path(
                    *staging_root.parts[assets_index:],
                    "images",
                    asset.staged_path.name,
                )
            )

        if logo_path is not None:
            self.lines.append(
                f'  publisher-logo: "{self._escape_string(logo_path)}",'
            )
        elif metadata.publisher_logo == "":
            self.lines.append("  show-publisher-logo: false,")
        else:
            self.lines.append("  show-publisher-logo: true,")

        if isinstance(metadata.publisher_name, list):
            self.lines.append(
                "  publisher-name-lines: "
                f"{self._typst_author_array(tuple(metadata.publisher_name))}," 
            )
        else:
            self.lines.append(
                f'  publisher-name: "{self._escape_string(metadata.publisher_name or "")}",'
            )
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

        front_matter_kinds = {
            NodeKind.CERTIFICATE,
            NodeKind.VIVA_VOCE,
            NodeKind.DECLARATION,
            NodeKind.ACKNOWLEDGEMENT,
            NodeKind.ABSTRACT,
            NodeKind.KEYWORDS,
            NodeKind.LIST_OF_FIGURES,
            NodeKind.LIST_OF_TABLES,
            NodeKind.REFERENCES,
        }

        if kind in front_matter_kinds:
            if self._document_section_open:
                if self._current_front_matter_kind in {
                    NodeKind.CERTIFICATE,
                    NodeKind.VIVA_VOCE,
                }:
                    self.lines.append("]")
                    self.lines.append("")
                self.lines.append("]")
                self.lines.append("")
                self.lines.append("#pagebreak()")
                self.lines.append("")

            self.lines.append("#front-matter-page[")
            self.lines.append("")

            centered = kind in {NodeKind.CERTIFICATE, NodeKind.VIVA_VOCE}
            if centered:
                self.lines.append("#align(center)[")
                self.lines.append("")
                self._render_heading(heading.level, heading.title, outlined=False)
                self.lines.append("")
                self.lines.append("]")
                self.lines.append("")
                # Keep the heading visually separated from the body.
                self.lines.append("#v(2.5em)")
                self.lines.append("")
            else:
                self._render_heading(heading.level, heading.title, outlined=False)
                self.lines.append("")

            self._document_section_open = True
            self._current_front_matter_kind = kind
            return

        if kind == NodeKind.SECTION:
            if self._document_section_open:
                if self._current_front_matter_kind in {
                    NodeKind.CERTIFICATE,
                    NodeKind.VIVA_VOCE,
                }:
                    self.lines.append("]")
                    self.lines.append("")
                self.lines.append("]")
                self.lines.append("")
                self.lines.append("#pagebreak()")
                self.lines.append("")

            if not self._main_matter_open:
                self._start_main_matter()

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
            self._current_front_matter_kind = None
            return

        self._render_heading(
            heading.level,
            heading.title,
            outlined=outlined,
        )
        self.lines.append("")
