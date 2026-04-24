#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:archive - Archive completed chapters and volumes
"""

import sys
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from .paths import find_project_root, load_config, load_project_paths, get_volume_and_chapter, get_chapters_for_volume, get_global_chapter_num, save_config
from .progress import (
    load_progress, save_progress,
    set_chapter_status, ChapterStatus,
    get_chapter_status,
)
from .consistency import (
    run_all_consistency_checks,
    format_check_report,
    save_yaml,
)


def load_yaml(path: Path):
    """Load YAML file with JSON fallback"""
    import json
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False

    if not path.exists():
        return None

    with open(path, 'r', encoding='utf-8') as f:
        if use_yaml:
            try:
                return yaml.safe_load(f) or {}
            except:
                pass
        # Try JSON fallback
        try:
            f.seek(0)
            return json.load(f)
        except:
            return None


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    CYAN = '\033[96m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def archive_chapter(chapter_num: int, paths: dict, config: dict, force: bool = False, check_only: bool = False, skip_consistency: bool = False):
    """Archive a completed chapter"""
    print(f"\n{c('═' * 60, Colors.BOLD)}")
    print(f"  {c(f'[ARCHIVE] Chapter {chapter_num}', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.BOLD)}\n")

    structure = config.get('structure', {})
    volume_num, chapter_in_volume = get_volume_and_chapter(chapter_num, structure)

    # Run consistency checks unless skipped
    check_results = None
    if not skip_consistency:
        vol_name = f'volume-{volume_num:03d}'
        ch_name = f'chapter-{chapter_in_volume:03d}'
        chapter_file = paths['content'] / vol_name / f'{ch_name}.md'

        chapter_content = ''
        if chapter_file.exists():
            with open(chapter_file, 'r', encoding='utf-8') as f:
                chapter_content = f.read()

        from .snapshot import get_snapshot_dir
        snapshots_dir = get_snapshot_dir(paths['outline'], volume_num)
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        check_results = run_all_consistency_checks(
            chapter_content, chapter_num, volume_num, paths, config
        )

        check_path = snapshots_dir / f'chapter-{chapter_in_volume:03d}-check.yaml'
        save_yaml(check_path, check_results)

        print(format_check_report(check_results))

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

    vol_name = f'volume-{volume_num:03d}'
    ch_name = f'chapter-{chapter_in_volume:03d}'
    chapter_file = paths['content'] / vol_name / f'{ch_name}.md'

    if not chapter_file.exists():
        print(f"  {c('Error: Chapter file not found', Colors.RED)}")
        print(f"  Expected: {chapter_file}")
        return

    archive_file = paths['archive'] / f'{ch_name}.md'
    copyfile(chapter_file, archive_file)

    progress = load_progress(paths['process'])
    progress = set_chapter_status(
        progress, chapter_num, ChapterStatus.ARCHIVED, volume_num
    )
    save_progress(paths['process'], progress)

    print(f"  {c('✓ Archived!', Colors.GREEN)}")
    print(f"  Archived to: {archive_file}")


def archive_volume(volume_num: int, paths: dict, config: dict, force: bool = False):
    """Archive a complete volume"""
    print(f"\n{c('═' * 60, Colors.BOLD)}")
    print(f"  {c(f'[ARCHIVE] Volume {volume_num}', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.BOLD)}\n")

    structure = config.get('structure', {})
    chapters_per_volume = get_chapters_for_volume(structure, volume_num)
    book = config.get('book', {})

    progress = load_progress(paths['process'])

    print(f"  {c('Checking chapters...', Colors.CYAN)}")
    chapters_to_archive = []
    unarchived_chapters = []

    for chapter_num in range(1, chapters_per_volume + 1):
        global_chapter_num = get_global_chapter_num(volume_num, chapter_num, structure)
        status = get_chapter_status(progress, global_chapter_num)

        vol_name = f'volume-{volume_num:03d}'
        ch_name = f'chapter-{chapter_num:03d}'
        chapter_file = paths['content'] / vol_name / f'{ch_name}.md'

        if chapter_file.exists():
            if status == ChapterStatus.ARCHIVED:
                chapters_to_archive.append(global_chapter_num)
            else:
                unarchived_chapters.append(global_chapter_num)

    if unarchived_chapters and not force:
        print(f"  {c('❌  Found unarchived chapters:', Colors.RED)}")
        print(f"      Chapters: {unarchived_chapters}")
        print(f"  {c('Archive them first or use --force to proceed', Colors.YELLOW)}")
        return

    if not chapters_to_archive:
        print(f"  {c('No chapters found for volume', Colors.RED)}")
        return

    vol_archive_dir = paths['archive'] / f'volume-{volume_num:03d}'
    vol_archive_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  {c('Copying chapters...', Colors.CYAN)}")
    for chapter_num in chapters_to_archive:
        ch_name = f'chapter-{chapter_num:03d}'
        src_file = paths['archive'] / f'{ch_name}.md'
        dest_file = vol_archive_dir / f'{ch_name}.md'

        if src_file.exists():
            copyfile(src_file, dest_file)
            print(f"    {c('✓', Colors.GREEN)} Chapter {chapter_num}")
        else:
            print(f"    {c('⚠', Colors.YELLOW)} Chapter {chapter_num} (file missing, skipped)")

    vol_info = {
        'volume_number': volume_num,
        'archived_at': datetime.now().isoformat(),
        'book_title': book.get('title', ''),
        'chapters': chapters_to_archive,
        'total_chapters': len(chapters_to_archive),
    }

    vol_outline_path = paths['outline'] / f'volume-{volume_num:03d}.yaml'
    if vol_outline_path.exists():
        vol_outline = load_yaml(vol_outline_path)
        if vol_outline:
            vol_info['volume_title'] = vol_outline.get('volume_info', {}).get('title', '')
            vol_info['volume_theme'] = vol_outline.get('volume_info', {}).get('theme', '')

    info_path = vol_archive_dir / 'volume-info.yaml'
    save_yaml(info_path, vol_info)

    print(f"\n  {c('✓ Volume archived!', Colors.GREEN)}")
    print(f"  Archive dir: {vol_archive_dir}")
    print(f"  Chapters: {len(chapters_to_archive)}")


def unarchive_chapter(chapter_num: int, paths: dict, config: dict):
    """Unarchive a chapter - restore from archive back to content"""
    print(f"\n{c('═' * 60, Colors.BOLD)}")
    print(f"  {c(f'[UNARCHIVE] Chapter {chapter_num}', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.BOLD)}\n")

    structure = config.get('structure', {})
    volume_num, chapter_in_volume = get_volume_and_chapter(chapter_num, structure)

    ch_name = f'chapter-{chapter_in_volume:03d}'
    archive_file = paths['archive'] / f'{ch_name}.md'

    if not archive_file.exists():
        print(f"  {c(f'❌ Archive file not found: {archive_file}', Colors.RED)}")
        return

    vol_name = f'volume-{volume_num:03d}'
    chapter_file = paths['content'] / vol_name / f'{ch_name}.md'
    copyfile(archive_file, chapter_file)

    progress = load_progress(paths['process'])
    progress = set_chapter_status(
        progress, chapter_num, ChapterStatus.COMPLETED, volume_num
    )
    save_progress(paths['process'], progress)

    # Remove from story.yaml completed_chapters
    root = find_project_root()
    if root:
        story_config = load_config(root)
        completed = story_config.get('progress', {}).get('completed_chapters', [])
        if chapter_num in completed:
            completed.remove(chapter_num)
            story_config['progress']['completed_chapters'] = completed
            save_config(root, story_config)

    print(f"  {c('✓ Unarchived!', Colors.GREEN)}")
    print(f"  Restored to: {chapter_file}")


def show_archive_help():
    print("""
