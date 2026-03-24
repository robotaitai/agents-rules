# agents-rules

Personal collection of AI agent rules and skills for Cursor and Claude Code. Install them into any project for consistent, high-quality AI assistance.

## Quick Start

```bash
# Clone
git clone <repo-url> ~/agents-rules

# --- Cursor ---
# Symlink global rules into ~/.cursor/rules/
~/agents-rules/scripts/install-global.sh

# Symlink project rules into a project
~/agents-rules/scripts/install.sh /path/to/project

# --- Claude Code ---
# Install global rules into ~/.claude/CLAUDE.md
~/agents-rules/claude/scripts/install.sh

# Install global rules + scaffold CLAUDE.md in a project
~/agents-rules/claude/scripts/install.sh /path/to/project
```

## Structure

```
agents-rules/
  rules/                    # On-demand Cursor rules (.mdc) — symlinked per project
  rules-global/             # Always-on Cursor rules (.mdc) — symlinked into ~/.cursor/rules/
  skills/                   # Cursor/Claude skills (memory, sessions)
  skills-cursor/            # Cursor-specific built-in skills
  scripts/                  # Cursor install/uninstall/list scripts
  claude/
    global.md               # Source of truth for global Claude Code rules
    project-template.md     # Starter CLAUDE.md for new projects
    scripts/
      install.sh            # Installs global.md into ~/.claude/CLAUDE.md
```

---

## Cursor

### How it works

Rules are **symlinked** into each project's `.cursor/rules/` directory. Edit the source file once — all projects get the update instantly.

### Rules

| File | Always On | Description |
|------|-----------|-------------|
| `rules-global/action-first.mdc` | Yes | Think deeply, act decisively, speak briefly |
| `rules-global/no-icons-emojis.mdc` | Yes | No emojis or icons anywhere |
| `rules-global/no-unsolicited-docs.mdc` | Yes | Never create docs unless asked |
| `rules/workflow-orchestration.mdc` | Yes | Plan-first, subagents, verification, elegance |
| `rules/generate-architecture-doc.mdc` | No | Generate rich HTML architecture docs |

### Skills

| Directory | Description |
|-----------|-------------|
| `skills/memory-management/` | Persistent memory across conversations |
| `skills/session-management/` | Work-in-progress session tracking |
| `skills-cursor/create-rule/` | Create new Cursor rules |
| `skills-cursor/create-skill/` | Create new skills |
| `skills-cursor/create-subagent/` | Create custom subagents |
| `skills-cursor/migrate-to-skills/` | Migrate rules/commands to skills format |
| `skills-cursor/shell/` | Run shell commands via /shell |
| `skills-cursor/update-cursor-settings/` | Edit Cursor/VSCode settings.json |

### Cursor Scripts

| Script | Usage | Description |
|--------|-------|-------------|
| `scripts/install.sh` | `./install.sh /path/to/project [rule.mdc]` | Symlink rules into a project |
| `scripts/uninstall.sh` | `./uninstall.sh /path/to/project` | Remove symlinked rules |
| `scripts/list.sh` | `./list.sh` | List available rules |

### Adding a Cursor Rule

Create a `.mdc` file in `rules/` or `rules-global/`:

```markdown
---
description: Short description shown in Cursor's rule picker
globs:           # Optional: **/*.ts
alwaysApply: false  # true = always active
---

# Rule Title

Your instructions here...
```

---

## Claude Code

### How it works

Claude Code reads two CLAUDE.md files on every session:

- `~/.claude/CLAUDE.md` — global rules, loaded for all projects
- `<project>/CLAUDE.md` — project-specific rules, loaded for that project only

The install script writes global rules into `~/.claude/CLAUDE.md` inside a managed marker section, so re-running is safe.

### Install global rules

```bash
~/agents-rules/claude/scripts/install.sh
```

### Scaffold a new project

```bash
~/agents-rules/claude/scripts/install.sh /path/to/project
# Creates /path/to/project/CLAUDE.md from project-template.md
# Also installs/updates global rules in ~/.claude/CLAUDE.md
```

Then edit `CLAUDE.md` in the project root with your project-specific stack, conventions, and constraints.

### What global.md contains

- Communication style: action-first, brief, no filler
- Prohibitions: no emojis, no unsolicited docs
- Workflow: plan-first, subagents, verification, elegance, autonomous bug fixing
- Code quality: simplicity, minimal impact, no unnecessary dependencies
- Memory: when and what to save/forget

### Memory system (Claude Code)

Claude Code has a built-in persistent memory at `~/.claude/projects/<project-id>/memory/`. The memory-management skill describes how to use it.

| File | Purpose |
|------|---------|
| `MEMORY.md` | Index — always loaded, keep under 200 lines |
| `*.md` | Topic files linked from MEMORY.md |

Memory types: `user` (who they are), `feedback` (corrections + confirmations), `project` (goals, decisions, status), `reference` (where to find things).

---

## Shell Aliases (Optional)

```bash
alias ari='~/agents-rules/scripts/install.sh'
alias arl='~/agents-rules/scripts/list.sh'
alias aru='~/agents-rules/scripts/uninstall.sh'
alias arci='~/agents-rules/claude/scripts/install.sh'
```
