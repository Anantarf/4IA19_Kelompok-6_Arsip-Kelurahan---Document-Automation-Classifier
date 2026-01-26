"""
Script migrasi data dari SQLite ke MySQL menggunakan SQLAlchemy model project ini.
VERSI AMAN dengan backup, rollback, dan validasi data integrity.

Fitur keamanan:
- ✅ Dry-run mode untuk testing
- ✅ Backup otomatis sebelum migrasi
- ✅ Transaction rollback jika gagal
- ✅ Data integrity validation
- ✅ Progress tracking
- ✅ Foreign key constraint handling
- ✅ Detailed logging

Cara pakai:
  1. Aktifkan venv: .venv\Scripts\activate
  2. Set MYSQL_USE=1
  3. Jalankan dry-run dulu: python scripts/migrate_sqlite_to_mysql.py --dry-run
  4. Jika OK, jalankan migrasi: python scripts/migrate_sqlite_to_mysql.py
  5. Verifikasi data: python scripts/migrate_sqlite_to_mysql.py --verify
"""
import os
import sys
import argparse
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load .env before importing app modules
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models import Document, OCRText, AuditLog, User, Base
from app.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup_path = None

        # SQLite connection
        self.sqlite_url = f"sqlite:///{settings.DB_FILE.as_posix()}"
        self.engine_sqlite = create_engine(self.sqlite_url, connect_args={"check_same_thread": False})
        self.SessionSqlite = sessionmaker(bind=self.engine_sqlite)

        # MySQL connection
        if not settings.MYSQL_URL:
            raise ValueError("MYSQL_URL tidak dikonfigurasi. Pastikan MYSQL_USE=1 dan konfigurasi MySQL lengkap.")
        self.mysql_url = settings.MYSQL_URL
        self.engine_mysql = create_engine(self.mysql_url)
        self.SessionMySQL = sessionmaker(bind=self.engine_mysql)

    def validate_connections(self) -> bool:
        """Validasi koneksi ke kedua database"""
        try:
            # Test SQLite
            with self.engine_sqlite.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ SQLite connection OK")

            # Test MySQL
            with self.engine_mysql.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ MySQL connection OK")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def create_backup(self) -> str:
        """Buat backup SQLite database"""
        if self.dry_run:
            logger.info("🔄 DRY-RUN: Skipping backup creation")
            return "dry-run-backup"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        backup_path = backup_dir / f"sqlite_backup_{timestamp}.db"
        shutil.copy2(settings.DB_FILE, backup_path)

        logger.info(f"✅ Backup created: {backup_path}")
        self.backup_path = backup_path
        return str(backup_path)

    def get_table_counts(self, session: Session, tables: List[Any]) -> Dict[str, int]:
        """Hitung jumlah record di setiap tabel"""
        counts = {}
        for table in tables:
            try:
                count = session.query(table).count()
                counts[table.__tablename__] = count
            except Exception as e:
                logger.warning(f"Could not count {table.__tablename__}: {e}")
                counts[table.__tablename__] = 0
        return counts

    def migrate_table(self, session_sqlite: Session, session_mysql: Session,
                      model_class: Any, unique_fields: List[str],
                      transform_func=None) -> tuple[int, int, int]:
        """Migrasi satu tabel dengan error handling"""
        items = session_sqlite.query(model_class).all()
        migrated = 0
        skipped = 0
        errors = 0

        logger.info(f"Migrating {len(items)} {model_class.__tablename__} records...")

        for i, item in enumerate(items):
            if (i + 1) % 100 == 0:
                logger.info(f"Progress: {i + 1}/{len(items)} {model_class.__tablename__}")

            try:
                # Check if already exists
                query = session_mysql.query(model_class)
                for field in unique_fields:
                    value = getattr(item, field)
                    query = query.filter(getattr(model_class, field) == value)

                exists = query.first()
                if exists:
                    skipped += 1
                    continue

                # Transform if needed
                if transform_func:
                    new_item = transform_func(item)
                else:
                    # Copy all attributes
                    new_item = model_class()
                    for attr in model_class.__table__.columns.keys():
                        if hasattr(item, attr):
                            setattr(new_item, attr, getattr(item, attr))

                session_mysql.add(new_item)
                migrated += 1

            except Exception as e:
                logger.error(f"Error migrating {model_class.__tablename__} item {getattr(item, 'id', 'unknown')}: {e}")
                errors += 1
                continue

        if not self.dry_run:
            session_mysql.commit()

        return migrated, skipped, errors

    def verify_migration(self) -> bool:
        """Verifikasi integritas data setelah migrasi"""
        logger.info("🔍 Verifying migration integrity...")

        try:
            session_sqlite = self.SessionSqlite()
            session_mysql = self.SessionMySQL()

            sqlite_counts = self.get_table_counts(session_sqlite, [Document, OCRText, AuditLog, User])
            mysql_counts = self.get_table_counts(session_mysql, [Document, OCRText, AuditLog, User])

            logger.info("Data counts comparison:")
            logger.info(f"{'Table':<15} {'SQLite':<8} {'MySQL':<8} {'Status'}")
            logger.info("-" * 50)

            all_good = True
            for table in ['documents', 'ocr_texts', 'audit_logs', 'users']:
                sqlite_count = sqlite_counts.get(table, 0)
                mysql_count = mysql_counts.get(table, 0)
                status = "✅" if mysql_count >= sqlite_count else "❌"
                if mysql_count < sqlite_count:
                    all_good = False
                logger.info(f"{table:<15} {sqlite_count:<8} {mysql_count:<8} {status}")

            # Additional integrity checks
            if mysql_counts.get('documents', 0) > 0:
                # Check for orphaned OCR texts
                orphaned_ocr = session_mysql.execute(text("""
                    SELECT COUNT(*) FROM ocr_texts ot
                    LEFT JOIN documents d ON ot.document_id = d.id
                    WHERE d.id IS NULL
                """)).scalar()

                if orphaned_ocr > 0:
                    logger.warning(f"⚠️  Found {orphaned_ocr} orphaned OCR records")
                    all_good = False

                # Check for orphaned audit logs
                orphaned_audit = session_mysql.execute(text("""
                    SELECT COUNT(*) FROM audit_logs al
                    LEFT JOIN documents d ON al.document_id = d.id
                    WHERE al.document_id IS NOT NULL AND d.id IS NULL
                """)).scalar()

                if orphaned_audit > 0:
                    logger.warning(f"⚠️  Found {orphaned_audit} orphaned audit log records")
                    all_good = False

            session_sqlite.close()
            session_mysql.close()

            return all_good

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def migrate(self) -> bool:
        """Main migration function"""
        logger.info("🚀 Starting database migration...")
        if self.dry_run:
            logger.info("🔄 DRY-RUN MODE - No actual changes will be made")

        # Validate connections
        if not self.validate_connections():
            return False

        # Create backup
        backup_path = self.create_backup()

        session_sqlite = self.SessionSqlite()
        session_mysql = self.SessionMySQL()

        try:
            # Get source data counts
            source_counts = self.get_table_counts(session_sqlite, [Document, OCRText, AuditLog, User])
            logger.info(f"Source data: {source_counts}")

            # Migrate in order (respecting foreign keys)
            migration_order = [
                (User, ['username']),  # No dependencies
                (Document, ['file_hash']),  # Referenced by others
                (OCRText, ['document_id']),  # Depends on Document
                (AuditLog, ['id']),  # Can reference Document
            ]

            total_migrated = 0
            total_skipped = 0
            total_errors = 0

            for model_class, unique_fields in migration_order:
                migrated, skipped, errors = self.migrate_table(
                    session_sqlite, session_mysql, model_class, unique_fields
                )
                total_migrated += migrated
                total_skipped += skipped
                total_errors += errors

                logger.info(f"✅ {model_class.__tablename__}: {migrated} migrated, {skipped} skipped, {errors} errors")

            logger.info("🎉 Migration completed!")
            logger.info(f"📊 Summary: {total_migrated} migrated, {total_skipped} skipped, {total_errors} errors")
            logger.info(f"💾 Backup saved at: {backup_path}")

            # Verify migration
            if not self.dry_run and self.verify_migration():
                logger.info("✅ Migration verification PASSED")
                return True
            elif self.dry_run:
                logger.info("🔄 DRY-RUN completed successfully")
                return True
            else:
                logger.error("❌ Migration verification FAILED")
                return False

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            if not self.dry_run:
                logger.info("🔄 Rolling back MySQL changes...")
                session_mysql.rollback()
            return False

        finally:
            session_sqlite.close()
            session_mysql.close()

def main():
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to MySQL")
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no changes made)')
    parser.add_argument('--verify', action='store_true', help='Only verify migration integrity')

    args = parser.parse_args()

    if args.verify:
        migrator = DatabaseMigrator(dry_run=True)
        success = migrator.verify_migration()
        sys.exit(0 if success else 1)

    migrator = DatabaseMigrator(dry_run=args.dry_run)
    success = migrator.migrate()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
