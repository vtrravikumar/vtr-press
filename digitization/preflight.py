"""Preflight checks for digitization runtime dependencies.

The checks run before expensive PDF rendering/OCR work begins. They validate
Python packages selected by the CLI without changing the runtime environment.
"""

from __future__ import annotations

import importlib.util
import sys


def required_packages(
    *,
    pdf_renderer: str,
    ocr_engine: str,
    preprocess: str,
    combine_sources: bool,
) -> dict[str, str]:
    """Return import-name -> package-name requirements for the selected run."""
    requirements: dict[str, str] = {}

    if preprocess == "conservative":
        requirements["PIL"] = "Pillow"

    if pdf_renderer == "pymupdf" or combine_sources:
        requirements["pymupdf"] = "PyMuPDF"

    if ocr_engine == "macos-vision":
        requirements["ocrmac"] = "ocrmac"

    return requirements


def check_dependencies(
    *,
    pdf_renderer: str,
    ocr_engine: str,
    preprocess: str,
    combine_sources: bool,
) -> list[str]:
    """Return actionable dependency errors for the selected configuration."""
    missing = []
    for import_name, package_name in required_packages(
        pdf_renderer=pdf_renderer,
        ocr_engine=ocr_engine,
        preprocess=preprocess,
        combine_sources=combine_sources,
    ).items():
        if importlib.util.find_spec(import_name) is None:
            missing.append(
                f"{package_name} is required for this configuration "
                f"(import {import_name!r}); install it with "
                f"'python -m pip install {package_name}'"
            )
    return missing


def run_preflight(
    *,
    pdf_renderer: str,
    ocr_engine: str,
    preprocess: str,
    combine_sources: bool,
) -> None:
    """Fail fast when selected Python dependencies are unavailable."""
    errors = check_dependencies(
        pdf_renderer=pdf_renderer,
        ocr_engine=ocr_engine,
        preprocess=preprocess,
        combine_sources=combine_sources,
    )
    print(f"Python: {sys.executable}")
    if errors:
        raise SystemExit("Digitization preflight failed:\n- " + "\n- ".join(errors))
    print("Preflight: OK")
