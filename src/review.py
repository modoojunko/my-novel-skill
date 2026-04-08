#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:review - 人机差异对比与审核

功能：
1. 导入 AI 生成的内容
2. 对比 AI 生成版 vs 用户修改版
3. 计算修改率
4. 生成差异报告

使用 difflib 进行差异分析。
"""

import os
import sys
import json
import argparse
import difflib
from pathlib import Path
from datetime import datetime
from collections import Counter


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
        if (current / 'story.json').exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def load_config(root):
    """加载配置"""
    config_path = root / 'story.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_chapter_path(root, chapter_num):
    """获取章节文件路径"""
    chapters_per = 30
    volume_num = ((chapter_num - 1) // chapters_per) + 1
    chapter_path = root / 'CONTENT' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'
    return chapter_path, volume_num


def count_chinese_chars(text: str) -> int:
    """统计中文字符数"""
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            count += 1
    return count


def extract_text_from_markdown(content: str) -> str:
    """从 Markdown 中提取纯文本"""
    lines = content.split('\n')
    result = []
    in_frontmatter = False

    for line in lines:
        # 跳过 frontmatter
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        # 跳过标题行
        if line.startswith('#'):
            continue
        result.append(line)

    return '\n'.join(result)


# ============================================================================
# 差异分析核心
# ============================================================================

def analyze_diff(ai_content: str, human_content: str) -> dict:
    """
    分析 AI 内容与人工修改的差异

    返回：
    {
        'ai_chars': AI 字符数,
        'human_chars': 人工字符数,
        'added_chars': 新增字符数,
        'deleted_chars': 删除字符数,
        'replacement_count': 替换次数,
        'modification_rate': 修改率 (0-1),
        'word_replacements': [(from, to, count), ...],
        'patterns': {
            'added_patterns': [...],
            'deleted_patterns': [...],
        }
    }
    """
    # 提取纯文本
    ai_text = extract_text_from_markdown(ai_content)
    human_text = extract_text_from_markdown(human_content)

    ai_chars = count_chinese_chars(ai_text)
    human_chars = count_chinese_chars(human_text)

    # 使用 difflib 进行差异分析
    ai_lines = ai_text.split('\n')
    human_lines = human_text.split('\n')

    differ = difflib.Differ()
    diff_result = list(differ.compare(ai_lines, human_lines))

    # 统计差异
    added_lines = []
    deleted_lines = []
    replaced_lines = []
    unchanged_count = 0

    i = 0
    while i < len(diff_result):
        line = diff_result[i]

        if line.startswith('+ '):
            # 新增的行
            added_lines.append(line[2:])
        elif line.startswith('- '):
            # 删除的行
            deleted_lines.append(line[2:])
        elif line.startswith('? '):
            # 差异标记行，跳过
            pass
        else:
            # unchanged
            if added_lines or deleted_lines:
                # 有未匹配的差异
                pass
            unchanged_count += 1

        i += 1

    # 计算替换次数（简化：删除和新增配对）
    replaced = min(len(added_lines), len(deleted_lines))
    only_added = len(added_lines) - replaced
    only_deleted = len(deleted_lines) - replaced

    # 统计新增/删除的字符数
    added_chars = sum(count_chinese_chars(line) for line in added_lines)
    deleted_chars = sum(count_chinese_chars(line) for line in deleted_lines)

    # 计算修改率（修改字数 / AI 总字数）
    total_modified = added_chars + deleted_chars
    modification_rate = min(1.0, total_modified / max(ai_chars, 1))

    # 提取高频替换词（简化版：基于行的对比）
    word_replacements = extract_word_replacements(ai_lines, human_lines)

    # 提取修改模式
    patterns = extract_modification_patterns(added_lines, deleted_lines)

    return {
        'ai_chars': ai_chars,
        'human_chars': human_chars,
        'added_chars': added_chars,
        'deleted_chars': deleted_chars,
        'replacement_count': replaced,
        'only_added_lines': only_added,
        'only_deleted_lines': only_deleted,
        'unchanged_count': unchanged_count,
        'modification_rate': modification_rate,
        'word_replacements': word_replacements,
        'patterns': patterns,
        'diff_lines': diff_result[:100]  # 限制返回的 diff 行数
    }


def extract_word_replacements(ai_lines: list, human_lines: list) -> list:
    """
    提取高频替换词

    返回格式：[(from_word, to_word, count), ...]
    """
    # 简单的基于整行对比
    replacements = []

    ai_set = set(ai_lines)
    human_set = set(human_lines)

    # 找出被替换的行
    for line in human_lines:
        if line not in ai_set:
            # 这行在 human 中存在但不在 ai 中
            # 找一个相似的 ai 行作为源
            best_match = None
            best_ratio = 0
            for ai_line in ai_lines:
                ratio = difflib.SequenceMatcher(None, line, ai_line).ratio()
                if ratio > best_ratio and ratio > 0.6:
                    best_ratio = ratio
                    best_match = ai_line

            if best_match:
                replacements.append((best_match, line, 1))

    # 合并相同替换
    counter = Counter()
    for from_word, to_word, _ in replacements:
        key = (from_word[:20], to_word[:20])  # 取前20字符作为 key
        counter[key] += 1

    return [(k[0], k[1], v) for k, v in counter.most_common(10)]


def extract_modification_patterns(added_lines: list, deleted_lines: list) -> dict:
    """
    提取修改模式

    分析添加和删除的内容，总结写作偏好
    """
    patterns = {
        'prefers_short_sentences': False,
        'avoids_passive_voice': False,
        'removes_redundant_modifiers': False,
        'adds_concrete_details': False,
        'notes': []
    }

    # 检测是否偏好短句
    avg_added_length = sum(len(line) for line in added_lines) / max(len(added_lines), 1)
    avg_deleted_length = sum(len(line) for line in deleted_lines) / max(len(deleted_lines), 1)

    if avg_deleted_length > avg_added_length * 1.5:
        patterns['prefers_short_sentences'] = True
        patterns['notes'].append('偏好短句，删除了较长的句子')

    # 检测是否删除冗余修饰词
    redundant_words = ['非常', '十分', '特别', '极其', '相当', '格外']
    redundant_found = [w for w in redundant_words if any(w in line for line in deleted_lines)]

    if redundant_found:
        patterns['removes_redundant_modifiers'] = True
        patterns['notes'].append(f'删除冗余修饰词：{", ".join(redundant_found)}')

    # 检测是否增加具体细节
    if len(added_lines) > len(deleted_lines):
        patterns['adds_concrete_details'] = True
        patterns['notes'].append('添加了更多细节描写')

    return patterns


def generate_diff_report(chapter_num: int, analysis: dict) -> str:
    """生成差异报告"""
    rate_percent = analysis['modification_rate'] * 100

    # 根据修改率显示颜色
    if rate_percent < 20:
        rate_color = Colors.GREEN
    elif rate_percent < 40:
        rate_color = Colors.YELLOW
    else:
        rate_color = Colors.RED

    lines = []
    lines.append(c(f"\n{'='*70}", Colors.BOLD))
    lines.append(c(f"          第 {chapter_num} 章 差异分析报告", Colors.BOLD))
    lines.append(c(f"{'='*70}\n", Colors.BOLD))

    # 基础统计
    lines.append(c("  基础统计", Colors.CYAN))
    lines.append("-" * 50)
    lines.append(f"  AI 生成字数：{analysis['ai_chars']} 字")
    lines.append(f"  用户修改字数：{analysis['human_chars']} 字")
    lines.append(f"  修改占比：{c(f'{rate_percent:.1f}%', rate_color)}")
    lines.append("")

    # 详细统计
    lines.append(c("  详细统计", Colors.CYAN))
    lines.append("-" * 50)
    lines.append(f"  新增：{analysis['added_chars']} 字 ({analysis['only_added_lines']} 处)")
    lines.append(f"  删除：{analysis['deleted_chars']} 字 ({analysis['only_deleted_lines']} 处)")
    lines.append(f"  替换：{analysis['replacement_count']} 处")
    lines.append(f"  未改动：{analysis['unchanged_count']} 处")
    lines.append("")

    # 高频替换
    if analysis['word_replacements']:
        lines.append(c("  高频替换", Colors.CYAN))
        lines.append("-" * 50)
        for from_word, to_word, count in analysis['word_replacements'][:5]:
            if from_word and to_word:
                from_display = from_word[:15] + ('...' if len(from_word) > 15 else '')
                to_display = to_word[:15] + ('...' if len(to_word) > 15 else '')
                lines.append(f'  "{from_display}" -> "{to_display}" ({count}次)')
        lines.append("")

    # 写作偏好
    patterns = analysis['patterns']
    if patterns['notes']:
        lines.append(c("  检测到的写作偏好", Colors.CYAN))
        lines.append("-" * 50)
        for note in patterns['notes']:
            lines.append(f"  * {note}")
        lines.append("")

    # 建议
    lines.append(c("  建议", Colors.CYAN))
    lines.append("-" * 50)
    if rate_percent < 15:
        lines.append(c("  [OK] 修改率很低，AI 写作质量很好！", Colors.GREEN))
    elif rate_percent < 30:
        lines.append(c("  [->] 修改率适中，AI 学习效果良好", Colors.YELLOW))
    else:
        lines.append(c("  [!] 修改率较高，建议查看 STYLE/prompts/ 更新风格指南", Colors.RED))
    lines.append("")

    lines.append(c(f"{'='*70}\n", Colors.BOLD))

    return '\n'.join(lines)


# ============================================================================
# 文件操作
# ============================================================================

def ensure_learning_dirs(root):
    """确保学习相关目录存在"""
    dirs = [
        root / 'STYLE',
        root / 'STYLE' / 'history',
        root / 'STYLE' / 'prompts',
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def save_review_history(root, chapter_num: int, ai_content: str, human_content: str, analysis: dict):
    """保存审核历史"""
    ensure_learning_dirs(root)

    history_dir = root / 'STYLE' / 'history' / f'chapter-{chapter_num:03d}'
    history_dir.mkdir(parents=True, exist_ok=True)

    # 保存 AI 原始版本
    (history_dir / 'ai_raw.md').write_text(ai_content, encoding='utf-8')

    # 保存人工修改版本
    (history_dir / 'human_final.md').write_text(human_content, encoding='utf-8')

    # 保存差异分析结果
    report = {
        'chapter': chapter_num,
        'analyzed_at': datetime.now().isoformat(),
        'ai_chars': analysis['ai_chars'],
        'human_chars': analysis['human_chars'],
        'modification_rate': analysis['modification_rate'],
        'patterns': analysis['patterns'],
        'word_replacements': [
            {'from': w[0], 'to': w[1], 'count': w[2]}
            for w in analysis['word_replacements']
        ]
    }
    (history_dir / 'analysis.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    return history_dir


def load_review_history(root, chapter_num: int) -> dict:
    """加载审核历史"""
    history_dir = root / 'STYLE' / 'history' / f'chapter-{chapter_num:03d}'

    if not history_dir.exists():
        return None

    ai_path = history_dir / 'ai_raw.md'
    human_path = history_dir / 'human_final.md'
    analysis_path = history_dir / 'analysis.json'

    if not all(p.exists() for p in [ai_path, human_path, analysis_path]):
        return None

    ai_content = ai_path.read_text(encoding='utf-8')
    human_content = human_path.read_text(encoding='utf-8')
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    return {
        'ai_content': ai_content,
        'human_content': human_content,
        'analysis': analysis
    }


# ============================================================================
# 命令行接口
# ============================================================================

def cmd_import(root, chapter_num: int, ai_file: str):
    """导入 AI 内容"""
    ai_path = Path(ai_file)
    if not ai_path.exists():
        print(f"  {c(f'[ERROR] 文件不存在：{ai_file}', Colors.RED)}")
        sys.exit(1)

    content = ai_path.read_text(encoding='utf-8')
    chars = count_chinese_chars(extract_text_from_markdown(content))

    # 保存到草稿目录
    draft_dir = root / 'CONTENT' / 'draft'
    draft_dir.mkdir(exist_ok=True)

    draft_path = draft_dir / f'chapter-{chapter_num:03d}.ai-draft.md'
    draft_path.write_text(content, encoding='utf-8')

    print(f"""
{c('[OK] AI 内容已导入', Colors.GREEN)}

  章节：第{chapter_num}章
  字数：约 {chars} 字
  文件：{draft_path.relative_to(root)}

