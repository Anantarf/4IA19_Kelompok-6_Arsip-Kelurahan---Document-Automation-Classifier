#!/usr/bin/env python3
"""
Document Recovery Script
Recover document records from metadata.json files when database is corrupted/lost.

Usage:
    python scripts/recover_documents.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def recover_document_from_metadata(metadata_path: Path):
    """Recover document record from metadata.json"""
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        # Extract folder path to get stored_path
        folder_path = metadata_path.parent
        stored_path = str(folder_path / meta['file_original'])

        # Create document record
        doc = Document(
            tahun=meta['tahun'],
            jenis=meta['jenis'],
            nomor_surat=meta.get('nomor'),
            perihal=meta.get('perihal'),
            tanggal_surat=meta.get('tanggal_surat'),
            pengirim=meta.get('pengirim'),
            penerima=meta.get('penerima'),
            stored_path=stored_path,
            metadata_path=str(metadata_path),
            uploaded_at=datetime.fromisoformat(meta['uploaded_at'].replace('Z', '+00:00')),
            mime_type=meta['mime_type'],
            file_hash=meta.get('hash_sha256'),
            ocr_enabled=meta.get('ocr_enabled', False)
        )

        return doc
    except Exception as e:
        logger.error(f'Error recovering {metadata_path}: {e}')
        return None


def main():
    """Main recovery function"""
    storage_path = Path('storage/arsip_kelurahan')
    metadata_files = list(storage_path.rglob('metadata.json'))

    logger.info(f'Found {len(metadata_files)} metadata.json files')

    db = SessionLocal()
    try:
        recovered_count = 0
        skipped_count = 0

        for meta_file in metadata_files:
            # Check if already exists in database
            if db.query(Document).filter(Document.metadata_path == str(meta_file)).first():
                logger.info(f'Skipping {meta_file} - already exists in DB')
                skipped_count += 1
                continue

            doc = recover_document_from_metadata(meta_file)
            if doc:
                db.add(doc)
                recovered_count += 1
                logger.info(f'Recovered: {doc.tahun} {doc.jenis} {doc.nomor_surat}')

        db.commit()
        logger.info(f'Successfully recovered {recovered_count} documents')
        logger.info(f'Skipped {skipped_count} existing documents')

        # Verify
        total_after = db.query(Document).count()
        logger.info(f'Total documents in DB after recovery: {total_after}')

    except Exception as e:
        logger.error(f'Recovery failed: {e}')
        db.rollback()
        return 1
    finally:
        db.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())