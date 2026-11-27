// Pure helpers behind the event detail panel; kept out of App.svelte so node --test can cover them.

export function eventHistory(editions, eventId) {
  return editions.filter(row => row.event_id === eventId).sort((a, b) => a.year - b.year)
}

// A counted figure outranks any estimate: a catalogue guess must not read as the event's peak.
function largest(rows) {
  return rows.reduce((best, row) => (best === null || row.population > best.population ? row : best), null)
}

export function eventSummary(history) {
  const figures = history.filter(row => row.population !== null)
  const held = history.filter(row => row.status === 'held')
  return {
    firstYear: history[0]?.year ?? null,
    lastYear: history.at(-1)?.year ?? null,
    held: held.length,
    latestHeld: held.at(-1)?.year ?? null,
    peak: largest(figures.filter(row => !row.population_estimate)) ?? largest(figures),
  }
}
