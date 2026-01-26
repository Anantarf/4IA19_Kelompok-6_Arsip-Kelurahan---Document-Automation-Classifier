"""Centralized application constants.

Put values here that may be tuned or reused across modules.
"""
from pathlib import Path
from typing import Dict

ALLOWED_MIME: Dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

# OCR / imaging defaults
PDF2IMAGE_DPI = 200
DEFAULT_OCR_DPI = 300
TESSERACT_LANG = "ind"  # default language to try for pytesseract

# PDF parser threshold: below this number of characters, consider PDF as scanned image
SCANNED_TEXT_THRESHOLD = 20

# Filenames & folder names
BACKUP_DIR_NAME = "backup"
METADATA_FILENAME = "metadata.json"
TEXT_FILENAME = "text.txt"
TMP_UPLOAD_NAME = "tmp_upload"
