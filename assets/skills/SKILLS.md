# agent-knowledge Skills

Focused, composable skills for the agent-knowledge project knowledge system.

Skills are reusable instruction sets that compatible agents (Cursor, Claude Code,
Codex, or any skill-aware agent) can load on demand.

---

## How skills relate to the CLI

The agent-knowledge CLI is the primary install surface:

```
pip install agent-knowledge-cli
agent-knowledge init
```

Skills are a **portable layer on top**. They provide focused guidance to agents
about how to use the knowledge system correctly. You do not need skills to use
the CLI, but skills make agents much more effective.

Install skills globally with:

```
agent-knowledge setup
```

This symlinks the bundled skills into `~/.cursor/skills/`, `~/.claude/skills/`,
and `~/.cursor/skills-cursor/` (Cursor-specific meta-skills).

---

## Skills index

### Core knowledge management

| Skill | Description |
|-------|-------------|
| `memory-management` | Session-start skill: tree structure, reading strategy, writeback rules |
| `project-memory-writing` | How to write high-quality, stable memory notes |
| `branch-note-convention` | Exact naming and structure convention for branch notes |
| `ontology-inference` | How to infer project ontology from the actual repo |
| `decision-recording` | Recording architectural decisions as lightweight ADRs |
| `evidence-handling` | What goes in Evidence/, what is canonical, promotion rules |

### Evidence and import

| Skill | Description |
|-------|-------------|
| `clean-web-import` | Import web content cleanly into Evidence/imports/ |
| `history-backfill` | Backfill memory from existing repo history |
| `absorb-repo` | Walk a repo, filter vendor/build noise, and feed `/absorb` one batch per top-level dir |

### Session and maintenance

| Skill | Description |
|-------|-------------|
| `session-management` | Track session progress, milestones, and handoffs |
| `memory-compaction` | Prune stale memory notes conservatively |
| `project-ontology-bootstrap` | Bootstrap a new memory tree from scratch |

### Optional Obsidian authoring

| Skill | Description |
|-------|-------------|
| `obsidian-compatible-writing` | Write notes that are pleasant in Obsidian (optional) |

---

## Using skills without the CLI

Skills are plain markdown files. Any agent that can read markdown can use them.

To use a skill directly:
1. Copy the relevant `SKILL.md` file to your agent's skill directory
2. Configure your agent to load it (method varies by tool)
3. The skill references `agent-knowledge` CLI commands where relevant

Skill files are self-contained. They reference each other by name where composition
is useful (e.g., `memory-management` references `project-ontology-bootstrap` and
`memory-compaction`).

---

## Skill composition

Skills are designed to compose:

| Task | Skills to combine |
|------|-------------------|
| Setting up a new project | `project-ontology-bootstrap` + `project-memory-writing` |
| Importing external docs | `clean-web-import` + `evidence-handling` |
| Recording a decision | `decision-recording` + `project-memory-writing` |
| Session start | `memory-management` + `session-management` |
| Vault cleanup | `memory-compaction` + `evidence-handling` |
| Obsidian enhancement | `obsidian-compatible-writing` (optional, standalone) |

---

## Architecture

The skills layer is separate from the CLI, templates, and runtime:

```
assets/
  skills/             <- portable agent skills (this directory)
    SKILLS.md         <- this index
    <skill>/
      SKILL.md
  skills-cursor/      <- Cursor-specific skills (same format)
  scripts/            <- operational bash scripts
  templates/          <- project scaffolding templates
  rules/              <- Cursor rule files (.mdc)

src/agent_knowledge/  <- Python CLI and runtime
```

Skills reference the system but do not depend on internal implementation details.
They work with any agent that can follow markdown instructions.
