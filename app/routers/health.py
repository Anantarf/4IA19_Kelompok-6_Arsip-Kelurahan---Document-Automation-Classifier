# app/routers/health.py
"""
Health endpoints (OCR health check).

GET /healthz/ocr -> { ocr: bool, details: { pytesseract, pymupdf, tesseract_cmd, tesseract_cmd_exists, tesseract_version }}
"""
from fastapi import APIRouter
import os
from app.config import settings

router = APIRouter()


@router.get("/healthz/ocr", summary="OCR health check", tags=["Root"])
def ocr_health():
    details = {}

    # Modules availability
    try:
        import pytesseract
        details["pytesseract"] = True
    except Exception:
        pytesseract = None
        details["pytesseract"] = False

    try:
        import fitz
        details["pymupdf"] = True
    except Exception:
        fitz = None
        details["pymupdf"] = False

    try:
        from PIL import Image
        details["Pillow"] = True
    except Exception:
        details["Pillow"] = False

    # Config path
    tcmd = settings.TESSERACT_CMD
    details["tesseract_cmd"] = tcmd
    details["tesseract_cmd_exists"] = bool(tcmd and os.path.exists(str(tcmd)))

    # Try to get version if pytesseract available and tesseract present
    tver = None
    if details["pytesseract"]:
        try:
            if tcmd:
                pytesseract.pytesseract.tesseract_cmd = str(tcmd)
            tver = str(pytesseract.get_tesseract_version())
        except Exception as e:
            tver = None
            details["tesseract_error"] = str(e)
    details["tesseract_version"] = tver

    # Determine overall OCR availability
    ocr_ok = details.get("pytesseract") and details.get("pymupdf") and details.get("tesseract_cmd_exists")

    return {"ocr": bool(ocr_ok), "details": details}