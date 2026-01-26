
# app/services/foldering.py
"""
Menyimpan dokumen ke struktur folder per tahun/jenis dan menulis metadata.json.
"""
from pathlib import Path
import json
from typing import Dict, Optional, Union
from app.utils.slugs import slugify, slugify_nomor


def target_dir(root: Union[str, Path], tahun: int, jenis: str, nomor_surat: Optional[str], perihal: Optional[str]) -> Path:
    """Return a Path for the target directory.

    `root` may be a string or a Path; the function always returns a Path.
    """
    root_p = Path(root)
    slug = slugify(perihal or "tanpa-perihal")
    nomor = slugify_nomor(nomor_surat)
    return root_p / str(tahun) / jenis / f"{nomor}_{slug}"


def write_metadata(dir_path: Union[str, Path], metadata: Dict) -> Path:
    """Write `metadata` as JSON into `dir_path/metadata.json` and return Path to the file."""
    dir_p = Path(dir_path)
    dir_p.mkdir(parents=True, exist_ok=True)
    from app.constants import METADATA_FILENAME
    meta_path = dir_p / METADATA_FILENAME
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta_path
