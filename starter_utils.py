"""Shared small helpers for non-destructive output paths."""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import count
from pathlib import Path


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def candidate_path(path: Path) -> Path:
    """Return path if unused, otherwise a timestamped sibling without overwriting."""
    path = Path(path)
    if not path.exists() and not path.is_symlink():
        return path

    stamp = utc_stamp()

    for index in count():
        serial = f".{index}" if index else ""
        candidate = path.with_name(
            f"{path.stem}.{stamp}{serial}.candidate{path.suffix}"
        )
        if not candidate.exists() and not candidate.is_symlink():
            return candidate


def ensure_parent(path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
