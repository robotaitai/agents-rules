---
note_type: durable-branch
area: deployments
updated: 2026-04-08
tags:
  - agent-knowledge
  - memory
  - deployments
---

# Deployments

Release, CI, and distribution strategy.

## Version

**0.0.1** (tagged `v0.0.1`). See [[packaging]].

## CI Pipeline

[[testing|GitHub Actions]] (`.github/workflows/ci.yml`):
- Triggered on push/PR to `main`
- Matrix: `ubuntu-latest` + `macos-latest`, Python 3.10/3.12/3.13
- **test** job: pytest with editable install
- **build** job: wheel build + installed [[cli|CLI]] smoke test

## Distribution

- `pip install agent-knowledge` (PyPI-ready, not yet published)
- Build: `python -m build` produces wheel and sdist
- Local dev: `pip install -e ".[dev]"` inside a venv (see [[gotchas]])

## No Server Components

No Docker, no container deployment, no API server. See [[stack]].

## See Also

- [[packaging]] -- build system details
- [[testing]] -- what CI runs
- [[stack]] -- runtime requirements
