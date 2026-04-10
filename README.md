# agent-knowledge

Persistent, file-based project memory for AI coding agents.

One command gives any project a knowledge vault that agents read on startup,
maintain during work, and carry across sessions -- no database, no server,
just markdown files and a CLI.

## Install

```
pip install agent-knowledge-cli
```

This installs the `agent-knowledge` command. PyPI package name is `agent-knowledge-cli`;
the CLI command and all documentation refer to it as `agent-knowledge`.

## Quick Start

```
cd your-project
agent-knowledge init
```

Open Cursor, Claude, or Codex in the repo -- the agent picks up from there.

`init` automatically:
- infers the project slug from the directory name
- creates an external knowledge vault at `~/agent-os/projects/<slug>/`
- symlinks `./agent-knowledge` into the repo as the local handle
- detects Cursor, Claude, and Codex and installs integration files
- bootstraps the memory tree and marks onboarding as `pending`
- prints the prompt to kick off first-time agent ingestion

## How It Works

```
your-project/
  .agent-project.yaml        # project config
  AGENTS.md                   # instructions agents read on startup
  agent-knowledge/            # symlink -> ~/agent-os/projects/<slug>/
    STATUS.md                 # onboarding state + sync timestamps
    Memory/                   # curated, durable knowledge (source of truth)
      MEMORY.md
      stack.md
      decisions/
        decisions.md
    Evidence/                 # imported or extracted material (not canonical)
      raw/
      imports/
      captures/               # automatic event stream
    Outputs/                  # generated views (never canonical)
      knowledge-index.json
      knowledge-index.md
      knowledge-export.html
    Sessions/                 # ephemeral session state
```

Knowledge lives **outside** the repo so it persists across branches, tools,
and clones. The symlink gives every tool a stable `./agent-knowledge` path.

### Architecture boundaries

| Folder | Role | Canonical? |
|--------|------|-----------|
| `Memory/` | Curated, durable facts -- source of truth | Yes |
| `Evidence/` | Imported/extracted material, event stream | No |
| `Outputs/` | Generated views, indexes, HTML export | No |
| `Sessions/` | Ephemeral session state, prune aggressively | No |

Evidence is never auto-promoted into Memory. Outputs are never treated as truth.
Only agents and humans deliberately write to Memory.

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

#
## Commands

| Command | What it does |
|---------|-------------|
| `init` | Set up a project (zero-arg, auto-detects everything) |
| `sync` | Memory sync + session rollup + git evidence + capture + index |
| `doctor` | Validate setup and report health |
| `update` | Sync project changes into the knowledge tree |
| `import` | Import repo history into Evidence/ |
| `ship` | Validate, sync, commit, push |
| `bootstrap` | Create or repair the memory tree |
| `setup` | Install global Cursor rules and skills |
| `global-sync` | Import safe local tooling config |
| `graphify-sync` | Import graph/discovery artifacts |
| `compact` | Prune stale memory and old captures |
| `index` | Regenerate the knowledge index in Outputs/ |
| `search <query>` | Search the knowledge index (Memory-first) |
| `export-html` | Build polished static site in Outputs/site/ |
| `view` | Build site and open it in the browser |
| `clean-import <url>` | Import a URL or HTML file as cleaned evidence |
| `refresh-system` | Refresh integration files to the current framework version |
| `export-canvas` | Export vault as an Obsidian Canvas file (optional) |
| `measure-tokens` | Estimate context token savings |

All write commands support `--dry-run`. Use `--json` for machine-readable output.

## Static site export

Build a polished standalone site from your knowledge vault — no Obsidian required:

```
agent-knowledge export-html
# produces: agent-knowledge/Outputs/site/index.html
#           agent-knowledge/Outputs/site/data/knowledge.json
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
- **Structured data** — `knowledge.json` machine-readable model of the entire vault

Memory/ notes are always primary. Evidence and Outputs items are clearly marked non-canonical. The site is a generated presentation layer — the vault remains the source of truth.

The site is a single `index.html` with all data embedded as a JS variable, so it opens correctly via `file://` without any server.

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

## Obsidian (optional)

Obsidian is an **optional** viewer/editor. agent-knowledge is not Obsidian-centric.

Open `~/agent-os/projects/<slug>/` as an Obsidian vault for backlinks and graph view.

![Obsidian graph view of a project knowledge vault](docs/obsidian-graph.png)

For an optional spatial canvas of the knowledge graph:

```
agent-knowledge export-canvas
# produces: agent-knowledge/Outputs/knowledge-export.canvas
# open in Obsidian with Core plugins > Canvas
```

All Obsidian-specific features are optional. The system works fully without Obsidian.

## Multi-Tool Support

`init` detects which tools are present and installs the right bridge files:

| Tool | Bridge file | When installed |
|------|-------------|---------------|
| Cursor | `.cursor/hooks.json` + `.cursor/rules/agent-knowledge.mdc` | Always |
| Claude | `CLAUDE.md` | When `.claude/` directory is detected |
| Codex | `.codex/AGENTS.md` | When `.codex/` directory is detected |

Multiple tools in the same repo work together.

## Custom Knowledge Home

```bash
export AGENT_KNOWLEDGE_HOME=~/my-knowledge
agent-knowledge init
```

## Keeping up to date

When a new version of agent-knowledge is installed, refresh the project integration:

```bash
pip install -U agent-knowledge-cli
agent-knowledge refresh-system
```

`refresh-system` updates integration bridge files (Cursor hooks, `AGENTS.md` header, `CLAUDE.md`, Codex config) and version markers in `STATUS.md` and `.agent-project.yaml`. It never touches `Memory/`, `Evidence/`, `Sessions/`, or any curated project knowledge.

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
