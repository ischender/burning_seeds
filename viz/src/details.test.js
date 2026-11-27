import { test } from 'node:test'
import assert from 'node:assert/strict'
import { eventHistory, eventSummary } from './details.js'

const edition = (year, status, population = null, estimate = false) =>
  ({ event_id: 'a', year, status, population, population_estimate: estimate })

test('history lists one event by year', () => {
  const rows = [edition(2022, 'held'), { ...edition(2020, 'held'), event_id: 'b' }, edition(2019, 'held')]
  assert.deepEqual(eventHistory(rows, 'a').map(row => row.year), [2019, 2022])
})

test('summary spans documented years and prefers counted peaks over estimates', () => {
  const summary = eventSummary([
    edition(2015, 'held', 100), edition(2016, 'held', 900, true),
    edition(2017, 'held', 400), edition(2020, 'cancelled'), edition(2027, 'scheduled_or_unverified'),
  ])
  assert.equal(summary.firstYear, 2015)
  assert.equal(summary.lastYear, 2027)
  assert.equal(summary.held, 3)
  assert.deepEqual([summary.peak.year, summary.peak.population], [2017, 400])
  assert.equal(summary.latestHeld, 2017)
})

test('summary falls back to the largest estimate, and to nothing', () => {
  assert.equal(eventSummary([edition(2019, 'held', 300, true)]).peak.population, 300)
  const empty = eventSummary([edition(2019, 'unknown')])
  assert.equal(empty.peak, null)
  assert.equal(empty.latestHeld, null)
})
