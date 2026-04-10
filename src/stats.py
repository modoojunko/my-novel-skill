#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:stats - 学习进度统计 + 写作字数统计

功能：
1. 查看学习进度（AI 写作风格学习）
2. 统计实际写作字数
3. 展示修改率趋势
4. 导出统计报告
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


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
# 工具函数（从 paths.py 导入）
# ============================================================================

from .paths import find_project_root, load_config


def count_chinese_chars(text: str) -> int:
    """统计中文字符数（不含标点、空格）"""
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            count += 1
    return count


def extract_content_text(content: str) -> str:
    """从 Markdown 内容中提取正文（去除 frontmatter、标题、链接等）"""
    lines = content.split('\n')
    result_lines = []
    in_frontmatter = False

    for line in lines:
        # 跳过 frontmatter
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        # 跳过 YAML frontmatter
        if ':' in line and not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
            # 检查是否是 frontmatter 字段（简短的一行）
            stripped = line.strip()
            if stripped and not stripped.startswith('[') and ':' in stripped:
                key = stripped.split(':', 1)[0].strip()
                if len(key) < 20 and not any(c in key for c in '{}[]'):
                    continue
        # 跳过标题
        if line.startswith('#'):
            continue
        # 跳过链接语法
        if line.strip().startswith('[') and '](' in line:
            continue
        # 跳过纯标记行
        stripped = line.strip()
        if not stripped or stripped.startswith('---') or stripped.startswith('***'):
            continue
        result_lines.append(line)

    return '\n'.join(result_lines)


def scan_content_words(root) -> dict:
    """扫描 CONTENT 目录，统计实际写作字数"""
    content_dir = root / 'CONTENT'
    if not content_dir.exists():
        return {'total': 0, 'volumes': {}, 'chapters': {}}

    result = {
        'total': 0,
        'volumes': {},
        'chapters': {},
        'draft': 0,
        'archived': 0
    }

    # 扫描卷目录
    for vol_dir in sorted(content_dir.iterdir()):
        if not vol_dir.is_dir() or not vol_dir.name.startswith('volume-'):
            continue

        vol_name = vol_dir.name
        vol_num = int(vol_name.replace('volume-', ''))
        vol_total = 0
        vol_chapters = {}

        # 扫描章节文件
        for chapter_file in sorted(vol_dir.glob('chapter-*.md')):
            # 跳过草稿文件
            if '.draft' in chapter_file.name or '.ai-draft' in chapter_file.name:
                continue

            chapter_num = int(chapter_file.stem.replace('chapter-', ''))
            content = chapter_file.read_text(encoding='utf-8')
            text = extract_content_text(content)
            word_count = count_chinese_chars(text)

            vol_chapters[chapter_num] = {
                'words': word_count,
                'file': chapter_file.name,
                'complete': is_chapter_complete(content)
            }
            vol_total += word_count
            result['total'] += word_count

        # 统计草稿字数
        for draft_file in vol_dir.glob('*.ai-draft.md'):
            draft_content = draft_file.read_text(encoding='utf-8')
            draft_words = count_chinese_chars(extract_content_text(draft_content))
            result['draft'] += draft_words

        result['volumes'][vol_num] = {
            'name': vol_name,
            'words': vol_total,
            'chapters': vol_chapters,
            'chapter_count': len(vol_chapters)
        }

    return result


def is_chapter_complete(content: str) -> bool:
    """判断章节是否已完成（正文超过500字）"""
    text = extract_content_text(content)
    word_count = count_chinese_chars(text)
    return word_count >= 500


def get_target_words(config: dict) -> dict:
    """获取目标字数"""
    target = config.get('target_words', 300000)
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    total_chapters = config.get('structure', {}).get('total_chapters', 100)

    # 计算每章目标字数
    per_chapter = target // total_chapters if total_chapters > 0 else 3000

    return {
        'total': target,
        'per_chapter': per_chapter,
        'chapters_per_volume': chapters_per,
        'total_chapters': total_chapters
    }


