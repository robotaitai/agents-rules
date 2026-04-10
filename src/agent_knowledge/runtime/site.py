"""Static site generation for agent-knowledge vaults.

Pipeline:
  1. build_site_data() -> structured dict (site data model)
  2. Write Outputs/site/data/knowledge.json
  3. _render_html()    -> complete index.html with data embedded
  4. Write Outputs/site/index.html

Generated output is non-canonical. Memory/ remains the source of truth.
The site is a presentation layer, not the authoritative knowledge store.
"""

from __future__ import annotations

import datetime
import html as html_mod
import json
import re
from pathlib import Path
from typing import Any

from .index import (
    _CANONICAL_FOLDERS,
    _FOLDER_ORDER,
    _extract_frontmatter,
    _first_content_lines,
    _note_title,
    build_index,
)

_SITE_SCHEMA_VERSION = "1"


# --------------------------------------------------------------------------- #
# Section extraction                                                           #
# --------------------------------------------------------------------------- #


def _extract_section(text: str, name: str) -> str:
    """Extract body of a markdown ## section (everything until the next ##)."""
    pattern = rf"^##\s+{re.escape(name)}\s*$(.+?)(?=^##|\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _parse_bullets(text: str, section_name: str) -> list[str]:
    """Return bullet items from a named section as a plain list of strings."""
    section = _extract_section(text, section_name)
    items: list[str] = []
    for line in section.splitlines():
        s = line.strip()
        if s.startswith(("- ", "* ")):
            items.append(s[2:].strip())
        elif s.startswith("+ "):
            items.append(s[2:].strip())
    return items


def _parse_recent_changes(text: str) -> list[dict[str, str]]:
    """Parse the Recent Changes section into structured dicts."""
    section = _extract_section(text, "Recent Changes")
    items: list[dict[str, str]] = []
    pattern = re.compile(r"[-*]\s+(\d{4}-\d{2}-\d{2})\s*[-:—–]\s*(.+)")
    for line in section.splitlines():
        m = pattern.match(line.strip())
        if m:
            items.append({"date": m.group(1), "text": m.group(2).strip()})
    return items


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            return text[end + 4:].lstrip("\n")
    return text


# --------------------------------------------------------------------------- #
# Minimal markdown → HTML (no external deps)                                  #
# --------------------------------------------------------------------------- #


def _md_to_html(text: str) -> str:
    """Minimal markdown-to-HTML for note rendering in the generated site."""
    text = _strip_frontmatter(text)
    lines = text.split("\n")
    out: list[str] = []
    in_code = False
    in_ul = False
    in_ol = False
    code_buf: list[str] = []
    code_lang = ""

    def flush_list() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def inline(s: str) -> str:
        s = html_mod.escape(s)
        # Bold
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"__(.+?)__", r"<strong>\1</strong>", s)
        # Italic
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"_(.+?)_", r"<em>\1</em>", s)
        # Inline code
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        # Links
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        # Wiki-links (strip them gracefully)
        s = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", s)
        s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
        return s

    for line in lines:
        if line.startswith("```"):
            flush_list()
            if in_code:
                out.append(html_mod.escape("\n".join(code_buf)))
                out.append("</code></pre>")
                code_buf = []
                in_code = False
                code_lang = ""
            else:
                code_lang = line[3:].strip()
                cls = f' class="language-{code_lang}"' if code_lang else ""
                out.append(f'<pre><code{cls}>')
                in_code = True
            continue

        if in_code:
            code_buf.append(line)
            continue

        if re.match(r"^#{1,6}\s", line):
            flush_list()
            level = len(re.match(r"^(#+)", line).group(1))
            content = line.lstrip("#").strip()
            out.append(f"<h{level}>{html_mod.escape(content)}</h{level}>")
        elif line.startswith("> "):
            flush_list()
            out.append(f"<blockquote><p>{inline(line[2:])}</p></blockquote>")
        elif re.match(r"^[-*+]\s", line):
            if not in_ul:
                flush_list()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line[2:])}</li>")
        elif re.match(r"^\d+\.\s", line):
            if not in_ol:
                flush_list()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(re.sub(r'^\d+\.\s+', '', line))}</li>")
        elif re.match(r"^---+$", line.strip()) or re.match(r"^\*\*\*+$", line.strip()):
            flush_list()
            out.append("<hr>")
        elif line.strip() == "":
            flush_list()
            out.append("")
        else:
            flush_list()
            out.append(f"<p>{inline(line)}</p>")

    flush_list()
    if in_code and code_buf:
        out.append(html_mod.escape("\n".join(code_buf)))
        out.append("</code></pre>")

    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Data model construction                                                      #
# --------------------------------------------------------------------------- #


def _read_status(vault_dir: Path) -> dict[str, str]:
    status_file = vault_dir / "STATUS.md"
    if not status_file.is_file():
        return {}
    return _extract_frontmatter(status_file.read_text(errors="replace"))


def _read_note(vault_dir: Path, rel_path: str) -> str:
    p = vault_dir / rel_path
    try:
        return p.read_text(errors="replace") if p.is_file() else ""
    except OSError:
        return ""


