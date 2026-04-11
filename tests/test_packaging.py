"""Verify packaging: imports, assets, entry points."""

from __future__ import annotations

from pathlib import Path


def test_package_importable():
    import agent_knowledge

    assert hasattr(agent_knowledge, "__version__")
    assert isinstance(agent_knowledge.__version__, str)


def test_assets_dir_resolves():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    assert assets.is_dir()


def test_bundled_scripts_exist():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    for name in [
        "install-project-links.sh",
        "bootstrap-memory-tree.sh",
        "import-agent-history.sh",
        "update-knowledge.sh",
        "doctor.sh",
        "validate-knowledge.sh",
        "ship.sh",
        "global-knowledge-sync.sh",
        "graphify-sync.sh",
        "compact-memory.sh",
        "measure-token-savings.py",
    ]:
        assert (assets / "scripts" / name).is_file(), f"Missing script: {name}"


def test_bundled_common_lib_exists():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    assert (assets / "scripts" / "lib" / "knowledge-common.sh").is_file()


def test_bundled_templates_exist():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    assert (assets / "templates" / "project" / ".agent-project.yaml").is_file()
    assert (assets / "templates" / "memory" / "branch.template.md").is_file()
    assert (assets / "templates" / "memory" / "MEMORY.root.template.md").is_file()


def test_bundled_rules_exist():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    assert (assets / "rules" / "memory-bootstrap.mdc").is_file()
    assert (assets / "rules" / "memory-writeback.mdc").is_file()


def test_bundled_commands_exist():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    assert (assets / "commands" / "knowledge-sync.md").is_file()
    assert (assets / "commands" / "doctor.md").is_file()


def test_get_script_resolves():
    from agent_knowledge.runtime.paths import get_script

    path = get_script("doctor.sh")
    assert path.is_file()
    assert path.name == "doctor.sh"


def test_get_script_missing_raises():
    import pytest
    from agent_knowledge.runtime.paths import get_script

    with pytest.raises(FileNotFoundError):
        get_script("nonexistent-script.sh")


def test_capture_module_importable():
    from agent_knowledge.runtime.capture import record, list_captures

    assert callable(record)
    assert callable(list_captures)


def test_index_module_importable():
    from agent_knowledge.runtime.index import build_index, write_index, search

    assert callable(build_index)
    assert callable(write_index)
    assert callable(search)


def test_viewer_module_importable():
    from agent_knowledge.runtime.viewer import export_html

    assert callable(export_html)


def test_bundled_captures_readme_exists():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    captures_readme = assets / "templates" / "project" / "agent-knowledge" / "Evidence" / "captures" / "README.md"
    assert captures_readme.is_file(), "Evidence/captures/README.md template must be bundled"


def test_site_module_importable():
    from agent_knowledge.runtime.site import generate_site, build_site_data

    assert callable(generate_site)
    assert callable(build_site_data)


def test_canvas_module_importable():
    from agent_knowledge.runtime.canvas import export_canvas, build_canvas

    assert callable(export_canvas)
    assert callable(build_canvas)


def test_importer_module_importable():
    from agent_knowledge.runtime.importer import clean_import, html_to_markdown

    assert callable(clean_import)
    assert callable(html_to_markdown)


def test_html_to_markdown_strips_nav():
    """html_to_markdown must strip navigation elements."""
    from agent_knowledge.runtime.importer import html_to_markdown

    html = (
        "<html><body>"
        "<nav>Skip navigation</nav>"
        "<h1>Real Title</h1>"
        "<p>Real content here.</p>"
        "<footer>Footer noise</footer>"
        "</body></html>"
    )
    title, body = html_to_markdown(html)
    assert "Real Title" in title or "Real Title" in body
    assert "Real content" in body
    # Nav and footer should be removed
    assert "Skip navigation" not in body
    assert "Footer noise" not in body


def test_html_to_markdown_preserves_headings():
    from agent_knowledge.runtime.importer import html_to_markdown

    html = "<html><body><h1>Top</h1><h2>Second</h2><p>Text</p></body></html>"
    _title, body = html_to_markdown(html)
    assert "# Top" in body or "Top" in body
    assert "## Second" in body or "Second" in body


def test_bundled_skills_exist():
    """New focused skills must be bundled."""
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    new_skills = [
        "project-memory-writing",
        "evidence-handling",
        "ontology-inference",
        "branch-note-convention",
        "obsidian-compatible-writing",
        "clean-web-import",
    ]
    for skill in new_skills:
        path = assets / "skills" / skill / "SKILL.md"
        assert path.is_file(), f"Bundled skill missing: skills/{skill}/SKILL.md"


def test_skills_index_bundled():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    index = assets / "skills" / "SKILLS.md"
    assert index.is_file(), "assets/skills/SKILLS.md must be bundled"


def test_bundled_cursor_command_templates_exist():
    from agent_knowledge.runtime.paths import get_assets_dir

    assets = get_assets_dir()
    for cmd in ("memory-update.md", "system-update.md"):
        path = assets / "templates" / "integrations" / "cursor" / "commands" / cmd
        assert path.is_file(), f"Cursor command template missing: {path}"


def test_refresh_module_has_check_cursor_integration():
    from agent_knowledge.runtime.refresh import check_cursor_integration

    assert callable(check_cursor_integration)


def test_readme_mentions_obsidian_optional():
    """README must make clear Obsidian is optional."""
    readme = (
        __import__("pathlib").Path(__file__).parent.parent / "README.md"
    ).read_text().lower()
    assert "optional" in readme
    assert "obsidian" in readme
    # Must NOT claim Obsidian is required
    assert "obsidian is required" not in readme
    assert "must use obsidian" not in readme
