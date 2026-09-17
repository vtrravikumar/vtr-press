from pathlib import Path

import pytest

from digitization.assets import preserve_page_image


def test_preserve_page_image_copies_source(tmp_path: Path):
    source = tmp_path / "page-7.png"
    source.write_bytes(b"original-image")

    target = preserve_page_image(source, tmp_path / "assets")

    assert target == tmp_path / "assets" / "page-7.png"
    assert target.read_bytes() == b"original-image"


def test_preserve_page_image_rejects_missing_source(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        preserve_page_image(tmp_path / "missing.png", tmp_path / "assets")
