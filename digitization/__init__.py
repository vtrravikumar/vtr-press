"""Source-document digitization utilities for VTR Press."""

from .assets import preserve_page_image
from .ocr import OCRConfig, OCR_PROFILES, TesseractOCR, get_ocr_profile
from .preprocess import PassthroughPreprocessor, PillowPreprocessor, PreprocessConfig
from .structure import PageStructure, StructureClassification, classify_structure

__all__ = [
    "OCRConfig",
    "OCR_PROFILES",
    "TesseractOCR",
    "get_ocr_profile",
    "PassthroughPreprocessor",
    "PillowPreprocessor",
    "PreprocessConfig",
    "PageStructure",
    "StructureClassification",
    "classify_structure",
    "preserve_page_image",
]
