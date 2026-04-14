#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
character_knowledge - Character knowledge base management with smart summarization

Manages character-knowledge.yaml and provides smart summarization when
knowledge lists exceed threshold (default: 10 items).
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
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
            yaml.dump(data, f, allow_unicode=True, sort_keys=False,
                     default_flow_style=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_knowledge_path(info_dir: Path) -> Path:
    """Get character-knowledge.yaml file path"""
    return info_dir / 'character-knowledge.yaml'


def load_character_knowledge(info_dir: Path) -> Dict[str, Any]:
    """Load character knowledge base, create if doesn't exist"""
    path = get_knowledge_path(info_dir)
    if path.exists():
        return load_yaml(path) or {}
    return {}


def save_character_knowledge(info_dir: Path, knowledge: Dict[str, Any]) -> None:
    """Save character knowledge base"""
    save_yaml(get_knowledge_path(info_dir), knowledge)


def create_character_knowledge(
    name: str,
    world: Optional[List[str]] = None,
    characters: Optional[List[str]] = None,
    events: Optional[List[str]] = None,
    unaware: Optional[List[str]] = None,
    relationships: Optional[List[str]] = None,
    pov_restrictions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new character knowledge structure"""
    return {
        'knows': {
            'world': world or [],
            'characters': characters or [],
            'events': events or [],
        },
        'unaware': unaware or [],
        'relationships': relationships or [],
        'pov_restrictions': pov_restrictions or [],
    }


def add_world_knowledge(knowledge: Dict[str, Any], char_name: str, info: str) -> Dict[str, Any]:
    """Add world knowledge to a character"""
    if char_name not in knowledge:
        knowledge[char_name] = create_character_knowledge(char_name)
    if 'knows' not in knowledge[char_name]:
        knowledge[char_name]['knows'] = {'world': [], 'characters': [], 'events': []}
    if 'world' not in knowledge[char_name]['knows']:
        knowledge[char_name]['knows']['world'] = []
    knowledge[char_name]['knows']['world'].append(info)
    return knowledge


def add_character_knowledge(knowledge: Dict[str, Any], char_name: str, known_char: str) -> Dict[str, Any]:
    """Add character knowledge to a character"""
    if char_name not in knowledge:
        knowledge[char_name] = create_character_knowledge(char_name)
    if 'knows' not in knowledge[char_name]:
        knowledge[char_name]['knows'] = {'world': [], 'characters': [], 'events': []}
    if 'characters' not in knowledge[char_name]['knows']:
        knowledge[char_name]['knows']['characters'] = []
    knowledge[char_name]['knows']['characters'].append(known_char)
    return knowledge


def add_event_knowledge(knowledge: Dict[str, Any], char_name: str, event: str) -> Dict[str, Any]:
    """Add event knowledge to a character"""
    if char_name not in knowledge:
        knowledge[char_name] = create_character_knowledge(char_name)
    if 'knows' not in knowledge[char_name]:
        knowledge[char_name]['knows'] = {'world': [], 'characters': [], 'events': []}
    if 'events' not in knowledge[char_name]['knows']:
        knowledge[char_name]['knows']['events'] = []
    knowledge[char_name]['knows']['events'].append(event)
    return knowledge


def add_unaware(knowledge: Dict[str, Any], char_name: str, info: str) -> Dict[str, Any]:
    """Add something the character is unaware of"""
    if char_name not in knowledge:
        knowledge[char_name] = create_character_knowledge(char_name)
    if 'unaware' not in knowledge[char_name]:
        knowledge[char_name]['unaware'] = []
    knowledge[char_name]['unaware'].append(info)
    return knowledge


def add_relationship(knowledge: Dict[str, Any], char_name: str, relationship: str) -> Dict[str, Any]:
    """Add a relationship for the character"""
    if char_name not in knowledge:
        knowledge[char_name] = create_character_knowledge(char_name)
    if 'relationships' not in knowledge[char_name]:
        knowledge[char_name]['relationships'] = []
    knowledge[char_name]['relationships'].append(relationship)
    return knowledge


def add_pov_restriction(knowledge: Dict[str, Any], char_name: str, restriction: str) -> Dict[str, Any]:
    """Add a POV restriction for the character"""
    if char_name not in knowledge:
        knowledge[char_name] = create_character_knowledge(char_name)
    if 'pov_restrictions' not in knowledge[char_name]:
        knowledge[char_name]['pov_restrictions'] = []
    knowledge[char_name]['pov_restrictions'].append(restriction)
    return knowledge


# ============== Smart Summarization ==============

SUMMARY_THRESHOLD = 10


def extract_temporal_info(event: str) -> Optional[str]:
    """Extract temporal markers from event text"""
    time_patterns = [
        r'凌晨[一二三四五六七八九十\d]+点[到至]?[一二三四五六七八九十\d]*点*',
        r'下午[一二三四五六七八九十\d]+点[到至]?[一二三四五六七八九十\d]*点*[分]*',
        r'上午[一二三四五六七八九十\d]+点[到至]?[一二三四五六七八九十\d]*点*',
        r'晚上[一二三四五六七八九十\d]+点[到至]?[一二三四五六七八九十\d]*点*',
        r'今天',
        r'昨天',
        r'前天',
        r'第二天',
        r'第[一二三四五六七八九十百千\d]+章',
        r'近期',
    ]
    for pattern in time_patterns:
        match = re.search(pattern, event)
        if match:
            return match.group(0)
    return None


def extract_location_info(event: str) -> Optional[str]:
    """Extract location markers from event text"""
    location_patterns = [
        r'惠民小区',
        r'福安小区',
        r'302室',
        r'城东',
        r'城西',
        r'城南',
        r'城北',
        r'现场',
        r'房间',
    ]
    for pattern in location_patterns:
        if pattern in event:
            return pattern
    return None


def extract_topic(event: str) -> Optional[str]:
    """Extract topic/category from event"""
    topics = {
        '死亡': ['死亡', '死', '死者', '尸体'],
        '案件': ['案子', '案件', '查案', '报案'],
        '现场': ['现场', '房间', '痕迹', '门锁'],
        '人物': ['师父', '老李', '王大爷', '陈建国', '张建国'],
        '照片': ['照片', '笔记本'],
    }
    for topic, keywords in topics.items():
        for keyword in keywords:
            if keyword in event:
                return topic
    return None


def group_events_by_topic(events: List[str]) -> Dict[str, List[str]]:
    """Group events by topic/location/time"""
    groups = defaultdict(list)

    for event in events:
        # Try to group by location first
        location = extract_location_info(event)
        if location:
            groups[f'location:{location}'].append(event)
            continue

        # Then by topic
        topic = extract_topic(event)
        if topic:
            groups[f'topic:{topic}'].append(event)
            continue

        # Otherwise put in general
        groups['general'].append(event)

    return groups


def merge_similar_events(events: List[str]) -> List[str]:
    """Merge similar/related events"""
    if len(events) <= SUMMARY_THRESHOLD:
        return events

    merged = []
    seen = set()

    # First pass: identify and merge duplicates
    for i, event in enumerate(events):
        if i in seen:
            continue

        similar = [event]
        for j in range(i + 1, len(events)):
            if j in seen:
                continue
            # Check for similarity (simple overlap check)
            words1 = set(event.replace('，', ' ').replace('。', ' ').split())
            words2 = set(events[j].replace('，', ' ').replace('。', ' ').split())
            overlap = len(words1 & words2)
            if overlap >= 2:  # At least 2 words in common
                similar.append(events[j])
                seen.add(j)

        if len(similar) == 1:
            merged.append(event)
        else:
            # Merge similar events
            merged.append(f"[合并] {'; '.join(similar[:3])}" +
                        (f"... 等{len(similar)}条" if len(similar) > 3 else ""))

    return merged


def summarize_events_extractive(events: List[str], max_items: int = SUMMARY_THRESHOLD) -> Dict[str, Any]:
    """
    Extractive summarization: keep most important items, group/merge others.

    Returns a dict with either:
    - {'full': events} (if under threshold)
    - {'summary': [...], 'full_count': N} (if summarized)
    """
    if len(events) <= max_items:
        return {'full': events}

    # Group events
    groups = group_events_by_topic(events)

    summarized = {
        'summary': [],
        'full_count': len(events),
        'groups': {},
    }

    # Keep at most max_items total
    items_per_group = max(1, max_items // max(1, len(groups)))

    for group_key, group_events in groups.items():
        group_name = group_key.split(':', 1)[1] if ':' in group_key else group_key

        if len(group_events) <= items_per_group:
            summarized['groups'][group_name] = group_events
            summarized['summary'].extend(group_events)
        else:
            # Merge similar items in this group
            merged = merge_similar_events(group_events)
            # Take first N items
            summarized['groups'][group_name] = merged[:items_per_group]
            summarized['summary'].extend(merged[:items_per_group])

    # Trim to max_items
    summarized['summary'] = summarized['summary'][:max_items]

    return summarized


def summarize_character_knowledge(
    char_data: Dict[str, Any],
    threshold: int = SUMMARY_THRESHOLD,
) -> Dict[str, Any]:
    """
    Summarize a character's knowledge if any list exceeds threshold.

    Returns a new dict with summaries where needed.
    """
    result = char_data.copy()

    # Check and summarize events
    knows = char_data.get('knows', {})
    events = knows.get('events', [])

    if len(events) > threshold:
        summary = summarize_events_extractive(events, threshold)
        result['knows']['events'] = summary

    # Also check other lists if needed
    for list_key in ['world', 'characters']:
        items = knows.get(list_key, [])
        if len(items) > threshold * 2:  # Higher threshold for these
            result['knows'][list_key] = {
                'summary': items[:threshold],
                'full_count': len(items),
            }

    return result


def update_character_knowledge_with_summary(
    info_dir: Path,
    char_name: str,
    event: Optional[str] = None,
    world_knowledge: Optional[str] = None,
    character_knowledge: Optional[str] = None,
    unaware: Optional[str] = None,
    relationship: Optional[str] = None,
    pov_restriction: Optional[str] = None,
    threshold: int = SUMMARY_THRESHOLD,
) -> Dict[str, Any]:
    """
    Update character knowledge and apply smart summarization when needed.

    This is the main function to use for updating character knowledge.
    """
    knowledge = load_character_knowledge(info_dir)

    if char_name not in knowledge:
        knowledge[char_name] = create_character_knowledge(char_name)

    # Add new information
    if event:
        knowledge = add_event_knowledge(knowledge, char_name, event)
    if world_knowledge:
        knowledge = add_world_knowledge(knowledge, char_name, world_knowledge)
    if character_knowledge:
        knowledge = add_character_knowledge(knowledge, char_name, character_knowledge)
    if unaware:
        knowledge = add_unaware(knowledge, char_name, unaware)
    if relationship:
        knowledge = add_relationship(knowledge, char_name, relationship)
    if pov_restriction:
        knowledge = add_pov_restriction(knowledge, char_name, pov_restriction)

    # Apply summarization if needed
    knowledge[char_name] = summarize_character_knowledge(knowledge[char_name], threshold)

    # Save and return
    save_character_knowledge(info_dir, knowledge)
    return knowledge


def get_character_knowledge_for_prompt(
    info_dir: Path,
    char_name: str,
) -> Dict[str, Any]:
    """
    Get character knowledge formatted for inclusion in writing prompt.
    Expands summaries if needed for prompt context.
    """
    knowledge = load_character_knowledge(info_dir)
    if char_name not in knowledge:
        return {}

    char_data = knowledge[char_name]
    result = char_data.copy()

    # Expand event summaries if they exist
    knows = char_data.get('knows', {})
    if isinstance(knows.get('events'), dict) and 'summary' in knows['events']:
        result['knows']['events'] = knows['events']['summary']
        result['knows']['_events_was_summarized'] = knows['events'].get('full_count', 0)

    return result


if __name__ == '__main__':
    # Test summarization
    test_events = [
        "张建国死亡（41岁，本地人，无业，独居）",
        "死亡时间：今天凌晨两点到四点之间",
        "现场：门窗从里面反锁、无撬动痕迹、无其他出入口、地板有一个几乎看不见的小痕迹、房间太干净不正常",
        "死者状态：穿着睡衣、极度恐惧表情、无外伤、无血迹、无挣扎痕迹、无中毒迹象、无疾病征兆",
        "近期三起类似死亡案件",
        "三张照片对比，死者表情一模一样",
        "师父让她不要查这个案子",
        "师父会把案子交给老李接手",
        "时间：下午四点十七分（第一章）",
        "第二天悄悄返回惠民小区",
        "302室换了新锁",
        "房间被打扫得干干净净，没有命案痕迹",
        "死者家属联系不上，登记信息是假的",
        "门卫王大爷\"不记得\"她了，说302室本来就没人住",
        "周边居民要么说不知道，要么说没听说过",
        "昨天拍的照片不见了，笔记本也空了",
        "怀疑是陈建国安排别的手下清理的",
        "城东福安小区有人报警，警局来电",
    ]

    print("Testing summarization with", len(test_events), "events")
    summary = summarize_events_extractive(test_events, 10)

    if 'full' in summary:
        print("No summarization needed")
    else:
        print(f"Summarized from {summary['full_count']} events:")
        for i, item in enumerate(summary['summary'], 1):
            print(f"  {i}. {item}")
