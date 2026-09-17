from pathlib import Path

from PIL import Image, ImageDraw

from digitization.pipeline import DigitizationPipeline, MarkdownAssembler
from digitization.structure import PageStructure


class ImageRenderer:
    def render(self, pdf: str | Path, output_dir: str | Path) -> list[Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        page = output / "page-1.png"
        image = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(image)
        for x in (100, 250, 400):
            draw.line((x, 80, x, 320), fill="black", width=3)
        for y in (80, 160, 240, 320):
            draw.line((100, y, 400, y), fill="black", width=3)
        image.save(page)
        return [page]


class OCR:
    def ocr_image(self, image: str | Path) -> str:
        return "A table follows."


def test_pipeline_extracts_reviewable_visual_assets(tmp_path: Path) -> None:
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    result = DigitizationPipeline(ImageRenderer(), OCR()).run(pdf, tmp_path / "work")
    page = result.pages[0]

    assert page.structure is PageStructure.PROSE
    assert page.visual_analysis is not None
    assert page.visual_analysis.table_likely
    assert page.visual_assets
    assert all(asset.startswith("visuals/source/page-001/") for asset in page.visual_assets)
    assert all((tmp_path / "work" / asset).is_file() for asset in page.visual_assets)
    assert "table-visual-verification" in page.review_markers


def test_markdown_references_visual_assets_as_review_candidates(tmp_path: Path) -> None:
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pdf")

    result = DigitizationPipeline(ImageRenderer(), OCR()).run(pdf, tmp_path / "work")
    page = result.pages[0]
    # Simulate the CLI's final asset relocation: assets are manuscript-relative.
    relocated = tuple(asset.replace("visuals/source/", "visuals/01-source/") for asset in page.visual_assets)
    page = page.__class__(**{**page.__dict__, "visual_assets": relocated})

    markdown = MarkdownAssembler().assemble(result.__class__(source_pdf=pdf, pages=(page,)))

    assert "<!-- visual-candidate: assets/visuals/01-source/page-001/" in markdown
    assert "![Visual candidate](assets/visuals/01-source/page-001/" in markdown
    assert "review: required -->" in markdown
