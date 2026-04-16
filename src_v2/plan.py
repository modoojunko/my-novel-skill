#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:plan - Plan volume and chapter outlines

Supports both interactive and non-interactive modes:
- Interactive: `story plan <target>` (normal output)
- Non-interactive: `story plan <target> --non-interactive`
- JSON output: `story plan <target> --json`
"""

import sys
import argparse
import json
from pathlib import Path
from .paths import find_project_root, load_config, load_project_paths
from .templates import get_collect_questions, ensure_default_templates
from .outline import (
    create_volume_outline, create_chapter_outline,
    add_chapter_to_volume,
    load_volume_outline, save_volume_outline,
    load_chapter_outline, save_chapter_outline,
)
from .timeline import collect_timeline_for_volume
from . import cli


def plan_volume(volume_num: int, paths: dict, config: dict, no_timeline: bool = False):
    """Interactive volume planning"""
    cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
    cli.print_out(f"  {cli.c(f'[PLAN] Volume {volume_num}', cli.Colors.BOLD)}")
    cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")

    # Check if already exists
    outline_dir = paths['outline']
    existing = load_volume_outline(outline_dir, volume_num)
    if existing:
        if not cli.is_interactive():
            cli.print_out(f"  {cli.c(f'Volume {volume_num} outline already exists, skipping', cli.Colors.YELLOW)}")
            return
        cli.print_out(f"  {cli.c(f'Warning: Volume {volume_num} outline already exists', cli.Colors.YELLOW)}")
        response = cli.input_with_default("Re-plan?", "N", arg_key="replan")
        if response.strip().lower() != 'y':
            cli.print_out("  Cancelled")
            return

    # Collect basic info
    title = cli.input_with_default("Volume title", f"第{volume_num}卷", arg_key="volume_title")
    theme = cli.input_with_default("Theme", "", arg_key="theme")

    # Create outline
    outline = create_volume_outline(volume_num, title, theme)

    # Get structure info
    cli.print_out(f"\n  {cli.c('[STRUCTURE]', cli.Colors.BOLD)}")
    outline['structure']['opening'] = cli.input_with_default("Opening", "", arg_key="opening")
    outline['structure']['development'] = cli.input_with_default("Development", "", arg_key="development")
    outline['structure']['climax'] = cli.input_with_default("Climax", "", arg_key="climax")
    outline['structure']['ending'] = cli.input_with_default("Ending", "", arg_key="ending")

    # Add chapters
    structure = config.get('structure', {})
    chapters_per_volume = structure.get('chapters_per_volume', 30)

    cli.print_out(f"\n  {cli.c('[CHAPTERS]', cli.Colors.BOLD)}")
    if not cli.is_interactive():
        auto_chapters = True
    else:
        auto_chapters = cli.input_with_default(
            f"Auto-create {chapters_per_volume} chapters?", "Y", arg_key="auto_chapters"
        ).lower() == 'y'

    if auto_chapters:
        for i in range(1, chapters_per_volume + 1):
            outline = add_chapter_to_volume(outline, i, f"第{i}章", "")
    else:
        cli.print_out("  Add chapters manually (leave title empty when done)")
        i = 1
        while True:
            ch_title = cli.input_with_default(f"Chapter {i} title", "", arg_key=f"chapter_{i}_title")
            if not ch_title:
                break
            ch_pov = cli.input_with_default(f"Chapter {i} POV", "", arg_key=f"chapter_{i}_pov")
            outline = add_chapter_to_volume(outline, i, ch_title, ch_pov)
            i += 1

    # Collect timeline
    if not no_timeline:
        outline = collect_timeline_for_volume(outline, not cli.is_interactive())

    # Save
    save_volume_outline(outline_dir, volume_num, outline)
    cli.print_out(f"\n  {cli.c('✓ Volume outline saved!', cli.Colors.GREEN)}")


def plan_chapter(volume_num: int, chapter_num: int, paths: dict):
    """Interactive chapter planning"""
    cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
    cli.print_out(f"  {cli.c(f'[PLAN] Chapter {chapter_num} (Volume {volume_num})', cli.Colors.BOLD)}")
    cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")

    outline_dir = paths['outline']

    # Check if volume exists
    volume = load_volume_outline(outline_dir, volume_num)
    if not volume:
        cli.print_out(f"  {cli.c(f'Error: Volume {volume_num} not found', cli.Colors.RED)}")
        cli.print_out(f"  Run 'story plan volume {volume_num}' first")
        return

    # Check if chapter exists
    existing = load_chapter_outline(outline_dir, volume_num, chapter_num)
    if existing:
        if not cli.is_interactive():
            # 在非交互模式下，直接使用已有的或自动创建
            cli.print_out(f"  {cli.c(f'Chapter {chapter_num} outline already exists, skipping', cli.Colors.YELLOW)}")
            return
        cli.print_out(f"  {cli.c(f'Warning: Chapter {chapter_num} outline already exists', cli.Colors.YELLOW)}")
        response = cli.input_with_default("Re-plan?", "N", arg_key="replan")
        if response.strip().lower() != 'y':
            cli.print_out("  Cancelled")
            return

    # Get chapter title from volume outline
    chapter_title = f"第{chapter_num}章"
    chapter_pov = ""
    for ch in volume.get('chapter_list', []):
        if ch.get('number') == chapter_num:
            chapter_title = ch.get('title', chapter_title)
            chapter_pov = ch.get('pov', '')
            break

    # Collect info
    title = cli.input_with_default("Chapter title", chapter_title, arg_key="chapter_title")
    pov = cli.input_with_default("POV character", chapter_pov, arg_key="pov")

    # Create outline
    outline = create_chapter_outline(chapter_num, volume_num, title, pov)
    outline['summary'] = cli.input_with_default(
        "Chapter summary (high-level overview: plot progression, character arcs)",
        "",
        arg_key="summary"
    )

    # Save
    save_chapter_outline(outline_dir, volume_num, chapter_num, outline)
    cli.print_out(f"\n  {cli.c('✓ Chapter outline saved!', cli.Colors.GREEN)}")


def show_plan_help():
    cli.print_out("""
