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
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .paths import find_project_root, load_config, load_project_paths, get_volume_prompts_dir, get_chapters_for_volume
from .templates import ensure_default_templates
from .prompt import load_core_info
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
    chapters_per_volume = get_chapters_for_volume(structure, volume_num)

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


def build_volume_outline_prompt(volume_num: int, paths: Dict[str, Any]) -> str:
    """Build prompt for AI-assisted volume outline generation"""
    prompt = f"# 第{volume_num}卷大纲生成任务\n\n"

    prompt += "## 任务说明\n"
    prompt += "你是一位专业的小说大纲设计师。请根据以下信息，生成一份完整、格式正确的卷大纲 YAML 文件。\n\n"

    # Load core info
    core_info = load_core_info(paths['info'])
    if core_info:
        prompt += "## 小说核心信息\n"
        prompt += json.dumps(core_info, ensure_ascii=False, indent=2)
        prompt += "\n\n"

    # Load previous volume if exists
    outline_dir = paths['outline']
    if volume_num > 1:
        prev_volume = load_volume_outline(outline_dir, volume_num - 1)
        if prev_volume:
            prompt += f"## 第{volume_num - 1}卷大纲（参考）\n"
            prompt += json.dumps(prev_volume, ensure_ascii=False, indent=2)
            prompt += "\n\n"

    # Structure requirements
    prompt += "## 输出格式要求\n"
    prompt += "请直接输出 YAML 格式，不要任何说明文字。YAML 结构如下：\n\n"
    prompt += f"""```yaml
volume_info:
  number: {volume_num}
  title: "卷标题"
  theme: "本卷主题"
structure:
  opening: "开场描述"
  development: "发展部分描述"
  climax: "高潮描述"
  ending: "结局描述"
key_events: []
chapter_list:
  - number: 1
    title: "第1章标题"
    pov: ""
  - number: 2
    title: "第2章标题"
    pov: ""
  # ... 更多章节
foreshadowing_in_this_volume: []
```
"""

    prompt += "\n## 写作要求\n"
    prompt += "1. 章节数量：根据小说规模确定，通常 20-50 章\n"
    prompt += "2. 每章要有明确的标题，可以先使用占位符如\"第X章\"\n"
    prompt += "3. 关键事件要列出本卷的重要转折点\n"
    prompt += "4. 结构部分要详细描述起承转合\n\n"

    prompt += f"现在请生成第{volume_num}卷的完整大纲 YAML：\n"

    return prompt


