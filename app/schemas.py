# app/schemas.py
"""
Skema Pydantic untuk request/response API.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DocumentCreate(BaseModel):
    jenis: str = Field(example='surat_masuk')
    tahun: int
    nomor_surat: Optional[str] = None
    perihal: Optional[str] = Field(default=None, description="Hanya untuk surat masuk/lainnya. Tidak berlaku untuk surat keluar.")
    uploaded_by: Optional[str] = None

class DocumentRead(BaseModel):
    """Match actual Document model fields"""
    id: int
    tahun: Optional[int] = None  # Allow None for invalid docs
    jenis: str
    nomor_surat: Optional[str] = None
    perihal: Optional[str] = Field(default=None, description="Hanya untuk surat masuk/lainnya. Tidak berlaku untuk surat keluar.")
    tanggal_surat: Optional[str] = None
    bulan: Optional[str] = None
    stored_path: str
    metadata_path: str
    uploaded_at: datetime
    mime_type: str
    file_hash: Optional[str] = None
    ocr_enabled: bool = False
    original_filename: Optional[str] = None

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        # Hapus perihal jika jenis == 'keluar'
        if d.get('jenis') == 'keluar' and 'perihal' in d:
            d.pop('perihal')
        return d

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    """Schema for updating document metadata"""
    nomor_surat: Optional[str] = Field(default=None, description="Nomor surat")
    perihal: Optional[str] = Field(default=None, description="Perihal surat")
    tanggal_surat: Optional[str] = Field(default=None, description="Tanggal surat")
    jenis: Optional[str] = Field(default=None, description="Jenis surat: masuk/keluar/lainnya")
    pengirim: Optional[str] = Field(default=None, description="Pengirim")
    penerima: Optional[str] = Field(default=None, description="Penerima")
    confirm_sensitive: bool = Field(default=False, description="Konfirmasi untuk mengubah tanggal dan jenis surat")

class SearchQuery(BaseModel):
    tahun: Optional[int] = None
    jenis: Optional[str] = None
    nomor_surat: Optional[str] = None
    perihal: Optional[str] = None
