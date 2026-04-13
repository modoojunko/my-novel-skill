#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli - Unified CLI utilities for both interactive and non-interactive modes

This module provides:
- Color output (disabled in JSON mode)
- Input handling (interactive) or argument parsing (non-interactive)
- JSON output mode for AI consumption
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Tuple


# Global state
_json_mode = False
_non_interactive = False
_args = {}
_collected_output = []


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
    """Colorize text (disabled in JSON mode)"""
    if _json_mode or not sys.stdout.isatty():
        return text
    return f"{color}{text}{Colors.ENDC}"


def print_out(text: str = "", end: str = "\n"):
    """Print output (collected in JSON mode)"""
    if _json_mode:
        _collected_output.append(text)
    else:
        print(text, end=end)


def output_json(data: Dict[str, Any]):
    """Output final JSON data"""
    if _collected_output:
        data['output'] = _collected_output
    print(json.dumps(data, ensure_ascii=False, indent=2))


def is_interactive() -> bool:
    """Check if running in interactive mode"""
    return not _non_interactive


def is_json_mode() -> bool:
    """Check if running in JSON mode"""
    return _json_mode


def get_args() -> Dict[str, Any]:
    """Get non-interactive arguments"""
    return _args


def parse_cli_args(parser: argparse.ArgumentParser,
                   non_interactive_params: List[str] = None) -> Tuple[argparse.Namespace, Dict[str, Any]]:
    """
    Parse CLI arguments with common options.

    Args:
        parser: The ArgumentParser to add common options to
        non_interactive_params: List of parameter names expected in --args JSON

    Returns:
        (parsed_args, non_interactive_args_dict)
    """
    parser.add_argument('--json', action='store_true',
                        help='Output JSON format for AI consumption')
    parser.add_argument('--non-interactive', action='store_true',
                        help='Non-interactive mode (use --args)')
    parser.add_argument('--args', type=str, default='{}',
                        help='JSON string with arguments for non-interactive mode')

    args = parser.parse_args()

    # Set global state
    global _json_mode, _non_interactive, _args
    _json_mode = args.json
    _non_interactive = args.non_interactive

    # Parse non-interactive args
    try:
        _args = json.loads(args.args) if args.args else {}
    except json.JSONDecodeError:
        _args = {}

    return args, _args


def input_with_default(prompt: str, default: str = "",
                       arg_key: str = None) -> str:
    """
    Get input with default value.
    In non-interactive mode, uses arg_key from --args.
    """
    if _non_interactive:
        if arg_key and arg_key in _args:
            return str(_args[arg_key])
        return default

    user_input = input(f"  {prompt} [{default}]: ").strip()
    return user_input if user_input else default


def select_option(prompt: str, options: List[str],
                  arg_key: str = None) -> int:
    """
    Show selection menu (interactive) or get from args (non-interactive).

    Args:
        prompt: The prompt to show
        options: List of options (indexes 1-based)
        arg_key: Key in --args for non-interactive mode

    Returns:
        Selected index (1-based)
    """
    if _non_interactive:
        if arg_key and arg_key in _args:
            val = _args[arg_key]
            if isinstance(val, int) and 1 <= val <= len(options):
                return val
            if isinstance(val, str):
                # Try to match by name
                for i, opt in enumerate(options, 1):
                    if val.lower() in opt.lower():
                        return i
        return 1

    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        try:
            choice = int(input(f"  Select [1-{len(options)}]: ").strip())
            if 1 <= choice <= len(options):
                return choice
        except ValueError:
            pass
        print(f"  {c('Invalid selection', Colors.RED)}")


def collect_questions_interactive(questions: List[Dict[str, Any]],
                                  template_name: str) -> Dict[str, str]:
    """Interactive question collection"""
    answers = {}
    print_out(f"\n{c('═' * 60, Colors.CYAN)}")
    print_out(f"  {c(f'[COLLECT] {template_name.capitalize()} Info', Colors.BOLD)}")
    print_out(f"{c('═' * 60, Colors.CYAN)}\n")

    for q in questions:
        key = q.get('key', '')
        question = q.get('question', '')
        if key and question:
            answer = input_with_default(question, q.get('default', ''), arg_key=key)
            answers[key] = answer

    print_out(f"\n  {c('✓ Collected answers:', Colors.GREEN)}")
    for key, value in answers.items():
        print_out(f"    {key}: {value}")

    return answers


def collect_questions_non_interactive(questions: List[Dict[str, Any]]) -> Dict[str, str]:
    """Non-interactive question collection from --args"""
    answers = {}
    for q in questions:
        key = q.get('key', '')
        if key:
            if key in _args:
                answers[key] = str(_args[key])
            else:
                answers[key] = q.get('default', '')
    return answers


def collect_questions(questions: List[Dict[str, Any]],
                      template_name: str) -> Dict[str, str]:
    """
    Collect questions using appropriate mode.

    Args:
        questions: List of question dicts with 'key', 'question', 'default'
        template_name: Name of template for display

    Returns:
        Dictionary of answers
    """
    if _non_interactive:
        return collect_questions_non_interactive(questions)
    else:
        return collect_questions_interactive(questions, template_name)


def confirm_action(prompt: str, default: bool = False,
                   arg_key: str = None) -> bool:
    """
    Ask for confirmation (interactive) or get from args (non-interactive).
    """
    if _non_interactive:
        if arg_key and arg_key in _args:
            val = _args[arg_key]
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ('y', 'yes', 'true', '1')
        return default

    default_str = 'Y/n' if default else 'y/N'
    response = input(f"  {prompt} [{default_str}]: ").strip().lower()
    if not response:
        return default
    return response in ('y', 'yes')


def init_success_message(root: Path, next_steps: List[str]):
    """Show success message or output JSON"""
    if _json_mode:
        output_json({
            'success': True,
            'project_root': str(root),
            'next_steps': next_steps
        })
    else:
        print_out(f"\n  {c('✓ Success!', Colors.GREEN)}")
        print_out(f"  Project initialized at: {root}")
        print_out(f"\n  Next steps:")
        for i, step in enumerate(next_steps, 1):
            print_out(f"    {i}. {step}")


def collect_success_message(out_path: Path, answers: Dict[str, Any]):
    """Show collect success or output JSON"""
    if _json_mode:
        output_json({
            'success': True,
            'output_path': str(out_path),
            'answers': answers
        })
    else:
        print_out(f"\n  {c('✓ Saved to:', Colors.GREEN)} {out_path}")


def error_message(message: str, exit_code: int = 1):
    """Show error message or output JSON, then exit"""
    if _json_mode:
        output_json({
            'success': False,
            'error': message
        })
    else:
        print_out(f"  {c('Error: ' + message, Colors.RED)}")
    sys.exit(exit_code)


def warn_message(message: str):
    """Show warning message"""
    if _json_mode:
        _collected_output.append(f"Warning: {message}")
    else:
        print_out(f"  {c('Warning: ' + message, Colors.YELLOW)}")
