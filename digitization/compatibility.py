"""VTR Press manuscript compatibility helpers for digitization output."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .structure import PageStructure


@dataclass(frozen=True)
class DigitizedMetadata:
    """Metadata that can be safely emitted from source material."""

    title: str = ""
    subtitle: str = ""
    author: str = ""
    document_type: str = "technical-document"
    language: str = "en"
    edition: str = ""
    version: str = ""
    copyright_year: str = ""


def _clean_line(line: str) -> str:
    line = re.sub(r"^[|{}\[\]<>*_~`'\".,:;]+", "", line)
    line = re.sub(r"[|{}\[\]<>*_~`]+$", "", line)
    return re.sub(r"\s+", " ", line).strip()


def _yaml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def extract_metadata(first_page_text: str) -> DigitizedMetadata:
    """Extract only high-confidence metadata from a title page.

    The extractor is intentionally conservative. Unknown fields remain blank
    so digitization never invents publication metadata.
    """
    lines = [_clean_line(line) for line in first_page_text.splitlines()]
    lines = [line for line in lines if line]

    title = ""
    subtitle = ""
    author_lines: list[str] = []

    try:
        project_index = next(i for i, line in enumerate(lines) if "PROJECT REPORT" in line.upper())
    except StopIteration:
        project_index = -1

    if project_index >= 0:
        candidates = lines[project_index + 1:]
        for index, line in enumerate(candidates):
            upper = line.upper()
            if "SUBMITTED BY" in upper:
                break
            if upper == "ON" or not line:
                continue
            if line.startswith("(") and line.endswith(")"):
                subtitle = line.strip("() ")
                continue
            if not title and len(line.split()) >= 3:
                title = line
                continue
    else:
        # Fallback: choose the longest all-uppercase line near the top.
        for line in lines[:20]:
            if len(line.split()) >= 3 and line.upper() == line and "DEPARTMENT" not in line:
                if len(line) > len(title):
                    title = line

    try:
        submitted_index = next(i for i, line in enumerate(lines) if "SUBMITTED BY" in line.upper())
    except StopIteration:
        submitted_index = -1

    if submitted_index >= 0:
        for line in lines[submitted_index + 1:]:
            upper = line.upper()
            if "DEPARTMENT" in upper or "COLLEGE" in upper or "UNIVERSITY" in upper:
                break
            # Names are normally short title/name lines. Ignore obvious scan noise.
            if 1 < len(line.split()) <= 5 and re.search(r"[A-Za-z]", line):
                author_lines.append(line)

    author = "; ".join(author_lines)
    return DigitizedMetadata(
        title=title,
        subtitle=subtitle,
        author=author,
    )


def build_front_matter(metadata: DigitizedMetadata) -> str:
    """Build YAML front matter using the VTR Press metadata contract."""
    return "\n".join(
        [
            "---",
            f"title: {_yaml_string(metadata.title)}",
            f"subtitle: {_yaml_string(metadata.subtitle)}",
            f"author: {_yaml_string(metadata.author)}",
            f"type: {_yaml_string(metadata.document_type)}",
            f"edition: {_yaml_string(metadata.edition)}",
            f"version: {_yaml_string(metadata.version)}",
            f"copyright_year: {_yaml_string(metadata.copyright_year)}",
            f"language: {_yaml_string(metadata.language)}",
            "---",
        ]
    )


_NUMBERED_HEADING = re.compile(
    r"^\s*(\d+(?:\.\d+){0,5})[.)]?\s+(.+?)\s*$"
)

_TOP_LEVEL_LABELS = {
    "ABSTRACT",
    "ACKNOWLEDGEMENT",
    "ACKNOWLEDGEMENTS",
    "INTRODUCTION",
    "CONCLUSION",
    "REFERENCES",
    "BIBLIOGRAPHY",
    "APPENDIX",
    "APPENDICES",
}


def _heading_level(number: str) -> int:
    return min(number.count(".") + 1, 4)


def normalize_ocr_headings(text: str, structure: PageStructure | None) -> str:
    """Convert only high-confidence source headings to VTR Press Markdown.

    Printed numeric prefixes are removed because VTR Press owns rendered
    numbering. Ambiguous lines are left untouched rather than guessed.
    """
    if structure is PageStructure.CODE:
        return text

    output: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            output.append(raw_line)
            continue

        match = _NUMBERED_HEADING.match(line)
        if match:
            heading = match.group(2).strip()
            # Require a short, heading-like line. This prevents numbered prose
            # and lists from being promoted to headings.
            if len(heading.split()) <= 14 and not heading.endswith((".", ";", ":")):
                output.append("#" * _heading_level(match.group(1)) + " " + heading)
                continue

        cleaned = _clean_line(line)
        if (
            cleaned.upper() in _TOP_LEVEL_LABELS
            and len(cleaned.split()) <= 4
        ):
            output.append("# " + cleaned.title())
            continue

        output.append(raw_line)

    return "\n".join(output)


def validate_vtr_press_markdown(markdown: str) -> tuple[str, ...]:
    """Return compatibility errors; an empty tuple means structurally valid."""
    errors: list[str] = []
    text = markdown.lstrip()
    if not text.startswith("---\n"):
        errors.append("missing YAML front matter")
    else:
        closing = text.find("\n---\n", 4)
        if closing < 0:
            errors.append("malformed YAML front matter")
        else:
            front = text[4:closing]
            for key in ("title:", "subtitle:", "author:", "type:", "language:"):
                if not re.search(rf"(?m)^{re.escape(key)}", front):
                    errors.append(f"missing metadata field: {key[:-1]}")
            if not re.search(r"(?m)^type:\s*[\"']?technical-document[\"']?\s*$", front):
                errors.append("digitization default document type must be technical-document")

    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            heading = match.group(2)
            if re.match(r"^\d+(?:\.\d+){0,5}[.)]?\s+", heading):
                errors.append("generated heading contains printed section numbering")
            if len(match.group(1)) > 4:
                errors.append("heading depth exceeds digitization contract of four levels")

    return tuple(dict.fromkeys(errors))
