---
project: agent-knowledge
updated: 2026-04-23
---

# Memory

## Areas

- [packaging](packaging.md) -- Python packaging, hatchling, v0.2.0, pip install agent-knowledge-cli
- [cli](cli.md) -- CLI, 21 subcommands, click framework, shell delegation pattern
- [architecture](architecture.md) -- Runtime modules, path resolution, project config v4, asset layout
- [integrations](integrations.md) -- Multi-tool detection (Cursor/Claude/Codex), bridge files, hooks
- [testing](testing.md) -- 128 tests, pytest, GitHub Actions CI (ubuntu + macos, py 3.10/3.12/3.13)
- [stack](stack.md) -- Python 3.9+, Bash scripts, click, hatchling, no database/server
- [conventions](conventions.md) -- Naming rules, file layout conventions, design constraints
- [deployments](deployments.md) -- CI pipeline, release process, PyPI publish
- [gotchas](gotchas.md) -- Known pitfalls and non-obvious behaviors
- [history-layer](history-layer.md) -- Lightweight History/ diary, events.ndjson, backfill-history command
