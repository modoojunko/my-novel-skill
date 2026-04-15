#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
outline - Outline management (volume, chapter, scene formats)
"""

from pathlib import Path
from typing import Dict, Any, Optional, List


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


def save_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Save YAML file, with JSON fallback"""
    import json
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        if use_yaml:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)


def create_volume_outline(volume_num: int, title: str, theme: str = "") -> Dict[str, Any]:
    """Create a new volume outline structure"""
    return {
        'volume_info': {
            'number': volume_num,
            'title': title,
            'theme': theme,
        },
        'structure': {
            'opening': '',
            'development': '',
            'climax': '',
            'ending': '',
        },
        'key_events': [],
        'chapter_list': [],
        'foreshadowing_in_this_volume': [],
    }


def create_chapter_outline(chapter_num: int, volume_num: int, title: str, pov: str = "") -> Dict[str, Any]:
    """Create a new chapter outline structure
    
    Structure designed to avoid repetition (Issue #6):
    - summary: High-level overview, focusing on plot progression and character arcs
    - key_scenes: Specific scene-by-scene breakdown, each focusing on a particular moment
    """
    return {
        'chapter_info': {
            'number': chapter_num,
            'volume': volume_num,
            'title': title,
            'pov': pov,
            'target_words': 3000,
            'tone': 'neutral',
        },
        'summary': '',  # High-level overview: plot progression, character arcs, emotional beats
        'key_scenes': [],  # Specific scenes: each with location, POV, key action/dialogue
        'scene_list': [],
        'plot_beats': [],
        'foreshadowing': [],
        'character_arcs_in_chapter': [],
        'must_include': [],
        'must_avoid': [],
    }


def create_scene(scene_num: int, title: str, pov: str, location: str, scene_type: str = "transition") -> Dict[str, Any]:
    """Create a new scene structure"""
    return {
        'number': scene_num,
        'title': title,
        'pov': pov,
        'location': location,
        'type': scene_type,
        'key_details': [],
        'min_words': 500,
        'max_words': 1000,
    }


def add_chapter_to_volume(volume_outline: Dict[str, Any], chapter_num: int, title: str, pov: str = "") -> Dict[str, Any]:
    """Add a chapter to a volume outline"""
    chapter = {
        'number': chapter_num,
        'title': title,
        'pov': pov,
    }
    volume_outline['chapter_list'].append(chapter)
    return volume_outline


def add_scene_to_chapter(chapter_outline: Dict[str, Any], scene: Dict[str, Any]) -> Dict[str, Any]:
    """Add a scene to a chapter outline"""
    chapter_outline['scene_list'].append(scene)
    return chapter_outline


def get_volume_path(outline_dir: Path, volume_num: int) -> Path:
    """Get volume outline file path"""
    return outline_dir / f'volume-{volume_num:03d}.yaml'


def get_chapter_dir(outline_dir: Path, volume_num: int) -> Path:
    """Get chapter directory path"""
    return outline_dir / f'volume-{volume_num:03d}'


def get_chapter_path(outline_dir: Path, volume_num: int, chapter_num: int) -> Path:
    """Get chapter outline file path"""
    return get_chapter_dir(outline_dir, volume_num) / f'chapter-{chapter_num:03d}.yaml'


def load_volume_outline(outline_dir: Path, volume_num: int) -> Optional[Dict[str, Any]]:
    """Load a volume outline"""
    return load_yaml(get_volume_path(outline_dir, volume_num))


def save_volume_outline(outline_dir: Path, volume_num: int, data: Dict[str, Any]) -> None:
    """Save a volume outline"""
    save_yaml(get_volume_path(outline_dir, volume_num), data)


def load_chapter_outline(outline_dir: Path, volume_num: int, chapter_num: int) -> Optional[Dict[str, Any]]:
    """Load a chapter outline"""
    return load_yaml(get_chapter_path(outline_dir, volume_num, chapter_num))


def save_chapter_outline(outline_dir: Path, volume_num: int, chapter_num: int, data: Dict[str, Any]) -> None:
    """Save a chapter outline"""
    get_chapter_dir(outline_dir, volume_num).mkdir(parents=True, exist_ok=True)
    save_yaml(get_chapter_path(outline_dir, volume_num, chapter_num), data)


if __name__ == '__main__':
    # Test outline creation
    v1 = create_volume_outline(1, "风起云涌", "主角初入修仙界")
    v1 = add_chapter_to_volume(v1, 1, "山村少年", "张三")
    v1 = add_chapter_to_volume(v1, 2, "神秘小瓶", "张三")
    print("Volume outline created")

    ch1 = create_chapter_outline(1, 1, "山村少年", "张三")
    scene1 = create_scene(1, "山村清晨", "张三", "张三的小屋", "opening/setup")
    scene1['key_details'] = ["雾气弥漫的清晨", "张三在采药"]
    ch1 = add_scene_to_chapter(ch1, scene1)
    print("Chapter outline created")
