#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
character_cmd - Character knowledge management CLI

Commands:
  story character list                    # 列出所有角色及认知状态
  story character view <角色名>          # 查看单个角色的详细认知
  story character update <角色名>       # 更新角色认知
    --event "..."            # 添加已知事件
    --world "..."            # 添加已知世界事实
    --character "..."        # 添加已知人物
    --unaware "..."          # 添加不知道的信息
    --relationship "..."  # 添加关系备注
    --pov "..."              # 添加POV限制
  story character check <角色名>        # 检查POV一致性
    --chapter <章节>        # 指定章节号
  story character export <角色名>         # 导出认知给提示词
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add src_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from src_v2 import paths, cli
from src_v2 import character_knowledge as ck


def show_help():
    print("""
Usage: story character <subcommand> [options]

Subcommands:
  list                    List all characters and their knowledge status
  view <name>             View detailed knowledge for a character
  update <name>           Update character knowledge
  check <name>            Check POV consistency
  export <name>           Export knowledge for prompt inclusion

Use 'story character <subcommand> --help' for more info.
""")


def list_characters(info_dir: Path):
    """List all characters and their knowledge status"""
    knowledge = ck.load_character_knowledge(info_dir)

    if not knowledge:
        cli.print_out(f"  {cli.c('No characters found', cli.Colors.YELLOW)}")
        return

    cli.print_out(f"\n  {cli.c('═' * 60, cli.Colors.CYAN)}")
    cli.print_out(f"  {cli.c('[CHARACTERS] Knowledge Base', cli.Colors.BOLD)}")
    cli.print_out(f"  {cli.c('═' * 60, cli.Colors.CYAN)}\n")

    for name, data in sorted(knowledge.items()):
        knows = data.get('knows', {})
        world_count = len(knows.get('world', []))
        char_count = len(knows.get('characters', []))
        event_count = len(knows.get('events', []))
        unaware_count = len(data.get('unaware', []))

        # Handle summarized counts
        if isinstance(knows.get('events'), dict) and 'full_count' in knows['events']:
            event_count = knows['events']['full_count']

        cli.print_out(f"  {cli.c(name, cli.Colors.BOLD)}")
        cli.print_out(f"    已知世界: {world_count} | 已知人物: {char_count} | "
                     f"已知事件: {event_count} | 未知信息: {unaware_count}")
        cli.print_out()


def view_character(info_dir: Path, name: str):
    """View detailed knowledge for a character"""
    knowledge = ck.load_character_knowledge(info_dir)

    if name not in knowledge:
        cli.error_message(f"Character '{name}' not found")
        return

    data = knowledge[name]
    knows = data.get('knows', {})

    cli.print_out(f"\n  {cli.c('═' * 60, cli.Colors.CYAN)}")
    cli.print_out(f"  {cli.c(f'[CHARACTER] {name}', cli.Colors.BOLD)}")
    cli.print_out(f"  {cli.c('═' * 60, cli.Colors.CYAN)}\n")

    # Known world facts
    world_items = knows.get('world', [])
    if isinstance(world_items, dict) and 'summary' in world_items:
        world_items = world_items['summary']
        cli.print_out(f"  {cli.c('📌 已知世界 (摘要):', cli.Colors.BLUE)}")
    else:
        cli.print_out(f"  {cli.c('📌 已知世界:', cli.Colors.BLUE)}")
    if world_items:
        for item in world_items:
            cli.print_out(f"    - {item}")
    else:
        cli.print_out(f"    (无)")
    cli.print_out()

    # Known characters
    char_items = knows.get('characters', [])
    if isinstance(char_items, dict) and 'summary' in char_items:
        char_items = char_items['summary']
        cli.print_out(f"  {cli.c('👥 已知人物 (摘要):', cli.Colors.BLUE)}")
    else:
        cli.print_out(f"  {cli.c('👥 已知人物:', cli.Colors.BLUE)}")
    if char_items:
        for item in char_items:
            cli.print_out(f"    - {item}")
    else:
        cli.print_out(f"    (无)")
    cli.print_out()

    # Known events
    event_items = knows.get('events', [])
    was_summarized = False
    if isinstance(event_items, dict) and 'summary' in event_items:
        was_summarized = True
        event_items = event_items['summary']
        cli.print_out(f"  {cli.c('📝 已知事件 (摘要):', cli.Colors.BLUE)}")
    else:
        cli.print_out(f"  {cli.c('📝 已知事件:', cli.Colors.BLUE)}")
    if event_items:
        for i, item in enumerate(event_items, 1):
            cli.print_out(f"    {i}. {item}")
    else:
        cli.print_out(f"    (无)")
    if was_summarized and isinstance(knows.get('events'), dict):
        cli.print_out(f"    ... (共 {knows['events'].get('full_count', 0)} 条)")
    cli.print_out()

    # Unaware
    unaware = data.get('unaware', [])
    cli.print_out(f"  {cli.c('❌ 绝对不能写的内容 (角色不知道):', cli.Colors.RED)}")
    if unaware:
        for item in unaware:
            cli.print_out(f"    - {item}")
    else:
        cli.print_out(f"    (无)")
    cli.print_out()

    # Relationships
    relationships = data.get('relationships', [])
    cli.print_out(f"  {cli.c('💬 关系备注:', cli.Colors.GREEN)}")
    if relationships:
        for item in relationships:
            cli.print_out(f"    - {item}")
    else:
        cli.print_out(f"    (无)")
    cli.print_out()

    # POV restrictions
    pov_restrictions = data.get('pov_restrictions', [])
    cli.print_out(f"  {cli.c('🚫 POV 限制:', cli.Colors.YELLOW)}")
    if pov_restrictions:
        for item in pov_restrictions:
            cli.print_out(f"    - {item}")
    else:
        cli.print_out(f"    (无)")
    cli.print_out()


