#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:write - Generate chapter prompt and manage writing

Supports both interactive and non-interactive modes:
- Interactive: `story write 1 --prompt`
- Non-interactive: `story write 1 --prompt --non-interactive`
- JSON output: `story write 1 --prompt --json`
"""

import sys
import argparse
from pathlib import Path
from .paths import find_project_root, load_config, load_project_paths, get_volume_prompts_dir
from .prompt import build_writing_prompt
from .progress import (
    load_progress, save_progress,
    set_chapter_status, get_chapter_status,
    ChapterStatus,
)
from . import cli


def generate_prompt(volume_num: int, chapter_num: int, paths: dict, config: dict, no_anti_repeat: bool = False) -> str:
    """Generate writing prompt for a chapter"""
    if not cli.is_json_mode():
        cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
        cli.print_out(f"  {cli.c(f'[WRITE] Generating Prompt for Chapter {chapter_num}', cli.Colors.BOLD)}")
        cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")

    # Disable anti-repeat if requested
    if no_anti_repeat:
        style = config.get('style', {})
        if 'anti_repeat' not in style:
            style['anti_repeat'] = {}
        style['anti_repeat']['enabled'] = False

    # Calculate chapter number within volume
    structure = config.get('structure', {})
    chapters_per_volume = structure.get('chapters_per_volume', 30)
    chapter_in_volume = ((chapter_num - 1) % chapters_per_volume) + 1

    prompt = build_writing_prompt(paths, volume_num, chapter_in_volume, chapter_num, config)

    # Save prompt to file
    vol_prompts_dir = get_volume_prompts_dir(paths, volume_num)
    prompt_path = vol_prompts_dir / f'chapter-{chapter_num:03d}-prompt.md'
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)

    # Update progress
    progress = load_progress(paths['process'])
    progress = set_chapter_status(
        progress, chapter_num, ChapterStatus.WRITING, volume_num
    )
    save_progress(paths['process'], progress)

    # Output result
    if cli.is_json_mode():
        cli.output_json({
            'success': True,
            'chapter': chapter_num,
            'volume': volume_num,
            'prompt_path': str(prompt_path),
            'prompt_content': prompt
        })
    else:
        cli.print_out(f"  {cli.c('✓ Prompt generated!', cli.Colors.GREEN)}")
        cli.print_out(f"  Saved to: {prompt_path}")

        # Also show a preview
        cli.print_out(f"\n{cli.c('--- Prompt Preview ---', cli.Colors.BOLD)}")
        lines = prompt.split('\n')[:30]
        cli.print_out('\n'.join(lines))
        if len(lines) < len(prompt.split('\n')):
            cli.print_out("... (truncated, see full file)")

    return prompt


def show_write_help():
    print("""
Usage: story write <chapter_num> [options]

Options:
  --prompt          Only generate prompt, don't write
  --resume          Resume writing from last position
  --volume <n>      Specify volume number (auto-detected if not given)
  --json            Output JSON format for AI consumption
  --non-interactive  Non-interactive mode
  --args JSON       JSON string with arguments (for non-interactive mode)
  --no-anti-repeat  Skip anti-repetition check

Examples:
  story write 1 --prompt
  story write 5 --resume
  story write 1 --prompt --json
""")


def main():
    if len(sys.argv) < 2:
        show_write_help()
        return

    # Check for help
    if sys.argv[1] in ('help', '--help', '-h'):
        show_write_help()
        return

    # Parse arguments
    chapter_num = None
    volume_num = None
    prompt_only = False
    resume = False
    no_anti_repeat = False

    # First pass to get chapter_num before argparse
    i = 1
    remaining_args = []
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--prompt':
            prompt_only = True
        elif arg == '--resume':
            resume = True
        elif arg == '--no-anti-repeat':
            no_anti_repeat = True
        elif arg == '--volume' and i + 1 < len(sys.argv):
            volume_num = int(sys.argv[i + 1])
            remaining_args.append(arg)
            remaining_args.append(sys.argv[i + 1])
            i += 1
        elif arg.isdigit() and chapter_num is None:
            chapter_num = int(arg)
        else:
            remaining_args.append(arg)
        i += 1

    if chapter_num is None:
        cli.error_message("Chapter number required")

    # Parse CLI arguments for json/non-interactive
    sys.argv = ['story-write'] + remaining_args
    parser = argparse.ArgumentParser(add_help=False)
    args, write_args = cli.parse_cli_args(parser)

    # Find project root
    root = find_project_root()
    if not root:
        cli.error_message("Not in a novel project (no story.yaml/story.json). Run 'story init' first.")

    config = load_config(root)
    paths = load_project_paths(root)

    # Auto-detect volume if not given
    if volume_num is None:
        structure = config.get('structure', {})
        chapters_per_volume = structure.get('chapters_per_volume', 30)
        volume_num = ((chapter_num - 1) // chapters_per_volume) + 1

    if prompt_only:
        generate_prompt(volume_num, chapter_num, paths, config, no_anti_repeat)
    else:
        if not cli.is_json_mode():
            cli.print_out(f"  Writing mode (full mode coming soon)")
            cli.print_out(f"  Use --prompt to just generate the prompt file")
        generate_prompt(volume_num, chapter_num, paths, config, no_anti_repeat)


if __name__ == '__main__':
    main()
