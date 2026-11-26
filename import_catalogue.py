#!/usr/bin/env python3
"""Import the public 2019 "Burns Around the World" Google Sheet.

The importer treats the sheet as a discovery/catalogue snapshot, not as proof
that each listed event occurred in every year since its first burn.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import unicodedata
import urllib.request
from pathlib import Path
from typing import Iterable

from starter_utils import candidate_path, ensure_parent, utc_stamp


SHEET_ID = (
    "1_t7ltGb3BD8Ocs3W3CajANOJa2tKDZLpZeBy4XyhjNc"
)

DEFAULT_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid=1584735033"
)

SOURCE_URL = (
    "https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/edit#gid=1584735033"
)

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


def slugify(value: str) -> str:
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode()
    )

    value = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        value.strip().lower(),
    ).strip("_")

    return value or "unnamed_event"


def clean_header(value: str) -> str:
    value = (
        (value or "")
        .replace("\n", " ")
        .strip()
        .upper()
    )

    return re.sub(r"\s+", " ", value)


def parse_first_year(value: str) -> str:
    match = re.search(
        r"\b(19|20)\d{2}\b",
        value or "",
    )

    return match.group(0) if match else ""


def parse_size(
    value: str,
) -> tuple[str, str]:

    raw = (value or "").strip()

    if not raw:
        return "", ""

    nums = [
        int(x.replace(",", ""))
        for x in re.findall(
            r"\d[\d,]*",
            raw,
        )
    ]

    if not nums:
        return "", f"Unparsed catalogue size: {raw}"

    if (
        len(nums) >= 2
        and any(
            sep in raw
            for sep in ("-", "–", "~")
        )
    ):
        midpoint = round(
            sum(nums[:2]) / 2
        )

        return (
            str(midpoint),
            f"Catalogue range/approximation: {raw}",
        )

    return (
        str(nums[0]),
        f"Catalogue size as published: {raw}",
    )


def fetch_csv(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "burning-seeds-catalogue-import/0.1"
            )
        },
    )

    with urllib.request.urlopen(
        req,
        timeout=30,
    ) as resp:
        return resp.read().decode(
            "utf-8-sig"
        )


def load_rows(
    text: str,
) -> list[dict[str, str]]:

    raw_rows = list(
        csv.reader(io.StringIO(text))
    )

    header_idx = None

    for i, row in enumerate(raw_rows):
        if row:
            title_year = re.fullmatch(
                r"Burns Around the World (\d{4})", row[0].strip(), re.IGNORECASE
            )
            if title_year and title_year[1] != "2019":
                raise ValueError(f"Expected the 2019 catalogue, got {title_year[1]}.")
        normalized = [
            clean_header(x)
            for x in row
        ]

        if (
            "NAME" in normalized
            and any(
                h.startswith("FIRST BURN")
                for h in normalized
            )
        ):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(
            "Could not find the catalogue header row "
            "containing NAME and FIRST BURN."
        )

    headers = [
        clean_header(x) or f"COL_{i}"
        for i, x in enumerate(
            raw_rows[header_idx]
        )
    ]

    rows = []

    for raw in raw_rows[
        header_idx + 1:
    ]:
        if not any(
            (x or "").strip()
            for x in raw
        ):
            continue

        padded = (
            raw
            + [""] * max(
                0,
                len(headers) - len(raw),
            )
        )

        rows.append(
            dict(
                zip(
                    headers,
                    padded[:len(headers)],
                )
            )
        )

    return rows


def pick(
    row: dict[str, str],
    *prefixes: str,
) -> str:

    for key, value in row.items():
        if any(
            key.startswith(p)
            for p in prefixes
        ):
            return (
                value or ""
            ).strip()

    return ""


def normalize(
    rows: Iterable[
        dict[str, str]
    ],
):
    events = []
    editions = []
    observations = []

    seen_ids: dict[str, int] = {}

    for idx, row in enumerate(
        rows,
        start=1,
    ):
        name = pick(
            row,
            "NAME",
        )

        if not name:
            continue

        base_id = slugify(name)

        count = seen_ids.get(
            base_id,
            0,
        )

        seen_ids[base_id] = (
            count + 1
        )

        event_id = (
            base_id
            if count == 0
            else f"{base_id}_{count + 1}"
        )

        town = pick(
            row,
            "(CLOSEST) TOWN",
            "TOWN",
        )

        region = pick(
            row,
            "STATE/PROVINCE/REGION",
        )

        country = pick(
            row,
            "COUNTRY",
        )

        first_year = parse_first_year(
            pick(
                row,
                "FIRST BURN",
            )
        )

        sanctioned = pick(
            row,
            "BM SANCTIONNED",
            "BM SANCTIONED",
        )

        remarks = pick(
            row,
            "REMARKS",
        )

        website = pick(
            row,
            "WEBSITE",
        )

        size_raw = pick(
            row,
            "SIZE",
        )

        (
            population,
            size_note,
        ) = parse_size(size_raw)

        official_status = "unknown"

        if sanctioned.upper().startswith(
            "Y"
        ):
            official_status = (
                "official_regional_in_2019_catalogue"
            )

        elif sanctioned.upper().startswith(
            "N"
        ):
            official_status = (
                "not_official_in_2019_catalogue"
            )

        events.append({
            "event_id": event_id,
            "name": name,
            "country": country,
            "first_year": first_year,
            "parent_event_id": "",
            "official_status": (
                official_status
            ),
            "notes": remarks,
        })

        location = ", ".join(
            x
            for x in (
                town,
                region,
                country,
            )
            if x
        )

        editions.append({
            "event_id": event_id,
            "year": "2019",
            "location": location,
            "lat": "",
            "lon": "",
            "population": population,
            "population_metric": (
                "catalogue_size_snapshot"
            ),
            "confidence": "medium",
            "status": (
                "catalogue_snapshot"
            ),
            "source_url": SOURCE_URL,
        })

        observations.append({
            "observation_id": (
                f"catalogue2019_{idx:04d}"
            ),
            "event_id": event_id,
            "year": "2019",
            "field": (
                "catalogue_record"
            ),
            "value": size_raw,
            "metric": (
                "catalogue_size_snapshot"
            ),
            "source_url": SOURCE_URL,
            "source_type": (
                "community_catalogue"
            ),
            "retrieved_at": "",
            "confidence": "medium",
            "raw_text": json.dumps(
                row,
                ensure_ascii=False,
            ),
            "notes": "; ".join(
                x
                for x in (
                    size_note,
                    (
                        f"website={website}"
                        if website
                        else ""
                    ),
                )
                if x
            ),
        })

    return (
        events,
        editions,
        observations,
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
        )

        writer.writeheader()
        writer.writerows(rows)

    return path


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        help=(
            "Local CSV export. "
            "If omitted, download the "
            "public Google Sheet."
        ),
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_CSV_URL,
    )

    parser.add_argument(
        "--out-dir",
        default="data",
    )

    args = parser.parse_args()

    if args.input:
        text = Path(
            args.input
        ).read_text(
            encoding="utf-8-sig"
        )
    else:
        text = fetch_csv(
            args.url
        )

    try:
        rows = load_rows(text)
    except ValueError as error:
        parser.error(str(error))

    (
        events,
        editions,
        observations,
    ) = normalize(rows)

    stamp = utc_stamp()
    out = Path(args.out_dir)

    paths = [
        write_csv(
            out
            / (
                f"catalogue_2019.events."
                f"{stamp}.csv"
            ),
            EVENT_FIELDS,
            events,
        ),
        write_csv(
            out
            / (
                f"catalogue_2019.editions."
                f"{stamp}.csv"
            ),
            EDITION_FIELDS,
            editions,
        ),
        write_csv(
            out
            / (
                f"catalogue_2019.observations."
                f"{stamp}.csv"
            ),
            OBS_FIELDS,
            observations,
        ),
    ]

    json_path = candidate_path(
        out
        / (
            f"catalogue_2019."
            f"{stamp}.json"
        )
    )

    ensure_parent(json_path)

    json_path.write_text(
        json.dumps(
            {
                "source": SOURCE_URL,
                "events": events,
                "editions": editions,
                "observations": observations,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    paths.append(json_path)

    print(
        f"Imported {len(events)} "
        "catalogue records."
    )

    for path in paths:
        print(f"Wrote {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
