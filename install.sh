#!/usr/bin/env bash
# install.sh - Install my-novel skill (Linux/macOS)
set -euo pipefail

PLATFORM="${1:-workbuddy}"
SKILL_NAME="my-novel"
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
cp "$SCRIPT_DIR/story.py" "$DEST/"
cp -r "$SCRIPT_DIR/src" "$DEST/src"

echo "Installed $SKILL_NAME to $DEST"
echo "Files: SKILL.md, story.py, src/"
