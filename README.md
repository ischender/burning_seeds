# Burning Seeds

The standard-library Python starter is based on docs/burner-seed-handoff.md.
The canonical CSVs in `data/` are schema templates. The initial historical seed
is available alongside them as timestamped candidates for review.

```sh
uv run python -m unittest discover -s tests -v
uv run python seed_data.py --out-dir data
```

Validate one run by substituting its timestamp below.

```sh
stamp=YYYYMMDDTHHMMSSZ
uv run python validate.py \
  --events "data/events.seed.$stamp.csv" \
  --editions "data/editions.seed.$stamp.csv" \
  --observations "data/observations.seed.$stamp.csv"
```

Archive the 2019 Burns Around the World CSV export in `data/raw/`, then
run `uv run python import_catalogue.py --input data/raw/burns_around_world_2019.csv`.
Review aliases against the seed before promoting records. The importer records
catalogue sizes as snapshots and preserves the raw catalogue text in observations.

Run `uv run python geocode.py --help` for sample geocoding. Use an identifying user
agent with your contact information, set an explicit small limit, and inspect
locations before accepting the generated coordinates.

## Historical atlas

The atlas is a local Svelte app. From the repository root, run:

```sh
uv run --locked python export_viz.py data viz/src/editions.json
npm --prefix viz ci
npm --prefix viz run dev
```

For a static build, use `npm --prefix viz run build`. The export uses seed,
research, and recovered candidates in that order, with later batches taking
precedence. It excludes catalogue snapshots and keeps conflicting attendance
figures visible in the record list. Approximate map reference points and their
sources are stored in `data/viz_locations.csv`. Edition records without a
location fix remain visible in the list. Land geometry comes from Natural Earth.
