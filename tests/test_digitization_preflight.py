from digitization.preflight import check_dependencies, required_packages


def test_required_packages_for_default_configuration():
    assert required_packages(
        pdf_renderer="pdftoppm",
        ocr_engine="tesseract",
        preprocess="conservative",
        combine_sources=False,
    ) == {"PIL": "Pillow"}


def test_required_packages_for_pymupdf_vision_combined():
    assert required_packages(
        pdf_renderer="pymupdf",
        ocr_engine="macos-vision",
        preprocess="none",
        combine_sources=True,
    ) == {
        "pymupdf": "PyMuPDF",
        "ocrmac": "ocrmac",
    }


def test_check_dependencies_reports_missing_import(monkeypatch):
    monkeypatch.setattr(
        "digitization.preflight.importlib.util.find_spec",
        lambda name: None if name == "PIL" else object(),
    )
    errors = check_dependencies(
        pdf_renderer="pdftoppm",
        ocr_engine="tesseract",
        preprocess="conservative",
        combine_sources=False,
    )
    assert len(errors) == 1
    assert "Pillow" in errors[0]
    assert "python -m pip install Pillow" in errors[0]
