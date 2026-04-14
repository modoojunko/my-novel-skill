#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prompt - Smart prompt generation with layered summarization
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from .paths import load_project_paths
from .anti_repeat import (
    extract_scenes_from_snapshots,
    generate_forbidden_list,
    generate_suggested_scenes,
    build_prompt_section,
)
from .timeline import generate_date_anchor_prompt


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


def summarize_chapter_outline(chapter: Dict[str, Any], level: str = 'full') -> str:
    """Summarize chapter outline at different levels"""
    if level == 'full':
        import json
        return json.dumps(chapter, ensure_ascii=False, indent=2)

    info = chapter.get('chapter_info', {})
    summary = f"Chapter {info.get('number', '')}: {info.get('title', '')}\n"
    summary += f"POV: {info.get('pov', '')}\n"

    if level == 'core':
        brief = chapter.get('brief_summary', '')
        if brief:
            summary += f"Summary: {brief}\n"

    return summary


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


def build_writing_prompt(
    paths: Dict[str, Any],
    volume_num: int,
    chapter_num: int,
    config: Dict[str, Any],
) -> str:
    """
    Build a complete writing prompt with layered information.

    L0: Must have - Chapter outline, tasks, POV constraint (~30%)
    L1: Very important - Volume outline, protagonist, recent 3 chapters (~30%)
    L2: Useful - Other main cast, chapters 4-10 (~20%)
    L3: Optional - Earlier chapters, world details (~20%)
    """
    prompt = f"# 第{chapter_num}章写作任务\n\n"

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
                date_anchor = generate_date_anchor_prompt(timeline, chapter_num, show_prev_next)
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

        # Get snapshot directory from outline dir
        snapshots_dir = paths['outline']

        # Extract scenes from previous chapters
        scenes = extract_scenes_from_snapshots(
            snapshots_dir,
            volume_num,
            chapter_num,
            lookback
        )

        if scenes:
            # Generate forbidden list
            forbidden_list = generate_forbidden_list(scenes)

            # Get chapter outline
            chapter_outline = load_chapter_outline(paths['outline'], volume_num, chapter_num)

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

    # ========== L0: Chapter info (MUST HAVE - complete) ==========
    chapter = load_chapter_outline(paths['outline'], volume_num, chapter_num)
    if chapter:
        prompt += "## [L0] 本章信息（必须完整）\n"
        prompt += summarize_chapter_outline(chapter, 'full')
        prompt += "\n\n"

    # ========== L1: Volume & protagonist (MUST HAVE - complete) ==========
    volume = load_volume_outline(paths['outline'], volume_num)
    if volume:
        prompt += "## [L1] 本卷信息（必须完整）\n"
        prompt += summarize_volume_outline(volume, 'full')
        prompt += "\n\n"

    return prompt


if __name__ == '__main__':
    print("Prompt module loaded")
