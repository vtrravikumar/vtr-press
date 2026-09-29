"""Conservative, offline spelling suggestions for OCR manuscript text.

This module is intentionally isolated: it does not alter the digitization pipeline.
It only considers lowercase alphabetic words in ordinary prose lines. Callers
must review the returned corrections and retain the original source text.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re
from typing import Iterable, Protocol


TOKEN_RE = re.compile(r"(?<![A-Za-z])[A-Za-z]{3,}(?![A-Za-z])")
URL_RE = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
PATH_RE = re.compile(r"(?:^|[\s:])(?:/|~[/])\S+")
TABLE_RE = re.compile(r"\|")
INLINE_CODE_RE = re.compile(r"(`+).*?\1")
ABBREVIATION_RE = re.compile(r"\b(?:[A-Z]\.){2,}")
ENGINE_NAME = "pyspellchecker"


class CandidateEngine(Protocol):
    def candidates(self, word: str) -> set[str]: ...


@dataclass(frozen=True)
class Correction:
    original: str
    corrected: str
    start: int
    end: int
    corrected_start: int
    corrected_end: int
    context: str
    reason: str
    engine: str
    engine_version: str


@dataclass(frozen=True)
class SpellcheckResult:
    text: str
    corrections: tuple[Correction, ...]

    def to_report(self) -> dict:
        """Return JSON-serializable correction data; writing reports is caller-owned."""
        return {
            "engine": ENGINE_NAME,
            "correction_count": len(self.corrections),
            "corrections": [asdict(item) for item in self.corrections],
        }


def load_vocabulary(*paths: str | Path) -> frozenset[str]:
    """Load UTF-8 custom terms, one per line; ignore blanks and # comments."""
    words: set[str] = set()
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            term = line.strip()
            if term and not term.startswith("#"):
                words.add(term.casefold())
    return frozenset(words)


