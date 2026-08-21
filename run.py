"""
Development runner for VTR Press.

Usage
-----

python run.py engineering
python run.py memoir
python run.py memoir print
"""

from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from exceptions import FrontMatterError
from parser.reader import read
from publish import publish_all
from renderer.document_assets import DocumentAssets
from renderer.typst import RenderOptions


ROOT = Path(__file__).parent

BOOKS_FILE = ROOT / "books.yaml"
GENERATED_DIR = ROOT / "generated"
OUTPUT_DIR = ROOT / "output"


def load_books() -> dict:
    """Load the books configuration."""

    with BOOKS_FILE.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)["books"]


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        print("Usage:")
        print("    python run.py <book>")
        print("    python run.py <book> print")
        print()
        print("Example:")
        print("    python run.py engineering")
        print("    python run.py memoir print")
        sys.exit(1)

    book_name = sys.argv[1]
    print_mode = len(sys.argv) == 3

    if print_mode and sys.argv[2] != "print":
        print(f'Unknown publishing mode "{sys.argv[2]}"')
        print()
        print("Available optional modes:")
        print("  - print")
        sys.exit(1)

    render_options = RenderOptions(print_mode=print_mode)

    books = load_books()

    if book_name not in books:
        print(f'Unknown book "{book_name}"')
        print()
        print("Available books:")

        for name in books:
            print(f"  - {name}")

        sys.exit(1)

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = books[book_name]

    bookpath = (ROOT / config["bookpath"]).resolve()
    manuscript_config = config.get("manuscript", "manuscript.md")
    manuscript = (bookpath / manuscript_config).resolve()
    output_name = config["output_name"]

    # A cover is required for type: book; optional for every other
    # type (see VP-006/B2, which already makes cover rendering
    # book-only). The manuscript's own declared type decides this,
    # not whether books.yaml happens to have a "cover" entry.
    try:
        metadata, _ = read(manuscript)
    except FrontMatterError as exc:
        print(f"Error reading manuscript: {exc}")
        sys.exit(1)

    cover_config = config.get("cover")

    if metadata.type == "book" and not cover_config:
        print(
            f'Book "{book_name}" is type "book" and requires a '
            f'"cover" entry in books.yaml.'
        )
        sys.exit(1)

    cover = (ROOT / cover_config).resolve() if cover_config else None

    # Book assets are rooted at the book directory.
    #
    # Therefore a manuscript image reference such as:
    #
    #     assets/images/example.png
    #
    # resolves to:
    #
    #     <bookpath>/assets/images/example.png
    #
    assets_root = bookpath

    #
    # Stage book assets
    #

    typst_cover_path = None

    if cover is not None:
        cover_suffix = cover.suffix.lower() or ".png"
        cover_filename = f"cover{cover_suffix}"

        book_assets = GENERATED_DIR / "assets" / "books" / output_name
        book_assets.mkdir(parents=True, exist_ok=True)

        staged_cover = book_assets / cover_filename

        shutil.copy2(
            cover,
            staged_cover,
        )

        typst_cover_path = (
            f"/generated/assets/books/{output_name}/{cover_filename}"
        )

    #
    # Technical-document assets must remain staged until Typst
    # compilation has completed.
    #

    asset_context = (
        DocumentAssets(
            manuscript,
            assets_root=assets_root,
            staging_root=(
                GENERATED_DIR
                / "assets"
                / "documents"
                / output_name
            ),
        )
        if metadata.type == "technical-document"
        else nullcontext(None)
    )

    with asset_context as assets:

        #
        # Generate publication formats
        #

        typst_source, epub_source = publish_all(
            manuscript,
            cover,
            typst_cover_path,
            render_options=render_options,
            assets_root=assets_root,
            assets=assets,
        )

        typ_file = GENERATED_DIR / f"{output_name}.typ"

        pdf_filename = (
            f"{output_name}-interior.pdf"
            if print_mode
            else f"{output_name}.pdf"
        )

        pdf_file = OUTPUT_DIR / pdf_filename
        epub_file = OUTPUT_DIR / f"{output_name}.epub"

        typ_file.write_text(
            typst_source,
            encoding="utf-8",
        )

        epub_file.write_bytes(epub_source)

        #
        # Compile PDF
        #

        print()
        print("Compiling Typst...")
        print()

        compile_command = [
            "typst",
            "compile",
            "--root",
            str(ROOT),
        ]

        if print_mode:
            compile_command.extend(["--input", "print-mode=true"])

        compile_command.extend(
            [
                str(typ_file),
                str(pdf_file),
            ]
        )

        subprocess.run(
            compile_command,
            check=True,
        )

    #
    # Publish artifacts to ISBN workspace
    #

    isbn_dir = ROOT / "isbn" / output_name
    isbn_dir.mkdir(parents=True, exist_ok=True)

    for artifact in (pdf_file, epub_file):
        shutil.copy2(
            artifact,
            isbn_dir / artifact.name,
        )

    manifest_file = isbn_dir / "publication-manifest.md"

    manifest_file.write_text(
        publication_manifest(
            output_name,
            (pdf_file, epub_file),
        ),
        encoding="utf-8",
    )

    #
    # Success
    #

    print()
    print(f"✓ PDF    output/{pdf_file.name}")
    print(f"✓ EPUB   output/{epub_file.name}")
    print(f"✓ ISBN   isbn/{output_name}/")
    print(f"✓ Manifest isbn/{output_name}/{manifest_file.name}")
    print()
    print("Done.")


def publication_manifest(
    output_name: str,
    artifacts: tuple[Path, ...],
) -> str:
    """Return a manifest for the latest generated publication artifacts."""

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# {output_name} Publication Manifest",
        "",
        f"Generated: {timestamp}",
        "",
        "Use the files listed here for the current publication pass.",
        "",
        "## Artifacts",
        "",
    ]

    for artifact in artifacts:
        lines.extend(
            [
                f"### {artifact.name}",
                "",
                f"- Size: {artifact.stat().st_size} bytes",
                f"- SHA256: {_sha256(artifact)}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _sha256(path: Path) -> str:
    """Return the SHA256 digest for a generated artifact."""

    digest = hashlib.sha256()

    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


if __name__ == "__main__":
    main()