def _build_note_data(
    vault_dir: Path,
    meta: dict[str, Any],
    *,
    include_html: bool = True,
) -> dict[str, Any]:
    """Build full data dict for a single note."""
    raw = _read_note(vault_dir, meta["path"])
    fm = _extract_frontmatter(raw)

    data: dict[str, Any] = {
        "path": meta["path"],
        "title": meta["title"],
        "folder": meta["folder"],
        "canonical": meta["canonical"],
        "note_type": meta.get("note_type", fm.get("note_type", "unknown")),
        "area": meta.get("area", fm.get("area", "")),
        "is_branch_entry": meta.get("is_branch_entry", False),
        "updated": fm.get("updated", fm.get("date", "")),
        "summary": meta.get("summary", ""),
    }

    if include_html:
        data["html"] = _md_to_html(raw)

    return data


def _build_branch_data(vault_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    """Build rich data for a Memory branch entry note."""
    raw = _read_note(vault_dir, meta["path"])
    fm = _extract_frontmatter(raw)

    purpose = _extract_section(raw, "Purpose")
    if not purpose:
        purpose = _first_content_lines(raw, max_chars=200)

    return {
        "path": meta["path"],
        "title": meta["title"],
        "folder": "Memory",
        "canonical": True,
        "note_type": fm.get("note_type", "branch-entry"),
        "area": fm.get("area", meta.get("area", "")),
        "is_branch_entry": True,
        "updated": fm.get("updated", ""),
        "summary": meta.get("summary", purpose[:150] if purpose else ""),
        "purpose": purpose,
        "current_state": _parse_bullets(raw, "Current State"),
        "recent_changes": _parse_recent_changes(raw),
        "open_questions": _parse_bullets(raw, "Open Questions"),
        "decision_links": _parse_bullets(raw, "Decisions"),
        "leaves": [],
        "html": _md_to_html(raw),
    }


def _build_decision_data(vault_dir: Path, meta: dict[str, Any]) -> dict[str, Any]:
    """Build data for a decision file."""
    raw = _read_note(vault_dir, meta["path"])
    fm = _extract_frontmatter(raw)

    what = _extract_section(raw, "What")
    why = _extract_section(raw, "Why")

    # Derive a clean title from the filename if the heading isn't found
    title = meta["title"]
    if title.lower().startswith("decision:"):
        title = title[9:].strip()

    return {
        "path": meta["path"],
        "title": title,
        "folder": "Memory",
        "canonical": True,
        "note_type": "decision",
        "date": fm.get("date", ""),
        "status": fm.get("status", "active"),
        "what": what[:200] if what else "",
        "why": why[:200] if why else "",
        "summary": what[:120] if what else meta.get("summary", ""),
        "updated": fm.get("date", fm.get("updated", "")),
        "html": _md_to_html(raw),
    }


def build_site_data(
    vault_dir: Path,
    *,
    include_evidence: bool = True,
    include_sessions: bool = False,
) -> dict[str, Any]:
    """Build the complete site data model from the vault.

    Returns a structured dict ready to be serialized as knowledge.json.
    Memory/ is primary; Evidence/Outputs are marked non-canonical.
    """
    status = _read_status(vault_dir)
    index = build_index(vault_dir)
    all_notes = index["notes"]

    generated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    project = {
        "name": status.get("project", vault_dir.name),
        "slug": status.get("slug", vault_dir.name),
        "profile": status.get("profile", "unknown"),
        "onboarding": status.get("onboarding", "unknown"),
        "vault_path": str(vault_dir),
        "last_updated": status.get("last_project_sync", ""),
    }

    # --- Separate notes by folder ---
    memory_notes = [n for n in all_notes if n["folder"] == "Memory"]
    evidence_notes = [n for n in all_notes if n["folder"] == "Evidence"]
    output_notes = [n for n in all_notes if n["folder"] == "Outputs"]
    session_notes = [n for n in all_notes if n["folder"] == "Sessions"]

    # --- Branches: Memory entry notes (excluding decisions/) ---
    branch_metas = [
        n for n in memory_notes
        if n["is_branch_entry"]
        and "decisions" not in n["path"].lower()
        and n["path"] != "Memory/MEMORY.md"
    ]

    # Leaf notes: non-entry Memory notes (excluding decisions/)
    leaf_metas = [
        n for n in memory_notes
        if not n["is_branch_entry"]
        and "decisions" not in n["path"].lower()
        and n["path"] != "Memory/MEMORY.md"
    ]

    # Flat (non-folder) Memory notes: treat as their own branch
    flat_metas = [
        n for n in memory_notes
        if not n["is_branch_entry"]
        and "decisions" not in n["path"].lower()
        and n["path"] != "Memory/MEMORY.md"
        and "/" not in n["path"].replace("Memory/", "", 1)
    ]

    # Build branch data
    branches: list[dict[str, Any]] = []
    for meta in branch_metas:
        branch = _build_branch_data(vault_dir, meta)
        # Attach leaves from the same folder
        branch_folder_prefix = str(Path(meta["path"]).parent.as_posix()) + "/"
        branch["leaves"] = [
            _build_note_data(vault_dir, lm)
            for lm in leaf_metas
            if lm["path"].startswith(branch_folder_prefix)
        ]
        branches.append(branch)

    # Flat notes that are not leaves of a folder-branch
    covered_paths = {b["path"] for b in branches}
    covered_paths.update(
        lf["path"] for b in branches for lf in b["leaves"]
    )
    for meta in flat_metas:
        if meta["path"] not in covered_paths:
            branches.append(_build_branch_data(vault_dir, meta))

    # Sort branches: root MEMORY.md summary first, then alphabetical
    branches.sort(key=lambda b: (0 if "MEMORY" in b["path"] else 1, b["title"]))

    # --- Decisions ---
    decision_metas = [
        n for n in memory_notes
        if "decisions" in n["path"].lower()
        and n["path"] != "Memory/decisions/decisions.md"
    ]
    decisions = sorted(
        [_build_decision_data(vault_dir, m) for m in decision_metas],
        key=lambda d: d.get("date", ""),
        reverse=True,
    )

    # --- Global recent changes: merge across all branches, sorted ---
    all_changes: list[dict[str, str]] = []
    for branch in branches:
        for change in branch.get("recent_changes", []):
            all_changes.append({
                "date": change["date"],
                "text": change["text"],
                "branch": branch["title"],
                "branch_path": branch["path"],
            })
    all_changes.sort(key=lambda c: c["date"], reverse=True)
    recent_changes_global = all_changes[:20]

    # --- Evidence ---
    evidence: list[dict[str, Any]] = []
    if include_evidence:
        for meta in evidence_notes:
            raw = _read_note(vault_dir, meta["path"])
            fm = _extract_frontmatter(raw)
            evidence.append({
                "path": meta["path"],
                "title": meta["title"],
                "folder": "Evidence",
                "canonical": False,
                "note_type": fm.get("note_type", "evidence"),
                "source": fm.get("source", ""),
                "imported": fm.get("imported", fm.get("extracted", "")),
                "summary": meta.get("summary", ""),
                "html": _md_to_html(raw),
            })

    # --- Outputs (only list, don't embed content) ---
    outputs: list[dict[str, Any]] = []
    for meta in output_notes:
        raw = _read_note(vault_dir, meta["path"])
        fm = _extract_frontmatter(raw)
        outputs.append({
            "path": meta["path"],
            "title": meta["title"],
            "folder": "Outputs",
            "canonical": False,
            "note_type": fm.get("note_type", "output"),
            "summary": meta.get("summary", ""),
        })

    # --- Warnings ---
    warnings: list[str] = []
    status_raw_text = _read_note(vault_dir, "STATUS.md") if (vault_dir / "STATUS.md").is_file() else ""
    warn_section = _extract_section(status_raw_text, "Warnings")
    if warn_section:
        for line in warn_section.splitlines():
            s = line.strip()
            if s.startswith(("- ", "* ")):
                warnings.append(s[2:].strip())
            elif s and not s.startswith("#"):
                warnings.append(s)

    return {
        "schema": _SITE_SCHEMA_VERSION,
        "generated": generated,
        "project": project,
        "warnings": warnings,
        "branches": branches,
        "decisions": decisions,
        "recent_changes_global": recent_changes_global,
        "evidence": evidence,
        "outputs": outputs,
        "stats": {
            "branch_count": len(branches),
            "decision_count": len(decisions),
            "evidence_count": len(evidence),
            "output_count": len(outputs),
            "note_count": index["note_count"],
        },
    }


# --------------------------------------------------------------------------- #
# HTML template                                                                #
# --------------------------------------------------------------------------- #

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>__PROJECT_NAME__ — Knowledge</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d1117;--surface:#161b22;--surface-2:#1c2128;--surface-3:#21262d;
  --border:#30363d;--border-2:#21262d;
  --text:#e6edf3;--text-2:#cdd9e5;--muted:#8b949e;--muted-2:#6e7681;
  --accent:#58a6ff;--accent-muted:#1f6feb;
  --mem-bg:#031d44;--mem-fg:#79c0ff;--mem-border:#1f6feb;
  --ev-bg:#1b0045;--ev-fg:#d2a8ff;--ev-border:#6e40c9;
  --out-bg:#2d1b00;--out-fg:#e3b341;--out-border:#9e6a03;
  --ses-bg:#1a0000;--ses-fg:#ff7b72;--ses-border:#b62324;
  --ok:#3fb950;--warn-bg:#3a2000;--warn-fg:#d29922;
  --radius:8px;--radius-sm:5px;
}
html,body{height:100%;overflow:hidden}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;font-size:14px;line-height:1.6}