def build_chapter_outline_prompt(volume_num: int, chapter_num: int, paths: Dict[str, Any]) -> str:
    """Build prompt for AI-assisted chapter outline generation"""
    prompt = f"# 第{chapter_num}章大纲生成任务\n\n"

    prompt += "## 任务说明\n"
    prompt += "你是一位专业的小说大纲设计师。请根据以下信息，生成一份完整、格式正确的章节大纲 YAML 文件。\n\n"

    # Load volume outline
    outline_dir = paths['outline']
    volume = load_volume_outline(outline_dir, volume_num)
    if volume:
        prompt += "## 本卷大纲\n"
        prompt += json.dumps(volume, ensure_ascii=False, indent=2)
        prompt += "\n\n"

    # Get chapter title from volume outline
    chapter_title = f"第{chapter_num}章"
    chapter_pov = ""
    if volume:
        for ch in volume.get('chapter_list', []):
            if ch.get('number') == chapter_num:
                chapter_title = ch.get('title', chapter_title)
                chapter_pov = ch.get('pov', '')
                break

    # Load previous chapter if exists
    if chapter_num > 1:
        prev_chapter = load_chapter_outline(outline_dir, volume_num, chapter_num - 1)
        if prev_chapter:
            prompt += f"## 第{chapter_num - 1}章大纲（参考）\n"
            prompt += json.dumps(prev_chapter, ensure_ascii=False, indent=2)
            prompt += "\n\n"

    # Structure requirements
    prompt += "## 输出格式要求\n"
    prompt += "请直接输出 YAML 格式，不要任何说明文字。YAML 结构如下：\n\n"
    prompt += f"""```yaml
chapter_info:
  number: {chapter_num}
  volume: {volume_num}
  title: "{chapter_title}"
  pov: "{chapter_pov}"
  target_words: 3000
  tone: "neutral"
summary: "本章概要（300-500字，高层次概述：情节发展、人物弧光、情感节奏）"
key_scenes:
  - "场景1描述：包含地点、POV、关键动作/对话、情感点"
  - "场景2描述：..."
scene_list: []
plot_beats: []
foreshadowing: []
character_arcs_in_chapter: []
must_include: []
must_avoid: []
```
"""

    prompt += "\n## 重要：避免重复\n"
    prompt += "- summary 和 key_scenes 必须有明显区分：\n"
    prompt += "  * summary: 高层次概述，聚焦于情节发展和人物弧光\n"
    prompt += "  * key_scenes: 具体的场景列表，每个场景聚焦于某个关键时刻或对话\n\n"

    prompt += "## 写作要求\n"
    prompt += "1. summary 长度：300-500 字\n"
    prompt += "2. key_scenes：3-8 个关键场景\n"
    prompt += "3. 每个场景要包含：地点、POV、关键动作/对话、情感点\n"
    prompt += "4. 确保本章内容与卷大纲和前章衔接自然\n\n"

    prompt += f"现在请生成第{chapter_num}章的完整大纲 YAML：\n"

    return prompt


def save_and_output_prompt(prompt: str, prompt_path: Path, json_data: Dict[str, Any], display_title: str) -> None:
    """Save prompt to file and output result (common function)"""
    # Save prompt to file
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)

    # Output result
    if cli.is_json_mode():
        cli.output_json(json_data)
    else:
        cli.print_out(f"  {cli.c('✓ ' + display_title, cli.Colors.GREEN)}")
        cli.print_out(f"  Saved to: {prompt_path}")

        # Also show a preview
        cli.print_out(f"\n{cli.c('--- Prompt Preview ---', cli.Colors.BOLD)}")
        lines = prompt.split('\n')[:30]
        cli.print_out('\n'.join(lines))
        if len(lines) < len(prompt.split('\n')):
            cli.print_out("... (truncated, see full file)")


def generate_volume_outline_prompt(volume_num: int, paths: Dict[str, Any]) -> str:
    """Generate volume outline prompt and save to file"""
    if not cli.is_json_mode():
        cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
        cli.print_out(f"  {cli.c(f'[OUTLINE] Generating Volume {volume_num} Outline Prompt', cli.Colors.BOLD)}")
        cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")

    prompt = build_volume_outline_prompt(volume_num, paths)
    vol_prompts_dir = get_volume_prompts_dir(paths, volume_num)
    prompt_path = vol_prompts_dir / f'volume-{volume_num:03d}-outline-prompt.md'

    json_data = {
        'success': True,
        'volume': volume_num,
        'prompt_path': str(prompt_path),
        'prompt_content': prompt
    }

    save_and_output_prompt(prompt, prompt_path, json_data, "Volume outline prompt generated!")

    return prompt


