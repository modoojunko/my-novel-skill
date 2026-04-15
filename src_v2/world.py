#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:world - World building management (Issue #4)

Manage comprehensive world building framework:
- Basic world settings (time, location, tech level)
- Factions/Groups
- History/Timeline
- Powers/Abilities system
- Organizations
- Locations

Supports both interactive and non-interactive modes:
- Interactive: `story world basic`
- Non-interactive: `story world basic --non-interactive --args '{"time":"202X"}'`
- JSON output: `story world basic --json`
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from .paths import find_project_root, load_config, load_project_paths
from .templates import get_collect_questions, ensure_default_templates
from . import cli


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


def save_world_element(world_dir: Path, element_type: str, name: str, data: Dict[str, Any]) -> Path:
    """
    Save a world element to the appropriate file.
    
    Args:
        world_dir: Path to world directory
        element_type: Type of element (basic, faction, history, power, organization, location)
        name: Name of the element (for multi-file types)
        data: Data to save
    
    Returns:
        Path to saved file
    """
    from datetime import datetime
    
    data['updated_at'] = datetime.now().isoformat()
    
    if element_type == 'basic':
        output_path = world_dir / 'basic.yaml'
    elif element_type == 'timeline':
        output_path = world_dir / 'timeline.yaml'
    elif element_type == 'faction':
        output_path = world_dir / 'factions' / f'{name.lower().replace(" ", "-")}.yaml'
    elif element_type == 'history':
        output_path = world_dir / 'history' / f'{name.lower().replace(" ", "-")}.yaml'
    elif element_type == 'power':
        output_path = world_dir / 'powers' / f'{name.lower().replace(" ", "-")}.yaml'
    elif element_type == 'organization':
        output_path = world_dir / 'organizations' / f'{name.lower().replace(" ", "-")}.yaml'
    elif element_type == 'location':
        output_path = world_dir / 'locations' / f'{name.lower().replace(" ", "-")}.yaml'
    else:
        raise ValueError(f"Unknown element type: {element_type}")
    
    save_yaml(output_path, data)
    return output_path


def list_world_elements(world_dir: Path, element_type: str) -> List[Path]:
    """List all world elements of a given type"""
    if element_type == 'faction':
        dir_path = world_dir / 'factions'
    elif element_type == 'history':
        dir_path = world_dir / 'history'
    elif element_type == 'power':
        dir_path = world_dir / 'powers'
    elif element_type == 'organization':
        dir_path = world_dir / 'organizations'
    elif element_type == 'location':
        dir_path = world_dir / 'locations'
    else:
        return []
    
    if not dir_path.exists():
        return []
    
    return list(dir_path.glob('*.yaml'))


def show_world_help():
    print("""
Usage: story world <target> [options]

World Building Targets:
  basic               Manage basic world settings
  timeline            Manage world timeline
  faction <name>      Manage a faction/group
  history <name>      Manage a historical event
  power <name>        Manage a power/ability system
  organization <name> Manage an organization
  location <name>     Manage an important location
  list                List all world elements
  export              Export world building as markdown

Options:
  --json               Output JSON format for AI consumption
  --non-interactive    Non-interactive mode (use --args)
  --args JSON          JSON string with answers

Examples:
  story world basic
  story world faction "破晓组织"
  story world list
  story world basic --non-interactive --args '{"time":"202X","location":"成都"}'
""")


def list_all_elements(world_dir: Path):
    """List all world building elements"""
    cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.BOLD)}")
    cli.print_out(f"  {cli.c('🌍 世界观设定总览', cli.Colors.BOLD)}")
    cli.print_out(f"{cli.c('═' * 60, cli.Colors.BOLD)}\n")
    
    # Basic settings
    basic_path = world_dir / 'basic.yaml'
    if basic_path.exists():
        basic = load_yaml(basic_path)
        cli.print_out(f"  {cli.c('📋 基本设定', cli.Colors.CYAN)}")
        if basic:
            for key, value in basic.items():
                if key not in ['updated_at', 'created_at'] and value:
                    cli.print_out(f"    - {key}: {value}")
        cli.print_out()
    
    # Timeline
    timeline_path = world_dir / 'timeline.yaml'
    if timeline_path.exists():
        cli.print_out(f"  {cli.c('⏰ 时间线', cli.Colors.CYAN)}: 已创建\n")
    
    # Factions
    factions = list_world_elements(world_dir, 'faction')
    if factions:
        cli.print_out(f"  {cli.c('⚔️  阵营/势力 ({len(factions)})', cli.Colors.CYAN)}")
        for f in factions:
            data = load_yaml(f)
            name = data.get('name', f.stem) if data else f.stem
            cli.print_out(f"    - {name}")
        cli.print_out()
    
    # Organizations
    orgs = list_world_elements(world_dir, 'organization')
    if orgs:
        cli.print_out(f"  {cli.c('🏢 组织 ({len(orgs)})', cli.Colors.CYAN)}")
        for o in orgs:
            data = load_yaml(o)
            name = data.get('name', o.stem) if data else o.stem
            cli.print_out(f"    - {name}")
        cli.print_out()
    
    # Powers
    powers = list_world_elements(world_dir, 'power')
    if powers:
        cli.print_out(f"  {cli.c('✨ 能力体系 ({len(powers)})', cli.Colors.CYAN)}")
        for p in powers:
            data = load_yaml(p)
            name = data.get('name', p.stem) if data else p.stem
            cli.print_out(f"    - {name}")
        cli.print_out()
    
    # Locations
    locations = list_world_elements(world_dir, 'location')
    if locations:
        cli.print_out(f"  {cli.c('📍 地点 ({len(locations)})', cli.Colors.CYAN)}")
        for loc in locations:
            data = load_yaml(loc)
            name = data.get('name', loc.stem) if data else loc.stem
            cli.print_out(f"    - {name}")
        cli.print_out()
    
    # History
    history = list_world_elements(world_dir, 'history')
    if history:
        cli.print_out(f"  {cli.c('📜 历史事件 ({len(history)})', cli.Colors.CYAN)}")
        for h in history:
            data = load_yaml(h)
            name = data.get('name', h.stem) if data else h.stem
            cli.print_out(f"    - {name}")
        cli.print_out()