/* ---- LAYOUT ---- */
#root{display:grid;grid-template-columns:268px 1fr;grid-template-rows:100vh;overflow:hidden}

/* ---- SIDEBAR ---- */
#sidebar{background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden}
.sidebar-header{padding:14px 14px 12px;border-bottom:1px solid var(--border);flex-shrink:0}
.sidebar-logo{display:flex;align-items:center;gap:7px;color:var(--muted);font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;margin-bottom:10px}
.sidebar-logo-mark{width:16px;height:16px;background:var(--accent);border-radius:3px;display:inline-flex;align-items:center;justify-content:center;color:#0d1117;font-weight:900;font-size:9px;flex-shrink:0}
.sidebar-project-name{font-size:15px;font-weight:700;color:var(--text);margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sidebar-meta{display:flex;gap:5px;flex-wrap:wrap;align-items:center}
#sidebar-tree{flex:1;overflow-y:auto;padding:6px 0}
.tree-group{margin-bottom:2px}
.tree-group-header{padding:7px 12px 5px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted-2);display:flex;align-items:center;gap:7px;user-select:none}
.tree-group-header .count{background:var(--surface-2);border-radius:9px;padding:0 5px;font-size:9px;margin-left:auto}
.tree-item{padding:5px 12px 5px 18px;cursor:pointer;color:var(--muted);font-size:13px;display:flex;align-items:center;gap:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:background .1s,color .1s;border-radius:0}
.tree-item:hover{background:var(--surface-2);color:var(--text-2)}
.tree-item.active{background:var(--surface-2);color:var(--accent)}
.tree-item.leaf{padding-left:30px;font-size:12px}
.tree-item.branch{font-weight:500}
.tree-item-icon{font-size:10px;flex-shrink:0;opacity:.7}
.tree-item-label{overflow:hidden;text-overflow:ellipsis;flex:1}
.tree-sep{height:1px;background:var(--border-2);margin:6px 12px}
.sidebar-footer{padding:9px 12px;border-top:1px solid var(--border);flex-shrink:0;font-size:10px;color:var(--muted-2);line-height:1.5}

/* ---- MAIN ---- */
#main{display:flex;flex-direction:column;overflow:hidden}

/* ---- TOPBAR ---- */
#topbar{height:46px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 20px;gap:14px;flex-shrink:0}
#breadcrumb{flex:1;font-size:13px;color:var(--muted);display:flex;align-items:center;gap:5px;overflow:hidden}
#breadcrumb a{color:var(--accent);text-decoration:none;flex-shrink:0}
#breadcrumb a:hover{text-decoration:underline}
.bc-sep{color:var(--muted-2);flex-shrink:0}
.bc-current{color:var(--text-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#topbar-tabs{display:flex;gap:3px;flex-shrink:0}
.tab-btn{background:none;border:1px solid transparent;border-radius:var(--radius-sm);color:var(--muted);cursor:pointer;font-size:12px;padding:4px 11px;transition:all .15s}
.tab-btn:hover{color:var(--text);background:var(--surface-2)}
.tab-btn.active{color:var(--accent);border-color:var(--mem-border);background:var(--mem-bg)}

/* ---- CONTENT ---- */
#content{flex:1;overflow-y:auto;padding:0}
.view-wrap{max-width:900px;margin:0 auto;padding:28px 32px}

/* ---- OVERVIEW ---- */
.ov-header{padding-bottom:20px;margin-bottom:24px;border-bottom:1px solid var(--border)}
.ov-title{font-size:26px;font-weight:800;letter-spacing:-.5px;margin-bottom:9px}
.ov-meta{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:12px;color:var(--muted)}
.ov-meta-item{display:flex;align-items:center;gap:4px}
.status-ok{color:var(--ok)}
.status-pending{color:var(--warn-fg)}
.sep-dot{color:var(--border)}

.warnings-box{background:var(--warn-bg);border:1px solid var(--warn-fg);border-radius:var(--radius);padding:13px 15px;margin-bottom:22px}
.warnings-box h3{color:var(--warn-fg);font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:7px}
.warn-item{color:var(--warn-fg);font-size:13px;margin-bottom:4px;display:flex;gap:7px}
.warn-item::before{content:"⚠";flex-shrink:0}

.section{margin-bottom:32px}
.section-heading{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin-bottom:13px;display:flex;align-items:center;gap:8px}
.section-heading::after{content:"";flex:1;height:1px;background:var(--border)}

.branch-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:11px}
.branch-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 15px;cursor:pointer;transition:border-color .15s,background .15s}
.branch-card:hover{border-color:var(--accent);background:var(--surface-2)}
.branch-card-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:7px;gap:8px}
.branch-card-title{font-weight:600;font-size:14px;color:var(--text);flex:1}
.branch-card-purpose{font-size:12px;color:var(--muted);line-height:1.5;margin-bottom:8px}
.branch-card-foot{font-size:11px;color:var(--muted-2);display:flex;gap:10px}

