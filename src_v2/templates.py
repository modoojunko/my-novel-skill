#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
templates - Template loading and management module
"""

from pathlib import Path
from typing import Dict, Any, Optional


def load_template(templates_dir: Path, template_type: str, template_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a template from the templates directory.

    Args:
        templates_dir: Path to templates directory (process/TEMPLATES/)
        template_type: 'collect' or 'expand'
        template_name: Template name without .yaml (e.g., 'core', 'characters')

    Returns:
        Template dictionary or None if not found
    """
    import json
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False

    template_path = templates_dir / template_type / f'{template_name}.yaml'
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            if use_yaml:
                return yaml.safe_load(f) or {}
            else:
                # Try JSON as fallback
                try:
                    return json.load(f)
                except:
                    return {}
    return None


def get_collect_questions(templates_dir: Path, template_name: str) -> list:
    """
    Get list of questions from a collect template.

    Args:
        templates_dir: Path to templates directory
        template_name: Template name (e.g., 'core', 'characters')

    Returns:
        List of question dicts with 'key' and 'question' fields
    """
    template = load_template(templates_dir, 'collect', template_name)
    if template and 'questions' in template:
        return template['questions']
    return []


def get_expand_template(templates_dir: Path, template_name: str) -> Optional[str]:
    """
    Get the template string from an expand template.

    Args:
        templates_dir: Path to templates directory
        template_name: Template name (e.g., 'core', 'characters')

    Returns:
        Template string or None if not found
    """
    template = load_template(templates_dir, 'expand', template_name)
    if template and 'template' in template:
        return template['template']
    return None


def render_template(template_str: str, context: Dict[str, Any]) -> str:
    """
    Simple template rendering using {key} syntax.

    Args:
        template_str: Template string with {placeholders}
        context: Dictionary with placeholder values

    Returns:
        Rendered string
    """
    result = template_str
    for key, value in context.items():
        placeholder = f'{{{key}}}'
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    return result