def get_element_template_questions(element_type: str) -> list:
    """Get question template for a world element type"""
    templates = {
        'basic': [
            {'key': 'time', 'question': '世界的时间设定？（如：202X年现代、古代、未来、架空等）'},
            {'key': 'location', 'question': '主要地点/区域？'},
            {'key': 'technology', 'question': '科技/魔法水平？'},
            {'key': 'overview', 'question': '世界背景概述？'},
        ],
        'faction': [
            {'key': 'name', 'question': '阵营名称？'},
            {'key': 'goal', 'question': '阵营的目标/理念？'},
            {'key': 'strengths', 'question': '阵营的能力/特点？'},
            {'key': 'weaknesses', 'question': '阵营的弱点？'},
            {'key': 'relationships', 'question': '与其他阵营的关系？'},
            {'key': 'reveal_stage', 'question': '揭露阶段？（early/middle/late）'},
        ],
        'history': [
            {'key': 'name', 'question': '历史事件名称？'},
            {'key': 'time_period', 'question': '发生时间？'},
            {'key': 'description', 'question': '事件描述？'},
            {'key': 'impact', 'question': '对世界的影响？'},
            {'key': 'reveal_stage', 'question': '揭露阶段？（early/middle/late）'},
        ],
        'power': [
            {'key': 'name', 'question': '能力/体系名称？'},
            {'key': 'type', 'question': '能力类型？（如：觉醒者、异兽、魔法等）'},
            {'key': 'rules', 'question': '能力规则/限制？'},
            {'key': 'levels', 'question': '能力等级/分类？'},
            {'key': 'reveal_stage', 'question': '揭露阶段？（early/middle/late）'},
        ],
        'organization': [
            {'key': 'name', 'question': '组织名称？'},
            {'key': 'purpose', 'question': '组织的目的？'},
            {'key': 'structure', 'question': '组织结构？'},
            {'key': 'history', 'question': '组织历史？'},
            {'key': 'methods', 'question': '行动方式？'},
            {'key': 'reveal_stage', 'question': '揭露阶段？（early/middle/late）'},
        ],
        'location': [
            {'key': 'name', 'question': '地点名称？'},
            {'key': 'type', 'question': '地点类型？（城市、建筑、特殊地点等）'},
            {'key': 'description', 'question': '地点描述？'},
            {'key': 'importance', 'question': '重要性/意义？'},
            {'key': 'reveal_stage', 'question': '揭露阶段？（early/middle/late）'},
        ],
        'timeline': [
            {'key': 'anchor_date', 'question': '故事开始的日期？'},
            {'key': 'note', 'question': '时间线备注？'},
        ],
    }
    return templates.get(element_type, [])


def main():
    if len(sys.argv) < 2:
        show_world_help()
        return
    
    # Check for help
    if sys.argv[1] in ('help', '--help', '-h'):
        show_world_help()
        return
    
    target = sys.argv[1].lower()
    
    # Handle list command
    if target == 'list':
        root = find_project_root()
        if not root:
            cli.error_message("Not in a novel project (no story.yaml/story.json). Run 'story init' first.")
        paths = load_project_paths(root)
        list_all_elements(paths['world'])
        return
    
    # Handle export command
    if target == 'export':
        cli.print_out("  Export feature coming soon!")
        return
    
    # Parse element name for types that need it
    element_name = None
    remaining_args = sys.argv[2:]
    
    needs_name = ['faction', 'history', 'power', 'organization', 'location']
    if target in needs_name:
        if not remaining_args or remaining_args[0].startswith('-'):
            show_world_help()
            return
        # Collect name (may contain spaces)
        name_parts = []
        i = 0
        while i < len(remaining_args) and not remaining_args[i].startswith('-'):
            name_parts.append(remaining_args[i])
            i += 1
        element_name = ' '.join(name_parts)
        remaining_args = remaining_args[i:]
    
    # Insert dummy program name for argparse
    sys.argv = ['story-world'] + remaining_args
    
    # Parse CLI arguments
    parser = argparse.ArgumentParser(add_help=False)
    args, collect_args = cli.parse_cli_args(parser)
    
    # Find project root
    root = find_project_root()
    if not root:
        cli.error_message("Not in a novel project (no story.yaml/story.json). Run 'story init' first.")
    
    paths = load_project_paths(root)
    ensure_default_templates(paths['templates'])
    
    # Get questions for this element type
    questions = get_element_template_questions(target)
    if not questions:
        cli.error_message(f"Unknown target: {target}")
    
    # Collect answers
    answers = cli.collect_questions(questions, f'world-{target}')
    
    if not answers:
        if cli.is_json_mode():
            cli.output_json({'success': False, 'error': 'No answers collected'})
        return
    
    # For types that need name, ensure it's in answers
    if element_name and 'name' not in answers:
        answers['name'] = element_name
    
    # Save the element
    try:
        out_path = save_world_element(paths['world'], target, answers.get('name', 'unnamed'), answers)
        cli.collect_success_message(out_path, answers)
    except ValueError as e:
        cli.error_message(str(e))


if __name__ == '__main__':
    main()
