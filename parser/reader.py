"""
Read a manuscript file and extract metadata and body.

This module is responsible only for reading the file and parsing the
YAML front matter. It performs no structural parsing.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from exceptions import FrontMatterError
from model import Metadata


def read(path: str | Path) -> tuple[Metadata, str]:
    """
    Read a manuscript file.

    Parameters
    ----------
    path
        Path to the manuscript Markdown file.

    Returns
    -------
    tuple[Metadata, str]
        A tuple containing the book metadata and the Markdown body.

    Raises
    ------
    FileNotFoundError
        If the manuscript file does not exist.

    FrontMatterError
        If the YAML front matter is missing or invalid.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    text = path.read_text(encoding="utf-8")

    # --------------------------------------------------------------
    # Skip leading whitespace
    # --------------------------------------------------------------

    text = text.lstrip()

    # --------------------------------------------------------------
    # Skip leading HTML comments
    # --------------------------------------------------------------

    while text.startswith("<!--"):

        end = text.find("-->")

        if end == -1:
            raise FrontMatterError("Unterminated HTML comment.")

        text = text[end + 3:].lstrip()

    # --------------------------------------------------------------
    # Optional YAML front matter
    # --------------------------------------------------------------

    if not text.startswith("---"):
        return Metadata(), text

    # Find the closing YAML delimiter.
    end = text.find("\n---\n", 3)

    if end == -1:
        raise FrontMatterError("Malformed YAML front matter.")

    yaml_text = text[4:end]
    body = text[end + 5:]

    try:
        data = yaml.safe_load(yaml_text) or {}

    except yaml.YAMLError as exc:
        raise FrontMatterError("Invalid YAML front matter.") from exc

    if not isinstance(data, dict):
        raise FrontMatterError(
            "YAML front matter must contain key-value pairs."
        )

    metadata = Metadata(
        title=data.get("title", ""),
        subtitle=data.get("subtitle", ""),
        author=data.get("author", ""),

        type=data.get("type", "book"),

        edition=data.get("edition", ""),
        version=data.get("version", ""),
        copyright_year=str(data.get("copyright_year", "")),

        paper=data.get("paper", ""),
        language=data.get("language", ""),
    )

    return metadata, body.lstrip()