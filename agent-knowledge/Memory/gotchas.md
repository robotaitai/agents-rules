---
note_type: durable-branch
area: gotchas
updated: 2026-04-08
tags:
  - agent-knowledge
  - memory
  - gotchas
---

# Gotchas

Known pitfalls, traps, and non-obvious behaviors.

## Shell Scripts

- `set -euo pipefail` + trailing `[ "$DRY_RUN" -eq 1 ] && log ...` causes exit 1 when test is false. Use `if/then` instead. See [[conventions]].
- `ship.sh` uses `python -m pytest -q` not bare `pytest` -- bare `pytest` fails outside venvs. See [[testing]].

## Python / pip

- macOS system Python refuses `pip install` ("externally managed"). Use brew python + `--user --break-system-packages`, or a venv. See [[stack]].
- Old system pip (e.g. 21.2.4) doesn't support PEP 660 editable installs with `pyproject.toml`. Need pip >= 21.3.
- Venv can get corrupted if multiple Python versions coexist in `.venv/lib/`. Fix: `rm -rf .venv` and recreate with explicit version.

## [[packaging|Packaging]]

- [[architecture|hatchling]] editable installs copy `src/` files to `site-packages`. Changes to `assets/` require rebuild to take effect in the wheel. Source Python files update live.
- pip may silently skip extracting `.mdc` files from wheels. Workaround: [[integrations|inline critical content in Python code]]. See [[decisions#006]].

## Sync

- `stamp_status` regex must use `[ \t]*` not `\s*` to avoid eating newlines across YAML frontmatter fields. Fixed in `runtime/sync.py`.

## See Also

- [[conventions]] -- rules designed to avoid these
- [[testing]] -- tests that catch regressions
- [[decisions|Decisions]] -- why certain workarounds exist
