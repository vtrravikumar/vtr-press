"""
Development runner for VTR Press.

Usage
-----

python run.py engineering
python run.py memoir
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from publish import publish


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

    manuscript = (ROOT / config["manuscript"]).resolve()

    output_name = config["output_name"]

    typst_source = publish(manuscript)

    typ_file = GENERATED_DIR / f"{output_name}.typ"

    typ_file.write_text(
        typst_source,
        encoding="utf-8",
    )

    pdf_file = OUTPUT_DIR / f"{output_name}.pdf"

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

    print()
    print("✓ Success")
    print()
    print(f"Book      : {book_name}")
    print(f"Source    : {manuscript}")
    print(f"Typst     : {typ_file}")
    print(f"PDF       : {pdf_file}")
    print()


if __name__ == "__main__":
    main()