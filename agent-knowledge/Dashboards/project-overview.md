---
note_type: dashboard
dashboard: project-overview
project: agent-knowledge
last_updated: 2026-04-08
tags:
  - agent-knowledge
  - dashboard
---

# Project Overview

## At a Glance

| Property | Value |
|----------|-------|
| Project | agent-knowledge |
| Version | 0.0.1 |
| Profile | hybrid |
| Onboarding | complete |
| Last sync | 2026-04-08 |

## Architecture

- [[stack]]: Python 3.9+ / Bash, [[packaging|hatchling]], [[cli|click]]
- [[architecture]]: src-layout, 14 [[cli|CLI subcommands]], bundled scripts
- [[integrations]]: Cursor + Claude + Codex auto-detection
- [[testing]]: 46 tests, [[deployments|GitHub Actions CI]]

## Knowledge Health

- [[MEMORY]] -- 9 curated area notes + [[decisions|6 recorded decisions]]
- [[git-recent]] -- latest 30 commits extracted
- [[STATUS]] -- sync timestamps and warnings
- [[session-rollup]] -- session summaries

## Key Decisions

- [[decisions#001|Hatchling]] as build backend
- [[decisions#002|Shell scripts wrapped in Python]] CLI
- [[decisions#003|External vault]] + local symlink
- [[decisions#004|Zero-arg init]] with auto-detection
- [[decisions#005|Automatic onboarding]] via AGENTS.md
- [[decisions#006|Inlined Cursor rule]] (pip workaround)

## See Also

- [[home]] -- vault root
- [[MEMORY]] -- full memory tree
- [[gotchas]] -- known pitfalls

#agent-knowledge #dashboard
