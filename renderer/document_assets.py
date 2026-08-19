"""Asset resolution and persistent staging for technical documents.

This module is renderer-neutral. It resolves asset references from a
technical-document manuscript relative to the configured asset root and
stages existing assets into a persistent generated publication directory.

Missing assets are recorded rather than treated as fatal publication
errors.
"""

from __future__ import annotations

import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Self


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

    def __init__(
        self,
        manuscript_path: str | Path,
        assets_root: str | Path | None = None,
        staging_root: str | Path | None = None,
    ) -> None:
        self.manuscript_path = Path(manuscript_path).resolve()
        self.source_root = (
            Path(assets_root).resolve()
            if assets_root is not None
            else self.manuscript_path.parent
        )

        if staging_root is None:
            staging_root = (
                self.manuscript_path.parent
                / "generated"
                / "assets"
                / "documents"
                / self.manuscript_path.stem
            )

        self.staging_root = Path(staging_root).resolve()
        self.staging_root.mkdir(parents=True, exist_ok=True)

        self.assets_root = self.staging_root / "images"
        self.assets_root.mkdir(parents=True, exist_ok=True)

        self.missing: list[str] = []
        self._resolved: dict[str, ResolvedAsset] = {}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def close(self) -> None:
        """Retain generated staging for the current publication workspace."""
        return

    def resolve(self, source: str) -> ResolvedAsset | None:
        """Resolve and stage one manuscript-relative asset.

        Absolute filesystem paths are rejected deliberately. Technical
        document assets are expected to be referenced relative to the
        configured asset root.
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

        # Persistent staging is regenerated on every publication pass so
        # that the generated publication always reflects the current source.
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