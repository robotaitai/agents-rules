---
note_type: decisions-index
updated: 2026-04-18
tags:
  - agent-knowledge
  - memory
  - decision
---

# Decision Log

Architectural and process decisions for agent-knowledge.

## 001 - Hatchling as build backend {#001}

- **Date**: 2026-04-08
- **Context**: Needed a modern `pyproject.toml`-only backend that supports `force-include` for non-Python assets
- **Decision**: [[packaging|hatchling]] -- simpler than setuptools, native `force-include`
- **Status**: Active

## 002 - Keep shell scripts, wrap in Python {#002}

- **Date**: 2026-04-08
- **Context**: Existing bash scripts handle complex file ops. Rewriting all in Python is high risk.
- **Decision**: Keep scripts in `assets/scripts/`, invoke via [[cli|subprocess from click CLI]]
- **Status**: Active

## 003 - External knowledge vault + local symlink {#003}

- **Date**: 2026-04-08
- **Context**: Project knowledge needs to be shareable across tools and openable in Obsidian
- **Decision**: Real knowledge at `~/agent-os/projects/<slug>/`, project repo gets `./agent-knowledge` symlink
- **Status**: Active

## 004 - Zero-arg init with auto-detection {#004}

- **Date**: 2026-04-08
- **Context**: Reduce friction for new project setup
- **Decision**: [[cli#init (zero-arg)|init]] infers slug from dir name, auto-detects [[integrations|Cursor/Claude/Codex]]
- **Status**: Active

## 005 - Automatic onboarding via AGENTS.md + STATUS.md {#005}

- **Date**: 2026-04-08
- **Context**: Agents should start maintaining knowledge without extra user commands
- **Decision**: [[STATUS]] tracks onboarding state, `AGENTS.md` instructs agents, [[integrations|bridge files]] reinforce
- **Status**: Active

## 006 - Inline Cursor rule content in Python {#006}

- **Date**: 2026-04-08
- **Context**: pip had a rare bug extracting `.mdc` files from wheels during editable installs
- **Decision**: Inline rule content as a Python string in `integrations.py` (see [[gotchas]])
- **Status**: Active (workaround)

## 007 - Project-local Cursor integration as primary runtime {#007}

- **Date**: 2026-04-12
- **Context**: Global home-dir hook setup was fragile; agents forgot memory layer between sessions
- **Decision**: `init` installs `.cursor/rules/`, `.cursor/hooks.json`, `.cursor/commands/` per-project; project carries the contract
- **Status**: Active

## 008 - Full session lifecycle hooks {#008}

- **Date**: 2026-04-12
- **Context**: Only `post-write` and `session-start` hooks existed; stop and compaction events missed
- **Decision**: Add `stop` + `preCompact` hooks both calling `agent-knowledge sync`; hooks stay thin
- **Status**: Active

## 009 - init auto-runs import and shows single clean prompt {#009}

- **Date**: 2026-04-13
- **Context**: `init` output had multiple "Next steps" blocks confusing users
- **Decision**: `init` auto-runs `import-agent-history.sh` and `backfill-history`; shows one agent-chat box at the end
- **Status**: Active

## 010 - Claude Code as always-installed first-class integration {#010}

- **Date**: 2026-04-13
- **Context**: Claude Code adoption growing; was previously optional/detected-only
- **Decision**: `init` always installs `.claude/` integration (settings.json, CLAUDE.md, commands/); `refresh-system` keeps it current
- **Status**: Active

## See Also

- [[architecture]] -- where these decisions are applied
- [[gotchas]] -- problems these decisions solve
