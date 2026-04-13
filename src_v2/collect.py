#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:collect - Collect information via interactive Q&A
"""

import sys
from pathlib import Path
from .paths import find_project_root, load_config, load_project_paths
from .templates import get_collect_questions, ensure_default_templates


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def input_with_default(prompt: str, default: str = "") -> str:
    """Get input with default value"""
    user_input = input(f"  {prompt} [{default}]: ").strip()
    return user_input if user_input else default


def collect_questions(templates_dir: Path, template_name: str) -> dict:
    """
    Interactive collection using a template.

    Args:
        templates_dir: Path to templates directory
        template_name: Name of collect template to use

    Returns:
        Dictionary of answers
    """
    questions = get_collect_questions(templates_dir, template_name)
    if not questions:
        print(f"  {c('Warning: No questions found for template', Colors.YELLOW)} {template_name}")
        return {}

    answers = {}
    print(f"\n{c('═' * 60, Colors.CYAN)}")
    print(f"  {c(f'[COLLECT] {template_name.capitalize()} Info', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.CYAN)}\n")

    for q in questions:
        key = q.get('key', '')
        question = q.get('question', '')
        if key and question:
            answer = input_with_default(question, q.get('default', ''))
            answers[key] = answer

    print(f"\n  {c('✓ Collected answers:', Colors.GREEN)}")
    for key, value in answers.items():
        print(f"    {key}: {value}")

    return answers


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
Usage: story collect <target>

Targets:
  core          Collect core story info
  protagonist   Create protagonist
  mainline      Collect story mainline
  volume <num>  Collect volume outline info

Examples:
  story collect core
  story collect protagonist
  story collect volume 1
""")


def main():
    if len(sys.argv) < 2:
        show_collect_help()
        return

    target = sys.argv[1].lower()

    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml/story.json)")
        print("  Run 'story init' first")
        return

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
        print(f"  Unknown target: {target}")
        show_collect_help()
        return

    template_name = target_map.get(target, target)

    # Handle volume target with number
    if target == 'volume':
        if len(sys.argv) < 3:
            print("  Usage: story collect volume <number>")
            return
        volume_num = sys.argv[2]
        answers = collect_questions(paths['templates'], template_name)
        if answers:
            out_path = save_answers(paths['info'], f'volume-{volume_num}', answers)
            print(f"\n  {c('✓ Saved to:', Colors.GREEN)} {out_path}")
    else:
        answers = collect_questions(paths['templates'], template_name)
        if answers:
            out_path = save_answers(paths['info'], template_name, answers)
            print(f"\n  {c('✓ Saved to:', Colors.GREEN)} {out_path}")


if __name__ == '__main__':
    main()
