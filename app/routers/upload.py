
# app/routers/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
import hashlib
import json
import logging
import re

from app.dependencies import get_db
from app.config import settings
from app.models import Document
from app.services.text_extraction import extract_text_and_save
from app.services.metadata import parse_metadata
from app.utils.slugs import slugify_nomor
from app.constants import METADATA_FILENAME, TEXT_FILENAME, ALLOWED_MIME

router = APIRouter()
log = logging.getLogger(__name__)


class PredictRequest(BaseModel):
    text: str
    jenis_hint: str | None = None

# Use `slugify_nomor` from `app.utils.slugs` for nomor normalization
# Helper function to extract month name from tanggal_surat
def extract_bulan(tanggal_surat: str | None) -> str | None:
    """Extract Indonesian month name from tanggal_surat string."""
    if not tanggal_surat:
        return None
    
    MONTHS = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    MONTHS_EN = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    tanggal_lower = tanggal_surat.lower()
    
    # Check Indonesian months
    for month in MONTHS:
        if month.lower() in tanggal_lower:
            return month
    
    # Check English months and convert to Indonesian
    for i, month_en in enumerate(MONTHS_EN):
        if month_en.lower() in tanggal_lower:
            return MONTHS[i]
    
    return None

@router.post("/upload/", summary="Unggah DOCX/PDF (auto kategori tahun & jenis)", tags=["Upload"])
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # --- Validasi MIME ---
        ext = ALLOWED_MIME.get(file.content_type)
        if not ext:
            raise HTTPException(status_code=415, detail="Only DOCX/PDF allowed")

        # --- Baca file & hash ---
        content = await file.read()
        size_bytes = len(content)
        
        # --- Validasi ukuran file ---
        from app.constants import MAX_UPLOAD_SIZE
        if size_bytes > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail=f"File terlalu besar (max {MAX_UPLOAD_SIZE / (1024*1024):.0f} MB)")
        
        sha256 = hashlib.sha256(content).hexdigest()
        log.info(f"📤 Processing upload: {file.filename} ({size_bytes} bytes, hash: {sha256[:8]}...)")

        # --- Cek duplikasi by hash ---
        existing = db.query(Document).filter(Document.file_hash == sha256).first()
        duplicate_of = None
        duplicate_count = 1
        if existing:
            duplicate_of = existing.id
            # Hitung sudah ada berapa file dengan hash ini (termasuk yang lama)
            duplicate_count = db.query(Document).filter(Document.file_hash == sha256).count() + 1
            log.info(f"⚠️ Duplicate upload: {file.filename} matches doc #{existing.id}, this is duplicate #{duplicate_count}")

        now_utc = datetime.utcnow()

        # --- Ekstrak teks di folder temp ---
        temp_dir: Path = settings.TEMP_UPLOAD_PATH
        temp_dir.mkdir(parents=True, exist_ok=True)
        text_path, text_content, ocr_used, ocr_stats = extract_text_and_save(
            content=content,
            mime_type=file.content_type,
            base_dir=temp_dir,
        )

        # --- Parse metadata dari teks + nama file ---
        parsed = parse_metadata(text_content or "", file.filename, uploaded_at=now_utc)

        # Metadata quality assessment (enhanced with text quality)
        metadata_quality = {"score": 0, "warnings": [], "ocr_used": ocr_used}
        
        # Get jenis early for conditional quality checks
        jenis_parsed = parsed.get("jenis")
        
        # Quality scoring (field: weight, default_value)
        # NOTE: Perihal is OPTIONAL for surat masuk (variatif), REQUIRED for surat keluar
        quality_checks = [
            ("nomor", 30, "TANPA-NOMOR", "Nomor surat tidak terdeteksi"),
            ("tanggal_surat", 20, None, "Tanggal surat tidak terdeteksi"),
            ("tahun", 10, None, "Tahun tidak terdeteksi"),
            ("jenis", 10, None, "Jenis surat tidak terdeteksi"),
        ]
        
        for field, weight, default, warning in quality_checks:
            value = parsed.get(field)
            if value and value != default:
                metadata_quality["score"] += weight
            else:
                metadata_quality["warnings"].append(warning)
        
        # Perihal check: ONLY required for surat keluar
        perihal_value = parsed.get("perihal")
        if jenis_parsed == "keluar":
            # Surat keluar WAJIB ada perihal (weight: 25)
            if perihal_value and perihal_value != "Tidak ada perihal":
                metadata_quality["score"] += 25
            else:
                metadata_quality["warnings"].append("Perihal tidak terdeteksi (wajib untuk surat keluar)")
        else:
            # Surat masuk: perihal OPSIONAL, tidak ada penalty jika kosong
            # Tambah bonus score jika ada (weight: 15, lebih rendah dari keluar)
            if perihal_value and perihal_value != "Tidak ada perihal":
                metadata_quality["score"] += 15
                log.debug(f"Bonus: Perihal terdeteksi di surat masuk (+15 points)")
            # No warning if empty for masuk
        
        # Text extraction quality checks
        text_length = len(text_content or "")
        if text_length < 100:
            metadata_quality["warnings"].append("Teks terekstrak sangat pendek (kualitas OCR buruk)")
            metadata_quality["score"] = max(0, metadata_quality["score"] - 15)  # Penalty
        elif ocr_used and text_length < 300:
            metadata_quality["warnings"].append("Teks hasil OCR kurang lengkap")
            metadata_quality["score"] = max(0, metadata_quality["score"] - 5)  # Small penalty
        
        # OCR stats check
        if ocr_used and ocr_stats:
            success_rate = ocr_stats.get('success_rate', 0)
            if success_rate < 50:
                metadata_quality["warnings"].append(f"OCR success rate rendah ({success_rate}%)")
                metadata_quality["score"] = max(0, metadata_quality["score"] - 10)
        
        # Log quality assessment
        score = metadata_quality["score"]
        log_msg = f"Metadata quality {score}/100 for {file.filename}"
        if score < 50:
            log.warning(f"⚠️  Low: {log_msg}. Warnings: {metadata_quality['warnings']}")
        elif score < 75:
            log.info(f"⚡ Medium: {log_msg}")
        else:
            log.info(f"✅ Good: {log_msg}")
        
        # Log perihal regulation status
        if jenis_parsed == "keluar":
            log.info(f"📋 Perihal requirement: WAJIB (surat keluar)")
        else:
            log.info(f"📋 Perihal requirement: OPSIONAL (surat masuk/lainnya)")

        # --- Tentukan nilai final (input menang jika diisi) ---
        nomor_final = parsed.get("nomor") or "TANPA-NOMOR"
        
        # Perihal hanya untuk surat masuk/lainnya
        perihal_final = None
        perihal_parsed = parsed.get("perihal")
        jenis_temp = parsed.get("jenis")
        if jenis_temp != "keluar":
            perihal_final = perihal_parsed if perihal_parsed else None
            if perihal_parsed:
                log.info(f"✅ Perihal terdeteksi di surat masuk: {perihal_parsed[:50]}...")
        
        tanggal_final = parsed.get("tanggal_surat")
        
        # Extract bulan (month) from tanggal_surat for categorization
        bulan_final = extract_bulan(tanggal_final)
        
        # Validate month extraction
        if tanggal_final and not bulan_final:
            log.warning(f"⚠️ Month not extracted from date: '{tanggal_final}' for {file.filename}")

        # Tahun: prefer nilai input yang valid (positive int). Jika input kosong/0, fallback ke parsed.
        # Jika tidak terdeteksi, biarkan None untuk disimpan di luar folder tahun.
        tahun_final = parsed.get("tahun")
        try:
            tahun_final = int(tahun_final)
            if tahun_final <= 0:
                tahun_final = None
        except (TypeError, ValueError):
            tahun_final = None

        # Jenis: parsed -> fallback pattern check -> default 'masuk' for formal letters
        jenis_final = parsed.get("jenis")
        jenis_confidence = parsed.get("jenis_confidence", 0.0)
        jenis_method = parsed.get("jenis_method", "unknown")
        
        if jenis_final is None:
            # Fallback: check nomor pattern
            if re.search(r"(?i)(?:^|/|[-_])SM(?:/|[-_]|$)", nomor_final):
                jenis_final = "masuk"
                jenis_confidence = 0.75
                jenis_method = "nomor-pattern"
            elif re.search(r"(?i)(?:^|/|[-_])SK(?:/|[-_]|$)", nomor_final):
                jenis_final = "keluar"
                jenis_confidence = 0.75
                jenis_method = "nomor-pattern"
            else:
                jenis_final = "masuk"  # Default for formal letters with unclear origin
                jenis_confidence = 0.50
                jenis_method = "default-fallback"
            log.info(f"Jenis fallback: {jenis_final} (method: {jenis_method}, confidence: {jenis_confidence:.2f})")
        
        # Validate jenis is one of allowed values
        if jenis_final not in {"masuk", "keluar", "lainnya"}:
            log.warning(f"Invalid jenis '{jenis_final}' detected, defaulting to 'masuk'")
            jenis_final = "masuk"
            jenis_confidence = 0.50
            jenis_method = "invalid-fallback"

        # Foldering: structured by tahun/jenis/slug or just jenis/slug
        slug = slugify_nomor(nomor_final)
        if tahun_final and bulan_final:
            # Valid document with tahun & bulan: store in tahun/jenis/bulan/slug structure
            base_dir: Path = settings.STORAGE_ROOT_DIR / str(tahun_final) / jenis_final / bulan_final / slug
        elif tahun_final:
            # Has tahun but no bulan: store in tahun/jenis/slug
            base_dir: Path = settings.STORAGE_ROOT_DIR / str(tahun_final) / jenis_final / slug
        else:
            # No tahun: store directly in jenis/slug
            base_dir: Path = settings.STORAGE_ROOT_DIR / jenis_final / slug
        base_dir.mkdir(parents=True, exist_ok=True)

        # --- Simpan file asli ---
        original_name = f"original.{ext}"
        original_path = base_dir / original_name
        
        # Collision handling: Prevent overwrite if content is different
        if original_path.exists():
            # Check if existing file is identical
            try:
                existing_bytes = original_path.read_bytes()
                existing_hash = hashlib.sha256(existing_bytes).hexdigest()
                
                if existing_hash != sha256:
                    # Content differs: Collision! Rename new file
                    import time
                    timestamp = int(time.time())
                    original_name = f"original_{timestamp}.{ext}"
                    original_path = base_dir / original_name
                    log.info(f"⚠️ Collision detected: Renaming to {original_name}")
                else:
                    log.info(f"ℹ️ File content identical to existing {original_path.name}, using existing file.")
            except Exception as e:
                log.warning(f"Failed to check existing file {original_path}: {e}, using separate name.")
                import time
                timestamp = int(time.time())
                original_name = f"original_{timestamp}.{ext}"
                original_path = base_dir / original_name

        original_path.write_bytes(content)

        # --- Simpan text.txt (kalau ada) ---
        final_text_path = None
        if text_content:
            final_text_path = base_dir / TEXT_FILENAME
            final_text_path.write_text(text_content, encoding="utf-8")

        # --- Siapkan metadata.json ---
        metadata_path = base_dir / METADATA_FILENAME
        metadata = {
            "uploaded_at": now_utc.isoformat() + "Z",
            "file_original": original_name,
            "mime_type": file.content_type,
            "size_bytes": size_bytes,
            "hash_sha256": sha256,
            "ocr_enabled": bool(settings.TESSERACT_CMD) or ocr_used,
            "ocr_used": ocr_used,
            "ocr_stats": ocr_stats if ocr_stats else None,
            "text_path": final_text_path.as_posix() if final_text_path else None,
            "text_length": len(text_content) if text_content else 0,
            "source_filename": file.filename,
            "duplicate_of": duplicate_of,
            "duplicate_count": duplicate_count if duplicate_of else 1,
        }
        metadata.update({
            "tahun": tahun_final,
            "jenis": jenis_final,
            "nomor": nomor_final,
            "tanggal_surat": tanggal_final,
            "parsed": parsed,
            "metadata_quality": metadata_quality,  # Include quality assessment
        })
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        # --- Simpan ke SQLite ---
        try:
            doc = Document(
                tahun=tahun_final,
                jenis=jenis_final,
                nomor_surat=nomor_final,
                perihal=perihal_final if jenis_final != "keluar" else None,
                tanggal_surat=tanggal_final,
                bulan=bulan_final,
                stored_path=original_path.as_posix(),
                metadata_path=metadata_path.as_posix().replace("\\", "/"),
                uploaded_at=now_utc,
                mime_type=file.content_type,
                file_hash=sha256,
                ocr_enabled=metadata["ocr_enabled"],
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            log.info(f"✅ Document saved to database: ID={doc.id}, nomor={nomor_final}, jenis={jenis_final}")
        except Exception as e:
            db.rollback()
            log.error(f"❌ Database error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Gagal menyimpan ke database: {str(e)}")

        # --- Bersihkan file text temp (best-effort) ---
        try:
            if text_path: text_path.unlink(missing_ok=True)
        except Exception:
            pass

        # --- Respons ---
        log.info(f"✅ Upload complete: {file.filename} → ID={doc.id}")
        response = {
            "id": doc.id,
            "message": "uploaded",
            "tahun": tahun_final,
            "jenis": jenis_final,
            "nomor": nomor_final,               # legacy key (backward compatibility)
            "nomor_surat": nomor_final,        # canonical key
            "stored_path": doc.stored_path,
            "metadata_path": doc.metadata_path,
            "mime_type": file.content_type,
            "size": size_bytes,
            "hash": f"sha256:{sha256}",
            "parsed": parsed,
            "metadata_quality": metadata_quality,
            "ocr_info": {
                "used": ocr_used,
                "stats": ocr_stats,
                "text_length": len(text_content) if text_content else 0,
            } if ocr_used else None,
            "duplicate_of": duplicate_of,
            "duplicate_count": duplicate_count if duplicate_of else 1,
        }
        # Hanya sertakan perihal jika bukan surat keluar
        if jenis_final != "keluar":
            response["perihal"] = perihal_final
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        log.error(f"❌ Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan sistem: {str(e)}")


@router.post("/upload/analyze", summary="Analyze file metadata without saving", tags=["Upload"])
async def analyze_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # --- Validasi MIME ---
    ext = ALLOWED_MIME.get(file.content_type)
    if not ext:
        raise HTTPException(status_code=415, detail="Only DOCX/PDF allowed")

    # --- Baca content ---
    content = await file.read()
    
    # --- Cek duplikasi by hash ---
    sha256 = hashlib.sha256(content).hexdigest()
    existing = db.query(Document).filter(Document.file_hash == sha256).first()
    duplicate_info = None
    if existing:
        duplicate_info = {
            "duplicate_of": existing.id,
            "nomor_surat": existing.nomor_surat,
            "tanggal_surat": existing.tanggal_surat,
            "jenis": existing.jenis,
            "uploaded_at": existing.uploaded_at.isoformat() + "Z" if existing.uploaded_at else None,
        }
        log.info(f"⚠️ Duplicate detected during analysis: {file.filename} matches doc #{existing.id}")
    
    # --- Estrak Teks (Temp) ---
    temp_dir: Path = settings.TEMP_UPLOAD_PATH
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Gunakan extract_text_and_save tapi kita hapus hasilnya nanti
    text_path, text_content, ocr_used, ocr_stats = extract_text_and_save(
        content=content,
        mime_type=file.content_type,
        base_dir=temp_dir,
    )
    
    # --- Parse Metadata ---
    parsed = parse_metadata(text_content or "", file.filename, uploaded_at=datetime.utcnow())
    
    # Clean up temp text file immediately
    try:
        if text_path and text_path.exists():
            text_path.unlink()
    except Exception:
        pass
        
    return {
        "filename": file.filename,
        "parsed": parsed,
        "duplicate": duplicate_info,
        "ocr_info": {
            "used": ocr_used,
            "stats": ocr_stats,
            "text_length": len(text_content) if text_content else 0,
        },
        "preview_supported": True 
    }


@router.post("/predict-jenis")
async def predict_jenis(request: PredictRequest):
    """Predict document type (masuk/keluar) using ML classifier or rules."""
    from app.services.classifier_ml import classify
    
    try:
        jenis, confidence = classify(request.text)
        return {
            "predicted_jenis": jenis,
            "confidence": confidence,
            "method": "ml" if confidence > 0.7 else "rule-based"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")
