#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:learn - 风格学习引擎

功能：
1. 从审核历史中提取修改模式
2. 生成/更新风格 prompt 片段
3. 保存到 STYLE/prompts/ 目录

这个模块不调用 LLM，只做模式提取和文件生成。
提取出的 prompt 片段供 Agent 使用。
"""

import os
import sys
import json
import argparse
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


def ensure_dirs(root):
    """确保学习相关目录存在"""
    dirs = [
        root / 'STYLE',
        root / 'STYLE' / 'history',
        root / 'STYLE' / 'prompts',
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 风格模式提取
# ============================================================================

def extract_vocabulary_patterns(analysis: dict, history_dir: Path) -> dict:
    """
    提取词汇替换模式

    分析词级替换，生成词汇偏好 prompt
    """
    patterns = {
        'replacements': {},  # {原词: 替换词}
        'avoid': [],         # 应避免的词汇
        'prefer': []         # 偏好的词汇
    }

    word_replacements = analysis.get('word_replacements', [])

    for item in word_replacements:
        if isinstance(item, dict):
            from_word = item.get('from', '')
            to_word = item.get('to', '')
            count = item.get('count', 1)
        else:
            from_word, to_word, count = item[0], item[1], item[2]

        if count >= 1:
            if len(from_word) > 1 and len(to_word) > 1:
                patterns['replacements'][from_word] = to_word

    patterns_data = analysis.get('patterns', {})
    notes = patterns_data.get('notes', [])

    for note in notes:
        if '冗余修饰词' in note:
            words = note.split('：')[-1].replace(',', '、').split('、')
            for w in words:
                w = w.strip()
                if w:
                    patterns['avoid'].append(w)

    return patterns


def extract_sentence_patterns(analysis: dict) -> dict:
    """提取句式偏好"""
    patterns = {
        'prefers_short_sentences': False,
        'avoids_passive_voice': False,
        'removes_fillers': False,
        'direct_dialogue': False,
        'notes': []
    }

    patterns_data = analysis.get('patterns', {})

    if patterns_data.get('prefers_short_sentences'):
        patterns['prefers_short_sentences'] = True
        patterns['notes'].append('优先使用短句，避免冗长')

    if patterns_data.get('removes_redundant_modifiers'):
        patterns['removes_fillers'] = True
        patterns['notes'].append('删除冗余修饰词')

    if patterns_data.get('adds_concrete_details'):
        patterns['direct_dialogue'] = True
        patterns['notes'].append('偏好具体细节，减少抽象描写')

    return patterns


def extract_pacing_patterns(analysis: dict) -> dict:
    """提取节奏偏好"""
    patterns = {
        'fast_pacing': False,
        'short_paragraphs': False,
        'frequent_scene_change': False,
        'notes': []
    }

    added_lines = analysis.get('only_added_lines', 0)
    deleted_lines = analysis.get('only_deleted_lines', 0)

    if deleted_lines > added_lines * 2:
        patterns['fast_pacing'] = True
        patterns['notes'].append('偏好快节奏，删除多余内容')

    return patterns


# ============================================================================
# Prompt 片段生成
# ============================================================================

def generate_vocabulary_prompt(vocabulary_patterns: dict) -> str:
    """生成词汇偏好 prompt 片段"""
    lines = []
    lines.append("# 词汇偏好\n")

    replacements = vocabulary_patterns.get('replacements', {})
    if replacements:
        lines.append("## 替换规则\n")
        lines.append("请将以下词汇替换为更符合用户风格的表达：\n")
        for from_word, to_word in list(replacements.items())[:10]:
            lines.append(f"- \"{from_word}\" -> \"{to_word}\"")
        lines.append("")

    avoid_words = vocabulary_patterns.get('avoid', [])
    if avoid_words:
        lines.append("## 避免词汇\n")
        lines.append("尽量避免使用以下词汇：\n")
        lines.append(f"- {'、'.join(avoid_words)}")
        lines.append("")

    return '\n'.join(lines)


def generate_sentence_prompt(sentence_patterns: dict) -> str:
    """生成句式偏好 prompt 片段"""
    lines = []
    lines.append("# 句式偏好\n")

    notes = sentence_patterns.get('notes', [])

    if sentence_patterns.get('prefers_short_sentences'):
        lines.append("## 句子长度\n")
        lines.append("- 优先使用短句，每句不超过 25 字")
        lines.append("- 减少从句使用，拆分长句")
        lines.append("")

    if sentence_patterns.get('removes_fillers'):
        lines.append("## 修饰词使用\n")
        lines.append("- 删除冗余修饰词（如\"非常\"、\"十分\"、\"特别\"）")
        lines.append("- 用具体动作或细节代替笼统描述")
        lines.append("")

    if sentence_patterns.get('direct_dialogue'):
        lines.append("## 对话风格\n")
        lines.append("- 对话直接，少用\"说道\"、\"答道\"等引语")
        lines.append("- 多用简短有力的对话")
        lines.append("")

    return '\n'.join(lines)


def generate_pacing_prompt(pacing_patterns: dict) -> str:
    """生成节奏偏好 prompt 片段"""
    lines = []
    lines.append("# 节奏偏好\n")

    notes = pacing_patterns.get('notes', [])

    if pacing_patterns.get('fast_pacing'):
        lines.append("## 叙事节奏\n")
        lines.append("- 保持快节奏，场景内事件紧凑")
        lines.append("- 减少环境描写篇幅")
        lines.append("- 快速推进情节")
        lines.append("")

    if pacing_patterns.get('short_paragraphs'):
        lines.append("## 段落结构\n")
        lines.append("- 每个段落 3-5 行")
        lines.append("- 频繁分段，避免大段落")
        lines.append("")

    return '\n'.join(lines)


def generate_style_guide(chapters_data: list) -> dict:
    """生成完整的风格指南"""
    all_vocab_replacements = {}
    all_avoid_words = []

    for chapter_data in chapters_data:
        analysis = chapter_data.get('analysis', {})
        vocab = extract_vocabulary_patterns(analysis, None)
        for k, v in vocab.get('replacements', {}).items():
            if k not in all_vocab_replacements:
                all_vocab_replacements[k] = v
        all_avoid_words.extend(vocab.get('avoid', []))

    vocabulary_prompt = generate_vocabulary_prompt({
        'replacements': all_vocab_replacements,
        'avoid': list(set(all_avoid_words))
    })

    if chapters_data:
        sentence_prompt = generate_sentence_prompt(
            extract_sentence_patterns(chapters_data[0].get('analysis', {}))
        )
        pacing_prompt = generate_pacing_prompt(
            extract_pacing_patterns(chapters_data[0].get('analysis', {}))
        )
    else:
        sentence_prompt = ""
        pacing_prompt = ""

    return {
        'vocabulary': vocabulary_prompt,
        'sentence': sentence_prompt,
        'pacing': pacing_prompt,
        'full_guide': vocabulary_prompt + '\n\n' + sentence_prompt + '\n\n' + pacing_prompt
    }


# ============================================================================
# 文件保存
# ============================================================================

def save_style_prompts(root, style_guide: dict):
    """保存风格 prompt 到文件"""
    ensure_dirs(root)
    prompts_dir = root / 'STYLE' / 'prompts'

    vocab_path = prompts_dir / 'vocabulary.md'
    vocab_path.write_text(style_guide.get('vocabulary', '# 词汇偏好\n'), encoding='utf-8')
    print(f"  {c('[OK]', Colors.GREEN)} {vocab_path.relative_to(root)}")

    sentence_path = prompts_dir / 'sentence.md'
    sentence_path.write_text(style_guide.get('sentence', '# 句式偏好\n'), encoding='utf-8')
    print(f"  {c('[OK]', Colors.GREEN)} {sentence_path.relative_to(root)}")

    pacing_path = prompts_dir / 'pacing.md'
    pacing_path.write_text(style_guide.get('pacing', '# 节奏偏好\n'), encoding='utf-8')
    print(f"  {c('[OK]', Colors.GREEN)} {pacing_path.relative_to(root)}")

    full_path = prompts_dir / 'full_guide.md'
    full_path.write_text(style_guide.get('full_guide', ''), encoding='utf-8')
    print(f"  {c('[OK]', Colors.GREEN)} {full_path.relative_to(root)}")


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

        chapter_num = int(chapter_num_str)
        analysis_path = chapter_dir / 'analysis.json'

        if not analysis_path.exists():
            continue

        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis = json.load(f)

        chapters_data.append({
            'chapter': chapter_num,
            'analysis': analysis
        })

    return chapters_data


def update_profile(root, chapters_count: int, modification_rate: float):
    """更新风格档案"""
    profile_path = root / 'STYLE' / 'profile.json'

    if profile_path.exists():
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
    else:
        profile = {
            'created': datetime.now().isoformat(),
            'chapters_trained': 0,
            'avg_modification_rate': 0.0,
            'target_modification_rate': 0.15
        }

    profile['chapters_trained'] = chapters_count
    profile['avg_modification_rate'] = modification_rate
    profile['last_learned'] = datetime.now().isoformat()

    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


# ============================================================================
# 命令行接口
# ============================================================================

def cmd_learn_chapter(root, chapter_num: int, force: bool = False):
    """学习单个章节"""
    history_dir = root / 'STYLE' / 'history' / f'chapter-{chapter_num:03d}'

    if not history_dir.exists():
        print(f"  {c(f'[ERROR] 第 {chapter_num} 章暂无审核历史', Colors.RED)}")
        print(f"  请先运行：python story.py review {chapter_num}")
        return

    analysis_path = history_dir / 'analysis.json'
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    print(f"\n{c('[LEARN] 学习第 {chapter_num} 章风格...', Colors.BOLD)}\n")

    vocab_patterns = extract_vocabulary_patterns(analysis, history_dir)
    sentence_patterns = extract_sentence_patterns(analysis)
    pacing_patterns = extract_pacing_patterns(analysis)

    vocabulary_prompt = generate_vocabulary_prompt(vocab_patterns)
    sentence_prompt = generate_sentence_prompt(sentence_patterns)
    pacing_prompt = generate_pacing_prompt(pacing_patterns)

    style_guide = {
        'vocabulary': vocabulary_prompt,
        'sentence': sentence_prompt,
        'pacing': pacing_prompt,
        'full_guide': vocabulary_prompt + '\n\n' + sentence_prompt + '\n\n' + pacing_prompt
    }

    print(c('  保存风格片段：', Colors.CYAN))
    save_style_prompts(root, style_guide)

    update_profile(root, 1, analysis.get('modification_rate', 0))

    print(f"""
{c('[OK] 学习完成！', Colors.GREEN)}

  修改率：{analysis.get('modification_rate', 0) * 100:.1f}%

