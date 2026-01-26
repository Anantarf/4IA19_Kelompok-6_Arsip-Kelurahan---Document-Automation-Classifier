
# app/utils/audit.py
"""
Audit log util untuk mencatat aktivitas penting:
- upload | upload_duplicate | override | delete | export | error
"""

from sqlalchemy.orm import Session
from datetime import datetime
from app.models import AuditLog


def log(session: Session, actor: str | None, level: str, document_id: int | None, message: str | None = None) -> None:
    """Tambahkan entry audit ke tabel AuditLog.

    Parameter:
    - session: SQLAlchemy Session aktif
    - actor: nama actor/username yang melakukan aksi
    - level: level log (mis. 'info', 'error')
    - document_id: id dokumen terkait (opsional)
    - message: pesan/detail aksi
    """
    entry = AuditLog(
        actor=actor,
        level=level,
        document_id=document_id,
        message=message or "",
        created_at=datetime.utcnow(),
    )
    session.add(entry)
    session.commit()
