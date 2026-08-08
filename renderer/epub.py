"""
Render a Book AST into an EPUB 3 package.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from io import BytesIO
import mimetypes
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from model import (
    Book,
    Part,
    Chapter,
    Scene,
    Section,
    Paragraph,
    Subheading,
    Verse,
    Text,
    Bold,
    Italic,
    Code,
    Link,
    LineBreak,
    Block,
    Inline,
    SectionKind,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_COVER = ROOT / "assets" / "books" / "current" / "cover.png"
DEFAULT_LOGO = ROOT / "assets" / "publisher" / "logo.png"


BOOK_CSS = """
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


@dataclass(slots=True)
class _Document:
    """A generated XHTML document."""

    id: str
    href: str
    title: str
    body: str


@dataclass(slots=True)
class _NavPoint:
    """An item that appears in nav.xhtml and toc.ncx."""

    title: str
    href: str
    children: list[_NavPoint]


def render(
    book: Book,
    cover_path: str | Path | None = None,
) -> bytes:
    """Render a Book AST into EPUB bytes."""

    renderer = _Renderer(cover_path)
    return renderer.render(book)


def write(
    book: Book,
    path: str | Path,
    cover_path: str | Path | None = None,
) -> None:
    """Render a Book AST and write it to an .epub file."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render(book, cover_path))


class _Renderer:
    """EPUB renderer."""

    def __init__(self, cover_path: str | Path | None = None) -> None:
        self.cover_path = Path(cover_path) if cover_path is not None else DEFAULT_COVER
        self.logo_path = DEFAULT_LOGO
        self.documents: list[_Document] = []
        self.nav_points: list[_NavPoint] = []
        self._id_counts: dict[str, int] = {}
        self._section_number = 0
        self._part_number = 0
        self._chapter_number = 0
        self._contents_index: int | None = None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def render(self, book: Book) -> bytes:
        """Render a Book AST into EPUB bytes."""

        self._render_cover(book)
        self._render_title_page(book)

        for item in book.sections:

            if isinstance(item, Section):
                if self._skip_section(item):
                    continue

                self._render_section(item)

            elif isinstance(item, Part):
                self._render_part(item)

        self._insert_contents()

        return self._package(book)

    # ------------------------------------------------------------------
    # Cover
    # ------------------------------------------------------------------

    def _render_cover(self, book: Book) -> None:
        """Render the cover page."""

        cover_name = self._cover_name()

        if cover_name:
            cover_alt = _attr(book.metadata.title or "Cover")
            body = (
                '<section class="cover">'
                f'<img src="images/{cover_name}" alt="{cover_alt}"/>'
                "</section>"
            )

        else:
            body = (
                '<section class="title-page">'
                f"<h1>{_text(book.metadata.title or 'Untitled')}</h1>"
                "</section>"
            )

        self.documents.append(
            _Document(
                id="cover",
                href="cover.xhtml",
                title="Cover",
                body=body,
            )
        )

    # ------------------------------------------------------------------
    # Title Page
    # ------------------------------------------------------------------

    def _render_title_page(self, book: Book) -> None:
        """Render the title page."""

        md = book.metadata
        logo_name = self._logo_name()
        lines = ['<section class="title-page">']

        lines.append(f"<h1>{_text(md.title)}</h1>")

        if md.subtitle:
            lines.append(f'<p class="subtitle">{_text(md.subtitle)}</p>')

        if md.author:
            lines.append(f'<p class="author">{_text(md.author)}</p>')

        if logo_name:
            lines.append(
                '<img class="publisher-logo" '
                f'src="images/{_attr(logo_name)}" alt="VTR Press"/>'
            )

        if md.copyright_year:
            lines.append(f'<p class="copyright">{_text(md.copyright_year)}</p>')

        lines.append("</section>")

        self.documents.append(
            _Document(
                id="title",
                href="title.xhtml",
                title=md.title or "Title",
                body="\n".join(lines),
            )
        )

    # ------------------------------------------------------------------
    # Part
    # ------------------------------------------------------------------

    def _render_part(self, part: Part) -> None:
        """Render a Part and its chapters."""

        self._part_number += 1

        part_doc = _Document(
            id=f"part-{self._part_number:03d}",
            href=f"part-{self._part_number:03d}.xhtml",
            title=part.title,
            body=f"<h1>{_text(part.title)}</h1>",
        )
        self.documents.append(part_doc)

        children: list[_NavPoint] = []

        for chapter in part.chapters:
            chapter_doc = self._render_chapter(chapter)
            children.append(
                _NavPoint(
                    title=chapter.title,
                    href=chapter_doc.href,
                    children=[],
                )
            )

        self.nav_points.append(
            _NavPoint(
                title=part.title,
                href=part_doc.href,
                children=children,
            )
        )

    # ------------------------------------------------------------------
    # Chapter
    # ------------------------------------------------------------------

    def _render_chapter(self, chapter: Chapter) -> _Document:
        """Render a chapter and its scenes."""

        self._chapter_number += 1

        lines = [f"<h2>{_text(chapter.title)}</h2>"]

        for scene in chapter.scenes:
            self._render_scene(scene, lines)

        document = _Document(
            id=f"chapter-{self._chapter_number:03d}",
            href=f"chapter-{self._chapter_number:03d}.xhtml",
            title=chapter.title,
            body="\n".join(lines),
        )
        self.documents.append(document)
        return document

    # ------------------------------------------------------------------
    # Scene
    # ------------------------------------------------------------------

    def _render_scene(self, scene: Scene, lines: list[str]) -> None:
        """Render a scene within a chapter."""

        if scene.title:
            lines.append(f'<h3 class="scene">{_text(scene.title)}</h3>')

        for block in scene.blocks:
            lines.append(self._render_block(block))

    # ------------------------------------------------------------------
    # Section
    # ------------------------------------------------------------------

    def _skip_section(self, section: Section) -> bool:
        """
        Return whether a top-level section should be omitted from the EPUB.

        The Back Cover is print-only marketing matter (and, for print
        mode, a placeholder for the physical back cover artwork). EPUB
        readers should end with the final reading content -- typically
        the Epilogue or "About the Author" -- rather than a back-cover
        blurb that only makes sense on a physical book.
        """

        return section.kind == SectionKind.BACK_COVER

    def _render_section(self, section: Section) -> None:
        """Render a top-level non-part section."""

        self._section_number += 1

        if (
            self._contents_index is None
            and section.kind == SectionKind.PROLOGUE
        ):
            self._contents_index = len(self.documents)

        lines = [f"<h2>{_text(section.title)}</h2>"]

        for block in section.blocks:
            lines.append(self._render_block(block))

        self.documents.append(
            _Document(
                id=f"section-{self._section_number:03d}",
                href=f"front-{self._section_number:03d}.xhtml",
                title=section.title,
                body="\n".join(lines),
            )
        )

    # ------------------------------------------------------------------
    # Contents
    # ------------------------------------------------------------------

    def _insert_contents(self) -> None:
        """Insert the readable Contents page before the Prologue."""

        index = self._contents_index

        if index is None:
            index = min(2, len(self.documents))

        self.documents.insert(
            index,
            _Document(
                id="contents",
                href="contents.xhtml",
                title="Contents",
                body=self._contents_body(),
            )
        )

    def _contents_body(self) -> str:
        """Render the readable Contents page body."""

        lines = [
            '<section class="contents">',
            "<h1>Contents</h1>",
            "<ol>",
        ]

        for point in self.nav_points:
            self._render_contents_point(point, lines, 1)

        lines.extend(
            [
                "</ol>",
                "</section>",
            ]
        )

        return "\n".join(lines)

    def _render_contents_point(
        self,
        point: _NavPoint,
        lines: list[str],
        indent: int,
    ) -> None:
        """Render one readable Contents entry."""

        pad = "  " * indent
        lines.append(
            f'{pad}<li><a href="{_attr(point.href)}">{_text(point.title)}</a>'
        )

        if point.children:
            lines.append(f"{pad}  <ol>")

            for child in point.children:
                self._render_contents_point(child, lines, indent + 2)

            lines.append(f"{pad}  </ol>")

        lines.append(f"{pad}</li>")

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    def _render_block(self, block: Block) -> str:
        """Render a block element."""

        if isinstance(block, Paragraph):
            return self._render_paragraph(block)

        if isinstance(block, Verse):
            return self._render_verse(block)

        if isinstance(block, Subheading):
            level = block.level if block.level in (3, 4, 5, 6) else 3
            return f"<h{level}>{_text(block.title)}</h{level}>"

        raise TypeError(f"Unsupported block: {type(block).__name__}")

    # ------------------------------------------------------------------
    # Paragraph
    # ------------------------------------------------------------------

    def _render_paragraph(self, paragraph: Paragraph) -> str:
        """Render a paragraph."""

        content = "".join(
            self._render_inline(node)
            for node in paragraph.children
        )
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
    # Inline
    # ------------------------------------------------------------------

    def _render_inline(self, node: Inline) -> str:
        """Render an inline element."""

        if isinstance(node, Text):
            return _text(node.text)

        if isinstance(node, Bold):
            return "<strong>" + "".join(
                self._render_inline(child)
                for child in node.children
            ) + "</strong>"

        if isinstance(node, Italic):
            return "<em>" + "".join(
                self._render_inline(child)
                for child in node.children
            ) + "</em>"

        if isinstance(node, Code):
            return f"<code>{_text(node.text)}</code>"

        if isinstance(node, Link):
            return f'<a href="{_attr(node.url)}">{_text(node.text)}</a>'

        if isinstance(node, LineBreak):
            return "<br/>"

        raise TypeError(f"Unsupported inline: {type(node).__name__}")

    # ------------------------------------------------------------------
    # Package
    # ------------------------------------------------------------------

    def _package(self, book: Book) -> bytes:
        """Package all EPUB files into a zip archive."""

        output = BytesIO()
        cover_name = self._cover_name()
        logo_name = self._logo_name()

        with ZipFile(output, "w") as epub:
            info = ZipInfo("mimetype")
            info.compress_type = ZIP_STORED
            epub.writestr(info, "application/epub+zip")

            self._write(epub, "META-INF/container.xml", self._container_xml())
            self._write(epub, "OEBPS/book.css", BOOK_CSS)
            self._write(epub, "OEBPS/nav.xhtml", self._nav_xhtml(book))
            self._write(epub, "OEBPS/toc.ncx", self._toc_ncx(book))
            self._write(epub, "OEBPS/content.opf", self._content_opf(book))

            if cover_name and self.cover_path.exists():
                epub.write(
                    self.cover_path,
                    f"OEBPS/images/{cover_name}",
                    compress_type=ZIP_DEFLATED,
                )

            if logo_name and self.logo_path.exists():
                epub.write(
                    self.logo_path,
                    f"OEBPS/images/{logo_name}",
                    compress_type=ZIP_DEFLATED,
                )

            for document in self.documents:
                self._write(
                    epub,
                    f"OEBPS/{document.href}",
                    self._document_xhtml(document),
                )

        return output.getvalue()

    def _write(self, epub: ZipFile, name: str, text: str) -> None:
        """Write a UTF-8 text file to the EPUB archive."""

        epub.writestr(name, text.encode("utf-8"), compress_type=ZIP_DEFLATED)

    # ------------------------------------------------------------------
    # XML Documents
    # ------------------------------------------------------------------

    def _container_xml(self) -> str:
        """Render META-INF/container.xml."""

        return """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    def _document_xhtml(self, document: _Document) -> str:
        """Render a content XHTML document."""

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

    def _nav_xhtml(self, book: Book) -> str:
        """Render the EPUB 3 navigation document."""

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops" lang="en">',
            "<head>",
            f"  <title>{_text(book.metadata.title or 'Contents')}</title>",
            '  <link rel="stylesheet" type="text/css" href="book.css"/>',
            "</head>",
            "<body>",
            '  <nav epub:type="toc" id="toc">',
            "    <h1>Contents</h1>",
            "    <ol>",
        ]

        for point in self.nav_points:
            self._render_nav_point(point, lines, 3)

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

    def _render_nav_point(
        self,
        point: _NavPoint,
        lines: list[str],
        indent: int,
    ) -> None:
        """Render one nav.xhtml point."""

        pad = "  " * indent
        lines.append(
            f'{pad}<li><a href="{_attr(point.href)}">{_text(point.title)}</a>'
        )

        if point.children:
            lines.append(f"{pad}  <ol>")

            for child in point.children:
                self._render_nav_point(child, lines, indent + 2)

            lines.append(f"{pad}  </ol>")

        lines.append(f"{pad}</li>")

    def _toc_ncx(self, book: Book) -> str:
        """Render toc.ncx for compatibility readers."""

        uid = _book_uid(book)
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
            "  <head>",
            f'    <meta name="dtb:uid" content="{_attr(uid)}"/>',
            '    <meta name="dtb:depth" content="2"/>',
            '    <meta name="dtb:totalPageCount" content="0"/>',
            '    <meta name="dtb:maxPageNumber" content="0"/>',
            "  </head>",
            "  <docTitle><text>"
            f"{_text(book.metadata.title or 'Untitled')}"
            "</text></docTitle>",
            "  <navMap>",
        ]

        play_order = 1

        for point in self.nav_points:
            play_order = self._render_ncx_point(point, lines, play_order, 2)

        lines.extend(
            [
                "  </navMap>",
                "</ncx>",
                "",
            ]
        )

        return "\n".join(lines)

    def _render_ncx_point(
        self,
        point: _NavPoint,
        lines: list[str],
        play_order: int,
        indent: int,
    ) -> int:
        """Render one toc.ncx navPoint."""

        nav_id = self._unique_id("nav")
        pad = "  " * indent

        lines.extend(
            [
                f'{pad}<navPoint id="{nav_id}" playOrder="{play_order}">',
                f"{pad}  <navLabel><text>{_text(point.title)}</text></navLabel>",
                f'{pad}  <content src="{_attr(point.href)}"/>',
            ]
        )

        play_order += 1

        for child in point.children:
            play_order = self._render_ncx_point(
                child,
                lines,
                play_order,
                indent + 1,
            )

        lines.append(f"{pad}</navPoint>")
        return play_order

    def _content_opf(self, book: Book) -> str:
        """Render OEBPS/content.opf."""

        uid = _book_uid(book)
        modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        language = book.metadata.language or "en"
        cover_name = self._cover_name()
        logo_name = self._logo_name()

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<package xmlns="http://www.idpf.org/2007/opf" '
            'unique-identifier="book-id" version="3.0">',
            "  <metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\">",
            f'    <dc:identifier id="book-id">{_text(uid)}</dc:identifier>',
            '    <dc:title id="title">'
            f'{_text(book.metadata.title or "Untitled")}'
            "</dc:title>",
            f"    <dc:language>{_text(language)}</dc:language>",
            f'    <meta property="dcterms:modified">{modified}</meta>',
        ]

        if book.metadata.author:
            lines.append(
                f"    <dc:creator>{_text(book.metadata.author)}</dc:creator>"
            )

        if book.metadata.subtitle:
            lines.append(
                '    <dc:title id="subtitle">'
                f"{_text(book.metadata.subtitle)}"
                "</dc:title>"
            )
            lines.append(
                '    <meta property="title-type" refines="#subtitle">subtitle</meta>'
            )

        if book.metadata.version:
            lines.append(
                f"    <dc:identifier>{_text(book.metadata.version)}</dc:identifier>"
            )

        if cover_name:
            lines.append(f'    <meta name="cover" content="cover-image"/>')

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

        if cover_name:
            lines.append(
                f'    <item id="cover-image" href="images/{_attr(cover_name)}" '
                f'media-type="{_attr(_media_type(cover_name))}" '
                'properties="cover-image"/>'
            )

        if logo_name:
            lines.append(
                f'    <item id="publisher-logo" href="images/{_attr(logo_name)}" '
                f'media-type="{_attr(_media_type(logo_name))}"/>'
            )

        for document in self.documents:
            lines.append(
                f'    <item id="{_attr(document.id)}" href="{_attr(document.href)}" '
                'media-type="application/xhtml+xml"/>'
            )

        lines.extend(
            [
                "  </manifest>",
                '  <spine toc="ncx">',
            ]
        )

        for document in self.documents:
            linear = ' linear="no"' if document.id == "cover" else ""
            lines.append(f'    <itemref idref="{_attr(document.id)}"{linear}/>')

        lines.extend(
            [
                "  </spine>",
                "</package>",
                "",
            ]
        )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cover_name(self) -> str | None:
        """Return the packaged cover image name."""

        if not self.cover_path.exists():
            return None

        suffix = self.cover_path.suffix.lower()

        if suffix not in {".jpg", ".jpeg", ".png", ".gif", ".svg"}:
            suffix = ".png"

        return f"cover{suffix}"

    def _logo_name(self) -> str | None:
        """Return the packaged publisher logo image name."""

        if not self.logo_path.exists():
            return None

        suffix = self.logo_path.suffix.lower()

        if suffix not in {".jpg", ".jpeg", ".png", ".gif", ".svg"}:
            suffix = ".png"

        return f"publisher-logo{suffix}"

    def _unique_id(self, prefix: str) -> str:
        """Return a unique XML id."""

        count = self._id_counts.get(prefix, 0) + 1
        self._id_counts[prefix] = count
        return f"{prefix}-{count}"


def _book_uid(book: Book) -> str:
    """Return a stable package identifier."""

    metadata = book.metadata
    value = "|".join(
        [
            _plain(metadata.title),
            _plain(metadata.subtitle),
            _plain(metadata.author),
            _plain(metadata.version),
        ]
    )
    return f"urn:uuid:{uuid5(NAMESPACE_URL, value)}"


def _media_type(name: str) -> str:
    """Return an EPUB media type for a filename."""

    media_type, _ = mimetypes.guess_type(name)
    return media_type or "image/png"


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