def load_profile(root) -> dict:
    """加载风格档案"""
    profile_path = root / 'STYLE' / 'profile.json'
    if profile_path.exists():
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_all_history(root) -> list:
    """加载所有审核历史"""
    history_base = root / 'STYLE' / 'history'
    if not history_base.exists():
        return []

    chapters_data = []
    for chapter_dir in sorted(history_base.iterdir()):
        if not chapter_dir.is_dir():
            continue
        chapter_num_str = chapter_dir.name.replace('chapter-', '')
        if not chapter_num_str.isdigit():
            continue
        analysis_path = chapter_dir / 'analysis.json'
        if not analysis_path.exists():
            continue
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        chapters_data.append({'chapter': int(chapter_num_str), 'analysis': analysis})
    return chapters_data


def calculate_learning_progress(chapters_data: list, profile: dict) -> dict:
    """计算学习进度"""
    if not chapters_data:
        return {
            'chapters_count': 0,
            'avg_rate': 0.0,
            'trend': [],
            'progress_percent': 0
        }

    rates = [c['analysis']['modification_rate'] for c in chapters_data]
    avg_rate = sum(rates) / len(rates) if rates else 0
    target_rate = profile.get('target_modification_rate', 0.15)

    # 进度百分比（基于修改率下降）
    initial_rate = 0.50
    if rates:
        first_rate = rates[0]
        progress = max(0, min(100, (initial_rate - avg_rate) / (initial_rate - target_rate) * 100))
    else:
        progress = 0

    return {
        'chapters_count': len(chapters_data),
        'avg_rate': avg_rate,
        'target_rate': target_rate,
        'trend': rates,
        'progress_percent': progress,
        'first_rate': rates[0] if rates else 0,
        'last_rate': rates[-1] if rates else 0
    }


def show_progress_bar(percent: float, width: int = 30) -> str:
    """显示进度条"""
    filled = int(width * percent / 100)
    empty = width - filled
    bar = '█' * filled + '░' * empty
    return f"[{bar}] {percent:.1f}%"


def format_number(n: int) -> str:
    """格式化数字为千分位"""
    return f"{n:,}"


def show_words_stats(root, config, content_stats, target_info):
    """显示字数统计"""
    total_words = content_stats['total']
    target_words = target_info['total']
    draft_words = content_stats.get('draft', 0)

    # 计算完成百分比
    if target_words > 0:
        complete_percent = min(100, total_words / target_words * 100)
    else:
        complete_percent = 0

    print(f"\n{c('='*65, Colors.BOLD)}")
    print(f"{c(' '*15)}写作字数统计", Colors.BOLD)
    print(f"{c('='*65, Colors.BOLD)}\n")

    # 总览
    print(f"  {c('已完成字数：', Colors.CYAN)}{c(format_number(total_words), Colors.GREEN)} 字")
    print(f"  {c('目标字数：', Colors.CYAN)}{format_number(target_words)} 字")
    print(f"  {c('草稿字数：', Colors.CYAN)}{format_number(draft_words)} 字（未完成）")
    print()

    # 总进度条
    print(f"  {c('总体进度：', Colors.CYAN)}{show_progress_bar(complete_percent)}")
    print(f"  {c('  差距：', Colors.DIM)}{format_number(target_words - total_words)} 字")
    print()

    # 章节统计
    all_chapters = []
    for vol_num, vol_data in sorted(content_stats['volumes'].items()):
        for ch_num, ch_data in sorted(vol_data['chapters'].items()):
            all_chapters.append((vol_num, ch_num, ch_data))

    if all_chapters:
        print(f"  {c('章节字数：', Colors.CYAN)}")
        print(f"  {c('-'*50, Colors.DIM)}")

        # 按卷分组显示
        current_vol = None
        for vol_num, ch_num, ch_data in all_chapters:
            if vol_num != current_vol:
                if current_vol is not None:
                    print()
                vol_words = content_stats['volumes'][vol_num]['words']
                vol_count = content_stats['volumes'][vol_num]['chapter_count']
                print(f"  {c(f'卷{vol_num}', Colors.YELLOW)} ({vol_count}章, {format_number(vol_words)}字)")
                current_vol = vol_num

            # 每章进度条
            ch_words = ch_data['words']
            target_ch = target_info['per_chapter']
            ch_percent = min(100, ch_words / target_ch * 100)
            status_icon = c('✓', Colors.GREEN) if ch_data['complete'] else c('○', Colors.DIM)
            bar_width = 15
            filled = int(bar_width * ch_percent / 100)
            bar = '█' * filled + '░' * (bar_width - filled)
            print(f"    {status_icon} 第{ch_num:2d}章 [{bar}] {format_number(ch_words)}字")

        print()

    # 写作效率分析
    if all_chapters:
        avg_words = total_words // len(all_chapters) if all_chapters else 0
        print(f"  {c('写作效率：', Colors.CYAN)}")
        print(f"  {c('-'*50, Colors.DIM)}")
        print(f"  平均每章：{format_number(avg_words)} 字")
        print(f"  目标每章：{format_number(target_info['per_chapter'])} 字")
        if avg_words > 0:
            efficiency = avg_words / target_info['per_chapter'] * 100
            eff_color = Colors.GREEN if 80 <= efficiency <= 120 else Colors.YELLOW if efficiency >= 50 else Colors.RED
            print(f"  效率比：{c(f'{efficiency:.0f}%', eff_color)}")
        print()


