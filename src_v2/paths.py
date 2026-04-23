#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paths - Simplified path resolution module

Two-directory design:
- project_root: story.yaml (config file at root)
- process_dir: process/ (INFO, OUTLINE, PROMPTS, TEMPLATES)
- output_dir: output/ (CONTENT, EXPORT, ARCHIVE)
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any


def get_skill_templates_dir() -> Path:
    """Get skill templates directory (inside the skill installation, not user project)"""
    # Get the directory of this file (paths.py), which is in src_v2/
    this_file = Path(__file__)
    skill_root = this_file.parent.parent
    return skill_root / 'templates'


def get_skill_root_dir() -> Path:
    """Get skill root directory (inside the skill installation, not user project)"""
    # Get the directory of this file (paths.py), which is in src_v2/
    this_file = Path(__file__)
    return this_file.parent.parent


def get_writing_principles_template_path() -> Path:
    """Get writing principles template path from skill directory"""
    return get_skill_root_dir() / 'skills' / 'writing-principles.yaml'


def get_project_writing_principles_path(process_dir: Path) -> Path:
    """Get project-specific writing principles path"""
    templates_dir = process_dir / 'TEMPLATES'
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir / 'writing-principles.yaml'


def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """Check current directory for story.yaml (or story.json/story.yml for backward compatibility)"""
    if start is None:
        start = Path.cwd()
    if (start / 'story.yaml').exists():
        return start
    if (start / 'story.json').exists():
        return start
    if (start / 'story.yml').exists():
        return start
    return None


def load_config(root: Path) -> Dict[str, Any]:
    """Load story.yaml config (or story.json/story.yml for backward compatibility)"""
    # Try story.yaml first (preferred format)
    config_path = root / 'story.yaml'
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # Fall back to json if yaml not available
            pass

    # Try story.json (zero-dependency fallback)
    config_path = root / 'story.json'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Try story.yml
    config_path = root / 'story.yml'
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            pass

    return {}


def save_config(root: Path, config: Dict[str, Any]) -> None:
    """Save config to story.json (zero-dependency default) or story.yaml if PyYAML available"""
    # Prefer story.json for zero-dependency, but use story.yaml if PyYAML available
    try:
        import yaml
        config_path = root / 'story.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    except ImportError:
        # Fall back to json (zero-dependency)
        config_path = root / 'story.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)


def load_project_paths(root: Path) -> Dict[str, Path]:
    """Load all project paths, create directories if needed"""
    config = load_config(root)
    paths_cfg = config.get('paths', {})

    # Three main directories
    project_root = root
    process_dir = root / paths_cfg.get('process_dir', 'process')
    output_dir = root / paths_cfg.get('output_dir', 'output')

    # Create all directories
    dirs_to_create = [
        # Process dir structure
        process_dir / 'INFO',
        process_dir / 'INFO' / 'characters' / 'protagonist',
        process_dir / 'INFO' / 'characters' / 'main_cast',
        process_dir / 'INFO' / 'characters' / 'supporting',
        process_dir / 'INFO' / 'characters' / 'guest',
        # World building directories (Issue #4)
        process_dir / 'INFO' / 'world',
        process_dir / 'INFO' / 'world' / 'factions',
        process_dir / 'INFO' / 'world' / 'history',
        process_dir / 'INFO' / 'world' / 'powers',
        process_dir / 'INFO' / 'world' / 'organizations',
        process_dir / 'INFO' / 'world' / 'locations',
        process_dir / 'OUTLINE',
        process_dir / 'OUTLINE' / 'volume-001',
        process_dir / 'PROMPTS',
        # Output dir structure
        output_dir / 'CONTENT' / 'volume-001',
        output_dir / 'EXPORT',
        output_dir / 'ARCHIVE',
    ]

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

    return {
        'root': project_root,
        'process': process_dir,
        'output': output_dir,
        'info': process_dir / 'INFO',
        'characters': process_dir / 'INFO' / 'characters',
        'world': process_dir / 'INFO' / 'world',
        'world_factions': process_dir / 'INFO' / 'world' / 'factions',
        'world_history': process_dir / 'INFO' / 'world' / 'history',
        'world_powers': process_dir / 'INFO' / 'world' / 'powers',
        'world_organizations': process_dir / 'INFO' / 'world' / 'organizations',
        'world_locations': process_dir / 'INFO' / 'world' / 'locations',
        'outline': process_dir / 'OUTLINE',
        'snapshots': process_dir / 'OUTLINE',
        'prompts': process_dir / 'PROMPTS',
        'templates': get_skill_templates_dir(),
        'content': output_dir / 'CONTENT',
        'export': output_dir / 'EXPORT',
        'archive': output_dir / 'ARCHIVE',
        'world_basic': process_dir / 'INFO' / 'world' / 'basic.yaml',
        'world_timeline': process_dir / 'INFO' / 'world' / 'timeline.yaml',
    }


