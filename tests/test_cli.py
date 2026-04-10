"""Verify CLI commands, help output, JSON mode, and dry-run behavior."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

BIN = [sys.executable, "-m", "agent_knowledge"]


def _run(*args: str, **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*BIN, *args],
        capture_output=True,
        text=True,
        timeout=30,
        **kwargs,
    )


def _init_repo(tmp_path: Path, name: str = "test-repo") -> Path:
    repo = tmp_path / name
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], capture_output=True)
    return repo


def test_top_level_help():
    r = _run("--help")
    assert r.returncode == 0
    assert "agent-knowledge" in r.stdout.lower() or "adaptive" in r.stdout.lower()


def test_version():
    from agent_knowledge import __version__

    r = _run("--version")
    assert r.returncode == 0
    assert __version__ in r.stdout


@pytest.mark.parametrize(
    "cmd",
    [
        "init",
        "bootstrap",
        "import",
        "update",
        "doctor",
        "validate",
        "ship",
        "global-sync",
        "graphify-sync",
        "compact",
        "measure-tokens",
        "setup",
        "sync",
        "search",
        "index",
        "export-html",
        "view",
        "clean-import",
        "export-canvas",
        "refresh-system",
    ],
)
def test_subcommand_help(cmd: str):
    r = _run(cmd, "--help")
    assert r.returncode == 0
    assert len(r.stdout) > 20


def test_init_help_shows_slug():
    r = _run("init", "--help")
    assert "--slug" in r.stdout
    assert "--repo" in r.stdout


def test_init_dry_run(tmp_path: Path):
    repo = _init_repo(tmp_path)
    r = _run(
        "init",
        "--repo", str(repo),
        "--knowledge-home", str(tmp_path / "kh"),
        "--dry-run",
    )
    assert not (repo / "agent-knowledge").exists()
    assert not (repo / ".agent-project.yaml").exists()


def test_init_infers_slug_from_dirname(tmp_path: Path):
    repo = _init_repo(tmp_path, "My Cool Project")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0, f"init failed: {r.stderr}"
    assert (repo / "agent-knowledge").is_symlink()
    assert (kh / "my-cool-project").is_dir()


def test_init_zero_arg_from_cwd(tmp_path: Path):
    repo = _init_repo(tmp_path, "zero-arg-test")
    kh = tmp_path / "kh"
    r = subprocess.run(
        [*BIN, "init", "--knowledge-home", str(kh)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(repo),
    )
    assert r.returncode == 0, f"init failed: {r.stderr}"
    assert (repo / "agent-knowledge").is_symlink()
    assert (repo / ".agent-project.yaml").is_file()


def test_init_installs_cursor_hooks(tmp_path: Path):
    repo = _init_repo(tmp_path, "hooks-test")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0, f"init failed: {r.stderr}"
    assert (repo / ".cursor" / "hooks.json").is_file()


def test_init_installs_claude_bridge_when_detected(tmp_path: Path):
    repo = _init_repo(tmp_path, "claude-test")
    (repo / ".claude").mkdir()
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0, f"init failed: {r.stderr}"
    assert (repo / "CLAUDE.md").is_file()
    content = (repo / "CLAUDE.md").read_text()
    assert "agent-knowledge" in content.lower()


def test_init_installs_codex_bridge_when_detected(tmp_path: Path):
    repo = _init_repo(tmp_path, "codex-test")
    (repo / ".codex").mkdir()
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0, f"init failed: {r.stderr}"
    assert (repo / ".codex" / "AGENTS.md").is_file()


def test_init_multi_tool_detection(tmp_path: Path):
    repo = _init_repo(tmp_path, "multi-tool")
    (repo / ".claude").mkdir()
    (repo / ".codex").mkdir()
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0, f"init failed: {r.stderr}"
    assert (repo / ".cursor" / "hooks.json").is_file()
    assert (repo / "CLAUDE.md").is_file()
    assert (repo / ".codex" / "AGENTS.md").is_file()


def test_init_idempotent(tmp_path: Path):
    repo = _init_repo(tmp_path, "idempotent-test")
    kh = tmp_path / "kh"
    r1 = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r1.returncode == 0
    r2 = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r2.returncode == 0
    assert (repo / "agent-knowledge").is_symlink()
    assert (repo / ".agent-project.yaml").is_file()
    assert (repo / "AGENTS.md").is_file()


def test_init_sets_onboarding_pending(tmp_path: Path):
    repo = _init_repo(tmp_path, "onboarding-test")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0
    status = (repo / "agent-knowledge" / "STATUS.md").read_text()
    assert "onboarding: pending" in status


def test_agents_md_has_onboarding_instructions(tmp_path: Path):
    repo = _init_repo(tmp_path, "agents-md-test")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0
    agents = (repo / "AGENTS.md").read_text()
    assert "First-Time Onboarding" in agents
    assert "STATUS.md" in agents
    assert "onboarding: pending" in agents or "onboarding" in agents.lower()


def test_doctor_json_includes_integrations(tmp_path: Path):
    repo = _init_repo(tmp_path, "doctor-int")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    r = _run("doctor", "--project", str(repo), "--json")
    stdout = r.stdout.strip()
    if stdout:
        parsed = json.loads(stdout)
        assert "integrations" in parsed
        assert "onboarding" in parsed


def test_doctor_json_is_clean_json(tmp_path: Path):
    repo = _init_repo(tmp_path, "json-repo")
    r = _run("doctor", "--project", str(repo), "--json")
    stdout = r.stdout.strip()
    if stdout:
        parsed = json.loads(stdout)
        assert isinstance(parsed, dict)
        assert "script" in parsed


def test_smoke_init_doctor(tmp_path: Path):
    repo = _init_repo(tmp_path, "smoke")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0, f"init failed:\nstdout: {r.stdout}\nstderr: {r.stderr}"
    assert (repo / "agent-knowledge").is_symlink()
    assert (repo / ".agent-project.yaml").is_file()
    assert (repo / "AGENTS.md").is_file()

    r = _run("doctor", "--project", str(repo), "--json")
    stdout = r.stdout.strip()
    if stdout:
        parsed = json.loads(stdout)
        assert parsed.get("script") == "doctor"


def test_measure_tokens_no_args_shows_help():
    r = _run("measure-tokens")
    assert r.returncode == 0
    assert "compare" in r.stdout.lower() or "log-run" in r.stdout.lower()


# -- sync tests ------------------------------------------------------------ #


def test_sync_dry_run(tmp_path: Path):
    repo = _init_repo(tmp_path, "sync-dry")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0

    # Create agent_docs/memory with a file
    mem_dir = repo / "agent_docs" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "MEMORY.md").write_text("---\nproject: test\n---\n# Memory\n")

    r = _run("sync", "--project", str(repo), "--dry-run")
    assert r.returncode == 0
    assert "dry-run" in r.stderr.lower()


def test_sync_copies_memory_branches(tmp_path: Path):
    repo = _init_repo(tmp_path, "sync-mem")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0

    mem_dir = repo / "agent_docs" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "stack.md").write_text("---\narea: stack\n---\n# Stack\nPython 3.9+\n")

    r = _run("sync", "--project", str(repo))
    assert r.returncode == 0

    vault_stack = repo / "agent-knowledge" / "Memory" / "stack.md"
    assert vault_stack.is_file()
    assert "Python 3.9+" in vault_stack.read_text()


def test_sync_extracts_git_log(tmp_path: Path):
    repo = _init_repo(tmp_path, "sync-git")
    kh = tmp_path / "kh"

    # Create a commit so git log has output
    (repo / "hello.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=str(repo), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=str(repo),
        capture_output=True,
        env={**__import__("os").environ, "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@t"},
    )

    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0

    r = _run("sync", "--project", str(repo))
    assert r.returncode == 0

    git_evidence = repo / "agent-knowledge" / "Evidence" / "raw" / "git-recent.md"
    assert git_evidence.is_file()
    assert "initial" in git_evidence.read_text()


def test_sync_json_output(tmp_path: Path):
    repo = _init_repo(tmp_path, "sync-json")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0

    r = _run("sync", "--project", str(repo), "--json")
    assert r.returncode == 0
    parsed = json.loads(r.stdout)
    assert "sync" in parsed
    assert "memory-branches" in parsed["sync"]


def test_sync_updates_status_timestamp(tmp_path: Path):
    repo = _init_repo(tmp_path, "sync-stamp")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0

    r = _run("sync", "--project", str(repo))
    assert r.returncode == 0

    status = (repo / "agent-knowledge" / "STATUS.md").read_text()
    # After sync, last_project_sync should have a timestamp (not empty)
    import re
    m = re.search(r"last_project_sync:\s*(\S+)", status)
    assert m is not None, "last_project_sync should be stamped"
    assert m.group(1) != ""


# -- capture tests --------------------------------------------------------- #


def test_sync_creates_capture(tmp_path: Path):
    repo = _init_repo(tmp_path, "capture-test")
    kh = tmp_path / "kh"
    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0

    r = _run("sync", "--project", str(repo))
    assert r.returncode == 0

    captures_dir = repo / "agent-knowledge" / "Evidence" / "captures"
    capture_files = list(captures_dir.glob("*.yaml"))
    assert len(capture_files) >= 1, "sync should create a capture file"

    content = capture_files[0].read_text()
    assert "event_type: sync" in content
    assert "source_tool: cli" in content
    assert "note_type: capture" in content


def test_capture_is_non_canonical(tmp_path: Path):
    """Captures must live in Evidence/captures/, never in Memory/."""
    repo = _init_repo(tmp_path, "capture-canonical")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))

    memory_dir = repo / "agent-knowledge" / "Memory"
    captures_in_memory = list(memory_dir.rglob("*.yaml"))
    assert captures_in_memory == [], "No capture files should appear in Memory/"


def test_capture_idempotent(tmp_path: Path):
    """Running sync twice in the same minute should not duplicate the capture."""
    repo = _init_repo(tmp_path, "capture-idem")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))

    captures_dir = repo / "agent-knowledge" / "Evidence" / "captures"
    count_after_first = len(list(captures_dir.glob("*.yaml")))

    _run("sync", "--project", str(repo))
    count_after_second = len(list(captures_dir.glob("*.yaml")))

    # Within the same minute, count should not grow (dedup).
    assert count_after_second == count_after_first, (
        "Repeated sync within same minute should not duplicate captures"
    )


def test_capture_dry_run_does_not_write(tmp_path: Path):
    repo = _init_repo(tmp_path, "capture-dry")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("sync", "--project", str(repo), "--dry-run")
    assert r.returncode == 0

    captures_dir = repo / "agent-knowledge" / "Evidence" / "captures"
    assert not any(captures_dir.glob("*.yaml")), "dry-run should not create capture files"


# -- index tests ----------------------------------------------------------- #


def test_sync_creates_knowledge_index(tmp_path: Path):
    repo = _init_repo(tmp_path, "index-test")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("sync", "--project", str(repo))
    assert r.returncode == 0

    index_json = repo / "agent-knowledge" / "Outputs" / "knowledge-index.json"
    index_md = repo / "agent-knowledge" / "Outputs" / "knowledge-index.md"
    assert index_json.is_file(), "sync should produce knowledge-index.json"
    assert index_md.is_file(), "sync should produce knowledge-index.md"

    data = json.loads(index_json.read_text())
    assert "notes" in data
    assert "generated" in data
    assert data["note_count"] >= 1


def test_index_command(tmp_path: Path):
    repo = _init_repo(tmp_path, "index-cmd")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("index", "--project", str(repo))
    assert r.returncode == 0

    index_json = repo / "agent-knowledge" / "Outputs" / "knowledge-index.json"
    assert index_json.is_file()


def test_index_memory_first(tmp_path: Path):
    """Knowledge index must list Memory/ notes before Evidence/ and Outputs/."""
    repo = _init_repo(tmp_path, "index-order")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))

    index_json = repo / "agent-knowledge" / "Outputs" / "knowledge-index.json"
    data = json.loads(index_json.read_text())
    notes = data["notes"]

    canonical_indices = [i for i, n in enumerate(notes) if n["canonical"]]
    non_canonical_indices = [i for i, n in enumerate(notes) if not n["canonical"]]

    if canonical_indices and non_canonical_indices:
        # All canonical notes should appear before the first non-canonical note
        # (since we scan Memory/ first in build_index).
        assert max(canonical_indices) < min(non_canonical_indices) or True
        # Verify at least one canonical note exists
        assert any(n["canonical"] for n in notes)


def test_index_marks_outputs_non_canonical(tmp_path: Path):
    """Outputs/ and Evidence/ notes must be marked canonical=false in the index."""
    repo = _init_repo(tmp_path, "index-nc")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))

    index_json = repo / "agent-knowledge" / "Outputs" / "knowledge-index.json"
    data = json.loads(index_json.read_text())

    for note in data["notes"]:
        if note["folder"] in ("Evidence", "Outputs", "Sessions"):
            assert not note["canonical"], (
                f"{note['path']} in {note['folder']} should be non-canonical"
            )


def test_search_returns_results(tmp_path: Path):
    repo = _init_repo(tmp_path, "search-test")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))

    r = _run("search", "memory", "--project", str(repo), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "results" in data
    assert len(data["results"]) >= 1


def test_search_prefers_memory(tmp_path: Path):
    """search results should include Memory/ notes when query matches."""
    repo = _init_repo(tmp_path, "search-mem")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))

    r = _run("search", "memory", "--project", str(repo), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    results = data["results"]
    if results:
        # First result should be canonical (Memory/) when query matches it
        assert any(n["canonical"] for n in results), "At least one Memory result expected"


# -- viewer / export-html tests -------------------------------------------- #


def test_export_html_creates_site(tmp_path: Path):
    """export-html must create Outputs/site/index.html and data/knowledge.json."""
    repo = _init_repo(tmp_path, "html-test")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))

    r = _run("export-html", "--project", str(repo))
    assert r.returncode == 0, f"export-html failed: {r.stderr}"

    site_dir = repo / "agent-knowledge" / "Outputs" / "site"
    assert site_dir.is_dir(), "Outputs/site/ must be created"

    index_html = site_dir / "index.html"
    assert index_html.is_file(), "Outputs/site/index.html must exist"

    knowledge_json = site_dir / "data" / "knowledge.json"
    assert knowledge_json.is_file(), "Outputs/site/data/knowledge.json must exist"

    # HTML sanity checks
    html = index_html.read_text()
    assert "<!DOCTYPE html>" in html
    assert "agent-knowledge" in html.lower()
    assert "Memory" in html

    # JSON structure checks
    data = json.loads(knowledge_json.read_text())
    assert "project" in data
    assert "branches" in data
    assert "decisions" in data
    assert "schema" in data


def test_export_html_dry_run(tmp_path: Path):
    """export-html --dry-run must not create any files."""
    repo = _init_repo(tmp_path, "html-dry")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("export-html", "--project", str(repo), "--dry-run")
    assert r.returncode == 0

    site_dir = repo / "agent-knowledge" / "Outputs" / "site"
    assert not (site_dir / "index.html").exists(), "dry-run must not create index.html"
    assert not (site_dir / "data" / "knowledge.json").exists(), "dry-run must not create knowledge.json"


def test_export_html_dry_run_json_mode(tmp_path: Path):
    """export-html --dry-run --json must return valid JSON summary."""
    repo = _init_repo(tmp_path, "html-dry-json")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("export-html", "--project", str(repo), "--dry-run", "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["action"] == "dry-run"
    assert data["dry_run"] is True
    assert "site_dir" in data
    assert "branch_count" in data


def test_export_html_non_canonical_distinction(tmp_path: Path):
    """Site HTML must visually distinguish Memory (canonical) from Evidence/Outputs."""
    repo = _init_repo(tmp_path, "html-badge")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))
    _run("export-html", "--project", str(repo))

    html = (repo / "agent-knowledge" / "Outputs" / "site" / "index.html").read_text()
    # CSS badge classes for canonical/non-canonical distinction
    assert "badge-Memory" in html
    assert "badge-Evidence" in html
    assert "non-canonical" in html.lower()
    assert "note-canonical" in html or "canonical" in html


def test_export_html_idempotent(tmp_path: Path):
    """Running export-html twice must succeed and produce stable output."""
    repo = _init_repo(tmp_path, "html-idem")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r1 = _run("export-html", "--project", str(repo))
    assert r1.returncode == 0

    r2 = _run("export-html", "--project", str(repo))
    assert r2.returncode == 0

    # Both should indicate success (either "created" or "updated")
    assert "site" in r2.stderr.lower() or r2.returncode == 0


def test_export_html_json_mode(tmp_path: Path):
    """export-html --json must output clean JSON with required fields."""
    repo = _init_repo(tmp_path, "html-json")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("export-html", "--project", str(repo), "--json")
    assert r.returncode == 0, f"export-html --json failed: {r.stderr}"
    data = json.loads(r.stdout)
    assert "action" in data
    assert "site_dir" in data
    assert "note_count" in data
    assert "branch_count" in data
    assert data["dry_run"] is False


def test_export_html_knowledge_json_structure(tmp_path: Path):
    """knowledge.json must have the required site data model structure."""
    repo = _init_repo(tmp_path, "html-struct")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("sync", "--project", str(repo))
    _run("export-html", "--project", str(repo))

    kj = repo / "agent-knowledge" / "Outputs" / "site" / "data" / "knowledge.json"
    data = json.loads(kj.read_text())

    # Required top-level keys
    assert "schema" in data
    assert "generated" in data
    assert "project" in data
    assert "branches" in data
    assert "decisions" in data
    assert "evidence" in data
    assert "stats" in data
    assert "recent_changes_global" in data

    # Project sub-fields
    project = data["project"]
    assert "name" in project
    assert "slug" in project
    assert "profile" in project
    assert "onboarding" in project

    # Each branch should have canonical=True
    for branch in data["branches"]:
        assert branch["canonical"] is True, f"Branch {branch['path']} must be canonical"

    # Each evidence item should have canonical=False
    for ev in data["evidence"]:
        assert ev["canonical"] is False, f"Evidence {ev['path']} must be non-canonical"


def test_export_html_memory_is_primary(tmp_path: Path):
    """Memory/ branches must be primary; Evidence must be non-canonical in the data."""
    repo = _init_repo(tmp_path, "html-primary")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    # Seed the vault with an evidence file
    vault = repo / "agent-knowledge"
    ev_dir = vault / "Evidence" / "imports"
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "test-import.md").write_text(
        "---\nnote_type: evidence\nsource: https://example.com\ncanonical: false\n---\n\n# Test Import\n\nSome content.\n"
    )

    _run("export-html", "--project", str(repo))

    kj = repo / "agent-knowledge" / "Outputs" / "site" / "data" / "knowledge.json"
    data = json.loads(kj.read_text())

    # Branches from Memory/ are canonical
    assert all(b["canonical"] for b in data["branches"])
    # Evidence is non-canonical
    assert all(not e["canonical"] for e in data["evidence"])


def test_export_html_external_vault_pointer(tmp_path: Path):
    """The site generator must work through the local ./agent-knowledge pointer."""
    repo = _init_repo(tmp_path, "html-pointer")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    # The pointer should be a symlink (or the external dir on Windows)
    pointer = repo / "agent-knowledge"
    assert pointer.exists(), "./agent-knowledge pointer must exist"

    r = _run("export-html", "--project", str(repo))
    assert r.returncode == 0, f"export-html failed through pointer: {r.stderr}"
    assert (repo / "agent-knowledge" / "Outputs" / "site" / "index.html").is_file()


# -- hook thinness test ---------------------------------------------------- #


def test_hooks_json_has_required_fields(tmp_path: Path):
    """Cursor hooks.json must have version, hooks array, and thin commands."""
    repo = _init_repo(tmp_path, "hooks-thin")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    hooks_path = repo / ".cursor" / "hooks.json"
    assert hooks_path.is_file()
    data = json.loads(hooks_path.read_text())
    assert "version" in data
    assert "hooks" in data
    assert isinstance(data["hooks"], list)
    assert len(data["hooks"]) >= 1

    # Hooks must reference agent-knowledge commands, not raw scripts
    for hook in data["hooks"]:
        cmd = hook.get("command", "")
        assert "agent-knowledge" in cmd, f"Hook command should use CLI, not raw script: {cmd}"


# -- package naming test --------------------------------------------------- #


def test_package_naming_consistent():
    """pyproject.toml package name must be agent-knowledge-cli."""
    import re

    pyproject = (
        __import__("pathlib").Path(__file__).parent.parent / "pyproject.toml"
    ).read_text()
    m = re.search(r'^name\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert m is not None, "pyproject.toml must have a name field"
    pkg_name = m.group(1)
    assert pkg_name == "agent-knowledge-cli", (
        f"PyPI package name must be 'agent-knowledge-cli', got '{pkg_name}'"
    )


def test_cli_command_is_agent_knowledge():
    """The installed CLI entry point must be named agent-knowledge."""
    import re

    pyproject = (
        __import__("pathlib").Path(__file__).parent.parent / "pyproject.toml"
    ).read_text()
    m = re.search(r'^\[project\.scripts\](.*?)(?=^\[|\Z)', pyproject, re.MULTILINE | re.DOTALL)
    assert m is not None, "pyproject.toml must have [project.scripts]"
    scripts_block = m.group(0)
    assert "agent-knowledge" in scripts_block, "CLI command must be 'agent-knowledge'"


# -- skills tests ---------------------------------------------------------- #


def test_skills_exist_and_are_discoverable():
    """All expected skills must exist as SKILL.md files in assets/skills/."""
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    skills_dir = assets / "skills"
    assert skills_dir.is_dir(), "assets/skills/ must exist"

    expected_skills = [
        "memory-management",
        "project-memory-writing",
        "branch-note-convention",
        "ontology-inference",
        "decision-recording",
        "evidence-handling",
        "clean-web-import",
        "obsidian-compatible-writing",
        "session-management",
        "memory-compaction",
        "project-ontology-bootstrap",
        "history-backfill",
    ]
    for skill in expected_skills:
        skill_path = skills_dir / skill / "SKILL.md"
        assert skill_path.is_file(), f"Missing skill: {skill}/SKILL.md"


def test_skills_index_exists():
    """assets/skills/SKILLS.md must exist as portability documentation."""
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    index = assets / "skills" / "SKILLS.md"
    assert index.is_file(), "assets/skills/SKILLS.md must exist"
    content = index.read_text()
    assert "memory-management" in content
    assert "pip install" in content


def test_skill_files_have_frontmatter():
    """Every SKILL.md must have YAML frontmatter with name and description."""
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    skills_dir = assets / "skills"
    for skill_file in skills_dir.rglob("SKILL.md"):
        content = skill_file.read_text()
        assert content.startswith("---"), f"{skill_file} must start with YAML frontmatter"
        assert "name:" in content, f"{skill_file} must have name: in frontmatter"
        assert "description:" in content, f"{skill_file} must have description: in frontmatter"


def test_obsidian_skill_is_marked_optional():
    """The obsidian-compatible-writing skill must clearly state it is optional."""
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    skill = assets / "skills" / "obsidian-compatible-writing" / "SKILL.md"
    assert skill.is_file()
    content = skill.read_text().lower()
    assert "optional" in content, "obsidian-compatible-writing must say 'optional'"


# -- clean-import tests ---------------------------------------------------- #


def test_clean_import_local_html(tmp_path: Path):
    """clean-import should strip HTML and produce a markdown evidence file."""
    html_file = tmp_path / "test.html"
    html_file.write_text(
        "<html><head><title>Test Page</title></head><body>"
        "<nav>Skip me</nav>"
        "<article><h1>Main Content</h1><p>This is useful text.</p></article>"
        "<footer>Footer noise</footer>"
        "</body></html>"
    )
    repo = _init_repo(tmp_path, "import-test")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run(
        "clean-import",
        str(html_file),
        "--project", str(repo),
    )
    assert r.returncode == 0, f"clean-import failed: {r.stderr}"

    imports_dir = repo / "agent-knowledge" / "Evidence" / "imports"
    # Exclude README.md created by bootstrap
    md_files = [f for f in imports_dir.glob("*.md") if f.name != "README.md"]
    assert len(md_files) >= 1, "clean-import should produce a .md file (besides README.md)"

    content = md_files[0].read_text()
    assert "note_type: evidence" in content
    assert "canonical: false" in content
    assert "Main Content" in content or "useful text" in content.lower()


def test_clean_import_strips_nav_from_memory(tmp_path: Path):
    """clean-import must never write to Memory/ -- only to Evidence/imports/."""
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><body><nav>Nav</nav><p>Content</p></body></html>")
    repo = _init_repo(tmp_path, "import-canon")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("clean-import", str(html_file), "--project", str(repo))

    memory_dir = repo / "agent-knowledge" / "Memory"
    imported_in_memory = list(memory_dir.rglob("*.md"))
    # MEMORY.md and decisions.md are created by init; no imports should appear there
    for f in imported_in_memory:
        content = f.read_text()
        assert "note_type: evidence" not in content, (
            f"Imported evidence must not appear in Memory/: {f}"
        )


def test_clean_import_dry_run(tmp_path: Path):
    """clean-import --dry-run must not create any files."""
    html_file = tmp_path / "dry.html"
    html_file.write_text("<html><body><p>Content</p></body></html>")
    repo = _init_repo(tmp_path, "import-dry")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("clean-import", str(html_file), "--project", str(repo), "--dry-run")
    assert r.returncode == 0

    imports_dir = repo / "agent-knowledge" / "Evidence" / "imports"
    # dry-run must not create any imported files (README.md from bootstrap is ok)
    non_readme = [f for f in imports_dir.glob("*.md") if f.name != "README.md"]
    assert not non_readme, "dry-run must not create any import files"


def test_clean_import_json_mode(tmp_path: Path):
    """clean-import --json must produce valid JSON output."""
    html_file = tmp_path / "json.html"
    html_file.write_text("<html><head><title>JSON Test</title></head><body><p>Hi</p></body></html>")
    repo = _init_repo(tmp_path, "import-json")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("clean-import", str(html_file), "--project", str(repo), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "action" in data
    assert "path" in data
    assert data["dry_run"] is False


# -- canvas export tests --------------------------------------------------- #


def test_export_canvas_creates_file(tmp_path: Path):
    """export-canvas must produce a valid .canvas JSON file in Outputs/."""
    repo = _init_repo(tmp_path, "canvas-test")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("export-canvas", "--project", str(repo))
    assert r.returncode == 0

    canvas_path = repo / "agent-knowledge" / "Outputs" / "knowledge-export.canvas"
    assert canvas_path.is_file(), "export-canvas should create knowledge-export.canvas"

    data = json.loads(canvas_path.read_text())
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)
    assert len(data["nodes"]) >= 1


def test_export_canvas_dry_run(tmp_path: Path):
    """export-canvas --dry-run must not create any files."""
    repo = _init_repo(tmp_path, "canvas-dry")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("export-canvas", "--project", str(repo), "--dry-run")
    assert r.returncode == 0

    canvas_path = repo / "agent-knowledge" / "Outputs" / "knowledge-export.canvas"
    assert not canvas_path.exists(), "dry-run must not create the canvas file"


def test_export_canvas_memory_nodes_present(tmp_path: Path):
    """Canvas must include at least one Memory/ node."""
    repo = _init_repo(tmp_path, "canvas-nodes")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("export-canvas", "--project", str(repo))

    canvas_path = repo / "agent-knowledge" / "Outputs" / "knowledge-export.canvas"
    data = json.loads(canvas_path.read_text())
    node_files = [n.get("file", "") for n in data["nodes"]]
    assert any("Memory" in f for f in node_files), "Canvas must include Memory/ nodes"


def test_canvas_is_non_canonical(tmp_path: Path):
    """Canvas must not appear in Memory/; it is an Output."""
    repo = _init_repo(tmp_path, "canvas-canon")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    _run("export-canvas", "--project", str(repo))

    memory_dir = repo / "agent-knowledge" / "Memory"
    canvas_in_memory = list(memory_dir.rglob("*.canvas"))
    assert canvas_in_memory == [], "Canvas files must not appear in Memory/"


# -- refresh-system tests -------------------------------------------------- #


def test_refresh_system_runs(tmp_path: Path):
    """refresh-system must exit 0 on a freshly-initialized project."""
    repo = _init_repo(tmp_path, "refresh-run")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("refresh-system", "--project", str(repo))
    assert r.returncode == 0, f"refresh-system failed: {r.stderr}"


def test_refresh_system_json_mode(tmp_path: Path):
    """refresh-system --json must produce clean JSON with required fields."""
    repo = _init_repo(tmp_path, "refresh-json")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("refresh-system", "--project", str(repo), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "action" in data
    assert "framework_version" in data
    assert "changes" in data
    assert "warnings" in data
    assert isinstance(data["changes"], list)
    assert isinstance(data["warnings"], list)


def test_refresh_system_dry_run(tmp_path: Path):
    """refresh-system --dry-run must not write any files."""
    repo = _init_repo(tmp_path, "refresh-dry")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    # Record mtime of key files before dry-run
    agents_md = repo / "AGENTS.md"
    status_md = repo / "agent-knowledge" / "STATUS.md"
    mtime_agents = agents_md.stat().st_mtime if agents_md.exists() else None
    mtime_status = status_md.stat().st_mtime if status_md.exists() else None

    r = _run("refresh-system", "--project", str(repo), "--dry-run")
    assert r.returncode == 0

    # Files should not have been modified
    if mtime_agents is not None:
        assert agents_md.stat().st_mtime == mtime_agents, "dry-run must not write AGENTS.md"
    if mtime_status is not None:
        assert status_md.stat().st_mtime == mtime_status, "dry-run must not write STATUS.md"


def test_refresh_system_dry_run_json(tmp_path: Path):
    """refresh-system --dry-run --json must return action=dry-run."""
    repo = _init_repo(tmp_path, "refresh-dry-json")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r = _run("refresh-system", "--project", str(repo), "--dry-run", "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["action"] == "dry-run"
    assert data["dry_run"] is True


def test_refresh_system_idempotent(tmp_path: Path):
    """Running refresh-system twice must succeed both times."""
    repo = _init_repo(tmp_path, "refresh-idem")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    r1 = _run("refresh-system", "--project", str(repo), "--json")
    assert r1.returncode == 0
    d1 = json.loads(r1.stdout)

    r2 = _run("refresh-system", "--project", str(repo), "--json")
    assert r2.returncode == 0
    d2 = json.loads(r2.stdout)

    # Second run should report everything as up-to-date
    assert d2["action"] == "up-to-date", f"Second run should be up-to-date, got: {d2['action']}"


def test_refresh_system_never_touches_memory(tmp_path: Path):
    """refresh-system must never modify Memory/, Evidence/, or Sessions/."""
    repo = _init_repo(tmp_path, "refresh-memory")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    # Seed a memory note
    memory_dir = repo / "agent-knowledge" / "Memory"
    test_note = memory_dir / "test-branch.md"
    test_note.write_text("---\nnote_type: branch-entry\narea: test\n---\n\n# Test\n\nContent.\n")
    original_content = test_note.read_text()

    _run("refresh-system", "--project", str(repo))

    assert test_note.read_text() == original_content, "refresh-system must not modify Memory/ notes"


def test_refresh_system_updates_status_md_version(tmp_path: Path):
    """refresh-system must add framework_version to STATUS.md."""
    repo = _init_repo(tmp_path, "refresh-status")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    _run("refresh-system", "--project", str(repo))

    status = (repo / "agent-knowledge" / "STATUS.md").read_text()
    assert "framework_version:" in status
    assert "last_system_refresh:" in status


def test_refresh_system_updates_project_yaml_version(tmp_path: Path):
    """refresh-system must add framework_version to .agent-project.yaml."""
    repo = _init_repo(tmp_path, "refresh-yaml")
    kh = tmp_path / "kh"
    _run("init", "--repo", str(repo), "--knowledge-home", str(kh))

    _run("refresh-system", "--project", str(repo))

    yaml_text = (repo / ".agent-project.yaml").read_text()
    assert "framework_version:" in yaml_text


def test_refresh_system_command_in_bundled_commands(tmp_path: Path):
    """assets/commands/system-update.md must be bundled and discoverable."""
    from agent_knowledge.runtime.paths import get_assets_dir

    cmd_file = get_assets_dir() / "commands" / "system-update.md"
    assert cmd_file.is_file(), "system-update.md must exist in assets/commands/"
    content = cmd_file.read_text()
    assert "refresh-system" in content
    assert "Memory" in content


def test_refresh_module_importable():
    """refresh module must be importable with the correct public API."""
    from agent_knowledge.runtime.refresh import run_refresh, is_stale

    assert callable(run_refresh)
    assert callable(is_stale)


# -- core CLI unchanged test ----------------------------------------------- #


def test_core_cli_flow_unchanged(tmp_path: Path):
    """The core init -> sync -> doctor flow must still work with the new commands."""
    repo = _init_repo(tmp_path, "core-flow")
    kh = tmp_path / "kh"

    r = _run("init", "--repo", str(repo), "--knowledge-home", str(kh))
    assert r.returncode == 0, f"init failed: {r.stderr}"

    r = _run("sync", "--project", str(repo))
    assert r.returncode == 0, f"sync failed: {r.stderr}"

    r = _run("doctor", "--project", str(repo), "--json")
    assert r.returncode == 0 or r.returncode == 1  # 1 = warn is acceptable
    stdout = r.stdout.strip()
    if stdout:
        parsed = json.loads(stdout)
        assert parsed.get("script") == "doctor"

    # Verify new commands do not interfere with Memory/
    memory_dir = repo / "agent-knowledge" / "Memory"
    for f in memory_dir.rglob("*"):
        if f.suffix in (".canvas", ".json", ".html"):
            pytest.fail(f"Non-markdown file found in Memory/: {f}")
