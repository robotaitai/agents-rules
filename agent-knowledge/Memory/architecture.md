---
note_type: durable-branch
area: architecture
updated: 2026-04-11
tags:
  - agent-knowledge
  - memory
  - architecture
---

# Architecture

Core design: path resolution, runtime modules, project config, integrations, knowledge vault model.

## Runtime Modules (`src/agent_knowledge/runtime/`)

| Module | Purpose |
|--------|---------|
| `paths.py` | Asset directory resolution (installed vs dev checkout) |
| `shell.py` | `run_bash_script()` / `run_python_script()` subprocess wrappers |
| `integrations.py` | Multi-tool detection and bridge file installation |
| `sync.py` | `agent-knowledge sync` implementation (memory, sessions, git, capture, index) |
| `capture.py` | Automatic capture layer (Evidence/captures/ YAML files) + clean-import |
| `index.py` | Knowledge index generation (knowledge-index.json/md) + search |
| `site.py` | Static HTML site export with interactive graph view |
| `refresh.py` | System refresh: updates integration files to current framework version |
| `history.py` | Lightweight history layer (History/events.ndjson, history.md, timeline/) |

## Knowledge Vault Model

- External vault at `~/agent-os/projects/<slug>/` — source of truth
- Inside each repo: `./agent-knowledge` is a symlink/pointer to the external vault
- Vault structure:
  - `Memory/` — curated, canonical, durable knowledge (MEMORY.md + branch files)
  - `Evidence/` — non-canonical: raw imports, captures, backfills
  - `Outputs/` — generated helper artifacts (site, index, canvas) — never canonical
  - `Sessions/` — temporary working state, rolled up by sync
  - `History/` — lightweight diary: events.ndjson, history.md, timeline/

## Path Resolution

- `runtime/paths.py` → `get_assets_dir()` with dual-mode:
  1. Installed: `assets/` sibling of `runtime/` in site-packages
  2. Dev: `repo_root/assets/` (4 parents up from `paths.py`)
- Marker file for validation: `scripts/lib/knowledge-common.sh`
- Result cached in `_cached_assets_dir` for the process lifetime

## Asset Layout

All non-Python assets under `assets/`:
- `assets/scripts/` — bundled bash scripts
- `assets/templates/` — project, memory, integrations, portfolio templates
- `assets/rules/` — project-level Cursor rules
- `assets/rules-global/` — global Cursor rules
- `assets/commands/` — agent command docs (system-update, ship, etc.)
- `assets/skills/` — composable skill files for agent use
- `assets/skills-cursor/` — Cursor-specific skills
- `assets/claude/` — Claude Code integration files

## Site Generation Pipeline

`vault → knowledge.json → graph.json → index.html`
1. Read vault (Memory/, Evidence/, Outputs/, STATUS.md)
2. Build normalized `Outputs/site/data/knowledge.json`
3. Build `Outputs/site/data/graph.json` with nodes/edges + canonical status
4. Render single-page `Outputs/site/index.html` with all data embedded

Site views: Overview, Tree/Ontology, Note/Detail, Evidence, Graph (force-directed canvas)

## History Layer

- `History/events.ndjson` — append-only machine-readable log
- `History/history.md` — human-readable entrypoint (< 150 lines)
- `History/timeline/` — sparse milestone notes (init, backfill, releases only)
- Dedup: releases once-per-tag, backfill once-per-month, project_start once-ever
- Auto-created by `init`, refreshable with `backfill-history`

## Project Config (`.agent-project.yaml`)

- Version 4, `ontology_model: 2`, `framework_version` field
- `onboarding: status: pending|complete` in STATUS.md
- No `root_index` — entry points are STATUS.md + Memory/MEMORY.md
- Hooks reference `agent-knowledge update --project .`

## System Refresh (`runtime/refresh.py`)

- Compares `framework_version` in STATUS.md to `__version__`
- Refreshes: `AGENTS.md`, `.cursor/hooks.json`, `.cursor/rules/agent-knowledge.mdc`, `CLAUDE.md`, `.codex/AGENTS.md`, `STATUS.md`, `.agent-project.yaml`
- Idempotent: skips files already at current version
- `is_stale()` used by `doctor` command for staleness warning

## Capture Layer

- `Evidence/captures/` — YAML event files (timestamp, source_tool, event_type, touched_branches)
- Idempotent within same UTC minute
- Sources: sync, init, refresh, graph sync, import, ship

## Knowledge Index

- `Outputs/knowledge-index.json` — structured catalog for programmatic retrieval
- `Outputs/knowledge-index.md` — human-readable version
- Search: Memory-first, Evidence/Outputs clearly marked non-canonical
- Used by `agent-knowledge search <query>`

## Gotchas

- `set -euo pipefail` + trailing `[` test returning false causes exit 1 — fixed with explicit `if`
- `ship.sh` must use `python -m pytest -q` not bare `pytest`
- Canvas 2D rendering: reading `clientWidth`/`clientHeight` after `display:none→block` must be deferred with `requestAnimationFrame` (graph fix, 2026-04-11)
- Evidence/Outputs are non-canonical and must not be auto-promoted to Memory/
