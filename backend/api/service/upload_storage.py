"""Filesystem storage for validated source game files."""

from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4


DEFAULT_UPLOAD_DIR = "/var/lib/ppr-uploads"


def upload_root() -> Path:
    return Path(os.getenv("UPLOAD_DIR", DEFAULT_UPLOAD_DIR)).resolve()


def safe_filename(filename: str) -> str:
    """Return a portable filename without accepting path traversal."""
    basename = Path(filename or "games.csv").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", basename).strip(".-")
    return cleaned or "games.csv"


def store_game_file(
    dataset: tuple[str, str, str],
    filename: str,
    content: bytes,
    upload_id: str | None = None,
) -> tuple[str, str]:
    """Atomically store one validated game file and return ID and relative path."""
    upload_id = upload_id or uuid4().hex
    dataset_dir = upload_root().joinpath(*dataset)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    relative_path = Path(*dataset, f"{upload_id}-{safe_filename(filename)}")
    destination = upload_root() / relative_path
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    temporary.write_bytes(content)
    temporary.replace(destination)
    return upload_id, relative_path.as_posix()


def delete_game_file(storage_path: str) -> bool:
    """Delete a stored upload only when it resolves below the upload root."""
    root = upload_root()
    candidate = (root / storage_path).resolve()
    if root not in candidate.parents:
        raise ValueError("Upload path resolves outside the upload directory")
    try:
        candidate.unlink()
        return True
    except FileNotFoundError:
        return False
