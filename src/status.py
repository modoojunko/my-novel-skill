#!/usr/bin/env python3
"""
story:status - 查看项目状态

显示当前小说项目的进度统计。
使用 JSON 作为配置文件格式。
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 导入 draft 模块用于待补全统计
try:
    from . import draft
    from . import paths
    DRAFT_AVAILABLE = True
except ImportError:
    DRAFT_AVAILABLE = False

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

def find_project_root():
    """查找项目根目录"""
    cwd = Path.cwd()
    current = cwd
    for _ in range(10):
        if (current / 'story.json').exists() or (current / 'story.yml').exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None

def load_config(root):
    """加载配置"""
    config_path = root / 'story.json'
    if not config_path.exists():
        config_path = root / 'story.yml'
    
    if config_path.suffix == '.json':
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

def count_words_in_file(filepath: Path) -> int:
    """统计文件字数"""
    try:
        content = filepath.read_text(encoding='utf-8')
        lines = content.split('\n')
        word_count = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                chinese = sum(1 for char in line if '\u4e00' <= char <= '\u9fff')
                english = len([w for w in line.split() if w.strip('.,!?;:()[]{}')])
                word_count += chinese + english
        return word_count
    except:
        return 0

def get_progress(root: Path, config: dict):
    """获取进度信息"""
    stats = {
        'total_chapters': 0,
        'written_chapters': 0,
        'archived_chapters': 0,
        'total_words': 0,
        'draft_words': 0,
        'content_words': 0,
        'characters': 0,
        'world_entries': 0,
    }

    volumes = config.get('structure', {}).get('volumes', 1)
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    stats['total_chapters'] = volumes * chapters_per

    chars_dir = root / 'SPECS' / 'characters'
    if chars_dir.exists():
        stats['characters'] = len(list(chars_dir.glob('*.md')))

    world_dir = root / 'SPECS' / 'world'
    if world_dir.exists():
        stats['world_entries'] = len(list(world_dir.glob('*.md')))

    content_dir = root / 'CONTENT'
    draft_dir = root / 'CONTENT' / 'draft'
    archive_dir = root / 'ARCHIVE'

    if draft_dir.exists():
        for f in draft_dir.glob('*.md'):
            stats['draft_words'] += count_words_in_file(f)

    if content_dir.exists():
        for f in content_dir.glob('**/*.md'):
            if 'draft' not in str(f):
                stats['content_words'] += count_words_in_file(f)

    if archive_dir.exists():
        for f in archive_dir.glob('**/final.md'):
            stats['content_words'] += count_words_in_file(f)

    stats['total_words'] = stats['draft_words'] + stats['content_words']

    if content_dir.exists():
        chapters = list(content_dir.glob('**/chapter-*.md'))
        stats['written_chapters'] = len([ch for ch in chapters if 'draft' not in str(ch)])

    if archive_dir.exists():
        stats['archived_chapters'] = len(list(archive_dir.glob('**/final.md')))

    return stats

def show_status(root: Path, config: dict):
    """显示状态"""
    stats = get_progress(root, config)

    book = config.get('book', {})
    target_words = book.get('target_words', 0)
    current_words = stats['total_words']
    progress_pct = (current_words / target_words * 100) if target_words > 0 else 0

    bar = '#' * int(progress_pct / 5) + '-' * (20 - int(progress_pct / 5))

    print(f"""
================================================================================
                      {book.get('title', '未命名')}
================================================================================

[INFO] 基本信息
{'-' * 80}
  类型：{book.get('genre', '未设置')}
  目标字数：{target_words:,}
  当前字数：{current_words:,}

[STAT] 写作进度
{'-' * 80}
  完成度：{progress_pct:.1f}% [{bar}]
  章节：{stats['written_chapters']}/{stats['total_chapters']}
  已归档：{stats['archived_chapters']}

[SPEC] 设定库
{'-' * 80}
  人物：{stats['characters']} 个
  世界观：{stats['world_entries']} 条

[STORAGE] 存储
{'-' * 80}
  草稿字数：{stats['draft_words']:,}
  正文字数：{stats['content_words']:,}
  总计：{current_words:,}
""")

    # 显示待补全统计
    if DRAFT_AVAILABLE:
        print(f"[DRAFT] 待补全")
        print('-' * 80)
        try:
            proj_paths = paths.load_project_paths(root)
            pending = draft.get_all_pending_files(root, proj_paths)
            if pending:
                for path, file_type in pending:
                    type_label = {
                        'character': '角色',
                        'meta': '总纲',
                        'world': '世界观'
                    }.get(file_type, file_type)
                    print(f"  [{type_label}] {path.name}")
                print(f"  共 {len(pending)} 个文件待补全")
            else:
                print(f"  {c('OK', Colors.GREEN)} 没有待补全的文件")
        except Exception as e:
            print(f"  {c('无法加载待补全列表', Colors.YELLOW)}")
        print()

    print(f"[RECENT] 最近活动")
    print('-' * 80)

    recent_files = []
    for ext in ['*.md', '*.json', '*.yml']:
        recent_files.extend(root.glob(f'**/{ext}'))

    recent_files = sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]

    if recent_files:
        for f in recent_files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            rel_path = f.relative_to(root)
            print(f"  {mtime.strftime('%Y-%m-%d %H:%M')}  {rel_path}")
    else:
        print("  无最近活动")

    print()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='查看项目状态')
    parser.add_argument('path', nargs='?', default='.', help='项目路径')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()

    if args.path == '.':
        root = find_project_root()
    else:
        root = Path(args.path)

    if not root or not ((root / 'story.json').exists() or (root / 'story.yml').exists()):
        print(f"  {c('[ERROR] 未找到项目目录', Colors.RED)}")
        sys.exit(1)

    config_path = root / 'story.json'
    if not config_path.exists():
        config_path = root / 'story.yml'
    
    if config_path.suffix == '.json':
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

    if args.json:
        stats = get_progress(root, config)
        print(json.dumps(stats, indent=2))
    else:
        show_status(root, config)

if __name__ == '__main__':
    main()
