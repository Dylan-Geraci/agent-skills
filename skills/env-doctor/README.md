# env-doctor

"Why won't this run?" — diagnose a freshly cloned or misbehaving project and get
the exact commands to fix it. Read-only: it reports and recommends, but never
installs, edits, or starts anything itself.

## What it checks

- **Tools** — are the required runtimes/package managers on `PATH`, and what
  versions (node, python, go, docker, java, …, inferred from the manifests).
- **Dependencies** — is the project actually installed (`node_modules`,
  a Python virtualenv)?
- **Env vars** — does `.env` exist, and is it missing any keys declared in
  `.env.example` / `.env.sample`? (Reports key *names* only — never values.)
- **Ports** — are the ports a `docker-compose` file wants already in use?

The bundled `scripts/env_check.py` (Python 3, stdlib only) gathers these signals;
the skill turns them into a prioritized, copy-pasteable fix list.

## Before / after

**Before** — a fresh clone explodes on startup and you're guessing:

```
$ npm run dev
Error: Cannot find module 'vite'
# ...is node too old? did install fail? is something else wrong too?
```

**After** — you ask Claude why it won't run and get:

```markdown
**3 issues blocking startup — all fixable.**

1. Dependencies not installed (no node_modules).
   npm install

2. .env is missing 2 keys from .env.example: JWT_SECRET, PORT.
   cp .env.example .env   # then fill in JWT_SECRET and PORT

3. Port 5432 is already in use (docker-compose wants it for Postgres).
   Stop whatever's on 5432, or change the host port mapping in docker-compose.yml.

Once those are done: `npm run dev` (from package.json scripts).
```

## Triggers

"why won't this run", "it won't start", "setup isn't working", "what do I need
to install", "why is it failing on startup", "help me get this running".

## Install

**As a project skill:**

```bash
cp -r skills/env-doctor .claude/skills/env-doctor
```

**As a global skill:**

```bash
cp -r skills/env-doctor ~/.claude/skills/env-doctor
```

Requires Python 3 (standard library only — no dependencies).