def update_character(info_dir: Path, name: str,
                     event: Optional[str] = None,
                     world: Optional[str] = None,
                     character: Optional[str] = None,
                     unaware: Optional[str] = None,
                     relationship: Optional[str] = None,
                     pov: Optional[str] = None):
    """Update character knowledge"""
    knowledge = ck.update_character_knowledge_with_summary(
        info_dir,
        name,
        event=event,
        world_knowledge=world,
        character_knowledge=character,
        unaware=unaware,
        relationship=relationship,
        pov_restriction=pov,
    )

    cli.print_out(f"\n  {cli.c('✓ Updated character:', cli.Colors.GREEN)} {name}")

    # Show what was added
    added = []
    if event:
        added.append(f"事件: {event}")
    if world:
        added.append(f"世界事实: {world}")
    if character:
        added.append(f"人物: {character}")
    if unaware:
        added.append(f"未知信息: {unaware}")
    if relationship:
        added.append(f"关系: {relationship}")
    if pov:
        added.append(f"POV限制: {pov}")

    if added:
        cli.print_out(f"  新增:")
        for item in added:
            cli.print_out(f"    - {item}")

    if cli.is_json_mode():
        cli.output_json({
            'success': True,
            'character': name,
            'knowledge': knowledge[name]
        })


def check_character(info_dir: Path, name: str, chapter: Optional[int] = None):
    """Check POV consistency"""
    knowledge = ck.load_character_knowledge(info_dir)

    if name not in knowledge:
        cli.error_message(f"Character '{name}' not found")
        return

    # Simple check - just verify structure
    data = knowledge[name]
    issues = []

    # Check that 'knows' structure exists
    if 'knows' not in data:
        issues.append("Missing 'knows' structure")
    else:
        knows = data['knows']
        for key in ['world', 'characters', 'events']:
            if key not in knows:
                issues.append(f"Missing '{key}' in 'knows'")

    cli.print_out(f"\n  {cli.c('═' * 60, cli.Colors.CYAN)}")
    cli.print_out(f"  {cli.c(f'[CHECK] {name}', cli.Colors.BOLD)}")
    cli.print_out(f"  {cli.c('═' * 60, cli.Colors.CYAN)}\n")

    if chapter:
        cli.print_out(f"  检查章节: {chapter}\n")

    if not issues:
        cli.print_out(f"  {cli.c('✓ POV structure looks good', cli.Colors.GREEN)}\n")
    else:
        cli.print_out(f"  {cli.c('⚠ Found issues:', cli.Colors.YELLOW)}")
        for issue in issues:
            cli.print_out(f"    - {issue}")
        cli.print_out()

    if cli.is_json_mode():
        cli.output_json({
            'success': len(issues) == 0,
            'character': name,
            'chapter': chapter,
            'issues': issues
        })


