import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

// wrangler.jsonc allows whole-line comments only, so stripping them yields plain JSON.
const config = JSON.parse(
  readFileSync(new URL('./wrangler.jsonc', import.meta.url), 'utf8').replace(/^\s*\/\/.*$/gm, ''),
)

test('production serves the built atlas on its own subdomain', () => {
  assert.equal(config.assets.directory, './dist')
  assert.equal(config.main, undefined)
  assert.deepEqual(config.routes, [{ pattern: 'burningseeds.wetwarecraft.com', custom_domain: true }])
})

test('every uploaded version gets a workers.dev preview URL', () => {
  assert.equal(config.workers_dev, true)
  assert.equal(config.preview_urls, true)
})