.changes-list{display:flex;flex-direction:column;gap:1px}
.change-row{display:grid;grid-template-columns:90px auto 1fr;gap:10px;align-items:baseline;padding:6px 0;border-bottom:1px solid var(--border-2);font-size:13px}
.change-date{color:var(--muted-2);font-size:11px;font-variant-numeric:tabular-nums;white-space:nowrap}
.change-branch-tag{color:var(--mem-fg);font-size:10px;font-weight:600;background:var(--mem-bg);border-radius:9px;padding:1px 7px;white-space:nowrap}
.change-text{color:var(--text-2)}

.decision-list{display:flex;flex-direction:column;gap:6px}
.decision-item{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--mem-border);border-radius:var(--radius-sm);padding:9px 12px;cursor:pointer;transition:border-color .15s}
.decision-item:hover{border-color:var(--accent)}
.decision-item-title{font-size:13px;font-weight:500;color:var(--accent);margin-bottom:3px}
.decision-item-what{font-size:12px;color:var(--muted)}
.decision-item-date{font-size:11px;color:var(--muted-2);margin-top:4px}

.question-list{list-style:none;display:flex;flex-direction:column;gap:5px}
.question-item{font-size:13px;display:flex;gap:9px;align-items:baseline}
.q-branch{font-size:10px;color:var(--muted);background:var(--surface);border-radius:9px;padding:2px 7px;white-space:nowrap;flex-shrink:0}
.q-text{color:var(--text-2)}

