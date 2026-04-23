---
note_type: durable-branch
area: stack
updated: 2026-04-08
tags:
  - agent-knowledge
  - memory
  - stack
---

# Stack

Languages, runtimes, frameworks, and tooling used by agent-knowledge.

## Languages & Runtimes

- **Python 3.9+** -- package code, [[cli|CLI]], [[testing|tests]]
- **Bash** -- bundled scripts in `assets/scripts/` (see [[architecture]])

## Build & Packaging

- **[[packaging|hatchling]]** via `pyproject.toml`, src-layout at `src/agent_knowledge/`
- Wheel includes all non-Python assets via `force-include`

## Dependencies

- **click >= 8.0** -- [[cli|CLI framework]]
- **tiktoken** (optional) -- token measurement
- **pytest >= 7.0** (dev) -- [[testing]]
- **python-build** (dev) -- wheel/sdist building

## CI/CD

- [[deployments|GitHub Actions]] -- Python 3.10, 3.12, 3.13 on Ubuntu + macOS

## What This Is Not

- No frontend, no database, no API server, no Docker

## See Also

- [[packaging]] -- how the package is built and distributed
- [[architecture]] -- how the code is structured
- [[deployments]] -- CI pipeline details
