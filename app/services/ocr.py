
# app/services/ocr.py
"""
OCR untuk PDF scan menggunakan PyMuPDF (render) + pytesseract.
"""

import logging
import tempfile
from pathlib import Path
from app.config import settings

log = logging.getLogger(__name__)

# Optional OCR deps: import safely so module import won't fail when not installed
try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# Set path tesseract jika disediakan di .env (gunakan nama setting yang benar)
if pytesseract and settings.TESSERACT_CMD:
    try:
        pytesseract.pytesseract.tesseract_cmd = str(settings.TESSERACT_CMD)
    except Exception:
        # ignore assignment errors; function will check pytesseract presence at runtime
        pass


from app.constants import DEFAULT_OCR_DPI, TESSERACT_LANG
from typing import Dict, Tuple

def ocr_pdf_to_text(path: str, dpi: int = DEFAULT_OCR_DPI) -> Tuple[str, Dict]:
    """
    Render setiap halaman PDF ke gambar dan lakukan OCR, gabungkan hasil per halaman.

    Fitur:
    - Multi-language support (Indonesia + fallback ke English)
    - Image preprocessing untuk meningkatkan akurasi OCR
    - Per-page error handling agar satu halaman gagal tidak stop proses
    - Grayscale conversion untuk optimasi
    - Comprehensive logging untuk debugging
    - Return OCR stats untuk tracking kualitas
    
    Returns:
        Tuple[str, Dict]: (extracted_text, ocr_stats)
        ocr_stats contains: total_pages, success_pages, failed_pages, 
                           total_chars, dpi, language
    """
    text_chunks = []
    ocr_stats = {
        "total_pages": 0,
        "success_pages": 0,
        "failed_pages": 0,
        "total_chars": 0,
        "dpi": dpi,
        "language": TESSERACT_LANG,
        "method": "PyMuPDF + Pytesseract",
    }

    if not pytesseract:
        log.warning("⚠️  pytesseract not available, OCR skipped. Install pytesseract to enable OCR.")
        return "", {**ocr_stats, "error": "pytesseract not available"}
    
    if not fitz:
        log.warning("⚠️  PyMuPDF (fitz) not available, OCR skipped. Install PyMuPDF to enable OCR.")
        return "", {**ocr_stats, "error": "PyMuPDF not available"}
    
    if not Image:
        log.warning("⚠️  PIL/Pillow not available, OCR skipped. Install Pillow to enable OCR.")
        return "", {**ocr_stats, "error": "PIL/Pillow not available"}

    try:
        with fitz.open(path) as doc:
            total_pages = doc.page_count
            ocr_stats["total_pages"] = total_pages
            log.info(f"📄 Starting OCR on {Path(path).name}: {total_pages} page(s) at {dpi} DPI")
            
            for page_number, page in enumerate(doc, start=1):
                try:
                    pix = page.get_pixmap(dpi=dpi)
                except Exception as e:
                    log.warning(f"⚠️  Failed to render page {page_number}/{total_pages}: {e}")
                    ocr_stats["failed_pages"] += 1
                    continue

                # Use TemporaryDirectory context manager for automatic cleanup
                try:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_file = Path(tmp_dir) / f"page_{page_number}.png"
                        tmp_file.write_bytes(pix.tobytes("png"))

                        img = Image.open(tmp_file)
                        # Konversi ke grayscale untuk meningkatkan OCR pada gambar dokumen
                        img = img.convert("L")
                        
                        # PERBAIKAN: Aktifkan contrast enhancement untuk akurasi OCR lebih baik
                        try:
                            from PIL import ImageEnhance
                            enhancer = ImageEnhance.Contrast(img)
                            img = enhancer.enhance(1.5)  # Tingkatkan kontras 50%
                            # Optional: sharpen juga untuk teks lebih jelas
                            sharpener = ImageEnhance.Sharpness(img)
                            img = sharpener.enhance(1.3)
                        except Exception as e:
                            log.debug(f"Image enhancement skipped for page {page_number}: {e}")

                        # Coba OCR dengan bahasa Indonesia terlebih dahulu
                        txt = ""
                        page_success = False
                        try:
                            txt = pytesseract.image_to_string(img, lang=TESSERACT_LANG)
                            log.debug(f"✅ Page {page_number}/{total_pages} OCR (lang={TESSERACT_LANG}): {len(txt or '')} chars")
                            page_success = bool(txt and txt.strip())
                        except Exception as e:
                            log.debug(f"⚠️  Page {page_number} OCR with lang={TESSERACT_LANG} failed: {e}")
                            # Fallback tanpa spesifikasi bahasa
                            try:
                                txt = pytesseract.image_to_string(img)
                                log.debug(f"✅ Page {page_number}/{total_pages} OCR (default): {len(txt or '')} chars")
                                page_success = bool(txt and txt.strip())
                            except Exception as e2:
                                log.error(f"❌ Page {page_number} OCR completely failed: {e2}")
                                txt = ""
                                page_success = False

                        if page_success:
                            ocr_stats["success_pages"] += 1
                        else:
                            ocr_stats["failed_pages"] += 1
                        
                        text_chunks.append(txt or "")
                except Exception as e:
                    # Jangan berhenti jika satu halaman gagal
                    log.error(f"❌ Page {page_number} processing failed: {e}", exc_info=True)
                    text_chunks.append("")

            result = "\n".join([t for t in text_chunks if t and t.strip()])
            ocr_stats["total_chars"] = len(result)
            ocr_stats["success_rate"] = round(ocr_stats["success_pages"] / total_pages * 100, 1) if total_pages > 0 else 0
            
            log.info(
                f"✅ OCR completed: {ocr_stats['total_chars']} chars extracted from "
                f"{ocr_stats['success_pages']}/{total_pages} pages ({ocr_stats['success_rate']}% success)"
            )
            return result.strip(), ocr_stats
    except Exception as e:
        log.error(f"❌ OCR failed to open/process PDF {path}: {e}", exc_info=True)
        return "", {**ocr_stats, "error": str(e)}
