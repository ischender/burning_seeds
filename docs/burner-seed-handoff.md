  

# Burning Seeds: Codex-ready project starter

## Executive summary

The project is ready to move into Codex as a reproducible data-engineering repository rather than another one-off research exercise.

The recovered Deep Research report already established a useful seed: 91 event entities and 205 edition/year observations, with explicit distinctions between attendance, tickets sold, capacity, cancellations, catalogue snapshots, and unresolved conflicts. It also recommends keeping `events.csv` as the entity layer, `editions.csv` as the animation-driving layer, and `observations.csv` as the provenance/conflict audit trail.

I built a starter bundle around that model. The important design choices are:

- Existing files are never silently overwritten.
- Unknown population is `null`/blank, never `0`.
- A cancelled event is not an event with attendance `0`.
- Attendance, tickets sold, tickets used, capacity, organizer estimates, and catalogue-scale estimates remain separate metrics.
- Locations belong to editions because events move.
- Current catalogues are discovery sources, not proof that every intervening annual edition happened.
- Raw/conflicting observations survive reconciliation.
- Every generated dataset is timestamped.
- Python starter code uses only the standard library.
- Codex is explicitly instructed to inspect `/Users/aliosha/Development/personal_code/burning_seeds` before touching anything.

This matches the evidence structure found in the historical sources. For example, the Nowhere census simultaneously provides a retrospective participant series and separately reports 2,980 tickets sold for 2023, demonstrating why ticket and attendance fields should not be collapsed. Kiwiburn similarly publishes annual AfterBurn reports and its 2013 report gives an explicit attendance series for 2007-2013.

**Starter bundle:** [burning_seeds_codex_starter.zip](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)

The individual files are also available directly:

