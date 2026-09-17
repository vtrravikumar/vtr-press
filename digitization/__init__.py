"""Source-document digitization utilities for VTR Press."""

from .ocr import OCRConfig, OCR_PROFILES, TesseractOCR, get_ocr_profile

__all__ = ["OCRConfig", "OCR_PROFILES", "TesseractOCR", "get_ocr_profile"]