Usage: story plan <target> [options]

Targets:
  volume <num>        Plan a volume outline
  chapter <vol> <num> Plan a chapter outline

Options:
  --no-timeline        Skip timeline collection for volume
  --json               Output JSON format for AI consumption
  --non-interactive    Non-interactive mode (use --args)
  --args JSON          JSON string with arguments

Examples:
  story plan volume 1
  story plan volume 1 --no-timeline
  story plan chapter 1 5
""")


def main():
    if len(sys.argv) < 2:
        show_plan_help()
        return

    # Check for help
    if sys.argv[1] in ('help', '--help', '-h'):
        show_plan_help()
        return

    # First, extract --json, --non-interactive, --args from anywhere in args
    # and set cli module's global state manually
    json_mode = '--json' in sys.argv
    non_interactive = '--non-interactive' in sys.argv

    # Find and parse --args if present
    args_dict = {}
    if '--args' in sys.argv:
        args_idx = sys.argv.index('--args')
        if args_idx + 1 < len(sys.argv):
            try:
                args_dict = json.loads(sys.argv[args_idx + 1])
            except json.JSONDecodeError:
                pass

    # Set cli module's global state manually
    cli._json_mode = json_mode
    cli._non_interactive = non_interactive
    cli._args = args_dict

    # Now filter out the global options and process subcommand
    filtered_args = []
    no_timeline = False
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--no-timeline':
            no_timeline = True
            i += 1
        elif arg in ('--json', '--non-interactive'):
            i += 1
        elif arg == '--args':
            i += 2
        else:
            filtered_args.append(arg)
            i += 1

    if not filtered_args:
        show_plan_help()
        return

    target = filtered_args[0].lower()
    target_args = filtered_args[1:]

    # Parse numbers from target_args
    volume_num = None
    chapter_num = None
    for arg in target_args:
        if arg.isdigit():
            if volume_num is None:
                volume_num = int(arg)
            else:
                chapter_num = int(arg)

    # Find project root
    root = find_project_root()
    if not root:
        cli.error_message("Not in a novel project (no story.yaml/story.json). Run 'story init' first.")

    config = load_config(root)
    paths = load_project_paths(root)
    ensure_default_templates(paths['templates'])

    if target == 'volume':
        if volume_num is None:
            cli.print_out("  Usage: story plan volume <number>")
            return
        try:
            plan_volume(volume_num, paths, config, no_timeline)
        except ValueError:
            cli.error_message("Volume number must be an integer")
    elif target == 'chapter':
        if volume_num is None or chapter_num is None:
            cli.print_out("  Usage: story plan chapter <volume> <number>")
            return
        try:
            plan_chapter(volume_num, chapter_num, paths)
        except ValueError:
            cli.error_message("Volume and chapter numbers must be integers")
    else:
        cli.print_out(f"  Unknown target: {target}")
        show_plan_help()


if __name__ == '__main__':
    main()
