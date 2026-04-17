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
                     chapters_per: int = 30, file_type: str = 'outline') -> Path:
    """Get chapter file path"""
    volume_num = ((chapter_num - 1) // chapters_per) + 1
    vol_dir = get_volume_dir(paths, volume_num, 'outline' if file_type == 'outline' else 'content')
    ch_name = f'chapter-{chapter_num:03d}'

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
