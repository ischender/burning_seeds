<script>
  import editions from './editions.json'
  import catalogue from './catalogue.json'
  import landSource from './land.geojson?raw'

  const start = Math.min(...editions.map(row => row.year))
  const end = Math.max(...editions.map(row => row.year))
  const years = Array.from({ length: end - start + 1 }, (_, i) => i + start)
  const project = ([lon, lat]) => [(lon + 180) * 2.5, (82 - lat) * 2.5]
  const land = JSON.parse(landSource).features.flatMap(({ geometry }) =>
    geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates
  ).map(polygon => polygon.map(ring =>
    'M' + ring.map(point => project(point).join(',')).join('L') + 'Z'
  ).join(''))
  const format = new Intl.NumberFormat('en')
  const metrics = {
    attendance: 'Attendance', organizer_estimate: 'Organizer estimate',
    gate_count: 'Gate count', tickets_sold: 'Tickets sold',
    tickets_used: 'Tickets used', capacity: 'Capacity', lower_bound: 'Lower bound',
  }
  const statuses = {
    held: 'Held', cancelled: 'Cancelled', precursor_held: 'Precursor',
    pilot_burn: 'Pilot burn', virtual: 'Virtual',
  }

  let year = $state(editions.some(row => row.year === 2023) ? 2023 : end)
  let playing = $state(false)
  let showCatalogue = $state(false)
  let query = $state('')
  let country = $state('')
  const catalogueCountries = [...new Set(catalogue.map(row => row.country).filter(Boolean))].sort()
  const catalogueByName = [...catalogue].sort((a, b) => a.name.localeCompare(b.name))
  let filteredCatalogue = $derived(catalogueByName.filter(row =>
    (!country || row.country === country) &&
    [row.name, row.location, row.country].some(value =>
      value.toLowerCase().includes(query.trim().toLowerCase())
    )
  ))
  const precisionLabels = {
    town: 'Listed town', region: 'Regional capital', country: 'National capital',
  }
  let catalogueMarkers = $derived(Object.values(Object.groupBy(
    filteredCatalogue.filter(row => row.lat !== null && row.lon !== null),
    row => `${row.lat},${row.lon}`
  )))
  let rows = $derived(editions.filter(row => row.year === year))
  let mapped = $derived(rows.filter(row =>
    row.lat !== null && row.lon !== null && row.status !== 'cancelled' && row.status !== 'virtual'
  ))
  let countries = $derived(new Set(rows.filter(row => row.country).map(row => row.country)).size)

  $effect(() => {
    if (!playing) return
    const timer = window.setInterval(() => {
      if (year >= end) playing = false
      else year += 1
    }, 650)
    return () => window.clearInterval(timer)
  })

  function togglePlayback() {
    if (!playing && year === end) year = start
    playing = !playing
  }
</script>

