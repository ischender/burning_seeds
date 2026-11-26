# Burning Seeds

The standard-library Python starter is based on burner-seed-handoff.md.
The canonical CSVs in `data/` are schema templates. The initial historical seed
is checked in alongside them as timestamped candidates for review.

```sh
python3 -m unittest discover -s tests -v
python3 seed_data.py --out-dir data
```

Validate one run by substituting its timestamp below.

```sh
stamp=YYYYMMDDTHHMMSSZ
python3 validate.py \
  --events "data/events.seed.$stamp.csv" \
  --editions "data/editions.seed.$stamp.csv" \
  --observations "data/observations.seed.$stamp.csv"
```

Archive the 2019 Burns Around the World CSV export in `data/raw/`, then
run `python3 import_catalogue.py --input data/raw/burns_around_world_2019.csv`.
Review aliases against the seed before promoting records. The importer records
catalogue sizes as snapshots and preserves the raw catalogue text in observations.

Run `python3 geocode.py --help` for sample geocoding. Use an identifying user
agent with your contact information, set an explicit small limit, and inspect
locations before accepting the generated coordinates.
