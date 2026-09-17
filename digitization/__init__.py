"""Source-document digitization utilities for VTR Press."""

from .ocr import OCRConfig, OCR_PROFILES, TesseractOCR, get_ocr_profile
from .preprocess import PassthroughPreprocessor, PillowPreprocessor, PreprocessConfig

__all__ = [
    "OCRConfig",
    "OCR_PROFILES",
    "TesseractOCR",
    "get_ocr_profile",
    "PassthroughPreprocessor",
    "PillowPreprocessor",
    "PreprocessConfig",
]