def show_learning_stats(root, profile, chapters_data, progress):
    """显示学习进度"""
    print(f"\n{c('='*65, Colors.BOLD)}")
    print(f"{c(' '*15)}AI 写作学习进度", Colors.BOLD)
    print(f"{c('='*65, Colors.BOLD)}\n")

    # 基本信息
    print(f"  {c('已学习章节：', Colors.CYAN)}{progress['chapters_count']} 章")
    print(f"  {c('当前修改率：', Colors.CYAN)}{progress['avg_rate']*100:.1f}%")
    print(f"  {c('目标修改率：', Colors.CYAN)}{progress['target_rate']*100:.1f}%")
    print()

    # 进度条
    print(f"  {c('学习进度：', Colors.CYAN)}{show_progress_bar(progress['progress_percent'])}")
    print()

    # 修改率趋势
    if progress['trend']:
        print(f"  {c('修改率趋势：', Colors.CYAN)}")
        print(f"  {c('-'*50, Colors.DIM)}")

        for i, rate in enumerate(progress['trend']):
            chapter = chapters_data[i]['chapter']
            bar_len = int(rate * 50)
            bar = '█' * bar_len + '░' * (50 - bar_len)
            rate_color = Colors.GREEN if rate < 0.2 else Colors.YELLOW if rate < 0.4 else Colors.RED
            print(f"  第{chapter:2d}章 [{bar}] {rate*100:5.1f}% {c('★' if rate < 0.2 else '☆', rate_color)}")

        print()

    # 最近学习
    if chapters_data:
        print(f"  {c('最近学习：', Colors.CYAN)}")
        print(f"  {c('-'*50, Colors.DIM)}")
        recent = chapters_data[-3:] if len(chapters_data) > 3 else chapters_data
        for item in reversed(recent):
            chapter = item['chapter']
            rate = item['analysis']['modification_rate'] * 100
            analyzed_at = item['analysis'].get('analyzed_at', 'unknown')[:10]
            rate_color = Colors.GREEN if rate < 20 else Colors.YELLOW if rate < 40 else Colors.RED
            print(f"  第{chapter:2d}章 - 修改率 {c(f'{rate:.1f}%', rate_color)} - {analyzed_at}")
        print()

    # 建议
    print(f"  {c('建议：', Colors.CYAN)}")
    print(f"  {c('-'*50, Colors.DIM)}")
    if progress['avg_rate'] < 0.15:
        print(f"  {c('  ★ 修改率已达标！AI 写作风格与你非常接近', Colors.GREEN)}")
    elif progress['avg_rate'] < 0.30:
        print(f"  {c('  → 继续学习 2-3 章，修改率将继续下降', Colors.YELLOW)}")
    elif progress['avg_rate'] < 0.50:
        print(f"  {c('  → 坚持学习，风格正在逐步形成', Colors.YELLOW)}")
    else:
        print(f"  {c('  ! 修改率较高，建议继续学习更多章节', Colors.RED)}")

    print(f"\n{c('='*65, Colors.BOLD)}\n")


