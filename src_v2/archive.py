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
from .consistency import (
    run_all_consistency_checks,
    format_check_report,
    save_yaml,
)


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def archive_chapter(chapter_num: int, paths: dict, config: dict, force: bool = False, check_only: bool = False, skip_consistency: bool = False):
    """Archive a completed chapter"""
    print(f"\n{c('═' * 60, Colors.BOLD)}")
    print(f"  {c(f'[ARCHIVE] Chapter {chapter_num}', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.BOLD)}\n")

    structure = config.get('structure', {})
    chapters_per_volume = structure.get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per_volume) + 1

    # Run consistency checks unless skipped
    check_results = None
    if not skip_consistency:
        # Load chapter content
        vol_name = f'volume-{volume_num:03d}'
        ch_name = f'chapter-{chapter_num:03d}'
        chapter_file = paths['content'] / vol_name / f'{ch_name}.md'

        chapter_content = ''
        if chapter_file.exists():
            with open(chapter_file, 'r', encoding='utf-8') as f:
                chapter_content = f.read()

        # Ensure snapshots directory exists
        paths['snapshots'].mkdir(parents=True, exist_ok=True)

        # Run checks
        check_results = run_all_consistency_checks(
            chapter_content, chapter_num, volume_num, paths, config
        )

        # Save check results
        check_path = paths['snapshots'] / f'chapter-{chapter_num:03d}-check.yaml'
        save_yaml(check_path, check_results)

        # Display report
        print(format_check_report(check_results))

        # Check if we should block
        summary = check_results.get('check_results', {}).get('summary', {})
        has_errors = summary.get('errors', 0) > 0

        if has_errors and not force:
            print(f"\n  {c('❌ 检查发现错误，使用 --force 强制归档', Colors.RED)}")
            return

        if check_only:
            print(f"\n  {c('✓ 检查完成（--check-only 模式，不执行归档）', Colors.YELLOW)}")
            return

        if not has_errors:
            print(f"\n  {c('✓ 检查通过，继续归档...', Colors.GREEN)}")

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
Usage: story archive <chapter_num> [options]

Archive a completed chapter with consistency checks.

Options:
  --force            Force archive even if checks fail
  --check-only       Only run checks, don't archive
  --skip-consistency  Skip consistency checks entirely

Examples:
  story archive 1
  story archive 5 --check-only
  story archive 5 --force
""")


def main():
    if len(sys.argv) < 2:
        show_archive_help()
        return

    # Parse arguments
    chapter_num = None
    force = False
    check_only = False
    skip_consistency = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--force':
            force = True
        elif arg == '--check-only':
            check_only = True
        elif arg == '--skip-consistency':
            skip_consistency = True
        elif arg in ('help', '--help', '-h'):
            show_archive_help()
            return
        elif arg.isdigit() and chapter_num is None:
            chapter_num = int(arg)
        i += 1

    if chapter_num is None:
        show_archive_help()
        return

    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml/story.json)")
        print("  Run 'story init' first")
        return

    config = load_config(root)
    paths = load_project_paths(root)

    archive_chapter(chapter_num, paths, config, force, check_only, skip_consistency)


if __name__ == '__main__':
    main()
