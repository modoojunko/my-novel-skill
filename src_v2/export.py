#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:export - Export novel to various formats
"""

import sys
from pathlib import Path
from typing import Optional
from .paths import find_project_root, load_config, load_project_paths


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def export_txt(paths: dict, config: dict, output_name: Optional[str] = None):
    """Export novel as plain text"""
    book = config.get('book', {})
    title = book.get('title', 'novel')

    if not output_name:
        output_name = f"{title}.txt"

    output_path = paths['export'] / output_name

    structure = config.get('structure', {})
    volumes = structure.get('volumes', 1)
    chapters_per_volume = structure.get('chapters_per_volume', 30)

    print(f"\n{c('═' * 60, Colors.BOLD)}")
    print(f"  {c(f'[EXPORT] {title}', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.BOLD)}\n")

    content = []

    # Add title
    content.append(f"# {title}\n\n")

    # Collect all chapters
    total_chapters = 0
    for volume_num in range(1, volumes + 1):
        vol_name = f'volume-{volume_num:03d}'
        vol_dir = paths['content'] / vol_name

        if vol_dir.exists():
            for chapter_num in range(1, chapters_per_volume + 1):
                ch_name = f'chapter-{chapter_num:03d}.md'
                ch_file = vol_dir / ch_name

                if ch_file.exists():
                    with open(ch_file, 'r', encoding='utf-8') as f:
                        ch_content = f.read()
                        content.append(ch_content)
                        content.append("\n\n")
                        total_chapters += 1

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(content)

    print(f"  {c('✓ Exported!', Colors.GREEN)}")
    print(f"  Chapters: {total_chapters}")
    print(f"  Output: {output_path}")


def show_export_help():
    print("""
Usage: story export [format] [options]

Formats:
  txt     Export as plain text (default)

Options:
  -o <name>  Output filename

Examples:
  story export
  story export txt -o my_novel.txt
""")


def main():
    format_type = 'txt'
    output_name = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ('txt',):
            format_type = arg
        elif arg == '-o' and i + 1 < len(sys.argv):
            output_name = sys.argv[i + 1]
            i += 1
        elif arg in ('-h', '--help', 'help'):
            show_export_help()
            return
        i += 1

    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml/story.json)")
        print("  Run 'story init' first")
        return

    config = load_config(root)
    paths = load_project_paths(root)

    if format_type == 'txt':
        export_txt(paths, config, output_name)


if __name__ == '__main__':
    main()
