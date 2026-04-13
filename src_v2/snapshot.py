#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
snapshot - Chapter setting snapshots to prevent plot inconsistency
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


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


def create_snapshot(
    chapter_num: int,
    volume_num: int,
    events_happened: Optional[List[str]] = None,
    characters_introduced: Optional[List[Dict[str, Any]]] = None,
    info_revealed: Optional[List[str]] = None,
    character_states: Optional[List[Dict[str, Any]]] = None,
    foils_planted: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create a new chapter snapshot"""
    return {
        'chapter': chapter_num,
        'volume': volume_num,
        'ended_at': datetime.now().isoformat(),
        'events_happened': events_happened or [],
        'characters_introduced': characters_introduced or [],
        'info_revealed': info_revealed or [],
        'character_states': character_states or [],
        'foils_planted': foils_planted or [],
    }


def get_snapshot_dir(outline_dir: Path, volume_num: int) -> Path:
    """Get snapshot directory for a volume"""
    return outline_dir / f'volume-{volume_num:03d}' / 'snapshots'


def get_snapshot_path(outline_dir: Path, volume_num: int, chapter_num: int) -> Path:
    """Get snapshot file path"""
    return get_snapshot_dir(outline_dir, volume_num) / f'chapter-{chapter_num:03d}.yaml'


def load_snapshot(outline_dir: Path, volume_num: int, chapter_num: int) -> Optional[Dict[str, Any]]:
    """Load a chapter snapshot"""
    return load_yaml(get_snapshot_path(outline_dir, volume_num, chapter_num))


def save_snapshot(outline_dir: Path, volume_num: int, chapter_num: int, snapshot: Dict[str, Any]) -> None:
    """Save a chapter snapshot"""
    save_yaml(get_snapshot_path(outline_dir, volume_num, chapter_num), snapshot)


def add_event(snapshot: Dict[str, Any], event: str) -> Dict[str, Any]:
    """Add an event to snapshot"""
    if 'events_happened' not in snapshot:
        snapshot['events_happened'] = []
    snapshot['events_happened'].append(event)
    return snapshot


def add_character_intro(
    snapshot: Dict[str, Any],
    name: str,
    role: str = "",
    first_appearance: str = "",
) -> Dict[str, Any]:
    """Add a character introduction to snapshot"""
    if 'characters_introduced' not in snapshot:
        snapshot['characters_introduced'] = []

    char_intro = {
        'name': name,
        'role': role,
        'first_appearance': first_appearance,
    }
    snapshot['characters_introduced'].append(char_intro)
    return snapshot


def add_info_reveal(snapshot: Dict[str, Any], info: str) -> Dict[str, Any]:
    """Add revealed info to snapshot"""
    if 'info_revealed' not in snapshot:
        snapshot['info_revealed'] = []
    snapshot['info_revealed'].append(info)
    return snapshot


def add_character_state_change(
    snapshot: Dict[str, Any],
    name: str,
    mood: str = "",
    knowledge_gained: Optional[List[str]] = None,
    relationships_changed: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Add character state change to snapshot"""
    if 'character_states' not in snapshot:
        snapshot['character_states'] = []

    state = {
        'name': name,
        'mood': mood,
        'knowledge_gained': knowledge_gained or [],
        'relationships_changed': relationships_changed or [],
    }
    snapshot['character_states'].append(state)
    return snapshot


def add_foil(
    snapshot: Dict[str, Any],
    description: str,
    payoff_chapter: Optional[int] = None,
) -> Dict[str, Any]:
    """Add a foil/foreshadowing to snapshot"""
    if 'foils_planted' not in snapshot:
        snapshot['foils_planted'] = []

    foil = {
        'description': description,
        'payoff_chapter': payoff_chapter,
    }
    snapshot['foils_planted'].append(foil)
    return snapshot


def get_recent_snapshots(
    outline_dir: Path,
    volume_num: int,
    up_to_chapter: int,
    count: int = 3,
) -> List[Dict[str, Any]]:
    """Get the most recent snapshots"""
    snapshots = []
    start = max(1, up_to_chapter - count)

    for ch in range(start, up_to_chapter):
        snapshot = load_snapshot(outline_dir, volume_num, ch)
        if snapshot:
            snapshots.append(snapshot)

    return snapshots


def summarize_snapshots_for_prompt(snapshots: List[Dict[str, Any]]) -> str:
    """Summarize snapshots for inclusion in writing prompt"""
    if not snapshots:
        return ""

    summary = "## 前情摘要（从快照生成）\n\n"

    for snap in snapshots:
        ch = snap.get('chapter', '')
        summary += f"### 第{ch}章\n"

        events = snap.get('events_happened', [])
        if events:
            summary += "- 已发生事件：\n"
            for event in events:
                summary += f"  - {event}\n"

        chars = snap.get('characters_introduced', [])
        if chars:
            summary += "- 已出场角色：\n"
            for char in chars:
                summary += f"  - {char.get('name', '')}\n"

        reveals = snap.get('info_revealed', [])
        if reveals:
            summary += "- 已揭示信息：\n"
            for reveal in reveals:
                summary += f"  - {reveal}\n"

        summary += "\n"

    return summary


if __name__ == '__main__':
    # Test snapshot creation
    snap = create_snapshot(1, 1)
    snap = add_event(snap, "张三得到了小绿瓶")
    snap = add_character_intro(snap, "王五", "反派", "场景2")
    snap = add_info_reveal(snap, "张三的身世之谜（部分揭开）")
    print("Snapshot created")
