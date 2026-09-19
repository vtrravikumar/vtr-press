from pathlib import Path

from model import Metadata
from renderer.document_epub import _DocumentRenderer


def test_technical_epub_uses_declared_publisher_logo(tmp_path, monkeypatch):
    publisher_dir = tmp_path / "assets" / "publisher"
    publisher_dir.mkdir(parents=True)
    logo = publisher_dir / "college-logo.png"
    logo.write_bytes(b"fake-png")

    import renderer.document_epub as document_epub

    monkeypatch.setattr(document_epub, "ROOT", tmp_path)

    metadata = Metadata(
        title="College Project",
        author=["KUMARESAN U", "RAGUPATHI KUMAR D.", "RAVI KUMAR V.T.R."],
        type="technical-document",
        publisher_logo="college-logo.png",
    )

    renderer = _DocumentRenderer()
    resolved = renderer._resolve_publisher_logo(metadata)

    assert resolved == logo

    renderer.logo_path = resolved
    renderer._render_title_page(metadata)

    assert 'src="images/publisher-logo.png"' in renderer.documents[0].body


def test_technical_epub_explicit_empty_publisher_logo_disables_logo():
    metadata = Metadata(
        title="College Project",
        type="technical-document",
        publisher_logo="",
    )

    renderer = _DocumentRenderer()

    assert renderer._resolve_publisher_logo(metadata) is None
