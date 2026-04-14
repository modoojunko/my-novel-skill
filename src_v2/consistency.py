#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consistency - Detail consistency checking for novel writing

Checks character names, locations, timeline, and avoids repetition
by comparing actual usage against source data (character cards,
worldview specs, timeline).
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
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


def load_character_cards(characters_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load all character cards from the characters directory.

    Args:
        characters_dir: Path to INFO/characters/ directory

    Returns:
        Dictionary mapping character names to their full card data
    """
    from .character import CharacterCategory, list_characters, load_character

    result = {}

    # Load from all categories
    for cat in CharacterCategory:
        chars = list_characters(characters_dir, cat)
        for char in chars:
            name = char.get('name', '')
            if name:
                result[name] = char

    return result


def load_worldview_specs(specs_dir: Path) -> Dict[str, Any]:
    """
    Load worldview specifications from SPECS directory.

    Args:
        specs_dir: Path to SPECS/ directory

    Returns:
        Worldview specs dictionary
    """
    result = {
        'locations': [],
        'items': [],
        'terms': []
    }

    # Try to load worldview files
    worldview_file = specs_dir / 'worldview.yaml'
    if worldview_file.exists():
        data = load_yaml(worldview_file)
        if data:
            result.update(data)

    return result


def load_world_specs(world_path: Path) -> Optional[Dict[str, Any]]:
    """
    加载世界观设定。

    Returns:
        世界观设定 dict，优先用 full，没有则用 core
    """
    if not world_path.exists():
        return None

    world_data = load_yaml(world_path)
    if not world_data:
        return None

    # Get specs - prefer full, fall back to core
    specs = world_data.get('full', {})
    core = world_data.get('core', {})

    # Merge: use full if available, otherwise core
    merged = {}
    for key in ['background', 'factions', 'history', 'entities', 'rules', 'locations']:
        full_spec = specs.get(key, {})
        core_spec = core.get(key, {})
        if full_spec:
            merged[key] = full_spec
        elif core_spec:
            merged[key] = core_spec

    return merged if any(merged.values()) else None


def check_world_consistency(
    world_specs: Dict[str, Any],
    actual_usage: Dict[str, Any],
    chapter_content: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    检查章节内容是否符合世界观设定。

    检查项：
    - 地点名称是否在世界观中定义
    - 是否提到了世界观禁止的内容
    - 阵营描述是否一致

    Returns:
        (status, issues_list)
    """
    issues = []

    if not world_specs:
        return ("ok", issues)

    # Check locations - if world defines locations, check if chapter uses undefined ones
    world_locations = world_specs.get('locations', {})
    chapter_locations = actual_usage.get('locations_used', [])

    if world_locations and chapter_locations:
        # Extract defined location names
        defined_names = set()
        if isinstance(world_locations, dict):
            for v in world_locations.values():
                if v:
                    # Add the value itself and any parts that might be location names
                    defined_names.add(str(v))
        elif isinstance(world_locations, list):
            for loc in world_locations:
                defined_names.add(str(loc))

        # Simple heuristic check - just warn if we have world locations
        if defined_names:
            issues.append({
                'message': '本章使用了地点，请确认与世界观设定一致',
                'severity': 'info',
            })

    # Overall status - we keep this simple for now
    status = "ok"
    for issue in issues:
        if issue.get('severity') == 'error':
            status = "error"
            break
        elif issue.get('severity') == 'warning' and status == 'ok':
            status = "warning"

    return (status, issues)


def extract_actual_usage(
    chapter_content: str,
    chapter_outline: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract actual usage from chapter content.

    Uses simple keyword matching and pattern detection (no NLP).

    Args:
        chapter_content: Full chapter text
        chapter_outline: Optional chapter outline data

    Returns:
        Dictionary with:
        - character_names_used: {canonical_name: [variations_used]}
        - locations_used: [location_names]
        - time_expressions: [time_expressions_found]
        - potential_repeats: [patterns_that_might_be_repeats]
    """
    result = {
        'character_names_used': defaultdict(list),
        'locations_used': [],
        'time_expressions': [],
        'potential_repeats': []
    }

    if not chapter_content:
        return result

    # Extract time expressions
    time_patterns = [
        r'当天[早晚深夜午]',
        r'第二?天[早晚深夜午]?',
        r'第\d+天',
        r'\d+月\d+日',
        r'早上|上午|中午|下午|晚上|深夜|凌晨',
        r'今天|明天|昨天',
    ]
    for pattern in time_patterns:
        matches = re.findall(pattern, chapter_content)
        result['time_expressions'].extend(matches)

    # Deduplicate
    result['time_expressions'] = list(set(result['time_expressions']))

    # Look for potential repeat patterns (simple heuristic)
    repeat_indicators = [
        (r'门卫.*说.*没人住', '门卫对话模式'),
        (r'想敲门.*不敢|犹豫.*敲门', '敲门犹豫模式'),
        (r'现场勘查|勘查现场|检查现场', '现场勘查模式'),
        (r'系统提示音|那个声音|机械音', '系统提示音模式'),
        (r'夸.*手艺|厨艺.*好', '夸奖厨艺模式'),
        (r'洗碗|收拾碗筷', '洗碗场景'),
    ]
    for pattern, label in repeat_indicators:
        if re.search(pattern, chapter_content):
            result['potential_repeats'].append(label)

    return result


def check_character_name_consistency(
    character_cards: Dict[str, Dict[str, Any]],
    actual_usage: Dict[str, Any],
    snapshots_dir: Path,
    chapter_num: int
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Check character name consistency against previous chapters.

    Args:
        character_cards: Loaded character cards
        actual_usage: Extracted usage from current chapter
        snapshots_dir: Directory with chapter snapshots
        chapter_num: Current chapter number

    Returns:
        (status: 'ok'|'warning'|'error', issues_list)
    """
    issues = []

    # Load previous snapshots to compare naming
    prev_names = defaultdict(list)

    for ch in range(max(1, chapter_num - 5), chapter_num):
        # Try to load check results from previous chapters
        check_path = snapshots_dir / f'chapter-{ch:03d}-check.yaml'
        if check_path.exists():
            check_data = load_yaml(check_path)
            if check_data:
                # Extract character usage history if available
                pass

        # Also try snapshot itself
        snap_path = snapshots_dir / f'chapter-{ch:03d}.yaml'
        if snap_path.exists():
            snap = load_yaml(snap_path)
            if snap:
                for char in snap.get('characters_introduced', []):
                    name = char.get('name', '')
                    if name:
                        prev_names[name].append(ch)

    # TODO: More sophisticated name consistency check
    # For now, simple check passes if we can't do deep analysis

    return 'ok', issues


def check_location_consistency(
    worldview_specs: Dict[str, Any],
    actual_usage: Dict[str, Any]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Check location name consistency.

    Returns:
        (status, issues_list)
    """
    # TODO: Implement location consistency checking
    return 'ok', []


def check_timeline_consistency(
    timeline: Dict[str, Any],
    actual_usage: Dict[str, Any],
    chapter_num: int
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Check timeline consistency.

    Returns:
        (status, issues_list)
    """
    from .timeline import validate_timeline_continuity

    issues = []

    if not timeline or not timeline.get('enabled', False):
        return 'ok', []

    chapter_dates = timeline.get('chapter_dates', {})
    chapter_date = chapter_dates.get(str(chapter_num), '')

    if chapter_date:
        is_valid, timeline_issues = validate_timeline_continuity(
            timeline, chapter_num, chapter_date
        )
        for issue in timeline_issues:
            issues.append({
                'message': issue,
                'severity': 'warning'
            })

    # Check time expressions for contradictions
    time_exprs = actual_usage.get('time_expressions', [])
    # TODO: More sophisticated time expression analysis

    if issues:
        return 'warning', issues

    return 'ok', []


def run_all_consistency_checks(
    chapter_content: str,
    chapter_num: int,
    volume_num: int,
    paths: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run all consistency checks and generate a complete report.

    Args:
        chapter_content: Full chapter text
        chapter_num: Chapter number
        volume_num: Volume number
        paths: Project paths dictionary
        config: Project config

    Returns:
        Complete check results in chapter-XXX-check.yaml format
    """
    from datetime import datetime

    style = config.get('style', {})
    consistency_config = style.get('consistency', {})

    # Extract actual usage
    actual_usage = extract_actual_usage(chapter_content)

    # Load source data
    character_cards = {}
    if consistency_config.get('check_character_names', True):
        if 'characters' in paths:
            character_cards = load_character_cards(paths['characters'])

    worldview_specs = {}
    if consistency_config.get('check_locations', True):
        if 'specs' in paths:
            worldview_specs = load_worldview_specs(paths['specs'])

    # Load timeline
    timeline = {}
    if consistency_config.get('check_timeline', True):
        from .outline import load_volume_outline
        volume_outline = load_volume_outline(paths['outline'], volume_num)
        if volume_outline:
            timeline = volume_outline.get('timeline', {})

    # Load world specs
    world_specs = None
    if consistency_config.get('check_world', True):
        if 'world' in paths:
            world_specs = load_world_specs(paths['world'])

    # Run individual checks
    checks = {}

    # Character names
    char_status, char_issues = check_character_name_consistency(
        character_cards, actual_usage, paths['snapshots'], chapter_num
    )
    checks['character_names'] = {
        'status': char_status,
        'issues': char_issues
    }

    # Locations
    loc_status, loc_issues = check_location_consistency(
        worldview_specs, actual_usage
    )
    checks['locations'] = {
        'status': loc_status,
        'issues': loc_issues
    }

    # Timeline
    tl_status, tl_issues = check_timeline_consistency(
        timeline, actual_usage, chapter_num
    )
    checks['timeline'] = {
        'status': tl_status,
        'issues': tl_issues
    }

    # Anti-repeat (just report potential repeats, don't block)
    anti_repeat_issues = []
    for pattern in actual_usage.get('potential_repeats', []):
        anti_repeat_issues.append({
            'message': f"可能重复了'{pattern}'模式",
            'severity': 'warning'
        })
    checks['anti_repeat'] = {
        'status': 'warning' if anti_repeat_issues else 'ok',
        'issues': anti_repeat_issues
    }

    # World consistency
    if consistency_config.get('check_world', True) and world_specs:
        world_status, world_issues = check_world_consistency(
            world_specs, actual_usage, chapter_content
        )
        checks['world'] = {
            'status': world_status,
            'issues': world_issues
        }

    # Calculate summary
    total_checks = len(checks)
    passed = sum(1 for c in checks.values() if c['status'] == 'ok')
    warnings = sum(1 for c in checks.values() if c['status'] == 'warning')
    errors = sum(1 for c in checks.values() if c['status'] == 'error')

    result = {
        'check_results': {
            'chapter': chapter_num,
            'volume': volume_num,
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
            'summary': {
                'total_checks': total_checks,
                'passed': passed,
                'warnings': warnings,
                'errors': errors
            }
        }
    }

    return result


def format_check_report(
    check_results: Dict[str, Any],
    use_colors: bool = True
) -> str:
    """
    Format check report for terminal display.

    Args:
        check_results: Complete check results
        use_colors: Whether to use ANSI colors

    Returns:
        Formatted report string
    """
    results = check_results.get('check_results', {})
    checks = results.get('checks', {})
    summary = results.get('summary', {})

    if use_colors:
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
    else:
        GREEN = YELLOW = RED = ENDC = BOLD = ''

    report = f"\n{BOLD}═══ 章节检查报告 ═══{ENDC}\n\n"

    # Check details
    check_names = {
        'character_names': '角色称呼',
        'locations': '地点名称',
        'timeline': '时间线',
        'anti_repeat': '防重复',
        'world': '世界观'
    }

    for check_key, check_data in checks.items():
        name = check_names.get(check_key, check_key)
        status = check_data.get('status', 'unknown')
        issues = check_data.get('issues', [])

        status_color = GREEN
        if status == 'warning':
            status_color = YELLOW
        elif status == 'error':
            status_color = RED

        report += f"{name}: {status_color}{status.upper()}{ENDC}\n"

        for issue in issues:
            severity = issue.get('severity', 'warning')
            msg = issue.get('message', '')
            sev_color = YELLOW if severity == 'warning' else RED
            report += f"  {sev_color}●{ENDC} {msg}\n"

        report += "\n"

    # Summary
    report += f"{BOLD} summary:{ENDC}\n"
    report += f"  通过: {GREEN}{summary.get('passed', 0)}{ENDC}\n"
    report += f"  警告: {YELLOW}{summary.get('warnings', 0)}{ENDC}\n"
    report += f"  错误: {RED}{summary.get('errors', 0)}{ENDC}\n"

    return report


if __name__ == '__main__':
    print("consistency module loaded")
