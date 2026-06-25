# repo-onboarding

Drop into an unfamiliar repo and get a concise **"start here"** guide: what the
project is, the architecture, how to build/run/test it, and the exact files to
read first. Read-only — it never modifies the repository.

## What it does

1. Runs a bundled scanner (`scripts/repo_scan.py`) that collects objective
   signals — languages, package manifests, run/build scripts, entry points,
   config, tests, CI, and docs.
2. Reads the high-signal files those signals point to.
3. Synthesizes a short architecture map + onboarding guide grounded in what
   actually exists in the repo (no invented commands).

## Before / after

**Before** — you clone a repo and stare at a wall of folders:

```
$ ls
api/  cmd/  internal/  pkg/  web/  migrations/  Makefile  go.mod  docker-compose.yml
# ...where do I even start? how do I run it?
```

**After** — you ask Claude to onboard you and get:

```markdown
## What it is
A Go HTTP API for short-link management, with a React frontend in `web/`.

## Tech stack
Go 1.22 (chi router, sqlc), Postgres, React + Vite. Orchestrated via docker-compose.

## Architecture map
  cmd/server ──> internal/handlers ──> internal/store ──> Postgres
                         │
                      pkg/auth (JWT middleware)
  web/ (React SPA) ──> /api/* on the Go server

## How to run it
  docker compose up -d        # Postgres + server (from docker-compose.yml)
  make migrate                # apply migrations/ (Makefile: `migrate` target)
  cd web && npm install && npm run dev   # frontend (web/package.json)

## Start here
1. cmd/server/main.go       — wiring: router, DB, middleware
2. internal/handlers/links.go — core request handlers
3. internal/store/store.go    — DB access layer (sqlc-generated callers)
4. pkg/auth/jwt.go            — how auth works
5. migrations/0001_init.sql   — the data model

## Gotchas
- Needs DATABASE_URL and JWT_SECRET (see .env.example).
- `make migrate` must run before the server will start cleanly.
```

## Triggers

"explain this codebase", "where do I start", "how do I run this", "give me an
architecture overview", "onboard me to this repo".

## Install

**As a project skill** — copy this folder into your repo:

```bash
cp -r skills/repo-onboarding .claude/skills/repo-onboarding
```

**As a global skill** — make it available everywhere:

```bash
cp -r skills/repo-onboarding ~/.claude/skills/repo-onboarding
```

The helper script needs Python 3 (standard library only — no dependencies).
