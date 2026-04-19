---
name: absorb-repo
description: Ingest an entire repository into agent-knowledge by running `/absorb` once and helping triage the resulting manifest into Memory branches. Use when the user asks to onboard an existing project, pull all project docs into Memory, or bring a legacy repo into the vault. For a single file or narrow subset, use `/absorb` directly instead.
allowed-tools: Bash
---

# absorb-repo

## Purpose

Drive a full-repo onboarding pass into the agent-knowledge vault.

The CLI (`agent-knowledge absorb`, exposed as the `/absorb` slash
command) already discovers knowledge-bearing files
(`README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, ADRs, `docs/`,
`decisions/`, etc.) and copies them into `Evidence/imports/` as
non-canonical evidence. This skill is the **triage layer on top**: it
runs `/absorb` once, then walks the generated manifest and decides what
deserves promotion into `Memory/`.

The skill never re-implements discovery — `/absorb` owns that. It
focuses on the work `/absorb` explicitly leaves to the agent:
interpreting evidence and writing durable memory.

## Prerequisites

- Target repo must already be initialised for agent-knowledge
  (`./agent-knowledge/` present). The `/absorb` slash command must also
  be installed — either `.claude/commands/absorb.md` (Claude Code) or
  `.cursor/commands/absorb.md` (Cursor).
- If `/absorb` is not available in the current project, stop and tell
  the user to run `agent-knowledge init` first.

## Instructions

### Step 1 — Run `/absorb` at the repo root

Invoke the `/absorb` slash command once from the repo root. Do not try
to pass a file list — the CLI scans the whole project itself and
ignores unexpected arguments. Let it run to completion.

Output locations after it finishes:
- `Evidence/imports/` — raw copies with metadata headers
- `Memory/decisions/decisions.md` — parsed ADR entries (if any)
- `Outputs/absorb-manifest.md` — manifest of what was imported/skipped
- `History/events.ndjson` — absorb event appended

### Step 2 — Read the manifest

Read `./agent-knowledge/Outputs/absorb-manifest.md`. It lists:
- Files copied into `Evidence/imports/`
- Files skipped (already present, ignored, or boilerplate)
- Decisions parsed from ADR-shaped files

Skim the manifest before touching Memory — it is the cheapest way to
understand the shape of the repo's knowledge.

### Step 3 — Triage into Memory

For each imported file, decide where stable facts belong:

| Content shape | Destination |
|---|---|
| Architectural decision / ADR | `Memory/decisions/decisions.md` (often already populated by absorb — verify and enrich) |
| System component or service description | `Memory/<branch>.md` — create or update the relevant branch note |
| Changelog / release history | Spot-check `History/events.ndjson`; promote only durable milestones |
| Onboarding / contribution / setup doc | Extract durable facts only; leave process-heavy content in Evidence |
| Boilerplate (license headers, stubs, TOC-only files) | Leave in Evidence, do not promote |

Use the `project-memory-writing` and `branch-note-convention` skills for
the actual Memory writes — keep branch notes small, curated, and
cross-linked. Use `memory-management` to decide whether a branch
already exists or a new one is justified.

### Step 4 — Update `MEMORY.md`

If you created new branch notes, add a one-line entry for each under
the relevant section of `Memory/MEMORY.md`. Keep it an index, not a
summary.

### Step 5 — Finish with `/memory-update`

Run `/memory-update` to sync the vault, regenerate the index, and log
a session summary. This closes the onboarding loop and makes the new
branches discoverable to future sessions.

## Notes

- **Absorb is idempotent.** Re-running `/absorb` is safe — files
  already in `Evidence/imports/` are skipped. Triage, however, is not
  idempotent; be deliberate about what you promote.
- **Evidence is not Memory.** `Evidence/imports/` stays non-canonical.
  The manifest gives you the raw surface; `Memory/` captures the
  durable facts you have deliberately curated.
- **Large repos.** If the manifest runs to hundreds of imports, triage
  by directory rather than file-by-file: identify the three or four
  directories that carry the real knowledge and focus there. Everything
  unpromoted stays usefully searchable in Evidence.
- **Single files or a narrow subset.** Do not use this skill — call
  `/absorb` directly. This skill is specifically the whole-repo
  onboarding workflow.
