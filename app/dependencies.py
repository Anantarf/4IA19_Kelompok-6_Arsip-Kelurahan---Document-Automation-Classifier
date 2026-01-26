
# app/dependencies.py
import logging
from typing import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal

log = logging.getLogger(__name__)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency untuk setiap request: buka sesi, tutup setelah selesai.
    Dipakai di endpoint: db: Session = Depends(get_db)
    
    Improved: log errors dan rollback jika terjadi exception.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        log.error(f"Database error during request: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
