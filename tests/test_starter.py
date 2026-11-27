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


class EditionSchemaTests(unittest.TestCase):
    def run_cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / script), *map(str, args)],
            capture_output=True, text=True,
        )

    def test_writers_share_the_canonical_edition_schema(self):
        from starter_utils import EDITION_FIELDS

        self.assertEqual(
            EDITION_FIELDS[-3:], ["start_date", "end_date", "location_precision"],
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(self.run_cli("seed_data.py", "--out-dir", output).returncode, 0)
            editions, = output.glob("editions.seed.*.csv")
            with editions.open(newline="") as stream:
                self.assertEqual(csv.DictReader(stream).fieldnames, EDITION_FIELDS)
        with (ROOT / "data" / "editions.csv").open(newline="") as stream:
            self.assertEqual(csv.DictReader(stream).fieldnames, EDITION_FIELDS)

    def test_catalogue_dates_keep_their_published_precision(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            source = output / "source.csv"
            source.write_text(
                "NAME,START DATE,END DATE,FIRST BURN\n"
                'Exact,"January 18, 2019","June 20,2019",2012\n'
                "Vague,early October,early October,2012\n"
                "Unknown,2019 dates TBA,2019 dates TBA,2012\n",
                encoding="utf-8",
            )
            result = self.run_cli("import_catalogue.py", "--input", source, "--out-dir", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            editions, = output.glob("catalogue_2019.editions.*.csv")
            with editions.open(newline="") as stream:
                dates = [(row["start_date"], row["end_date"]) for row in csv.DictReader(stream)]
            self.assertEqual(dates, [("2019-01-18", "2019-06-20"), ("2019-10", "2019-10"), ("", "")])

    def test_validator_checks_dates_and_location_precision(self):
        from starter_utils import EDITION_FIELDS

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            events = folder / "events.csv"
            events.write_text("event_id,name,country,first_year,parent_event_id,official_status,notes\na,A,Spain,,,,\n")
            editions = folder / "editions.csv"
            with editions.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=EDITION_FIELDS, restval="")
                writer.writeheader()
                writer.writerow({"event_id": "a", "year": "2020", "start_date": "2020-13-01"})
                writer.writerow({"event_id": "a", "year": "2021", "start_date": "2021-06-09",
                                 "end_date": "2021-06-02"})
                writer.writerow({"event_id": "a", "year": "2022", "start_date": "2023-06",
                                 "lat": "1", "lon": "2", "location_precision": "galaxy"})
                writer.writerow({"event_id": "a", "year": "2023", "start_date": "2023-06",
                                 "end_date": "2023-06-04", "lat": "1", "lon": "2",
                                 "location_precision": "site"})
            report = folder / "report.json"
            result = self.run_cli("validate.py", "--events", events, "--editions", editions,
                                  "--report", report)
            self.assertNotEqual(result.returncode, 0)
            findings = json.loads(report.read_text())
            errors = "\n".join(findings["errors"])
            warnings = "\n".join(findings["warnings"])
            self.assertIn("editions.csv:2: invalid start_date='2020-13-01'", errors)
            self.assertIn("editions.csv:3: end_date precedes start_date", errors)
            self.assertIn("editions.csv:4: start_date year differs from 2022", warnings)
            self.assertIn("editions.csv:4: nonstandard location_precision='galaxy'", warnings)
            self.assertNotIn("editions.csv:5", errors + warnings.replace("editions.csv:5: missing", ""))
