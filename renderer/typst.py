"""
Render a Book AST into Typst source.
"""

from __future__ import annotations

from model import (
    Book,
    Part,
    Chapter,
    Section,
    Paragraph,
    Verse,
    Text,
    Bold,
    Italic,
    Code,
    Link,
    Block,
    Inline,
    SectionKind,
)

# ------------------------------------------------------------------
# Typst document preamble
# ------------------------------------------------------------------

TYPST_PREAMBLE = """
#set page(
  paper: "a5",
  margin: (
    x: 18mm,
    y: 22mm,
  ),
  numbering: none,
)

#set text(
    font: "Libertinus Serif",
    size: 11pt,
)

#show heading.where(level: 1): set text(
  size: 18pt,
  weight: "bold",
)

#show heading.where(level: 2): set text(
  size: 16pt,
  weight: "bold",
)

#show heading.where(level: 3): set text(
  size: 15pt,
  weight: "bold",
)

#set par(justify: true)

""".strip()


def render(book: Book) -> str:
    """Render a Book AST into Typst."""

    renderer = _Renderer()
    return renderer.render(book)


class _Renderer:
    """Typst renderer."""

    def __init__(self) -> None:
        self.lines: list[str] = []

        # Tracks whether we've already rendered the first printable page.
        self._first_page = True
        # Tracks whether the table of contents has been inserted.
        self._contents_inserted = False

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def render(self, book: Book) -> str:
        self._render_preamble(book)
        self._render_cover()
        self._render_title_page(book)
        for item in book.sections:

            if isinstance(item, Section):
                self._render_section(item)

            elif isinstance(item, Part):
                self._render_part(item)

        return "\n".join(self.lines).rstrip() + "\n"

    # ------------------------------------------------------------------
    # Document Preamble
    # ------------------------------------------------------------------

    def _render_preamble(self, book: Book) -> None:
        """Emit the Typst document preamble."""

        self.lines.append(TYPST_PREAMBLE)
        self.lines.append("")

        md = book.metadata

        # Optional document variables for future use.
        if md.title:
            self.lines.append(f'#let book_title = "{md.title}"')

        if md.author:
            self.lines.append(f'#let book_author = "{md.author}"')
        self.lines.append("")

    # ------------------------------------------------------------------
    # Cover
    # ------------------------------------------------------------------

    def _render_cover(self) -> None:
        """Render a full-page digital cover."""

        # Override margins for the cover page only.
        self.lines.append("#set page(")
        self.lines.append("  margin: 0mm,")
        self.lines.append(")")
        self.lines.append("")

        self.lines.append(
            '#image('
            '"../assets/book_cover.png", '
            'width: 100%, '
            'height: 100%'
            ')'
        )

        self.lines.append("")
        self.lines.append("#pagebreak()")
        self.lines.append("")

        # Restore normal margins for the remainder of the book.
        self.lines.append("#set page(")
        self.lines.append("  margin: (")
        self.lines.append("    x: 18mm,")
        self.lines.append("    y: 22mm,")
        self.lines.append("  ),")
        self.lines.append(")")
        self.lines.append("")


    # ------------------------------------------------------------------
    # Title Page
    # ------------------------------------------------------------------

    def _render_title_page(self, book: Book) -> None:
        """Render the title page."""

        md = book.metadata

        self.lines.append("#align(center)[")
        self.lines.append("")

        self.lines.append("#v(20%)")
        self.lines.append("")

        self.lines.append(
            f'#text(size: 28pt, weight: "bold")[{md.title}]'
        )

        if md.subtitle:
            self.lines.append("")
            self.lines.append(
                f'#text(size: 15pt)[{md.subtitle}]'
            )

        self.lines.append("")
        self.lines.append("#v(12%)")
        self.lines.append("")

        self.lines.append(
            f'#text(size: 16pt)[{md.author}]'
        )

        self.lines.append("")
        self.lines.append("#v(20%)")
        self.lines.append("")

        self.lines.append(
            '#text(size: 12pt, weight: "bold")[VTR Press]'
        )

        if md.copyright_year:
            self.lines.append(
                f'#text(size: 11pt)[{md.copyright_year}]'
            )

        self.lines.append("")
        self.lines.append("]")
        self.lines.append("")
        self.lines.append("#pagebreak()")
        self.lines.append("")

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def _page_break(self) -> None:
        """Insert a page break before every major object except the first."""

        if self._first_page:
            self._first_page = False
            return

        self.lines.append("#pagebreak()")
        self.lines.append("")
    # ------------------------------------------------------------------
    # Contents
    # ------------------------------------------------------------------

    def _render_contents(self) -> None:
        """Render the table of contents."""

        self.lines.append("#pagebreak()")
        self.lines.append("")

        self.lines.append("#align(left)[")
        self.lines.append("  #text(")
        self.lines.append("    size: 22pt,")
        self.lines.append('    weight: "bold",')
        self.lines.append("  )[Contents]")
        self.lines.append("]")
        self.lines.append("")

        self.lines.append("#v(1em)")
        self.lines.append("")

        self.lines.append("#outline(title: none)")
        self.lines.append("")


    # ------------------------------------------------------------------
    # Page Numbering
    # ------------------------------------------------------------------

    def _start_main_matter(self) -> None:
        """Begin page numbering for the main matter."""

        self.lines.append("#set page(numbering: \"1\")")
        self.lines.append("#counter(page).update(1)")
        self.lines.append("")

    # ------------------------------------------------------------------
    # Heading
    # ------------------------------------------------------------------

    def _render_heading(
        self,
        level: int,
        title: str,
        outlined: bool = True,
    ) -> None:
        """Render a Typst heading."""

        if outlined:
            self.lines.append(f'{"=" * level} {title}')
            return

        self.lines.append("#heading(")
        self.lines.append(f"  level: {level},")
        self.lines.append("  outlined: false,")
        self.lines.append(f")[{title}]")

    # ------------------------------------------------------------------
    # Part
    # ------------------------------------------------------------------

    def _render_part(self, part: Part) -> None:

        self._page_break()

        self._render_heading(1, part.title)
        self.lines.append("")

        for chapter in part.chapters:
            self._render_chapter(chapter)

    # ------------------------------------------------------------------
    # Chapter
    # ------------------------------------------------------------------

    def _render_chapter(self, chapter: Chapter) -> None:

        self._page_break()
        self._render_heading(2, chapter.title)
        self.lines.append("")

        for block in chapter.blocks:
            self._render_block(block)

    # ------------------------------------------------------------------
    # Section
    # ------------------------------------------------------------------

    def _render_section(self, section: Section) -> None:

        # Insert the Contents page immediately before the Prologue.
        if (
            not self._contents_inserted
            and section.kind == SectionKind.PROLOGUE
        ):
            self._render_contents()

            # Start numbering from the Prologue.
            self._start_main_matter()

            self._contents_inserted = True

        self._page_break()

        outlined = section.kind not in {
            SectionKind.COPYRIGHT,
            SectionKind.DEDICATION,
            SectionKind.THIRUKKURAL,
        }

        self._render_heading(
            2,
            section.title,
            outlined=outlined,
        )

        self.lines.append("")

        for block in section.blocks:
            self._render_block(block)
    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    def _render_block(self, block: Block) -> None:

        if isinstance(block, Paragraph):
            self.lines.append(self._render_paragraph(block))
            self.lines.append("")
            return

        if isinstance(block, Verse):
            self._render_verse(block)
            return

        raise TypeError(f"Unsupported block: {type(block).__name__}")
    # ------------------------------------------------------------------
    # Paragraph
    # ------------------------------------------------------------------

    def _render_paragraph(self, paragraph: Paragraph) -> str:

        return "".join(
            self._render_inline(node)
            for node in paragraph.children
        )

    # ------------------------------------------------------------------
    # Verse
    # ------------------------------------------------------------------

    def _render_verse(self, verse: Verse) -> None:
        """Render a verse preserving line breaks."""

        self.lines.append("#block[")

        for i, line in enumerate(verse.lines):

            self.lines.append(line)

            if i < len(verse.lines) - 1:
                self.lines.append("#linebreak()")

        self.lines.append("]")
        self.lines.append("")

    # ------------------------------------------------------------------
    # Inline
    # ------------------------------------------------------------------

    def _render_inline(self, node: Inline) -> str:

        if isinstance(node, Text):
            return node.text

        if isinstance(node, Bold):
            return "*" + "".join(
                self._render_inline(child)
                for child in node.children
            ) + "*"

        if isinstance(node, Italic):
            return "_" + "".join(
                self._render_inline(child)
                for child in node.children
            ) + "_"

        if isinstance(node, Code):
            return f"`{node.text}`"

        if isinstance(node, Link):
            return f'link("{node.url}")[{node.text}]'

        raise TypeError(f"Unsupported inline: {type(node).__name__}")