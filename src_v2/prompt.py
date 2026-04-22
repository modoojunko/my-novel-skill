#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prompt - Smart prompt generation with layered summarization
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from .paths import load_project_paths, get_project_writing_principles_path
from .anti_repeat import (
    extract_scenes_from_snapshots,
    generate_forbidden_list,
    generate_suggested_scenes,
    build_prompt_section,
)
from .timeline import generate_date_anchor_prompt
from . import character_knowledge as ck


class SummaryLevel(Enum):
    FULL = "full"
    CORE = "core"
    MINIMAL = "minimal"


def load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Load YAML file, with JSON fallback"""
    import json
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False

    if not path.exists():
        return None

    with open(path, 'r', encoding='utf-8') as f:
        if use_yaml:
            try:
                return yaml.safe_load(f) or {}
            except:
                pass
        # Try JSON fallback
        try:
            f.seek(0)
            return json.load(f)
        except:
            return None


def load_core_info(info_dir: Path) -> Dict[str, Any]:
    """Load core story info"""
    core_path = info_dir / '01-core.yaml'
    if core_path.exists():
        return load_yaml(core_path) or {}
    return {}


def load_volume_outline(outline_dir: Path, volume_num: int) -> Optional[Dict[str, Any]]:
    """Load volume outline"""
    from .outline import load_volume_outline as load_vol
    return load_vol(outline_dir, volume_num)


def load_chapter_outline(outline_dir: Path, volume_num: int, chapter_num: int) -> Optional[Dict[str, Any]]:
    """Load chapter outline"""
    from .outline import load_chapter_outline as load_ch
    return load_ch(outline_dir, volume_num, chapter_num)


def summarize_volume_outline(volume: Dict[str, Any], level: str = 'full') -> str:
    """Summarize volume outline at different levels"""
    if level == 'full':
        import json
        return json.dumps(volume, ensure_ascii=False, indent=2)

    info = volume.get('volume_info', {})
    summary = f"Volume {info.get('number', '')}: {info.get('title', '')}\n"
    summary += f"Theme: {info.get('theme', '')}\n"

    if level == 'core':
        structure = volume.get('structure', {})
        if structure.get('opening'):
            summary += f"Opening: {structure['opening']}\n"
        if structure.get('climax'):
            summary += f"Climax: {structure['climax']}\n"

    return summary


def smart_truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text smartly, trying to keep sentence boundaries if possible."""
    if not text or len(text) <= max_length:
        return text

    # Try to truncate at a sentence break
    truncated = text[:max_length]
    last_period = truncated.rfind('。')
    last_exclamation = truncated.rfind('！')
    last_question = truncated.rfind('？')

    cut_pos = max(last_period, last_exclamation, last_question)
    if cut_pos > max_length * 0.5:  # Only use if it's not too early
        return truncated[:cut_pos + 1]

    # Otherwise, just truncate at the max length
    return truncated[:max_length - len(suffix)] + suffix


def summarize_chapter_outline(chapter: Dict[str, Any], level: str = 'full') -> str:
    """
    Summarize chapter outline at different levels with smart truncation.

    Levels:
    - full: All content, but with smart truncation to avoid overwhelming prompts
    - core: Only essential information
    - minimal: Bare minimum (for older chapters)
    """
    info = chapter.get('chapter_info', {})
    result = f"Chapter {info.get('number', '')}: {info.get('title', '')}\n"

    pov = info.get('pov', '')
    if pov:
        result += f"POV: {pov}\n"

    # Get config for max lengths (or use defaults)
    max_summary_length = 500
    max_scene_length = 200
    max_scenes = 10

    if level == 'minimal':
        max_summary_length = 200
        max_scene_length = 100
        max_scenes = 5

    # Add summary if available
    if level in ['core', 'full']:
        summary_text = chapter.get('summary', '') or chapter.get('brief_summary', '')
        if summary_text:
            truncated_summary = smart_truncate(summary_text, max_summary_length)
            result += f"\nSummary:\n{truncated_summary}\n"

    # Add key_scenes if available
    key_scenes = chapter.get('key_scenes', [])
    if key_scenes and level in ['core', 'full']:
        result += "\nKey Scenes:\n"
        # Limit number of scenes and truncate each
        for i, scene in enumerate(key_scenes[:max_scenes], 1):
            truncated_scene = smart_truncate(scene, max_scene_length)
            result += f"  {i}. {truncated_scene}\n"

        if len(key_scenes) > max_scenes:
            result += f"  ... (and {len(key_scenes) - max_scenes} more scenes)\n"

    # Add chapter objectives/tasks if available
    objectives = chapter.get('objectives', []) or chapter.get('tasks', [])
    if objectives and level in ['core', 'full']:
        result += "\nChapter Objectives:\n"
        for i, obj in enumerate(objectives[:5], 1):
            result += f"  {i}. {obj}\n"

    return result


