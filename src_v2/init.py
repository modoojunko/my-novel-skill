#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:init - Initialize simplified novel project

Supports both interactive and non-interactive modes:
- Interactive: `story init` (asks questions)
- Non-interactive: `story init --non-interactive --args '{"title":"My Novel",...}'`
- JSON output: `story init --json --non-interactive --args '{"title":"..."}'`
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from .paths import find_project_root, save_config, load_project_paths, get_writing_principles_template_path, get_project_writing_principles_path
from . import cli


def show_init_help():
    print("""
Usage: story init [options]

Options:
  --json               Output JSON format for AI consumption
  --non-interactive    Non-interactive mode (use --args)
  --args JSON          JSON string with init arguments

Non-interactive args fields:
  title               Book title (default: "My Novel")
  genre               Genre (default: "玄幻")
  target_words        Target word count (default: 500000)
  volumes             Number of volumes (default: 3)
  chapters_per_volume Chapters per volume (default: 30)
  tone                Writing tone (default: "热血/成长")
  pacing              Pacing preference (default: "适中")
  description         Description preference (default: "详细")
  dialogue            Dialogue ratio (default: "平衡")
  examples            Comma-separated reference works (optional)
  reinit              Force re-initialize if project exists (bool)

Genres:
  玄幻, 都市, 科幻, 悬疑, 言情, 武侠, 历史, 游戏, 轻小说, 其他

Tones:
  热血/成长, 轻松/幽默, 沉郁/厚重, 诙谐/搞笑, 严肃/正剧

Examples:
  story init
  story init --non-interactive --args '{"title":"My Book","genre":"玄幻"}'
  story init --json --non-interactive --args '{"title":"My Book"}'
""")


def main():
    # Check for help
    if len(sys.argv) > 1 and sys.argv[1] in ('help', '--help', '-h'):
        show_init_help()
        return

    # Parse CLI arguments
    parser = argparse.ArgumentParser(add_help=False)
    args, init_args = cli.parse_cli_args(parser)

    if not cli.is_interactive() and not cli.is_json_mode():
        cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
        cli.print_out(f"  {cli.c('[INIT] Simplified Novel Workflow', cli.Colors.BOLD)}")
        cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")
    elif cli.is_interactive():
        cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
        cli.print_out(f"  {cli.c('[INIT] Simplified Novel Workflow', cli.Colors.BOLD)}")
        cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")

    # Check if already initialized
    root = Path.cwd()
    if (root / 'story.yaml').exists() or (root / 'story.json').exists():
        reinit = cli.confirm_action(
            "story.yaml/story.json already exists. Re-initialize?",
            default=False,
            arg_key='reinit'
        )
        if not reinit:
            if cli.is_json_mode():
                cli.output_json({'success': False, 'error': 'Project already exists, cancelled'})
            else:
                cli.print_out("  Cancelled")
            return

    # Collect basic info
    if cli.is_interactive():
        cli.print_out(f"  {cli.c('[STEP 1] Basic Info', cli.Colors.BOLD)}")

    genre_options = ["玄幻", "都市", "科幻", "悬疑", "言情", "武侠", "历史", "游戏", "轻小说", "其他"]
    tone_options = ["热血/成长", "轻松/幽默", "沉郁/厚重", "诙谐/搞笑", "严肃/正剧"]

    title = cli.input_with_default("Book title", "My Novel", arg_key='title')

    # Genre selection
    if cli.is_interactive():
        genre_idx = cli.select_option("Select genre", genre_options, arg_key='genre')
        genre = genre_options[genre_idx - 1]
    else:
        genre = init_args.get('genre', '玄幻')
        if genre not in genre_options:
            genre = '玄幻'

    target_words = int(cli.input_with_default("Target word count", "500000", arg_key='target_words'))
    volumes = int(cli.input_with_default("Number of volumes", "3", arg_key='volumes'))
    chapters_per_volume = int(cli.input_with_default("Chapters per volume", "30", arg_key='chapters_per_volume'))

    if cli.is_interactive():
        cli.print_out(f"\n  {cli.c('[STEP 2] Writing Style', cli.Colors.BOLD)}")

    # Tone selection
    if cli.is_interactive():
        tone_idx = cli.select_option("Overall tone", tone_options, arg_key='tone')
        tone = tone_options[tone_idx - 1]
    else:
        tone = init_args.get('tone', '热血/成长')
        if tone not in tone_options:
            tone = '热血/成长'

    pacing = cli.input_with_default("Pacing preference", "适中", arg_key='pacing')
    description = cli.input_with_default("Description preference", "详细", arg_key='description')
    dialogue = cli.input_with_default("Dialogue ratio", "平衡", arg_key='dialogue')
    examples = cli.input_with_default("Reference works (optional)", "", arg_key='examples')

    # Create config
    config = {
        "meta": {
            "version": "2.0-simplified",
            "created": datetime.now().strftime('%Y-%m-%d'),
            "updated": datetime.now().strftime('%Y-%m-%d'),
        },
        "book": {
            "title": title,
            "genre": genre,
            "target_words": target_words,
        },
        "structure": {
            "volumes": volumes,
            "chapters_per_volume": chapters_per_volume,
        },
        "style": {
            "tone": tone,
            "pacing": pacing,
            "description": description,
            "dialogue": dialogue,
            "examples": examples.split(',') if examples else [],
            # Date anchor configuration
            "date_anchor": {
                "enabled": True,
                "show_prev_next": True,
            },
            # Consistency check configuration
            "consistency": {
                "enabled": True,
                "check_character_names": True,
                "check_locations": True,
                "check_timeline": True,
                "check_world": True,
                "block_on_errors": True,
                "warn_on_warnings": True,
            },
        },
        "progress": {
            "current_volume": 1,
            "current_chapter": 0,
            "completed_chapters": [],
        },
        "paths": {
            "process_dir": "process",
            "output_dir": "output",
        },
    }

    # Save config and create directories
    save_config(root, config)
    paths = load_project_paths(root)

    # Copy writing principles template to project
    _copy_writing_principles_template(paths)

    # Create initial world.yaml
    _create_initial_world_yaml(paths)

    # Success output
    next_steps = [
        "story collect core      - Collect core story info",
        "story collect protagonist - Create protagonist",
        "story plan volume 1     - Plan volume 1",
        "story status            - Check project status",
    ]
    cli.init_success_message(root, next_steps)


