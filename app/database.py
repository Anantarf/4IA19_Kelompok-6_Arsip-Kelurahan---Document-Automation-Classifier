
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from app.config import settings, DB_FILE, ensure_dirs

ensure_dirs()


def get_database_url():
    # Use MySQL if env MYSQL_USE=1, else fallback to SQLite
    import os
    if os.getenv("MYSQL_USE", "0") == "1":
        return settings.MYSQL_URL
    else:
        return f"sqlite:///{DB_FILE.as_posix()}"

SQLALCHEMY_DATABASE_URL = get_database_url()

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # LAZY IMPORT -> hindari circular import
    from app.models import Base
    Base.metadata.create_all(bind=engine)
