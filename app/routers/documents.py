from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import logging

from app.dependencies import get_db
from app.schemas import DocumentRead, DocumentUpdate
from app.models import Document
from app.routers.auth import require_admin

log = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/{doc_id}", response_model=DocumentRead, summary="Get document metadata")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{doc_id}/file", summary="Stream original document file")
def get_document_file(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    stored = Path(doc.stored_path)
    if not stored.exists() or not stored.is_file():
        raise HTTPException(status_code=404, detail="File not found on server")

    # Try to get original filename from metadata if available
    filename = stored.name
    try:
        meta_path = Path(doc.metadata_path)
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            # Prefer original uploaded filename
            filename = meta.get("source_filename") or meta.get("file_original") or filename
    except Exception:
        pass

    def _stream():
        with stored.open("rb") as f:
            for chunk in iter(lambda: f.read(64 * 1024), b""):
                yield chunk

    return StreamingResponse(_stream(), media_type=doc.mime_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


class DocumentUpdate(BaseModel):
    perihal: Optional[str] = None
    nomor_surat: Optional[str] = None
    tahun: Optional[int] = None
    jenis: Optional[str] = None

@router.delete("/{doc_id}", summary="Delete document", status_code=204)
def delete_document(
    doc_id: int, 
    db: Session = Depends(get_db),
    admin: bool = Depends(require_admin)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Safe Delete: Only delete file if no other documents reference the same path
    # (Handling duplicate uploads that share the same physical file)
    try:
        if doc.stored_path:
            p = Path(doc.stored_path)
            # Check for other references
            other_refs = db.query(Document).filter(
                Document.stored_path == doc.stored_path,
                Document.id != doc.id
            ).count()
            
            if other_refs == 0:
                if p.exists():
                    p.unlink()
                # Also delete metadata file if exists
                if doc.metadata_path:
                    m = Path(doc.metadata_path)
                    if m.exists():
                        m.unlink()
            else:
                log.info(f"Skipping file deletion for doc {doc_id}: {other_refs} other documents reference {doc.stored_path}")

    except Exception as e:
        log.warning(f"Failed to delete files for doc {doc_id}: {e}")

    db.delete(doc)
    db.commit()
    return None

@router.patch("/{doc_id}", response_model=DocumentRead, summary="Update document metadata (OCR corrections)")
def update_document(
    doc_id: int, 
    update_data: DocumentUpdate, 
    db: Session = Depends(get_db),
    admin: bool = Depends(require_admin)
):
    from app.schemas import DocumentUpdate  # Import here to avoid circular import
    
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check for sensitive field changes
    sensitive_changed = False
    if getattr(update_data, 'tanggal_surat', None) is not None and getattr(update_data, 'tanggal_surat', None) != doc.tanggal_surat:
        sensitive_changed = True
    if getattr(update_data, 'jenis', None) is not None and getattr(update_data, 'jenis', None) != doc.jenis:
        sensitive_changed = True

    if sensitive_changed and not getattr(update_data, 'confirm_sensitive', False):
        raise HTTPException(
            status_code=400, 
            detail="Mengubah tanggal atau jenis surat memerlukan konfirmasi. Set confirm_sensitive=true"
        )

    # Update fields
    if getattr(update_data, 'nomor_surat', None) is not None:
        doc.nomor_surat = update_data.nomor_surat
    if getattr(update_data, 'perihal', None) is not None:
        doc.perihal = update_data.perihal
    if getattr(update_data, 'tanggal_surat', None) is not None:
        doc.tanggal_surat = update_data.tanggal_surat
        # Update bulan if tanggal changed
        from app.services.metadata import extract_bulan
        doc.bulan = extract_bulan(update_data.tanggal_surat)
    if getattr(update_data, 'jenis', None) is not None:
        doc.jenis = update_data.jenis
    if getattr(update_data, 'pengirim', None) is not None:
        doc.pengirim = update_data.pengirim
    if getattr(update_data, 'penerima', None) is not None:
        doc.penerima = update_data.penerima

    # Update metadata.json file
    try:
        meta_path = Path(doc.metadata_path)
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta.update({
                "nomor": doc.nomor_surat,
                "perihal": doc.perihal,
                "tanggal_surat": doc.tanggal_surat,
                "jenis": doc.jenis,
                "pengirim": doc.pengirim,
                "penerima": doc.penerima,
                "updated_at": str(doc.uploaded_at),  # Could add a separate updated_at field
            })
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning(f"Failed to update metadata.json for doc {doc_id}: {e}")

    db.commit()
    db.refresh(doc)
    log.info(f"Document {doc_id} metadata updated")
    return doc

@router.get("/{doc_id}/text", summary="Get extracted OCR/text content as plain text")
def get_document_text(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Attempt to read metadata.json and find text_path
    try:
        meta_path = Path(doc.metadata_path)
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            text_path = meta.get("text_path")
            if text_path:
                tp = Path(text_path)
                if tp.exists():
                    return PlainTextResponse(tp.read_text(encoding="utf-8"))
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Extracted text not available for this document")