def _create_default_templates(paths):
    """Create minimal default templates"""
    # Core collection template
    collect_core = paths['templates'] / 'collect' / 'core.yaml'
    collect_core.write_text("""questions:
  - key: story_concept
    question: "一句话故事概要？（如：一个___的___，在___中，必须___）"
  - key: core_theme
    question: "核心主题？（如：复仇与成长、忠诚与背叛）"
  - key: main_conflict_type
    question: "核心冲突类型？（正邪对立/情感纠葛/成长困境/其他）"
""", encoding='utf-8')

    # Core expansion template
    expand_core = paths['templates'] / 'expand' / 'core.yaml'
    expand_core.write_text("""template: |
  # 核心信息扩写任务

  ## 用户提供的核心信息
  {user_answers}

  ## 写作风格
  - 基调：{style_tone}
  - 节奏：{style_pacing}

  ## 任务
  基于以上信息，生成完整的 story-concept.yaml，包括：
  1. story_concept（一句话概要）
  2. core_theme（核心主题详述）
  3. premise（故事前提：如果...那么...）
  4. main_conflict（详细描述）
  5. ending_direction（大致结局走向）

  请直接返回 YAML 格式。
""", encoding='utf-8')


def _create_initial_world_yaml(paths):
    """Create empty world.yaml with initial structure"""
    world_path = paths['world']
    if not world_path.exists():
        import json
        try:
            import yaml
            use_yaml = True
        except ImportError:
            use_yaml = False

        initial_data = {
            'collected_at': None,
            'expanded_at': None,
            'core': {
                'background': {},
                'factions': {},
                'history': {},
                'entities': {},
                'rules': {},
                'locations': {},
            },
            'full': {
                'background': {},
                'factions': {},
                'history': {},
                'entities': {},
                'rules': {},
                'locations': {},
            },
        }

        with open(world_path, 'w', encoding='utf-8') as f:
            if use_yaml:
                yaml.dump(initial_data, f, allow_unicode=True, sort_keys=False)
            else:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)


def _copy_writing_principles_template(paths):
    """Copy writing principles template to project directory"""
    template_path = get_writing_principles_template_path()
    project_path = get_project_writing_principles_path(paths['process'])

    if template_path.exists() and not project_path.exists():
        import shutil
        shutil.copy2(template_path, project_path)


if __name__ == '__main__':
    main()
