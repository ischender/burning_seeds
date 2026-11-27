<script>
  import editions from './editions.json'
  import catalogue from './catalogue.json'
  import landSource from './land.geojson?raw'
  import { tick } from 'svelte'
  import { eventHistory, eventSummary } from './details.js'

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
    catalogue_size_snapshot: '2019 catalogue size',
  }
  const statuses = {
    held: 'Held', cancelled: 'Cancelled', precursor_held: 'Precursor',
    pilot_burn: 'Pilot burn', virtual: 'Virtual', scheduled_or_unverified: 'Planned or unconfirmed',
    unknown: 'Status unknown',
  }
  // Symbolic halo radii: at world scale even country-level error is a few pixels,
  // so the halo encodes the precision class rather than distance.
  // Planned or undocumented editions stay on the map but must not read as held.
  const unverified = new Set(['scheduled_or_unverified', 'unknown'])
  const uncertainty = { site: 0, area: 0, town: 5, region: 9, country: 14, '': 5 }
  const precisionText = {
    site: 'Venue location', area: 'Approximate venue area', town: 'Nearest town',
    region: 'Region only', country: 'Country only', '': 'Approximate location',
  }
  const officialStatuses = {
    origin: 'Origin event', official_regional: 'Official Burning Man regional',
    official_regional_in_2019_catalogue: 'Official regional (2019 catalogue)',
    not_official_in_2019_catalogue: 'Not an official regional (2019 catalogue)',
    period_specific: 'Official status varied over time',
  }
  const confidenceText = { high: 'High confidence', medium: 'Medium confidence', low: 'Low confidence' }
  const eventNames = Object.fromEntries([...catalogue, ...editions].map(row => [row.event_id, row.name]))
  const dayFormat = new Intl.DateTimeFormat('en', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
  const monthFormat = new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric', timeZone: 'UTC' })

  function formatDates({ start_date: start, end_date: end }) {
    if (!start) return ''
    const format = value => value.length === 7
      ? monthFormat.format(new Date(value + '-01')) + ' (approx.)'
      : dayFormat.format(new Date(value))
    if (start.length === 10 && end?.length === 10 && start !== end) {
      return dayFormat.formatRange(new Date(start), new Date(end))
    }
    return format(start)
  }

  function formatFigure(row) {
    return (row.population_estimate ? '≈ ' : '') + format.format(row.population)
  }

  function formatRecordFigure(row) {
    if (row.conflicting_populations.length) return row.conflicting_populations.map(value => format.format(value)).join(' / ')
    return row.population === null ? '—' : formatFigure(row)
  }

  function markerRadius(row) {
    return row.population === null ? 3 : Math.min(15, 3 + Math.sqrt(row.population) / 23)
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
  // Large markers first, so smaller ones drawn on top stay clickable.
  let drawOrder = $derived([...mapped].sort((a, b) => markerRadius(b) - markerRadius(a)))
  let selectedEvent = $state(null)
  let selectedListings = $state([])
  let panel = $state()
  let opener = null
  let selectedHistory = $derived(selectedEvent ? eventHistory(editions, selectedEvent) : [])
  let selectedEdition = $derived(rows.find(row => row.event_id === selectedEvent))
  let listingDetails = $derived(catalogue.filter(row => selectedListings.includes(row.event_id)))
  let countries = $derived(new Set(rows.filter(row => row.country).map(row => row.country)).size)

  $effect(() => {
    if (!playing) return
    const timer = window.setInterval(() => {
      if (year >= end) playing = false
      else year += 1
    }, 650)
    return () => window.clearInterval(timer)
  })

  // The panel is not modal: focus moves to it so keyboard and screen-reader users land on the
  // details, and closing returns focus (and the scroll position) to whatever opened it.
  async function openDetails(update) {
    opener = document.activeElement
    update()
    await tick()
    panel?.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
    panel?.focus({ preventScroll: true })
  }

  function closeDetails() {
    selectedEvent = null
    selectedListings = []
    opener?.focus()
    opener = null
  }

  function activateOnKey(event, action) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      action()
    }
  }

  function closeOnEscape(event) {
    if (event.key === 'Escape' && (selectedEvent || selectedListings.length)) closeDetails()
  }

  function showInTimeline(eventId) {
    const summary = eventSummary(eventHistory(editions, eventId))
    showCatalogue = false
    selectedListings = []
    openDetails(() => {
      selectedEvent = eventId
      year = summary.latestHeld ?? summary.lastYear
    })
  }

  function switchView(catalogueView) {
    showCatalogue = catalogueView
    playing = false
    selectedEvent = null
    selectedListings = []
  }

  function togglePlayback() {
    if (!playing && year === end) year = start
    playing = !playing
  }
