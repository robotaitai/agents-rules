# agent-knowledge

Persistent, file-based project memory for AI coding agents.

One command gives any project a knowledge vault that agents read on startup,
maintain during work, and carry across sessions -- no database, no server,
just markdown files and a CLI.

## Install

```bash
pip install agent-knowledge-cli
```

PyPI package name: `agent-knowledge-cli`. CLI command and all docs: `agent-knowledge`.

## Quick Start

```bash
cd your-project
agent-knowledge init
```

Open Cursor or Claude Code — the agent picks up from there automatically.

`init` does everything in one shot:
- infers the project slug from the directory name
- creates an external knowledge vault at `~/agent-os/projects/<slug>/`
- symlinks `./agent-knowledge` into the repo as the local handle
- installs Cursor integration: `.cursor/rules/`, `.cursor/hooks.json`, `.cursor/commands/`
- installs Claude integration: `.claude/settings.json`, `.claude/CLAUDE.md`, `.claude/commands/`
- detects Codex and installs its bridge files if present
- bootstraps the memory tree and marks onboarding as `pending`
- imports repo history into `Evidence/` automatically
- backfills lightweight history from git

## How It Works

Knowledge lives **outside** the repo at `~/agent-os/projects/<slug>/` so it persists
across branches, tools, and clones. The symlink `./agent-knowledge` gives every tool
a stable local handle.

### Architecture boundaries

| Folder | Role | Canonical? |
|--------|------|-----------|
| `Memory/` | Curated, durable facts — source of truth | Yes |
| `History/` | What happened over time — lightweight diary | Yes (diary) |
| `Evidence/` | Imported/extracted material, event stream | No |
| `Outputs/` | Generated views, indexes, HTML export | No |
| `Sessions/` | Ephemeral session state, prune aggressively | No |

Evidence is never auto-promoted into Memory. Outputs are never treated as truth.
Only agents and humans deliberately write to Memory or History.

## Obsidian-ready

The knowledge vault at `~/agent-os/projects/<slug>/` is a valid Obsidian vault.
Open it directly for backlinks, graph view, and note navigation.

![Obsidian graph view of a project knowledge vault](docs/obsidian-graph.png)

For a spatial canvas of the knowledge graph:

```bash
agent-knowledge export-canvas
# produces: agent-knowledge/Outputs/knowledge-export.canvas
```

The vault is designed to work well in Obsidian — good markdown, YAML frontmatter,
branch-note convention, internal links. But everything works without it too.

### Automatic capture

Every sync and update event is automatically recorded in `Evidence/captures/`
as a small structured YAML file. This gives a lightweight history of what
changed and when -- without a database or background service.

Captures are evidence, not memory. They accumulate quietly and can be pruned
with `agent-knowledge compact`.

### Progressive retrieval

The knowledge index (`Outputs/knowledge-index.json` and `.md`) is regenerated
on every sync. It provides a compact catalog of all notes so agents can:

1. Load the index first (cheap, a few KB)
2. Identify relevant branches from the shortlist
3. Load only the full note content they actually need

Use `agent-knowledge search <query>` to run a quick Layer 2 shortlist query
from the command line or a hook.

## Project-local runtime

The project carries everything it needs. Opening the repo in Cursor or Claude Code
is enough to get automatic behavior — no manual prompting, no global config required.

### Cursor

| What is installed | What it does |
|------------------|-------------|
| `.cursor/rules/agent-knowledge.mdc` | Always-on rule: loads memory context on every session |
| `.cursor/hooks.json` | Lifecycle hooks: sync on start, update on write, sync on stop and pre-compact |
| `.cursor/commands/memory-update.md` | `/memory-update` slash command |
| `.cursor/commands/system-update.md` | `/system-update` slash command |

### Claude Code

| What is installed | What it does |
|------------------|-------------|
| `.claude/settings.json` | Lifecycle hooks: sync on SessionStart, Stop, PreCompact |
| `.claude/CLAUDE.md` | Runtime contract: knowledge layers, session protocol, onboarding |
| `.claude/commands/memory-update.md` | `/memory-update` slash command |
| `.claude/commands/system-update.md` | `/system-update` slash command |

### Session lifecycle

Hooks fire automatically in both Cursor and Claude Code:

