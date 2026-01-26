  #!/usr/bin/env python3
"""
Script untuk menghapus dokumen yang tidak memiliki tahun/bulan yang valid.
Menghapus file dari storage dan record dari database.
"""

import sys
from pathlib import Path
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Document

def main():
    db = SessionLocal()
    try:
        # Query documents with invalid tahun or bulan
        invalid_docs = db.query(Document).filter(
            (Document.bulan.is_(None)) | (Document.tahun <= 0) | (Document.tahun.is_(None))
        ).all()
        
        total = len(invalid_docs)
        
        if total == 0:
            print("✅ Tidak ada dokumen invalid yang perlu dihapus.")
            return
        
        print(f"🔍 Ditemukan {total} dokumen invalid:")
        print()
        
        for doc in invalid_docs:
            print(f"📄 Doc #{doc.id}:")
            print(f"   Nomor: {doc.nomor_surat}")
            print(f"   Perihal: {doc.perihal}")
            print(f"   Tahun: {doc.tahun}")
            print(f"   Bulan: {doc.bulan}")
            print(f"   Tanggal Surat: {doc.tanggal_surat}")
            print(f"   Path: {doc.stored_path}")
            print()
        
        confirm = input(f"❓ Hapus {total} dokumen ini? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Dibatalkan.")
            return
        
        deleted_files = 0
        deleted_db = 0
        
        for doc in invalid_docs:
            try:
                # Get folder path (parent of stored_path)
                stored_path = Path(doc.stored_path)
                folder_path = stored_path.parent
                
                # Delete entire folder
                if folder_path.exists():
                    shutil.rmtree(folder_path)
                    deleted_files += 1
                    print(f"🗑️  Deleted folder: {folder_path}")
                
                # Delete from database
                db.delete(doc)
                deleted_db += 1
                
            except Exception as e:
                print(f"⚠️  Error deleting doc #{doc.id}: {e}")
        
        # Commit database changes
        db.commit()
        
        print()
        print(f"✨ Cleanup selesai!")
        print(f"   Folder dihapus: {deleted_files}")
        print(f"   Record DB dihapus: {deleted_db}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
