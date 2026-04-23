#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anti_repeat - Anti-repetition mechanism for novel writing

Prevents AI from repeating scenes, dialogues, and behavior patterns
from previous chapters.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict


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


def extract_scenes_from_snapshots(
    outline_dir: Path,
    current_chapter_global: int,
    structure: Dict[str, Any],
    lookback: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract scenes from previous N chapter snapshots.

    Args:
        outline_dir: Outline directory (parent of volume-XXX dirs)
        current_chapter_global: Current global chapter number
        structure: Project structure config (with chapters_per_volume or volumes_config)
        lookback: Number of chapters to look back (default: 5)

    Returns:
        List of scene dicts, each with:
        {
            'chapter': chapter number,
            'type': 'event'|'character'|'info',
            'content': scene content,
            'source': 'events_happened'|'characters_introduced'|'info_revealed'
        }
    """
    from .paths import get_volume_and_chapter

    scenes = []
    start_chapter_global = max(1, current_chapter_global - lookback)

    for ch_global in range(start_chapter_global, current_chapter_global):
        # Calculate volume and chapter-in-volume for this chapter
        vol_for_ch, ch_in_vol = get_volume_and_chapter(ch_global, structure)

        # Get snapshot path - snapshot is in volume-XXX/snapshots/ with chapter-in-volume numbering
        snapshot_path = outline_dir / f'volume-{vol_for_ch:03d}' / 'snapshots' / f'chapter-{ch_in_vol:03d}.yaml'

        if not snapshot_path.exists():
            continue

        snapshot = load_yaml(snapshot_path)
        if not snapshot:
            continue

        # Extract events
        for event in snapshot.get('events_happened', []):
            scenes.append({
                'chapter': ch_global,
                'type': 'event',
                'content': event,
                'source': 'events_happened'
            })

        # Extract character introductions
        for char in snapshot.get('characters_introduced', []):
            char_name = char.get('name', '')
            char_role = char.get('role', '')
            content = char_name
            if char_role:
                content += f" ({char_role})"
            if content:
                scenes.append({
                    'chapter': ch_global,
                    'type': 'character',
                    'content': content,
                    'source': 'characters_introduced'
                })

        # Extract info reveals
        for info in snapshot.get('info_revealed', []):
            scenes.append({
                'chapter': ch_global,
                'type': 'info',
                'content': info,
                'source': 'info_revealed'
            })

    return scenes


def generate_forbidden_list(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate forbidden repetition list from scenes.

    Returns:
        {
            'all_scenes': [...],  # Flat list of all scenes
            'by_type': {
                'event': [...],
                'character': [...],
                'info': [...]
            },
            'by_chapter': {
                '1': [...],
                '2': [...]
            }
        }
    """
    result = {
        'all_scenes': [],
        'by_type': defaultdict(list),
        'by_chapter': defaultdict(list),
    }

    for scene in scenes:
        scene_entry = {
            'chapter': scene['chapter'],
            'content': scene['content']
        }
        result['all_scenes'].append(scene_entry)
        result['by_type'][scene['type']].append(scene_entry)
        result['by_chapter'][str(scene['chapter'])].append(scene_entry)

    # Convert defaultdict to regular dict
    result['by_type'] = dict(result['by_type'])
    result['by_chapter'] = dict(result['by_chapter'])

    return result


def generate_suggested_scenes(
    forbidden_list: Dict[str, Any],
    chapter_outline: Optional[Dict[str, Any]] = None,
    heuristics: Optional[List[Dict[str, str]]] = None
) -> List[str]:
    """
    Generate suggested new scenes based on forbidden list and chapter outline.

    Args:
        forbidden_list: Forbidden scene list
        chapter_outline: Current chapter outline (optional)
        heuristics: List of heuristic rules (optional)

    Returns:
        List of suggested scene ideas
    """
    if heuristics is None:
        # Default heuristics
        heuristics = [
            {
                'pattern': r'现场勘查|勘查现场|检查现场',
                'suggestion': '让证人主动找上门来提供线索，而不是主角去勘查'
            },
            {
                'pattern': r'门卫.*不记得|失忆.*证人',
                'suggestion': '证人记得，但因为害怕而有所隐瞒'
            },
            {
                'pattern': r'想敲门.*不敢|犹豫.*敲门',
                'suggestion': '直接推门进去，发现门没锁'
            },
            {
                'pattern': r'换了新锁|门锁被换',
                'suggestion': '门锁没换，但钥匙孔里有奇怪的东西'
            },
        ]

    suggestions = []
    all_content = ' '.join([s['content'] for s in forbidden_list.get('all_scenes', [])])

    # Apply heuristics
    for heuristic in heuristics:
        pattern = heuristic.get('pattern', '')
        suggestion = heuristic.get('suggestion', '')
        if pattern and suggestion:
            if re.search(pattern, all_content):
                suggestions.append(suggestion)

    # Limit to max 5 suggestions
    return suggestions[:5]


def build_prompt_section(
    forbidden_list: Dict[str, Any],
    suggestions: List[str],
    show_by_type: bool = True,
    show_by_chapter: bool = True
) -> str:
    """
    Build the anti-repetition section for the writing prompt.

    Args:
        forbidden_list: Forbidden scene list
        suggestions: List of suggested new scenes
        show_by_type: Whether to show scenes grouped by type
        show_by_chapter: Whether to show scenes grouped by chapter

    Returns:
        Formatted prompt section string
    """
    prompt = ""

    # Forbidden list section
    prompt += "## [防重复] 本章禁止重复的场景清单\n\n"
    prompt += "⚠️  以下场景在前5章已经出现过，本章请避免完全重复：\n\n"

    if show_by_type and forbidden_list.get('by_type'):
        prompt += "### 按类型分组：\n"
        type_names = {
            'event': '事件类',
            'character': '人物类',
            'info': '信息类'
        }
        for scene_type, scenes in forbidden_list['by_type'].items():
            type_name = type_names.get(scene_type, scene_type)
            prompt += f"- {type_name}：\n"
            for scene in scenes:
                prompt += f"  - 第{scene['chapter']}章：{scene['content']}\n"
        prompt += "\n"

    if show_by_chapter and forbidden_list.get('by_chapter'):
        prompt += "### 按章节分组：\n"
        for ch_num in sorted(forbidden_list['by_chapter'].keys(), key=int):
            scenes = forbidden_list['by_chapter'][ch_num]
            prompt += f"- 第{ch_num}章：\n"
            for scene in scenes:
                prompt += f"  - {scene['content']}\n"
        prompt += "\n"

    prompt += "---\n\n"

    # Suggestions section
    if suggestions:
        prompt += "## [建议] 本章可以尝试的新场景\n\n"
        prompt += "💡 基于本章大纲和前5章的情况，建议尝试：\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            prompt += f"{i}. {suggestion}\n"
        prompt += "\n---\n\n"

    return prompt


if __name__ == '__main__':
    print("anti_repeat module loaded")
