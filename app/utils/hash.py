
# app/utils/hash.py
"""
SHA-256 hashing untuk deteksi duplikasi file.
"""
import hashlib
from typing import BinaryIO


def sha256_file(file_obj: BinaryIO, chunk_size: int = 65536) -> str:
    hasher = hashlib.sha256()
    while True:
        data = file_obj.read(chunk_size)
        if not data:
            break
        hasher.update(data)
    return hasher.hexdigest()
