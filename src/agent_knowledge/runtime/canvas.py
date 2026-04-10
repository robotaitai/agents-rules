"""Optional Obsidian Canvas export for agent-knowledge vaults.

Generates a .canvas file (Obsidian Canvas JSON) that shows the knowledge
graph as a spatial canvas. Nodes are memory branch notes; edges are
links between them.

This is a generated Output: non-canonical and regeneratable.
The system works fully without this file.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .index import build_index, _extract_frontmatter

_FOLDER_COLORS = {
    "Memory": "2",     # green
    "Evidence": "6",   # purple
    "Outputs": "4",    # yellow/orange
    "Sessions": "5",   # pink
}

_NODE_WIDTH = 220
_NODE_HEIGHT = 90
_BRANCH_RADIUS = 400
_LEAF_OFFSET = 260


def _extract_links(text: str, note_path: str) -> list[str]:
    """Extract relative markdown link targets from note text."""
    base_dir = str(Path(note_path).parent)
    links: list[str] = []
    for match in re.finditer(r"\[(?:[^\]]*)\]\(([^)#]+\.md)\)", text):
        target = match.group(1)
        # Resolve relative to note location
        if not target.startswith(("http://", "https://")):
            resolved = str((Path(base_dir) / target).resolve().relative_to(Path(".").resolve())) if base_dir != "." else target
            # Just keep as-is and normalise
            resolved = (Path(base_dir) / target).as_posix().lstrip("./")
            links.append(resolved)
    return links


def _layout_nodes(notes: list[dict]) -> dict[str, tuple[int, int]]:
    """Assign (x, y) positions. Memory branches radiate from center; others surround."""
    positions: dict[str, tuple[int, int]] = {}

    memory_roots = [n for n in notes if n["path"] == "Memory/MEMORY.md"]
    memory_branches = [
        n for n in notes
        if n["folder"] == "Memory" and n["is_branch_entry"] and n["path"] != "Memory/MEMORY.md"
    ]
    memory_leaves = [
        n for n in notes
        if n["folder"] == "Memory" and not n["is_branch_entry"] and "decisions" not in n["path"]
    ]
    memory_decisions = [n for n in notes if "decisions" in n["path"] and n["folder"] == "Memory"]
    non_memory = [n for n in notes if n["folder"] != "Memory"]

    # Root at center
    for n in memory_roots:
        positions[n["path"]] = (0, 0)

    # Branches in a circle around root
    count = len(memory_branches)
    for i, n in enumerate(memory_branches):
        angle = (2 * math.pi * i / max(count, 1)) - math.pi / 2
        x = int(_BRANCH_RADIUS * math.cos(angle))
        y = int(_BRANCH_RADIUS * math.sin(angle))
        positions[n["path"]] = (x, y)

    # Leaf notes near their branch
    for i, n in enumerate(memory_leaves):
        angle = (2 * math.pi * i / max(len(memory_leaves), 1))
        x = int((_BRANCH_RADIUS + _LEAF_OFFSET) * math.cos(angle))
        y = int((_BRANCH_RADIUS + _LEAF_OFFSET) * math.sin(angle))
        positions[n["path"]] = (x, y)

    # Decisions cluster bottom-left
    for i, n in enumerate(memory_decisions):
        positions[n["path"]] = (-700 + i * (_NODE_WIDTH + 20), 700)

    # Non-memory: ring at outer radius
    outer_radius = _BRANCH_RADIUS + _LEAF_OFFSET + 300
    count_nm = len(non_memory)
    for i, n in enumerate(non_memory):
        angle = (2 * math.pi * i / max(count_nm, 1)) + math.pi / 4
        x = int(outer_radius * math.cos(angle))
        y = int(outer_radius * math.sin(angle))
        positions[n["path"]] = (x, y)

    return positions


def build_canvas(vault_dir: Path) -> dict[str, Any]:
    """Build the canvas JSON structure from the vault index."""
    index = build_index(vault_dir)
    notes = index["notes"]

    positions = _layout_nodes(notes)

    nodes: list[dict] = []
    edges: list[dict] = []
    node_ids: dict[str, str] = {}

    for i, note in enumerate(notes):
        node_id = f"n{i}"
        node_ids[note["path"]] = node_id
        pos = positions.get(note["path"], (i * (_NODE_WIDTH + 20), 1200))

        color = _FOLDER_COLORS.get(note["folder"], "1")
        nodes.append(
            {
                "id": node_id,
                "type": "file",
                "file": note["path"],
                "x": pos[0],
                "y": pos[1],
                "width": _NODE_WIDTH,
                "height": _NODE_HEIGHT,
                "color": color,
            }
        )

    # Extract edges from markdown links in Memory/ notes
    edge_count = 0
    seen_edges: set[tuple[str, str]] = set()

    for note in notes:
        if note["folder"] != "Memory":
            continue
        md_path = vault_dir / note["path"]
        if not md_path.is_file():
            continue
        try:
            text = md_path.read_text(errors="replace")
        except OSError:
            continue

        for link in _extract_links(text, note["path"]):
            # Normalise: try to find the target in our note set
            target_path = None
            for candidate in notes:
                if candidate["path"] == link or candidate["path"].endswith(link):
                    target_path = candidate["path"]
                    break
            if target_path is None:
                continue
            if note["path"] == target_path:
                continue
            key = (note["path"], target_path)
            if key in seen_edges:
                continue
            seen_edges.add(key)

            from_id = node_ids.get(note["path"])
            to_id = node_ids.get(target_path)
            if from_id and to_id:
                edges.append(
                    {
                        "id": f"e{edge_count}",
                        "fromNode": from_id,
                        "toNode": to_id,
                        "fromSide": "right",
                        "toSide": "left",
                    }
                )
                edge_count += 1

    return {"nodes": nodes, "edges": edges}


def export_canvas(
    vault_dir: Path,
    output_path: Path | None = None,
    *,
    dry_run: bool = False,
) -> tuple[Path, str]:
    """Generate the Obsidian Canvas file.

    Returns (path, action) where action is 'created', 'updated', or 'dry-run'.
    The canvas is an Output and is non-canonical.
    """
    if output_path is None:
        output_path = vault_dir / "Outputs" / "knowledge-export.canvas"

    if dry_run:
        return output_path, "dry-run"

    canvas = build_canvas(vault_dir)
    content = json.dumps(canvas, indent=2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    existed = output_path.exists()
    output_path.write_text(content, encoding="utf-8")
    return output_path, "updated" if existed else "created"
