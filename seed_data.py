#!/usr/bin/env python3
"""Create a small, provenance-aware seed dataset without overwriting files.

The output is intentionally a seed, not a claim of completeness.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from starter_utils import (
    EDITION_FIELDS,
    EVENT_FIELDS,
    OBS_FIELDS,
    candidate_path,
    ensure_parent,
    utc_stamp,
)



BURNING_MAN_TIMELINE = (
    "https://history.burningman.org/timeline/"
)

AFRIKABURN_ARCHIVE = (
    "https://www.afrikaburn.com/event/event-archive/"
)

ELEMENT11_TIMELINE = (
    "https://www.element11.org/history/timeline/"
)


def write_csv(
    path: Path,
    fields: list[str],
    rows: list[dict],
) -> Path:
    path = candidate_path(path)
    ensure_parent(path)

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            restval="",
        )
        writer.writeheader()
        writer.writerows(rows)

    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        default="data",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    stamp = utc_stamp()

    events = [
        {
            "event_id": "burning_man",
            "name": "Burning Man",
            "country": "USA",
            "first_year": "1986",
            "parent_event_id": "",
            "official_status": "origin",
            "notes": (
                "Baker Beach origin; later moved to Nevada."
            ),
        },
        {
            "event_id": "burning_flipside",
            "name": "Burning Flipside",
            "country": "USA",
            "first_year": "1998",
            "parent_event_id": "",
            "official_status": "official_regional",
            "notes": (
                "1998 precursor/name: Burning Man Texas; "
                "Flipside name from 1999."
            ),
        },
        {
            "event_id": "element11",
            "name": "Element 11",
            "country": "USA",
            "first_year": "1998",
            "parent_event_id": "",
            "official_status": "period_specific",
            "notes": (
                "1998 precursor gathering; first Synorgy regional "
                "burn in 1999; renamed Element 11 in 2006."
            ),
        },
        {
            "event_id": "afrikaburn",
            "name": "AfrikaBurn",
            "country": "South Africa",
            "first_year": "2007",
            "parent_event_id": "",
            "official_status": "official_regional",
            "notes": "",
        },
    ]

    editions = [
        {
            "event_id": "burning_man",
            "year": "1986",
            "location": (
                "Baker Beach, San Francisco, California, USA"
            ),
            "lat": "",
            "lon": "",
            "population": "35",
            "population_metric": "attendance",
            "confidence": "high",
            "status": "held",
            "source_url": (
                "https://history.burningman.org/timeline/1986/"
            ),
        },
        {
            "event_id": "burning_flipside",
            "year": "1998",
            "location": "Austin region, Texas, USA",
            "lat": "",
            "lon": "",
            "population": "30",
            "population_metric": "attendance",
            "confidence": "high",
            "status": "precursor_held",
            "source_url": (
                "https://history.burningman.org/timeline/1998/"
            ),
        },
        {
            "event_id": "element11",
            "year": "1998",
            "location": "Stansbury Island, Utah, USA",
            "lat": "",
            "lon": "",
            "population": "8",
            "population_metric": "attendance",
            "confidence": "high",
            "status": "precursor_held",
            "source_url": ELEMENT11_TIMELINE,
        },
        {
            "event_id": "element11",
            "year": "1999",
            "location": (
                "West Utah / Sun Tunnels area, Utah, USA"
            ),
            "lat": "",
            "lon": "",
            "population": "70",
            "population_metric": "organizer_estimate",
            "confidence": "high",
            "status": "held",
            "source_url": ELEMENT11_TIMELINE,
        },
        {
            "event_id": "afrikaburn",
            "year": "2007",
            "location": "Tankwa Karoo, South Africa",
            "lat": "",
            "lon": "",
            "population": "1000",
            "population_metric": "organizer_estimate",
            "confidence": "high",
            "status": "held",
            "source_url": AFRIKABURN_ARCHIVE,
        },
    ]

    observations = [
        {
            "observation_id": "obs_bm_1990_transition",
            "event_id": "burning_man",
            "year": "1990",
            "field": "population",
            "value": "350",
            "metric": "headline_population",
            "source_url": BURNING_MAN_TIMELINE,
            "source_type": "official_timeline",
            "retrieved_at": "",
            "confidence": "high",
            "raw_text": "",
            "notes": (
                "Keep separate from the smaller first Black Rock "
                "Desert gathering count documented in historical "
                "narrative."
            ),
        }
    ]

    event_path = write_csv(
        out_dir / f"events.seed.{stamp}.csv",
        EVENT_FIELDS,
        events,
    )

    edition_path = write_csv(
        out_dir / f"editions.seed.{stamp}.csv",
        EDITION_FIELDS,
        editions,
    )

    obs_path = write_csv(
        out_dir / f"observations.seed.{stamp}.csv",
        OBS_FIELDS,
        observations,
    )

    bundle_path = candidate_path(
        out_dir / f"dataset.seed.{stamp}.json"
    )

    ensure_parent(bundle_path)

    bundle = {
        "events": events,
        "editions": editions,
        "observations": observations,
    }

    bundle_path.write_text(
        json.dumps(
            bundle,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {event_path}")
    print(f"Wrote {edition_path}")
    print(f"Wrote {obs_path}")
    print(f"Wrote {bundle_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
