#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:verify - Verify that chapter content follows the prompt requirements

This tool checks:
1. That chapter outline points are covered
2. That no unexpected content was added
3. That the content aligns with the prompt intent
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from .paths import find_project_root, load_config, load_project_paths
from .prompt import load_yaml, load_chapter_outline
from . import cli


def verify_chapter_content(
    content_path: Path,
    chapter_outline: Dict[str, Any],
) -> Tuple[bool, List[str], List[str]]:
    """
    Verify that chapter content follows the prompt.

    Returns:
        (is_valid, warnings, errors)
    """
    warnings = []
    errors = []
    is_valid = True

    if not content_path.exists():
        errors.append(f"Content file not found: {content_path}")
        return False, warnings, errors

    with open(content_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Quick check for any leftover process text that shouldn't be in final content
    process_text_indicators = [
        '[遵循提示词',
        '【遵循情况报告】',
        '提示词',
        '开始写作',
        '本章大纲',
        '关键场景',
        'POV',
    ]

    found_process_text = []
    lines = content.split('\n')
    for i, line in enumerate(lines[:20]):  # Check first 20 lines
        for indicator in process_text_indicators:
            if indicator in line:
                found_process_text.append(f"第 {i+1} 行: {line[:50]}...")

    if found_process_text:
        warnings.append("⚠️  正文开头发现可能的过程文字，请确认是否应该移除：")
        for text in found_process_text:
            warnings.append(f"   - {text}")

    # Check chapter outline key scenes are covered
    if chapter_outline:
        key_scenes = chapter_outline.get('key_scenes', [])
        if key_scenes:
            cli.print_out(f"\n  {cli.c('检查关键场景覆盖:', cli.Colors.CYAN)}")
            missing_scenes = []
            for i, scene in enumerate(key_scenes, 1):
                # Simple check: does scene text appear in content?
                scene_words = scene.replace('，', ' ').replace('。', ' ').split()
                found = False
                # Check if at least 50% of the key words are present
                match_count = 0
                key_word_count = 0
                for word in scene_words[:15]:  # Check first 15 words
                    if len(word) > 1:  # Only count meaningful words
                        key_word_count += 1
                        if word in content:
                            match_count += 1
                if key_word_count > 0 and match_count >= max(1, key_word_count // 2):
                    found = True
                if found:
                    cli.print_out(f"    {cli.c(f'✓ 场景{i}: {scene[:40]}...', cli.Colors.GREEN)}")
                else:
                    cli.print_out(f"    {cli.c(f'✗ 场景{i}: {scene[:40]}...', cli.Colors.RED)}")
                    missing_scenes.append(scene)
            if missing_scenes:
                warnings.append(f"⚠️  可能缺少 {len(missing_scenes)} 个关键场景，请手动检查")

    # Check chapter summary/objective
    if chapter_outline:
        summary = chapter_outline.get('summary', '') or chapter_outline.get('brief_summary', '')
        if summary:
            # Check if summary keywords are in content
            summary_words = summary.replace('，', ' ').replace('。', ' ').split()
            match_count = 0
            key_word_count = 0
            for word in summary_words[:20]:
                if len(word) > 1:
                    key_word_count += 1
                    if word in content:
                        match_count += 1
            if key_word_count > 0:
                coverage = match_count / key_word_count
                if coverage < 0.3:
                    warnings.append(f"⚠️  本章大纲摘要的关键词在正文中覆盖率较低 ({coverage:.0%})，请确认内容是否偏离")

    return is_valid, warnings, errors


def show_verify_help():
    print("""
Usage: story verify <chapter_num> [options]

Verify that chapter content follows the prompt requirements.

Options:
  --volume <n>      Specify volume number (auto-detected if not given)
  --json            Output JSON format for AI consumption
  --non-interactive  Non-interactive mode

Examples:
  story verify 1
  story verify 5 --volume 2
  story verify 1 --json
""")


def main():
    if len(sys.argv) < 2:
        show_verify_help()
        return

    # Check for help
    if sys.argv[1] in ('help', '--help', '-h'):
        show_verify_help()
        return

    # Parse arguments
    chapter_num = None
    volume_num = None

    # First pass to get chapter_num before argparse
    i = 1
    remaining_args = []
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--volume' and i + 1 < len(sys.argv):
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
    sys.argv = ['story-verify'] + remaining_args
    parser = argparse.ArgumentParser(add_help=False)
    args, verify_args = cli.parse_cli_args(parser)

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

    # Calculate chapter number within volume
    structure = config.get('structure', {})
    chapters_per_volume = structure.get('chapters_per_volume', 30)
    chapter_in_volume = ((chapter_num - 1) % chapters_per_volume) + 1

    # Get paths
    content_dir = paths['content'] / f'volume-{volume_num:03d}'
    content_path = content_dir / f'chapter-{chapter_num:03d}.md'

    # Load chapter outline (using chapter-in-volume number)
    chapter_outline = load_chapter_outline(paths['outline'], volume_num, chapter_in_volume)

    if not cli.is_json_mode():
        cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
        cli.print_out(f"  {cli.c(f'[VERIFY] 验证第 {chapter_num} 章', cli.Colors.BOLD)}")
        cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")
        cli.print_out(f"  {cli.c('验证内容:', cli.Colors.CYAN)}")
        cli.print_out(f"    - 检查正文是否干净（无过程文字）")
        cli.print_out(f"    - 检查关键场景是否覆盖")
        cli.print_out(f"    - 检查大纲摘要是否对齐")

    # Perform verification
    is_valid, warnings, errors = verify_chapter_content(content_path, chapter_outline)

    # Output results
    if cli.is_json_mode():
        cli.output_json({
            'success': True,
            'chapter': chapter_num,
            'volume': volume_num,
            'is_valid': is_valid,
            'warnings': warnings,
            'errors': errors,
            'content_path': str(content_path),
        })
    else:
        cli.print_out()
        if errors:
            cli.print_out(f"  {cli.c('❌ 发现问题:', cli.Colors.RED)}")
            for err in errors:
                cli.print_out(f"    {err}")
            cli.print_out()
        if warnings:
            cli.print_out(f"  {cli.c('⚠️  需要注意:', cli.Colors.YELLOW)}")
            for warn in warnings:
                cli.print_out(f"    {warn}")
            cli.print_out()
        if is_valid and not errors and not warnings:
            cli.print_out(f"  {cli.c('✓ 验证通过！', cli.Colors.GREEN)}")
            cli.print_out(f"  正文干净，关键场景覆盖良好。")
        elif is_valid:
            cli.print_out(f"  {cli.c('验证完成，请查看上方警告。', cli.Colors.YELLOW)}")
        else:
            cli.print_out(f"  {cli.c('✗ 验证失败！', cli.Colors.RED)}")
        cli.print_out()


if __name__ == '__main__':
    main()
