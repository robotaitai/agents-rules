---
name: ontology-inference
description: Infer a project's natural ontology from the actual repo. Use when determining what memory branches to create, how to name them, and how to decompose the project into focused domains.
---

# Ontology Inference

The agent-knowledge system never imposes a fixed ontology. Branch names and structure
must be inferred from the real project, not from templates or generic categories.

This skill covers the inference process: how to read a repo and determine its natural
decomposition into memory branches.

For running the bootstrap script, see `project-ontology-bootstrap`.
For writing the resulting notes, see `project-memory-writing`.

---

## Core principle

**Use the project's own terminology.** Branch names should sound like things this
project's developers would naturally say in a standup. Not "architecture" or "conventions"
-- those are generic catch-all names that hide structure.

Good branch names (from real projects):
- `perception`, `navigation`, `localization`, `safety` (robotics)
- `auth`, `billing`, `notifications`, `search` (web app)
- `training`, `inference`, `data-pipeline`, `evaluation` (ML platform)
- `cli`, `packaging`, `runtime`, `testing` (developer tool)

Bad branch names to avoid:
- `architecture` -- too generic, lumps unrelated concerns
- `conventions` -- usually belongs inside specific branches
- `overview` -- that's what MEMORY.md is
- `misc` -- if it's misc, it doesn't belong in memory yet

---

## Inference signals to read

Read these signals before deciding on branches:

### Manifests and package files
```
package.json, pyproject.toml, Cargo.toml, go.mod, CMakeLists.txt, package.xml
```
What: tech stack, dependencies, declared modules/packages
Branch signals: what frameworks, what services, what subsystems are named here?

### Directory structure (top 2 levels)
What: how the developers decomposed the code
Branch signals: folder names that recur across src/, packages/, services/, apps/ are often natural branches

### Docs and READMEs
```
README.md, AGENTS.md, CLAUDE.md, docs/
```
What: the project's own description of itself
Branch signals: section headers in README.md often map directly to branches

### CI/CD configuration
```
.github/workflows/, .gitlab-ci.yml, Makefile
```
What: what jobs/stages exist; what is tested; what is deployed
Branch signals: job names, build targets, test suites

### Test structure
What: what areas have significant test coverage
Branch signals: test directory names often mirror functional domains

---

## Decision rules

### One branch per functional domain
A functional domain is a coherent cluster of related code, config, and decisions
that a developer would naturally think about as one "thing".

Heuristics:
- If a developer would say "that's a [X] problem", X is probably a branch
- If a folder name appears in commit messages, it is probably a branch
- If it has its own config file, it is probably a branch

### Size check
Start with 2-5 branches. More branches = more maintenance. Only create a branch if:
- There are at least 3 verified facts that belong to it
- It has its own decisions or gotchas
- It is distinct enough that cross-referencing would be confusing

### Flat vs folder
- **Flat** (`stack.md`): when the topic is simple enough to fit in ~60 lines
- **Folder** (`auth/auth.md` + subtopics): when the topic has 2+ distinct subtopics that warrant their own notes

Do not pre-create folders "just in case". Promote to folder only when justified.

---

## Example inference: Python CLI tool

Signals observed:
- `src/tool/cli.py` (click-based CLI)
- `src/tool/runtime/` (several runtime modules)
- `assets/scripts/` (bundled bash scripts)
- `assets/templates/` (project templates)
- `tests/test_cli.py`, `tests/test_packaging.py`
- `pyproject.toml` with hatchling build

Inferred branches:
```
Memory/
  MEMORY.md
  cli.md           -- CLI design, subcommands, click patterns
  packaging.md     -- build system, asset bundling, dist format
  runtime.md       -- Python runtime modules, path resolution
  testing.md       -- test strategy, fixtures, CI
  decisions/
    decisions.md
```

Not created (yet):
- `architecture.md` -- redundant; cli/packaging/runtime already cover it
- `conventions.md` -- put conventions inside the relevant branch notes

---

## Example inference: web app with monorepo

Signals observed:
- `pnpm-workspace.yaml`, `packages/` directory
- `packages/api/`, `packages/web/`, `packages/worker/`
- `packages/api/src/auth/`, `packages/api/src/billing/`, `packages/api/src/search/`
- Stripe imports in billing, JWT in auth
- GitHub Actions: test, build-web, build-api, deploy-api, deploy-web

Inferred branches:
```
Memory/
  MEMORY.md
  stack.md           -- pnpm workspace, Node 20, TypeScript, PostgreSQL
  auth.md            -- JWT, bcrypt, refresh token rotation
  billing.md         -- Stripe, webhook handling, subscription states
  search.md          -- full-text, indexing strategy
  deployments.md     -- GitHub Actions, staging/prod, env vars
  decisions/
    decisions.md
```

---

## Anti-patterns

**Creating branches for obvious things**: if something is clear from reading the repo's own README, it does not need a memory branch. Memory is for things that are NOT obvious.

**Premature folder creation**: a branch with one note does not need a folder. Promote when it grows.

**Overfit to current task**: do not create branches for the current task only. Memory branches should be stable across many sessions.

**Copying README structure**: the README structure and the memory branch structure are often different. READMEs are user-facing docs; memory branches are agent-facing operational knowledge.

---

## Output

After inference, create the branch notes and update MEMORY.md:

```markdown
## Branches

- [cli.md](cli.md) -- click CLI, subcommands, stdin handling
- [packaging.md](packaging.md) -- hatchling, src layout, asset bundling
- [runtime.md](runtime.md) -- path resolution, subprocess wrappers, sync module
- [testing.md](testing.md) -- pytest, parametrized helpers, CI matrix
- [decisions/decisions.md](decisions/decisions.md) -- decision log
```

Then follow `project-memory-writing` to populate each branch note.
