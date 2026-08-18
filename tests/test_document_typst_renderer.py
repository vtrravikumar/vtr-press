"""Tests for native Typst rendering of the generic Document Model."""

from interpretation import (
    InterpretedDocument,
    InterpretedNode,
    NodeKind,
)
from model import (
    Bold,
    Document,
    Heading,
    Image,
    ListBlock,
    ListItem,
    Metadata,
    Paragraph,
    Text,
)
from renderer.document_assets import DocumentAssets
from renderer.document_typst import render_document


def _technical_document() -> InterpretedDocument:
    metadata = Metadata(
        title="Solution Architecture",
        subtitle="Ride Together",
        author="VTR Ravi Kumar",
        type="technical-document",
        copyright_year="2026",
    )
    document = Document(
        metadata=metadata,
        blocks=[
            Heading(level=1, title="Solution Architecture"),
            Heading(level=2, title="Introduction"),
            Paragraph(children=[Text("This is the introduction.")]),
            Heading(level=3, title="Purpose"),
            Paragraph(children=[Text("This is the purpose.")]),
            Heading(level=2, title="Architecture"),
            Paragraph(children=[Text("Architecture details.")]),
        ],
    )

    return InterpretedDocument(
        metadata=metadata,
        nodes=[
            InterpretedNode(
                block=document.blocks[0],
                kind=NodeKind.OTHER,
                outlined=False,
            ),
            InterpretedNode(
                block=document.blocks[1],
                kind=NodeKind.SECTION,
                outlined=True,
            ),
            InterpretedNode(block=document.blocks[2]),
            InterpretedNode(
                block=document.blocks[3],
                kind=NodeKind.SUBSECTION,
                outlined=True,
            ),
            InterpretedNode(block=document.blocks[4]),
            InterpretedNode(
                block=document.blocks[5],
                kind=NodeKind.SECTION,
                outlined=True,
            ),
            InterpretedNode(block=document.blocks[6]),
        ],
    )


def test_native_renderer_renders_unordered_list():
    document = _technical_document()
    list_block = ListBlock(
        ordered=False,
        items=[
            ListItem(children=[Text("First")]),
            ListItem(children=[Text("Second")]),
        ],
    )

    document.nodes.append(InterpretedNode(block=list_block))

    output = render_document(document)

    assert "- First" in output
    assert "- Second" in output


def test_native_renderer_renders_ordered_list():
    document = _technical_document()
    list_block = ListBlock(
        ordered=True,
        items=[
            ListItem(children=[Text("First")]),
            ListItem(children=[Text("Second")]),
        ],
    )

    document.nodes.append(InterpretedNode(block=list_block))

    output = render_document(document)

    assert "+ First" in output
    assert "+ Second" in output


def test_native_renderer_preserves_inline_formatting_in_list_item():
    document = _technical_document()
    list_block = ListBlock(
        items=[
            ListItem(
                children=[Bold(children=[Text("Important")])],
            ),
        ],
    )

    document.nodes.append(InterpretedNode(block=list_block))

    output = render_document(document)

    assert "- *Important*" in output


def test_native_renderer_uses_technical_theme_and_no_cover():
    output = render_document(_technical_document())

    assert '#import "../themes/technical/theme.typ": *' in output
    assert "#render-title-page(" in output
    assert "show-publisher-logo: true," in output
    assert "#render-cover(" not in output


def test_native_renderer_uses_interpreted_heading_semantics():
    output = render_document(_technical_document())

    # The Markdown level-1 title is represented in the model but is not
    # duplicated after the metadata-driven title page.
    assert output.count("Solution Architecture") == 2

    assert "== Introduction" in output
    assert "=== Purpose" in output
    assert "== Architecture" in output
    assert '#running-section-page("Introduction")["' not in output
    assert '#running-section-page("Introduction")[\n' in output
    assert '#running-section-page("Architecture")[\n' in output


def test_native_renderer_wraps_main_matter_and_contents():
    output = render_document(_technical_document())

    assert "#render-contents()" in output
    assert "#main-matter[" in output
    assert output.count("#running-section-page(") == 2
    assert output.find("#render-contents()") < output.find("#main-matter[")


def test_native_renderer_renders_image_with_asset_resolver(tmp_path):
    document = _technical_document()

    manuscript = tmp_path / "docs" / "EngineeringDesign.md"
    manuscript.parent.mkdir(parents=True)

    asset = tmp_path / "assets" / "architecture.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"PNG DATA")

    with DocumentAssets(manuscript) as assets:
        image = Image(
            alt_text="Architecture diagram",
            source="../assets/architecture.png",
        )

        document.nodes.append(InterpretedNode(block=image))

        output = render_document(
            document,
            assets=assets,
        )

        resolved = assets.resolved[0]

        assert resolved.source == "../assets/architecture.png"
        assert resolved.staged_path.exists()
        assert f'#image("{resolved.staged_path}")' in output
