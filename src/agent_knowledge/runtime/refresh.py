"""Framework refresh for agent-knowledge project integrations.

Refreshes project-level integration files (hooks, bridge files, AGENTS.md,
.agent-project.yaml fields, STATUS.md fields) to match the currently installed
framework version, without touching Memory/, Evidence/, Sessions/, or any
project-curated knowledge.

Idempotent: safe to run multiple times. When everything is already current,
all items report "up-to-date" and no files are written.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any

from agent_knowledge import __version__
from agent_knowledge.runtime.paths import get_assets_dir


# --------------------------------------------------------------------------- #
# Utilities                                                                    #
# --------------------------------------------------------------------------- #


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(errors="replace") if path.is_file() else ""
    except OSError:
        return ""


def _write(path: Path, content: str, *, dry_run: bool) -> str:
    if dry_run:
        return "dry-run"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "updated"


def _fm_get(text: str, key: str) -> str:
    """Read a field from YAML frontmatter."""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end < 0:
        return ""
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text[4:end], re.MULTILINE)
    return m.group(1).strip().strip("\"'") if m else ""


def _fm_set(text: str, key: str, value: str) -> str:
    """Add or update a field in YAML frontmatter."""
    if not text.startswith("---"):
        # No frontmatter — don't add one silently
        return text
    end = text.find("\n---", 3)
    if end < 0:
        return text
    fm_body = text[4:end]
    rest = text[end + 4:]
    pattern = rf"^{re.escape(key)}:.*$"
    if re.search(pattern, fm_body, re.MULTILINE):
        fm_body = re.sub(pattern, f"{key}: {value}", fm_body, flags=re.MULTILINE)
    else:
        fm_body = fm_body.rstrip("\n") + f"\n{key}: {value}\n"
    return f"---\n{fm_body}\n---{rest}"


def _yaml_set(text: str, key: str, value: str) -> str:
    """Add or update a top-level key in a bare YAML file (no frontmatter delimiters)."""
    pattern = rf"^{re.escape(key)}:.*$"
    quoted = f'"{value}"'
    if re.search(pattern, text, re.MULTILINE):
        return re.sub(pattern, f"{key}: {quoted}", text, flags=re.MULTILINE)
    return text.rstrip("\n") + f"\n{key}: {quoted}\n"


def _normalize_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Per-integration refreshers                                                   #
# --------------------------------------------------------------------------- #


def _refresh_agents_md(repo_root: Path, *, dry_run: bool) -> dict[str, Any]:
    """Refresh the framework header in AGENTS.md while preserving the project section."""
    target = repo_root / "AGENTS.md"
    template_path = get_assets_dir() / "templates" / "project" / "AGENTS.md"

    if not template_path.is_file():
        return {"target": "AGENTS.md", "action": "skip", "detail": "bundled template not found"}

    template = template_path.read_text()
    current = _read_text(target)

    _TODO = "## TODO"
    tmpl_parts = template.split(_TODO, 1)
    tmpl_header = tmpl_parts[0].rstrip("\n")

    if not current:
        action = _write(target, template, dry_run=dry_run)
        return {"target": "AGENTS.md", "action": action, "detail": "created from template"}

    curr_parts = current.split(_TODO, 1)
    curr_header = curr_parts[0].rstrip("\n")
    # Preserve whatever the project has after ## TODO
    curr_tail = (_TODO + curr_parts[1]) if len(curr_parts) > 1 else (
        _TODO + tmpl_parts[1] if len(tmpl_parts) > 1 else ""
    )

    if curr_header.strip() == tmpl_header.strip():
        return {"target": "AGENTS.md", "action": "up-to-date", "detail": "framework header is current"}

    merged = tmpl_header + "\n\n" + curr_tail if curr_tail else tmpl_header
    action = _write(target, merged.rstrip("\n") + "\n", dry_run=dry_run)
    return {"target": "AGENTS.md", "action": action, "detail": "updated framework header, preserved project section"}


def _refresh_cursor_hooks(repo_root: Path, *, dry_run: bool) -> dict[str, Any]:
    """Refresh .cursor/hooks.json from the bundled template (with repo-path substitution)."""
    target = repo_root / ".cursor" / "hooks.json"
    template_path = get_assets_dir() / "templates" / "integrations" / "cursor" / "hooks.json"

    if not template_path.is_file():
        return {"target": ".cursor/hooks.json", "action": "skip", "detail": "bundled template not found"}

    if not target.is_file():
        return {"target": ".cursor/hooks.json", "action": "skip", "detail": "not installed; run: agent-knowledge init"}

    repo_abs = str(repo_root.resolve())
    template_content = template_path.read_text().replace("<repo-path>", repo_abs)
    current_content = target.read_text(errors="replace")

    tmpl_obj = _normalize_json(template_content)
    curr_obj = _normalize_json(current_content)

    if tmpl_obj is None or curr_obj is None:
        return {"target": ".cursor/hooks.json", "action": "skip", "detail": "could not parse JSON"}

    if tmpl_obj == curr_obj:
        return {"target": ".cursor/hooks.json", "action": "up-to-date", "detail": "hooks match current template"}

    action = _write(target, template_content, dry_run=dry_run)
    return {"target": ".cursor/hooks.json", "action": action, "detail": "refreshed from bundled template"}


def _refresh_cursor_rule(repo_root: Path, *, dry_run: bool) -> dict[str, Any]:
    """Refresh .cursor/rules/agent-knowledge.mdc from the bundled template."""
    target = repo_root / ".cursor" / "rules" / "agent-knowledge.mdc"
    template_path = get_assets_dir() / "templates" / "integrations" / "cursor" / "agent-knowledge.mdc"

    if not target.is_file():
        return {"target": ".cursor/rules/agent-knowledge.mdc", "action": "skip", "detail": "not installed; run: agent-knowledge init"}

    if template_path.is_file():
        template = template_path.read_text()
    else:
        # Fall back to the in-code constant from integrations
        from agent_knowledge.runtime.integrations import _CURSOR_RULE as _fallback
        template = _fallback

    current = target.read_text(errors="replace")
    if current.strip() == template.strip():
        return {"target": ".cursor/rules/agent-knowledge.mdc", "action": "up-to-date", "detail": "rule is current"}

    action = _write(target, template, dry_run=dry_run)
    return {"target": ".cursor/rules/agent-knowledge.mdc", "action": action, "detail": "refreshed from bundled template"}


def _refresh_claude_md(repo_root: Path, *, dry_run: bool) -> dict[str, Any]:
    """Refresh CLAUDE.md if it matches the bundled template; warn if customized."""
    target = repo_root / "CLAUDE.md"
    template_path = get_assets_dir() / "templates" / "integrations" / "claude" / "CLAUDE.md"

    if not template_path.is_file():
        return {"target": "CLAUDE.md", "action": "skip", "detail": "bundled template not found"}

    if not target.is_file():
        return {"target": "CLAUDE.md", "action": "skip", "detail": "not installed; run: agent-knowledge init"}

    template = template_path.read_text()
    current = target.read_text(errors="replace")

    if current.strip() == template.strip():
        return {"target": "CLAUDE.md", "action": "up-to-date", "detail": "already matches template"}

    # Check if the opening header matches — if not, it's been customized
    tmpl_lines = template.strip().splitlines()
    curr_lines = current.strip().splitlines()
    header_match = (
        len(curr_lines) >= 3
        and curr_lines[:3] == tmpl_lines[:3]
    )

    if not header_match:
        return {
            "target": "CLAUDE.md",
            "action": "warn",
            "detail": "differs from template and appears customized — review manually or re-run with --force",
        }

    action = _write(target, template, dry_run=dry_run)
    return {"target": "CLAUDE.md", "action": action, "detail": "refreshed from bundled template"}


def _refresh_codex_agents_md(repo_root: Path, *, dry_run: bool) -> dict[str, Any]:
    """Refresh .codex/AGENTS.md from the bundled template."""
    target = repo_root / ".codex" / "AGENTS.md"
    template_path = get_assets_dir() / "templates" / "integrations" / "codex" / "AGENTS.md"

    if not template_path.is_file():
        return {"target": ".codex/AGENTS.md", "action": "skip", "detail": "bundled template not found"}

    if not target.is_file():
        return {"target": ".codex/AGENTS.md", "action": "skip", "detail": "not installed; run: agent-knowledge init"}

    template = template_path.read_text()
    current = target.read_text(errors="replace")

    if current.strip() == template.strip():
        return {"target": ".codex/AGENTS.md", "action": "up-to-date", "detail": "already matches template"}

    action = _write(target, template, dry_run=dry_run)
    return {"target": ".codex/AGENTS.md", "action": action, "detail": "refreshed from bundled template"}


def _refresh_status_md(vault_dir: Path, version: str, *, dry_run: bool) -> dict[str, Any]:
    """Update framework_version and last_system_refresh in STATUS.md frontmatter.

    last_system_refresh is only written when the framework_version is actually
    changing, to preserve idempotency on repeated runs.
    """
    target = vault_dir / "STATUS.md"

    if not target.is_file():
        return {"target": "STATUS.md", "action": "skip", "detail": "file not found"}

    current = target.read_text(errors="replace")
    prior = _fm_get(current, "framework_version")

    # If version is already set correctly, this is a no-op
    if prior == version:
        return {"target": "STATUS.md", "action": "up-to-date", "detail": f"framework_version already {version}"}

    # Version is changing (or absent) — update both fields
    updated = _fm_set(current, "framework_version", version)
    updated = _fm_set(updated, "last_system_refresh", _now_iso())

    action = _write(target, updated, dry_run=dry_run)
    detail = f"set framework_version: {version}"
    if prior:
        detail += f" (was: {prior})"
    return {"target": "STATUS.md", "action": action, "detail": detail}


def _refresh_project_yaml(repo_root: Path, version: str, *, dry_run: bool) -> dict[str, Any]:
    """Update framework_version in .agent-project.yaml."""
    target = repo_root / ".agent-project.yaml"

    if not target.is_file():
        return {"target": ".agent-project.yaml", "action": "skip", "detail": "file not found"}

    current = target.read_text(errors="replace")
    prior = ""
    m = re.search(r'^framework_version:\s*(.+)$', current, re.MULTILINE)
    if m:
        prior = m.group(1).strip().strip("\"'")

    if prior == version:
        return {"target": ".agent-project.yaml", "action": "up-to-date", "detail": f"framework_version already {version}"}

    updated = _yaml_set(current, "framework_version", version)
    action = _write(target, updated, dry_run=dry_run)
    detail = f"set framework_version: {version}"
    if prior:
        detail += f" (was: {prior})"
    return {"target": ".agent-project.yaml", "action": action, "detail": detail}


# --------------------------------------------------------------------------- #
# Staleness check (used by doctor integration)                                 #
# --------------------------------------------------------------------------- #


def is_stale(repo_root: Path) -> tuple[bool, str | None, str]:
    """Check whether the project integration is outdated.

    Returns (stale, prior_version, current_version).
    `stale` is True when the project was last refreshed with an older version.
    """
    vault_dir = repo_root / "agent-knowledge"
    if not vault_dir.is_dir():
        return False, None, __version__

    status_text = _read_text(vault_dir / "STATUS.md")
    prior = _fm_get(status_text, "framework_version")

    if not prior:
        # No version marker at all — legacy project, treat as stale
        return True, None, __version__

    return prior != __version__, prior, __version__


# --------------------------------------------------------------------------- #
# Main entry point                                                             #
# --------------------------------------------------------------------------- #


def run_refresh(
    repo_root: Path,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Refresh the project integration layer to the current framework version.

    Touches only integration bridge files and metadata fields.
    Never reads or writes Memory/, Evidence/, Sessions/, or Outputs/ content.

    Returns a summary dict with action, changes, warnings, and version info.
    """
    from agent_knowledge.runtime.integrations import detect

    version = __version__
    vault_dir = repo_root / "agent-knowledge"
    detected = detect(repo_root)

    # Snapshot prior version before any writes
    status_text = _read_text(vault_dir / "STATUS.md")
    prior_version = _fm_get(status_text, "framework_version") or None

    changes: list[dict[str, Any]] = []
    warnings: list[str] = []

    # AGENTS.md — the primary agent contract file
    r = _refresh_agents_md(repo_root, dry_run=dry_run)
    changes.append(r)
    if r["action"] == "warn":
        warnings.append(f"AGENTS.md: {r['detail']}")

    # Cursor integration (always installed)
    r = _refresh_cursor_hooks(repo_root, dry_run=dry_run)
    changes.append(r)

    r = _refresh_cursor_rule(repo_root, dry_run=dry_run)
    changes.append(r)

    # Claude integration (if detected)
    if detected.get("claude"):
        r = _refresh_claude_md(repo_root, dry_run=dry_run)
        changes.append(r)
        if r["action"] == "warn":
            warnings.append(f"CLAUDE.md: {r['detail']}")

    # Codex integration (if detected)
    if detected.get("codex"):
        r = _refresh_codex_agents_md(repo_root, dry_run=dry_run)
        changes.append(r)

    # STATUS.md — version markers
    if vault_dir.is_dir():
        r = _refresh_status_md(vault_dir, version, dry_run=dry_run)
        changes.append(r)

    # .agent-project.yaml — version field
    r = _refresh_project_yaml(repo_root, version, dry_run=dry_run)
    changes.append(r)

    # Determine overall action
    active_actions = {c["action"] for c in changes}
    if dry_run:
        action = "dry-run"
    elif active_actions <= {"up-to-date", "skip", "warn"}:
        action = "up-to-date"
    else:
        action = "refreshed"

    return {
        "action": action,
        "framework_version": version,
        "prior_version": prior_version,
        "dry_run": dry_run,
        "integrations_detected": [k for k, v in detected.items() if v],
        "changes": changes,
        "warnings": warnings,
    }
