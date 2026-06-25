---
name: repo-onboarding
description: >-
  Produce a "start here" onboarding guide for an unfamiliar repository: an
  architecture map, how to build/run/test it, the key entry points, and the
  first files a newcomer should read. Use when the user opens a repo they don't
  know and asks things like "explain this codebase", "how is this project laid
  out", "where do I start", "give me an architecture overview", "onboard me to
  this repo", or "what does this do and how do I run it". Read-only — it never
  modifies the repository.
---

# Repo Onboarding

Turn an unfamiliar repository into a concise onboarding guide. You are read-only:
inspect and explain, never modify, stage, or commit anything.

## When to use

Fire this skill when someone needs to get oriented in a codebase they don't yet
understand — a new hire, an OSS contributor, or anyone inheriting a project.
Typical asks: "explain this repo", "where do I start", "how do I run this",
"give me an architecture overview".

## Procedure

1. **Gather objective signals first.** Run the bundled scanner from the repo root:

   ```bash
   python "$CLAUDE_SKILL_DIR/scripts/repo_scan.py" .
   ```

   It prints JSON: detected languages, package manifests, `package.json` scripts,
   entry points, config files, test directories, CI workflows, and docs. This is
   ground truth about *what exists* — base your guide on it, not on assumptions.
   (If `python` is missing, use `python3`; if neither runs, fall back to listing
   the tree and key manifests yourself.)

2. **Read the high-signal files** the scan surfaced — in priority order:
   - the root `README.md` and anything under `docs/`,
   - each package manifest (`package.json`, `pyproject.toml`, `go.mod`, etc.) for
     dependencies and run/build commands,
   - the entry points (`main.*`, `index.*`, `app.py`, `server.*`, …),
   - one or two representative source files from the largest language to learn
     the project's conventions.
   Read enough to be accurate; don't read the whole repo.

3. **Map the architecture.** Identify the major components/layers and how they
   relate (e.g. CLI → service → data layer, or frontend ↔ API ↔ DB). Note the
   directory that owns each responsibility.

4. **Derive the real commands.** Pull install/build/run/test commands from the
   manifests and scripts the scan found — do not invent them. If a command is
   ambiguous, say so rather than guessing.

## Output

Produce a single Markdown guide with these sections (omit any that don't apply):

- **What it is** — one-paragraph summary of the project's purpose.
- **Tech stack** — languages, frameworks, package managers, notable services.
- **Architecture map** — the major components and how they fit together. A small
  ASCII/Mermaid diagram is welcome when it clarifies things.
- **How to run it** — install, build, run, and test commands, verbatim from the
  manifests/scripts (flag anything you inferred).
- **Start here** — an ordered reading list of 5–10 files with a one-line reason
  for each, so a newcomer knows exactly where to begin.
- **Gotchas** — required env vars, external services, setup steps, or anything
  surprising you noticed.

## Rules

- **Read-only.** Never edit, create, stage, or commit files. Running the scanner
  and reading files is the full scope.
- **Evidence over assumption.** Every command and claim should trace back to a
  file you actually read; mark inferences as inferences.
- **Detect, don't hardcode.** Work for any language/stack the scan reports.
- **Be concise.** Aim for a guide someone can read in a few minutes, not an
  exhaustive file-by-file dump.
