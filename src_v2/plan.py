#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:plan - Plan volume and chapter outlines
"""

import sys
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


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def plan_volume(volume_num: int, paths: dict, config: dict, no_timeline: bool = False, non_interactive: bool = False):
    """Interactive volume planning"""
    print(f"\n{c('═' * 60, Colors.CYAN)}")
    print(f"  {c(f'[PLAN] Volume {volume_num}', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.CYAN)}\n")

    # Check if already exists
    outline_dir = paths['outline']
    existing = load_volume_outline(outline_dir, volume_num)
    if existing:
        if non_interactive:
            print(f"  {c(f'Volume {volume_num} outline already exists, skipping', Colors.YELLOW)}")
            return
        print(f"  {c(f'Warning: Volume {volume_num} outline already exists', Colors.YELLOW)}")
        response = cli.input_with_default("Re-plan?", "N", arg_key="replan")
        if response.strip().lower() != 'y':
            print("  Cancelled")
            return

    # Collect basic info
    title = cli.input_with_default("Volume title", f"第{volume_num}卷", arg_key="volume_title")
    theme = cli.input_with_default("Theme", "", arg_key="theme")

    # Create outline
    outline = create_volume_outline(volume_num, title, theme)

    # Get structure info
    print(f"\n  {c('[STRUCTURE]', Colors.BOLD)}")
    outline['structure']['opening'] = cli.input_with_default("Opening", "", arg_key="opening")
    outline['structure']['development'] = cli.input_with_default("Development", "", arg_key="development")
    outline['structure']['climax'] = cli.input_with_default("Climax", "", arg_key="climax")
    outline['structure']['ending'] = cli.input_with_default("Ending", "", arg_key="ending")

    # Add chapters
    structure = config.get('structure', {})
    chapters_per_volume = structure.get('chapters_per_volume', 30)

    print(f"\n  {c('[CHAPTERS]', Colors.BOLD)}")
    if non_interactive:
        auto_chapters = True
    else:
        auto_chapters = cli.input_with_default(
            f"Auto-create {chapters_per_volume} chapters?", "Y", arg_key="auto_chapters"
        ).lower() == 'y'

    if auto_chapters:
        for i in range(1, chapters_per_volume + 1):
            outline = add_chapter_to_volume(outline, i, f"第{i}章", "")
    else:
        print("  Add chapters manually (leave title empty when done)")
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
        outline = collect_timeline_for_volume(outline, non_interactive)

    # Save
    save_volume_outline(outline_dir, volume_num, outline)
    print(f"\n  {c('✓ Volume outline saved!', Colors.GREEN)}")


def plan_chapter(volume_num: int, chapter_num: int, paths: dict, non_interactive: bool = False):
    """Interactive chapter planning"""
    print(f"\n{c('═' * 60, Colors.CYAN)}")
    print(f"  {c(f'[PLAN] Chapter {chapter_num} (Volume {volume_num})', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.CYAN)}\n")

    outline_dir = paths['outline']

    # Check if volume exists
    volume = load_volume_outline(outline_dir, volume_num)
    if not volume:
        print(f"  {c(f'Error: Volume {volume_num} not found', Colors.RED)}")
        print(f"  Run 'story plan volume {volume_num}' first")
        return

    # Check if chapter exists
    existing = load_chapter_outline(outline_dir, volume_num, chapter_num)
    if existing:
        if non_interactive:
            # 在非交互模式下，直接使用已有的或自动创建
            print(f"  {c(f'Chapter {chapter_num} outline already exists, skipping', Colors.YELLOW)}")
            return
        print(f"  {c(f'Warning: Chapter {chapter_num} outline already exists', Colors.YELLOW)}")
        response = cli.input_with_default("Re-plan?", "N", arg_key="replan")
        if response.strip().lower() != 'y':
            print("  Cancelled")
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
    print(f"\n  {c('✓ Chapter outline saved!', Colors.GREEN)}")


def show_plan_help():
    print("""
Usage: story plan <target> [options]

Targets:
  volume <num>        Plan a volume outline
  chapter <vol> <num> Plan a chapter outline

Examples:
  story plan volume 1
  story plan volume 1 --no-timeline
  story plan chapter 1 5
""")


def main():
    if len(sys.argv) < 2:
        show_plan_help()
        return

    # Parse options
    target = None
    volume_num = None
    chapter_num = None
    no_timeline = False
    non_interactive = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--no-timeline':
            no_timeline = True
        elif arg == '--non-interactive':
            non_interactive = True
        elif arg in ('help', '--help', '-h'):
            show_plan_help()
            return
        elif arg.isdigit():
            if volume_num is None:
                volume_num = int(arg)
            else:
                chapter_num = int(arg)
        elif not target:
            target = arg.lower()
        i += 1

    if not target:
        show_plan_help()
        return

    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml/story.json)")
        print("  Run 'story init' first")
        return

    config = load_config(root)
    paths = load_project_paths(root)
    ensure_default_templates(paths['templates'])

    if target == 'volume':
        if volume_num is None:
            print("  Usage: story plan volume <number>")
            return
        try:
            plan_volume(volume_num, paths, config, no_timeline, non_interactive)
        except ValueError:
            print("  Error: Volume number must be an integer")
    elif target == 'chapter':
        if volume_num is None or chapter_num is None:
            print("  Usage: story plan chapter <volume> <number>")
            return
        try:
            plan_chapter(volume_num, chapter_num, paths, non_interactive)
        except ValueError:
            print("  Error: Volume and chapter numbers must be integers")
    else:
        print(f"  Unknown target: {target}")
        show_plan_help()


if __name__ == '__main__':
    main()
