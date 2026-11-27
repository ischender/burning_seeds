"""Shared small helpers for non-destructive output paths."""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import count
from pathlib import Path


# Canonical table schemas; every writer and the validator import these.
EVENT_FIELDS = [
    "event_id",
    "name",
    "country",
    "first_year",
    "parent_event_id",
    "official_status",
    "notes",
]

EDITION_FIELDS = [
    "event_id",
    "year",
    "location",
    "lat",
    "lon",
    "population",
    "population_metric",
    "confidence",
    "status",
    "source_url",
    # ISO 8601 dates; YYYY-MM records a month-precision date such as "early October".
    "start_date",
    "end_date",
    # How closely lat/lon in the same row locate the venue; see LOCATION_PRECISIONS.
    "location_precision",
]

OBS_FIELDS = [
    "observation_id",
    "event_id",
    "year",
    "field",
    "value",
    "metric",
    "source_url",
    "source_type",
    "retrieved_at",
    "confidence",
    "raw_text",
    "notes",
]

# Ordered from most to least precise.
LOCATION_PRECISIONS = ("site", "area", "town", "region", "country")


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