def export_character(info_dir: Path, name: str):
    """Export knowledge for prompt inclusion"""
    knowledge_for_prompt = ck.get_character_knowledge_for_prompt(info_dir, name)

    if not knowledge_for_prompt:
        cli.error_message(f"Character '{name}' not found")
        return

    # Generate prompt section
    output = []
    output.append("---")
    output.append(f"## 📌 POV 角色认知约束 (必须遵守!)")
    output.append(f"**当前 POV: {name}**")
    output.append("")

    knows = knowledge_for_prompt.get('knows', {})

    # Known events
    events = knows.get('events', [])
    if events:
        output.append("### 已知事件:")
        for event in events:
            output.append(f"- {event}")
        output.append("")

    # Known characters
    characters = knows.get('characters', [])
    if characters:
        output.append("### 已知人物:")
        for char in characters:
            output.append(f"- {char}")
        output.append("")

    # Known world
    world = knows.get('world', [])
    if world:
        output.append("### 已知事实:")
        for fact in world:
            output.append(f"- {fact}")
        output.append("")

    # Unaware
    unaware = knowledge_for_prompt.get('unaware', [])
    if unaware:
        output.append("### 绝对不能写的内容 (角色不知道):")
        for item in unaware:
            output.append(f"- {item}")
        output.append("")

    output.append("---")

    # Print the export
    for line in output:
        cli.print_out(line)

    if cli.is_json_mode():
        cli.output_json({
            'success': True,
            'character': name,
            'export': '\n'.join(output),
            'knowledge': knowledge_for_prompt
        })


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    subcommand = sys.argv[1].lower()

    # Handle help first
    if subcommand in ('help', '--help', '-h'):
        show_help()
        return

    # For commands that need a name parameter, extract it first
    char_name = None
    remaining_args = sys.argv[2:]

    needs_name = ['view', 'update', 'check', 'export']
    if subcommand in needs_name:
        if not remaining_args or remaining_args[0].startswith('-'):
            show_help()
            return
        # Collect name (may contain spaces)
        name_parts = []
        i = 0
        while i < len(remaining_args) and not remaining_args[i].startswith('-'):
            name_parts.append(remaining_args[i])
            i += 1
        char_name = ' '.join(name_parts)
        remaining_args = remaining_args[i:]

    # Insert dummy program name for argparse
    sys.argv = ['story-character'] + remaining_args

    # Find project root
    root = paths.find_project_root()
    if not root:
        cli.error_message("Not in a story project (no story.yaml found)")
        return

    # Load paths
    project_paths = paths.load_project_paths(root)
    info_dir = project_paths['info']

    if subcommand == 'list':
        list_characters(info_dir)

    elif subcommand == 'view':
        parser = argparse.ArgumentParser(description='View character knowledge')
        args, _ = cli.parse_cli_args(parser)
        view_character(info_dir, char_name)

    elif subcommand == 'update':
        parser = argparse.ArgumentParser(description='Update character knowledge')
        parser.add_argument('--event', help='Add known event')
        parser.add_argument('--world', help='Add known world fact')
        parser.add_argument('--character', dest='known_char', help='Add known character')
        parser.add_argument('--unaware', help='Add something character is unaware of')
        parser.add_argument('--relationship', help='Add relationship note')
        parser.add_argument('--pov', help='Add POV restriction')
        args, _ = cli.parse_cli_args(parser)
        update_character(
            info_dir,
            char_name,
            event=args.event,
            world=args.world,
            character=args.known_char,
            unaware=args.unaware,
            relationship=args.relationship,
            pov=args.pov,
        )

    elif subcommand == 'check':
        parser = argparse.ArgumentParser(description='Check POV consistency')
        parser.add_argument('--chapter', type=int, help='Chapter number to check')
        args, _ = cli.parse_cli_args(parser)
        check_character(info_dir, char_name, args.chapter)

    elif subcommand == 'export':
        parser = argparse.ArgumentParser(description='Export knowledge for prompt')
        args, _ = cli.parse_cli_args(parser)
        export_character(info_dir, char_name)

    else:
        cli.print_out(f"  Unknown subcommand: {subcommand}")
        show_help()


if __name__ == '__main__':
    main()
