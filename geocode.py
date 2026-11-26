#!/usr/bin/env python3
"""Batch geocode edition locations with persistent caching."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from starter_utils import (
    candidate_path,
    ensure_parent,
    utc_stamp,
)


DEFAULT_PROVIDER = (
    "https://nominatim.openstreetmap.org/search"
)


def cache_key(query: str) -> str:
    return hashlib.sha256(
        query.strip().lower().encode(
            "utf-8"
        )
    ).hexdigest()


def load_cache(path: Path) -> dict:
    if not path.exists():
        return {}

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def save_cache(
    path: Path,
    cache: dict,
) -> None:

    ensure_parent(path)

    tmp = path.with_suffix(
        path.suffix + ".tmp"
    )

    tmp.write_text(
        json.dumps(
            cache,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    tmp.replace(path)


def request_json(
    url: str,
    user_agent: str,
    retries: int = 4,
) -> list[dict]:

    delay = 2.0

    for attempt in range(retries):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": (
                    "application/json"
                ),
            },
        )

        try:
            with urllib.request.urlopen(
                req,
                timeout=30,
            ) as resp:
                return json.loads(
                    resp.read().decode(
                        "utf-8"
                    )
                )

        except urllib.error.HTTPError as exc:
            if (
                exc.code
                not in (
                    429,
                    500,
                    502,
                    503,
                    504,
                )
                or attempt == retries - 1
            ):
                raise

        except urllib.error.URLError:
            if attempt == retries - 1:
                raise

        time.sleep(
            delay + random.random()
        )

        delay *= 2

    return []


def geocode_one(
    query: str,
    provider: str,
    user_agent: str,
) -> dict | None:

    params = urllib.parse.urlencode({
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
    })

    url = f"{provider}?{params}"

    results = request_json(
        url,
        user_agent=user_agent,
    )

    if not results:
        return None

    item = results[0]

    return {
        "lat": item.get(
            "lat",
            "",
        ),
        "lon": item.get(
            "lon",
            "",
        ),
        "display_name": item.get(
            "display_name",
            "",
        ),
        "osm_type": item.get(
            "osm_type",
            "",
        ),
        "osm_id": item.get(
            "osm_id",
            "",
        ),
        "raw": item,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
        help="Input editions CSV.",
    )

    parser.add_argument(
        "--output",
        help=(
            "Output CSV. Defaults to a "
            "timestamped file under data/."
        ),
    )

    parser.add_argument(
        "--cache",
        default="data/geocode_cache.json",
    )

    parser.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER,
    )

    parser.add_argument(
        "--user-agent",
        required=True,
        help=(
            'Identifying User-Agent, e.g. '
            '"burning-seeds/0.1 '
            '(contact: you@example.com)".'
        ),
    )

    parser.add_argument(
        "--min-delay",
        type=float,
        default=1.05,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help=(
            "0 means all ungeocoded rows."
        ),
    )

    args = parser.parse_args()

    if (
        args.provider == DEFAULT_PROVIDER
        and args.min_delay < 1.0
    ):
        raise SystemExit(
            "Public Nominatim must not exceed "
            "1 request/second; use "
            "--min-delay >= 1.0."
        )

    input_path = Path(
        args.input
    )

    with input_path.open(
        encoding="utf-8",
        newline="",
    ) as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(
            reader.fieldnames or []
        )
        rows = list(reader)

    for needed in (
        "location",
        "lat",
        "lon",
    ):
        if needed not in fieldnames:
            raise SystemExit(
                f"Missing required column: "
                f"{needed}"
            )

    cache_path = Path(
        args.cache
    )

    cache = load_cache(
        cache_path
    )

    requested = 0

    for row in rows:
        if (
            row.get("lat")
            and row.get("lon")
        ):
            continue

        query = (
            row.get("location")
            or ""
        ).strip()

        if not query:
            continue

        key = cache_key(query)

        result = cache.get(key)

        if result is None:
            if (
                args.limit
                and requested >= args.limit
            ):
                continue

            result = geocode_one(
                query,
                args.provider,
                args.user_agent,
            )

            cache[key] = {
                "query": query,
                "result": result,
                "provider": args.provider,
            }

            save_cache(
                cache_path,
                cache,
            )

            requested += 1

            time.sleep(
                args.min_delay
            )

        if result:
            row["lat"] = result.get(
                "lat",
                "",
            )

            row["lon"] = result.get(
                "lon",
                "",
            )

    if args.output:
        output = Path(
            args.output
        )
    else:
        output = (
            Path("data")
            / (
                "editions.geocoded."
                f"{utc_stamp()}.csv"
            )
        )

    output = candidate_path(
        output
    )

    ensure_parent(output)

    with output.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {output}")
    print(
        "Network geocoding requests: "
        f"{requested}"
    )
    print(
        f"Cache entries: {len(cache)}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
