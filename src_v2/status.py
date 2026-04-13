#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:status - Show project status
"""

from .paths import find_project_root, load_config, load_project_paths


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def main():
    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml/story.json)")
        print("  Run 'story init' first")
        return

    config = load_config(root)
    paths = load_project_paths(root)

    book = config.get('book', {})
    structure = config.get('structure', {})
    progress = config.get('progress', {})
    style = config.get('style', {})

    print(f"\n{c('═' * 60, Colors.BOLD)}")
    print(f"  {c(book.get('title', 'Untitled'), Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.BOLD)}\n")

    print(f"  {c('Basic Info:', Colors.BOLD)}")
    print(f"    Genre: {book.get('genre', 'Unknown')}")
    print(f"    Target: {book.get('target_words', 0):,} words")
    print(f"    Volumes: {structure.get('volumes', 0)}")
    print(f"    Chapters/Volume: {structure.get('chapters_per_volume', 30)}")

    print(f"\n  {c('Progress:', Colors.BOLD)}")
    completed = len(progress.get('completed_chapters', []))
    total = structure.get('volumes', 0) * structure.get('chapters_per_volume', 30)
    print(f"    Current: Volume {progress.get('current_volume', 1)}, Chapter {progress.get('current_chapter', 0)}")
    print(f"    Completed: {completed} / {total} chapters")
    if total > 0:
        pct = (completed / total) * 100
        print(f"    Progress: [{c('█' * int(pct/10) + '░' * (10-int(pct/10)), Colors.GREEN)}] {pct:.1f}%")

    print(f"\n  {c('Style:', Colors.BOLD)}")
    print(f"    Tone: {style.get('tone', 'N/A')}")
    print(f"    Pacing: {style.get('pacing', 'N/A')}")
    print(f"    Description: {style.get('description', 'N/A')}")
    print(f"    Dialogue: {style.get('dialogue', 'N/A')}")

    print(f"\n  {c('Next Steps:', Colors.BOLD)}")
    if not (paths['info'] / '01-core.yaml').exists():
        print(f"    1. story collect core      - Collect core story info")
    elif not list(paths['characters'].glob('protagonist/*.yaml')):
        print(f"    2. story collect protagonist - Create protagonist")
    elif not (paths['outline'] / 'volume-001.yaml').exists():
        print(f"    3. story plan volume 1     - Plan volume 1")
    else:
        print(f"    4. story write 1 --prompt  - Generate chapter 1 prompt")
    print()


if __name__ == '__main__':
    main()