def _edit_distance_one(left: str, right: str) -> bool:
    """Return whether words differ by one insertion, deletion, substitution,
    or adjacent transposition.
    """
    if left == right or abs(len(left) - len(right)) > 1:
        return False

    rows, cols = len(left) + 1, len(right) + 1
    distance = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        distance[i][0] = i
    for j in range(cols):
        distance[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if left[i - 1] == right[j - 1] else 1
            distance[i][j] = min(
                distance[i - 1][j] + 1,
                distance[i][j - 1] + 1,
                distance[i - 1][j - 1] + cost,
            )
            if (
                i > 1 and j > 1
                and left[i - 1] == right[j - 2]
                and left[i - 2] == right[j - 1]
            ):
                distance[i][j] = min(
                    distance[i][j], distance[i - 2][j - 2] + 1
                )
    return distance[-1][-1] == 1


def _default_engine() -> tuple[CandidateEngine, str]:
    try:
        from spellchecker import SpellChecker
    except ImportError as exc:
        raise RuntimeError(
            "Spellchecking requires pyspellchecker. Install it separately; "
            "this isolated module does not modify project dependencies."
        ) from exc
    try:
        engine_version = version("pyspellchecker")
    except PackageNotFoundError:
        engine_version = "unknown"
    return SpellChecker(), engine_version


def _protected_line(line: str, in_fence: bool) -> bool:
    stripped = line.lstrip()
    if in_fence or stripped.startswith("```") or stripped.startswith("~~~"):
        return True
    if TABLE_RE.search(line) or URL_RE.search(line) or PATH_RE.search(line):
        return True
    if ABBREVIATION_RE.search(line):
        return True
    # Code-like lines are excluded as a whole rather than risking partial edits.
    if any(marker in line for marker in ("=", "=>", "==", "def ", "class ")):
        return True
    return False


def _context(text: str, start: int, end: int, radius: int = 36) -> str:
    return text[max(0, start - radius):min(len(text), end + radius)]


def correct_prose(
    text: str,
    *,
    vocabulary: Iterable[str] = (),
    engine: CandidateEngine | None = None,
    engine_version: str | None = None,
) -> SpellcheckResult:
    """Suggest only unambiguous one-edit corrections in eligible prose.

    The input is never mutated. Capitalized words, protected lines, custom
    vocabulary, and ambiguous suggestions are left unchanged.
    """
    if engine is None:
        engine, detected_version = _default_engine()
        engine_version = engine_version or detected_version
    engine_version = engine_version or "injected"
    custom = {word.casefold() for word in vocabulary}

    proposed: list[tuple[int, int, str, str]] = []
    offset = 0
    in_fence = False

    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            offset += len(line)
            continue
        if _protected_line(line, in_fence):
            offset += len(line)
            continue

        inline_code_spans = [
            (match.start(), match.end()) for match in INLINE_CODE_RE.finditer(line)
        ]
        is_heading = line.lstrip().startswith("#")
        for match in TOKEN_RE.finditer(line):
            if any(
                match.start() < code_end and match.end() > code_start
                for code_start, code_end in inline_code_spans
            ):
                continue
            word = match.group(0)
            if word.isupper() or (not word.islower() and not (is_heading and word.istitle())):
                continue
            normalized = word.casefold()
            if normalized in custom:
                continue
            # Some dictionary lookups return None when no suggestions exist.
            # Treat that as an empty candidate set rather than aborting publishing.
            suggestions = engine.candidates(normalized) or ()
            candidates = {
                candidate.casefold()
                for candidate in suggestions
                if candidate.isalpha() and candidate.islower()
                and _edit_distance_one(normalized, candidate.casefold())
            }
            if len(candidates) == 1:
                corrected = next(iter(candidates))
                if word.istitle():
                    corrected = corrected.capitalize()
                if corrected != word:
                    proposed.append((
                        offset + match.start(),
                        offset + match.end(),
                        word,
                        corrected,
                    ))
        offset += len(line)

    # Calculate final positions while applying edits left-to-right.
    output_parts: list[str] = []
    corrections: list[Correction] = []
    cursor = 0
    shift = 0
    for start, end, original, corrected in proposed:
        output_parts.append(text[cursor:start])
        corrected_start = start + shift
        output_parts.append(corrected)
        corrections.append(Correction(
            original=original,
            corrected=corrected,
            start=start,
            end=end,
            corrected_start=corrected_start,
            corrected_end=corrected_start + len(corrected),
            context=_context(text, start, end),
            reason="unique candidate at Damerau-Levenshtein distance 1",
            engine=ENGINE_NAME,
            engine_version=engine_version,
        ))
        shift += len(corrected) - (end - start)
        cursor = end
    output_parts.append(text[cursor:])

    return SpellcheckResult("".join(output_parts), tuple(corrections))


MARKDOWN_LINK_DEST_RE = re.compile(r"(?<=\])\([^)]*\)")
MARKDOWN_AUTOLINK_RE = re.compile(r"<https?://[^>]+>", re.IGNORECASE)
MARKDOWN_REFERENCE_SUFFIX_RE = re.compile(r"(?<=\])\[[^]]*\]")
MARKDOWN_REFERENCE_DEFINITION_RE = re.compile(r"(?m)^[ \t]{0,3}\[[^]]+\]:[^\r\n]*")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
NO_SPELLCHECK_RE = re.compile(r"<no-spellcheck>.*?</no-spellcheck>", re.DOTALL)
NO_SPELLCHECK_TAG_RE = re.compile(r"</?no-spellcheck>")


def _blank_span(chars: list[str], start: int, end: int) -> None:
    """Mask a span without changing offsets or line boundaries."""
    for index in range(start, end):
        if chars[index] not in "\r\n":
            chars[index] = " "


def _markdown_prose_view(text: str) -> str:
    """Return a same-length view with non-prose Markdown spans masked."""
    chars = list(text)

    # Mask fenced code, including its delimiters.
    offset = 0
    in_fence = False
    fence_char = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        opening = re.match(r"(`{3,}|~{3,})", stripped)
        if not in_fence and opening:
            in_fence = True
            fence_char = opening.group(1)[0]
            fence_length = len(opening.group(1))
            _blank_span(chars, offset, offset + len(line))
        elif in_fence:
            _blank_span(chars, offset, offset + len(line))
            closing = re.match(r"(`{3,}|~{3,})[ \\t]*(?:\\r?\\n)?$", stripped)
            if closing and closing.group(1)[0] == fence_char and len(closing.group(1)) >= fence_length:
                in_fence = False
        offset += len(line)

    view = "".join(chars)

    # Mask explicit spellcheck exclusions, including the enclosed text.
    for match in NO_SPELLCHECK_RE.finditer("".join(chars)):
        _blank_span(chars, match.start(), match.end())

    # Mask HTML comments such as OCR source metadata without changing offsets.
    for match in HTML_COMMENT_RE.finditer("".join(chars)):
        _blank_span(chars, match.start(), match.end())

    # Mask inline code and link destinations while preserving link labels.
    for pattern in (INLINE_CODE_RE, MARKDOWN_LINK_DEST_RE, MARKDOWN_REFERENCE_SUFFIX_RE, MARKDOWN_REFERENCE_DEFINITION_RE, MARKDOWN_AUTOLINK_RE):
        for match in pattern.finditer(view):
            _blank_span(chars, match.start(), match.end())

    # Mask bare URLs and filesystem paths, but retain surrounding prose.
    view = "".join(chars)
    for match in re.finditer(r"https?://\S+|www\.\S+", view, re.IGNORECASE):
        _blank_span(chars, match.start(), match.end())
    view = "".join(chars)
    for match in re.finditer(r"(?<!\w)(?:/|~/)\S+", view):
        _blank_span(chars, match.start(), match.end())

    return "".join(chars)


def check_markdown(
    text: str,
    *,
    vocabulary: Iterable[str] = (),
    engine: CandidateEngine | None = None,
    engine_version: str | None = None,
) -> SpellcheckResult:
    """Check Markdown prose without modifying the supplied Markdown.

    Headings, paragraphs, list items, and link labels are eligible. Fenced and
    inline code, tables, link destinations, URLs, and paths are excluded.
    Correction offsets refer to the original Markdown string.
    """
    prose_view = _markdown_prose_view(text)
    checked = correct_prose(
        prose_view,
        vocabulary=vocabulary,
        engine=engine,
        engine_version=engine_version,
    )

    # The masked view is only for detection. Return original text and contexts.
    corrections = tuple(
        Correction(
            original=item.original,
            corrected=item.corrected,
            start=item.start,
            end=item.end,
            corrected_start=item.start,
            corrected_end=item.end,
            context=_context(text, item.start, item.end),
            reason=item.reason,
            engine=item.engine,
            engine_version=item.engine_version,
        )
        for item in checked.corrections
    )
    return SpellcheckResult(text, corrections)


def apply_corrections(text: str, corrections: Iterable[Correction]) -> str:
    """Apply recorded corrections to a separate copy of their source text.

    Corrections are applied from right to left so original offsets remain
    valid. Stale, mismatched, or overlapping spans are rejected.
    """
    ordered = sorted(corrections, key=lambda item: (item.start, item.end))
    previous_end = 0
    for item in ordered:
        if item.start < 0 or item.end > len(text) or item.start >= item.end:
            raise ValueError("Correction span is outside the source text")
        if item.start < previous_end:
            raise ValueError("Correction spans overlap")
        if text[item.start:item.end] != item.original:
            raise ValueError("Correction no longer matches source text")
        previous_end = item.end

    corrected = text
    for item in reversed(ordered):
        corrected = corrected[:item.start] + item.corrected + corrected[item.end:]
    return corrected


def strip_no_spellcheck_markup(text: str) -> str:
    """Remove paired no-spellcheck markers while preserving their enclosed text."""
    return NO_SPELLCHECK_TAG_RE.sub("", text)
