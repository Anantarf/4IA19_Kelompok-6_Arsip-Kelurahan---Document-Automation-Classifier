from pathlib import Path
import shutil
from datetime import datetime
from typing import Optional

from app.config import settings


def backup_folder(src: Path) -> Optional[Path]:
    """
    Backup a folder by copying it to STORAGE_ROOT_DIR/backup/{src.name}_{timestamp}.

    Returns the destination Path, or None if `src` does not exist.
    """
    if not src.exists():
        return None
    stamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    from app.constants import BACKUP_DIR_NAME
    dst = settings.STORAGE_ROOT_DIR / BACKUP_DIR_NAME / f"{src.name}_{stamp}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    return dst
