#!/usr/bin/env python3
"""
Simplified Novel Workflow CLI
"""

import sys
from pathlib import Path

# Add src_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from src_v2 import init, paths, status, collect, write, archive, export, world, verify, github, publish, migrate, character_cmd, plan


def show_help():
    print("""
Usage: story <command> [options]

Commands:
  init        Initialize new project
  status      Show project status
  collect     Collect information (core, protagonist, etc.)
  world       Manage world building (basic, faction, history, power, etc.)
  character   Manage character knowledge (list, view, update, check, export)
  write       Generate chapter prompt / write
  verify      Verify that chapter follows the prompt
  archive     Archive completed chapter
  unarchive   Unarchive/restore a chapter back to content
  export      Export novel
  github      GitHub Issue 查阅和创建 (check, list, view, create, bug, feature)
  publish     Publish chapters to platforms (check, status, <chapter>, all)
  migrate     Migrate old project structure to new format
  plan        Plan volume/chapter outlines (volume, chapter)

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
        'world': world,
        'character': character_cmd,
        'write': write,
        'verify': verify,
        'archive': archive,
        'unarchive': archive,
        'export': export,
        'github': github,
        'publish': publish,
        'migrate': migrate,
        'plan': plan,
    }

    if cmd in commands:
        if cmd in ('archive', 'unarchive'):
            # Pass command name as first arg so archive module can distinguish
            sys.argv = [sys.argv[0], cmd] + sys.argv[2:]
        else:
            sys.argv = [sys.argv[0]] + sys.argv[2:]
        commands[cmd].main()
    else:
        print(f"  Unknown command: {cmd}")
        print("  Use 'story --help' for available commands")


if __name__ == '__main__':
    main()
