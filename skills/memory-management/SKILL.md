---
name: memory-management
description: Read on sessions start. Manages persistent memory files across conversations. Use when recording learnings, updating MEMORY.md, creating topic files, or when the session-start hook injects memory context.
---

# Auto Memory

You have a persistent auto memory via markdown files. The memory directory path is provided by the session-start hook. (e.g., `~/.cursor/projects/<project-id>/memory/MEMORY.md`).
Its contents persist across conversations.
As you work, consult your memory files to build on previous experience.

## Tree structure

Memory is a **tree**. Load only the branch you need.

```
MEMORY.md                 ← root index — always loaded, stays under 200 lines
<area>.md                 ← one file per functional area (branch node)
<area>/<subtopic>.md      ← deep detail (leaf node), created only when area file > ~150 lines
```

### Reading

1. `MEMORY.md` is always loaded. It is an index only — short entry + relative link per area.
2. At session start, identify which area(s) your task touches.
3. Read the relevant area file(s) before starting work.
4. If an area file links to a sub-topic you need, read that too.
5. Ignore branches unrelated to your task.

### Writing

- **MEMORY.md**: one-line summary + relative link per area. Do not put detail here.
- **Area file** (`<area>.md`): all stable facts, decisions, gotchas, and patterns for that area.
- **Sub-topic file** (`<area>/<subtopic>.md`): create only when an area grows beyond ~150 lines.
  When you create one, replace the inline detail in the area file with a link.

### Example root index entry

```markdown
## OCR Pipeline
Paperwork intake, zip upload, review queue, per-tenant credential resolution.
→ [ocr.md](ocr.md)
```

## How to save memories: <!-- markdownlint-disable-line MD026 -->

- Organize memory semantically by area/topic, not chronologically
- Use the Write and Edit tools to update memory files
- `MEMORY.md` stays under 200 lines — it is an index, not a detail store
- Put detail in area files; put deep detail in sub-topic files under the area directory
- Update or remove memories that turn out to be wrong or outdated
- Do not write duplicate memories. Check existing files before writing a new entry.

## What to save: <!-- markdownlint-disable-line MD026 -->

- Stable patterns and conventions confirmed across multiple interactions
- Key architectural decisions, important file paths, and project structure
- User preferences for workflow, tools, and communication style
- Solutions to recurring problems and debugging insights

## What NOT to save: <!-- markdownlint-disable-line MD026 -->

- Session-specific context (current task details, in-progress work, temporary
  state)
- Information that might be incomplete — verify against project docs before
  writing
- Anything that duplicates or contradicts higher-priority instructions
- Speculative or unverified conclusions from reading a single file

## Explicit user requests: <!-- markdownlint-disable-line MD026 -->
  
- When the user asks you to remember something across sessions (for example, "always
  use bun", "never auto-commit"), save it — no need to wait for multiple
  interactions
- When the user asks to forget or stop remembering something, remove the relevant
  entries from your memory files