</script>

<svelte:window onkeydown={closeOnEscape} />

<main>
  <header>
    <p class="kicker">Historical atlas</p>
    <h1>Burning Seeds<span>.</span></h1>
    <p class="intro">Trace Burning Man and regional burns through documented editions, from the first gathering at Baker Beach onward.</p>
  </header>

  <nav aria-label="Atlas views">
    <button aria-pressed={!showCatalogue} onclick={() => switchView(false)}>Timeline</button>
    <button aria-pressed={showCatalogue} onclick={() => switchView(true)}>
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
              {@const radius = 3 + Math.sqrt(group.length) * 1.8}
              {@const label = group.map(row => row.name).join(', ')}
              <g class="marker" class:selected={group.some(row => selectedListings.includes(row.event_id))}
                role="button" tabindex="0" aria-label={'Details: ' + label}
                onclick={() => openDetails(() => selectedListings = group.map(row => row.event_id))}
                onkeydown={event => activateOnKey(event, () => openDetails(() => selectedListings = group.map(row => row.event_id)))}>
                <title>{group[0].map_reference} · {label}</title>
                <circle class="ring" cx={x} cy={y} r={radius + 4} />
                {#if uncertainty[group[0].location_precision]}
                  <circle class="halo" cx={x} cy={y} r={radius + uncertainty[group[0].location_precision]} />
                {/if}
                <circle cx={x} cy={y} r={radius} fill="#ff9a59" fill-opacity=".8" stroke="#ffe0b6" />
                <circle class="hit" cx={x} cy={y} r={Math.max(radius + 3, 9)} />
              </g>
            {/each}
          </svg>
        </div>
        <figcaption>Select a marker for its listings. Dotted rings mark reference points less precise than the listed town; wider rings are less precise. Larger markers represent multiple listings at the same reference point. Map data by <a href="https://www.naturalearthdata.com/">Natural Earth</a>.</figcaption>
      </figure>
      {#if listingDetails.length}
        <section class="details" aria-labelledby="listing-title" tabindex="-1" bind:this={panel}>
          <div class="details-head">
            <div>
              <p class="kicker">{listingDetails[0].map_reference || 'Catalogue listing'}</p>
              <h2 id="listing-title">{listingDetails.length === 1 ? listingDetails[0].name : listingDetails.length + ' listings'}</h2>
            </div>
            <button class="secondary" onclick={closeDetails}>Close</button>
          </div>
          {#each listingDetails as row (row.event_id)}
            {@const summary = eventSummary(eventHistory(editions, row.event_id))}
            <div class="details-grid">
              <div>
                <h3>{listingDetails.length === 1 ? '2019 listing' : row.name}</h3>
                <dl>
                  <dt>Listed location</dt><dd>{row.location || row.country || 'Unknown'}</dd>
                  {#if formatDates(row)}<dt>Planned dates</dt><dd>{formatDates(row)}</dd>{/if}
                  <dt>Catalogue size</dt><dd>{row.population === null ? 'Unknown' : formatFigure(row)}</dd>
                  {#if row.location_precision}<dt>On the map</dt><dd>{precisionLabels[row.location_precision]} · {row.map_reference}</dd>{/if}
                </dl>
                <a href={row.source_url} target="_blank" rel="noreferrer">Catalogue source</a>
              </div>
              <div>
                <h3>About the event</h3>
                {@render about(row)}
                {#if summary.firstYear !== null}
                  <p>{summary.held} documented held {summary.held === 1 ? 'edition' : 'editions'}, {summary.firstYear}–{summary.lastYear}.</p>
                  <button class="secondary" onclick={() => showInTimeline(row.event_id)}>Show in timeline</button>
                {:else}
                  <p>No editions documented beyond this listing yet.</p>
                {/if}
              </div>
            </div>
          {/each}
        </section>
      {/if}
      {#each filteredCatalogue as row (row.event_id)}
        <article>
          <div>
            <h3><button class="name" onclick={() => openDetails(() => selectedListings = [row.event_id])}>{row.name}</button></h3>
            <p>{row.location || row.country || 'Location unknown'}</p>
            {#if formatDates(row)}<p>{formatDates(row)}</p>{/if}
            {#if row.location_precision}
              <p>{precisionLabels[row.location_precision]} on map · {row.map_reference}</p>
            {/if}
          </div>
          <div class="measure">
            <strong>{row.population === null ? 'Unknown' : formatFigure(row)}</strong>
            <span>Catalogue size estimate</span>
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
        {#each drawOrder as row (row.event_id)}
          {@const [x, y] = project([row.lon, row.lat])}
          {@const radius = markerRadius(row)}
          <g class="marker" class:selected={row.event_id === selectedEvent} role="button" tabindex="0"
            aria-label={'Details: ' + row.name + ', ' + year}
            onclick={() => openDetails(() => selectedEvent = row.event_id)}
            onkeydown={event => activateOnKey(event, () => openDetails(() => selectedEvent = row.event_id))}>
            <title>{row.name} · {row.location}{row.population === null ? '' : ' · ' + formatFigure(row)}</title>
            <circle class="ring" cx={x} cy={y} r={radius + 4} />
            {#if uncertainty[row.location_precision]}
              <circle class="halo" cx={x} cy={y} r={radius + uncertainty[row.location_precision]} />
            {/if}
            {#if unverified.has(row.status)}
              <circle class="unverified" cx={x} cy={y} r={radius} />
            {:else if row.population_estimate}
              <circle class="estimate" cx={x} cy={y} r={radius} />
            {:else}
              <circle cx={x} cy={y} r={radius + 3} fill="#fb6b2d" filter="url(#glow)" opacity=".75" />
              <circle cx={x} cy={y} r={radius} fill="#ff9a59" stroke="#ffe0b6" stroke-width="1" />
            {/if}
            <circle class="hit" cx={x} cy={y} r={Math.max(radius + 3, 9)} />
          </g>
        {/each}
      </svg>
      {#if !mapped.length}<p class="map-note">No mapped editions for {year}</p>{/if}
    </div>
    <ul class="legend" aria-label="Map legend">
      <li><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="6" fill="#ff9a59" stroke="#ffe0b6" /></svg>Counted figure</li>
      <li><svg viewBox="0 0 24 24" aria-hidden="true"><circle class="estimate" cx="12" cy="12" r="6" /></svg>Estimated figure</li>
      <li><svg viewBox="0 0 24 24" aria-hidden="true"><circle class="unverified" cx="12" cy="12" r="6" /></svg>Planned or unconfirmed edition</li>
      <li><svg viewBox="0 0 24 24" aria-hidden="true"><circle class="halo" cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="4" fill="#ff9a59" /></svg>Approximate location (wider ring, less precise)</li>
    </ul>
    <div class="timeline">
      <button onclick={togglePlayback}>{playing ? 'Pause' : 'Play timeline'}</button>
      <div class="scrubber">
        <input aria-label="Timeline year" type="range" min={start} max={end} bind:value={year} oninput={() => playing = false} />
        <div class="ticks"><span>{years[0]}</span><span>{years.at(-1)}</span></div>
      </div>
    </div>
    {#if selectedEvent}
      {@const event = selectedHistory[0]}
      {@const summary = eventSummary(selectedHistory)}
      <section class="details timeline-details" aria-labelledby="details-title" tabindex="-1" bind:this={panel}>
        <div class="details-head">
          <div>
            <p class="kicker">{event.country || 'Country unknown'}</p>
            <h2 id="details-title">{event.name}</h2>
          </div>
          <button class="secondary" onclick={closeDetails}>Close</button>
        </div>
        <div class="details-grid">
          <div>
            <h3>{year} edition</h3>
            {#if selectedEdition}
              <dl>
                <dt>Status</dt><dd>{statuses[selectedEdition.status] || selectedEdition.status}</dd>
                {#if formatDates(selectedEdition)}<dt>Dates</dt><dd>{formatDates(selectedEdition)}</dd>{/if}
                <dt>Location</dt><dd>{selectedEdition.location || 'Unknown'}</dd>
                {#if selectedEdition.lat !== null}<dt>On the map</dt><dd>{precisionText[selectedEdition.location_precision]}</dd>{/if}
                <dt>Reported {selectedEdition.reported_figures.length === 1 ? 'figure' : 'figures'}</dt>
                <dd>
                  {#each selectedEdition.reported_figures as figure}
                    <span class="figure">
                      {figure.estimate ? '≈ ' : ''}{format.format(figure.population)} · {metrics[figure.metric] || figure.metric.replaceAll('_', ' ')}
                      {#if figure.confidence}<small>{confidenceText[figure.confidence] || figure.confidence}</small>{/if}
                      {#if figure.source_url}<a href={figure.source_url} target="_blank" rel="noreferrer">Source</a>{/if}
                    </span>
                  {:else}
                    {selectedEdition.status === 'cancelled' ? 'No physical edition' : 'Not reported'}
                  {/each}
                </dd>
              </dl>
              <div class="sources">
                {#if selectedEdition.source_url}<a href={selectedEdition.source_url} target="_blank" rel="noreferrer">Edition source</a>{/if}
                {#if selectedEdition.location_source}<a href={selectedEdition.location_source} target="_blank" rel="noreferrer">Location source</a>{/if}
              </div>
            {:else}
              <p>No record for {year}. Choose a year below.</p>
            {/if}
          </div>
          <div>
            <h3>About the event</h3>
            {@render about(event)}
            <dl>
              <dt>Documented</dt><dd>{summary.held} held {summary.held === 1 ? 'edition' : 'editions'}, {summary.firstYear}–{summary.lastYear}</dd>
              {#if summary.peak}
                <dt>Largest figure</dt>
                <dd>{formatFigure(summary.peak)} in {summary.peak.year} · {metrics[summary.peak.population_metric] || summary.peak.population_metric}</dd>
              {/if}
            </dl>
          </div>
        </div>
        <div class="history">
          <table>
            <caption>Every documented edition of {event.name}</caption>
            <thead><tr><th scope="col">Year</th><th scope="col">Status</th><th scope="col">Figure</th></tr></thead>
            <tbody>
              {#each selectedHistory as row (row.year)}
                <tr aria-current={row.year === year ? 'true' : undefined}>
                  <th scope="row"><button class="name" aria-label={'Show ' + row.year} onclick={() => { year = row.year; playing = false }}>{row.year}</button></th>
                  <td>{statuses[row.status] || row.status}</td>
                  <td>{formatRecordFigure(row)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </section>
    {/if}
  </section>

  <section class="records" aria-labelledby="records-title">
    <div class="records-head">
      <h2 id="records-title">Edition records</h2>
      <p>Reported figures retain their original metric.</p>
    </div>
    {#each rows as row}
      <article>
        <div>
          <h3><button class="name" onclick={() => openDetails(() => selectedEvent = row.event_id)}>{row.name}</button></h3>
          <p>{row.location || row.country || 'Location unknown'}</p>
          {#if formatDates(row)}<p>{formatDates(row)}</p>{/if}
          {#if row.lat !== null && row.location_precision !== 'site'}<p>{precisionText[row.location_precision]} on map</p>{/if}
          {#if unverified.has(row.status) && row.population !== null}<p>{statuses[row.status]}</p>{/if}
        </div>
        <div class="measure">
          <strong>{row.conflicting_populations.length ? row.conflicting_populations.map(value => format.format(value)).join(' / ') : row.population === null ? statuses[row.status] || 'Unknown' : formatFigure(row)}</strong>
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
  <footer>Select a marker or a name for the edition's sources and the event's history. Map geometry by <a href="https://www.naturalearthdata.com/">Natural Earth</a>. Marker size represents the reported figure; dashed markers are estimates.</footer>
  {/if}
</main>

{#snippet about(row)}
  <dl>
    {#if row.first_year}<dt>First burn</dt><dd>{row.first_year}</dd>{/if}
    {#if officialStatuses[row.official_status]}<dt>Official status</dt><dd>{officialStatuses[row.official_status]}</dd>{/if}
    {#if row.parent_event_id}
      <dt>Grew out of</dt>
      <dd>{#if eventNames[row.parent_event_id]}{eventNames[row.parent_event_id]}{:else}{row.parent_event_id}{/if}</dd>
    {/if}
  </dl>
  {#if row.event_notes}<p class="notes">{row.event_notes}</p>{/if}
{/snippet}

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
  .halo { fill: none; stroke: #ffe0b6; stroke-opacity: .55; stroke-width: 1; stroke-dasharray: 1.5 2; }
  .unverified { fill: none; stroke: #d2c2b5; stroke-opacity: .7; stroke-width: 1; }
  .estimate { fill: #ff9a59; fill-opacity: .28; stroke: #ffb27f; stroke-width: 1.2; stroke-dasharray: 2.5 1.8; }
  .legend { display: flex; flex-wrap: wrap; gap: .5rem 1.25rem; margin: 0; padding: .75rem 1.25rem 0; list-style: none; color: #d2c2b5; font-size: .875rem; }
  .legend li { display: flex; align-items: center; gap: .4rem; }
  .legend svg { width: 1.5rem; flex: none; }
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
  .marker { cursor: pointer; }
  .marker:focus-visible { outline: none; }
  .hit { fill: transparent; }
  .ring { display: none; fill: none; stroke: #fff0e1; stroke-width: 1.5; }
  .marker.selected .ring, .marker:focus-visible .ring, .marker:hover .ring { display: inline; }
  .marker:focus-visible .ring { stroke: #ffce9c; stroke-width: 2; }
  .details { margin: 0 1.25rem 1.25rem; padding: 1rem 1.25rem; background: #2a201c; border: 1px solid #775b49; border-radius: .75rem; }
  .catalogue-map + .details { margin: 0 0 1rem; }
  .details:focus { outline: none; }
  .details-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: .75rem; }
  .details-head h2 { font: 700 1.75rem Georgia, serif; }
  .details-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 1rem 2rem; padding: .75rem 0; border-top: 1px solid #50372c; }
  .details h3 { font-size: 1rem; margin-bottom: .5rem; }
  .details p { color: #d2c2b5; font-size: .875rem; line-height: 1.5; margin-bottom: .5rem; }
  dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: .35rem 1rem; margin: 0 0 .5rem; font-size: .875rem; }
  dt { color: #d2c2b5; }
  dd { margin: 0; overflow-wrap: anywhere; }
  .figure { display: flex; flex-wrap: wrap; align-items: center; gap: 0 .6rem; }
  .figure small { color: #d2c2b5; }
  .details a { display: inline-flex; align-items: center; min-height: 44px; font-size: .875rem; }
  .figure a { min-height: 32px; }
  button.secondary { background: #30241e; color: #f4ede4; border: 1px solid #775b49; }
  button.name { background: none; color: inherit; padding: 0; min-height: 0; font: inherit; font-weight: 700; text-align: left; text-decoration: underline dotted #ffa574; text-underline-offset: .2em; }
  h3 button.name { min-height: 44px; }
  .history { max-height: 18rem; overflow-y: auto; border-top: 1px solid #50372c; }
  table { width: 100%; border-collapse: collapse; font-size: .875rem; }
  caption { text-align: left; color: #d2c2b5; padding: .6rem 0; }
  th, td { text-align: left; padding: .15rem .5rem .15rem 0; border-bottom: 1px solid #3a2b24; }
  thead th { position: sticky; top: 0; background: #2a201c; color: #d2c2b5; font-weight: 600; }
  tbody th button.name { min-height: 32px; }
  tr[aria-current] { background: #3a2b24; }
  :global(:focus-visible) { outline: 2px solid #ffce9c; outline-offset: 3px; }
  @media (max-width: 480px) {
    .map-head { align-items: flex-start; flex-direction: column; }
    .map-head, .timeline { padding-inline: .75rem; }
    .details { margin-inline: .75rem; padding-inline: .75rem; }
    .catalogue-map + .details { margin-inline: 0; }
  }
</style>
