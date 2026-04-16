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
    hermes)
        DEST="$HOME/.hermes/skills/$SKILL_NAME"
        ;;
    *)
        echo "Usage: $0 [workbuddy|claude|openclaw|hermes]"
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
cp -r "$SCRIPT_DIR/src_v2" "$DEST/src_v2"
cp -r "$SCRIPT_DIR/docs" "$DEST/docs" 2>/dev/null || true

echo "Installed $SKILL_NAME to $DEST"
echo "Files: SKILL.md, README.md, install.md, story.py, src_v2/, docs/"

# Hermes专用：创建wrapper脚本，让story命令可用
if [ "$PLATFORM" = "hermes" ]; then
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
    
    WRAPPER="$BIN_DIR/story"
    cat > "$WRAPPER" << 'EOF'
#!/usr/bin/env bash
# story - Wrapper for my-novel-skill story.py
SKILL_DIR="$HOME/.hermes/skills/my-novel-v2"
if [ -f "$SKILL_DIR/story.py" ]; then
    # Try python3 first, then python
    if command -v python3 &> /dev/null; then
        python3 "$SKILL_DIR/story.py" "$@"
    elif command -v python &> /dev/null; then
        python "$SKILL_DIR/story.py" "$@"
    else
        echo "Error: python or python3 not found"
        exit 1
    fi
else
    echo "Error: my-novel-skill not found at $SKILL_DIR"
    echo "Please run install.sh hermes first"
    exit 1
fi
EOF
    chmod +x "$WRAPPER"
    
    echo ""
    echo "✅ Hermes installation complete!"
    echo "   - Wrapper script created at: $WRAPPER"
    echo "   - You can now use 'story' command directly!"
    echo ""
    echo "   If 'story' command is not found, add this to your ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
