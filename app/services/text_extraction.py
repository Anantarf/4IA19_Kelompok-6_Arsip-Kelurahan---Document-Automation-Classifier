
# app/services/text_extraction.py
"""
Bridge untuk ekstraksi teks yang memanfaatkan parser buatan kamu:
- DOCX: app.services.parser_docx.extract_text_from_docx(path)
- PDF:  app.services.parser_pdf.extract_text_from_pdf(path) -> (text, is_scanned)
- OCR (opsional) untuk PDF scan menggunakan PyMuPDF + pytesseract (via app.services.ocr)

Perubahan: disederhanakan dengan menghapus ketergantungan pada pdf2image/Poppler.
OCR fallback sekarang hanya menggunakan app.services.ocr.ocr_pdf_to_text.
"""

from pathlib import Path
from typing import Optional, Tuple, Callable

from app.config import settings
from app.constants import TMP_UPLOAD_NAME

# Import parser buatan kamu
from app.services.parser_docx import extract_text_from_docx
from app.services.parser_pdf import extract_text_from_pdf


class TextExtractor:
    """Service class that encapsulates text extraction strategy for DOCX/PDF and OCR.

    Simplified version that only uses PyMuPDF + pytesseract for OCR fallback.
    """

    def __init__(
        self,
        ocr_pdf_fn: Callable | None = None,
    ) -> None:
        self.external_ocr_pdf = ocr_pdf_fn  # function(path) -> text (string)

    @staticmethod
    def _write_text(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")

    def extract_text_and_save(
        self,
        content: bytes,
        mime_type: str,
        base_dir: Path,
        temp_file_name: Optional[str] = None,
    ) -> Tuple[Optional[Path], str, bool, Optional[dict]]:
        """Main entry: save temporary upload, parse, try OCR fallback and write text.txt.

        Returns: (text_path, text_content, ocr_used, ocr_stats)
        """
        text_content = ""
        ocr_used = False
        ocr_stats = None

        # Simpan sementara untuk parser kamu (karena butuh path)
        temp_dir: Path = settings.TEMP_UPLOAD_PATH
        temp_dir.mkdir(parents=True, exist_ok=True)
        name = temp_file_name or TMP_UPLOAD_NAME
        # Tentukan ekstensi sederhana dari MIME
        ext = ".pdf" if mime_type == "application/pdf" else ".docx"
        tmp_path = temp_dir / f"{name}{ext}"
        tmp_path.write_bytes(content)

        if mime_type == "application/pdf":
            import logging
            log = logging.getLogger(__name__)
            # Pakai parser_pdf
            log.info(f"📄 Extracting text from PDF: {tmp_path.name}")
            text, is_scanned = extract_text_from_pdf(tmp_path.as_posix())
            text_content = (text or "").strip()
            log.info(f"📄 PDF parser returned {len(text_content)} chars, is_scanned={is_scanned}")
            
            # PERBAIKAN: Tampilkan preview RAW text sebelum cleaning
            if text_content:
                log.info(f"📄 RAW text preview (first 500 chars):\n{text_content[:500]}")
                log.info(f"📄 RAW text preview (last 200 chars):\n...{text_content[-200:]}")
            else:
                log.warning("⚠️  No text extracted from PDF")

            # OCR fallback jika scan dan OCR aktif/tersedia
            # Check word count, not just empty text (some scans have noise/garbage text)
            word_count = len((text_content or "").split())
            needs_ocr = is_scanned and word_count < 50  # Threshold: <50 words likely needs OCR
            
            if needs_ocr:
                import logging
                log = logging.getLogger(__name__)
                log.info(f"PDF is scanned/low-quality (file: {tmp_path.name}, words: {word_count}), attempting OCR...")
                
                ocr_text = ""
                ocr_error = None
                
                # Use external OCR if provided, otherwise use app.services.ocr
                if self.external_ocr_pdf is not None:
                    try:
                        log.debug("Using external OCR function")
                        ocr_text = self.external_ocr_pdf(tmp_path.as_posix())
                        ocr_stats = {"method": "external"}  # External function may not return stats
                    except Exception as e:
                        log.warning(f"External OCR failed: {e}")
                        ocr_error = str(e)
                        ocr_text = ""
                        ocr_stats = {"error": ocr_error}
                else:
                    try:
                        # lazy import to avoid hard dependency
                        from app.services.ocr import ocr_pdf_to_text
                        log.debug("Using PyMuPDF + pytesseract OCR")
                        ocr_text, ocr_stats = ocr_pdf_to_text(tmp_path.as_posix())
                    except ImportError as e:
                        log.error(f"OCR module not available: {e}. Install pytesseract and PyMuPDF.")
                        ocr_error = f"Import error: {e}"
                        ocr_stats = {"error": ocr_error}
                    except Exception as e:
                        log.error(f"OCR processing failed: {e}", exc_info=True)
                        ocr_error = str(e)
                        ocr_text = ""
                        ocr_stats = {"error": ocr_error}

                if ocr_text and len(ocr_text.strip()) > 0:
                    text_content = ocr_text
                    ocr_used = True
                    log.info(f"✅ OCR successful: extracted {len(ocr_text)} characters from {tmp_path.name}")
                    
                    # PERBAIKAN: Log detailed OCR stats
                    if ocr_stats:
                        log.info(f"📊 OCR Stats: {ocr_stats.get('success_pages', 0)}/{ocr_stats.get('total_pages', 0)} pages "
                                f"({ocr_stats.get('success_rate', 0)}% success), "
                                f"Failed: {ocr_stats.get('failed_pages', 0)}, "
                                f"DPI: {ocr_stats.get('dpi', 'N/A')}, "
                                f"Lang: {ocr_stats.get('language', 'N/A')}")
                    
                    # Preview OCR result
                    log.info(f"📄 OCR text preview (first 500 chars):\n{ocr_text[:500]}")
                else:
                    log.warning(
                        f"⚠️  OCR returned no text for {tmp_path.name}. "
                        f"Error: {ocr_error or 'Unknown'}. "
                        "Ensure pytesseract and Tesseract are properly installed."
                    )
                    # Log OCR stats even if failed
                    if ocr_stats:
                        log.warning(f"📊 OCR Stats (failed): {ocr_stats}")

        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            import logging
            log = logging.getLogger(__name__)
            # Pakai parser_docx
            log.debug(f"Extracting text from DOCX: {tmp_path.name}")
            try:
                text_content = (extract_text_from_docx(tmp_path.as_posix()) or "").strip()
                log.debug(f"DOCX parser returned {len(text_content)} chars")
            except Exception as e:
                log.error(f"DOCX extraction failed for {tmp_path.name}: {e}", exc_info=True)
                text_content = ""

        # Tulis text.txt jika ada
        text_path = None
        if text_content:
            from app.constants import TEXT_FILENAME
            text_path = base_dir / TEXT_FILENAME
            self._write_text(text_path, text_content)

        # Bersihkan file temp (best-effort)
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

        return text_path, text_content, ocr_used, ocr_stats


# Backwards-compatible convenience function
_default_extractor = TextExtractor()


def extract_text_and_save(
    content: bytes,
    mime_type: str,
    base_dir: Path,
    temp_file_name: Optional[str] = None,
) -> Tuple[Optional[Path], str, bool, Optional[dict]]:
    return _default_extractor.extract_text_and_save(content=content, mime_type=mime_type, base_dir=base_dir, temp_file_name=temp_file_name)

