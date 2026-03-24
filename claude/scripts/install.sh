#!/bin/bash
#
# Install Claude Code global rules into ~/.claude/CLAUDE.md
#
# Usage:
#   ./install.sh              # install global rules
#   ./install.sh /path/to/project  # also install project template into project root
#
# The global rules are appended under a managed section marker so re-running
# this script is safe (it replaces the section, not appends again).
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
GLOBAL_SOURCE="$SCRIPT_DIR/../global.md"
GLOBAL_TARGET="$CLAUDE_DIR/CLAUDE.md"
PROJECT="${1:-}"

MARKER_START="<!-- agents-rules:global:start -->"
MARKER_END="<!-- agents-rules:global:end -->"

mkdir -p "$CLAUDE_DIR"

install_global() {
    local content
    content="$(cat "$GLOBAL_SOURCE")"

    if [ -f "$GLOBAL_TARGET" ]; then
        # Remove existing managed section if present
        if grep -q "$MARKER_START" "$GLOBAL_TARGET" 2>/dev/null; then
            # Strip from marker-start to marker-end inclusive
            local tmp
            tmp="$(mktemp)"
            awk "/$MARKER_START/{flag=1} !flag{print} /$MARKER_END/{flag=0}" "$GLOBAL_TARGET" > "$tmp"
            mv "$tmp" "$GLOBAL_TARGET"
            echo "  updated existing section in $GLOBAL_TARGET"
        else
            echo "  appending to existing $GLOBAL_TARGET"
            echo "" >> "$GLOBAL_TARGET"
        fi
    else
        echo "  creating $GLOBAL_TARGET"
    fi

    {
        echo "$MARKER_START"
        echo "$content"
        echo "$MARKER_END"
    } >> "$GLOBAL_TARGET"

    echo "  global rules installed -> $GLOBAL_TARGET"
}

install_project_template() {
    local project_dir
    project_dir="$(cd "$1" && pwd)"
    local target="$project_dir/CLAUDE.md"
    local source="$SCRIPT_DIR/../project-template.md"

    if [ -f "$target" ]; then
        echo "  $target already exists — skipping (edit manually)"
    else
        cp "$source" "$target"
        echo "  project template installed -> $target"
        echo "  Edit CLAUDE.md with your project-specific rules"
    fi
}

echo "Installing Claude Code rules..."
echo ""

install_global

if [ -n "$PROJECT" ]; then
    install_project_template "$PROJECT"
fi

echo ""
echo "Done."
echo ""
echo "Claude Code reads:"
echo "  ~/.claude/CLAUDE.md         <- global rules (all projects)"
echo "  <project>/CLAUDE.md         <- project rules (this project only)"
