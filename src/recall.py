#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:recall - 章节回顾/摘要

快速查看章节摘要，回顾前文剧情。
读取预先生成的摘要文件（由 update-specs 生成）。
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from .snapshot import read_chapter_snapshot, _strip_frontmatter


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


# ============================================================================
# 工具函数
# ============================================================================

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
    import json
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


def get_chapter_volume(chapter_num: int, chapters_per: int = 30) -> int:
    """根据章节号计算卷号"""
    return ((chapter_num - 1) // chapters_per) + 1


def parse_chapter_range(range_str: str, chapters_per: int = 30) -> Tuple[int, int]:
    """
    解析章节范围字符串。

    支持格式：
    - "5"        -> (5, 5)
    - "3-5"      -> (3, 5)
    - "3~5"      -> (3, 5)
    - "recent 3" -> 返回最近3章（需要额外参数）
    """
    range_str = range_str.strip().lower()

    # 解析 "3-5" 或 "3~5" 格式
    if '-' in range_str:
        parts = range_str.split('-')
    elif '~' in range_str:
        parts = range_str.split('~')
    else:
        # 单个数字
        try:
            num = int(range_str)
            return num, num
        except ValueError:
            return 1, 1

    if len(parts) == 2:
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())
            return start, end
        except ValueError:
            return 1, 1

    return 1, 1


def get_summary_path(root: Path, chapter_num: int, chapters_per: int = 30) -> Path:
    """获取章节摘要文件路径"""
    volume_num = get_chapter_volume(chapter_num, chapters_per)
    summary_dir = root / 'OUTLINE' / f'volume-{volume_num}' / 'summaries'
    return summary_dir / f'chapter-{chapter_num:03d}-summary.md'


def read_summary(summary_path: Path) -> Tuple[Optional[str], dict]:
    """
    读取摘要文件。

    返回：(摘要内容, 元数据字典)
    """
    if not summary_path.exists():
        return None, {}

    content = summary_path.read_text(encoding='utf-8')

    # 解析 frontmatter
    meta = {}
    lines = content.split('\n')

    if lines and lines[0].strip() == '---':
        frontmatter_lines = []
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                break
            frontmatter_lines.append(lines[i])

        # 解析 YAML 格式的 frontmatter
        for line in frontmatter_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                meta[key.strip()] = value.strip()

        # 找到内容部分
        content_start = content.find('---', 3) + 3
        while content_start < len(content) and content[content_start] == '\n':
            content_start += 1
        content = content[content_start:].strip()

    return content, meta


def get_latest_chapter(root: Path, config: dict) -> int:
    """获取当前最新章节号"""
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)

    # 从 CONTENT 目录获取
    content_dir = root / 'CONTENT'
    if content_dir.exists():
        chapters = list(content_dir.glob('**/chapter-*.md'))
        if chapters:
            nums = []
            for ch in chapters:
                match = re.search(r'chapter-(\d+)', ch.name)
                if match:
                    nums.append(int(match.group(1)))
            if nums:
                return max(nums)

    # 从 progress 获取
    progress = config.get('progress', {})
    return progress.get('current_chapter', 1)


# ============================================================================
# 显示函数
# ============================================================================

def format_recall_view(chapter_num: int, summary_content: str, meta: dict,
                       show_full: bool = False) -> str:
    """格式化回顾视图"""
    lines = []

    # 标题
    lines.append(c('=' * 60, Colors.HEADER))
    lines.append(c(f'  第{chapter_num}章 摘要', Colors.CYAN))
    lines.append(c('=' * 60, Colors.HEADER))
    lines.append('')

    # 元数据
    if meta:
        if 'word_count' in meta:
            lines.append(f"  {c('字数:', Colors.DIM)} {meta['word_count']}")
        if 'pov' in meta and meta['pov']:
            lines.append(f"  {c('POV:', Colors.DIM)} {meta['pov']}")
        if 'date' in meta:
            lines.append(f"  {c('日期:', Colors.DIM)} {meta['date']}")
        lines.append('')

    # 摘要内容
    if summary_content:
        # 如果内容太长且不显示全文，截断
        if not show_full and len(summary_content) > 1000:
            lines.append(summary_content[:1000])
            lines.append(c(f'\n  ... (还有 {len(summary_content) - 1000} 字)', Colors.DIM))
        else:
            lines.append(summary_content)
    else:
        lines.append(c('  [无摘要]', Colors.DIM))

    lines.append('')
    return '\n'.join(lines)


