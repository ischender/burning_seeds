#!/usr/bin/env python3
"""Validate Burning Seeds CSVs without modifying them."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from starter_utils import (
    candidate_path,
    ensure_parent,
    utc_stamp,
)


EVENT_REQUIRED = [
    "event_id",
    "name",
    "country",
    "first_year",
    "parent_event_id",
    "official_status",
    "notes",
]

EDITION_REQUIRED = [
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
]

OBS_REQUIRED = [
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

VALID_CONFIDENCE = {
    "",
    "high",
    "medium",
    "low",
}

VALID_STATUS = {
    "",
    "held",
    "cancelled",
    "virtual",
    "precursor_held",
    "pilot_burn",
    "catalogue_snapshot",
    "scheduled_or_unverified",
    "unknown",
}


def read_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    with path.open(
        encoding="utf-8",
        newline="",
    ) as fh:
        reader = csv.DictReader(fh)

        return (
            list(
                reader.fieldnames
                or []
            ),
            list(reader),
        )


def missing_columns(
    actual: list[str],
    required: list[str],
) -> list[str]:

    return [
        x
        for x in required
        if x not in actual
    ]


def parse_float(value: str):
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--events",
        required=True,
    )

    parser.add_argument(
        "--editions",
        required=True,
    )

    parser.add_argument(
        "--observations",
    )

    parser.add_argument(
        "--report",
    )

    args = parser.parse_args()

    (
        event_fields,
        events,
    ) = read_csv(
        Path(args.events)
    )

    (
        edition_fields,
        editions,
    ) = read_csv(
        Path(args.editions)
    )

    observations = []
    obs_fields = []

    if args.observations:
        (
            obs_fields,
            observations,
        ) = read_csv(
            Path(args.observations)
        )

    report = {
        "schema_errors": [],
        "errors": [],
        "warnings": [],
        "stats": {},
        "conflicts": [],
    }

    for (
        label,
        actual,
        required,
    ) in (
        (
            "events",
            event_fields,
            EVENT_REQUIRED,
        ),
        (
            "editions",
            edition_fields,
            EDITION_REQUIRED,
        ),
        (
            "observations",
            obs_fields,
            (
                OBS_REQUIRED
                if args.observations
                else []
            ),
        ),
    ):
        missing = missing_columns(
            actual,
            required,
        )

        if missing:
            report[
                "schema_errors"
            ].append({
                "table": label,
                "missing": missing,
            })

    event_ids = [
        r.get(
            "event_id",
            "",
        )
        for r in events
    ]

    event_set = {
        x
        for x in event_ids
        if x
    }

    if len(event_ids) != len(
        event_set
    ):
        report["errors"].append(
            "Duplicate or empty event_id "
            "values exist in events.csv."
        )

    for idx, row in enumerate(
        editions,
        start=2,
    ):
        eid = row.get(
            "event_id",
            "",
        )

        if eid not in event_set:
            report["errors"].append(
                f"editions.csv:{idx}: "
                f"orphan event_id={eid!r}"
            )

        year = row.get(
            "year",
            "",
        )

        if (
            year
            and (
                not year.isdigit()
                or not (
                    1800
                    <= int(year)
                    <= 2100
                )
            )
        ):
            report["errors"].append(
                f"editions.csv:{idx}: "
                f"invalid year={year!r}"
            )

        pop = row.get(
            "population",
            "",
        )

        if pop:
            popf = parse_float(pop)

            if (
                popf is None
                or popf < 0
            ):
                report[
                    "errors"
                ].append(
                    f"editions.csv:{idx}: "
                    "invalid population="
                    f"{pop!r}"
                )

        lat = row.get(
            "lat",
            "",
        )

        lon = row.get(
            "lon",
            "",
        )

        if bool(lat) != bool(lon):
            report[
                "warnings"
            ].append(
                f"editions.csv:{idx}: "
                "only one coordinate present."
            )

        if (
            lat
            and not (
                -90
                <= float(lat)
                <= 90
            )
        ):
            report[
                "errors"
            ].append(
                f"editions.csv:{idx}: "
                "latitude out of range."
            )

        if (
            lon
            and not (
                -180
                <= float(lon)
                <= 180
            )
        ):
            report[
                "errors"
            ].append(
                f"editions.csv:{idx}: "
                "longitude out of range."
            )

        confidence = row.get(
            "confidence",
            "",
        )

        if (
            confidence
            not in VALID_CONFIDENCE
        ):
            report[
                "warnings"
            ].append(
                f"editions.csv:{idx}: "
                "nonstandard confidence="
                f"{confidence!r}"
            )

        status = row.get(
            "status",
            "",
        )

        if (
            status
            not in VALID_STATUS
        ):
            report[
                "warnings"
            ].append(
                f"editions.csv:{idx}: "
                "nonstandard status="
                f"{status!r}"
            )

        if (
            status == "cancelled"
            and pop not in (
                "",
                "0",
            )
        ):
            report[
                "warnings"
            ].append(
                f"editions.csv:{idx}: "
                "cancelled edition has "
                f"population={pop!r}; "
                "verify semantics."
            )

        if not lat or not lon:
            report[
                "warnings"
            ].append(
                f"editions.csv:{idx}: "
                "missing coordinates for "
                f"{eid} {year}."
            )

    groups = defaultdict(list)

    for row in editions:
        key = (
            row.get(
                "event_id",
                "",
            ),
            row.get(
                "year",
                "",
            ),
        )

        groups[key].append(row)

    for (
        key,
        rows,
    ) in groups.items():

        by_metric = defaultdict(set)

        for row in rows:
            metric = row.get(
                "population_metric",
                "",
            )

            value = row.get(
                "population",
                "",
            )

            if value:
                by_metric[
                    metric
                ].add(value)

        for (
            metric,
            values,
        ) in by_metric.items():

            if len(values) > 1:
                report[
                    "conflicts"
                ].append({
                    "event_id": (
                        key[0]
                    ),
                    "year": key[1],
                    "population_metric": (
                        metric
                    ),
                    "values": sorted(
                        values
                    ),
                })

    report["stats"] = {
        "events": len(events),
        "editions": len(editions),
        "observations": len(
            observations
        ),
        "editions_missing_coords": (
            sum(
                1
                for r in editions
                if (
                    not r.get("lat")
                    or not r.get("lon")
                )
            )
        ),
        "conflicting_event_year_metrics": (
            len(
                report["conflicts"]
            )
        ),
    }

    if args.report:
        output = Path(
            args.report
        )
    else:
        output = (
            Path("data")
            / (
                f"validation."
                f"{utc_stamp()}.json"
            )
        )

    output = candidate_path(
        output
    )

    ensure_parent(output)

    output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            report["stats"],
            indent=2,
        )
    )

    print(
        f"Wrote {output}"
    )

    return (
        1
        if (
            report[
                "schema_errors"
            ]
            or report["errors"]
        )
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
