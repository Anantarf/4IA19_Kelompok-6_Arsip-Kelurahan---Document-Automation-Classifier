
# app/config.py
import os
from pathlib import Path
from typing import Optional

# Base project dir = .../BISMILAH P3L BERES
BASE_DIR = Path(__file__).resolve().parent.parent

def _env(key: str, default: Optional[str] = None) -> str:
    val = os.getenv(key)
    return val if val is not None else (default or "")

def as_abs_path(path_like: str) -> Path:
    """
    Konversi path env menjadi absolute Path yang aman di Windows/Linux.
    - Jika env berisi absolute Windows (C:\...), tetap dipakai.
    - Jika relatif (data/app.db), gabungkan ke BASE_DIR.
    """
    p = Path(path_like)
    if not p.is_absolute():
        p = (BASE_DIR / path_like)
    return p.resolve()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings via `pydantic-settings` for env validation and loading.

    Keeps backward-compatible attributes and convenience properties used across the
    codebase (e.g., `DB_FILE`, `STORAGE_ROOT_DIR`, snake_case aliases).
    """

    SQLITE_DB_PATH: str = "data/app.db"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "docdb"
    STORAGE_ROOT: str = "storage/arsip_kelurahan"
    TEMP_UPLOAD_DIR: str = "storage/uploads"
    TESSERACT_CMD: str = ""
    POPPLER_PATH: str = ""
    SECRET_KEY: str = ""  # For JWT authentication - REQUIRED in production

    # Tell pydantic-settings to read .env automatically
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Derived path helpers
    @property
    def DB_FILE(self):
        return as_abs_path(self.SQLITE_DB_PATH)

    @property
    def MYSQL_URL(self):
        # Example: mysql+pymysql://user:pass@host:port/dbname
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    @property
    def STORAGE_ROOT_DIR(self):
        return as_abs_path(self.STORAGE_ROOT)

    @property
    def TEMP_UPLOAD_PATH(self):
        return as_abs_path(self.TEMP_UPLOAD_DIR)

    def ensure_dirs(self) -> None:
        """Create important folders if missing."""
        self.DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.STORAGE_ROOT_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_UPLOAD_PATH.mkdir(parents=True, exist_ok=True)

    # Compatibility aliases for older code that used snake_case names
    @property
    def tesseract_cmd(self) -> str:
        return self.TESSERACT_CMD

    @property
    def sqlite_db_path(self) -> str:
        # Return string path for scripts expecting path-like string
        return str(self.DB_FILE)

    @property
    def storage_root(self) -> str:
        return str(self.STORAGE_ROOT_DIR)

    @property
    def temp_upload_dir(self) -> str:
        return str(self.TEMP_UPLOAD_PATH)

# Ekspor objek settings untuk kompatibilitas impor lama
settings = Settings()

# Alias untuk kompatibilitas patch lain
DB_FILE = settings.DB_FILE
STORAGE_ROOT_DIR = settings.STORAGE_ROOT_DIR
TEMP_UPLOAD_PATH = settings.TEMP_UPLOAD_PATH

def ensure_dirs():
    settings.ensure_dirs()
