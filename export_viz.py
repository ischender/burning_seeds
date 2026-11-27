"""Export the reviewed candidate batches used by the visualization."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


# Direct counts; every other metric (organizer estimates, catalogue sizes,
# capacities, lower bounds) is shown as an estimate.
COUNTED_METRICS = {"attendance", "gate_count", "tickets_sold", "tickets_used"}
TIMELINE_BATCHES = ("seed", "research", "recovered")


def batch_paths(directory, table, *, catalogue):
    """Return batch CSVs oldest first, so newer evidence replaces older event-years."""
    if catalogue:
        return sorted(directory.glob(f"catalogue_2019.{table}.*.csv"))
    paths = [path for batch in TIMELINE_BATCHES for path in directory.glob(f"{table}.{batch}.*.csv")]
    return sorted(paths, key=lambda path: (path.name.split(".")[2], path.name))


def reported_figures(candidates):
    """Every figure reported for one event-year, with its own metric and source."""
    return [{
        "population": int(row["population"]),
        "metric": row.get("population_metric", ""),
        "estimate": row.get("population_metric", "") not in COUNTED_METRICS,
        "source_url": row.get("source_url", ""),
        "confidence": row.get("confidence", ""),
    } for row in candidates if row["population"]]


def export(directory, *, catalogue=False):
    events = {}
    editions = {}
    for path in batch_paths(directory, "events", catalogue=catalogue):
        events.update((row["event_id"], row) for row in rows(path))
    for path in batch_paths(directory, "editions", catalogue=catalogue):
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
        if edition["lat"] and edition["lon"]:
            # The edition's own fix wins, so its text and source must win too.
            location = {"lat": edition["lat"], "lon": edition["lon"],
                        "precision": edition.get("location_precision", "")}
        lat = location.get("lat")
        lon = location.get("lon")
        precision = location.get("precision", "")
        result.append({
            **edition,
            "year": year,
            "name": event["name"],
            "country": event["country"],
            "first_year": int(event["first_year"]) if event.get("first_year") else None,
            "parent_event_id": event.get("parent_event_id", ""),
            "official_status": event.get("official_status", ""),
            "event_notes": event.get("notes", ""),
            "reported_figures": reported_figures(candidates),
            "population": figures[0] if len(figures) == 1 else None,
            "conflicting_populations": figures if len(figures) > 1 else [],
            "population_estimate": bool(figures) and metric not in COUNTED_METRICS,
            "start_date": edition.get("start_date", ""),
            "end_date": edition.get("end_date", ""),
            "location": (edition.get("location", "") if catalogue else
                         location.get("location", edition.get("location", ""))),
            "location_source": location.get("source_url", ""),
            "location_precision": precision,
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
