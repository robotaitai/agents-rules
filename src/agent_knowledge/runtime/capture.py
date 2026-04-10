"""Lightweight, file-based capture layer for project events.

Capture items land in Evidence/captures/ as small structured YAML files.
They are evidence/history, never curated memory, and must never be
auto-promoted into Memory/.

Design constraints:
- No database, no daemon, no SQLite.
- Append-only by convention (one file per event).
- Idempotency via minute-level content hash: identical logical events
  within the same minute produce the same filename and are skipped.
- No secrets, tokens, or sensitive local state are recorded.
"""

from __future__ import annotations

import datetime
import hashlib
from pathlib import Path
from typing import Sequence


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _minute_bucket() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def _slug_ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _event_id(event_type: str, source_tool: str, project_slug: str, changed_paths: Sequence[str]) -> str:
    """Compute a stable short ID for deduplication within the same minute."""
    text = "|".join([_minute_bucket(), event_type, source_tool, project_slug, ",".join(sorted(changed_paths))])
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _yaml_list(items: Sequence[str], indent: int = 2) -> str:
    if not items:
        return "  []\n"
    prefix = " " * indent
    return "".join(f"{prefix}- {item}\n" for item in items)


def record(
    captures_dir: Path,
    *,
    event_type: str,
    source_tool: str,
    project_slug: str,
    summary: str,
    changed_paths: Sequence[str] = (),
    touched_branches: Sequence[str] = (),
    related_notes: Sequence[str] = (),
    confidence: str = "cli-confirmed",
    dry_run: bool = False,
) -> tuple[Path | None, str]:
    """Write a capture item file.

    Returns (path, action) where action is 'created', 'exists', or 'dry-run'.
    Idempotent: repeated calls with the same logical event within the same
    minute produce the same event_id, and the second call is skipped.
    """
    event_id = _event_id(event_type, source_tool, project_slug, changed_paths)
    filename = f"{_slug_ts()}-{event_type}-{event_id}.yaml"
    dst = captures_dir / filename

    if not dry_run:
        # Check for an existing capture with the same event_id (any timestamp).
        existing = list(captures_dir.glob(f"*-{event_id}.yaml"))
        if existing:
            return existing[0], "exists"

    if dry_run:
        return None, "dry-run"

    timestamp = _now_iso()
    lines: list[str] = [
        "---\n",
        "note_type: capture\n",
        f"timestamp: {timestamp}\n",
        f"source_tool: {source_tool}\n",
        f"event_type: {event_type}\n",
        f"project_slug: {project_slug}\n",
        f"confidence: {confidence}\n",
        "---\n",
        "\n",
        f"summary: {summary}\n",
    ]
    if changed_paths:
        lines.append("changed_paths:\n")
        lines.append(_yaml_list(changed_paths))
    if touched_branches:
        lines.append("touched_branches:\n")
        lines.append(_yaml_list(touched_branches))
    if related_notes:
        lines.append("related_notes:\n")
        lines.append(_yaml_list(related_notes))

    captures_dir.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(lines))
    return dst, "created"


def list_captures(captures_dir: Path, *, limit: int = 20) -> list[dict]:
    """Return the most recent capture items as dicts (for index/display)."""
    if not captures_dir.is_dir():
        return []
    files = sorted(captures_dir.glob("*.yaml"), reverse=True)[:limit]
    results = []
    for f in files:
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        item: dict = {"path": f.name}
        for line in text.splitlines():
            if line.startswith("---"):
                continue
            if ":" in line and not line.startswith(" ") and not line.startswith("-"):
                key, _, val = line.partition(":")
                item[key.strip()] = val.strip()
        results.append(item)
    return results
