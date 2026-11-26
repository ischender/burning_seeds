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
