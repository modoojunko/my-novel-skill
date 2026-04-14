#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timeline - Timeline management for novel writing

Manages chapter dates, validates timeline continuity, and generates
date anchor prompts for consistent storytelling.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
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


def save_yaml(path: Path, data: Dict[str, Any]):
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
            try:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
                return
            except:
                pass
        # JSON fallback
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Parse date string with flexible formats.

    Supported formats:
    - "2024-10-15"
    - "2024-10-15 晚上"
    - "10-15"
    - "第一天"
    - "第2天"

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    # Remove time suffixes like "晚上", "上午", "下午"
    date_str = re.sub(r'[ \t]*(晚上|上午|下午|早上|凌晨|中午).*$', '', date_str)

    # Try full ISO format: "2024-10-15"
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        pass

    # Try month-day format: "10-15" (assume current year or 2024)
    try:
        parsed = datetime.strptime(date_str, '%m-%d')
        return parsed.replace(year=2024)
    except ValueError:
        pass

    # Try "第X天" format
    match = re.match(r'第(\d+)[天日]', date_str)
    if match:
        day_num = int(match.group(1))
        # Day 1 = 2024-10-01 as reference
        return datetime(2024, 10, 1) + (day_num - 1)

    return None


def generate_date_anchor_prompt(
    timeline: Dict[str, Any],
    chapter_num: int,
    show_prev_next: bool = True
) -> str:
    """
    Generate date anchor prompt section.

    Args:
        timeline: Timeline data from volume outline
        chapter_num: Current chapter number
        show_prev_next: Whether to show previous/next chapter dates

    Returns:
        Formatted prompt string
    """
    if not timeline or not timeline.get('enabled', False):
        return ""

    chapter_dates = timeline.get('chapter_dates', {})
    current_date = chapter_dates.get(str(chapter_num), '')

    if not current_date:
        return ""

    prompt = "## 📅 本章时间锚点\n\n"
    prompt += f"- 日期：{current_date}\n"

    # Try to parse and extract time component if present
    if ' ' in current_date:
        parts = current_date.split(' ', 1)
        prompt += f"- 时间：{parts[1]}\n"
    else:
        prompt += "- 时间：全天\n"

    if show_prev_next:
        prev_date = chapter_dates.get(str(chapter_num - 1), '')
        next_date = chapter_dates.get(str(chapter_num + 1), '')
        if prev_date:
            prompt += f"- 前一章：第{chapter_num - 1}章（{prev_date}）\n"
        if next_date:
            prompt += f"- 后一章：第{chapter_num + 1}章（{next_date}）\n"

    prompt += "\n⚠️  要求：正文可用\"今天\"、\"第二天\"等相对时间，但必须与本章日期一致！\n\n"
    prompt += "---\n\n"

    return prompt


def validate_timeline_continuity(
    timeline: Dict[str, Any],
    chapter_num: int,
    chapter_date: str
) -> Tuple[bool, List[str]]:
    """
    Validate timeline continuity for a chapter.

    Args:
        timeline: Timeline data
        chapter_num: Current chapter number
        chapter_date: Date for current chapter

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    if not timeline or not timeline.get('enabled', False):
        return True, []

    chapter_dates = timeline.get('chapter_dates', {})

    # Parse current date
    current_dt = parse_date_string(chapter_date)
    if not current_dt:
        # Can't parse, skip validation but warn
        issues.append(f"无法解析日期格式：{chapter_date}，时间线检查跳过")
        return True, issues

    # Check previous chapter
    prev_num = chapter_num - 1
    if str(prev_num) in chapter_dates:
        prev_date = chapter_dates[str(prev_num)]
        prev_dt = parse_date_string(prev_date)
        if prev_dt:
            if current_dt < prev_dt:
                issues.append(f"本章日期（{chapter_date}）早于前一章（{prev_date}）")

    # Check next chapter if already exists
    next_num = chapter_num + 1
    if str(next_num) in chapter_dates:
        next_date = chapter_dates[str(next_num)]
        next_dt = parse_date_string(next_date)
        if next_dt:
            if current_dt > next_dt:
                issues.append(f"本章日期（{chapter_date}）晚于后一章（{next_date}）")

    return len(issues) == 0, issues


def collect_timeline_for_volume(
    volume_outline: Dict[str, Any],
    non_interactive: bool = False
) -> Dict[str, Any]:
    """
    Collect timeline information for a volume (interactive or non-interactive).

    Args:
        volume_outline: Volume outline data
        non_interactive: Skip interactive prompts

    Returns:
        Updated volume outline with timeline field
    """
    if non_interactive:
        # Non-interactive mode: create empty timeline
        volume_outline['timeline'] = {
            'enabled': False,
            'chapter_dates': {},
            'timeline_notes': ''
        }
        return volume_outline

    # Get chapter list from outline
    chapter_list = volume_outline.get('chapter_list', [])
    if not chapter_list:
        # Create timeline with empty dates
        volume_outline['timeline'] = {
            'enabled': False,
            'chapter_dates': {},
            'timeline_notes': ''
        }
        return volume_outline

    print("\n  [TIMELINE]")
    response = input("  Do you want to set up a timeline for this volume? [Y/n]: ").strip().lower()
    if response not in ('', 'y', 'yes'):
        volume_outline['timeline'] = {
            'enabled': False,
            'chapter_dates': {},
            'timeline_notes': ''
        }
        return volume_outline

    # Get start date
    start_date = input("  Enter start date (e.g., 2024-10-01): ").strip()
    if not start_date:
        start_date = "2024-10-01"

    # Collect dates for each chapter
    chapter_dates = {}
    current_date = parse_date_string(start_date)

    print(f"\n  Set date for each chapter (Enter to auto-increment from previous):")

    for ch in chapter_list:
        ch_num = ch.get('number', 0)
        suggested_date = ""

        if ch_num == 1:
            suggested_date = start_date
        elif current_date:
            suggested_date = current_date.strftime('%Y-%m-%d')

        prompt = f"  Chapter {ch_num} date"
        if suggested_date:
            prompt += f" [{suggested_date}]"
        prompt += ": "

        user_date = input(prompt).strip()
        if not user_date and suggested_date:
            user_date = suggested_date

        chapter_dates[str(ch_num)] = user_date

        # Update current_date for next chapter
        parsed = parse_date_string(user_date)
        if parsed:
            current_date = parsed

    # Get timeline notes
    notes = input("\n  Timeline notes (optional): ").strip()

    volume_outline['timeline'] = {
        'enabled': True,
        'chapter_dates': chapter_dates,
        'timeline_notes': notes
    }

    return volume_outline


if __name__ == '__main__':
    print("timeline module loaded")
