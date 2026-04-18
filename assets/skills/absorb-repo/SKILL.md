---
name: absorb-repo
description: Scan a git repository (or current directory) for markdown documentation and feed it to the agent-knowledge `/absorb` command in logical batches. Use when the user asks to absorb a whole repo, onboard an existing project into agent-knowledge, or pull all project `.md` files into Memory. Ignores vendor and build artefacts (node_modules, .git, .terraform/providers, dist, build, .next, .venv, target, vendor, __pycache__, .pytest_cache, .mypy_cache, coverage). Invokes `/absorb` once per top-level directory so classification and deduplication happen inside `/absorb`'s normal logic. Do NOT use to ingest a single file — use `/absorb <path>` directly.
allowed-tools: Bash
---

# absorb-repo

## Purpose

`/absorb` knows how to classify and route a single set of markdown files
into the agent-knowledge vault. This skill is the **discovery and
orchestration layer on top of it** — it walks a repository, filters out
vendor/build noise, and feeds `/absorb` one logical batch at a time.

The skill never classifies content itself. `/absorb` owns:
- Deciding which branch each file maps to
- Reconciling contradictions against existing Memory
- Splitting mixed-content files across branches
- Skipping boilerplate

## Prerequisites

- Target repo must already be initialised for agent-knowledge
  (`./agent-knowledge/` present). The `/absorb` slash command must also
  be installed — either `.claude/commands/absorb.md` (Claude Code) or
  `.cursor/commands/absorb.md` (Cursor).
- If `/absorb` is not available in the current project, stop and tell
  the user to run `agent-knowledge init` first.

## Instructions

### Step 1 — Identify target

- If the user passed a path as argument, use it as `TARGET`.
- Otherwise use the current working directory.
- Verify the path exists and is a directory. Reject single files — tell
  the user to call `/absorb <file>` directly for one-offs.

### Step 2 — Scan

Run a single Bash command to list every `.md` file under `TARGET`,
excluding vendor and build artefacts. Use this exact `find` invocation
(it handles the ignore list in one pass and is fast on large repos):

```bash
find "$TARGET" -type d \( \
  -name node_modules -o \
  -name .git -o \
  -name dist -o \
  -name build -o \
  -name .next -o \
  -name .venv -o \
  -name target -o \
  -name vendor -o \
  -name __pycache__ -o \
  -name .pytest_cache -o \
  -name .mypy_cache -o \
  -name coverage \
\) -prune -o \
-type d -path '*/.terraform/providers' -prune -o \
-type f -name '*.md' -print | sort
```

If the result is empty, stop and tell the user no markdown files were
found under the target.

### Step 3 — Group into logical batches

Group results by the **first path segment relative to `TARGET`**. Files
directly under `TARGET` form a single `root` batch.

Example, with `TARGET=/repo/VisageAI-main`:

| Batch name | Paths matched |
|---|---|
| `root` | `README.md`, `AGENTS.md`, `CLAUDE.md` |
| `docs` | everything under `docs/` |
| `backend` | everything under `backend/` |
| `frontend` | everything under `frontend/` |
| ... | |

Preserve natural batching even if a batch is large — do not split a
directory. `/absorb` handles per-batch volume internally.

### Step 4 — Announce the plan

Before invoking `/absorb`, show the user:
1. Target path.
2. Total file count.
3. The batch list with a count per batch.

Then proceed without waiting for confirmation — the user has already
asked to absorb the repo. If they want to abort, they will stop the
run.

### Step 5 — Invoke `/absorb` per batch

For each batch, invoke the `/absorb` slash command once with the
explicit file list as arguments, space-separated. Always pass absolute
paths so `/absorb` is robust to cwd changes.

Run batches **sequentially**, not in parallel. `/absorb` writes to
shared Memory files (`MEMORY.md`, `decisions.md`, `events.ndjson`) and
parallel writes would race.

Wait for each `/absorb` invocation to finish before starting the next
one. After each batch, briefly note what happened (branches
touched, decisions added, files skipped) so the user can follow along.

### Step 6 — Final summary

After all batches finish, run `agent-knowledge sync --project <TARGET>`
once (if `/absorb` has not already done so in the last batch — it
usually does), then print:

- Target path and total files discovered
- Batch count
- New or updated Memory branches across the whole run
- Any batches that produced no writes (e.g. all-boilerplate dirs)
- A reminder that `/absorb` already logged individual absorb events to
  `History/events.ndjson`

## Notes

- **No dedup against prior absorb runs.** The skill re-feeds every
  discovered file. `/absorb` is responsible for recognising unchanged
  facts and no-op'ing; if that is not happening, that is a `/absorb`
  bug, not something this skill should work around.
- **Do not edit the ignore list inline.** If a project needs a
  different exclusion set, tell the user to invoke `/absorb` directly
  on the specific paths they want.
- **Do not touch `.terraform/providers` subtrees** — these contain
  vendored provider docs that would pollute Memory. The `-path` prune
  above handles this.
- **Batch order matters slightly.** Prefer this order if possible:
  `root` → `docs` → `backend` → `frontend` → `mobile` → infra dirs
  (`terraform`, `scripts`, `.github`). It mirrors the typical
  logical-dependency order and gives `/absorb` the richest cross-ref
  context as branches accumulate. If the repo doesn't have these dirs,
  alphabetical is fine.
