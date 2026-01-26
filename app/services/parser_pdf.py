
# app/services/parser_pdf.py
"""
Ekstraksi teks dari PDF. Coba teks native; bila kosong, tandai sebagai scan.
"""

import logging
from typing import Tuple
from pdfminer.high_level import extract_text

log = logging.getLogger(__name__)


def extract_text_from_pdf(path: str) -> Tuple[str, bool]:
    """
    Returns: (text, is_scanned)
    is_scanned True bila text kosong/nyaris kosong -> perlu OCR.
    """
    try:
        text = extract_text(path) or ""
        log.debug(f"Extracted {len(text)} chars from {path}")
    except Exception as e:
        log.error(f"Failed to extract text from {path}: {e}", exc_info=True)
        text = ""
    from app.constants import SCANNED_TEXT_THRESHOLD
    is_scanned = (len(text.strip()) < SCANNED_TEXT_THRESHOLD)  # ambang sederhana
    log.debug(f"PDF {path} is_scanned={is_scanned} (text length: {len(text.strip())})")
    return (text, is_scanned)
