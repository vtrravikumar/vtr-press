"""Run statistics for reproducible document digitization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass
class DocumentStats:
    """Timing and processing statistics for one source document."""

    filename: str
    profile: str
    pages: int
    started_at: str
    ended_at: str
    duration_seconds: float
    average_seconds_per_page: float
    page_durations_seconds: list[float] = field(default_factory=list)


@dataclass
class RunStats:
    """Machine-readable record of one complete digitization run."""

    run_started_at: str
    run_ended_at: str
    source: str
    document_count: int
    total_pages: int
    renderer: str
    ocr_engine: str
    preprocessing: str
    output_manuscript: str
    total_duration_seconds: float
    average_seconds_per_page: float
    documents: list[DocumentStats] = field(default_factory=list)
    combined_sources: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def utc_timestamp() -> str:
    """Return a stable ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_run_stats(stats: RunStats, output_dir: str | Path) -> Path:
    """Write a timestamped JSON run record and return its path."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = stats.run_started_at.replace(":", "-").replace("Z", "")
    filename = timestamp.replace("T", "_") + ".json"
    path = directory / filename
    path.write_text(json.dumps(stats.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path
