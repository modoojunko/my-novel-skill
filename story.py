#!/usr/bin/env python3
"""
Simplified Novel Workflow CLI
"""

import sys
from pathlib import Path

# Add src_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from src_v2 import init, paths, status, collect


def show_help():
    print("""
Usage: story <command> [options]

Commands:
  init        Initialize new project
  status      Show project status
  collect     Collect information (core, protagonist, etc.)
  plan        Plan outline (volume, chapter)
  write       Generate chapter prompt / write
  archive     Archive completed chapter
  export      Export novel

Use 'story <command> --help' for more info.
""")


def main():
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║          [BOOK] Simplified Novel Workflow v2.0                ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝
""")
        show_help()
        return

    cmd = sys.argv[1].lower()

    if cmd == 'help' or cmd == '--help' or cmd == '-h':
        show_help()
        return

    commands = {
        'init': init,
        'status': status,
        'collect': collect,
        # Add other modules as we implement them
    }

    if cmd in commands:
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        commands[cmd].main()
    else:
        print(f"  Unknown command: {cmd}")
        print("  Use 'story --help' for available commands")


if __name__ == '__main__':
    main()