/* ---- NOTE VIEW ---- */
.note-wrap{max-width:760px;margin:0 auto;padding:28px 32px}
.note-breadcrumb{display:flex;align-items:center;gap:5px;font-size:12px;color:var(--muted);margin-bottom:18px;flex-wrap:wrap}
.note-breadcrumb a{color:var(--accent);text-decoration:none}
.note-breadcrumb a:hover{text-decoration:underline}
.note-header{margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border)}
.note-badges{display:flex;gap:6px;align-items:center;margin-bottom:9px;flex-wrap:wrap}
.note-type-label{font-size:11px;color:var(--muted)}
.note-title{font-size:23px;font-weight:700;letter-spacing:-.3px;margin-bottom:8px;color:var(--text)}
.note-meta{display:flex;gap:11px;font-size:12px;color:var(--muted);flex-wrap:wrap}
.note-canonical{color:var(--ok)}
.note-non-canonical{color:var(--ev-fg)}

.nc-warning{background:#1a0a00;border:1px solid var(--ev-border);border-radius:var(--radius-sm);padding:9px 13px;margin-bottom:18px;font-size:12px;color:var(--ev-fg)}

/* Note body markdown */
.note-body{color:var(--text-2);line-height:1.75}
.note-body h1{font-size:20px;font-weight:700;margin:22px 0 10px;color:var(--text)}
.note-body h2{font-size:16px;font-weight:600;margin:20px 0 8px;color:var(--text-2);padding-bottom:5px;border-bottom:1px solid var(--border)}
.note-body h3{font-size:14px;font-weight:600;margin:16px 0 6px;color:var(--text-2)}
.note-body h4{font-size:13px;font-weight:600;margin:12px 0 5px;color:var(--muted)}
.note-body p{margin:7px 0}
.note-body ul,.note-body ol{margin:7px 0 7px 20px}
.note-body li{margin:3px 0}
.note-body code{background:var(--surface-2);border:1px solid var(--border);border-radius:3px;padding:1px 5px;font-family:ui-monospace,"Cascadia Code","Fira Code",monospace;font-size:12px;color:var(--text-2)}
.note-body pre{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;overflow-x:auto;margin:12px 0}
.note-body pre code{background:none;border:none;padding:0;font-size:12.5px}
.note-body blockquote{border-left:3px solid var(--accent);padding:2px 0 2px 14px;color:var(--muted);margin:10px 0}
.note-body a{color:var(--accent)}
.note-body hr{border:none;border-top:1px solid var(--border);margin:18px 0}
.note-body table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13px}
.note-body th{background:var(--surface-2);padding:6px 12px;text-align:left;border:1px solid var(--border);font-weight:600;color:var(--text-2)}
.note-body td{padding:6px 12px;border:1px solid var(--border);color:var(--text-2)}
.note-body strong{color:var(--text);font-weight:600}
.note-body em{color:var(--text-2)}

.related-section{margin-top:30px;padding-top:18px;border-top:1px solid var(--border)}
.related-section h4{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted-2);margin-bottom:10px}
.related-list{display:flex;flex-direction:column;gap:5px}
.related-item{display:flex;flex-direction:column;gap:3px;text-decoration:none;padding:9px 12px;background:var(--surface);border-radius:var(--radius-sm);border:1px solid var(--border);transition:border-color .15s}
.related-item:hover{border-color:var(--accent)}
.related-item-title{color:var(--accent);font-size:13px;font-weight:500}
.related-item-summary{color:var(--muted);font-size:12px}

/* ---- EVIDENCE VIEW ---- */
.evidence-list{display:flex;flex-direction:column;gap:8px}
.ev-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:13px 15px;cursor:pointer;transition:border-color .15s}
.ev-card:hover{border-color:var(--ev-border)}
.ev-card-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:5px}
.ev-card-title{font-weight:500;font-size:13px;color:var(--text);flex:1}
.ev-source{font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;margin-bottom:4px}
.ev-date{font-size:11px;color:var(--muted-2)}
.empty-state{text-align:center;color:var(--muted);padding:48px 20px;font-size:14px}

