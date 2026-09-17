"""Tests for the VTR Press digitization OCR boundary."""

from pathlib import Path

import pytest

from digitization.ocr import OCRConfig, TesseractOCR


def test_ocr_config_defaults():
    config = OCRConfig()

    assert config.language == "eng"
    assert config.psm is None
    assert config.extra_args == ()


def test_ocr_missing_image_fails_before_invoking_engine(tmp_path: Path):
    ocr = TesseractOCR(config=OCRConfig(psm=6))

    with pytest.raises(FileNotFoundError):
        ocr.ocr_image(tmp_path / "missing.png")


def test_ocr_command_can_be_configured(monkeypatch, tmp_path: Path):
    image = tmp_path / "page.png"
    image.write_bytes(b"placeholder")

    calls = []

    class Result:
        stdout = "Recognised text\n"
        stderr = ""

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return Result()

    monkeypatch.setattr("digitization.ocr.subprocess.run", fake_run)

    ocr = TesseractOCR(
        executable="tesseract-test",
        config=OCRConfig(language="eng", psm=6, extra_args=("--dpi", "300")),
    )

    assert ocr.ocr_image(image) == "Recognised text\n"
    assert calls[0][0] == [
        "tesseract-test",
        str(image),
        "stdout",
        "-l",
        "eng",
        "--psm",
        "6",
        "--dpi",
        "300",
    ]
    assert calls[0][1]["check"] is True
    assert calls[0][1]["capture_output"] is True
    assert calls[0][1]["text"] is True
