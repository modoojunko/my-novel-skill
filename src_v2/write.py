#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:write - Generate chapter prompt and manage writing
"""

import sys
from pathlib import Path
from .paths import find_project_root, load_config, load_project_paths
from .prompt import build_writing_prompt
from .progress import (
    load_progress, save_progress,
    set_chapter_status, get_chapter_status,
    ChapterStatus,
)


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


def generate_prompt(volume_num: int, chapter_num: int, paths: dict, config: dict) -> str:
    """Generate writing prompt for a chapter"""
    print(f"\n{c('═' * 60, Colors.CYAN)}")
    print(f"  {c(f'[WRITE] Generating Prompt for Chapter {chapter_num}', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.CYAN)}\n")

    prompt = build_writing_prompt(paths, volume_num, chapter_num, config)

    # Save prompt to file
    prompt_path = paths['prompts'] / f'chapter-{chapter_num:03d}-prompt.md'
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"  {c('✓ Prompt generated!', Colors.GREEN)}")
    print(f"  Saved to: {prompt_path}")

    # Also show a preview
    print(f"\n{c('--- Prompt Preview ---', Colors.BOLD)}")
    lines = prompt.split('\n')[:30]
    print('\n'.join(lines))
    if len(lines) < len(prompt.split('\n')):
        print("... (truncated, see full file)")

    # Update progress
    progress = load_progress(paths['process'])
    progress = set_chapter_status(
        progress, chapter_num, ChapterStatus.WRITING, volume_num
    )
    save_progress(paths['process'], progress)

    return prompt


def show_write_help():
    print("""
Usage: story write <chapter_num> [options]

Options:
  --prompt      Only generate prompt, don't write
  --resume      Resume writing from last position
  --volume <n>  Specify volume number (auto-detected if not given)

Examples:
  story write 1 --prompt
  story write 5 --resume
""")


def main():
    if len(sys.argv) < 2:
        show_write_help()
        return

    # Parse arguments
    chapter_num = None
    volume_num = None
    prompt_only = False
    resume = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--prompt':
            prompt_only = True
        elif arg == '--resume':
            resume = True
        elif arg == '--volume' and i + 1 < len(sys.argv):
            volume_num = int(sys.argv[i + 1])
            i += 1
        elif arg.isdigit() and chapter_num is None:
            chapter_num = int(arg)
        else:
            print(f"  Unknown argument: {arg}")
            show_write_help()
            return
        i += 1

    if chapter_num is None:
        print("  Error: Chapter number required")
        show_write_help()
        return

    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml/story.json)")
        print("  Run 'story init' first")
        return

    config = load_config(root)
    paths = load_project_paths(root)

    # Auto-detect volume if not given
    if volume_num is None:
        structure = config.get('structure', {})
        chapters_per_volume = structure.get('chapters_per_volume', 30)
        volume_num = ((chapter_num - 1) // chapters_per_volume) + 1

    if prompt_only:
        generate_prompt(volume_num, chapter_num, paths, config)
    else:
        print(f"  Writing mode (full mode coming soon)")
        print(f"  Use --prompt to just generate the prompt file")
        generate_prompt(volume_num, chapter_num, paths, config)


if __name__ == '__main__':
    main()
