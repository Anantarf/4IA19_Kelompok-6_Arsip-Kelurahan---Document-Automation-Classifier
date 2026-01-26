
# app/models.py
import json
from pathlib import Path

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index

# Definisikan Base DI SINI (jangan impor dari app.database)
Base = declarative_base()

# --- Skema contoh; sesuaikan jika kamu punya field lain ---

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_jenis_tahun_bulan", "jenis", "tahun", "bulan"),
        Index("ix_documents_uploaded_at_id", "uploaded_at", "id"),
        Index("ix_documents_tanggal_surat", "tanggal_surat"),
    )
    id = Column(Integer, primary_key=True, index=True)

    tahun = Column(Integer, index=True, nullable=True)  # Allow NULL for invalid docs
    jenis = Column(String(20), index=True)        # 'masuk' | 'keluar' | 'lainnya'
    # Keep DB column name as 'nomor' but expose it as `nomor_surat` on the model
    nomor_surat = Column("nomor", String(255), index=True)
    perihal = Column(String(255), index=True, nullable=True)  # OPTIONAL for surat masuk

    tanggal_surat = Column(String(20), nullable=True)
    bulan = Column(String(20), nullable=True, index=True)  # Extracted month name for categorization

    # Backwards-compatible attribute accessors for code that still uses `doc.nomor`
    @property
    def nomor(self) -> str | None:
        return self.nomor_surat

    @nomor.setter
    def nomor(self, value: str | None) -> None:
        self.nomor_surat = value
    pengirim = Column(String(255), nullable=True)
    penerima = Column(String(255), nullable=True)

    stored_path = Column(Text, nullable=False)
    metadata_path = Column(Text, nullable=False)

    uploaded_at = Column(DateTime, index=True)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(100), index=True, nullable=True)
    ocr_enabled = Column(Boolean, default=False)

    @property
    def original_filename(self) -> str | None:
        cache_attr = "_original_filename_cache"
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)

        value = None
        try:
            meta_path = Path(self.metadata_path)
            if meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                value = meta.get("source_filename") or meta.get("file_original")
        except Exception:
            value = None

        if not value and self.stored_path:
            value = Path(self.stored_path).name

        setattr(self, cache_attr, value)
        return value


class OCRText(Base):
    __tablename__ = "ocr_texts"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    text_path = Column(Text, nullable=False)
    created_at = Column(DateTime, index=True)



class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)   # 'info' | 'error' dsb.
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, index=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="staf") # admin | staf
