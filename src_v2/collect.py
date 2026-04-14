#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:collect - Collect information via interactive Q&A or non-interactive args

Supports both interactive and non-interactive modes:
- Interactive: `story collect core` (asks questions)
- Non-interactive: `story collect core --non-interactive --args '{"story_concept":"..."}'`
- JSON output: `story collect core --json --non-interactive --args '{"story_concept":"..."}'`
"""

import sys
import argparse
from pathlib import Path
from .paths import find_project_root, load_config, load_project_paths
from .templates import get_collect_questions, ensure_default_templates
from . import cli


def save_answers(info_dir: Path, template_name: str, answers: dict) -> Path:
    """
    Save collected answers to a file.

    Args:
        info_dir: Path to INFO directory
        template_name: Template name (used for filename)
        answers: Dictionary of answers

    Returns:
        Path to saved file
    """
    import json
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False

    filename = f'01-{template_name}.yaml' if template_name == 'core' else f'{template_name}.yaml'
    output_path = info_dir / filename

    data = {
        'collected_at': __import__('datetime').datetime.now().isoformat(),
        'answers': answers
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        if use_yaml:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return output_path


def show_collect_help():
    print("""
Usage: story collect <target> [options]

Targets:
  core          Collect core story info
  protagonist   Create protagonist
  mainline      Collect story mainline
  volume <num>  Collect volume outline info

Options:
  --json               Output JSON format for AI consumption
  --non-interactive    Non-interactive mode (use --args)
  --args JSON          JSON string with answers

Examples:
  story collect core
  story collect protagonist
  story collect volume 1
  story collect core --non-interactive --args '{"story_concept":"...","core_theme":"..."}'
  story collect core --json --non-interactive --args '{"story_concept":"..."}'
""")


def main():
    if len(sys.argv) < 2:
        show_collect_help()
        return

    # Check for help
    if sys.argv[1] in ('help', '--help', '-h'):
        show_collect_help()
        return

    target = sys.argv[1].lower()

    # Parse remaining args for collect
    remaining_args = sys.argv[2:]
    volume_num = None

    if target == 'volume':
        if len(remaining_args) < 1 or remaining_args[0].startswith('-'):
            show_collect_help()
            return
        volume_num = remaining_args[0]
        remaining_args = remaining_args[1:]

    # Insert a dummy program name for argparse
    sys.argv = ['story-collect'] + remaining_args

    # Parse CLI arguments
    parser = argparse.ArgumentParser(add_help=False)
    args, collect_args = cli.parse_cli_args(parser)

    # Find project root
    root = find_project_root()
    if not root:
        cli.error_message("Not in a novel project (no story.yaml/story.json). Run 'story init' first.")

    config = load_config(root)
    paths = load_project_paths(root)

    # Ensure templates exist
    ensure_default_templates(paths['templates'])

    # Map targets to template names
    target_map = {
        'core': 'core',
        'protagonist': 'characters',
        'mainline': 'core',
        'volume': 'volume',
    }

    if target not in target_map and target != 'volume':
        cli.error_message(f"Unknown target: {target}")

    template_name = target_map.get(target, target)

    # Get questions
    questions = get_collect_questions(paths['templates'], template_name)
    if not questions:
        cli.warn_message(f"No questions found for template: {template_name}")
        questions = []

    # Collect answers
    answers = cli.collect_questions(questions, template_name)

    if not answers:
        if cli.is_json_mode():
            cli.output_json({'success': False, 'error': 'No answers collected'})
        return

    # Handle volume target with number
    if target == 'volume' and volume_num:
        out_path = save_answers(paths['info'], f'volume-{volume_num}', answers)
    else:
        out_path = save_answers(paths['info'], template_name, answers)

    cli.collect_success_message(out_path, answers)


if __name__ == '__main__':
    main()
