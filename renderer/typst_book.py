"""
Render a Book AST into Typst source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from model import (
    Block,
    Book,
    Chapter,
    Image,
    ListBlock,
    Paragraph,
    Part,
    Scene,
    Section,
    SectionKind,
    Subheading,
    Verse,
    CodeBlock,
)
from renderer.document_assets import DocumentAssets
from renderer.typst_common import TypstCommonMixin
DEFAULT_THEME_IMPORT = "../themes/classic/theme.typ"

# Type -> theme import path. An unrecognized (or omitted) type falls
# back to DEFAULT_THEME_IMPORT (classic/book) at this level -- but
# every real manuscript is validated against SUPPORTED_DOCUMENT_TYPES
# in parser/reader.py before it ever reaches this dict, and an
# unrecognized value is rejected there with a clear error (Decision
# Log item 1, resolved). This fallback exists only for callers that
# construct a Book/Metadata directly, bypassing the parser (as many
# tests in this file do).
THEME_IMPORT_BY_TYPE: dict[str, str] = {
    "book": DEFAULT_THEME_IMPORT,
    "technical-document": "../themes/technical/theme.typ",
}


@dataclass(slots=True)
class RenderOptions:
    """Options that customize Typst rendering for publication variants."""

    print_mode: bool = False


def render(
    book: Book,
    cover_path: str = "/assets/books/current/cover.png",
    options: RenderOptions | None = None,
) -> str:
    """Render a Book AST into Typst."""

    renderer = TypstBookRenderer(cover_path, options)
    return renderer.render(book)


class TypstBookRenderer(TypstCommonMixin):
    """Typst renderer."""

    def __init__(
        self,
        cover_path: str,
        options: RenderOptions | None = None,
        document_assets: DocumentAssets | None = None,
    ) -> None:
        self.lines: list[str] = []
        self.cover_path = cover_path
        self.options = options or RenderOptions()
        self.document_assets = document_assets
        # Tracks whether we've already rendered the first printable page.
        self._first_page = True
        # Tracks whether the table of contents has been inserted.
        self._contents_inserted = False
        self._main_matter_open = False
        self._print_book = False

    # ------------------------------------------------------------------
    # Typst Escaping
    # ------------------------------------------------------------------

    def _escape_text(self, text: str) -> str:
        """Escape plain text for Typst."""

        return (
            self._plain(text)
            .replace("\\", "\\\\")
            .replace("#", "\\#")
            .replace("@", "\\@")
        )

    def _escape_string(self, text: str) -> str:
        """Escape Typst string literals."""

        return self._plain(text).replace("\\", "\\\\").replace('"', '\\"')

    def _plain(self, value: object) -> str:
        """Return a safe string for Typst output."""

        if value is None:
            return ""

        return str(value)

    def _running_title(self, title: str) -> str:
        """Return a title suitable for running heads."""

        return re.sub(
            r"^chapter\s+\S+\s*[-–—:]\s*",
            "",
            title,
            flags=re.IGNORECASE,
        )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def render(self, book: Book) -> str:
        self._print_book = self.options.print_mode and book.metadata.type == "book"
        self._render_preamble(book)
        # Cover is a print-and-book-only concept for now: print mode
        # produces a print-on-demand interior with no embedded cover,
        # and technical documents (per SPECIFICATION.md's A4/no-cover
        # convention) don't get one either. This is a direct type
        # check, not a convention-profile system -- Phase D is where
        # "does this document get a cover" becomes a generic property
        # the renderer reads rather than a type comparison here.
        if not self.options.print_mode and book.metadata.type == "book":
            self._render_cover()
        self._render_title_page(book)
        for item in book.sections:
            if isinstance(item, Section):
                if self._skip_section(item):
                    continue

                self._render_section(item)

            elif isinstance(item, Part):
                self._render_part(item)

        if self._main_matter_open:
            self.lines.append("]")

        return "\n".join(self.lines).rstrip() + "\n"

    # ------------------------------------------------------------------
    # Document Preamble
    # ------------------------------------------------------------------

    def _render_preamble(self, book: Book) -> None:
        """Emit the Typst document preamble."""

        md = book.metadata

        theme_import = THEME_IMPORT_BY_TYPE.get(md.type, DEFAULT_THEME_IMPORT)

        self.lines.append(f'#import "{theme_import}": *')
        self.lines.append("")
        self.lines.append("#show: initialize-theme.with(")
        self.lines.append(f'  book-title: "{self._escape_string(md.title)}",')
        self.lines.append(f'  book-author: "{self._escape_string(md.author)}",')
        self.lines.append(")")
        self.lines.append("")

    # ------------------------------------------------------------------
    # Cover
    # ------------------------------------------------------------------

    def _render_cover(self) -> None:
        """Render a full-page digital cover."""

        self.lines.append(f'#render-cover("{self._escape_string(self.cover_path)}")')
        self.lines.append("")
        self.lines.append("#pagebreak()")
        self.lines.append("")

    # ------------------------------------------------------------------
    # Title Page
    # ------------------------------------------------------------------

    def _render_title_page(self, book: Book) -> None:
        """Render the title page."""

        md = book.metadata

        self.lines.append("#render-title-page(")
        self.lines.append(f'  title: "{self._escape_string(md.title)}",')
        self.lines.append(f'  subtitle: "{self._escape_string(md.subtitle)}",')
        self.lines.append(f'  author: "{self._escape_string(md.author)}",')
        self.lines.append(
            f'  copyright-year: "{self._escape_string(md.copyright_year)}",'
        )
        if self.options.print_mode:
            self.lines.append("  show-publisher-logo: false,")
        self.lines.append(")")
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

        # Route this through _page_break() (rather than an
        # unconditional raw #pagebreak()) so the _first_page
        # suppression applies here too. Without it, a document whose
        # first section is also the one that triggers Contents (no
        # front matter in between -- e.g. a technical document with
        # no Prologue) gets two consecutive #pagebreak() calls with
        # nothing rendered between them: the title page's own trailing
        # pagebreak, immediately followed by this one. That produces
        # a genuinely empty page with no enclosing page-styling
        # function active, which Typst then renders at its own
        # built-in default page size rather than the theme's.
        self._page_break()
        self.lines.append("#render-contents()")
        self.lines.append("")

    # ------------------------------------------------------------------
    # Page Numbering
    # ------------------------------------------------------------------

    def _start_main_matter(self) -> None:
        """Begin page numbering for the main matter."""

        self.lines.append("#main-matter[")
        self.lines.append("")
        self._main_matter_open = True

    def _recto_page_break(self) -> None:
        """Advance to the next right-hand page with blank inserts if needed."""

        self.lines.append("#blank-recto-pagebreak()")
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
            self.lines.append(f"{'=' * level} {self._escape_text(title)}")
            return

        self.lines.append("#heading(")
        self.lines.append(f"  level: {level},")
        self.lines.append("  outlined: false,")
        self.lines.append(f")[{self._escape_text(title)}]")

    # ------------------------------------------------------------------
    # Part
    # ------------------------------------------------------------------

    def _render_part(self, part: Part) -> None:

        if self._print_book:
            if not self._contents_inserted:
                self._render_contents()

            self._recto_page_break()

            if not self._main_matter_open:
                self._start_main_matter()
        else:
            self._page_break()

        part_page = "#print-part-page[" if self._print_book else "#part-page["
        self.lines.append(part_page)
        self.lines.append("")

        self._render_heading(1, part.title)
        self.lines.append("")
        self.lines.append("]")

        for index, chapter in enumerate(part.chapters):
            self._render_chapter(
                chapter,
                recto=self._print_book and index == 0,
            )

    # ------------------------------------------------------------------
    # Chapter
    # ------------------------------------------------------------------

    def _render_chapter(
        self,
        chapter: Chapter,
        recto: bool = False,
    ) -> None:

        if recto:
            self._recto_page_break()
        else:
            self._page_break()
        self.lines.append(
            "#chapter-page("
            f'"{self._escape_string(self._running_title(chapter.title))}"'
            ")["
        )
        self.lines.append("")

        self._render_heading(2, chapter.title)
        self.lines.append("")

        for scene in chapter.scenes:
            self._render_scene(scene)

        self.lines.append("]")

    # ------------------------------------------------------------------
    # Scene
    # ------------------------------------------------------------------

    def _render_scene(self, scene: Scene) -> None:
        """Render a scene within a chapter."""

        if scene.title:
            self.lines.append(f"#render-scene-title[{self._escape_text(scene.title)}]")
            self.lines.append("")

        for block in scene.blocks:
            self._render_block(block)

    # ------------------------------------------------------------------
    # Section
    # ------------------------------------------------------------------

    def _skip_section(self, section: Section) -> bool:
        """Return whether a whole section is excluded for the active mode."""

        return self.options.print_mode and section.kind == SectionKind.BACK_COVER

    def _render_section(self, section: Section) -> None:

        needs_page_break = True

        outlined = section.kind not in {
            SectionKind.COPYRIGHT,
            SectionKind.DEDICATION,
            SectionKind.THIRUKKURAL,
        }
        heading_outlined = outlined and not (
            self._print_book and outlined and not self._main_matter_open
        )

        # Insert the Contents page and begin main-matter numbering at
        # the first section that participates in the outline. For a
        # book, that's normally the Prologue (Copyright/Dedication/
        # Thirukkural are front matter, not outlined). For a technical
        # document with no Prologue, it's whichever ordinary section
        # comes first -- without this, such a document never opens
        # main-matter at all, and any outlined section appearing
        # before this point would render with the raw, un-reset page
        # counter instead of the properly numbered main matter.
        if not self._contents_inserted and outlined:
            self._render_contents()
            self.lines.append("#pagebreak()")
            self.lines.append("")

            if not self._print_book:
                # Start numbering from this section. Print books keep
                # front matter, including Prologue, unnumbered; their
                # main matter begins at Part I instead.
                self._start_main_matter()

            self._contents_inserted = True
            needs_page_break = False

        if needs_page_break:
            self._page_break()

        if section.kind in {
            SectionKind.COPYRIGHT,
            SectionKind.DEDICATION,
            SectionKind.THIRUKKURAL,
        }:
            self.lines.append("#front-matter-page[")
            self.lines.append("")

        elif section.kind == SectionKind.BACK_COVER:
            self.lines.append("#back-cover-page[")
            self.lines.append("")

        elif outlined and self._print_book and not self._main_matter_open:
            self.lines.append("#front-matter-page[")
            self.lines.append("")

        elif outlined:
            self.lines.append(
                f'#running-section-page("{self._escape_string(section.title)}")['
            )
            self.lines.append("")

        if section.kind != SectionKind.BACK_COVER:
            self._render_heading(
                2,
                section.title,
                outlined=heading_outlined,
            )
            self.lines.append("")

        centered_section = section.kind in {
            SectionKind.COPYRIGHT,
            SectionKind.DEDICATION,
            SectionKind.THIRUKKURAL,
        }

        if centered_section:
            self.lines.append("#centered-front-matter[")
            self.lines.append("")

        for block in section.blocks:
            if section.kind == SectionKind.COPYRIGHT and self._is_empty_isbn_paragraph(
                block
            ):
                continue

            self._render_block(block)

        if section.kind == SectionKind.COPYRIGHT and not self.options.print_mode:
            self.lines.append("#render-publisher-imprint()")
            self.lines.append("")

        if centered_section:
            self.lines.append("]")
            self.lines.append("")

        if (
            section.kind
            in {
                SectionKind.COPYRIGHT,
                SectionKind.DEDICATION,
                SectionKind.THIRUKKURAL,
                SectionKind.BACK_COVER,
            }
            or outlined
        ):
            self.lines.append("]")
            self.lines.append("")

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
        if isinstance(block, ListBlock):
            self._render_list(block)
            return
        if isinstance(block, Image):
            self._render_image(block)
            return
        if isinstance(block, Subheading):
            self._render_heading(block.level, block.title)
            self.lines.append("")
            return
        if isinstance(block, CodeBlock):
            self._render_code_block(block)
            return
        raise TypeError(f"Unsupported block: {type(block).__name__}")