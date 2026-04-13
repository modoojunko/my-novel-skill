#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:archive - Archive completed chapters
"""

import sys
from pathlib import Path
from shutil import copyfile
from .paths import find_project_root, load_config, load_project_paths
from .progress import (
    load_progress, save_progress,
    set_chapter_status, ChapterStatus,
)


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def archive_chapter(chapter_num: int, paths: dict, config: dict):
    """Archive a completed chapter"""
    print(f"\n{c('═' * 60, Colors.BOLD)}")
    print(f"  {c(f'[ARCHIVE] Chapter {chapter_num}', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.BOLD)}\n")

    structure = config.get('structure', {})
    chapters_per_volume = structure.get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per_volume) + 1

    # Find chapter file
    vol_name = f'volume-{volume_num:03d}'
    ch_name = f'chapter-{chapter_num:03d}'
    chapter_file = paths['content'] / vol_name / f'{ch_name}.md'

    if not chapter_file.exists():
        print(f"  {c('Error: Chapter file not found', Colors.RED)}")
        print(f"  Expected: {chapter_file}")
        return

    # Copy to archive
    archive_file = paths['archive'] / f'{ch_name}.md'
    copyfile(chapter_file, archive_file)

    # Update progress
    progress = load_progress(paths['process'])
    progress = set_chapter_status(
        progress, chapter_num, ChapterStatus.ARCHIVED, volume_num
    )
    save_progress(paths['process'], progress)

    print(f"  {c('✓ Archived!', Colors.GREEN)}")
    print(f"  Archived to: {archive_file}")


def show_archive_help():
    print("""
Usage: story archive <chapter_num>

Archive a completed chapter.

Examples:
  story archive 1
  story archive 5
""")


def main():
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        show_archive_help()
        return

    chapter_num = int(sys.argv[1])

    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml/story.json)")
        print("  Run 'story init' first")
        return

    config = load_config(root)
    paths = load_project_paths(root)

    archive_chapter(chapter_num, paths, config)


if __name__ == '__main__':
    main()
