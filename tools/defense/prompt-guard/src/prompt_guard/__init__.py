"""Lightweight prompt injection detection."""

from .guard import BaseScanner, BlockReason, PromptGuard, ScanResult

__version__ = "0.1.0"
SCANNER_NAME = "aisecintel-prompt-guard"

__all__ = [
    "SCANNER_NAME",
    "BaseScanner",
    "BlockReason",
    "PromptGuard",
    "ScanResult",
    "__version__",
]
