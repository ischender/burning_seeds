"""Export the reviewed candidate batches used by the visualization."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def export(directory, *, catalogue=False):
    events = {}
    editions = {}
    batches = (
        (("catalogue_2019.events.*.csv", "catalogue_2019.editions.*.csv"),)
        if catalogue else tuple(
            (f"events.{batch}.*.csv", f"editions.{batch}.*.csv")
            for batch in ("seed", "research", "recovered")
        )
    )
    for event_pattern, edition_pattern in batches:
        for path in sorted(directory.glob(event_pattern)):
            events.update((row["event_id"], row) for row in rows(path))
        for path in sorted(directory.glob(edition_pattern)):
            candidates = defaultdict(list)
            for row in rows(path):
                if (row["status"] == "catalogue_snapshot") == catalogue:
                    candidates[row["event_id"], int(row["year"])].append(row)
            editions.update(candidates)

    location_path = directory / ("catalogue_locations.csv" if catalogue else "viz_locations.csv")
    locations = rows(location_path) if location_path.is_file() else []
    result = []
    for (event_id, year), candidates in sorted(editions.items(), key=lambda item: item[0][::-1]):
        edition = next((row for row in candidates if row.get("population_metric") == "attendance"), candidates[0])
        metric = edition.get("population_metric")
        figures = sorted({
            int(row["population"]) for row in candidates
            if row.get("population_metric") == metric and row["population"]
        })
        event = events[event_id]
        location = next((
            row for row in locations
            if row["event_id"] == event_id and int(row["start"]) <= year <= int(row["end"])
        ), {})
        lat = edition["lat"] or location.get("lat")
        lon = edition["lon"] or location.get("lon")
        result.append({
            **edition,
            "year": year,
            "name": event["name"],
            "country": event["country"],
            "population": figures[0] if len(figures) == 1 else None,
            "conflicting_populations": figures if len(figures) > 1 else [],
            "location": (edition.get("location", "") if catalogue else
                         location.get("location", edition.get("location", ""))),
            "location_source": location.get("source_url", ""),
            "location_precision": location.get("precision", ""),
            "map_reference": location.get("location", ""),
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
        })
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--catalogue", action="store_true")
    args = parser.parse_args()
    dataset = export(args.data, catalogue=args.catalogue)
    args.output.write_text(json.dumps(dataset, ensure_ascii=False) + "\n", encoding="utf-8")
