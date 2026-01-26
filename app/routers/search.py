
# app/routers/search.py
"""
Endpoint pencarian & filter dokumen berdasarkan metadata:
- tahun
- jenis ('masuk' | 'keluar')
- nomor / nomor_surat (LIKE, case-insensitive)
- perihal (LIKE, case-insensitive)
- limit & offset (opsional)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db
from app.models import Document
from app.schemas import DocumentRead  # pastikan schema ini fields-nya match dengan model


router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/stats", summary="Get dashboard stats")
def get_stats(db: Session = Depends(get_db)):
    total_docs = db.query(Document).count()
    masuk = db.query(Document).filter(Document.jenis == 'masuk').count()
    keluar = db.query(Document).filter(Document.jenis == 'keluar').count()
    lainnya = db.query(Document).filter(Document.jenis == 'lainnya').count()
    return {
        "total_documents": total_docs,
        "surat_masuk": masuk,
        "surat_keluar": keluar,
        "dokumen_lainnya": lainnya
    }



@router.get("/", response_model=List[DocumentRead], summary="Cari dokumen")
def search_documents(
    tahun: Optional[int] = Query(None, description="Tahun surat (mis. 2025)"),
    year: Optional[int] = Query(None, description="Alias untuk tahun (untuk kompatibilitas frontend)"),
    jenis: Optional[str] = Query(None, description="Jenis surat: 'masuk' atau 'keluar'"),
    nomor: Optional[str] = Query(None, max_length=100, description="Nomor surat (partial match, case-insensitive, max 100 chars)"),
    nomor_surat: Optional[str] = Query(None, max_length=100, description="Alias untuk 'nomor' (partial match, max 100 chars)"),
    perihal: Optional[str] = Query(None, max_length=500, description="Perihal (partial match, case-insensitive, max 500 chars)"),
    bulan: Optional[str] = Query(None, description="Bulan (partial match in tanggal_surat, e.g. 'Januari')"),
    q: Optional[str] = Query(None, max_length=500, description="Global search - mencari di nomor_surat, perihal, dan tanggal_surat"),
    limit: int = Query(100, ge=1, le=1000, description="Batas jumlah hasil"),
    offset: int = Query(0, ge=0, description="Offset/paging"),
    sort_by: Optional[str] = Query(None, description="Kolom untuk sorting: 'uploaded_at'|'id'|'tahun'"),
    sort_dir: str = Query('desc', description="Arah sorting: 'asc' atau 'desc'"),
    db: Session = Depends(get_db),
    response: Response = None,
):
    # normalize sort_dir
    sort_dir = (sort_dir or 'desc').lower()
    if sort_dir not in {'asc', 'desc'}:
        sort_dir = 'desc'
    # Validasi jenis
    if jenis is not None and jenis not in {"masuk", "keluar", "lainnya"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="jenis harus 'masuk', 'keluar', atau 'lainnya'"
        )

    query = db.query(Document)
    
    # Support both 'tahun' and 'year' parameters
    tahun_value = tahun or year
    if tahun_value is not None:
        query = query.filter(Document.tahun == tahun_value)

    if jenis:
        query = query.filter(Document.jenis == jenis)

    # Global search with 'q' parameter - searches across multiple fields
    if q:
        search_term = q.strip().lower()
        # Handle NULL values by using coalesce to treat NULL as empty string
        query = query.filter(
            (Document.nomor_surat.isnot(None) & func.lower(Document.nomor_surat).like(f"%{search_term}%")) |
            (Document.perihal.isnot(None) & func.lower(Document.perihal).like(f"%{search_term}%")) |
            (Document.tanggal_surat.isnot(None) & func.lower(Document.tanggal_surat).like(f"%{search_term}%"))
        )
    else:
        # Specific field searches (only if 'q' is not used)
        # Pakai alias: nomor OR nomor_surat
        nomor_term = nomor or nomor_surat
        if nomor_term:
            term = nomor_term.strip().lower()
            query = query.filter(
                Document.nomor_surat.isnot(None) & func.lower(Document.nomor_surat).like(f"%{term}%")
            )

        # Filter Bulan logic - now using dedicated bulan column
        if bulan:
            term = bulan.strip()
            # Direct match on bulan column (case-insensitive)
            query = query.filter(
                Document.bulan.isnot(None) & (func.lower(Document.bulan) == term.lower())
            )

        if perihal:
            term = perihal.strip().lower()
            query = query.filter(
                Document.perihal.isnot(None) & func.lower(Document.perihal).like(f"%{term}%")
            )

    # Sorting
    if sort_by in {'uploaded_at', 'id', 'tahun'}:
        col = getattr(Document, sort_by)
        if sort_dir == 'asc':
            query = query.order_by(col.asc())
        else:
            query = query.order_by(col.desc())
    else:
        # default ordering
        query = query.order_by(Document.uploaded_at.desc(), Document.id.desc())

    # Get total count BEFORE adding limit/offset
    total = query.count()

    rows = (
        query.offset(offset)
         .limit(limit)
         .all()
    )

    # Attach total in header for frontend pagination
    if response is not None:
        try:
            response.headers['X-Total-Count'] = str(total)
        except Exception:
            pass

    return rows


@router.get("/years", summary="Get available years")
def get_years(
    jenis: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(Document.tahun).distinct()
    if jenis:
        q = q.filter(Document.jenis == jenis)
    # Return list of ints, sorted desc
    years = [r[0] for r in q.all() if r[0]]
    return sorted(years, reverse=True)


@router.get("/months", summary="Get available months for year/jenis")
def get_months(
    tahun: int,
    jenis: str,
    db: Session = Depends(get_db)
):
    """
    Returns list of months (names) found in documents for specific year/jenis.
    Now uses dedicated bulan column for accurate categorization.
    """
    # Query distinct bulan values
    months = db.query(Document.bulan).filter(
        Document.tahun == tahun,
        Document.jenis == jenis,
        Document.bulan.isnot(None)
    ).distinct().all()
    
    # Extract month names from query results
    found_months = [m[0] for m in months if m[0]]
    
    # Sort chronologically using Indonesian month order
    MONTHS_ORDER = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    
    sorted_months = sorted(found_months, key=lambda x: MONTHS_ORDER.index(x) if x in MONTHS_ORDER else 999)
    return sorted_months
