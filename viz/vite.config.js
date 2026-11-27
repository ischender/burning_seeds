import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { noindex, robotsMeta } from './build-env.js'

export default defineConfig({ plugins: [svelte(), robotsMeta(noindex(process.env))] })
