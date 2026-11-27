import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VizExportTest(unittest.TestCase):
    def test_exports_cancellations_and_excludes_catalogue_snapshots(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "events.seed.stamp.csv").write_text(
                "event_id,name,country\na,Example,Spain\n"
            )
            (data / "editions.seed.stamp.csv").write_text(
                "event_id,year,population,status,lat,lon\n"
                "a,2020,,cancelled,,\na,2022,120,catalogue_snapshot,,\na,2023,20,held,40,0\n"
            )
            output = data / "viz.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "export_viz.py"), str(data), str(output)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = json.loads(output.read_text())
            self.assertEqual([row["year"] for row in dataset], [2020, 2023])
            self.assertIsNone(dataset[0]["population"])
            self.assertEqual(dataset[1]["lon"], 0)
            self.assertEqual(dataset[1]["name"], "Example")

    def test_preserves_attendance_and_exposes_conflicting_counts(self):
        from export_viz import export

        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "events.recovered.stamp.csv").write_text(
                "event_id,name,country\na,Example,Spain\n"
            )
            (data / "editions.recovered.stamp.csv").write_text(
                "event_id,year,population,population_metric,status,lat,lon\n"
                "a,2022,20,attendance,held,,\na,2022,25,tickets_sold,held,,\n"
                "a,2023,30,attendance,held,,\na,2023,40,attendance,held,,\n"
            )
            attendance, conflict = export(data)
            self.assertEqual(attendance["population"], 20)
            self.assertIsNone(conflict["population"])
            self.assertEqual(conflict["conflicting_populations"], [30, 40])

    def test_catalogue_export_preserves_discovery_status_and_metric(self):
        from export_viz import export

        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "catalogue_2019.events.stamp.csv").write_text(
                "event_id,name,country\na,Example,Spain\n"
            )
            (data / "catalogue_2019.editions.stamp.csv").write_text(
                "event_id,year,population,population_metric,status,lat,lon\n"
                "a,2019,120,catalogue_size_snapshot,catalogue_snapshot,,\n"
            )
            (data / "catalogue_locations.csv").write_text(
                "event_id,start,end,location,lat,lon,source_url,precision\n"
                "a,2019,2019,Spain,40,-4,https://example.com,country\n"
            )
            row, = export(data, catalogue=True)
            self.assertEqual((row["lat"], row["lon"]), (40, -4))
            self.assertEqual(row["location_precision"], "country")
            self.assertEqual(row["status"], "catalogue_snapshot")
            self.assertEqual(row["population_metric"], "catalogue_size_snapshot")
            self.assertEqual(row["population"], 120)

    def test_newer_batches_take_precedence_regardless_of_kind(self):
        from export_viz import export

        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "events.recovered.20260101T000000Z.csv").write_text(
                "event_id,name,country\na,Example,Spain\n"
            )
            (data / "editions.recovered.20260101T000000Z.csv").write_text(
                "event_id,year,population,population_metric,status,lat,lon\n"
                "a,2022,20,attendance,held,,\n"
            )
            (data / "editions.research.20260201T000000Z.csv").write_text(
                "event_id,year,population,population_metric,status,lat,lon,start_date,end_date\n"
                "a,2022,20,attendance,held,,,2022-07-06,2022-07-10\n"
            )
            row, = export(data)
            self.assertEqual((row["start_date"], row["end_date"]), ("2022-07-06", "2022-07-10"))

    def test_marks_estimates_and_location_precision(self):
        from export_viz import export

        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "events.research.stamp.csv").write_text(
                "event_id,name,country\na,Example,Spain\n"
            )
            (data / "editions.research.stamp.csv").write_text(
                "event_id,year,population,population_metric,status,lat,lon,location_precision\n"
                "a,2021,100,organizer_estimate,held,,,\n"
                "a,2022,90,attendance,held,41,-1,site\n"
                "a,2023,,,held,,,\n"
            )
            (data / "viz_locations.csv").write_text(
                "event_id,start,end,location,lat,lon,source_url,precision\n"
                "a,2021,2022,Monegros,41.5,-0.5,https://example.com,area\n"
            )
            estimate, counted, unknown = export(data)
            self.assertTrue(estimate["population_estimate"])
            self.assertEqual(estimate["location_precision"], "area")
            self.assertFalse(counted["population_estimate"])
            self.assertEqual((counted["lat"], counted["location_precision"]), (41, "site"))
            self.assertFalse(unknown["population_estimate"])
            self.assertEqual(unknown["start_date"], "")

    def test_edition_coordinates_keep_their_own_location_text(self):
        from export_viz import export

        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "events.research.stamp.csv").write_text("event_id,name,country\na,Example,Spain\n")
            (data / "editions.research.stamp.csv").write_text(
                "event_id,year,location,population,status,lat,lon,location_precision\n"
                "a,2022,Venue farm,,held,41,-1,site\n"
            )
            (data / "viz_locations.csv").write_text(
                "event_id,start,end,location,lat,lon,source_url,precision\n"
                "a,2022,2022,Old reference,41.5,-0.5,https://example.com,area\n"
            )
            row, = export(data)
            self.assertEqual((row["location"], row["location_source"]), ("Venue farm", ""))

    def test_reference_locations_record_their_precision(self):
        with (ROOT / "data" / "viz_locations.csv").open(newline="") as stream:
            locations = list(csv.DictReader(stream))
        self.assertTrue(locations)
        self.assertTrue(all(row["precision"] in {"site", "area", "town", "region", "country"}
                            for row in locations))

    def test_rows_carry_event_details_and_every_reported_figure(self):
        from export_viz import export

        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / "events.research.stamp.csv").write_text(
                "event_id,name,country,first_year,parent_event_id,official_status,notes\n"
                "a,Example,Spain,2015,b,official_regional,Renamed in 2018.\n"
                "b,Origin,USA,,,origin,\n"
            )
            (data / "editions.research.stamp.csv").write_text(
                "event_id,year,population,population_metric,status,lat,lon,source_url,confidence\n"
                "a,2022,90,attendance,held,,,https://a.example,high\n"
                "a,2022,120,tickets_sold,held,,,https://b.example,medium\n"
                "a,2023,,,cancelled,,,https://c.example,high\n"
                "b,2022,,,held,,,,\n"
            )
            held, origin, cancelled = export(data)
            self.assertEqual(
                (held["first_year"], held["parent_event_id"], held["official_status"], held["event_notes"]),
                (2015, "b", "official_regional", "Renamed in 2018."),
            )
            self.assertEqual(held["reported_figures"], [
                {"population": 90, "metric": "attendance", "estimate": False,
                 "source_url": "https://a.example", "confidence": "high"},
                {"population": 120, "metric": "tickets_sold", "estimate": False,
                 "source_url": "https://b.example", "confidence": "medium"},
            ])
            self.assertEqual(cancelled["reported_figures"], [])
            self.assertIsNone(origin["first_year"])