def generate_chapter_outline_prompt(volume_num: int, chapter_num: int, paths: Dict[str, Any]) -> str:
    """Generate chapter outline prompt and save to file"""
    if not cli.is_json_mode():
        cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
        cli.print_out(f"  {cli.c(f'[OUTLINE] Generating Chapter {chapter_num} Outline Prompt', cli.Colors.BOLD)}")
        cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")

    # Check if volume exists
    outline_dir = paths['outline']
    volume = load_volume_outline(outline_dir, volume_num)
    if not volume:
        cli.error_message(f"Volume {volume_num} not found. Run 'story plan volume {volume_num}' first.")

    prompt = build_chapter_outline_prompt(volume_num, chapter_num, paths)
    vol_prompts_dir = get_volume_prompts_dir(paths, volume_num)
    prompt_path = vol_prompts_dir / f'chapter-{chapter_num:03d}-outline-prompt.md'

    json_data = {
        'success': True,
        'chapter': chapter_num,
        'volume': volume_num,
        'prompt_path': str(prompt_path),
        'prompt_content': prompt
    }

    save_and_output_prompt(prompt, prompt_path, json_data, "Chapter outline prompt generated!")

    return prompt


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

    # Check if chapter exists and has meaningful content
    existing = load_chapter_outline(outline_dir, volume_num, chapter_num)
    has_content = existing and (existing.get('summary', '').strip() or existing.get('key_scenes'))
    if existing and has_content:
        if not cli.is_interactive():
            cli.print_out(f"  {cli.c(f'Chapter {chapter_num} outline already exists, skipping', cli.Colors.YELLOW)}")
            return
        cli.print_out(f"  {cli.c(f'Warning: Chapter {chapter_num} outline is empty', cli.Colors.YELLOW)}")
        response = cli.input_with_default("Re-plan?", "Y", arg_key="replan")
        if response.strip().lower() != 'y':
            cli.print_out("  Cancelled")
            return
    elif existing and not has_content:
        # Empty outline - in non-interactive mode with args, proceed; otherwise skip
        if not cli.is_interactive():
            args = cli.get_args()
            if not (args.get('summary') or args.get('pov') or args.get('time')):
                cli.print_out(f"  {cli.c(f'Chapter {chapter_num} outline is empty, skipping', cli.Colors.YELLOW)}")
                return
        # Interactive mode: ask to replan
        # Interactive mode: ask to replan
        cli.print_out(f"  {cli.c(f'Warning: Chapter {chapter_num} outline is empty', cli.Colors.YELLOW)}")
        response = cli.input_with_default("Re-plan?", "Y", arg_key="replan")
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
    time_setting = cli.input_with_default("Time setting (e.g., 凌晨6:47, 上午10点)", "", arg_key="time")
    location = cli.input_with_default("Location (e.g., 合租房, 警局)", "", arg_key="location")
    characters = cli.input_with_default("Main characters (comma separated)", "", arg_key="characters")

    # Create outline
    outline = create_chapter_outline(chapter_num, volume_num, title, pov)
    outline['chapter_info']['time'] = time_setting
    outline['chapter_info']['location'] = location
    if characters:
        outline['chapter_info']['characters'] = [c.strip() for c in characters.split(',')]
    outline['summary'] = cli.input_with_default(
        "Chapter summary (客观描述事件，不暗示角色内心认知。如：'林默在6:47醒来，发现闹钟停在6:47'，禁止：'林默意识到时间重置了')",
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
  --prompt             Only generate AI prompt for outline creation
  --json               Output JSON format for AI consumption
  --non-interactive    Non-interactive mode (use --args)
  --args JSON          JSON string with arguments

Examples:
  story plan volume 1
  story plan volume 1 --no-timeline
  story plan volume 1 --prompt
  story plan chapter 1 5
  story plan chapter 1 5 --prompt
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
    prompt_only = False
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--no-timeline':
            no_timeline = True
            i += 1
        elif arg == '--prompt':
            prompt_only = True
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
            if prompt_only:
                generate_volume_outline_prompt(volume_num, paths)
            else:
                plan_volume(volume_num, paths, config, no_timeline)
        except ValueError:
            cli.error_message("Volume number must be an integer")
    elif target == 'chapter':
        if volume_num is None or chapter_num is None:
            cli.print_out("  Usage: story plan chapter <volume> <number>")
            return
        try:
            if prompt_only:
                generate_chapter_outline_prompt(volume_num, chapter_num, paths)
            else:
                plan_chapter(volume_num, chapter_num, paths)
        except ValueError:
            cli.error_message("Volume and chapter numbers must be integers")
    else:
        cli.print_out(f"  Unknown target: {target}")
        show_plan_help()


if __name__ == '__main__':
    main()