{c('[TIP] 下一步：', Colors.YELLOW)}
  1. 在章节文件中查看/修改内容
  2. 保存修改后，运行：python story.py review {chapter_num}
  3. 或运行：python story.py learn {chapter_num}
""")


def cmd_compare(root, chapter_num: int):
    """对比差异"""
    chapter_path, volume_num = get_chapter_path(root, chapter_num)

    # 查找 AI 原始版本
    draft_path = root / 'CONTENT' / 'draft' / f'chapter-{chapter_num:03d}.ai-draft.md'
    history_dir = root / 'STYLE' / 'history' / f'chapter-{chapter_num:03d}'

    # 确定 AI 原始内容
    if history_dir.exists():
        ai_path = history_dir / 'ai_raw.md'
    elif draft_path.exists():
        ai_path = draft_path
    else:
        print(f"  {c('[ERROR] 未找到 AI 原始版本', Colors.RED)}")
        print(f"  请先使用 --ai 参数导入 AI 内容")
        sys.exit(1)

    ai_content = ai_path.read_text(encoding='utf-8')

    # 读取人工修改版本
    if not chapter_path.exists():
        print(f"  {c('[ERROR] 未找到章节文件', Colors.RED)}")
        print(f"  文件：{chapter_path}")
        sys.exit(1)

    human_content = chapter_path.read_text(encoding='utf-8')

    # 分析差异
    analysis = analyze_diff(ai_content, human_content)

    # 生成报告
    report = generate_diff_report(chapter_num, analysis)
    print(report)

    # 保存历史
    history_path = save_review_history(root, chapter_num, ai_content, human_content, analysis)
    print(f"  {c(f'[INFO] 审核历史已保存到：{history_path.relative_to(root)}', Colors.DIM)}")


def cmd_stat(root, chapter_num: int):
    """仅显示统计信息"""
    analysis_data = load_review_history(root, chapter_num)

    if not analysis_data:
        print(f"  {c('[ERROR] 未找到审核历史', Colors.RED)}")
        print(f"  请先运行：python story.py review {chapter_num}")
        sys.exit(1)

    analysis = analysis_data['analysis']
    rate = analysis['modification_rate'] * 100

    if rate < 20:
        rate_color = Colors.GREEN
    elif rate < 40:
        rate_color = Colors.YELLOW
    else:
        rate_color = Colors.RED

    print(f"""
  第 {chapter_num} 章审核统计
  --------------------
  AI 字数：{analysis['ai_chars']}
  修改字数：{analysis['human_chars']}
  修改率：{c(f'{rate:.1f}%', rate_color)}
