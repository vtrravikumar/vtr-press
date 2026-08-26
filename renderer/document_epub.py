"""Render the generic Document Model to EPUB.

This renderer is the native EPUB consumer for the Phase D generic
Document Model. It consumes an InterpretedDocument directly and does
not reconstruct the legacy Book/Part/Chapter/Section tree.

D3 scope: technical-document only. The existing Book EPUB renderer
remains unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from interpretation import InterpretedDocument, InterpretedNode, NodeKind

from model import (
    Block,
    Bold,
    Code,
    Heading,
    Image,
    Inline,
    Italic,
    LineBreak,
    Link,
    Metadata,
    Paragraph,
    ListBlock,
    Table,
    TableAlignment,
    TableCell,
    Text,
    Verse,
    CodeBlock,
)
from renderer.document_assets import DocumentAssets
from renderer.epub import BOOK_CSS, DEFAULT_LOGO

ROOT = Path(__file__).resolve().parent.parent


@dataclass(slots=True)
class _Document:
    id: str
    href: str
    title: str
    body: str


@dataclass(slots=True)
class _NavPoint:
    title: str
    href: str


def render_document(
    document: InterpretedDocument,
    assets: DocumentAssets | None = None,
) -> bytes:
    """Render an interpreted technical document into EPUB bytes."""
    renderer = _DocumentRenderer(assets)
    return renderer.render(document)


class _DocumentRenderer:
    """Native EPUB renderer for the generic Document Model."""

    def __init__(
        self,
        assets: DocumentAssets | None = None,
    ) -> None:
        self.document_assets = assets
        self.documents: list[_Document] = []
        self.nav_points: list[_NavPoint] = []
        self.logo_path = DEFAULT_LOGO
        self._contents_index: int | None = None
        self._section_number = 0

    def render(self, document: InterpretedDocument) -> bytes:
        if document.metadata.type != "technical-document":
            raise ValueError(
                "render_document() currently supports only technical-document"
            )

        self._render_title_page(document.metadata)

        first_outlined = document.first_outlined_node()

        for node in document.nodes:
            if isinstance(node.block, Heading):
                self._render_heading_node(node, first_outlined)
            elif self.documents and self._section_number:
                self._append_block_to_current_section(node.block)

        self._insert_contents()

        return self._package(document.metadata)

    # ------------------------------------------------------------------
    # Title / sections
    # ------------------------------------------------------------------

    def _render_title_page(self, metadata: Metadata) -> None:
        lines = ['<section class="title-page">']
        lines.append(f"<h1>{_text(metadata.title)}</h1>")

        if metadata.subtitle:
            lines.append(f'<p class="subtitle">{_text(metadata.subtitle)}</p>')

        if metadata.author:
            lines.append(f'<p class="author">{_text(metadata.author)}</p>')

        if self.logo_path.exists():
            lines.append(
                '<img class="publisher-logo" '
                'src="images/publisher-logo.png" alt="VTR Press"/>'
            )

        if metadata.copyright_year:
            lines.append(f'<p class="copyright">{_text(metadata.copyright_year)}</p>')

        lines.append("</section>")

        self.documents.append(
            _Document(
                id="title",
                href="title.xhtml",
                title=metadata.title or "Title",
                body="\n".join(lines),
            )
        )

    def _render_heading_node(
        self,
        node: InterpretedNode,
        first_outlined: InterpretedNode | None,
    ) -> None:
        heading = node.block
        assert isinstance(heading, Heading)

        if node.kind == NodeKind.OTHER and heading.level == 1:
            return

        if node.kind == NodeKind.SECTION:
            self._section_number += 1

            if first_outlined is node:
                self._contents_index = len(self.documents)

            href = f"section-{self._section_number:03d}.xhtml"
            self.documents.append(
                _Document(
                    id=f"section-{self._section_number:03d}",
                    href=href,
                    title=heading.title,
                    body=f"<h2>{_text(heading.title)}</h2>",
                )
            )
            self.nav_points.append(_NavPoint(title=heading.title, href=href))
            return

        if not self.documents or not self._section_number:
            return

        level = max(2, min(heading.level, 6))
        self._append_to_current(f"<h{level}>{_text(heading.title)}</h{level}>")

    def _append_block_to_current_section(self, block: Block) -> None:
        self._append_to_current(self._render_block(block))

    def _append_to_current(self, rendered: str) -> None:
        if not self.documents or self._section_number == 0:
            return

        current = self.documents[-1]
        if current.id.startswith("section-"):
            current.body += "\n" + rendered

    # ------------------------------------------------------------------
    # Contents
    # ------------------------------------------------------------------

    def _insert_contents(self) -> None:
        index = self._contents_index
        if index is None:
            index = min(1, len(self.documents))

        self.documents.insert(
            index,
            _Document(
                id="contents",
                href="contents.xhtml",
                title="Contents",
                body=self._contents_body(),
            ),
        )

    def _contents_body(self) -> str:
        lines = [
            '<section class="contents">',
            "<h1>Contents</h1>",
            "<ol>",
        ]

        for point in self.nav_points:
            lines.append(
                f'  <li><a href="{_attr(point.href)}">{_text(point.title)}</a></li>'
            )

        lines.extend(["</ol>", "</section>"])
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Blocks / inline
    # ------------------------------------------------------------------

    def _render_block(self, block: Block) -> str:
        if isinstance(block, Paragraph):
            content = "".join(self._render_inline(node) for node in block.children)
            return f"<p>{content}</p>"
        if isinstance(block, ListBlock):
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

        if isinstance(block, Table):
            return self._render_table(block)

        if isinstance(block, Image):
            if self.document_assets is None:
                raise ValueError("Image rendering requires document assets.")
            asset = self.document_assets.resolve(block.source)
            if asset is None:
                return f'<p class="missing-image">{_text(block.alt_text)}</p>'
            return (
                f"<figure>"
                f'<img src="{_attr(asset.epub_href)}" '
                f'alt="{_attr(block.alt_text)}"/>'
                f"</figure>"
            )
        if isinstance(block, CodeBlock):
            return self._render_code_block(block)
        if isinstance(block, Verse):
            lines = ['<div class="verse">']
            for line in block.lines:
                lines.append(f"<p>{_text(line)}</p>")
            lines.append("</div>")
            return "\n".join(lines)

        raise TypeError(f"Unsupported block: {type(block).__name__}")

    def _render_code_block(self, block: CodeBlock) -> str:
        """Render a fenced code block as an EPUB preformatted block."""
        language = _attr(block.language.strip())
        class_attr = f' class="language-{language}"' if language else ""

        content = _text("\n".join(block.lines))

        return f"<pre{class_attr}><code>{content}</code></pre>"

    def _render_table(self, table: Table) -> str:
        lines = ["<table>", "<thead>", "<tr>"]

        for index, cell in enumerate(table.header.cells):
            alignment = table.alignments[index]
            lines.append(
                f'<th style="text-align: {self._render_table_alignment(alignment)}">'
                f"{self._render_table_cell(cell)}</th>"
            )

        lines.extend(["</tr>", "</thead>", "<tbody>"])

        for row in table.rows:
            lines.append("<tr>")
            for index, cell in enumerate(row.cells):
                alignment = table.alignments[index]
                lines.append(
                    f'<td style="text-align: {self._render_table_alignment(alignment)}">'
                    f"{self._render_table_cell(cell)}</td>"
                )
            lines.append("</tr>")

        lines.extend(["</tbody>", "</table>"])
        return "\n".join(lines)

    def _render_table_alignment(self, alignment: TableAlignment) -> str:
        return alignment.value

    def _render_table_cell(self, cell: TableCell) -> str:
        return "".join(self._render_inline(node) for node in cell.children)

    def _render_inline(self, node: Inline) -> str:
        if isinstance(node, Text):
            return _text(node.text)

        if isinstance(node, Bold):
            return (
                "<strong>"
                + "".join(self._render_inline(child) for child in node.children)
                + "</strong>"
            )

        if isinstance(node, Italic):
            return (
                "<em>"
                + "".join(self._render_inline(child) for child in node.children)
                + "</em>"
            )

        if isinstance(node, Code):
            return f"<code>{_text(node.text)}</code>"

        if isinstance(node, Link):
            return f'<a href="{_attr(node.url)}">{_text(node.text)}</a>'

        if isinstance(node, LineBreak):
            return "<br/>"

        raise TypeError(f"Unsupported inline: {type(node).__name__}")

    # ------------------------------------------------------------------
    # EPUB package
    # ------------------------------------------------------------------

    def _package(self, metadata: Metadata) -> bytes:
        output = BytesIO()
        logo_name = "publisher-logo.png" if self.logo_path.exists() else None

        with ZipFile(output, "w") as epub:
            info = ZipInfo("mimetype")
            info.compress_type = ZIP_STORED
            epub.writestr(info, "application/epub+zip")

            self._write(
                epub,
                "META-INF/container.xml",
                self._container_xml(),
            )
            self._write(epub, "OEBPS/book.css", BOOK_CSS)
            self._write(
                epub,
                "OEBPS/nav.xhtml",
                self._nav_xhtml(metadata),
            )
            self._write(
                epub,
                "OEBPS/toc.ncx",
                self._toc_ncx(metadata),
            )
            self._write(
                epub,
                "OEBPS/content.opf",
                self._content_opf(metadata),
            )

            if logo_name:
                epub.write(
                    self.logo_path,
                    "OEBPS/images/publisher-logo.png",
                    compress_type=ZIP_DEFLATED,
                )
            if self.document_assets is not None:
                for asset in self.document_assets.resolved:
                    epub.write(
                        asset.staged_path,
                        f"OEBPS/{asset.epub_href}",
                        compress_type=ZIP_DEFLATED,
                    )

            for item in self.documents:
                self._write(
                    epub,
                    f"OEBPS/{item.href}",
                    self._document_xhtml(item),
                )

        return output.getvalue()

    def _write(self, epub: ZipFile, name: str, text: str) -> None:
        epub.writestr(
            name,
            text.encode("utf-8"),
            compress_type=ZIP_DEFLATED,
        )

    def _container_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    def _document_xhtml(self, document: _Document) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <title>{_text(document.title)}</title>
  <link rel="stylesheet" type="text/css" href="book.css"/>
</head>
<body>
{document.body}
</body>
</html>
"""

    def _nav_xhtml(self, metadata: Metadata) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            "<!DOCTYPE html>",
            '<html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops" lang="en">',
            "<head>",
            f"  <title>{_text(metadata.title or 'Contents')}</title>",
            '  <link rel="stylesheet" type="text/css" href="book.css"/>',
            "</head>",
            "<body>",
            '  <nav epub:type="toc" id="toc">',
            "    <h1>Contents</h1>",
            "    <ol>",
        ]

        for point in self.nav_points:
            lines.append(
                f'      <li><a href="{_attr(point.href)}">{_text(point.title)}</a></li>'
            )

        lines.extend(
            [
                "    </ol>",
                "  </nav>",
                "</body>",
                "</html>",
                "",
            ]
        )
        return "\n".join(lines)

    def _toc_ncx(self, metadata: Metadata) -> str:
        uid = _metadata_uid(metadata)
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
            "  <head>",
            f'    <meta name="dtb:uid" content="{_attr(uid)}"/>',
            '    <meta name="dtb:depth" content="1"/>',
            '    <meta name="dtb:totalPageCount" content="0"/>',
            '    <meta name="dtb:maxPageNumber" content="0"/>',
            "  </head>",
            "  <docTitle><text>"
            f"{_text(metadata.title or 'Untitled')}"
            "</text></docTitle>",
            "  <navMap>",
        ]

        for index, point in enumerate(self.nav_points, start=1):
            lines.extend(
                [
                    f'    <navPoint id="nav-{index}" playOrder="{index}">',
                    f"      <navLabel><text>{_text(point.title)}</text></navLabel>",
                    f'      <content src="{_attr(point.href)}"/>',
                    "    </navPoint>",
                ]
            )

        lines.extend(["  </navMap>", "</ncx>", ""])
        return "\n".join(lines)

    def _content_opf(self, metadata: Metadata) -> str:
        modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        uid = _metadata_uid(metadata)
        language = metadata.language or "en"

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<package xmlns="http://www.idpf.org/2007/opf" '
            'unique-identifier="book-id" version="3.0">',
            '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">',
            f'    <dc:identifier id="book-id">{_text(uid)}</dc:identifier>',
            '    <dc:title id="title">'
            f"{_text(metadata.title or 'Untitled')}"
            "</dc:title>",
            '    <meta property="title-type" refines="#title">main</meta>',
            f"    <dc:language>{_text(language)}</dc:language>",
            f'    <meta property="dcterms:modified">{modified}</meta>',
        ]

        if metadata.author:
            lines.append(f"    <dc:creator>{_text(metadata.author)}</dc:creator>")

        if metadata.subtitle:
            lines.extend(
                [
                    '    <dc:title id="subtitle">'
                    f"{_text(metadata.subtitle)}</dc:title>",
                    '    <meta property="title-type" refines="#subtitle">subtitle</meta>',
                ]
            )

        if metadata.version:
            lines.append(
                f"    <dc:identifier>{_text(metadata.version)}</dc:identifier>"
            )

        lines.extend(
            [
                "  </metadata>",
                "  <manifest>",
                '    <item id="nav" href="nav.xhtml" '
                'media-type="application/xhtml+xml" properties="nav"/>',
                '    <item id="ncx" href="toc.ncx" '
                'media-type="application/x-dtbncx+xml"/>',
                '    <item id="css" href="book.css" media-type="text/css"/>',
            ]
        )

        if self.logo_path.exists():
            lines.append(
                '    <item id="publisher-logo" '
                'href="images/publisher-logo.png" '
                'media-type="image/png"/>'
            )
        if self.document_assets is not None:
            for index, asset in enumerate(
                self.document_assets.resolved,
                start=1,
            ):
                lines.append(
                    f'    <item id="asset-{index}" '
                    f'href="{_attr(asset.epub_href)}" '
                    f'media-type="{_attr(asset.media_type)}"/>'
                )

        for item in self.documents:
            lines.append(
                f'    <item id="{_attr(item.id)}" '
                f'href="{_attr(item.href)}" '
                'media-type="application/xhtml+xml"/>'
            )

        lines.extend(["  </manifest>", '  <spine toc="ncx">'])

        for item in self.documents:
            lines.append(f'    <itemref idref="{_attr(item.id)}"/>')

        lines.extend(["  </spine>", "</package>", ""])
        return "\n".join(lines)


def _metadata_uid(metadata: Metadata) -> str:
    value = "|".join(
        [
            _plain(metadata.title),
            _plain(metadata.subtitle),
            _plain(metadata.author),
            _plain(metadata.version),
        ]
    )
    return f"urn:uuid:{uuid5(NAMESPACE_URL, value)}"


def _text(value: object) -> str:
    return escape(_plain(value), quote=False)


def _attr(value: object) -> str:
    return escape(_plain(value), quote=True)


def _plain(value: object) -> str:
    if value is None:
        return ""
    return str(value)
