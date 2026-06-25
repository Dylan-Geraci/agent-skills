---
name: env-doctor
description: >-
  Diagnose why a project won't run on this machine and suggest the fixes.
  Checks for missing/outdated tools, uninstalled dependencies, environment
  variables declared in an example file but absent locally, and ports a config
  wants that are already in use. Use when the user just cloned or set up a repo
  and asks "why won't this run", "it won't start", "setup isn't working",
  "what do I need to install", "why is it failing on startup", or "help me get
  this running". Read-only — it diagnoses and recommends commands, but never
  installs, edits, or starts anything itself.
---

# Env Doctor

Figure out why a project won't run locally, then hand the user the exact commands
to fix it. You diagnose and recommend; you do not install, modify, or start
anything — the user runs the fixes.

## When to use

Fire this when someone is stuck getting a project to run: a fresh clone that
won't start, a failing setup, "what do I need to install", or a confusing
startup error.

## Procedure

1. **Run the diagnostic** from the repo root:

   ```bash
   python "$CLAUDE_SKILL_DIR/scripts/env_check.py" .
   ```

   It prints JSON with a `summary` (error/warn/ok counts) and a `findings` list.
   Each finding has a `check` type (`tool`, `dependencies`, `env_vars`, `port`),
   an `ok` flag, a `severity`, a human `detail`, and sometimes a `suggest`
   command. (Use `python3` if `python` isn't found.)

2. **If the user pasted an error**, line it up with the findings — a
   `ModuleNotFoundError` matches a missing `dependencies` finding, an
   `EADDRINUSE` matches a busy `port`, a missing-key crash matches `env_vars`.

3. **Read the manifest** when you need exact commands the scanner can't infer —
   e.g. open `package.json` to pick the right script (`npm run dev` vs `start`),
   or `pyproject.toml` for the right install command (pip vs poetry vs uv).

## Output

Lead with a one-line verdict (e.g. "3 issues blocking startup, all fixable").
Then list each problem worth acting on as:

- **What's wrong** — plain-language statement of the finding.
- **Fix** — the exact command(s) to run, in a copyable code block.

Order by severity: `error` first (hard blockers), then `warn`. Skip `ok`
findings unless the user asked for a full report. If nothing is wrong, say so
and point them at the actual run command from the manifest.

## Rules

- **Read-only.** Never run installers, edit files (including `.env`), or start
  servers. You output commands; the user decides whether to run them.
- **Never print secret values.** Report env-var *names* that are missing, never
  the contents of any `.env` file.
- **Evidence-based.** Base findings on the scanner output and files you read,
  not assumptions. If a fix is a guess, say so.
- **Detect, don't hardcode.** Work for whatever stack the scanner reports.
