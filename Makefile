# Burning Seeds — data pipeline tests and the atlas, deployed as static assets on Cloudflare Workers.
#
#   make check     Python + atlas tests and a production build — must pass before deploying
#   make preview   build, then serve viz/dist/ through wrangler, as Cloudflare will
#   make staging   noindex build, uploaded as a preview version aliased to the git branch
#   make deploy    check, then deploy to https://burningseeds.wetwarecraft.com

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Preview aliases must be lowercase DNS labels: feature/Map_Details → feature-map-details
BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null)
ALIAS ?= $(shell printf '%s' "$(BRANCH)" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$$//g' | cut -c1-40)
VIZ := pnpm --dir viz

.PHONY: help install test build check preview staging deploy

help:
	@sed -n '3,6p' $(firstword $(MAKEFILE_LIST)) | sed 's/^# \{0,1\}//'

install:
	$(VIZ) install --frozen-lockfile

test:
	uv run --locked python -m unittest discover -s tests
	$(VIZ) test

build:
	$(VIZ) build

check: test build

preview: build
	$(VIZ) exec wrangler dev

staging:
	@test -n "$(ALIAS)" || { echo "No git branch to name the preview after; run: make staging ALIAS=name" >&2; exit 1; }
	@test "$(ALIAS)" != "main" || { echo "On main: use 'make deploy', or pass ALIAS=something-else" >&2; exit 1; }
	$(MAKE) test
	NOINDEX=true $(VIZ) build
	@grep -q 'noindex' viz/dist/index.html || { echo 'staging build is indexable; refusing to upload' >&2; exit 1; }
	$(VIZ) exec wrangler versions upload --preview-alias "$(ALIAS)" --message "staging: $(BRANCH)"

deploy: check
	@test "$(BRANCH)" = "main" || { echo "Deploying from '$(BRANCH)', not main. Ctrl-C to abort, Enter to continue." >&2; read; }
	$(VIZ) exec wrangler deploy
