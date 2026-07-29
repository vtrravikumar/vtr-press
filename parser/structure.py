"""
Build the document hierarchy from Markdown.

This module understands only the structural elements of the manuscript.

It creates the Book, Part, Chapter, Scene, Section and Block objects.

Inline formatting is intentionally ignored and is handled later by
parser.inline.
"""

from __future__ import annotations

from exceptions import StructureError
from model import (
    Book,
    Chapter,
    Scene,
    Metadata,
    Paragraph,
    Part,
    Section,
    SectionKind,
    Text,
    Verse,
)


SECTION_MAP = {
    "copyright": SectionKind.COPYRIGHT,
    "dedication": SectionKind.DEDICATION,
    "thirukkural": SectionKind.THIRUKKURAL,
    "prologue": SectionKind.PROLOGUE,
    "preface": SectionKind.PREFACE,
    "foreword": SectionKind.FOREWORD,
    "acknowledgements": SectionKind.ACKNOWLEDGEMENTS,
    "epilogue": SectionKind.EPILOGUE,
    "about the author": SectionKind.ABOUT_AUTHOR,
}


def parse_structure(metadata: Metadata, body: str) -> Book:
    """
    Parse the Markdown body into a Book model.
    """

    book = Book(metadata=metadata)

    current_part: Part | None = None
    current_chapter: Chapter | None = None
    current_scene: Scene | None = None
    current_section: Section | None = None

    chapter_number = 0

    paragraph: list[str] = []

    verse: list[str] = []
    in_verse = False

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _ensure_scene() -> Scene:
        """
        Return the current scene.

        If the manuscript contains no explicit scene headings,
        automatically create an untitled scene so older books
        continue to work unchanged.
        """

        nonlocal current_scene

        if current_scene is None:

            if current_chapter is None:
                raise StructureError(
                    "Content found outside a Chapter."
                )

            current_scene = Scene(title=None)
            current_chapter.scenes.append(current_scene)

        return current_scene

    def flush_paragraph() -> None:
        """Create a Paragraph block from accumulated lines."""

        nonlocal paragraph

        if not paragraph:
            return

        text = "\n".join(paragraph).strip()
        paragraph = []

        if not text:
            return

        block = Paragraph(
            children=[
                Text(text=text)
            ]
        )

        if current_chapter is not None:

            _ensure_scene().blocks.append(block)

        elif current_section is not None:

            current_section.blocks.append(block)

        else:
            raise StructureError(
                "Paragraph found outside a Section or Chapter."
            )

    def flush_verse() -> None:
        """Create a Verse block from accumulated lines."""

        nonlocal verse

        if not verse:
            return

        block = Verse(
            lines=verse.copy(),
        )

        verse.clear()

        if current_chapter is not None:

            _ensure_scene().blocks.append(block)

        elif current_section is not None:

            current_section.blocks.append(block)

        else:
            raise StructureError(
                "Verse found outside a Section or Chapter."
            )

    # ----------------------------------------------------------
    # Parse document
    # ----------------------------------------------------------

    for raw_line in body.splitlines():

        line = raw_line.rstrip()



        # ----------------------------------------------------------
        # Verse block
        # ----------------------------------------------------------

        if line == ":::verse":

            flush_paragraph()
            in_verse = True
            verse.clear()
            continue

        if line == ":::" and in_verse:

            flush_verse()
            verse.clear()
            in_verse = False
            continue

        if in_verse:

            verse.append(line)
            continue

        # ----------------------------------------------------------
        # Blank line
        # ----------------------------------------------------------

        if not line:
            flush_paragraph()
            continue

        # ----------------------------------------------------------
        # Book title
        # ----------------------------------------------------------

        if line.startswith("# "):

            flush_paragraph()
            flush_verse()

            # Title comes from YAML front matter.
            continue

        # ----------------------------------------------------------
        # Part / Section
        # ----------------------------------------------------------

        if line.startswith("## "):

            flush_paragraph()
            flush_verse()

            title = line[3:].strip()
            key = title.lower()

            if key.startswith("part "):

                current_part = Part(title=title)
                book.sections.append(current_part)

                current_chapter = None
                current_scene = None
                current_section = None

            else:

                kind = SECTION_MAP.get(key, SectionKind.OTHER)

                current_section = Section(
                    kind=kind,
                    title=title,
                )

                book.sections.append(current_section)

                current_part = None
                current_chapter = None
                current_scene = None

            continue

        # ----------------------------------------------------------
        # Chapter
        # ----------------------------------------------------------

        if line.startswith("### "):

            flush_paragraph()
            flush_verse()

            if current_part is None:
                raise StructureError(
                    f"Chapter found outside a Part: {line}"
                )

            chapter_number += 1

            current_chapter = Chapter(
                number=chapter_number,
                title=line[4:].strip(),
            )

            current_part.chapters.append(current_chapter)

            current_scene = None

            continue

        # ----------------------------------------------------------
        # Scene
        # ----------------------------------------------------------

        if line.startswith("#### "):

            flush_paragraph()
            flush_verse()

            if current_chapter is None:
                raise StructureError(
                    f"Scene found outside a Chapter: {line}"
                )

            current_scene = Scene(
                title=line[5:].strip(),
            )

            current_chapter.scenes.append(current_scene)

            continue

        # ----------------------------------------------------------
        # Regular paragraph
        # ----------------------------------------------------------

        paragraph.append(line)

    if in_verse:
        raise StructureError(
            "Unterminated :::verse block."
        )

    flush_paragraph()
    flush_verse()

    return book