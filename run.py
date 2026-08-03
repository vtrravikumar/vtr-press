"""
Development runner for VTR Press.

Usage
-----

python run.py engineering
python run.py memoir
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from publish import publish_all


ROOT = Path(__file__).parent

BOOKS_FILE = ROOT / "books.yaml"
GENERATED_DIR = ROOT / "generated"
OUTPUT_DIR = ROOT / "output"


def load_books() -> dict:
    """Load the books configuration."""

    with BOOKS_FILE.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)["books"]


def main() -> None:

    if len(sys.argv) != 2:
        print("Usage:")
        print("    python run.py <book>")
        print()
        print("Example:")
        print("    python run.py engineering")
        sys.exit(1)

    book_name = sys.argv[1]

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

    cover = (ROOT / config["cover"]).resolve()
    manuscript = (ROOT / config["manuscript"]).resolve()

    output_name = config["output_name"]

    #
    # Stage book assets
    #

    cover_suffix = cover.suffix.lower() or ".png"
    cover_filename = f"cover{cover_suffix}"

    book_assets = GENERATED_DIR / "assets" / "books" / output_name
    book_assets.mkdir(parents=True, exist_ok=True)

    staged_cover = book_assets / cover_filename

    shutil.copy2(
        cover,
        staged_cover,
    )

    #
    # Generate publication formats
    #

    typst_source, epub_source = publish_all(
        manuscript,
        cover,
        f"/generated/assets/books/{output_name}/{cover_filename}",
    )

    typ_file = GENERATED_DIR / f"{output_name}.typ"
    pdf_file = OUTPUT_DIR / f"{output_name}.pdf"
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

    subprocess.run(
        [
            "typst",
            "compile",
            "--root",
            str(ROOT),
            str(typ_file),
            str(pdf_file),
        ],
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

    #
    # Success
    #

    print()
    print(f"✓ PDF    output/{pdf_file.name}")
    print(f"✓ EPUB   output/{epub_file.name}")
    print(f"✓ ISBN   isbn/{output_name}/")
    print()
    print("Done.")


if __name__ == "__main__":
    main()