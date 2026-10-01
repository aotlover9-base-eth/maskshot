"""MaskShot - Screenshot & Clipboard Secret Sanitizer."""

from .cli import main
from .detector import SecretDetector
from .ocr import OCRProcessor
from .redactor import ImageRedactor

__all__ = ["main", "SecretDetector", "OCRProcessor", "ImageRedactor"]
__version__ = "0.1.0"
