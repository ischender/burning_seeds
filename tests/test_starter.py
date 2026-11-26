import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    def run_cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / script), *map(str, args)],
            capture_output=True, text=True,
        )

    def test_seed_generates_valid_linked_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = self.run_cli("seed_data.py", "--out-dir", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            events, = output.glob("events.seed.*.csv")
            editions, = output.glob("editions.seed.*.csv")
            observations, = output.glob("observations.seed.*.csv")
            report = output / "report.json"
            result = self.run_cli(
                "validate.py", "--events", events, "--editions", editions,
                "--observations", observations, "--report", report,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            stats = json.loads(report.read_text())["stats"]
            self.assertEqual((stats["events"], stats["editions"]), (4, 5))
            self.assertEqual(stats["editions_missing_coords"], 5)

    def test_catalogue_keeps_size_as_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            source = output / "source.csv"
            source.write_text(
                'Catalogue title\nNAME,COUNTRY,SIZE,FIRST BURN\n'
                'Fête du Feu,France,100-200,2012\n', encoding="utf-8",
            )
            result = self.run_cli(
                "import_catalogue.py", "--input", source, "--out-dir", output,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            editions, = output.glob("catalogue_2019.editions.*.csv")
            with editions.open(newline="") as stream:
                row, = csv.DictReader(stream)
            self.assertEqual(row["population_metric"], "catalogue_size_snapshot")
            self.assertEqual(row["population"], "150")
            self.assertEqual(row["event_id"], "fete_du_feu")

    def test_candidate_path_skips_existing_timestamped_sibling(self):
        from unittest.mock import patch

        from starter_utils import candidate_path

        with tempfile.TemporaryDirectory() as directory, patch(
            "starter_utils.utc_stamp", return_value="20261126T000000Z",
        ):
            target = Path(directory) / "events.csv"
            target.touch()
            candidate_path(target).touch()
            self.assertFalse(candidate_path(target).exists())

    def test_catalogue_rejects_a_title_for_another_year(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            source = output / "source.csv"
            source.write_text(
                "Burns Around the World 2018\nNAME,FIRST BURN\nExample,2012\n",
                encoding="utf-8",
            )
            result = self.run_cli(
                "import_catalogue.py", "--input", source, "--out-dir", output,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("2018", result.stderr)
            self.assertEqual(list(output.glob("catalogue_2019.*")), [])
