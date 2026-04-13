#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
character - Character management with six-layer cognitive model
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum


class CharacterCategory(Enum):
    PROTAGONIST = "protagonist"
    MAIN_CAST = "main_cast"
    SUPPORTING = "supporting"
    GUEST = "guest"


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


def create_character(
    name: str,
    category: CharacterCategory,
    role: str = "",
    occupation: str = "",
) -> Dict[str, Any]:
    """Create a new character with basic structure"""
    char = {
        'name': name,
        'role': role,
        'category': category.value,
        'occupation': occupation,
        'status': 'active',
    }

    # Add category-specific fields
    if category in (CharacterCategory.PROTAGONIST, CharacterCategory.MAIN_CAST):
        char.update({
            'background': '',
            'appearance': [],
            'character_profile': {
                'outward_tags': [],
                'inward': {
                    'worldview': '',
                    'self_definition': '',
                    'values': [],
                    'core_abilities': [],
                    'skills': [],
                    'environment': '',
                },
            },
            'relationships': [],
            'cognition': {
                'known_characters': [],
                'known_info': [],
                'unknown_info': [],
                'pending_reveals': [],
            },
        })
    elif category == CharacterCategory.SUPPORTING:
        char.update({
            'appearance': '',
            'personality': '',
            'relationship_to_protagonist': '',
            'first_appearance': '',
        })
    elif category == CharacterCategory.GUEST:
        char.update({
            'appearance': '',
            'only_in_chapters': [],
        })

    return char


def add_relationship(
    character: Dict[str, Any],
    other_name: str,
    relationship_type: str,
    description: str = "",
    interaction_mode: str = "",
) -> Dict[str, Any]:
    """Add a relationship to a character"""
    if 'relationships' not in character:
        character['relationships'] = []

    relationship = {
        'name': other_name,
        'type': relationship_type,
        'description': description,
        'interaction_mode': interaction_mode,
    }
    character['relationships'].append(relationship)
    return character


def add_known_character(
    character: Dict[str, Any],
    other_name: str,
    relationship: str,
    learned_at: str = "",
) -> Dict[str, Any]:
    """Add a known character to cognition"""
    if 'cognition' not in character:
        character['cognition'] = {
            'known_characters': [],
            'known_info': [],
            'unknown_info': [],
            'pending_reveals': [],
        }

    known = {
        'name': other_name,
        'relationship': relationship,
        'learned_at': learned_at,
    }
    character['cognition']['known_characters'].append(known)
    return character


def add_known_info(character: Dict[str, Any], info: str) -> Dict[str, Any]:
    """Add known info to cognition"""
    if 'cognition' not in character:
        character['cognition'] = {
            'known_characters': [],
            'known_info': [],
            'unknown_info': [],
            'pending_reveals': [],
        }

    character['cognition']['known_info'].append(info)
    return character


def add_pending_reveal(
    character: Dict[str, Any],
    info: str,
    planned_chapter: int,
) -> Dict[str, Any]:
    """Add a pending reveal to cognition"""
    if 'cognition' not in character:
        character['cognition'] = {
            'known_characters': [],
            'known_info': [],
            'unknown_info': [],
            'pending_reveals': [],
        }

    reveal = {
        'info': info,
        'planned_chapter': planned_chapter,
    }
    character['cognition']['pending_reveals'].append(reveal)
    return character


def get_character_dir(characters_dir: Path, category: CharacterCategory) -> Path:
    """Get character directory for a category"""
    return characters_dir / category.value


def get_character_path(characters_dir: Path, category: CharacterCategory, name: str) -> Path:
    """Get character file path"""
    # Sanitize name for filename
    safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    return get_character_dir(characters_dir, category) / f'{safe_name}.yaml'


def load_character(characters_dir: Path, category: CharacterCategory, name: str) -> Optional[Dict[str, Any]]:
    """Load a character"""
    return load_yaml(get_character_path(characters_dir, category, name))


def save_character(characters_dir: Path, category: CharacterCategory, character: Dict[str, Any]) -> None:
    """Save a character"""
    name = character.get('name', 'unknown')
    save_yaml(get_character_path(characters_dir, category, name), character)


def list_characters(characters_dir: Path, category: Optional[CharacterCategory] = None) -> List[Dict[str, Any]]:
    """List all characters, optionally filtered by category"""
    characters = []

    categories = [category] if category else list(CharacterCategory)

    for cat in categories:
        cat_dir = get_character_dir(characters_dir, cat)
        if cat_dir.exists():
            for char_file in cat_dir.glob('*.yaml'):
                char = load_yaml(char_file)
                if char:
                    characters.append(char)

    return characters


def summarize_character(character: Dict[str, Any], level: str = 'full') -> Dict[str, Any]:
    """
    Summarize a character at different levels.

    Levels:
    - 'full': Complete character (for POV/protagonist)
    - 'core': Core summary (for main_cast)
    - 'minimal': Minimal summary (name + relationship)
    """
    name = character.get('name', '')
    category = character.get('category', '')

    if level == 'full':
        return character

    summary = {
        'name': name,
        'category': category,
    }

    if level == 'core':
        summary.update({
            'role': character.get('role', ''),
            'occupation': character.get('occupation', ''),
            'relationship_to_protagonist': character.get('relationship_to_protagonist', ''),
        })
        if 'personality' in character:
            summary['personality'] = character['personality']
        if 'character_profile' in character:
            summary['outward_tags'] = character['character_profile'].get('outward_tags', [])

    elif level == 'minimal':
        summary.update({
            'relationship': character.get('relationship_to_protagonist', ''),
        })

    return summary


if __name__ == '__main__':
    # Test character creation
    zhangsan = create_character(
        "张三",
        CharacterCategory.PROTAGONIST,
        "主角",
        "山村少年"
    )
    zhangsan['background'] = "从小在山村长大，不知道自己的身世，被村长收养。"
    zhangsan['appearance'] = ["身高175cm", "面容清秀", "常穿灰色布衣"]
    zhangsan['character_profile']['outward_tags'] = ["沉默寡言", "心思缜密", "外冷内热"]
    zhangsan['character_profile']['inward']['worldview'] = "这个世界弱肉强食，只有变强才能生存下去。"
    zhangsan['character_profile']['inward']['self_definition'] = "我只是一个普通的山村少年，无父无母，但我不想一辈子待在山里。"
    zhangsan['character_profile']['inward']['values'] = ["生存第一", "报恩", "不欠人情"]

    print("Character created:", zhangsan['name'])