def show_trend(root):
    """显示趋势图"""
    chapters_data = load_all_history(root)

    if not chapters_data:
        print(f"\n  {c('[INFO] 暂无数据，无法显示趋势', Colors.YELLOW)}\n")
        return

    rates = [c['analysis']['modification_rate'] for c in chapters_data]
    chapters = [c['chapter'] for c in chapters_data]

    print(f"\n{c('='*65, Colors.BOLD)}")
    print(f"{c(' '*20)}修改率趋势", Colors.BOLD)
    print(f"{c('='*65, Colors.BOLD)}\n")

    # 简单 ASCII 趋势图
    max_rate = max(rates) if rates else 1
    min_rate = min(rates) if rates else 0
    height = 10

    for y in range(height, -1, -1):
        threshold = min_rate + (max_rate - min_rate) * y / height
        line = f"  {threshold*100:5.1f}% |"
        for rate in rates:
            if rate >= threshold:
                line += "█"
            else:
                line += " "
        print(line)

    print(f"  {c('-'*50, Colors.DIM)}")
    print(f"  {'':7}|", end='')
    for ch in chapters:
        print(f"{ch:2d}", end='')
    print()

    # 趋势分析
    if len(rates) >= 2:
        first = rates[0]
        last = rates[-1]
        delta = last - first
        if delta < -0.05:
            trend = c("下降 ↓", Colors.GREEN)
        elif delta > 0.05:
            trend = c("上升 ↑", Colors.RED)
        else:
            trend = c("稳定 →", Colors.YELLOW)

        print(f"\n  趋势分析：从 {first*100:.1f}% 到 {last*100:.1f}% ({trend})\n")


def export_report(root, output_file: str):
    """导出报告"""
    config = load_config(root)
    profile = load_profile(root)
    chapters_data = load_all_history(root)
    content_stats = scan_content_words(root)
    progress = calculate_learning_progress(chapters_data, profile)
    target_info = get_target_words(config)

    report = {
        'generated_at': datetime.now().isoformat(),
        'writing': {
            'total_words': content_stats['total'],
            'draft_words': content_stats.get('draft', 0),
            'target_words': target_info['total'],
            'complete_percent': content_stats['total'] / target_info['total'] * 100 if target_info['total'] > 0 else 0,
            'volumes': content_stats['volumes']
        },
        'learning': {
            'chapters_count': progress['chapters_count'],
            'avg_modification_rate': progress['avg_rate'],
            'target_rate': progress['target_rate'],
            'progress_percent': progress['progress_percent']
        },
        'chapters': [
            {'chapter': c['chapter'], 'modification_rate': c['analysis']['modification_rate'],
             'analyzed_at': c['analysis'].get('analyzed_at', '')}
            for c in chapters_data
        ]
    }

    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n  {c('[OK]', Colors.GREEN)} 报告已导出到：{output_path}\n")


def main():
    parser = argparse.ArgumentParser(description='学习进度统计 + 写作字数统计',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python story.py stats                    # 显示完整统计（字数+学习）
  python story.py stats --words             # 仅显示字数统计
  python story.py stats --learning          # 仅显示学习进度
  python story.py stats --trend             # 显示修改率趋势图
  python story.py stats --export report.json  # 导出报告
        """)
    parser.add_argument('--trend', '-t', action='store_true', help='显示修改率趋势图')
    parser.add_argument('--words', '-w', action='store_true', help='仅显示字数统计')
    parser.add_argument('--learning', '-l', action='store_true', help='仅显示学习进度')
    parser.add_argument('--export', '-e', metavar='FILE', help='导出报告到文件')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录', Colors.RED)}")
        sys.exit(1)

    config = load_config(root)
    profile = load_profile(root)
    chapters_data = load_all_history(root)
    content_stats = scan_content_words(root)
    target_info = get_target_words(config)
    progress = calculate_learning_progress(chapters_data, profile)

    if args.trend:
        show_trend(root)
    elif args.words:
        show_words_stats(root, config, content_stats, target_info)
    elif args.learning:
        show_learning_stats(root, profile, chapters_data, progress)
    elif args.export:
        export_report(root, args.export)
    else:
        # 默认显示完整统计（先字数，再学习）
        show_words_stats(root, config, content_stats, target_info)
        show_learning_stats(root, profile, chapters_data, progress)


if __name__ == '__main__':
    main()
