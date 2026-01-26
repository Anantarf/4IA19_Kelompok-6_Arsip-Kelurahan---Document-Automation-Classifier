#!/usr/bin/env python3
"""
Data Consistency Monitor
Monitor consistency between storage files and database records.

Usage:
    python scripts/monitor_consistency.py
"""

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_consistency():
    """Check consistency between storage and database"""
    storage_path = Path('storage/arsip_kelurahan')
    metadata_files = list(storage_path.rglob('metadata.json'))

    db = SessionLocal()
    try:
        db_count = db.query(Document).count()

        logger.info(f'Storage files: {len(metadata_files)}')
        logger.info(f'Database records: {db_count}')

        if len(metadata_files) != db_count:
            logger.warning('⚠️  DATA INCONSISTENCY DETECTED!')
            logger.warning(f'Expected: {len(metadata_files)} records, Found: {db_count} records')

            # Find missing records
            db_metadata_paths = set()
            for doc in db.query(Document.metadata_path).all():
                if doc.metadata_path:
                    db_metadata_paths.add(doc.metadata_path)

            storage_metadata_paths = set(str(f) for f in metadata_files)

            missing_in_db = storage_metadata_paths - db_metadata_paths
            extra_in_db = db_metadata_paths - storage_metadata_paths

            if missing_in_db:
                logger.warning(f'📁 Missing in database ({len(missing_in_db)} files):')
                for path in sorted(list(missing_in_db)[:5]):  # Show first 5
                    logger.warning(f'  - {path}')
                if len(missing_in_db) > 5:
                    logger.warning(f'  ... and {len(missing_in_db) - 5} more')

            if extra_in_db:
                logger.warning(f'🗃️  Extra in database ({len(extra_in_db)} records):')
                for path in sorted(list(extra_in_db)[:5]):  # Show first 5
                    logger.warning(f'  - {path}')
                if len(extra_in_db) > 5:
                    logger.warning(f'  ... and {len(extra_in_db) - 5} more')

            logger.info('💡 Run: python scripts/recover_documents.py')
            return False
        else:
            logger.info('✅ Data consistency OK')
            return True

    except Exception as e:
        logger.error(f'Consistency check failed: {e}')
        return False
    finally:
        db.close()


def main():
    """Main monitoring function"""
    logger.info('Starting data consistency check...')

    if check_consistency():
        logger.info('Consistency check completed successfully')
        return 0
    else:
        logger.error('Consistency issues found')
        return 1


if __name__ == '__main__':
    sys.exit(main())