/* ---- BADGES ---- */
.badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;flex-shrink:0}
.badge-Memory{background:var(--mem-bg);color:var(--mem-fg);border:1px solid var(--mem-border)}
.badge-Evidence{background:var(--ev-bg);color:var(--ev-fg);border:1px solid var(--ev-border)}
.badge-Outputs{background:var(--out-bg);color:var(--out-fg);border:1px solid var(--out-border)}
.badge-Sessions{background:var(--ses-bg);color:var(--ses-fg);border:1px solid var(--ses-border)}
.badge-profile{background:var(--surface-2);color:var(--muted);border:1px solid var(--border);font-size:9px}
.badge-onboarding-ok{background:#0d2b0d;color:var(--ok);border:1px solid #1a4d1a;font-size:9px}
.badge-onboarding-pending{background:var(--warn-bg);color:var(--warn-fg);border:1px solid var(--warn-fg);font-size:9px}
</style>
</head>
<body>
<div id="root">
  <aside id="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo"><span class="sidebar-logo-mark">AK</span>agent-knowledge</div>
      <div class="sidebar-project-name">__PROJECT_NAME__</div>
      <div class="sidebar-meta" id="sidebar-meta"></div>
    </div>
    <div id="sidebar-tree"></div>
    <div class="sidebar-footer">
      Generated __GENERATED__<br>
      Non-canonical derived artifact — vault is the source of truth
    </div>
  </aside>
  <div id="main">
    <div id="topbar">
      <div id="breadcrumb"><span class="bc-current">Overview</span></div>
      <div id="topbar-tabs">
        <button class="tab-btn active" data-view="overview" onclick="nav('overview')">Overview</button>
        <button class="tab-btn" data-view="evidence" onclick="nav('evidence')">Evidence</button>
      </div>
    </div>
    <div id="content"></div>
  </div>
</div>

<script>
const DATA = __DATA_JSON__;

let _view = 'overview';
let _notePath = null;

// ---- Helpers ----
function esc(s){
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function badge(folder){
  return `<span class="badge badge-${esc(folder)}">${esc(folder)}</span>`;
}
function encP(s){ return encodeURIComponent(s); }

// ---- Navigation ----
function nav(view, arg){
  if(view==='overview') location.hash='overview';
  else if(view==='note') location.hash='note/'+encP(arg);
  else if(view==='evidence') location.hash='evidence';
}

function handleHash(){
  const h = location.hash.slice(1);
  if(!h||h==='overview') showOverview();
  else if(h.startsWith('note/')) showNote(decodeURIComponent(h.slice(5)));
  else if(h==='evidence') showEvidence();
  else showOverview();
}

// ---- Sidebar ----
function buildSidebar(){
  const meta = document.getElementById('sidebar-meta');
  const profile = DATA.project.profile||'unknown';
  const onb = DATA.project.onboarding||'unknown';
  const onbCls = onb==='complete'?'badge-onboarding-ok':'badge-onboarding-pending';
  meta.innerHTML = `<span class="badge badge-profile">${esc(profile)}</span><span class="badge ${onbCls}">${esc(onb)}</span>`;

  const tree = document.getElementById('sidebar-tree');
  let h = '';

  // Memory group
  h += '<div class="tree-group">';
  h += `<div class="tree-group-header">${badge('Memory')}</div>`;
  for(const b of DATA.branches){
    if(b.path==='Memory/MEMORY.md') continue;
    h += `<div class="tree-item branch" data-path="${esc(b.path)}" onclick="nav('note','${esc(b.path)}')" title="${esc(b.path)}">`;
    h += `<span class="tree-item-icon">◈</span><span class="tree-item-label">${esc(b.title)}</span></div>`;
    for(const lf of (b.leaves||[])){
      h += `<div class="tree-item leaf" data-path="${esc(lf.path)}" onclick="nav('note','${esc(lf.path)}')" title="${esc(lf.path)}">`;
      h += `<span class="tree-item-icon">·</span><span class="tree-item-label">${esc(lf.title)}</span></div>`;
    }
  }

  // Decisions
  if(DATA.decisions&&DATA.decisions.length>0){
    h += '<div class="tree-sep"></div>';
    h += '<div class="tree-group-header" style="font-size:9px">Decisions</div>';
    for(const d of DATA.decisions){
      h += `<div class="tree-item leaf" data-path="${esc(d.path)}" onclick="nav('note','${esc(d.path)}')" title="${esc(d.path)}">`;
      h += `<span class="tree-item-icon">⊞</span><span class="tree-item-label">${esc(d.title)}</span></div>`;
    }
  }
  h += '</div>';

  // Evidence group
  if(DATA.evidence&&DATA.evidence.length>0){
    h += '<div class="tree-sep"></div>';
    h += '<div class="tree-group">';
    h += `<div class="tree-group-header">${badge('Evidence')}<span class="count">${DATA.evidence.length}</span></div>`;
    for(const e of DATA.evidence){
      h += `<div class="tree-item leaf" data-path="${esc(e.path)}" onclick="nav('note','${esc(e.path)}')" title="${esc(e.path)}">`;
      h += `<span class="tree-item-icon">·</span><span class="tree-item-label">${esc(e.title)}</span></div>`;
    }
    h += '</div>';
  }

  tree.innerHTML = h;
}

function setSidebarActive(path){
  document.querySelectorAll('#sidebar-tree .tree-item').forEach(el=>{
    el.classList.toggle('active', el.dataset.path===path);
  });
}

// ---- Topbar ----
function setTopbar(view, note){
  const bc = document.getElementById('breadcrumb');
  document.querySelectorAll('.tab-btn').forEach(b=>{
    b.classList.toggle('active', b.dataset.view===view);
  });
  if(view==='overview'){
    bc.innerHTML='<span class="bc-current">Overview</span>';
  } else if(view==='evidence'){
    bc.innerHTML='<span class="bc-current">Evidence</span>';
  } else if(view==='note'&&note){
    const folderBadge = badge(note.folder);
    bc.innerHTML = `<a href="#overview" onclick="event.preventDefault();nav('overview')">Overview</a>`
      +`<span class="bc-sep">›</span>${folderBadge}`
      +`<span class="bc-sep">›</span><span class="bc-current">${esc(note.title)}</span>`;
  }
}

// ---- Overview ----
function showOverview(){
  _view='overview'; _notePath=null;
  const content = document.getElementById('content');
  let h = '<div class="view-wrap">';

  // Header
  const p = DATA.project;
  const onb = p.onboarding||'unknown';
  const onbOk = onb==='complete';
  h += `<div class="ov-header"><div class="ov-title">${esc(p.name)}</div>`;
  h += `<div class="ov-meta">`;
  h += `<span class="ov-meta-item">slug: <code>${esc(p.slug)}</code></span>`;
  h += `<span class="sep-dot">·</span>`;
  h += `<span class="ov-meta-item">profile: ${esc(p.profile)}</span>`;
  h += `<span class="sep-dot">·</span>`;
  const onbColor = onbOk?'status-ok':'status-pending';
  h += `<span class="ov-meta-item ${onbColor}">onboarding: ${esc(onb)}</span>`;
  if(DATA.stats){
    h += `<span class="sep-dot">·</span><span class="ov-meta-item">${DATA.stats.branch_count} branches · ${DATA.stats.decision_count} decisions · ${DATA.stats.evidence_count} evidence</span>`;
  }
  h += `</div></div>`;

  // Warnings
  if(DATA.warnings&&DATA.warnings.length>0){
    h += `<div class="warnings-box"><h3>Warnings</h3>`;
    for(const w of DATA.warnings) h += `<div class="warn-item">${esc(w)}</div>`;
    h += `</div>`;
  }

  // Branch cards
  const mainBranches = DATA.branches.filter(b=>b.path!=='Memory/MEMORY.md');
  if(mainBranches.length>0){
    h += `<div class="section"><div class="section-heading">Knowledge Branches</div>`;
    h += `<div class="branch-grid">`;
    for(const b of mainBranches){
      const purpose = b.purpose||b.summary||'';
      const stateN = (b.current_state||[]).length;
      const changesN = (b.recent_changes||[]).length;
      h += `<div class="branch-card" onclick="nav('note','${esc(b.path)}')">`;
      h += `<div class="branch-card-top"><span class="branch-card-title">${esc(b.title)}</span>${badge('Memory')}</div>`;
      h += `<div class="branch-card-purpose">${esc(purpose.substring(0,130))}${purpose.length>130?'…':''}</div>`;
      h += `<div class="branch-card-foot"><span>${stateN} facts</span><span>${changesN} changes</span>${b.updated?`<span>${esc(b.updated)}</span>`:''}</div>`;
      h += `</div>`;
    }
    h += `</div></div>`;
  }

  // Recent Changes
  if(DATA.recent_changes_global&&DATA.recent_changes_global.length>0){
    h += `<div class="section"><div class="section-heading">Recent Changes</div><div class="changes-list">`;
    for(const c of DATA.recent_changes_global){
      h += `<div class="change-row">`;
      h += `<span class="change-date">${esc(c.date)}</span>`;
      h += `<span class="change-branch-tag">${esc(c.branch)}</span>`;
      h += `<span class="change-text">${esc(c.text)}</span>`;
      h += `</div>`;
    }
    h += `</div></div>`;
  }

  // Decisions
  if(DATA.decisions&&DATA.decisions.length>0){
    const shown = DATA.decisions.slice(0,8);
    h += `<div class="section"><div class="section-heading">Key Decisions</div><div class="decision-list">`;
    for(const d of shown){
      h += `<div class="decision-item" onclick="nav('note','${esc(d.path)}')">`;
      h += `<div class="decision-item-title">${esc(d.title)}</div>`;
      if(d.what) h += `<div class="decision-item-what">${esc(d.what.substring(0,160))}${d.what.length>160?'…':''}</div>`;
      if(d.date) h += `<div class="decision-item-date">${esc(d.date)}</div>`;
      h += `</div>`;
    }
    h += `</div></div>`;
  }

  // Open Questions
  const allQ = DATA.branches.flatMap(b=>(b.open_questions||[]).map(q=>({q,branch:b.title})));
  if(allQ.length>0){
    h += `<div class="section"><div class="section-heading">Open Questions</div><ul class="question-list">`;
    for(const {q,branch} of allQ){
      h += `<li class="question-item"><span class="q-branch">${esc(branch)}</span><span class="q-text">${esc(q)}</span></li>`;
    }
    h += `</ul></div>`;
  }

  h += `</div>`;
  content.innerHTML = h;
  setTopbar('overview');
  setSidebarActive(null);
}

// ---- Note view ----
function findNote(path){
  for(const b of DATA.branches){
    if(b.path===path) return b;
    for(const lf of (b.leaves||[])){if(lf.path===path) return lf;}
  }
  for(const d of (DATA.decisions||[])){if(d.path===path) return d;}
  for(const e of (DATA.evidence||[])){if(e.path===path) return e;}
  return null;
}

function showNote(path){
  _view='note'; _notePath=path;
  const note = findNote(path);
  const content = document.getElementById('content');
  if(!note){
    content.innerHTML=`<div class="note-wrap"><div class="empty-state">Note not found: ${esc(path)}</div></div>`;
    return;
  }
  let h = `<div class="note-wrap">`;

  // Breadcrumb
  h += `<div class="note-breadcrumb">`;
  h += `<a href="#overview" onclick="event.preventDefault();nav('overview')">Overview</a>`;
  h += `<span class="bc-sep">›</span>${badge(note.folder)}`;
  h += `<span class="bc-sep">›</span><span>${esc(note.title)}</span>`;
  h += `</div>`;

  // Header
  h += `<div class="note-header">`;
  h += `<div class="note-badges">${badge(note.folder)}`;
  if(note.note_type&&note.note_type!=='unknown') h += `<span class="note-type-label">${esc(note.note_type)}</span>`;
  h += `</div>`;
  h += `<div class="note-title">${esc(note.title)}</div>`;
  h += `<div class="note-meta">`;
  if(note.area) h += `<span>area: ${esc(note.area)}</span>`;
  if(note.updated) h += `<span>updated: ${esc(note.updated)}</span>`;
  const cnCls = note.canonical?'note-canonical':'note-non-canonical';
  h += `<span class="${cnCls}">${note.canonical?'✓ canonical':'⊘ non-canonical'}</span>`;
  h += `</div></div>`;

  // Non-canonical warning
  if(!note.canonical){
    h += `<div class="nc-warning">This note is in <strong>${esc(note.folder)}</strong> and is not canonical memory. Do not treat it as source of truth.</div>`;
  }

  // Body
  h += `<div class="note-body">${note.html||''}</div>`;

  // Leaves (sub-notes)
  if(note.leaves&&note.leaves.length>0){
    h += `<div class="related-section"><h4>Branch Notes</h4><div class="related-list">`;
    for(const lf of note.leaves){
      h += `<a class="related-item" href="#note/${encP(lf.path)}" onclick="event.preventDefault();nav('note','${esc(lf.path)}')">`;
      h += `<span class="related-item-title">${esc(lf.title)}</span>`;
      if(lf.summary) h += `<span class="related-item-summary">${esc(lf.summary.substring(0,100))}</span>`;
      h += `</a>`;
    }
    h += `</div></div>`;
  }

  h += `</div>`;
  content.innerHTML = h;
  setTopbar('note', note);
  setSidebarActive(path);
  document.getElementById('content').scrollTop=0;
}

// ---- Evidence view ----
function showEvidence(){
  _view='evidence'; _notePath=null;
  const content = document.getElementById('content');
  let h = `<div class="view-wrap">`;
  h += `<div class="ov-header"><div class="ov-title">Evidence</div>`;
  h += `<div class="ov-meta"><span>Imported and extracted material — non-canonical. Verify before using as source of truth.</span></div></div>`;

  if(!DATA.evidence||DATA.evidence.length===0){
    h += `<div class="empty-state">No evidence items in this vault.</div>`;
  } else {
    h += `<div class="evidence-list">`;
    for(const e of DATA.evidence){
      h += `<div class="ev-card" onclick="nav('note','${esc(e.path)}')">`;
      h += `<div class="ev-card-top"><span class="ev-card-title">${esc(e.title)}</span>${badge('Evidence')}</div>`;
      if(e.source) h += `<div class="ev-source">${esc(e.source)}</div>`;
      if(e.imported) h += `<div class="ev-date">Imported: ${esc(e.imported.split('T')[0])}</div>`;
      if(e.summary&&!e.source) h += `<div class="ev-date">${esc(e.summary.substring(0,120))}</div>`;
      h += `</div>`;
    }
    h += `</div>`;
  }
  h += `</div>`;
  content.innerHTML = h;
  setTopbar('evidence');
  setSidebarActive(null);
}

// ---- Boot ----
buildSidebar();
handleHash();
window.addEventListener('hashchange', handleHash);
</script>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# Site generation entry point                                                  #
# --------------------------------------------------------------------------- #


def generate_site(
    vault_dir: Path,
    output_dir: Path | None = None,
    *,
    dry_run: bool = False,
    include_evidence: bool = True,
    include_sessions: bool = False,
) -> dict[str, Any]:
    """Generate the static site from the vault.

    Returns a summary dict:
      {"action": "created"|"updated"|"dry-run", "site_dir": str, "note_count": int, ...}

    Writes:
      <output_dir>/index.html          -- main SPA
      <output_dir>/data/knowledge.json -- structured data model
    """
    if output_dir is None:
        output_dir = vault_dir / "Outputs" / "site"

    site_data = build_site_data(
        vault_dir,
        include_evidence=include_evidence,
        include_sessions=include_sessions,
    )

    if dry_run:
        return {
            "action": "dry-run",
            "site_dir": str(output_dir),
            "note_count": site_data["stats"]["note_count"],
            "branch_count": site_data["stats"]["branch_count"],
            "evidence_count": site_data["stats"]["evidence_count"],
            "decision_count": site_data["stats"]["decision_count"],
            "dry_run": True,
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data").mkdir(exist_ok=True)

    # Write knowledge.json
    json_path = output_dir / "data" / "knowledge.json"
    json_existed = json_path.exists()
    json_path.write_text(json.dumps(site_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Build and write index.html
    html_content = _render_html(site_data)
    html_path = output_dir / "index.html"
    html_existed = html_path.exists()
    html_path.write_text(html_content, encoding="utf-8")

    action = "updated" if (json_existed or html_existed) else "created"

    return {
        "action": action,
        "site_dir": str(output_dir),
        "index_html": str(html_path),
        "knowledge_json": str(json_path),
        "note_count": site_data["stats"]["note_count"],
        "branch_count": site_data["stats"]["branch_count"],
        "evidence_count": site_data["stats"]["evidence_count"],
        "decision_count": site_data["stats"]["decision_count"],
        "dry_run": False,
    }


def _render_html(data: dict[str, Any]) -> str:
    """Render the complete index.html with data embedded."""
    project_name = html_mod.escape(data["project"].get("name", "Knowledge Vault"))
    generated = data.get("generated", "")

    # Embed data as a JS constant (no fetch needed — works with file:// protocol)
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    return (
        _HTML_TEMPLATE
        .replace("__PROJECT_NAME__", project_name)
        .replace("__GENERATED__", generated)
        .replace("__DATA_JSON__", data_json)
    )
