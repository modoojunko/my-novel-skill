#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:status - Show project status

Supports JSON output:
- Normal: `story status`
- JSON: `story status --json`
"""

import sys
import argparse
from pathlib import Path
from .paths import find_project_root, load_config, load_project_paths
from . import cli


def get_project_status_dict(root: Path, config: dict, paths: dict) -> dict:
    """Get status as a dictionary for JSON output"""
    book = config.get('book', {})
    structure = config.get('structure', {})
    progress = config.get('progress', {})
    style = config.get('style', {})

    completed = len(progress.get('completed_chapters', []))
    total = structure.get('volumes', 0) * structure.get('chapters_per_volume', 30)
    progress_pct = (completed / total * 100) if total > 0 else 0

    # Check next step
    next_step = None
    if not (paths['info'] / '01-core.yaml').exists():
        next_step = {"command": "story collect core", "description": "Collect core story info"}
    elif not list(paths['characters'].glob('protagonist/*.yaml')):
        next_step = {"command": "story collect protagonist", "description": "Create protagonist"}
    elif not (paths['outline'] / 'volume-001.yaml').exists():
        next_step = {"command": "story plan volume 1", "description": "Plan volume 1"}
    else:
        next_step = {"command": "story write 1 --prompt", "description": "Generate chapter 1 prompt"}

    return {
        "title": book.get('title', 'Untitled'),
        "basic_info": {
            "genre": book.get('genre', 'Unknown'),
            "target_words": int(book.get('target_words') or 0),
            "volumes": structure.get('volumes', 0),
            "chapters_per_volume": structure.get('chapters_per_volume', 30),
        },
        "progress": {
            "current_volume": progress.get('current_volume', 1),
            "current_chapter": progress.get('current_chapter', 0),
            "completed_chapters": completed,
            "total_chapters": total,
            "progress_percent": round(progress_pct, 1),
        },
        "style": {
            "tone": style.get('tone', 'N/A'),
            "pacing": style.get('pacing', 'N/A'),
            "description": style.get('description', 'N/A'),
            "dialogue": style.get('dialogue', 'N/A'),
        },
        "next_step": next_step,
        "project_root": str(root),
    }


def show_status_interactive(root: Path, config: dict, paths: dict):
    """Show status in interactive human-readable format"""
    book = config.get('book', {})
    structure = config.get('structure', {})
    progress = config.get('progress', {})
    style = config.get('style', {})

    cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.BOLD)}")
    cli.print_out(f"  {cli.c(book.get('title', 'Untitled'), cli.Colors.BOLD)}")
    cli.print_out(f"{cli.c('═' * 60, cli.Colors.BOLD)}\n")

    cli.print_out(f"  {cli.c('Basic Info:', cli.Colors.BOLD)}")
    cli.print_out(f"    Genre: {book.get('genre', 'Unknown')}")
    cli.print_out(f"    Target: {int(book.get('target_words') or 0):,} words")
    cli.print_out(f"    Volumes: {structure.get('volumes', 0)}")
    cli.print_out(f"    Chapters/Volume: {structure.get('chapters_per_volume', 30)}")

    cli.print_out(f"\n  {cli.c('Progress:', cli.Colors.BOLD)}")
    completed = len(progress.get('completed_chapters', []))
    total = structure.get('volumes', 0) * structure.get('chapters_per_volume', 30)
    cli.print_out(f"    Current: Volume {progress.get('current_volume', 1)}, Chapter {progress.get('current_chapter', 0)}")
    cli.print_out(f"    Completed: {completed} / {total} chapters")
    if total > 0:
        pct = (completed / total) * 100
        cli.print_out(f"    Progress: [{cli.c('█' * int(pct/10) + '░' * (10-int(pct/10)), cli.Colors.GREEN)}] {pct:.1f}%")

    cli.print_out(f"\n  {cli.c('Style:', cli.Colors.BOLD)}")
    cli.print_out(f"    Tone: {style.get('tone', 'N/A')}")
    cli.print_out(f"    Pacing: {style.get('pacing', 'N/A')}")
    cli.print_out(f"    Description: {style.get('description', 'N/A')}")
    cli.print_out(f"    Dialogue: {style.get('dialogue', 'N/A')}")

    cli.print_out(f"\n  {cli.c('Next Steps:', cli.Colors.BOLD)}")
    if not (paths['info'] / '01-core.yaml').exists():
        cli.print_out(f"    1. story collect core      - Collect core story info")
    elif not list(paths['characters'].glob('protagonist/*.yaml')):
        cli.print_out(f"    2. story collect protagonist - Create protagonist")
    elif not (paths['outline'] / 'volume-001.yaml').exists():
        cli.print_out(f"    3. story plan volume 1     - Plan volume 1")
    else:
        cli.print_out(f"    4. story write 1 --prompt  - Generate chapter 1 prompt")
    cli.print_out()


def show_status_help():
    print("""
Usage: story status [options]

Options:
  --json    Output JSON format for AI consumption

Examples:
  story status
  story status --json
""")


def main():
    # Check for help
    if len(sys.argv) > 1 and sys.argv[1] in ('help', '--help', '-h'):
        show_status_help()
        return

    # Parse CLI arguments
    sys.argv = ['story-status'] + sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    args, _ = cli.parse_cli_args(parser)

    # Find project root
    root = find_project_root()
    if not root:
        cli.error_message("Not in a novel project (no story.yaml/story.json). Run 'story init' first.")

    config = load_config(root)
    paths = load_project_paths(root)

    if cli.is_json_mode():
        status_dict = get_project_status_dict(root, config, paths)
        status_dict['success'] = True
        cli.output_json(status_dict)
    else:
        show_status_interactive(root, config, paths)


if __name__ == '__main__':
    main()
