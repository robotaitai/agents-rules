---
note_type: knowledge-root
project: agent-knowledge
status: active
last_updated: 2026-04-08
tags:
  - agent-knowledge
  - home
---

# agent-knowledge

Pip-installable CLI that gives AI agents persistent, file-based project memory.

## Quick Navigation

| Area | Description |
|------|-------------|
| [[STATUS]] | Onboarding state, sync timestamps, health |
| [[MEMORY]] | Curated project knowledge (source of truth) |
| [[project-overview]] | Live project dashboard |
| [[session-rollup]] | Recent session summaries |
| [[git-recent]] | Latest git commits |

## Memory Areas

- [[stack]] -- Python 3.9+, Bash, hatchling, click, pytest
- [[architecture]] -- Package layout, path resolution, integration system
- [[cli]] -- 14 subcommands, zero-arg init, sync command
- [[packaging]] -- Build system, asset bundling, version 0.0.1
- [[integrations]] -- Cursor/Claude/Codex auto-detection and bridge files
- [[testing]] -- 46 tests, GitHub Actions CI
- [[conventions]] -- Naming, output rules, template patterns
- [[gotchas]] -- macOS pip, venv corruption, shell script traps
- [[deployments]] -- CI, versioning, distribution
- [[decisions]] -- Architecture and process decisions

## Knowledge Layers

| Layer | Purpose |
|-------|---------|
| [[MEMORY]] | Curated, durable facts |
| [[evidence]] | Raw imports ([[git-recent]], backfill) |
| [[sessions]] | Ephemeral session state |
| [[project-overview]] / [[session-rollup]] | Dashboards |
| [[outputs]] | Generated views (never canonical) |

#agent-knowledge #home
