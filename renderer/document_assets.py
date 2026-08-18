"""Asset resolution and job-scoped staging for technical documents.

This module is renderer-neutral. It resolves asset references from a
technical-document manuscript relative to the manuscript location and
stages existing assets into an isolated temporary publication directory.

Missing assets are recorded rather than treated as fatal publication
errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import mimetypes
import shutil


@dataclass(frozen=True, slots=True)
class ResolvedAsset:
    """A source asset prepared for publication."""

    source: str
    source_path: Path
    staged_path: Path
    epub_href: str
    media_type: str


class DocumentAssets:
    """Resolve and stage assets referenced by one technical document."""

    def __init__(self, manuscript_path: str | Path) -> None:
        self.manuscript_path = Path(manuscript_path).resolve()
        self.source_root = self.manuscript_path.parent
        self._temporary_directory = TemporaryDirectory(
            prefix="vtr-press-document-"
        )
        self.staging_root = Path(self._temporary_directory.name)
        self.assets_root = self.staging_root / "assets"
        self.assets_root.mkdir(parents=True, exist_ok=True)
        self.missing: list[str] = []
        self._resolved: dict[str, ResolvedAsset] = {}

    def __enter__(self) -> "DocumentAssets":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def close(self) -> None:
        """Remove the job-specific staging directory."""
        self._temporary_directory.cleanup()

    def resolve(self, source: str) -> ResolvedAsset | None:
        """Resolve and stage one manuscript-relative asset.

        Absolute filesystem paths are rejected deliberately. Technical
        document assets are expected to be referenced relative to the
        manuscript source project.
        """
        if source in self._resolved:
            return self._resolved[source]

        source_path = Path(source)

        if source_path.is_absolute():
            self._record_missing(source)
            return None

        resolved_path = (self.source_root / source_path).resolve()

        if not resolved_path.is_file():
            self._record_missing(source)
            return None

        # Preserve the referenced filename while flattening the staged
        # publication asset namespace. A later refinement can introduce
        # collision-safe names if real documents demonstrate the need.
        staged_name = resolved_path.name
        staged_path = self.assets_root / staged_name

        if not staged_path.exists():
            shutil.copy2(resolved_path, staged_path)

        media_type = (
            mimetypes.guess_type(resolved_path.name)[0]
            or "application/octet-stream"
        )

        asset = ResolvedAsset(
            source=source,
            source_path=resolved_path,
            staged_path=staged_path,
            epub_href=f"images/{staged_name}",
            media_type=media_type,
        )

        self._resolved[source] = asset
        return asset

    def _record_missing(self, source: str) -> None:
        if source not in self.missing:
            self.missing.append(source)

    @property
    def resolved(self) -> tuple[ResolvedAsset, ...]:
        """Return all successfully resolved assets in resolution order."""
        return tuple(self._resolved.values())