|File|Purpose|
|---|---|
|[PROJECT_BRIEF.md](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Project goals, model, workflow, source hierarchy|
|[AGENTS.md](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Persistent Codex instructions|
|[README.md](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Operator/runbook instructions|
|[seed_data.py](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Non-destructive historical seed|
|[import_catalogue.py](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|2019 catalogue importer|
|[geocode.py](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Cached, rate-limited geocoder|
|[validate.py](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Schema/conflict/geography validation|
|[starter_utils.py](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Shared non-destructive helpers|
|[events.csv](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Minimal entity template|
|[editions.csv](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Minimal edition template|
|[observations.csv](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Raw provenance template|
|[test_starter.py](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Starter tests|

The five starter unit tests pass locally in the generated bundle.

## Architecture and data model

The intended data flow is:

Show code

The split between entities, editions, and raw observations is important because the historical sources frequently disagree or measure different things. The recovered research explicitly found cases where the same event/year has gate counts, tickets sold, allocations, capacities, or approximate organizer figures.

`events.csv` is deliberately small:

csv

Copy

```csv
event_id,name,country,first_year,parent_event_id,official_status,notes
```

`parent_event_id` should only encode a documented lineage. Similar names, shared communities, or chronological proximity are not enough to infer ancestry. The historical record includes precursor/name transitions such as Burning Man Texas to Burning Flipside and Synorgy to Element 11, which are exactly the sort of distinctions that should survive rather than being normalized away. Burning Man's historical timeline documents the 1998 Texas regional and its subsequent Flipside name. Element 11's organizer history separately records the 1998 gathering, the first Synorgy event in 1999, and the Element 11 rename in 2006.

`editions.csv` is:

csv

Copy

```csv
event_id,year,location,lat,lon,population,population_metric,confidence,status,source_url
```

Recommended population metrics are:

text

Copy

```text
attendance
gate_count
tickets_used
tickets_sold
capacity
organizer_estimate
catalogue_size_snapshot
lower_bound
not_applicable
```

Recommended statuses are:

text

Copy

```text
held
cancelled
virtual
precursor_held
pilot_burn
catalogue_snapshot
scheduled_or_unverified
unknown
```

`observations.csv` is the non-destructive audit layer:

csv

Copy

```csv
observation_id,event_id,year,field,value,metric,source_url,source_type,retrieved_at,confidence,raw_text,notes
```

The confidence convention in the starter is:

|Confidence|Meaning|
|---|---|
|`high`|Organizer/official source, census, annual report, directly auditable primary evidence|
|`medium`|Reputable secondary source or community catalogue with plausible provenance|
|`low`|Weakly sourced, ambiguous, recollected, or unresolved|

The evidence state is deliberately distinct from confidence. An event can be confidently **discovered** without having a verified edition, or an edition can be definitely held while its attendance remains only **estimated**.

## Source strategy and reproducibility

The source priority should be primary-first.

Burning Man's official historical timeline is the backbone for the origin event and records population and historical milestones beginning in 1986; the 1986 page reports a population of 35. Burning Man's Regional Network history provides the institutional history of the regional network, while its 1998 timeline explicitly records Burning Man Texas as the first Regional Burn and reports 30 attendees.

The 2019 "Burns Around the World" spreadsheet is especially valuable as a historical catalogue snapshot. It exposes fields including event name, dates, town, state/region, country, size, first burn, website, and Burning Man sanction status. It includes long-tail events that may later disappear from current websites, which makes it valuable for discovery and archival reconstruction. The importer therefore records its size values as `catalogue_size_snapshot`, not as automatically verified 2019 attendance.

The Nowhere 2023 census is unusually strong because it contains a retrospective participant series from 2004 through 2023 and separately reports tickets sold/no-shows. AfrikaBurn maintains an organizer event archive with dates, themes, participant counts, and explicit cancellation records for historical years. Kiwiburn maintains a multi-year AfterBurn archive, including older annual reports suitable for extracting event-year records. Element 11's organizer timeline is particularly useful because it preserves event names, dates, attendance estimates, cancellations, venue changes, and precursor events back to 1998.

Burning Wiki should remain a discovery source rather than an authority. The site itself describes its list as best-effort and advises verification against original event sources; it also documents that its list was assembled from earlier official regional lists, older community calendars, Thomas Tighe's spreadsheet, and Burns Around the World.

The initial source queue is therefore:

|Priority|Source|Main use|
|---|---|---|
|1|`https://history.burningman.org/timeline/`|Burning Man historical spine|
|1|`https://burningman.org/global-events-groups/burning-man-regional-network/history-of-the-regional-network/`|Regional lineage/recognition|
|1|`https://docs.google.com/spreadsheets/d/1_t7ltGb3BD8Ocs3W3CajANOJa2tKDZLpZeBy4XyhjNc/edit`|2019 global discovery snapshot|
|1|`https://www.goingnowhere.org/wp-content/uploads/2023/12/nowhere-census-2023.pdf`|Nowhere population series|
|1|`https://www.afrikaburn.com/event/event-archive/`|AfrikaBurn annual series|
|1|`https://kiwiburn.com/about/about-the-event/afterburn/`|Kiwiburn annual reports|
|1|`https://www.element11.org/history/timeline/`|Element 11/Synorgy history|
|2|`https://web.archive.org/`|Defunct/changed organizer pages|
|2|`https://burningwiki.com/wiki/Burns_%26_Burners_Worldwide`|Discovery and source leads|

For geocoding, the starter defaults to OpenStreetMap's public Nominatim endpoint only for small, deliberate runs. Its current public policy requires an identifying User-Agent, caching, single-threaded operation, and at most one request per second; larger or recurring bulk jobs should use another provider or a self-hosted instance. The starter enforces a minimum delay and persistent cache for that reason.

## Codex operating brief

Codex officially recognizes `AGENTS.md` as repository guidance and loads applicable instructions from repository directories, making it a good place for the non-destructive and provenance rules rather than relying on a long prompt every session. OpenAI's own agent-oriented engineering guidance also recommends keeping the repository instruction file concise and using it as a map to deeper source-of-truth documentation.

The first Codex prompt should be approximately:

text

Copy

```text
Work in:

/Users/aliosha/Development/personal_code/burning_seeds

Before creating or modifying anything:

1. Inspect the repo root.
2. Run git status.
3. List existing files through depth 2.
4. Read every applicable AGENTS.md plus README.md and PROJECT_BRIEF.md.
5. Inspect existing data/, exports/, and tests/.

Do not overwrite any existing file.

If a requested target already exists, create a .candidate or .new sibling,
preserve the original, and show me the diff.

Then:

1. Run the existing tests.
2. Run seed_data.py.
3. Import the 2019 Burns Around the World catalogue.
4. Inspect generated event and edition candidates.
5. Do not merge candidates into canonical CSVs until conflicts have been reviewed.
6. Geocode only a small sample first, using the cache.
7. Run validate.py.
8. Report missing coordinates, conflicting attendance metrics, duplicate aliases,
   and unresolved entity matches.

Preserve provenance throughout.
Never convert missing population to zero.
Never infer that an event happened in an undocumented year.
```

Before editing, Codex should literally run:

bash

Copy

```bash
cd /Users/aliosha/Development/personal_code/burning_seeds

pwd
git status --short --branch
find . -maxdepth 2 -type f | sort
```

Then:

bash

Copy

```bash
cat AGENTS.md
cat PROJECT_BRIEF.md
cat README.md
```

If those files already exist, the starter versions should **not** replace them. Codex should copy them to something like:

text

Copy

```text
AGENTS.candidate.md
PROJECT_BRIEF.candidate.md
README.candidate.md
```

and compare them.

## Starter files and CLI usage

The normal first run is:

|Phase|Command|Expected output|
|---|---|---|
|Tests|`python3 -m unittest discover -s tests -v`|Passing starter tests|
|Seed|`python3 seed_data.py --out-dir data`|Timestamped seed CSV/JSON|
|Catalogue|`python3 import_catalogue.py --out-dir data`|Timestamped 2019 catalogue files|
|Geocode|`python3 geocode.py --input ... --user-agent ... --limit 20`|Candidate geocoded editions + cache|
|Validate|`python3 validate.py --events ... --editions ... --observations ...`|Timestamped JSON validation report|
|Export|`zip -r exports/...`|Timestamped repository handoff bundle|

The starter test suite currently verifies:

text

Copy

```text
slug normalization
catalogue-size parsing
range parsing
non-destructive output naming
2019 spreadsheet header detection
```

All five tests passed when the generated starter was exercised.

A first seed run creates outputs like:

text

Copy

```text
data/events.seed.20261126T113800Z.csv
data/editions.seed.20261126T113800Z.csv
data/observations.seed.20261126T113800Z.csv
data/dataset.seed.20261126T113800Z.json
```

The seed script intentionally writes timestamped files instead of populating `data/events.csv` directly. This creates a review step before anything becomes canonical.

Catalogue import:

bash

Copy

```bash
python3 import_catalogue.py --out-dir data
```

or, preferably for fully reproducible archival work, first save a local copy of the sheet:

bash

Copy

```bash
python3 import_catalogue.py \
  --input data/raw/burns_around_world_2019.csv \
  --out-dir data
```

Expected:

text

Copy

```text
data/catalogue_2019.events.<timestamp>.csv
data/catalogue_2019.editions.<timestamp>.csv
data/catalogue_2019.observations.<timestamp>.csv
data/catalogue_2019.<timestamp>.json
```

Geocode a small batch:

bash

Copy

```bash
python3 geocode.py \
  --input data/catalogue_2019.editions.<timestamp>.csv \
  --user-agent "burning-seeds/0.1 (contact: YOUR_EMAIL)" \
  --cache data/geocode_cache.json \
  --limit 20
```

Validate:

bash

Copy

```bash
python3 validate.py \
  --events data/events.csv \
  --editions data/editions.csv \
  --observations data/observations.csv
```

Export:

bash

Copy

```bash
mkdir -p exports
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

zip -r "exports/burning_seeds_${STAMP}.zip" \
  README.md PROJECT_BRIEF.md AGENTS.md \
  seed_data.py import_catalogue.py geocode.py validate.py \
  starter_utils.py data tests
```

## Starter file contents

### `data/events.csv`

csv

Copy

```csv
event_id,name,country,first_year,parent_event_id,official_status,notes
```

### `data/editions.csv`

csv

Copy

```csv
event_id,year,location,lat,lon,population,population_metric,confidence,status,source_url
```

### `data/observations.csv`

csv

Copy

```csv
observation_id,event_id,year,field,value,metric,source_url,source_type,retrieved_at,confidence,raw_text,notes
```

### `starter_utils.py`

python

Copy

```python
"""Shared small helpers for non-destructive output paths."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def candidate_path(path: Path) -> Path:
    """Return path if unused, otherwise a timestamped sibling without overwriting."""
    path = Path(path)
    if not path.exists():
        return path

    stamp = utc_stamp()

    if path.suffix:
        return path.with_name(
            f"{path.stem}.{stamp}.candidate{path.suffix}"
        )

    return path.with_name(
        f"{path.name}.{stamp}.candidate"
    )


def ensure_parent(path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
```

### `seed_data.py`

python

Copy

```python
#!/usr/bin/env python3
"""Create a small, provenance-aware seed dataset without overwriting files.

The output is intentionally a seed, not a claim of completeness.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from starter_utils import candidate_path, ensure_parent, utc_stamp


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
```

### `import_catalogue.py`

python

Copy

```python
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
    f"{SHEET_ID}/export?format=csv&gid=0"
)

SOURCE_URL = (
    "https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/edit"
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

    rows = load_rows(text)

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
```

### `geocode.py`

python

Copy

```python
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
```

### `validate.py`

python

Copy

```python
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
```

The full `README.md`, `PROJECT_BRIEF.md`, `AGENTS.md`, and test code are in the downloadable bundle above. They contain the same operating rules in repository-ready form rather than requiring Codex to reconstruct them from this report.

## Handoff checklist

The first productive Codex session should be narrowly scoped:

1. Inspect `/Users/aliosha/Development/personal_code/burning_seeds`, git status, existing instructions, and current data.
2. Copy in the starter files only where they do not collide; create `.candidate` versions where they do.
3. Run the five starter tests.
4. Run `seed_data.py` and inspect the timestamped candidates.
5. Export or download a local copy of the 2019 catalogue and run `import_catalogue.py`.
6. Resolve obvious aliases between the catalogue and existing events before creating canonical rows.
7. Geocode a small sample, inspect the returned locations manually, then expand cautiously.
8. Run `validate.py`; resolve orphan IDs and same-metric conflicts while preserving `observations.csv`.
9. Enrich the high-value historical series first: Burning Man, Flipside, Playa del Fuego, Element 11, Nowhere, Kiwiburn, AfrikaBurn, Midburn, Burning Seed.
10. Once the first validated edition table is usable, build the map visualization without waiting for perfect long-tail coverage.

The recovered research is already strong enough to justify this staged approach: the high-value historical spine is substantially documented, while the weak area is long-tail enrichment rather than the underlying data model. The historical source ecosystem also supports incremental recovery: official archives preserve major events, while community catalogues and archived newsletters expose older or defunct burns that can then be verified individually.