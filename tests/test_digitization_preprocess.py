from pathlib import Path

import pytest
from PIL import Image

from digitization.preprocess import PassthroughPreprocessor, PillowPreprocessor, PreprocessConfig


def test_passthrough_preprocessor_preserves_source_bytes(tmp_path: Path):
    source = tmp_path / "page-1.png"
    source.write_bytes(b"source image bytes")

    output = PassthroughPreprocessor().process(source, tmp_path / "processed")

    assert output.name == source.name
    assert output.read_bytes() == source.read_bytes()


def test_passthrough_preprocessor_rejects_missing_image(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        PassthroughPreprocessor().process(tmp_path / "missing.png", tmp_path / "processed")


def test_pillow_preprocessor_creates_derived_png(tmp_path: Path):
    source = tmp_path / "page-1.jpg"
    Image.new("RGB", (20, 20), (120, 130, 140)).save(source)

    output = PillowPreprocessor().process(source, tmp_path / "processed")

    assert output.name == "page-1.png"
    assert output != source
    assert output.is_file()
    with Image.open(output) as image:
        assert image.mode == "L"


def test_pillow_preprocessor_thresholds_image(tmp_path: Path):
    source = tmp_path / "page.png"
    image = Image.new("L", (2, 1))
    image.putdata([50, 200])
    image.save(source)

    output = PillowPreprocessor(PreprocessConfig(threshold=128)).process(
        source, tmp_path / "processed"
    )

    with Image.open(output) as processed:
        assert list(processed.getdata()) == [0, 255]


def test_preprocess_config_rejects_invalid_threshold():
    with pytest.raises(ValueError, match="threshold"):
        PreprocessConfig(threshold=256)