def ensure_default_templates(templates_dir: Path) -> None:
    """
    Ensure all default templates exist, create them if missing.

    Args:
        templates_dir: Path to templates directory
    """
    collect_dir = templates_dir / 'collect'
    expand_dir = templates_dir / 'expand'
    collect_dir.mkdir(parents=True, exist_ok=True)
    expand_dir.mkdir(parents=True, exist_ok=True)

    # Core collect template
    core_collect = collect_dir / 'core.yaml'
    if not core_collect.exists():
        core_collect.write_text("""questions:
  - key: story_concept
    question: "一句话故事概要？（如：一个___的___，在___中，必须___）"
  - key: core_theme
    question: "核心主题？（如：复仇与成长、忠诚与背叛）"
  - key: main_conflict_type
    question: "核心冲突类型？（正邪对立/情感纠葛/成长困境/其他）"
""", encoding='utf-8')

    # Core expand template
    core_expand = expand_dir / 'core.yaml'
    if not core_expand.exists():
        core_expand.write_text("""template: |
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

    # Characters collect template
    chars_collect = collect_dir / 'characters.yaml'
    if not chars_collect.exists():
        chars_collect.write_text("""questions:
  - key: protagonist_name
    question: "主角叫什么名字？"
  - key: protagonist_role
    question: "主角的身份/职业是？"
  - key: protagonist_goal
    question: "主角想要什么？"
  - key: important_sidechars
    question: "有哪些重要配角？（名字+身份，用逗号分隔）"
""", encoding='utf-8')

    # Characters expand template
    chars_expand = expand_dir / 'characters.yaml'
    if not chars_expand.exists():
        chars_expand.write_text("""template: |
  # 角色设定扩写任务

  ## 用户提供的核心信息
  {user_answers}

  ## 任务
  基于以上信息，生成完整的角色设定。
  请直接返回 YAML 格式。
""", encoding='utf-8')

    # Volume collect template
    volume_collect = collect_dir / 'volume.yaml'
    if not volume_collect.exists():
        volume_collect.write_text("""questions:
  - key: volume_theme
    question: "这一卷的主题是什么？"
  - key: key_event_start
    question: "这一卷的开场发生了什么？"
  - key: key_event_mid
    question: "这一卷的中间发展是？"
  - key: key_event_climax
    question: "这一卷的高潮是什么？"
  - key: key_event_end
    question: "这一卷怎么收尾？"
""", encoding='utf-8')

    # Volume expand template
    volume_expand = expand_dir / 'volume.yaml'
    if not volume_expand.exists():
        volume_expand.write_text("""template: |
  # 卷大纲扩写任务

  ## 用户提供的核心信息
  {user_answers}

  ## 任务
  基于以上信息，生成完整的卷大纲。
  请直接返回 YAML 格式。
""", encoding='utf-8')

    # Chapter collect template
    chapter_collect = collect_dir / 'chapter.yaml'
    if not chapter_collect.exists():
        chapter_collect.write_text("""questions:
  - key: chapter_pov
    question: "本章 POV 角色是谁？"
  - key: chapter_location
    question: "本章主要发生在哪里？"
  - key: key_event
    question: "本章的关键事件是什么？"
  - key: summary
    question: "章节概要（客观描述事件，不暗示角色内心认知。如：'林默在6:47醒来，发现闹钟停在6:47'，禁止：'林默意识到时间重置了'）"
""", encoding='utf-8')

    # Chapter expand template
    chapter_expand = expand_dir / 'chapter.yaml'
    if not chapter_expand.exists():
        chapter_expand.write_text("""template: |
  # 章节大纲扩写任务 (避免重复 - Issue #6)

  ## 用户提供的核心信息
  {user_answers}

  ## 重要：避免重复指导
  - summary 和 key_scenes 必须有明显区分：
    * summary: 高层次概述，聚焦于情节发展和人物弧光
    * key_scenes: 具体的场景列表，每个场景聚焦于某个关键时刻或对话

  ## 任务
  基于以上信息，生成完整的章节大纲，包含：
  1. chapter_info（章节基本信息）
  2. summary（300-500字的高层次概述：情节发展、人物弧光、情感节奏）
  3. key_scenes（场景列表，每个场景包含：地点、POV、关键动作/对话、情感点）
  
  请直接返回 YAML 格式。
""", encoding='utf-8')

    # Writing expand template
    writing_expand = expand_dir / 'writing.yaml'
    if not writing_expand.exists():
        writing_expand.write_text("""template: |
  # 写作任务

  ## 本章大纲
  {chapter_outline}

  ## 任务
  根据以上大纲写正文。
""", encoding='utf-8')

    # World collect template
    world_collect = collect_dir / 'world.yaml'
    if not world_collect.exists():
        world_collect.write_text("""questions:
  # Background
  - key: background_time
    question: "世界的时间设定？（如：202X年现代、古代、未来、架空等）"
  - key: background_location
    question: "主要地点/区域？"
  - key: background_technology
    question: "科技/魔法水平？"
  - key: background_overview
    question: "世界背景概述？"

  # Factions
  - key: factions_main
    question: "有哪些主要阵营/势力？"

  # History
  - key: history_key_events
    question: "有哪些关键历史事件？"

  # Entities
  - key: entities_special
    question: "有哪些特殊存在/生物/种族？"

  # Rules
  - key: rules_world
    question: "世界有什么特殊规则？"

  # Locations
  - key: locations_important
    question: "有哪些重要地点？"
""", encoding='utf-8')

    # World expand template
    world_expand = expand_dir / 'world.yaml'
    if not world_expand.exists():
        world_expand.write_text("""template: |
  # 世界观设定扩写任务

  ## 用户提供的核心信息
  {user_answers}

  ## 写作风格
  - 基调：{style_tone}
  - 节奏：{style_pacing}

  ## 任务
  基于以上信息，生成完整的世界观设定，包括：
  1. background（详细的世界背景）
  2. factions（详细的阵营/势力设定）
  3. history（详细的历史/时间线）
  4. entities（详细的特殊存在设定）
  5. rules（详细的世界规则）
  6. locations（详细的重要地点）

  请直接返回 YAML 格式。
""", encoding='utf-8')


if __name__ == '__main__':
    # Test template loading
    from .paths import find_project_root, load_project_paths
    root = find_project_root()
    if root:
        paths = load_project_paths(root)
        ensure_default_templates(paths['templates'])
        print("Templates ensured")