def summarize_snapshots(snapshots_dir: Path, chapter_num: int, max_recent: int = 3) -> List[Dict[str, Any]]:
    """
    Summarize recent chapter snapshots.

    Args:
        snapshots_dir: Directory with snapshots
        chapter_num: Current chapter number
        max_recent: Number of recent chapters to include fully

    Returns:
        List of snapshot summaries
    """
    summaries = []

    # Look for snapshot files
    for i in range(max(1, chapter_num - 10), chapter_num):
        snapshot_path = snapshots_dir / f'chapter-{i:03d}.yaml'
        if snapshot_path.exists():
            snapshot = load_yaml(snapshot_path)
            if snapshot:
                if chapter_num - i <= max_recent:
                    # Full snapshot for recent chapters
                    summaries.append({
                        'chapter': i,
                        'full_snapshot': True,
                        'data': snapshot,
                    })
                else:
                    # Minimal summary for older chapters
                    summaries.append({
                        'chapter': i,
                        'key_events': snapshot.get('events_happened', [])[:3],
                        'new_chars': [c.get('name', '') for c in snapshot.get('characters_introduced', [])],
                    })

    return summaries


def get_characters_for_prompt(
    characters_dir: Path,
    pov_name: Optional[str] = None,
    chapter_characters: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Get characters with smart summarization for prompt.

    Args:
        characters_dir: Characters directory
        pov_name: POV character name (full info)
        chapter_characters: List of character names in this chapter

    Returns:
        Dictionary with characters at different summary levels
    """
    from .character import CharacterCategory, load_character, list_characters, summarize_character

    result = {
        'pov': None,
        'protagonist': None,
        'main_cast': [],
        'supporting': [],
        'guest': [],
    }

    # Load protagonist (full)
    protagonists = list_characters(characters_dir, CharacterCategory.PROTAGONIST)
    if protagonists:
        result['protagonist'] = protagonists[0]

    # Load POV character (full)
    if pov_name:
        # Try all categories
        for cat in CharacterCategory:
            pov_char = load_character(characters_dir, cat, pov_name)
            if pov_char:
                result['pov'] = pov_char
                break

    # Load main cast (full or core)
    main_cast = list_characters(characters_dir, CharacterCategory.MAIN_CAST)
    for char in main_cast:
        name = char.get('name', '')
        if chapter_characters and name in chapter_characters:
            result['main_cast'].append(char)  # Full if in chapter
        else:
            result['main_cast'].append(summarize_character(char, 'core'))

    # Load supporting (core or minimal)
    supporting = list_characters(characters_dir, CharacterCategory.SUPPORTING)
    for char in supporting:
        name = char.get('name', '')
        if chapter_characters and name in chapter_characters:
            result['supporting'].append(summarize_character(char, 'core'))
        else:
            result['supporting'].append(summarize_character(char, 'minimal'))

    # Load guests (minimal, only if in chapter)
    if chapter_characters:
        guests = list_characters(characters_dir, CharacterCategory.GUEST)
        for char in guests:
            name = char.get('name', '')
            if name in chapter_characters:
                result['guest'].append(summarize_character(char, 'minimal'))

    return result


def load_and_format_world_specs(paths: Dict[str, Any]) -> Optional[str]:
    """
    Load world specs from the new directory structure (Issue #4) and format as prompt section.

    Returns:
        Formatted prompt section or None if no world specs
    """
    world_dir = paths.get('world')
    if not world_dir or not world_dir.exists():
        return None

    section = "## 🌍 世界观设定（必读）\n\n"
    has_content = False

    # Title mapping for display
    titles = {
        'basic': '世界背景',
        'factions': '阵营/势力',
        'history': '关键历史',
        'powers': '能力体系',
        'organizations': '组织',
        'locations': '重要地点',
    }

    # 1. Load basic world settings
    basic_path = world_dir / 'basic.yaml'
    if basic_path.exists():
        basic_data = load_yaml(basic_path)
        if basic_data:
            section += f"### {titles['basic']}\n"
            for key, value in basic_data.items():
                if key not in ['updated_at', 'created_at'] and value:
                    section += f"- {key}: {value}\n"
            section += "\n"
            has_content = True

    # 2. Load timeline
    timeline_path = world_dir / 'timeline.yaml'
    if timeline_path.exists():
        timeline_data = load_yaml(timeline_path)
        if timeline_data:
            section += "### 时间线\n"
            for key, value in timeline_data.items():
                if key not in ['updated_at', 'created_at'] and value:
                    section += f"- {key}: {value}\n"
            section += "\n"
            has_content = True

    # 3. Load multi-file types
    multi_file_types = [
        ('factions', paths.get('world_factions')),
        ('history', paths.get('world_history')),
        ('powers', paths.get('world_powers')),
        ('organizations', paths.get('world_organizations')),
        ('locations', paths.get('world_locations')),
    ]

    for type_name, dir_path in multi_file_types:
        if dir_path and dir_path.exists():
            files = list(dir_path.glob('*.yaml'))
            if files:
                section += f"### {titles[type_name]}\n"
                for f in files:
                    data = load_yaml(f)
                    if data:
                        name = data.get('name', f.stem)
                        # Only include if revealed by current chapter
                        # TODO: Add reveal_stage filtering based on current chapter
                        section += f"- **{name}**:\n"
                        for key, value in data.items():
                            if key not in ['name', 'updated_at', 'created_at', 'reveal_stage'] and value:
                                section += f"  - {key}: {value}\n"
                section += "\n"
                has_content = True

    if not has_content:
        return None

    section += "⚠️  要求：本章内容必须严格遵守以上世界观设定！\n\n"
    section += "═══════════════════════════════════════════════════════════════\n\n"

    return section


def load_and_format_writing_principles(paths: Dict[str, Any]) -> Optional[str]:
    """
    Load writing principles from project templates and format as prompt section.

    Returns:
        Formatted prompt section or None if no principles
    """
    principles_path = get_project_writing_principles_path(paths['process'])
    if not principles_path.exists():
        return None

    principles = load_yaml(principles_path)
    if not principles:
        return None

    section = "## 📝 写作原则与风格（必读）\n\n"
    has_content = False

    # Style description
    style = principles.get('style', {})
    if style.get('description'):
        section += "### 整体写作风格\n"
        section += style['description']
        section += "\n\n"
        has_content = True

    # Core principles (sorted by priority)
    core_principles = principles.get('core_principles', [])
    if core_principles:
        section += "### 核心原则（按优先级）\n"
        # Sort by priority if available
        sorted_principles = sorted(core_principles, key=lambda p: p.get('priority', 999))
        for i, principle in enumerate(sorted_principles, 1):
            name = principle.get('name', f'原则{i}')
            desc = principle.get('description', '')
            if desc:
                section += f"{i}. **{name}**: {desc}\n"
        section += "\n"
        has_content = True

    # Techniques
    techniques = principles.get('techniques', {})
    for tech_name, tech_config in techniques.items():
        if tech_config and tech_config.get('enabled', True):
            guidelines = tech_config.get('guidelines', '')
            if guidelines:
                title = tech_name.replace('_', ' ').title()
                section += f"### {title}\n"
                section += guidelines
                section += "\n\n"
                has_content = True

    # Taboos
    taboos = principles.get('taboos', [])
    if taboos:
        section += "### ❌ 禁止事项\n"
        for taboo in taboos:
            section += f"- {taboo}\n"
        section += "\n"
        has_content = True

    if not has_content:
        return None

    section += "⚠️  要求：本章内容必须严格遵守以上写作原则！\n\n"
    section += "═══════════════════════════════════════════════════════════════\n\n"

    return section


def build_writing_prompt(
    paths: Dict[str, Any],
    volume_num: int,
    chapter_in_volume: int,
    chapter_global_num: int,
    config: Dict[str, Any],
) -> str:
    """
    Build a complete writing prompt with layered information.

    L0: Must have - Chapter outline, tasks, POV constraint (~30%)
    L1: Very important - Volume outline, protagonist, recent 3 chapters (~30%)
    L2: Useful - Other main cast, chapters 4-10 (~20%)
    L3: Optional - Earlier chapters, world details (~20%)
    """
    prompt = f"# 第{chapter_global_num}章写作任务\n\n"

    # ========== MANDATORY REQUIREMENTS ==========
    prompt += "## 写作要求（必须遵守）\n"
    prompt += "1. 严格按照本章大纲和关键场景写作，不要自由发挥\n"
    prompt += "2. 遵守 POV 角色认知约束，不要写其不知道的信息\n"
    prompt += "3. 不要添加提示词中未提及的新情节、新角色、新设定\n"
    prompt += "4. 只输出正文，不要任何说明、标记等过程文字\n\n"

    # ========== GLOBAL WRITING REQUIREMENTS (MUST READ FIRST) ==========
    prompt += "═══════════════════════════════════════════════════════════════\n"
    prompt += "  【全局写作要求 - 必须严格遵守】\n"
    prompt += "═══════════════════════════════════════════════════════════════\n\n"

    # Style info
    style = config.get('style', {})
    prompt += "## 核心写作风格\n"
    prompt += f"- 基调：{style.get('tone', 'N/A')}\n"
    prompt += f"- 节奏：{style.get('pacing', 'N/A')}\n"
    prompt += f"- 描写：{style.get('description', 'N/A')}\n"
    prompt += f"- 对话：{style.get('dialogue', 'N/A')}\n"
    if style.get('examples'):
        prompt += f"- 参考作品：{', '.join(style['examples'])}\n"
    prompt += "\n"

    # Writing requirements (from style.writing_requirements)
    writing_reqs = style.get('writing_requirements', {})
    if writing_reqs:
        prompt += "## 写作原则（必须遵守）\n"
        # Handle both dict and list formats
        if isinstance(writing_reqs, dict):
            for key, value in writing_reqs.items():
                if value:
                    prompt += f"- {key}: {value}\n"
        elif isinstance(writing_reqs, list):
            for req in writing_reqs:
                prompt += f"- {req}\n"
        prompt += "\n"

    # Character cognition strategy
    cognition_strategy = style.get('character_cognition_strategy')
    if cognition_strategy:
        prompt += "## 角色认知分层策略\n"
        if isinstance(cognition_strategy, dict):
            for key, value in cognition_strategy.items():
                prompt += f"- {key}: {value}\n"
        else:
            prompt += f"{cognition_strategy}\n"
        prompt += "\n"

    # Dual-line style contrast
    dual_line_style = style.get('dual_line_style_contrast')
    if dual_line_style:
        prompt += "## 双线风格对比\n"
        if isinstance(dual_line_style, dict):
            for key, value in dual_line_style.items():
                prompt += f"- {key}: {value}\n"
        else:
            prompt += f"{dual_line_style}\n"
        prompt += "\n"

    # Other style configs
    for key, value in style.items():
        if key not in ['tone', 'pacing', 'description', 'dialogue', 'examples',
                       'writing_requirements', 'character_cognition_strategy',
                       'dual_line_style_contrast']:
            if value:
                prompt += f"## {key.replace('_', ' ').title()}\n"
                if isinstance(value, dict):
                    for k, v in value.items():
                        prompt += f"- {k}: {v}\n"
                elif isinstance(value, list):
                    for item in value:
                        prompt += f"- {item}\n"
                else:
                    prompt += f"{value}\n"
                prompt += "\n"

    prompt += "═══════════════════════════════════════════════════════════════\n\n"

    # ========== POV CHARACTER COGNITION CONSTRAINTS ==========
    chapter = load_chapter_outline(paths['outline'], volume_num, chapter_in_volume)
    if chapter:
        chapter_info = chapter.get('chapter_info', {})
        pov_name = chapter_info.get('pov', '')
        if pov_name:
            knowledge_for_prompt = ck.get_character_knowledge_for_prompt(paths['info'], pov_name)
            if knowledge_for_prompt:
                prompt += "---\n"
                prompt += "## 📌 POV 角色认知约束（必须遵守！）\n"
                prompt += f"**当前 POV: {pov_name}**\n\n"

                knows = knowledge_for_prompt.get('knows', {})

                # Known events
                events = knows.get('events', [])
                if events:
                    prompt += "### 已知事件:\n"
                    for event in events:
                        prompt += f"- {event}\n"
                    prompt += "\n"

                # Known characters
                characters = knows.get('characters', [])
                if characters:
                    prompt += "### 已知人物:\n"
                    for char in characters:
                        prompt += f"- {char}\n"
                    prompt += "\n"

                # Known world
                world = knows.get('world', [])
                if world:
                    prompt += "### 已知事实:\n"
                    for fact in world:
                        prompt += f"- {fact}\n"
                    prompt += "\n"

                # Unaware
                unaware = knowledge_for_prompt.get('unaware', [])
                if unaware:
                    prompt += "### 绝对不能写的内容（角色不知道）:\n"
                    for item in unaware:
                        prompt += f"- {item}\n"
                    prompt += "\n"

                prompt += "---\n\n"

    # ========== WRITING PRINCIPLES ==========
    principles_section = load_and_format_writing_principles(paths)
    if principles_section:
        prompt += principles_section

    # ========== WORLD FRAMEWORK ==========
    world_section = load_and_format_world_specs(paths)
    if world_section:
        prompt += world_section

    # ========== DATE ANCHOR ==========
    style = config.get('style', {})
    date_anchor_config = style.get('date_anchor', {})

    if date_anchor_config.get('enabled', True):
        show_prev_next = date_anchor_config.get('show_prev_next', True)

        # Load volume outline to get timeline
        volume_outline = load_volume_outline(paths['outline'], volume_num)
        if volume_outline:
            timeline = volume_outline.get('timeline', {})
            if timeline and timeline.get('enabled', False):
                date_anchor = generate_date_anchor_prompt(timeline, chapter_global_num, show_prev_next)
                prompt += date_anchor

    # ========== ANTI-REPETITION CHECK ==========
    style = config.get('style', {})
    anti_repeat_config = style.get('anti_repeat', {})

    if anti_repeat_config.get('enabled', True):
        lookback = anti_repeat_config.get('lookback_chapters', 5)
        show_by_type = anti_repeat_config.get('show_by_type', True)
        show_by_chapter = anti_repeat_config.get('show_by_chapter', True)
        max_suggestions = anti_repeat_config.get('max_suggestions', 5)
        heuristics = anti_repeat_config.get('heuristics', None)

        # Get chapters per volume from config
        structure = config.get('structure', {})
        chapters_per_volume = structure.get('chapters_per_volume', 30)

        # Extract scenes from previous chapters
        scenes = extract_scenes_from_snapshots(
            paths['outline'],
            chapter_global_num,
            chapters_per_volume,
            lookback
        )

        if scenes:
            # Generate forbidden list
            forbidden_list = generate_forbidden_list(scenes)

            # Get chapter outline
            chapter_outline = load_chapter_outline(paths['outline'], volume_num, chapter_in_volume)

            # Generate suggestions
            suggestions = generate_suggested_scenes(
                forbidden_list,
                chapter_outline,
                heuristics
            )

            # Build prompt section
            anti_repeat_section = build_prompt_section(
                forbidden_list,
                suggestions,
                show_by_type,
                show_by_chapter
            )

            prompt += anti_repeat_section

    # ========== L0: Chapter info (MUST HAVE - smart summary) ==========
    if chapter:
        prompt += "## [L0] 本章信息（必须）\n"
        prompt += summarize_chapter_outline(chapter, 'full')
        prompt += "\n\n"

    # ========== L1: Volume & protagonist (MUST HAVE - complete) ==========
    volume = load_volume_outline(paths['outline'], volume_num)
    if volume:
        prompt += "## [L1] 本卷信息（必须完整）\n"
        prompt += summarize_volume_outline(volume, 'full')
        prompt += "\n\n"

    # Final reminder
    prompt += "现在开始写第 {} 章正文，直接从正文第一句开始写。\n".format(chapter_global_num)

    return prompt


if __name__ == '__main__':
    print("Prompt module loaded")