- **session start** — runs `agent-knowledge sync` to load fresh vault state
- **post-write** (Cursor only) — runs `agent-knowledge update` after each file save
- **stop** — runs `agent-knowledge sync` at end of each task
- **pre-compact** — runs `agent-knowledge sync` before context compaction

The runtime contract ensures the agent reads `STATUS.md` and `Memory/MEMORY.md` at the
start of every session, with no manual prompting required.

### Slash commands

Inside any Cursor or Claude Code session in this project:

- `/memory-update` — sync, review session work, write stable facts to `Memory/`, summarize
- `/system-update` — refresh integration files to the latest framework version

These are project-local. They work because `init` installed them in `.cursor/commands/`
and `.claude/commands/`.

### Integration health

```bash
agent-knowledge doctor
```

Reports whether Cursor and Claude integration files (rules, hooks, settings, commands)
are all installed and current. If any file is stale or missing, `doctor` suggests
`agent-knowledge refresh-system`.

## Commands

| Command | What it does |
|---------|-------------|
| `init` | Set up a project — one command, no arguments needed |
| `sync` | Full sync: memory, history, git evidence, index |
| `doctor` | Validate setup, integration health, version staleness |
| `ship` | Validate + sync + commit + push |
| `search <query>` | Search the knowledge index (Memory-first) |
| `export-html` | Build a polished static site from the vault |
| `view` | Build site and open in browser |
| `clean-import <url>` | Import a URL as cleaned, non-canonical evidence |
| `refresh-system` | Refresh all integration files to the current framework version |
| `backfill-history` | Rebuild lightweight project history from git |
| `compact` | Prune stale captures and old session state |

All write commands support `--dry-run` and `--json`. Run `agent-knowledge --help` for the full command list.

## Static site export with graph

Build a polished standalone site from your knowledge vault — no Obsidian required:

```
agent-knowledge export-html
# produces: agent-knowledge/Outputs/site/index.html
#           agent-knowledge/Outputs/site/data/knowledge.json
#           agent-knowledge/Outputs/site/data/graph.json
```

Or generate and open immediately:

```
agent-knowledge view
# or
agent-knowledge export-html --open
```

The generated site includes:
- **Overview page** — project summary, branch cards, recent changes, key decisions, open questions
- **Branch tree** — sidebar navigation across all Memory/ branches with leaf drill-down
- **Note detail view** — rendered markdown with metadata panel and related notes
- **Evidence view** — all imported material, clearly marked non-canonical
- **Graph view** — interactive force-directed graph of all knowledge nodes and relationships
- **Structured data** — `knowledge.json` and `graph.json` machine-readable models of the vault

**Graph view** is a secondary exploration aid, not the primary navigation. The tree explorer and note detail view are the main interfaces. The graph shows:
- Branches, leaf notes, decisions, evidence, and outputs as distinct node types
- Structural edges (solid) and inferred relationships (dashed)
- Color-coded node types with visual distinction between canonical (Memory) and non-canonical (Evidence/Outputs) content
- Interactive zoom/pan, click-to-select with info panel, filter by node type and canonical status, and text search

The graph is built from `graph.json`, which is derived from `knowledge.json`. Neither file is canonical truth.

Memory/ notes are always primary. Evidence and Outputs items are clearly marked non-canonical. The site is a generated presentation layer — the vault remains the source of truth.

The site is a single `index.html` with all data embedded as JS variables, so it opens correctly via `file://` without any server.

## Skills

agent-knowledge ships a set of focused, composable agent skills. Install them globally:

```
agent-knowledge setup
```

Skills installed to `~/.cursor/skills/`:

| Skill | Purpose |
|-------|---------|
| `memory-management` | Session-start: tree structure, reading, writeback |
| `project-memory-writing` | How to write high-quality memory notes |
| `branch-note-convention` | Naming and structure convention |
| `ontology-inference` | Infer project ontology from the repo |
| `decision-recording` | Record architectural decisions as ADRs |
| `evidence-handling` | Evidence rules and promotion process |
| `clean-web-import` | Import web content cleanly |
| `obsidian-compatible-writing` | Optional Obsidian-friendly authoring |
| `session-management` | Session tracking and handoffs |
| `memory-compaction` | Prune stale notes |
| `project-ontology-bootstrap` | Bootstrap a new memory tree |