<main>
  <header>
    <p class="kicker">Historical atlas</p>
    <h1>Burning Seeds<span>.</span></h1>
    <p class="intro">Trace Burning Man and regional burns through documented editions, from the first gathering at Baker Beach onward.</p>
  </header>

  <nav aria-label="Atlas views">
    <button aria-pressed={!showCatalogue} onclick={() => showCatalogue = false}>Timeline</button>
    <button aria-pressed={showCatalogue} onclick={() => { showCatalogue = true; playing = false }}>
      Global catalogue
    </button>
  </nav>

  {#if showCatalogue}
    <section class="records" aria-labelledby="catalogue-title">
      <div class="records-head">
        <h2 id="catalogue-title">2019 global catalogue</h2>
        <p>Sizes are estimates from the original catalogue. Edition status is unverified.</p>
      </div>
      <div class="filters">
        <label>Search burns <input type="search" placeholder="Name or location" bind:value={query} /></label>
        <label>Country or listing region
          <select bind:value={country}>
            <option value="">All locations</option>
            {#each catalogueCountries as place}<option value={place}>{place}</option>{/each}
          </select>
        </label>
      </div>
      <p class="result-count" aria-live="polite">{filteredCatalogue.length} of {catalogue.length} listings</p>
      <figure class="catalogue-map">
        <div class="map">
          <svg viewBox="0 0 900 365" role="img" aria-label="Approximate locations of filtered catalogue listings">
            {#each land as outline}
              <path class="land" d={outline} fill-rule="evenodd" />
            {/each}
            {#each catalogueMarkers as group}
              {@const [x, y] = project([group[0].lon, group[0].lat])}
              <circle cx={x} cy={y} r={3 + Math.sqrt(group.length) * 1.8}
                fill="#ff9a59" fill-opacity=".8" stroke="#ffe0b6">
                <title>{group[0].map_reference} · {group.map(row => row.name).join(', ')}</title>
              </circle>
            {/each}
          </svg>
        </div>
        <figcaption>Approximate locations. Larger markers represent multiple listings at the same reference point. Map data by <a href="https://www.naturalearthdata.com/">Natural Earth</a>.</figcaption>
      </figure>
      {#each filteredCatalogue as row (row.event_id)}
        <article>
          <div>
            <h3>{row.name}</h3>
            <p>{row.location || row.country || 'Location unknown'}</p>
            {#if row.location_precision}
              <p>{precisionLabels[row.location_precision]} on map · {row.map_reference}</p>
            {/if}
          </div>
          <div class="measure">
            <strong>{row.population === null ? 'Unknown' : format.format(row.population)}</strong>
            <span>Catalogue size</span>
          </div>
          <a href={row.source_url} target="_blank" rel="noreferrer" aria-label={'Catalogue source for ' + row.name}>Source</a>
        </article>
      {:else}
        <p class="empty">No burns match these filters.</p>
      {/each}
    </section>
  {:else}
  <section class="atlas" aria-label="Edition map and timeline">
    <div class="map-head">
      <div>
        <p class="kicker">Selected year</p>
        <h2>{year}</h2>
      </div>
      <div class="stats">
        <span><strong>{rows.length}</strong> records</span>
        <span><strong>{countries}</strong> countries</span>
        <span><strong>{mapped.length}</strong> mapped</span>
      </div>
    </div>
    <div class="map">
      <svg viewBox="0 0 900 365" role="img" aria-label="World map of editions with known locations">
        <defs>
          <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="5" />
          </filter>
        </defs>
        {#each [-120, -60, 0, 60, 120] as lon}
          <path class="gridline" d="M{project([lon, 0])[0]} 0v365" />
        {/each}
        {#each [-45, 0, 45] as lat}
          <path class="gridline" d="M0 {project([0, lat])[1]}h900" />
        {/each}
        {#each land as outline}
          <path class="land" d={outline} fill-rule="evenodd" />
        {/each}
        {#each mapped as row}
          {@const [x, y] = project([row.lon, row.lat])}
          {@const radius = row.population === null ? 3 : Math.min(15, 3 + Math.sqrt(row.population) / 23)}
          <g>
            <title>{row.name} · {row.location}</title>
            <circle cx={x} cy={y} r={radius + 3} fill="#fb6b2d" filter="url(#glow)" opacity=".75" />
            <circle cx={x} cy={y} r={radius} fill="#ff9a59" stroke="#ffe0b6" stroke-width="1" />
          </g>
        {/each}
      </svg>
      {#if !mapped.length}<p class="map-note">No mapped editions for {year}</p>{/if}
    </div>
    <div class="timeline">
      <button onclick={togglePlayback}>{playing ? 'Pause' : 'Play timeline'}</button>
      <div class="scrubber">
        <input aria-label="Timeline year" type="range" min={start} max={end} bind:value={year} oninput={() => playing = false} />
        <div class="ticks"><span>{years[0]}</span><span>{years.at(-1)}</span></div>
      </div>
    </div>
  </section>

  <section class="records" aria-labelledby="records-title">
    <div class="records-head">
      <h2 id="records-title">Edition records</h2>
      <p>Reported figures retain their original metric.</p>
    </div>
    {#each rows as row}
      <article>
        <div>
          <h3>{row.name}</h3>
          <p>{row.location || row.country || 'Location unknown'}</p>
        </div>
        <div class="measure">
          <strong>{row.conflicting_populations.length ? row.conflicting_populations.map(value => format.format(value)).join(' / ') : row.population === null ? statuses[row.status] || 'Unknown' : format.format(row.population)}</strong>
          <span>{row.conflicting_populations.length ? 'Conflicting reports' : row.population === null
            ? (row.status === 'cancelled' ? 'Physical edition' : 'Population unknown')
            : metrics[row.population_metric] || row.population_metric.replaceAll('_', ' ')}</span>
        </div>
        <div class="sources">
          {#if row.source_url}<a href={row.source_url} target="_blank" rel="noreferrer" aria-label={'Edition source for ' + row.name}>Edition source</a>{/if}
          {#if row.location_source}<a href={row.location_source} target="_blank" rel="noreferrer" aria-label={'Location source for ' + row.name}>Location source</a>{/if}
        </div>
      </article>
    {:else}
      <p class="empty">No edition records for {year} in this dataset.</p>
    {/each}
  </section>
  <footer>Map geometry by <a href="https://www.naturalearthdata.com/">Natural Earth</a>. Marker size represents the reported figure.</footer>
  {/if}
</main>

<style>
  :global(*) { box-sizing: border-box; }
  :global(body) { margin: 0; background: #15110f; color: #f4ede4; font-family: system-ui, sans-serif; }
  main { max-width: 1160px; margin: auto; padding: clamp(1rem, 4vw, 3rem); }
  header { padding: 1rem 0 2rem; }
  .kicker { margin: 0; color: #ffa574; font-size: .875rem; letter-spacing: .15em; text-transform: uppercase; font-weight: 700; }
  h1, h2, h3, p { margin: 0; }
  h1 { font: 700 clamp(3.5rem, 9vw, 7rem)/1 Georgia, serif; letter-spacing: -.07em; margin: .2em 0 .14em; }
  h1 span { color: #ff8f58; }
  .intro { color: #d2c2b5; max-width: 39rem; line-height: 1.55; }
  .atlas { background: #211a17; border: 1px solid #50372c; border-radius: 1rem; overflow: hidden; }
  .map-head, .timeline, .records-head { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1rem 1.25rem; }
  .map-head h2 { font: 700 3rem Georgia, serif; }
  .stats { display: flex; flex-wrap: wrap; gap: .5rem 1rem; color: #d2c2b5; font-size: .875rem; }
  strong { color: #fff0e1; }
  .map { position: relative; background: radial-gradient(ellipse, #30221d, #191513); }
  svg { display: block; width: 100%; }
  .gridline { stroke: #4a382e; stroke-width: .65; }
  .land { fill: #49372d; stroke: #775b49; stroke-width: .55; }
  .map-note { position: absolute; bottom: .55rem; left: .75rem; padding: .3rem .55rem; background: #211a17; border-radius: .35rem; color: #dfc9b7; font-size: .875rem; }
  .scrubber { flex: 1; min-width: 0; }
  .ticks { display: flex; justify-content: space-between; color: #d2c2b5; font-size: .875rem; }
  input { width: 100%; margin: 0; height: 2rem; accent-color: #ff945d; }
  button { background: #ffa574; color: #21130c; min-height: 44px; padding: .5rem 1rem; border: 0; border-radius: .45rem; font: inherit; font-weight: 700; cursor: pointer; }
  nav { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1rem; }
  nav button[aria-pressed="false"] { background: #30241e; color: #f4ede4; }
  .filters { display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem; }
  .filters label { display: grid; flex: 1 1 14rem; gap: .35rem; }
  .filters input, .filters select { width: 100%; min-height: 44px; padding: .5rem .65rem; border: 1px solid #775b49; border-radius: .45rem; background: #211a17; color: inherit; font: inherit; }
  .result-count { margin-bottom: .75rem; color: #d2c2b5; }
  .catalogue-map { margin: 0 0 1rem; }
  .catalogue-map .map { border: 1px solid #50372c; border-radius: .75rem; overflow: hidden; }
  figcaption { color: #d2c2b5; font-size: .875rem; padding: .65rem 0; }
  .records { margin-top: 1.75rem; }
  .records-head { padding-inline: 0; flex-wrap: wrap; }
  .records-head p, article p, .measure span, footer { color: #d2c2b5; font-size: .875rem; }
  article { display: grid; grid-template-columns: minmax(0, 1fr) minmax(7rem, .5fr) auto; align-items: center; gap: .75rem; padding: .85rem 0; border-top: 1px solid #50372c; }
  article p, .measure span { margin-top: .2rem; display: block; }
  .sources { display: flex; flex-direction: column; }
  article a { display: flex; align-items: center; min-height: 44px; font-size: .875rem; }
  a { color: #ffa574; }
  footer { margin-top: 2rem; }
  .empty { padding: .75rem 0; }
  :global(:focus-visible) { outline: 2px solid #ffce9c; outline-offset: 3px; }
  @media (max-width: 480px) {
    .map-head { align-items: flex-start; flex-direction: column; }
    .map-head, .timeline { padding-inline: .75rem; }
  }
</style>
