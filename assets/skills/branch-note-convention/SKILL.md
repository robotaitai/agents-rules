---
name: branch-note-convention
description: The exact naming and structure convention for memory branch notes. Use when creating, naming, or reorganizing notes in Memory/, or when checking whether a note follows the convention.
---

# Branch-Note Convention

The branch-note convention is the structural spine of the agent-knowledge memory tree.
It controls how notes are named, organized, and navigated.

---

## The two forms

### Form 1: Flat note (no subtopics needed)

```
Memory/
  stack.md
```

A single `.md` file. Topic has no subtopics currently.

### Form 2: Folder + same-name entry note (has subtopics)

```
Memory/
  auth/
    auth.md         <- entry note: same name as the folder
    jwt.md          <- subtopic note
    sessions.md     <- subtopic note
```

The entry note (`auth/auth.md`) is the summary and router for the branch.
Subtopic notes (`jwt.md`, `sessions.md`) hold the detail.

**The entry note always has the same name as its folder.** This is non-negotiable.
It makes the convention deterministic and machine-readable.

---

## Naming rules

| Rule | Good | Bad |
|------|------|-----|
| Use the project's own terminology | `perception.md` | `computer-vision.md` |
| Lowercase hyphenated | `data-pipeline.md` | `DataPipeline.md` |
| Specific, not generic | `billing.md` | `payments-and-invoicing.md` |
| One domain per note | `auth.md` | `auth-and-sessions-and-tokens.md` |
| Entry note = folder name | `auth/auth.md` | `auth/index.md`, `auth/overview.md` |

---

## Promotion: flat -> folder

Start flat. Promote to a folder only when:
1. The topic accumulates 2+ subtopics that deserve their own focused notes
2. The flat note is approaching 150 lines

How to promote:
1. Create the folder: `Memory/auth/`
2. Move the flat note into it: `Memory/auth/auth.md` (keep the same name)
3. Create subtopic notes beside it: `Memory/auth/jwt.md`
4. Update `Memory/MEMORY.md` to point to the entry note: `[auth/auth.md](auth/auth.md)`

Do NOT rename the entry note to `index.md`, `overview.md`, or `README.md`.

---

## Reading order

Agents follow this reading order:

1. `Memory/MEMORY.md` -- always first; contains branch summaries and links
2. Branch entry notes (`Memory/<topic>.md` or `Memory/<topic>/<topic>.md`) -- read only relevant ones
3. Subtopic notes (`Memory/<topic>/<subtopic>.md`) -- only if the specific detail is needed

Do not read the full tree on every session. Load only what the task requires.

---

## Linking between notes

Use relative markdown links. No wiki-links.

From MEMORY.md to a flat note:
```markdown
- [stack.md](stack.md) -- Python 3.12, FastAPI, PostgreSQL
```

From MEMORY.md to a branch entry note:
```markdown
- [auth/auth.md](auth/auth.md) -- JWT, bcrypt, refresh token rotation
```

From an entry note to a subtopic note:
```markdown
See [JWT handling](jwt.md) for token structure and expiry.
```

From a branch note to a decision:
```markdown
See [decisions/2025-01-15-use-raw-sql.md](../decisions/2025-01-15-use-raw-sql.md) for rationale.
```

---

## Decisions branch

`Memory/decisions/` uses the same convention but with dated filenames:

```
Memory/
  decisions/
    decisions.md              <- log of all decisions (same-name entry note)
    2025-01-15-use-raw-sql.md <- individual decision
    2025-02-03-drop-redis.md  <- another decision
```

The log (`decisions.md`) is the entry note for the `decisions` branch.
Individual decision files are subtopic notes with dated slugs.

---

## Frontmatter convention

```markdown
---
note_type: branch-entry     # or branch-leaf, durable-memory-root, decision
area: <topic>               # matches folder/file name
updated: 2025-01-15
---
```

All Memory/ notes must have frontmatter. Evidence and Outputs also use frontmatter but with `canonical: false` and `note_type: evidence` or `note_type: output`.

---

## Checklist for a new branch note

- [ ] File is named `<topic>.md` or `<topic>/<topic>.md`
- [ ] YAML frontmatter with `note_type`, `area`, `updated`
- [ ] Has `## Purpose` (one sentence)
- [ ] Has `## Current State` (bullet list of verified facts)
- [ ] Has `## Recent Changes` (YYYY-MM-DD entries, newest first)
- [ ] Has `## Decisions` (links to relevant decision files)
- [ ] Has `## Open Questions` (unresolved items)
- [ ] Under ~150 lines
- [ ] Linked from `Memory/MEMORY.md`

---

## What is NOT a branch note

- `README.md` in any folder
- `INDEX.md` -- not used in this system
- `index.md` -- the entry note pattern uses the folder name, not "index"
- Any file in `Evidence/`, `Outputs/`, or `Sessions/`
