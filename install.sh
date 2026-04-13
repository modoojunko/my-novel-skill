#!/usr/bin/env bash
# install.sh - Install my-novel-v2 skill (Linux/macOS)
set -euo pipefail

PLATFORM="${1:-workbuddy}"
SKILL_NAME="my-novel-v2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "$PLATFORM" in
    workbuddy)
        DEST="$HOME/.workbuddy/skills/$SKILL_NAME"
        ;;
    claude)
        DEST="$HOME/.claude/skills/$SKILL_NAME"
        ;;
    openclaw)
        DEST="$HOME/.openclaw/skills/$SKILL_NAME"
        ;;
    *)
        echo "Usage: $0 [workbuddy|claude|openclaw]"
        exit 1
        ;;
esac

if [ ! -f "$SCRIPT_DIR/SKILL.md" ]; then
    echo "Error: SKILL.md not found in $SCRIPT_DIR"
    exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST"
cp "$SCRIPT_DIR/SKILL.md" "$DEST/"
cp "$SCRIPT_DIR/README.md" "$DEST/" 2>/dev/null || true
cp "$SCRIPT_DIR/install.md" "$DEST/" 2>/dev/null || true
cp "$SCRIPT_DIR/story.py" "$DEST/"
cp -r "$SCRIPT_DIR/src_v2" "$DEST/src"
cp -r "$SCRIPT_DIR/docs" "$DEST/docs" 2>/dev/null || true

echo "Installed $SKILL_NAME to $DEST"
echo "Files: SKILL.md, README.md, install.md, story.py, src/, docs/"
