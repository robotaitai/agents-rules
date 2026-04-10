---
name: project-memory-writing
description: Write high-quality, stable memory notes. Use when creating or updating notes in agent-knowledge/Memory/ and you want specific guidance on format, quality, and what to include.
---

# Project Memory Writing

Focused rules for writing durable memory notes. This is the craft side of memory management: how to write notes that stay useful across sessions and agents.

## When to use this skill

- Creating a new branch note or subtopic note
- Updating Current State or Recent Changes sections
- Reviewing a note that has grown noisy or stale
- Any time the question is "how should I write this?"

For tree structure and reading strategy, see `memory-management`.
For bootstrapping from scratch, see `project-ontology-bootstrap`.

---

## Verification first

Before writing anything to Memory/, verify the fact against the source:

| Source type | Verification requirement |
|-------------|-------------------------|
| Code file | Read the actual file, not a cached summary |
| Test | Run it or check its current state in the test output |
| Decision | Confirm it is still active (not reversed) |
| Config | Read the current config file, not old docs |
| Agent output | Treat as hypothesis until confirmed |

Do NOT write:
- Speculative plans
- In-progress task state (use Sessions/)
- Raw agent summaries without verification
- Facts that change faster than once per week

---

## Required frontmatter

Every Memory/ note must open with YAML frontmatter:

```markdown
---
note_type: <type>
area: <branch-name>
updated: <YYYY-MM-DD>
---
```

`note_type` values: `durable-memory-root` (for MEMORY.md), `branch-entry`, `branch-leaf`, `decision`.

Do not add extra frontmatter fields that tools or other agents don't need.

---

## Required sections for branch notes

Use this section order. Keep each section focused.

```markdown
## Purpose
One sentence. What this branch covers. Rarely changes.

## Current State
Bullet list of verified facts about what is true right now.
- Lead each bullet with the fact itself.
- Do not describe what you "observed" -- state what IS.
- Each bullet should be independently verifiable.

## Recent Changes
Rolling log. Newest first. YYYY-MM-DD format. Prune to ~8 entries.
- 2025-01-15 - Switched from Prisma to raw SQL. See decisions/.
- 2025-01-10 - Added retry logic to all DB calls.

## Decisions
Links to decision files that affect this area.
- [2025-01-15-use-raw-sql.md](../decisions/2025-01-15-use-raw-sql.md) -- raw SQL over ORM

## Open Questions
Unresolved items. Remove when resolved.
- Why does the worker pool size default to 4? Is this tuned or a placeholder?
```

---

## Quality rules

**Be specific.** "Uses Python 3.12" not "uses modern Python".

**State facts, not observations.** "Auth uses JWT with 24h expiry" not "I noticed auth seems to use JWT".

**Stay bounded.** Each note covers one domain. Do not add cross-domain facts to a branch note. If a fact belongs to two domains, put it in the more specific one and link from the other.

**Keep Current State evergreen.** Remove outdated bullets. Do not append without pruning. If you're adding a new fact, check if an old bullet should be removed.

**Keep Recent Changes short.** 6-10 entries. Oldest entries get pruned by compaction. The purpose is "what changed recently", not a full changelog.

**Keep notes scannable.** Use short bullets over prose paragraphs. Headers are navigation -- keep them consistent across notes.

---

## Note sizing

| Size | Action |
|------|--------|
| Under ~100 lines | Fine. Keep as-is. |
| 100-150 lines | Consider pruning Recent Changes. |
| Over 150 lines | Split: create a folder + same-name entry note, move detail to a subtopic note. |
| Over 200 lines | Split immediately. |

When splitting, the entry note stays as the summary and router. Subtopic notes hold the detail.

---

## Linking

Use relative markdown links, not wiki-links:

```markdown
See [navigation](navigation/navigation.md) for path planning details.
```

Not:
```markdown
See [[navigation]] -- avoid wiki-links for portability
```

Links from entry notes to subtopic notes:
```markdown
## Branches
- [object-detection.md](object-detection.md) -- YOLO v8, TensorRT inference
- [lane-detection.md](lane-detection.md) -- semantic segmentation, road edge tracking
```

Links from branch notes to decisions:
```markdown
## Decisions
- [2025-01-15-use-raw-sql.md](../decisions/2025-01-15-use-raw-sql.md) -- raw SQL over ORM
```

---

## What goes where

| Content type | Location |
|--------------|----------|
| Stable, verified facts about the project | `Memory/<branch>.md` |
| Raw imported content (web, docs, git log) | `Evidence/raw/` or `Evidence/imports/` |
| Captured event history | `Evidence/captures/` |
| Generated views (indexes, exports) | `Outputs/` |
| Current session state | `Sessions/` |
| Architectural decisions with rationale | `Memory/decisions/` |

Never put raw content in Memory/. Never put curated facts in Evidence/.

---

## Memory/MEMORY.md rules

The root index must stay short (under 30 lines of content):
- One line per branch, with a brief inline summary
- No dense detail
- Updated only when branches are added, removed, or substantially renamed

```markdown
## Branches
- [stack.md](stack.md) -- Python 3.12, FastAPI, PostgreSQL
- [auth/auth.md](auth/auth.md) -- JWT, bcrypt, refresh token rotation
- [decisions/decisions.md](decisions/decisions.md) -- decision log
```