{c('[TIP] 下一步：', Colors.YELLOW)}
  1. 运行 story:write --show 查看更新后的 Prompt
  2. 运行 story:stats 查看学习进度
  3. 继续写作，让 AI 学习更多风格
""")


def cmd_learn_all(root, force: bool = False):
    """学习所有章节"""
    chapters_data = load_all_history(root)

    if not chapters_data:
        print(f"  {c('[ERROR] 未找到任何审核历史', Colors.RED)}")
        print(f"  请先完成审核：python story.py review <章节号>")
        return

    print(f"\n{c('[LEARN] 学习所有章节风格...', Colors.BOLD)}\n")
    print(f"  发现 {len(chapters_data)} 个章节的审核历史\n")

    style_guide = generate_style_guide(chapters_data)

    print(c('  保存风格片段：', Colors.CYAN))
    save_style_prompts(root, style_guide)

    rates = [c.get('analysis', {}).get('modification_rate', 0) for c in chapters_data]
    avg_rate = sum(rates) / len(rates) if rates else 0

    update_profile(root, len(chapters_data), avg_rate)

    print(f"""
{c('[OK] 学习完成！', Colors.GREEN)}

  学习章节数：{len(chapters_data)}
  平均修改率：{avg_rate * 100:.1f}%

{c('[TIP] 下一步：', Colors.YELLOW)}
  1. 运行 story:style --prompts 查看详细风格
  2. 运行 story:stats 查看学习进度
""")


def main():
    parser = argparse.ArgumentParser(
        description='风格学习引擎 - 从修改中学习写作风格',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python story.py learn              # 学习所有审核过的章节
  python story.py learn 5           # 学习第5章
  python story.py learn --force     # 强制重新学习

使用流程：
  1. story:write 5 --show -> 获取 Prompt
  2. Agent 生成内容后 -> story:review 5 --ai <文件>
  3. 在章节文件中修改内容
  4. story:review 5 -> 分析差异
  5. story:learn 5 -> 从修改中学习风格
        """
    )
    parser.add_argument('chapter', nargs='?', type=int, help='章节号（不指定则学习所有）')
    parser.add_argument('--force', '-f', action='store_true',
                        help='强制重新学习')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录', Colors.RED)}")
        sys.exit(1)

    if args.chapter:
        cmd_learn_chapter(root, args.chapter, args.force)
    else:
        cmd_learn_all(root, args.force)


if __name__ == '__main__':
    main()