Usage: story archive <target> [options]

Targets:
  <chapter_num>          Archive a single chapter (e.g., 5)
  volume <num>           Archive a complete volume (e.g., volume 1)

Options:
  --force            Force archive even if checks fail
  --check-only       Only run checks, don't archive (chapter only)
  --skip-consistency  Skip consistency checks entirely (chapter only)

Examples:
  story archive 1
  story archive 5 --check-only
  story archive volume 1
  story archive volume 2 --force
""")


def show_unarchive_help():
    print("""
Usage: story unarchive <chapter_num>

Restore a chapter from archive back to content directory.
The archive file is kept as backup.

Examples:
  story unarchive 5
""")


def main():
    if len(sys.argv) < 2:
        show_archive_help()
        return

    target = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if target in ('help', '--help', '-h'):
        show_archive_help()
        return

    # Handle unarchive command
    if target == 'unarchive':
        remaining_args = []
        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg in ('help', '--help', '-h'):
                show_unarchive_help()
                return
            else:
                remaining_args.append(arg)
            i += 1

        if not remaining_args or not remaining_args[0].isdigit():
            show_unarchive_help()
            return

        root = find_project_root()
        if not root:
            print("  Error: Not in a novel project (no story.yaml/story.json)")
            print("  Run 'story init' first")
            return

        config = load_config(root)
        paths = load_project_paths(root)
        chapter_num = int(remaining_args[0])
        unarchive_chapter(chapter_num, paths, config)
        return

    # Parse global options
    force = False
    check_only = False
    skip_consistency = False
    remaining_args = []

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--force':
            force = True
        elif arg == '--check-only':
            check_only = True
        elif arg == '--skip-consistency':
            skip_consistency = True
        else:
            remaining_args.append(arg)
        i += 1

    if not remaining_args:
        show_archive_help()
        return

    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml/story.json)")
        print("  Run 'story init' first")
        return

    config = load_config(root)
    paths = load_project_paths(root)

    if remaining_args[0].lower() == 'volume':
        if len(remaining_args) < 2 or not remaining_args[1].isdigit():
            show_archive_help()
            return
        volume_num = int(remaining_args[1])
        archive_volume(volume_num, paths, config, force)
        return

    if remaining_args[0].isdigit():
        chapter_num = int(remaining_args[0])
        archive_chapter(chapter_num, paths, config, force, check_only, skip_consistency)
        return

    show_archive_help()


if __name__ == '__main__':
    main()