def get_volume_dir(paths: Dict[str, Path], volume_num: int, dir_type: str = 'outline') -> Path:
    """Get volume directory path"""
    vol_name = f'volume-{volume_num:03d}'
    if dir_type == 'outline':
        return paths['outline'] / vol_name
    elif dir_type == 'content':
        return paths['content'] / vol_name
    return paths['outline'] / vol_name


def get_chapter_path(paths: Dict[str, Path], chapter_num: int,
                     structure: Optional[Dict[str, Any]] = None, file_type: str = 'outline',
                     volume_num: Optional[int] = None) -> Path:
    """Get chapter file path

    Args:
        paths: Project paths dict
        chapter_num: Global chapter number OR chapter-in-volume if volume_num is provided
        structure: Project structure config (required for per-volume chapter counts)
        file_type: 'outline', 'content', or 'tasks'
        volume_num: If provided, chapter_num is treated as chapter-in-volume
    """
    if volume_num is None and structure is not None:
        # Auto-detect volume and get chapter-in-volume
        volume_num, chapter_in_volume = get_volume_and_chapter(chapter_num, structure)
    elif volume_num is None:
        # Fallback to old method if no structure
        chapters_per = 30
        volume_num = ((chapter_num - 1) // chapters_per) + 1
        chapter_in_volume = chapter_num
    else:
        # Volume explicitly provided, chapter_num is chapter-in-volume
        chapter_in_volume = chapter_num

    vol_dir = get_volume_dir(paths, volume_num, 'outline' if file_type == 'outline' else 'content')
    ch_name = f'chapter-{chapter_in_volume:03d}'

    if file_type == 'outline':
        return vol_dir / f'{ch_name}.yaml'
    elif file_type == 'content':
        return vol_dir / f'{ch_name}.md'
    elif file_type == 'tasks':
        return vol_dir / f'{ch_name}.tasks.md'
    return vol_dir / f'{ch_name}.yaml'


def get_volume_prompts_dir(paths: Dict[str, Path], volume_num: int) -> Path:
    """Get volume prompts directory path, creates it if it doesn't exist"""
    vol_name = f'volume-{volume_num:03d}'
    vol_prompts_dir = paths['prompts'] / vol_name
    vol_prompts_dir.mkdir(parents=True, exist_ok=True)
    return vol_prompts_dir


def get_chapters_for_volume(structure: Dict[str, Any], volume_num: int) -> int:
    """Get number of chapters for a specific volume, fallback to global chapters_per_volume"""
    # First check if volumes have per-volume config
    volumes_config = structure.get('volumes_config', {})
    vol_key = str(volume_num)
    if vol_key in volumes_config and 'chapters' in volumes_config[vol_key]:
        return volumes_config[vol_key]['chapters']
    # Fallback to global config
    return structure.get('chapters_per_volume', 30)


def get_volume_and_chapter(chapter_global_num: int, structure: Dict[str, Any]) -> tuple[int, int]:
    """Get volume number and chapter-in-volume number from global chapter number"""
    # Calculate by checking each volume's chapter count
    vol_num = 1
    total_volumes = structure.get('volumes', 1)

    while vol_num <= total_volumes:
        chapters_in_vol = get_chapters_for_volume(structure, vol_num)
        if chapter_global_num <= chapters_in_vol:
            return vol_num, chapter_global_num
        chapter_global_num -= chapters_in_vol
        vol_num += 1

    # If we exceed known volumes, use fallback logic with global chapters_per_volume
    chapters_per_vol = structure.get('chapters_per_volume', 30)
    vol_num = ((chapter_global_num - 1) // chapters_per_vol) + 1
    ch_in_vol = ((chapter_global_num - 1) % chapters_per_vol) + 1
    return vol_num, ch_in_vol


def get_global_chapter_num(volume_num: int, chapter_in_volume: int, structure: Dict[str, Any]) -> int:
    """Get global chapter number from volume number and chapter-in-volume"""
    global_num = 0
    # Add chapters from previous volumes
    for vol in range(1, volume_num):
        global_num += get_chapters_for_volume(structure, vol)
    # Add current volume's chapter
    return global_num + chapter_in_volume


def get_total_chapters(structure: Dict[str, Any]) -> int:
    """Get total number of chapters across all volumes"""
    total = 0
    total_volumes = structure.get('volumes', 0)
    for vol in range(1, total_volumes + 1):
        total += get_chapters_for_volume(structure, vol)
    return total
