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

The atlas is a Svelte app, deployed as static assets on Cloudflare Workers (see
Deploying). From the repository root, run:

```sh
uv run --locked python export_viz.py data viz/src/editions.json
pnpm --dir viz install --frozen-lockfile
pnpm dev
```

For a static build, use `pnpm build`. The export reads seed, research, and
recovered candidates ordered by their batch timestamp. A newer batch replaces
every older row for the event-years it contains, so a batch that revisits an
event-year must carry forward the figures it keeps. The export excludes
catalogue snapshots and keeps conflicting attendance figures visible in the
record list. Edition coordinates take precedence over the approximate reference
points in `data/viz_locations.csv`, which record their source and precision.
Edition records without a location fix remain visible in the list. Land
geometry comes from Natural Earth.

Select a marker or a record name to open the detail panel. It shows the
selected year's edition (status, dates, location, every reported figure with
its metric, confidence, and source) and the event in general (first burn,
official status, notes, and every documented edition). The panel follows the
timeline, and a year in its history jumps the map there. Catalogue listings
open the same way and link to the event's timeline when it has documented
editions. Each exported row carries its event's `first_year`, `official_status`,
`parent_event_id`, and `event_notes`, plus `reported_figures` for all the
metrics reported that year. The pure helpers in `viz/src/details.js` are covered
by `pnpm --dir viz test` (Node's built-in test runner).

### Dates, estimates, and approximate locations

Editions record `start_date` and `end_date` as ISO dates. A `YYYY-MM` value
keeps month precision for phrases such as "early October". The
`location_precision` column describes how closely the row's coordinates locate
the venue, from most to least precise: `site`, `area`, `town`, `region`, or
`country`. The validator checks these columns when present, so earlier batches
without them stay valid.

The atlas draws counted figures (attendance, gate counts, tickets) as solid
markers. Organizer estimates, catalogue sizes, capacities, and lower bounds
are drawn as dashed, translucent markers and listed with "≈". Editions that
are only planned or whose status is unknown are drawn hollow. Town, region,
and country coordinates get a dotted halo that widens as precision falls. The
halo encodes the precision class, because real distances are sub-pixel at
world scale.

### Web research batches

Delegated research writes `events`, `editions`, and `observations` CSVs under
one `research` batch stamp, and never edits existing files. Each sourced claim
becomes an observation with a short verbatim quote. Validate every batch, and
review entity matches against the catalogue and seed before relying on it.

Correct a research batch with a newer review batch rather than editing it in
place. The review batch restates each affected event-year, and each correction
is recorded as a `review` observation. The 2019 catalogue is evidence of planned
dates, approximate sizes, and a first-burn year. It does not show that an
edition was held or where the first burn took place, so editions supported only
by the catalogue stay `scheduled_or_unverified` and keep their
`catalogue_size_snapshot` metric.

Regenerate the searchable global catalogue after importing a new copy of the
2019 source sheet:

```sh
uv run --locked python export_viz.py data viz/src/catalogue.json --catalogue
```

The catalogue preserves the sheet's approximate sizes and locations for discovery.

The catalogue map uses reference points in `data/catalogue_locations.csv`,
matched against Natural Earth's 1:10m populated places. A listing uses its
matched town, the relevant regional capital, or the national capital, in
that order. The original listing location and the map precision are both
shown. Virtual listings have no map point. These reference points apply
only to the catalogue, since historical editions can move between venues.

## Deploying

The atlas is the `burning-seeds` Worker (`viz/wrangler.jsonc`): static assets
only, served from `viz/dist/`. The exported JSON is committed, so a deploy
build needs only pnpm, not Python. First time: `pnpm --dir viz exec wrangler login`.

| Command | What it does |
| --- | --- |
| `make check` | Python and atlas tests, then a production build. Run before deploying |
| `make preview` | build, then serve `viz/dist/` through wrangler on :8787 |
| `make staging` | noindex build, uploaded as a preview version aliased to the current git branch |
| `make deploy` | `make check`, then `wrangler deploy` to production |

**Production**: `https://burningseeds.wetwarecraft.com`. The `wetwarecraft.com`
zone is on Cloudflare, so the first deploy creates the DNS record and
certificate for the custom domain. Don't add a record by hand.

**Previews, by hand**: `make staging` on a branch uploads a version without
deploying it and prints `https://<branch>-burning-seeds.<account>.workers.dev`.

**Previews, automatic**: in the Cloudflare dashboard, open Workers →
burning-seeds → Settings → Builds and connect the GitHub repository. Set the
root directory to `viz`, the build command to
`pnpm install --frozen-lockfile && pnpm build`, the deploy command to
`npx wrangler deploy`, and the production branch to `main`. Enable
non-production branch builds; they run `npx wrangler versions upload`, which
gets a branch alias. Builds of any branch but `main` are noindexed
automatically (`WORKERS_CI_BRANCH`, see `viz/build-env.js`).
