#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:style - 风格档案管理

功能：
1. 查看当前风格档案
2. 管理 STYLE/prompts/ 下的 prompt 片段
3. 手动编辑/重置风格
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from .paths import find_project_root, load_project_paths


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"



def ensure_dirs(root, paths=None):
    """确保风格目录存在"""
    if paths is None:
        paths = load_project_paths(root)
    dirs = [paths['style'], paths['style_prompts'], paths['style_history']]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def load_profile(root, paths=None) -> dict:
    """加载风格档案"""
    if paths is None:
        paths = load_project_paths(root)
    profile_path = paths['style'] / 'profile.json'
    if profile_path.exists():
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'created': None, 'chapters_trained': 0, 'avg_modification_rate': 0.0, 'target_modification_rate': 0.15}


def show_profile(profile: dict):
    """显示风格档案"""
    rate = profile.get('avg_modification_rate', 0) * 100
    target = profile.get('target_modification_rate', 0.15) * 100
    print(f"""
{c('='*60, Colors.BOLD)}
         风格档案
{c('='*60, Colors.BOLD)}

  创建时间：{profile.get('created', 'N/A')}
  学习章节：{profile.get('chapters_trained', 0)} 章
  平均修改率：{rate:.1f}%
  目标修改率：{target:.1f}%

{c('-'*60, Colors.DIM)}
  风格档案路径：STYLE/profile.json
  Prompt 片段：STYLE/prompts/
{c('-'*60, Colors.DIM)}
""")


def show_prompts(prompts_dir: Path):
    """显示所有 prompt 片段"""
    print(f"\n{c('='*60, Colors.BOLD)}")
    print(f"         可复用的 Prompt 片段")
    print(f"{c('='*60, Colors.BOLD)}\n")

    for fname in ['vocabulary.md', 'sentence.md', 'pacing.md', 'full_guide.md']:
        path = prompts_dir / fname
        if path.exists():
            content = path.read_text(encoding='utf-8')
            print(c(f"### {fname}", Colors.CYAN))
            print(c("-" * 40, Colors.DIM))
            print(content[:500] if len(content) > 500 else content)
            if len(content) > 500:
                print(c("  ... (内容较长)", Colors.DIM))
            print()
        else:
            print(c(f"### {fname} (未生成)", Colors.YELLOW))
            print()


def show_full_guide(prompts_dir: Path):
    """显示完整风格指南"""
    full_guide_path = prompts_dir / 'full_guide.md'
    if not full_guide_path.exists():
        print(f"  {c('[ERROR] 完整风格指南不存在', Colors.RED)}")
        print(f"  请先运行：python story.py learn")
        return
    content = full_guide_path.read_text(encoding='utf-8')
    print(f"\n{c('='*60, Colors.BOLD)}")
    print(f"         完整风格指南")
    print(f"{c('='*60, Colors.BOLD)}\n")
    print(content)


def reset_style(root, force: bool = False, paths=None):
    """重置风格档案"""
    if paths is None:
        paths = load_project_paths(root)
    if not force:
        print(f"\n{c('[WARN] 即将重置所有风格数据！', Colors.RED)}")
        confirm = input("  确认删除？[y/N]: ").strip().lower()
        if confirm != 'y':
            print("  取消操作")
            return

    prompts_dir = paths['style_prompts']
    if prompts_dir.exists():
        for f in prompts_dir.iterdir():
            if f.is_file():
                f.unlink()
        print(f"  {c('[OK]', Colors.GREEN)} 已清空 STYLE/prompts/")

    profile_path = paths['style'] / 'profile.json'
    new_profile = {'created': datetime.now().isoformat(), 'chapters_trained': 0,
                   'avg_modification_rate': 0.0, 'target_modification_rate': 0.15, 'reset_at': datetime.now().isoformat()}
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(new_profile, f, ensure_ascii=False, indent=2)
    print(f"  {c('[OK]', Colors.GREEN)} 已重置 STYLE/profile.json")
    print(f"\n  风格数据已重置，运行 story:learn 重新学习")


def main():
    parser = argparse.ArgumentParser(description='风格档案管理', formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n  python story.py style --prompts\n  python story.py style --reset")
    parser.add_argument('--prompts', '-p', action='store_true', help='显示 prompt 片段')
    parser.add_argument('--full', '-f', action='store_true', help='显示完整风格指南')
    parser.add_argument('--reset', '-r', action='store_true', help='重置风格数据')
    parser.add_argument('--force', action='store_true', help='跳过确认提示（重置等操作）')

    args = parser.parse_args()
    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录', Colors.RED)}")
        sys.exit(1)

    paths = load_project_paths(root)
    ensure_dirs(root, paths=paths)
    prompts_dir = paths['style_prompts']

    if args.reset:
        reset_style(root, force=args.force, paths=paths)
    elif args.full:
        show_full_guide(prompts_dir)
    elif args.prompts:
        show_prompts(prompts_dir)
    else:
        profile = load_profile(root, paths=paths)
        show_profile(profile)
        print(c("[TIP] 使用 --prompts 查看 prompt 片段", Colors.DIM))


if __name__ == '__main__':
    main()
