#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:migrate - Migrate old project structure to new structure

Supports both interactive and non-interactive modes:
- Interactive: `story migrate`
- Non-interactive: `story migrate --non-interactive`
- Dry run: `story migrate --dry-run`
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from .paths import (
    find_project_root, load_config, save_config,
    load_project_paths,
)
from . import cli


def detect_old_project(root: Path) -> bool:
    """Detect if this is an old-style project"""
    outline_dir = root / 'process' / 'OUTLINE'
    world_dir = root / 'process' / 'INFO' / 'world'
    return outline_dir.exists() or world_dir.exists()


def backup_old_files(root: Path, dry_run: bool = False) -> Path:
    """Backup old files to backup/ directory"""
    backup_dir = root / 'backup'
    if not dry_run:
        backup_dir.mkdir(exist_ok=True)

        # Backup OUTLINE
        outline_dir = root / 'process' / 'OUTLINE'
        if outline_dir.exists():
            shutil.copytree(outline_dir, backup_dir / 'OUTLINE')

        # Backup world
        world_dir = root / 'process' / 'INFO' / 'world'
        if world_dir.exists():
            shutil.copytree(world_dir, backup_dir / 'world')

    return backup_dir


def load_old_volume_outline(outline_dir: Path, volume_num: int) -> Optional[Dict[str, Any]]:
    """Load old-style volume outline"""
    vol_file = outline_dir / f'volume-{volume_num:03d}.yaml'
    if not vol_file.exists():
        vol_file = outline_dir / f'volume-{volume_num:03d}.json'
    if not vol_file.exists():
        return None

    with open(vol_file, 'r', encoding='utf-8') as f:
        if vol_file.suffix == '.yaml':
            try:
                import yaml
                return yaml.safe_load(f) or {}
            except ImportError:
                pass
        return json.load(f)


def load_old_world_data(world_dir: Path) -> Dict[str, Any]:
    """Load old-style world data"""
    world_data = {
        'basic': {},
        'factions': {},
        'history': {},
        'powers': {},
        'organizations': {},
        'locations': {},
    }

    # Load basic
    basic_file = world_dir / 'basic.yaml'
    if not basic_file.exists():
        basic_file = world_dir / 'basic.json'
    if basic_file.exists():
        with open(basic_file, 'r', encoding='utf-8') as f:
            if basic_file.suffix == '.yaml':
                try:
                    import yaml
                    world_data['basic'] = yaml.safe_load(f) or {}
                except ImportError:
                    pass
            else:
                world_data['basic'] = json.load(f)

    return world_data


def migrate_project(root: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Migrate an old project to new structure"""
    config = load_config(root)
    paths = load_project_paths(root)

    # Detect old project
    if not detect_old_project(root):
        return {
            'success': False,
            'message': 'Not an old-style project, no migration needed'
        }

    # Check if already migrated
    migrated_marker = root / '.migrated'
    if migrated_marker.exists():
        return {
            'success': False,
            'message': 'Project already migrated'
        }

    if not dry_run and not cli.is_json_mode():
        cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
        cli.print_out(f"  {cli.c('[MIGRATE] Migrating Project', cli.Colors.BOLD)}")
        cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")

    # Backup
    if not cli.is_json_mode():
        cli.print_out(f"  {cli.c('[1/5] Backing up old files...', cli.Colors.BOLD)}")
    backup_dir = backup_old_files(root, dry_run)

    # Load old data
    if not cli.is_json_mode():
        cli.print_out(f"  {cli.c('[2/5] Loading old data...', cli.Colors.BOLD)}")

    outline_dir = root / 'process' / 'OUTLINE'
    world_dir = root / 'process' / 'INFO' / 'world'

    # Load world data
    if world_dir.exists():
        config['world'] = load_old_world_data(world_dir)

    # Load outlines
    config['outlines'] = {'volumes': {}}
    if outline_dir.exists():
        # Scan for volume files
        for vol_file in outline_dir.glob('volume-*.yaml'):
            # Extract volume number
            pass  # TODO: implement

    # Update meta
    config['meta'] = config.get('meta', {})
    config['meta']['version'] = '3.0-simplified'
    config['meta']['migrated_from'] = '2.0-simplified'
    config['meta']['migration_date'] = datetime.now().strftime('%Y-%m-%d')

    # Save config
    if not cli.is_json_mode():
        cli.print_out(f"  {cli.c('[3/5] Saving updated story.yml...', cli.Colors.BOLD)}")
    if not dry_run:
        save_config(root, config)

    # Create marker
    if not cli.is_json_mode():
        cli.print_out(f"  {cli.c('[4/5] Creating migration marker...', cli.Colors.BOLD)}")
    if not dry_run:
        migrated_marker.write_text(datetime.now().isoformat(), encoding='utf-8')

    if not cli.is_json_mode():
        cli.print_out(f"\n  {cli.c('✓ Migration complete!', cli.Colors.GREEN)}")
        cli.print_out(f"  Backed up to: {backup_dir}")

    return {
        'success': True,
        'backup_dir': str(backup_dir) if not dry_run else None,
    }


def show_migrate_help():
    cli.print_out("""
Usage: story migrate [options]

Options:
  --dry-run          Show what would be done without making changes
  --json             Output JSON format for AI consumption
  --non-interactive  Non-interactive mode

Examples:
  story migrate
  story migrate --dry-run
  story migrate --json --non-interactive
""")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('help', '--help', '-h'):
        show_migrate_help()
        return

    # Parse arguments
    dry_run = '--dry-run' in sys.argv

    # Filter out global options
    filtered_args = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--dry-run':
            i += 1
        elif arg in ('--json', '--non-interactive'):
            filtered_args.append(arg)
            i += 1
        elif arg == '--args':
            filtered_args.append(arg)
            filtered_args.append(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    # Set up cli
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    args, _ = cli.parse_cli_args(parser)

    # Find project root
    root = find_project_root()
    if not root:
        cli.error_message("Not in a novel project (no story.yaml/story.json)")

    # Run migration
    result = migrate_project(root, dry_run=dry_run)

    if cli.is_json_mode():
        cli.output_json(result)


if __name__ == '__main__':
    main()
