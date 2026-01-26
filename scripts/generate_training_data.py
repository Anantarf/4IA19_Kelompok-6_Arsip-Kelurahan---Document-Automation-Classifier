#!/usr/bin/env python3
"""
Generate synthetic training documents untuk ML classifier.
Duplikasi dokumen yang ada dengan variasi text untuk dataset yang lebih besar.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Document
from app.utils.slugs import slugify_nomor
from app.constants import METADATA_FILENAME
from app.services.metadata import parse_metadata
import json
import hashlib

# Template variasi dokumen
MASUK_VARIATIONS = [
    # Undangan
    "Undangan Yth. untuk menghadiri acara sosialisasi program pemerintah",
    "Undangan mengikuti pelatihan keterampilan untuk masyarakat kelurahan",
    "Undangan rapat koordinasi dengan semua RW se-kelurahan",
    "Undangan menghadiri pertemuan rutin bulanan kelurahan",
    "Undangan kegiatan pelatihan pengurus PKK kelurahan",
    "Undangan acara musyawarah masyarakat kelurahan",
    
    # Permohonan
    "Permohonan bantuan sosial untuk keluarga kurang mampu",
    "Permohonan penggunaan balai kelurahan untuk kegiatan masyarakat",
    "Permohonan izin penyelenggaraan acara di kelurahan",
    "Permohonan data kependudukan untuk keperluan verifikasi",
    
    # Laporan
    "Laporan hasil kegiatan kerja bakti pembersihan lingkungan",
    "Laporan pelaksanaan program pemberdayaan masyarakat bulanan",
    "Laporan rapat koordinasi RW mengenai pembangunan desa",
    "Laporan kegiatan posyandu dan pendampingan kesehatan masyarakat",
    
    # Daftar
    "Daftar penerima bantuan langsung tunai dari pemerintah",
    "Daftar calon peserta pelatihan keterampilan kelurahan",
    "Daftar keluarga yang mengikuti program vaksinasi",
    "Daftar peserta kegiatan penguatan kapasitas RT/RW",
]

KELUAR_VARIATIONS = [
    # Surat Keputusan
    "Keputusan Lurah tentang pembentukan tim pelaksana program kesehatan",
    "Keputusan Lurah dalam hal penunjukan kepala dusun baru",
    "Keputusan Lurah tentang penetapan standar pelayanan publik kelurahan",
    "Keputusan tentang pembentukan panitia persiapan acara tahunan",
    
    # Surat Perintah
    "Perintah melaksanakan koordinasi dengan instansi terkait untuk program sosial",
    "Perintah mengadakan sosialisasi peraturan desa kepada masyarakat",
    "Perintah pemeriksaan kesiapan infrastruktur untuk acara kelurahan",
    "Perintah penyusunan laporan perkembangan program pemberdayaan masyarakat",
    
    # Surat Pemberitahuan
    "Pemberitahuan perubahan jam layanan administrasi kelurahan",
    "Pemberitahuan jadwal pelaksanaan vaksinasi dan imunisasi masyarakat",
    "Pemberitahuan tentang pemberian bantuan sosial kepada warga",
    "Pemberitahuan pemberhentian pemberian subsidi bantuan tempat tinggal",
    
    # Surat Resmi Lainnya
    "Surat persetujuan penggunaan tanah kelurahan untuk kegiatan sosial",
    "Surat rekomendasi untuk pengurusan surat keterangan tanah milik",
    "Surat pengantar permohonan bantuan ke level kecamatan",
    "Surat kerjasama dengan kelurahan tetangga untuk program bersama",
]

def generate_nomor_surat(jenis: str, counter: int) -> str:
    """Generate nomor surat dengan format yang realistis."""
    bulan = random.randint(1, 12)
    tahun = 2025
    return f"{counter:03d}/{jenis.upper()}.{bulan:02d}.{tahun % 100:02d}"

def generate_tanggal_surat() -> str:
    """Generate tanggal acak dalam 30 hari terakhir."""
    days_ago = random.randint(1, 30)
    date = datetime.now() - timedelta(days=days_ago)
    MONTHS_ID = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    month_name = MONTHS_ID[date.month - 1]
    return f"{date.day} {month_name} {date.year}"

def create_dummy_document(jenis: str, perihal: str, counter: int, db) -> Document | None:
    """Buat dokumen dummy untuk training."""
    try:
        nomor = generate_nomor_surat(jenis, counter)
        tanggal = generate_tanggal_surat()
        
        # Parse metadata dari perihal
        parsed = parse_metadata(perihal, "dummy.pdf", uploaded_at=datetime.utcnow())
        
        # Extract bulan dari tanggal
        MONTHS_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        bulan = None
        for month in MONTHS_ID:
            if month in tanggal:
                bulan = month
                break
        
        # Buat slug nomor
        nomor_slug = nomor.lower().replace("/", "-").replace(".", "-")
        
        # Path document
        storage_path = Path(__file__).parent.parent / "storage" / "arsip_kelurahan" / str(2025) / jenis / nomor_slug
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Simpan metadata
        metadata = {
            "nomor_surat": nomor,
            "perihal": perihal,
            "tanggal_surat": tanggal,
            "jenis": jenis,
        }
        
        metadata_file = storage_path / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        # Buat dummy file dengan hash
        dummy_content = f"DOKUMEN {jenis.upper()}\nNomor: {nomor}\nTanggal: {tanggal}\nPerihal: {perihal}".encode()
        file_hash = hashlib.sha256(dummy_content).hexdigest()
        
        stored_path = storage_path / "original.pdf"
        stored_path.write_bytes(dummy_content)
        
        # Buat record di database
        doc = Document(
            tahun=2025,
            jenis=jenis,
            nomor_surat=nomor,
            perihal=perihal,
            tanggal_surat=tanggal,
            bulan=bulan,
            stored_path=str(stored_path),
            metadata_path=str(metadata_file),
            mime_type="application/pdf",
            file_hash=file_hash,
            ocr_enabled=False,
        )
        
        db.add(doc)
        db.commit()
        
        return doc
        
    except Exception as e:
        print(f"❌ Error creating document: {e}")
        db.rollback()
        return None

def main():
    """Generate training data."""
    db = SessionLocal()
    
    print("🔄 Generate Synthetic Training Documents")
    print("=" * 60)
    
    # Hitung dokumen yang sudah ada
    existing_masuk = db.query(Document).filter(Document.jenis == "masuk").count()
    existing_keluar = db.query(Document).filter(Document.jenis == "keluar").count()
    
    print(f"\n📊 Dokumen yang ada saat ini:")
    print(f"   Masuk: {existing_masuk}")
    print(f"   Keluar: {existing_keluar}")
    print(f"   Total: {existing_masuk + existing_keluar}\n")
    
    target = 50  # Target dokumen per kategori
    
    # Generate MASUK variations
    masuk_needed = target - existing_masuk
    if masuk_needed > 0:
        print(f"📝 Generating {masuk_needed} MASUK documents...")
        created_masuk = 0
        for i in range(masuk_needed):
            perihal = random.choice(MASUK_VARIATIONS)
            doc = create_dummy_document("masuk", perihal, existing_masuk + i + 1, db)
            if doc:
                created_masuk += 1
                print(f"   ✅ {doc.nomor_surat} - {doc.perihal[:40]}...")
        print(f"✅ Created {created_masuk} MASUK documents\n")
    else:
        print(f"✓ Already have {existing_masuk} MASUK documents (target: {target})\n")
    
    # Generate KELUAR variations
    keluar_needed = target - existing_keluar
    if keluar_needed > 0:
        print(f"📝 Generating {keluar_needed} KELUAR documents...")
        created_keluar = 0
        for i in range(keluar_needed):
            perihal = random.choice(KELUAR_VARIATIONS)
            doc = create_dummy_document("keluar", perihal, existing_keluar + i + 1, db)
            if doc:
                created_keluar += 1
                print(f"   ✅ {doc.nomor_surat} - {doc.perihal[:40]}...")
        print(f"✅ Created {created_keluar} KELUAR documents\n")
    else:
        print(f"✓ Already have {existing_keluar} KELUAR documents (target: {target})\n")
    
    # Summary
    final_masuk = db.query(Document).filter(Document.jenis == "masuk").count()
    final_keluar = db.query(Document).filter(Document.jenis == "keluar").count()
    
    print("=" * 60)
    print(f"📊 Final Status:")
    print(f"   Masuk: {final_masuk}")
    print(f"   Keluar: {final_keluar}")
    print(f"   Total: {final_masuk + final_keluar}")
    print(f"\n✅ Siap untuk training ML model!")
    print(f"   Jalankan: python scripts/train_classifier.py\n")
    
    db.close()

if __name__ == "__main__":
    main()