def show_recall_summary(chapters: List[int], root: Path, config: dict, show_full: bool = False, show_snapshot: bool = False):
    """显示多个章节的回顾摘要"""
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)

    for i, chapter_num in enumerate(chapters):
        if i > 0:
            print()

        # 快照模式：优先显示设定快照
        if show_snapshot:
            snapshot_content = read_chapter_snapshot(root, chapter_num, chapters_per)
            if snapshot_content:
                clean = _strip_frontmatter(snapshot_content)
                print(c('=' * 60, Colors.HEADER))
                print(c(f'  第{chapter_num}章 设定快照', Colors.CYAN))
                print(c('=' * 60, Colors.HEADER))
                print()
                print(clean)
            else:
                print(c(f'  [警告] 第{chapter_num}章快照不存在', Colors.YELLOW))
                print(c(f'        运行 "story:snapshot {chapter_num}" 生成快照', Colors.DIM))
            continue

        # 摘要模式（默认）
        summary_path = get_summary_path(root, chapter_num, chapters_per)

        if not summary_path.exists():
            print(c(f'  [警告] 第{chapter_num}章摘要不存在（{summary_path.name}）', Colors.YELLOW))
            print(c(f'        运行 "story:update-specs {chapter_num}" 生成摘要', Colors.DIM))
            continue

        summary_content, meta = read_summary(summary_path)
        output = format_recall_view(chapter_num, summary_content, meta, show_full)
        print(output)


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='章节回顾 - 快速查看章节摘要',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  story:recall 5              # 查看第5章摘要
  story:recall 3-5            # 查看第3到5章摘要
  story:recall --recent 3     # 查看最近3章
  story:recall 5 --full       # 显示完整摘要（不截断）
  story:recall 5 --snapshot   # 查看第5章设定快照

提示：
  摘要文件由 update-specs 命令生成。
  设定快照由 snapshot 命令生成。
        """
    )
    parser.add_argument('range', nargs='?', help='章节范围（如 5 或 3-5）')
    parser.add_argument('--recent', type=int, metavar='N',
                        help='查看最近 N 章')
    parser.add_argument('--full', '-f', action='store_true',
                        help='显示完整摘要（不截断）')
    parser.add_argument('--snapshot', '-S', action='store_true',
                        help='查看章节设定快照（而非摘要）')
    parser.add_argument('--volume', '-v', type=int,
                        help='指定卷号（默认自动计算）')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录，请先运行 story:init', Colors.RED)}")
        sys.exit(1)

    config = load_config(root)
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)

    # 确定要显示的章节范围
    if args.recent:
        # 查看最近 N 章
        latest = get_latest_chapter(root, config)
        start = max(1, latest - args.recent + 1)
        chapters = list(range(start, latest + 1))
        print(f"\n{c('📖 章节回顾（最近 {} 章）'.format(args.recent), Colors.CYAN)}")

    elif args.range:
        # 解析范围
        start, end = parse_chapter_range(args.range, chapters_per)
        if start > end:
            print(f"  {c('[ERROR] 起始章节大于结束章节', Colors.RED)}")
            sys.exit(1)
        chapters = list(range(start, end + 1))
        print(f"\n{c(f'📖 章节回顾（第{start}-{end}章）', Colors.CYAN)}")

    else:
        # 默认查看最近 3 章
        latest = get_latest_chapter(root, config)
        start = max(1, latest - 2)
        chapters = list(range(start, latest + 1))
        print(f"\n{c('📖 章节回顾（最近 3 章）', Colors.CYAN)}")

    if not chapters:
        print(f"  {c('[ERROR] 没有可显示的章节', Colors.RED)}")
        sys.exit(1)

    # 显示回顾
    show_recall_summary(chapters, root, config, args.full, args.snapshot)


if __name__ == '__main__':
    main()
