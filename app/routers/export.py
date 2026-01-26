
# app/routers/export.py
"""
Ekspor arsip ZIP & CSV metadata dokumen.

- GET /export/zip?tahun=YYYY&jenis=masuk|keluar
  Mengemas seluruh berkas dalam folder: storage/arsip_kelurahan/{tahun}/{jenis}/** ke ZIP.

- GET /export/csv[?tahun=YYYY][&jenis=masuk|keluar][&nomor=...][&perihal=...]
  Mengekspor baris metadata dokumen dari SQLite berdasarkan filter ke CSV.
"""

import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.dependencies import get_db
from app.models import Document

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/zip", summary="Ekspor arsip dokumen menjadi ZIP")
def export_zip(
    tahun: int = Query(..., description="Tahun surat (mis. 2025)"),
    jenis: str = Query(..., description="Jenis surat: 'masuk' atau 'keluar'"),
):
    # Validasi tahun range
    current_year = datetime.utcnow().year
    if tahun < 2020 or tahun > current_year + 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Tahun harus antara 2020-{current_year + 1}")
    
    # Validasi jenis
    if jenis not in {"masuk", "keluar"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="jenis harus 'masuk' atau 'keluar'")

    # Root folder sesuai foldering: storage/arsip_kelurahan/{tahun}/{jenis}
    root: Path = settings.STORAGE_ROOT_DIR / str(tahun) / jenis
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arsip tidak ditemukan")

    # Buat ZIP ke memory buffer
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        # rglob semua file, simpan dengan arcname relative terhadap root
        for p in root.rglob("*"):
            if p.is_file():
                arcname = p.relative_to(root).as_posix()
                z.write(p.as_posix(), arcname)

    buffer.seek(0)
    filename = f"arsip_{tahun}_{jenis}_{datetime.utcnow().strftime('%Y%m%d%H%M')}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/csv", summary="Ekspor metadata dokumen ke CSV")
def export_csv(
    tahun: Optional[int] = Query(None, description="Filter tahun (opsional)"),
    jenis: Optional[str] = Query(None, description="Filter jenis: 'masuk' atau 'keluar' (opsional)"),
    nomor: Optional[str] = Query(None, max_length=100, description="Filter nomor (contains, case-insensitive, max 100 chars)"),
    perihal: Optional[str] = Query(None, max_length=500, description="Filter perihal (contains, case-insensitive, max 500 chars)"),
    limit: int = Query(10000, ge=1, le=100000, description="Batas maksimum baris CSV"),
    db: Session = Depends(get_db),
):
    # Validasi tahun range
    current_year = datetime.utcnow().year
    if tahun is not None and (tahun < 2020 or tahun > current_year + 1):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Tahun harus antara 2020-{current_year + 1}")
    
    # Validasi jenis bila diisi
    if jenis is not None and jenis not in {"masuk", "keluar"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="jenis harus 'masuk' atau 'keluar'")

    q = db.query(Document)

    if tahun is not None:
        q = q.filter(Document.tahun == tahun)
    if jenis:
        q = q.filter(Document.jenis == jenis)

    if nomor:
        term = nomor.strip().lower()
        q = q.filter(func.lower(Document.nomor_surat).like(f"%{term}%"))

    if perihal:
        term = perihal.strip().lower()
        q = q.filter(func.lower(Document.perihal).like(f"%{term}%"))

    rows: List[Document] = (
        q.order_by(Document.uploaded_at.asc(), Document.id.asc())
         .limit(limit)
         .all()
    )

    # Siapkan CSV ke memory
    import csv
    text_buffer = io.StringIO()
    writer = csv.writer(text_buffer)
    # Header sesuai kolom di model kita
    writer.writerow([
        "id", "tahun", "jenis", "nomor_surat", "perihal", "tanggal_surat",
        "stored_path", "metadata_path",
        "uploaded_at", "mime_type", "file_hash", "ocr_enabled",
    ])

    for d in rows:
        writer.writerow([
            d.id,
            d.tahun,
            d.jenis,
            d.nomor_surat or "",
            d.perihal or "",
            d.tanggal_surat or "",
            d.stored_path,
            d.metadata_path,
            d.uploaded_at.isoformat() if d.uploaded_at else "",
            d.mime_type,
            d.file_hash or "",
            "true" if d.ocr_enabled else "false",
        ])

    # StreamingResponse butuh bytes
    text_buffer.seek(0)
    csv_bytes = io.BytesIO(text_buffer.read().encode("utf-8"))
    filename = f"metadata_{tahun or 'all'}_{jenis or 'all'}_{datetime.utcnow().strftime('%Y%m%d%H%M')}.csv"

    return StreamingResponse(
        csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
