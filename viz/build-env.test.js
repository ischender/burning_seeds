import { test } from 'node:test'
import assert from 'node:assert/strict'
import { noindex, robotsMeta } from './build-env.js'

test('production builds are indexable', () => {
  assert.equal(noindex({}), false)
  assert.equal(noindex({ WORKERS_CI_BRANCH: 'main' }), false)
})

test('explicit staging builds and preview branches are never indexed', () => {
  assert.equal(noindex({ NOINDEX: 'true' }), true)
  assert.equal(noindex({ WORKERS_CI_BRANCH: 'feature/map-details' }), true)
})

test('the plugin adds the robots tag only to noindex builds', () => {
  const html = '<head><title>x</title></head>'
  assert.equal(robotsMeta(false).transformIndexHtml(html), html)
  assert.match(robotsMeta(true).transformIndexHtml(html), /<meta name="robots" content="noindex, nofollow" \/>\s*<\/head>/)
})
