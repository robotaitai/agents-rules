"""CLI entry point for agent-knowledge."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

from agent_knowledge import __version__
from agent_knowledge.runtime.paths import get_assets_dir
from agent_knowledge.runtime.shell import run_bash_script, run_python_script


def _add_common_flags(
    args: list[str],
    *,
    dry_run: bool = False,
    json_mode: bool = False,
    force: bool = False,
) -> list[str]:
    if dry_run:
        args.append("--dry-run")
    if json_mode:
        args.append("--json")
    if force:
        args.append("--force")
    return args


@click.group()
@click.version_option(version=__version__, prog_name="agent-knowledge")
def main() -> None:
    """Adaptive, file-based project knowledge for AI coding agents."""


# -- init ------------------------------------------------------------------ #


@main.command()
@click.option("--slug", default=None, help="Project slug (default: repo directory name).")
@click.option("--repo", default=".", type=click.Path(exists=True), help="Project repo path (default: cwd).")
@click.option("--knowledge-home", default=None, help="Knowledge root (default: $AGENT_KNOWLEDGE_HOME or ~/agent-os/projects).")
@click.option("--real-path", default=None, help="Explicit external knowledge folder path.")
@click.option("--no-integrations", is_flag=True, help="Skip auto-detection and installation of tool integrations.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def init(
    slug: str | None,
    repo: str,
    knowledge_home: str | None,
    real_path: str | None,
    no_integrations: bool,
    dry_run: bool,
    json_mode: bool,
    force: bool,
) -> None:
    """Initialize a project: create knowledge folder, pointer, and metadata.

    When run with no arguments inside a repo, infers slug from the directory
    name, auto-detects tool integrations, and installs everything needed.
    """
    from agent_knowledge.runtime.integrations import detect, install_all

    repo_path = Path(repo).resolve()
    if slug is None:
        slug = _sanitize_slug(repo_path.name)

    if knowledge_home is None:
        knowledge_home = os.environ.get("AGENT_KNOWLEDGE_HOME")

    # Core setup: symlink, .agent-project.yaml, AGENTS.md, bootstrap
    args = ["--slug", slug, "--repo", str(repo_path)]
    if knowledge_home:
        args.extend(["--knowledge-home", knowledge_home])
    if real_path:
        args.extend(["--real-path", real_path])
    args.append("--install-hooks")
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode, force=force)
    rc = run_bash_script("install-project-links.sh", args)
    if rc != 0:
        sys.exit(rc)

    # Auto-detect and install tool integrations
    if not no_integrations:
        detected = detect(repo_path)
        if not json_mode:
            tools_found = [t for t, v in detected.items() if v]
            click.echo("", err=True)
            click.echo(f"Detected integrations: {', '.join(tools_found) if tools_found else 'none'}", err=True)

        results = install_all(repo_path, detected, dry_run=dry_run, force=force)
        if not json_mode:
            for tool, actions in results.items():
                click.echo(f"  [{tool}]", err=True)
                for action in actions:
                    click.echo(action, err=True)

    if not json_mode:
        prompt = "Read AGENTS.md and ./agent-knowledge/STATUS.md, then onboard this project."
        border = "+" + "-" * (len(prompt) + 2) + "+"
        click.echo("", err=True)
        click.secho("Ready. Open your agent and send:", bold=True, err=True)
        click.echo("", err=True)
        click.secho(border, fg="cyan", err=True)
        click.secho(f"| {prompt} |", fg="cyan", bold=True, err=True)
        click.secho(border, fg="cyan", err=True)
        click.echo("", err=True)

        _maybe_star()


_REPO_URL = "https://github.com/robotaitai/agent-knowledge"
_STAR_MARKER = Path.home() / ".agent-knowledge-starred"


def _maybe_star() -> None:
    """Prompt to star the repo once, then never again. Skips in non-interactive shells."""
    if _STAR_MARKER.exists():
        return
    if not sys.stderr.isatty():
        return
    try:
        click.echo("", err=True)
        if click.confirm(
            click.style("Like agent-knowledge? Star it on GitHub", fg="yellow"),
            default=True,
            err=True,
        ):
            import webbrowser

            webbrowser.open(_REPO_URL)
    except (EOFError, KeyboardInterrupt):
        click.echo("", err=True)
    _STAR_MARKER.touch()


def _sanitize_slug(name: str) -> str:
    """Normalize a directory name into a safe project slug."""
    import re
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


# -- sync ------------------------------------------------------------------ #


@main.command()
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def sync(project: str, dry_run: bool, json_mode: bool) -> None:
    """Sync memory branches, roll up sessions, and extract git evidence.

    \b
    Steps:
      1. Copy agent_docs/memory/*.md -> agent-knowledge/Memory/ (newer only)
      2. Scan Sessions/ and rebuild Dashboards/session-rollup.md
      3. Extract recent git log into Evidence/raw/git-recent.md
      4. Update last_project_sync in STATUS.md
    """
    import json as json_mod

    from agent_knowledge.runtime.sync import run_sync

    repo_path = Path(project).resolve()
    results = run_sync(repo_path, dry_run=dry_run)

    if json_mode:
        click.echo(json_mod.dumps({"sync": results}, indent=2))
    else:
        for step, actions in results.items():
            click.echo(f"[{step}]", err=True)
            for action in actions:
                click.echo(action, err=True)
            click.echo("", err=True)

        if dry_run:
            click.echo("(dry-run -- no changes written)", err=True)
        else:
            click.secho("Sync complete.", bold=True, err=True)


# -- bootstrap ------------------------------------------------------------- #


@main.command()
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--profile", default=None, help="Profile hint (web-app, robotics, ml-platform, hybrid). Advisory only.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def bootstrap(
    project: str,
    profile: str | None,
    dry_run: bool,
    json_mode: bool,
    force: bool,
) -> None:
    """Bootstrap or repair the project memory tree."""
    args = ["--project", project]
    if profile:
        args.extend(["--profile", profile])
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode, force=force)
    sys.exit(run_bash_script("bootstrap-memory-tree.sh", args))


# -- import ---------------------------------------------------------------- #


@main.command(name="import")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def import_cmd(project: str, dry_run: bool, json_mode: bool) -> None:
    """Import repo history and evidence into Evidence/."""
    args = ["--project", project]
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode)
    sys.exit(run_bash_script("import-agent-history.sh", args))


# -- update ---------------------------------------------------------------- #


@main.command()
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--compact", is_flag=True, help="Run memory compaction after sync.")
@click.option("--decision-title", default=None, help="Record a decision note with this title.")
@click.option("--decision-why", default=None, help="Reason for the decision.")
@click.option("--decision-slug", default=None, help="Custom slug for the decision note.")
@click.option("--summary-file", default=None, hidden=True, help="Write JSON summary to file.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def update(
    project: str,
    compact: bool,
    decision_title: str | None,
    decision_why: str | None,
    decision_slug: str | None,
    summary_file: str | None,
    dry_run: bool,
    json_mode: bool,
) -> None:
    """Sync project changes into the knowledge tree."""
    args = ["--project", project]
    if compact:
        args.append("--compact")
    if decision_title:
        args.extend(["--decision-title", decision_title])
    if decision_why:
        args.extend(["--decision-why", decision_why])
    if decision_slug:
        args.extend(["--decision-slug", decision_slug])
    if summary_file:
        args.extend(["--summary-file", summary_file])
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode)
    sys.exit(run_bash_script("update-knowledge.sh", args))


# -- doctor ---------------------------------------------------------------- #


@main.command()
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def doctor(project: str, dry_run: bool, json_mode: bool) -> None:
    """Validate setup, pointer resolution, and note structure.

    Reports whether the project integration is stale and suggests
    `agent-knowledge refresh-system` when the framework version has changed.
    """
    from agent_knowledge.runtime.refresh import is_stale

    repo_root = Path(project).resolve()
    stale, prior, current = is_stale(repo_root)

    if stale and not json_mode:
        if prior:
            click.secho(
                f"Warning: project integration is at v{prior}, installed framework is v{current}. "
                f"Run: agent-knowledge refresh-system",
                fg="yellow",
                err=True,
            )
        else:
            click.secho(
                f"Warning: no framework_version in STATUS.md. "
                f"Run: agent-knowledge refresh-system",
                fg="yellow",
                err=True,
            )
        click.echo("", err=True)

    args = ["--project", project]
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode)
    sys.exit(run_bash_script("doctor.sh", args))


# -- validate -------------------------------------------------------------- #


@main.command()
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def validate(project: str, dry_run: bool, json_mode: bool) -> None:
    """Validate the knowledge layout and operational links."""
    args = ["--project", project]
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode)
    sys.exit(run_bash_script("validate-knowledge.sh", args))


# -- ship ------------------------------------------------------------------ #


@main.command()
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--message", default=None, help="Custom commit message.")
@click.option("--open-pr", is_flag=True, help="Create a pull request after pushing.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def ship(
    project: str,
    message: str | None,
    open_pr: bool,
    dry_run: bool,
    json_mode: bool,
) -> None:
    """Validate, sync, commit, push, and optionally create a PR."""
    args = ["--project", project]
    if message:
        args.extend(["--message", message])
    if open_pr:
        args.append("--open-pr")
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode)
    sys.exit(run_bash_script("ship.sh", args))


# -- global-sync ----------------------------------------------------------- #


@main.command("global-sync")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def global_sync(project: str, dry_run: bool, json_mode: bool) -> None:
    """Import safe local tooling config into the knowledge tree."""
    args = ["--project", project]
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode)
    sys.exit(run_bash_script("global-knowledge-sync.sh", args))


# -- graphify-sync --------------------------------------------------------- #


@main.command("graphify-sync")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--source", default=None, help="Override source path for graph artifacts.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def graphify_sync(
    project: str,
    source: str | None,
    dry_run: bool,
    json_mode: bool,
) -> None:
    """Import optional graph/discovery artifacts into Evidence and Outputs."""
    args = ["--project", project]
    if source:
        args.extend(["--source", source])
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode)
    sys.exit(run_bash_script("graphify-sync.sh", args))


# -- compact --------------------------------------------------------------- #


@main.command()
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def compact(project: str, dry_run: bool, json_mode: bool) -> None:
    """Compact memory notes conservatively."""
    args = ["--project", project]
    _add_common_flags(args, dry_run=dry_run, json_mode=json_mode)
    sys.exit(run_bash_script("compact-memory.sh", args))


# -- measure-tokens -------------------------------------------------------- #


@main.command(
    "measure-tokens",
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": False,
    },
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def measure_tokens(args: tuple[str, ...]) -> None:
    """Estimate repo-controlled context token savings.

    \b
    Subcommands: compare, log-run, summarize-log.
    Pass --help after the subcommand for its options:
      agent-knowledge measure-tokens compare --help
    """
    if not args:
        sys.exit(run_python_script("measure-token-savings.py", ["--help"]))
    sys.exit(run_python_script("measure-token-savings.py", list(args)))


# -- search ---------------------------------------------------------------- #


@main.command()
@click.argument("query", required=False, default="")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--limit", default=10, show_default=True, help="Max results.")
@click.option("--all", "include_all", is_flag=True, help="Include Evidence/Outputs in results (default: Memory-first).")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def search(query: str, project: str, limit: int, include_all: bool, json_mode: bool) -> None:
    """Search the knowledge index. Prefers Memory/ over Evidence/Outputs.

    \b
    Layer 1: loads the compact index (Outputs/knowledge-index.json).
    Layer 2: returns a ranked shortlist of relevant notes.
    Layer 3: use --full or read the note files directly for full content.
    """
    import json as json_mod

    from agent_knowledge.runtime.index import search as idx_search

    vault = Path(project).resolve() / "agent-knowledge"
    if not vault.is_dir():
        click.echo("No agent-knowledge vault found. Run: agent-knowledge init", err=True)
        sys.exit(1)

    if not query:
        click.echo("Usage: agent-knowledge search <query>", err=True)
        sys.exit(0)

    results = idx_search(vault, query, max_results=limit, include_non_canonical=include_all)

    if json_mode:
        click.echo(json_mod.dumps({"query": query, "results": results}, indent=2))
        return

    if not results:
        click.echo(f"No results for: {query}", err=True)
        return

    click.secho(f"Results for '{query}' ({len(results)} found):", bold=True, err=True)
    for r in results:
        canonical_tag = "[Memory]" if r["canonical"] else f"[{r['folder']}]"
        entry_tag = " (branch entry)" if r["is_branch_entry"] else ""
        click.echo(f"\n  {canonical_tag}{entry_tag} {r['path']}", err=True)
        click.echo(f"    {r['title']}", err=True)
        if r.get("summary"):
            click.echo(f"    {r['summary'][:120]}", err=True)


# -- index ----------------------------------------------------------------- #


@main.command("index")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def index_cmd(project: str, dry_run: bool, json_mode: bool) -> None:
    """Regenerate the knowledge index in Outputs/.

    Produces Outputs/knowledge-index.json (machine-readable) and
    Outputs/knowledge-index.md (compact human/agent catalog).
    The index is non-canonical output -- not curated memory.
    """
    import json as json_mod

    from agent_knowledge.runtime.index import write_index

    vault = Path(project).resolve() / "agent-knowledge"
    if not vault.is_dir():
        click.echo("No agent-knowledge vault found. Run: agent-knowledge init", err=True)
        sys.exit(1)

    actions = write_index(vault, dry_run=dry_run)

    if json_mode:
        click.echo(json_mod.dumps({"index": actions}, indent=2))
    else:
        for action in actions:
            click.echo(action, err=True)


# -- export-html ----------------------------------------------------------- #


@main.command("export-html")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--output-dir", default=None, type=click.Path(), help="Output directory (default: Outputs/site/).")
@click.option("--include-evidence", is_flag=True, default=True, show_default=True, help="Include Evidence/ notes in the site.")
@click.option("--no-evidence", "include_evidence", flag_value=False, help="Exclude Evidence/ notes from the site.")
@click.option("--dry-run", is_flag=True, help="Preview what would be generated without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON summary only.")
@click.option("--open", "open_browser", is_flag=True, help="Open the generated site in the browser after export.")
def export_html(
    project: str,
    output_dir: str | None,
    include_evidence: bool,
    dry_run: bool,
    json_mode: bool,
    open_browser: bool,
) -> None:
    """Build a polished static HTML site from the knowledge vault.

    Generates Outputs/site/index.html and Outputs/site/data/knowledge.json.
    Opens in any browser without Obsidian. Memory/ is primary; Evidence/ and
    Outputs/ are clearly marked non-canonical.

    \b
    Examples:
      agent-knowledge export-html
      agent-knowledge export-html --open
      agent-knowledge export-html --dry-run
      agent-knowledge export-html --no-evidence
    """
    import json as json_mod

    from agent_knowledge.runtime.site import generate_site

    vault = Path(project).resolve() / "agent-knowledge"
    if not vault.is_dir():
        click.echo("No agent-knowledge vault found. Run: agent-knowledge init", err=True)
        sys.exit(1)

    out_dir = Path(output_dir).resolve() if output_dir else None
    result = generate_site(
        vault,
        out_dir,
        dry_run=dry_run,
        include_evidence=include_evidence,
    )

    if json_mode:
        click.echo(json_mod.dumps(result, indent=2))
        return

    if dry_run:
        click.echo(f"[dry-run] would generate site: {result['site_dir']}", err=True)
        click.echo(f"  {result['branch_count']} branches, {result['decision_count']} decisions, {result['evidence_count']} evidence items", err=True)
    else:
        action = result["action"]
        click.echo(f"{action}: {result['site_dir']}", err=True)
        click.echo(f"  index.html — {result['branch_count']} branches, {result['decision_count']} decisions, {result['note_count']} notes total", err=True)
        click.echo(f"  data/knowledge.json — structured site data", err=True)
        if open_browser:
            import webbrowser
            webbrowser.open(Path(result["index_html"]).as_uri())


# -- view ------------------------------------------------------------------ #


@main.command()
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--output-dir", default=None, type=click.Path(), help="Override output directory for the site.")
def view(project: str, output_dir: str | None) -> None:
    """Build the knowledge site and open it in the browser.

    Equivalent to export-html --open. No Obsidian required.
    The site is generated into Outputs/site/ and opened via file://.
    """
    import webbrowser

    from agent_knowledge.runtime.site import generate_site

    vault = Path(project).resolve() / "agent-knowledge"
    if not vault.is_dir():
        click.echo("No agent-knowledge vault found. Run: agent-knowledge init", err=True)
        sys.exit(1)

    out_dir = Path(output_dir).resolve() if output_dir else None
    result = generate_site(vault, out_dir)
    click.echo(f"{result['action']}: {result['site_dir']}", err=True)
    webbrowser.open(Path(result["index_html"]).as_uri())


# -- clean-import ---------------------------------------------------------- #


@main.command("clean-import")
@click.argument("source")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--slug", default=None, help="Override output filename slug.")
@click.option("--output-dir", default=None, type=click.Path(), help="Override output directory (default: Evidence/imports/).")
@click.option("--dry-run", is_flag=True, help="Preview without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON only.")
def clean_import(
    source: str,
    project: str,
    slug: str | None,
    output_dir: str | None,
    dry_run: bool,
    json_mode: bool,
) -> None:
    """Import a URL or HTML file as cleaned evidence into Evidence/imports/.

    Strips navigation, ads, scripts, and boilerplate. Writes clean markdown
    with YAML frontmatter marking it as non-canonical evidence.

    \b
    Examples:
      agent-knowledge clean-import https://docs.example.com/api
      agent-knowledge clean-import page.html --slug api-ref-2025-01-15
      agent-knowledge clean-import https://... --dry-run
    """
    import json as json_mod

    from agent_knowledge.runtime.importer import clean_import as do_import

    vault = Path(project).resolve() / "agent-knowledge"
    if output_dir:
        out_dir = Path(output_dir).resolve()
    else:
        out_dir = vault / "Evidence" / "imports"

    try:
        path, action, title = do_import(source, out_dir, slug=slug, dry_run=dry_run)
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if json_mode:
        click.echo(
            json_mod.dumps(
                {
                    "action": action,
                    "path": str(path),
                    "title": title,
                    "source": source,
                    "dry_run": dry_run,
                },
                indent=2,
            )
        )
    else:
        if dry_run:
            click.echo(f"[dry-run] would create: {path}", err=True)
        elif action == "exists":
            click.echo(f"exists (same content): {path}", err=True)
        else:
            click.echo(f"{action}: {path}", err=True)
        if title and not json_mode:
            click.echo(f"  title: {title}", err=True)


# -- export-canvas --------------------------------------------------------- #


@main.command("export-canvas")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--output", default=None, type=click.Path(), help="Output .canvas path (default: Outputs/knowledge-export.canvas).")
@click.option("--dry-run", is_flag=True, help="Preview without writing.")
def export_canvas(project: str, output: str | None, dry_run: bool) -> None:
    """Export the knowledge vault as an Obsidian Canvas (.canvas) file.

    Generates a spatial graph of Memory/ notes with edges derived from
    markdown links. Open in Obsidian with Core plugins > Canvas enabled.

    This is an optional Output: non-canonical and regeneratable.
    The system works fully without it.
    """
    from agent_knowledge.runtime.canvas import export_canvas as do_export

    vault = Path(project).resolve() / "agent-knowledge"
    if not vault.is_dir():
        click.echo("No agent-knowledge vault found. Run: agent-knowledge init", err=True)
        sys.exit(1)

    out_path = Path(output).resolve() if output else None
    path, action = do_export(vault, out_path, dry_run=dry_run)

    if dry_run:
        click.echo(f"[dry-run] would write: {path}", err=True)
    else:
        click.echo(f"{action}: {path}", err=True)
        click.echo("  Open in Obsidian: Core plugins > Canvas", err=True)


# -- refresh-system -------------------------------------------------------- #


@main.command("refresh-system")
@click.option("--project", default=".", type=click.Path(exists=True), help="Project repo root.")
@click.option("--dry-run", is_flag=True, help="Preview what would change without writing.")
@click.option("--json", "json_mode", is_flag=True, help="Output JSON summary only.")
@click.option("--force", is_flag=True, hidden=True, help="Force updates even when up-to-date.")
def refresh_system(project: str, dry_run: bool, json_mode: bool, force: bool) -> None:
    """Refresh project integration files to the current framework version.

    Updates bridge files (AGENTS.md header, Cursor hooks, CLAUDE.md, Codex config)
    and metadata version markers (STATUS.md, .agent-project.yaml).

    Memory/, Evidence/, Sessions/, and project-curated content are never touched.
    Safe to run after `pip install -U agent-knowledge-cli`.

    \b
    Examples:
      agent-knowledge refresh-system
      agent-knowledge refresh-system --dry-run
      agent-knowledge refresh-system --json
    """
    import json as json_mod

    from agent_knowledge.runtime.refresh import run_refresh

    repo_root = Path(project).resolve()
    result = run_refresh(repo_root, dry_run=dry_run, force=force)

    if json_mode:
        click.echo(json_mod.dumps(result, indent=2))
        return

    action = result["action"]
    version = result["framework_version"]
    prior = result.get("prior_version")
    changes = result.get("changes", [])
    warnings = result.get("warnings", [])

    if not dry_run:
        if action == "up-to-date":
            click.secho(f"Up to date. (framework v{version})", bold=True, err=True)
        else:
            label = "dry-run preview" if dry_run else f"Refreshed to v{version}"
            if prior and prior != version:
                label += f" (was: {prior})"
            click.secho(label, bold=True, err=True)
    else:
        click.echo(f"[dry-run] framework v{version}", err=True)

    click.echo("", err=True)

    # Group changes by action
    for c in changes:
        act = c["action"]
        target = c["target"]
        detail = c.get("detail", "")
        if act == "up-to-date":
            click.echo(f"  ok       {target}  ({detail})", err=True)
        elif act in ("updated", "created"):
            click.secho(f"  updated  {target}  ({detail})", fg="green", err=True)
        elif act == "dry-run":
            click.echo(f"  [would]  {target}  ({detail})", err=True)
        elif act == "skip":
            click.echo(f"  skip     {target}  ({detail})", err=True)
        elif act == "warn":
            click.secho(f"  warn     {target}  ({detail})", fg="yellow", err=True)

    if warnings:
        click.echo("", err=True)
        for w in warnings:
            click.secho(f"Warning: {w}", fg="yellow", err=True)

    click.echo("", err=True)
    if not dry_run and action not in ("up-to-date",):
        click.echo("Next: agent-knowledge doctor --project .", err=True)


# -- setup ----------------------------------------------------------------- #


def _link(src: Path, dst: Path, label: str, dry_run: bool) -> None:
    if dst.is_symlink() and dst.resolve() == src.resolve():
        click.echo(f"  up to date: {label}", err=True)
        return
    if dry_run:
        click.echo(f"  [dry-run] would link: {label}", err=True)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink() if dst.is_file() or dst.is_symlink() else None
    dst.symlink_to(src)
    click.echo(f"  linked: {label}", err=True)


@main.command()
@click.option("--dry-run", is_flag=True, help="Preview changes without writing.")
def setup(dry_run: bool) -> None:
    """Install global Cursor rules, skills, and Claude config into your home directory."""
    assets = get_assets_dir()
    home = Path.home()

    click.echo("agent-knowledge: setting up global config", err=True)
    if dry_run:
        click.echo("(dry-run mode)", err=True)
    click.echo("", err=True)

    # Cursor rules
    rules_dst = home / ".cursor" / "rules"
    rules_dst.mkdir(parents=True, exist_ok=True)
    click.echo("[cursor rules -> ~/.cursor/rules/]", err=True)
    for src in sorted((assets / "rules-global").glob("*.mdc")):
        _link(src, rules_dst / src.name, src.name, dry_run)
    click.echo("", err=True)

    # Skills
    skills_dst = home / ".cursor" / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)
    click.echo("[skills -> ~/.cursor/skills/]", err=True)
    for src in sorted((assets / "skills").iterdir()):
        if src.is_dir():
            _link(src, skills_dst / src.name, src.name, dry_run)
    click.echo("", err=True)

    # Cursor-specific skills
    skills_cursor_dst = home / ".cursor" / "skills-cursor"
    skills_cursor_dst.mkdir(parents=True, exist_ok=True)
    click.echo("[skills-cursor -> ~/.cursor/skills-cursor/]", err=True)
    for src in sorted((assets / "skills-cursor").iterdir()):
        if src.is_dir():
            _link(src, skills_cursor_dst / src.name, src.name, dry_run)
    click.echo("", err=True)

    # Claude Code
    claude_install = assets / "claude" / "scripts" / "install.sh"
    click.echo("[claude code -> ~/.claude/CLAUDE.md]", err=True)
    if dry_run:
        click.echo("  [dry-run] would run: claude/scripts/install.sh", err=True)
    elif claude_install.is_file():
        subprocess.run(["bash", str(claude_install)], check=False)
    click.echo("", err=True)

    click.echo("Done.", err=True)