Skills are plain markdown files and work with any skill-compatible agent
(Cursor, Claude Code, Codex). See `assets/skills/SKILLS.md` for details.

## Clean web import

Import a web page as cleaned, non-canonical evidence:

```
agent-knowledge clean-import https://docs.example.com/api-reference
# produces: agent-knowledge/Evidence/imports/2025-01-15-api-reference.md
```

Strips navigation, ads, scripts, and boilerplate. Writes clean markdown with
YAML frontmatter marking it as non-canonical. Verify facts before promoting
any content to Memory/.


## Multi-Tool Support

`init` always installs both Cursor and Claude integration. Codex is installed when detected:

| Tool | Bridge files | When installed |
|------|-------------|---------------|
| Cursor | `.cursor/rules/` + `.cursor/hooks.json` + `.cursor/commands/` | Always |
| Claude | `.claude/settings.json` + `.claude/CLAUDE.md` + `.claude/commands/` | Always |
| Codex | `.codex/AGENTS.md` | When `.codex/` directory is detected |

Multiple tools in the same repo work together. Integration files are inert when
the respective tool is not in use.

## Custom Knowledge Home

```bash
export AGENT_KNOWLEDGE_HOME=~/my-knowledge
agent-knowledge init
```

## Project history

`init` automatically backfills a lightweight history layer when run on an existing repo.
You can also run it explicitly at any time:

```bash
agent-knowledge backfill-history
```

This creates `History/` inside the vault with:

- `events.ndjson` — compact append-only event log (one JSON object per line)
- `history.md` — human-readable entrypoint with recent milestones
- `timeline/` — sparse milestone notes for significant events (init, releases)

History records **what happened** over time — releases, detected integrations, sync
events. It is not a git replacement and not a second source of truth. Current truth
lives in `Memory/`.

| Layer | Role |
|-------|------|
| `Memory/` | What is true now (curated, authoritative) |
| `History/` | What happened over time (lightweight diary) |
| `Evidence/` | Imported/extracted material (non-canonical) |
| `Outputs/` | Generated helper artifacts |
| `Sessions/` | Temporary working state |

History is idempotent. Run `backfill-history --dry-run` to preview without writing.
`doctor` warns when `History/` is missing.

## Keeping up to date

When a new version of agent-knowledge is installed, refresh the project integration:

```bash
pip install -U agent-knowledge-cli
agent-knowledge refresh-system
```

`refresh-system` updates all integration bridge files — Cursor hooks/rules/commands, Claude settings/commands/contract, `AGENTS.md` header, Codex config — and version markers in `STATUS.md` and `.agent-project.yaml`. It never touches `Memory/`, `Evidence/`, `Sessions/`, or any curated project knowledge.

Run `--dry-run` to preview changes without writing:

```bash
agent-knowledge refresh-system --dry-run
```

`doctor` also warns when the project integration is behind the installed version.

## Troubleshooting

```bash
agent-knowledge doctor          # validate setup and report health
agent-knowledge doctor --json   # machine-readable health check
agent-knowledge validate        # check knowledge layout and links
```

Common issues:
- `./agent-knowledge` missing: run `agent-knowledge init`
- Onboarding still pending: paste the init prompt into your agent
- Stale index: run `agent-knowledge index` or `agent-knowledge sync`
- Large notes: run `agent-knowledge compact`
- **Wrong binary**: another tool (e.g. graphify) may install a Node.js `agent-knowledge` that shadows ours. Check with `which -a agent-knowledge`. Fix: add the Python bin to PATH before nvm — `export PATH="$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts"))'):$PATH"` — or invoke directly: `python3 -m agent_knowledge`

## Platform Support

- **macOS** and **Linux** are fully supported.
- **Windows** is not currently supported (relies on `bash` and POSIX shell scripts).
- Python 3.9+ is required.

## Package naming

| What | Value |
|------|-------|
| PyPI package | `agent-knowledge-cli` |
| CLI command | `agent-knowledge` |
| Python import | `agent_knowledge` |

Install: `pip install agent-knowledge-cli`
Command: `agent-knowledge --help`

## Development

```bash
git clone <repo-url>
cd agent-knowledge
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -q
```
