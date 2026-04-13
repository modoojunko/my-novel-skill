#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:init - Initialize simplified novel project
"""

import sys
from pathlib import Path
from datetime import datetime
from .paths import find_project_root, save_config, load_project_paths


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


def input_with_default(prompt: str, default: str = "") -> str:
    """Get input with default value"""
    user_input = input(f"  {prompt} [{default}]: ").strip()
    return user_input if user_input else default


def select_option(prompt: str, options: list) -> int:
    """Show selection menu"""
    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        try:
            choice = int(input(f"  Select [1-{len(options)}]: ").strip())
            if 1 <= choice <= len(options):
                return choice
        except ValueError:
            pass
        print(f"  {c('Invalid selection', Colors.RED)}")


def main():
    print(f"\n{c('═' * 60, Colors.CYAN)}")
    print(f"  {c('[INIT] Simplified Novel Workflow', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.CYAN)}\n")

    # Check if already initialized
    root = Path.cwd()
    if (root / 'story.yaml').exists() or (root / 'story.json').exists():
        print(f"  {c('Warning: story.yaml/story.json already exists', Colors.YELLOW)}")
        response = input(f"  Re-initialize? [y/N]: ").strip().lower()
        if response != 'y':
            print("  Cancelled")
            return

    # Collect basic info
    print(f"  {c('[STEP 1] Basic Info', Colors.BOLD)}")
    title = input_with_default("Book title", "My Novel")

    genre_options = ["玄幻", "都市", "科幻", "悬疑", "言情", "武侠", "历史", "游戏", "轻小说", "其他"]
    genre_idx = select_option("Select genre", genre_options)
    genre = genre_options[genre_idx - 1]

    target_words = int(input_with_default("Target word count", "500000"))
    volumes = int(input_with_default("Number of volumes", "3"))
    chapters_per_volume = int(input_with_default("Chapters per volume", "30"))

    print(f"\n  {c('[STEP 2] Writing Style', Colors.BOLD)}")
    tone_options = ["热血/成长", "轻松/幽默", "沉郁/厚重", "诙谐/搞笑", "严肃/正剧"]
    tone_idx = select_option("Overall tone", tone_options)
    tone = tone_options[tone_idx - 1]

    pacing = input_with_default("Pacing preference", "适中")
    description = input_with_default("Description preference", "详细")
    dialogue = input_with_default("Dialogue ratio", "平衡")
    examples = input_with_default("Reference works (optional)", "")

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

    # Create initial templates (minimal)
    _create_default_templates(paths)

    print(f"\n  {c('✓ Success!', Colors.GREEN)}")
    print(f"  Project initialized at: {root}")
    print(f"\n  Next steps:")
    print(f"    1. story collect core      - Collect core story info")
    print(f"    2. story collect protagonist - Create protagonist")
    print(f"    3. story plan volume 1     - Plan volume 1")
    print(f"    4. story status            - Check project status")


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


if __name__ == '__main__':
    main()
