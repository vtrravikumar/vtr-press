"""Source-document digitization utilities for VTR Press."""

from .assets import preserve_page_image
from .layout import TableGrid, VisualAnalysis, VisualRegion, analyze_page
from .ocr import OCRConfig, OCR_PROFILES, TesseractOCR, get_ocr_profile
from .preprocess import PassthroughPreprocessor, PillowPreprocessor, PreprocessConfig
from .review import build_review_markers
from .structure import PageStructure, StructureClassification, classify_structure
from .table import ExtractedTable, TableCell, extract_table_cells
from .table_markdown import TableMarkdownResult, to_markdown_table

__all__ = [
    "OCRConfig", "OCR_PROFILES", "TesseractOCR", "get_ocr_profile",
    "PassthroughPreprocessor", "PillowPreprocessor", "PreprocessConfig",
    "PageStructure", "StructureClassification", "classify_structure",
    "VisualRegion", "TableGrid", "VisualAnalysis", "analyze_page",
    "TableCell", "ExtractedTable", "extract_table_cells",
    "TableMarkdownResult", "to_markdown_table",
    "preserve_page_image", "build_review_markers",
]
