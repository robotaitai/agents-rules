---
name: clean-web-import
description: Import web content cleanly into Evidence/imports/ with clutter removed. Use when importing a URL or HTML file as evidence for the project.
---

# Clean Web Import

Reduces noisy web content before it lands in the knowledge vault.
Strips navigation, ads, footers, and boilerplate. Produces readable markdown
stored in `Evidence/imports/` -- clearly marked non-canonical.

---

## When to use

- Importing API documentation from a URL
- Importing a blog post, spec, or reference page as project evidence
- Importing any HTML document as background material
- Any time you'd otherwise paste a URL directly into a note

Do NOT use for:
- Internal project documents (use `Evidence/raw/` directly)
- Content that needs to stay verbatim (use raw import)
- Large datasets or binary files

---

## CLI usage

```bash
agent-knowledge clean-import <url-or-file> --project .
```

Options:
- `--project <dir>` -- project root (default: cwd)
- `--slug <name>` -- override output filename (default: derived from URL/title)
- `--output-dir <dir>` -- override output directory (default: `agent-knowledge/Evidence/imports/`)
- `--dry-run` -- preview without writing
- `--json` -- machine-readable output

The command:
1. Fetches the URL or reads the local HTML file
2. Extracts the main content (strips nav, header, footer, ads, scripts)
3. Converts to clean markdown
4. Writes to `Evidence/imports/<slug>.md` with proper frontmatter
5. Prints the output path

---

## Output format

```markdown
---
note_type: evidence
source: https://docs.example.com/api/rate-limits
title: Rate Limits - Example API
imported: 2025-01-15T14:30:00Z
canonical: false
---

# Rate Limits - Example API

(cleaned markdown content)
```

---

## What the cleaner removes

| Element | Action |
|---------|--------|
| `<nav>`, `<header>`, `<footer>` | Removed entirely |
| `<aside>` | Removed |
| `<script>`, `<style>` | Removed |
| `<button>`, `<form>`, `<select>` | Removed |
| Cookie banners, overlays | Removed (best effort) |
| Duplicate whitespace | Collapsed |

## What the cleaner keeps

| Element | Converted to |
|---------|-------------|
| `<h1>` - `<h6>` | `#` - `######` |
| `<p>` | Paragraph |
| `<ul>`, `<li>` | Markdown list |
| `<pre>`, `<code>` | Fenced code block |
| `<blockquote>` | `>` |
| `<a href>` | `[text](url)` |

---

## Manual clean import (without the CLI)

If you prefer to import manually:

1. Fetch the page and copy the text content
2. Remove navigation and boilerplate
3. Create `agent-knowledge/Evidence/imports/<slug>.md`
4. Add the required frontmatter:
   ```yaml
   ---
   note_type: evidence
   source: <url>
   imported: <YYYY-MM-DDThh:mm:ssZ>
   canonical: false
   ---
   ```
5. Paste the cleaned content below the frontmatter

---

## After import: distilling to memory

After importing, do NOT copy content directly to Memory/.
Follow the evidence promotion process:

1. Read the imported note
2. Identify facts that are stable and relevant to the project
3. Verify each fact is still true (docs go stale)
4. Write only verified, stable facts to the relevant Memory/ branch
5. Add a Recent Changes entry: `2025-01-15 - Updated from imported API docs`

See `evidence-handling` skill for full promotion rules.

---

## Freshness and expiry

Imported web content goes stale. Add a review reminder comment if the content
is time-sensitive:

```markdown
---
note_type: evidence
source: https://...
imported: 2025-01-15T14:30:00Z
canonical: false
review_by: 2025-04-15
---
```

When `imported:` is older than 90 days, treat the content as potentially outdated
before promoting any facts to Memory/.
