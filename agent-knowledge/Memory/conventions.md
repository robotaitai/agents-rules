---
note_type: durable-branch
area: conventions
updated: 2026-04-08
tags:
  - agent-knowledge
  - memory
  - conventions
---

# Conventions

Coding patterns, naming, and design rules.

## Naming

- [[cli|CLI]] command names use **hyphens**: `agent-knowledge graphify-sync`
- Python package uses **underscores**: `agent_knowledge`
- User-facing messages reference CLI commands, never script paths

## Code Patterns

- Shell scripts stay in `assets/scripts/`, invoked via `runtime/shell.py`
- Templates use `<placeholder>` syntax for substitution
- No emojis or icons in code, logs, or output (see project rules)

## Memory Notes

- Require YAML frontmatter: `note_type`, `area`/`project`, `updated`, `tags`
- Use wiki-links (`[[note-name]]`) for Obsidian graph connectivity
- [[MEMORY|Evidence and Outputs]] are never treated as curated truth

## Shell Scripts

- Always `set -euo pipefail`
- Avoid `[ test ] && cmd` -- use `if/then` (see [[gotchas]])
- Find assets via `SCRIPT_DIR`, never hardcode paths

## See Also

- [[architecture]] -- how patterns are applied
- [[gotchas]] -- things that break these conventions
- [[cli]] -- CLI naming examples
