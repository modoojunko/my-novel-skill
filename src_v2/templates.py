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
""", encoding='utf-8')

    # Chapter expand template
    chapter_expand = expand_dir / 'chapter.yaml'
    if not chapter_expand.exists():
        chapter_expand.write_text("""template: |
  # 章节大纲扩写任务

  ## 用户提供的核心信息
  {user_answers}

  ## 任务
  基于以上信息，生成完整的章节大纲。
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


if __name__ == '__main__':
    # Test template loading
    from .paths import find_project_root, load_project_paths
    root = find_project_root()
    if root:
        paths = load_project_paths(root)
        ensure_default_templates(paths['templates'])
        print("Templates ensured")
