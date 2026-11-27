// Build-time switches, resolved from the environment in vite.config.js.
//
// - NOINDEX=true marks the page noindex: `make staging`.
// - Workers Builds sets WORKERS_CI_BRANCH; any branch but main is a preview and
//   must never be indexed, whoever triggered it.

const PRODUCTION_BRANCH = 'main'

export function noindex(env) {
  const previewBranch = Boolean(env.WORKERS_CI_BRANCH) && env.WORKERS_CI_BRANCH !== PRODUCTION_BRANCH
  return env.NOINDEX === 'true' || previewBranch
}

export function robotsMeta(enabled) {
  return {
    name: 'robots-meta',
    transformIndexHtml: html =>
      enabled ? html.replace('</head>', '  <meta name="robots" content="noindex, nofollow" />\n  </head>') : html,
  }
}
