---
note_type: durable-branch
area: history-layer
updated: 2026-04-11
tags:
  - agent-knowledge
  - memory
  - history
---

# History Layer

Lightweight project diary. Records what happened over time without becoming a second knowledge base.

## Structure

```
History/
  events.ndjson    -- append-only machine-readable event log (NDJSON)
  history.md       -- human-readable entrypoint (< 150 lines, auto-generated)
  timeline/        -- sparse milestone notes (init, backfill, releases only)
```

## Memory vs History

| Layer | Role |
|-------|------|
| `Memory/` | What is true now (curated, authoritative) |
| `History/` | What happened over time (lightweight diary) |
| `Evidence/` | Imported/extracted material (non-canonical) |
| `Outputs/` | Generated helper artifacts |
| `Sessions/` | Temporary working state |

History is **not** a git replacement, not a full transcript store, not a second source of truth.

## Event Types

- `project_start` — first git commit date + total commits (once ever)
- `release` — one event per git tag (deduplicated by tag name)
- `integration_cursor/claude/codex` — detected tool integration (once per month)
- `backfill` — summary of the backfill run (once per month)

## Deduplication

- `project_start`: once ever
- `release`: once per tag name
- `backfill`, `integration_*`: once per calendar month
- Safe to re-run: idempotent by design

## Commands

- `agent-knowledge init` — auto-backfills history after setup
- `agent-knowledge backfill-history` — manual refresh, supports `--dry-run`, `--json`, `--force`
- `agent-knowledge doctor` — warns if `History/` is missing

## Implementation

- `src/agent_knowledge/runtime/history.py`
- Functions: `run_backfill()`, `init_history()`, `append_event()`, `log_event()`, `read_events()`, `history_exists()`
- Git helpers: subprocess calls to `git log`, `git tag`, `git rev-list`

## See Also

- [[architecture]] -- runtime module layout
- [[cli]] -- backfill-history and doctor commands