""")


def cmd_preview_diff(root, chapter_num: int):
    """预览差异（diff 格式）"""
    history_data = load_review_history(root, chapter_num)

    if not history_data:
        print(f"  {c('[ERROR] 未找到审核历史', Colors.RED)}")
        sys.exit(1)

    ai_text = extract_text_from_markdown(history_data['ai_content'])
    human_text = extract_text_from_markdown(history_data['human_content'])

    diff = difflib.unified_diff(
        ai_text.splitlines(keepends=True),
        human_text.splitlines(keepends=True),
        fromfile='AI 生成',
        tofile='你的修改',
        lineterm=''
    )

    print(c(f"\n{'='*70}", Colors.DIM))
    print(c(f"  第 {chapter_num} 章 差异预览 (前50行)", Colors.BOLD))
    print(c(f"{'='*70}\n", Colors.DIM))

    for i, line in enumerate(diff):
        if i > 50:
            print(f"\n  {c('... (超过50行，显示省略)', Colors.DIM)}")
            break

        if line.startswith('+'):
            print(c(line, Colors.GREEN), end='')
        elif line.startswith('-'):
            print(c(line, Colors.RED), end='')
        elif line.startswith('^'):
            print(c(line, Colors.BLUE), end='')
        else:
            print(line, end='')


def main():
    parser = argparse.ArgumentParser(
        description='人机差异对比与审核',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python story.py review 5                        # 对比差异
  python story.py review 5 --ai content.md        # 导入 AI 内容并对比
  python story.py review 5 --stat                 # 仅显示统计
  python story.py review 5 --diff                # 预览 diff 格式

使用流程：
  1. story:write 5 --show -> 获取 Agent Prompt
  2. Agent 生成内容后 -> story:review 5 --ai <文件>
  3. 在章节文件中修改内容
  4. story:review 5 -> 查看差异分析
  5. story:learn 5 -> 从修改中学习风格
        """
    )
    parser.add_argument('chapter', nargs='?', type=int, help='章节号')
    parser.add_argument('--ai', metavar='FILE',
                        help='导入 AI 生成的内容文件')
    parser.add_argument('--stat', action='store_true',
                        help='仅显示统计信息')
    parser.add_argument('--diff', action='store_true',
                        help='预览 diff 格式差异')
    parser.add_argument('--history', action='store_true',
                        help='显示历史审核记录')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录', Colors.RED)}")
        sys.exit(1)

    # 如果有 --ai 参数，先导入
    if args.ai:
        chapter_num = args.chapter or 1
        cmd_import(root, chapter_num, args.ai)
        return

    if not args.chapter:
        print(f"  {c('[ERROR] 请指定章节号', Colors.RED)}")
        print(f"  用法：python story.py review <章节号>")
        sys.exit(1)

    if args.diff:
        cmd_preview_diff(root, args.chapter)
    elif args.stat:
        cmd_stat(root, args.chapter)
    elif args.history:
        show_history_list(root, args.chapter)
    else:
        cmd_compare(root, args.chapter)


def show_history_list(root, chapter_num: int):
    """显示历史审核列表"""
    history_dir = root / 'STYLE' / 'history' / f'chapter-{chapter_num:03d}'

    if not history_dir.exists():
        print(f"  {c(f'[INFO] 第 {chapter_num} 章暂无审核历史', Colors.YELLOW)}")
        return

    analysis_path = history_dir / 'analysis.json'
    if analysis_path.exists():
        with open(analysis_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rate = data['modification_rate'] * 100
        analyzed_at = data.get('analyzed_at', 'unknown')

        print(f"""
  第 {chapter_num} 章审核历史
  --------------------
  分析时间：{analyzed_at}
  AI 字数：{data['ai_chars']}
  修改字数：{data['human_chars']}
  修改率：{rate:.1f}%
""")


if __name__ == '__main__':
    main()
