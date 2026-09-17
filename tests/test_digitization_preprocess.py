from pathlib import Path

import pytest

from digitization.preprocess import PassthroughPreprocessor, PreprocessConfig


def test_passthrough_preprocessor_preserves_source_bytes(tmp_path: Path):
    source = tmp_path / "page-1.png"
    source.write_bytes(b"source image bytes")

    output = PassthroughPreprocessor().process(source, tmp_path / "processed")

    assert output.name == source.name
    assert output.read_bytes() == source.read_bytes()


def test_passthrough_preprocessor_rejects_missing_image(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        PassthroughPreprocessor().process(tmp_path / "missing.png", tmp_path / "processed")


def test_passthrough_preprocessor_rejects_transform_mode():
    with pytest.raises(ValueError, match="copy_unchanged"):
        PassthroughPreprocessor(PreprocessConfig(copy_unchanged=False))
