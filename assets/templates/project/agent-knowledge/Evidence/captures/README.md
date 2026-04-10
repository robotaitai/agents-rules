# Evidence/captures/

Lightweight capture stream of project events. Auto-written by `agent-knowledge sync`,
`agent-knowledge update`, and hook-triggered maintenance flows.

## What lives here

Each file is a small structured YAML record of one event:

- `timestamp` -- when the event occurred (UTC ISO-8601)
- `source_tool` -- cursor / claude / codex / cli / hook
- `event_type` -- sync / update / import / ship / init / hook-triggered
- `project_slug` -- which project
- `changed_paths` -- files that changed (if available)
- `touched_branches` -- memory branches affected
- `summary` -- one-line human-readable description
- `confidence` -- cli-confirmed / hook-inferred

## Rules

- This is **evidence, not curated memory**. Never treated as canonical truth.
- Never manually move items from here into Memory/. If a pattern is stable and
  durable, write it into the appropriate Memory/ branch note instead.
- Do not store secrets, tokens, auth blobs, or large raw output here.
- Files are append-only: do not edit existing capture files.
- Idempotent: repeated identical events within the same minute produce only one file.

## Pruning

Captures accumulate over time. Prune periodically with `agent-knowledge compact`.
The compact command leaves at least 30 recent captures and removes the rest.
