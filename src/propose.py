#!/usr/bin/env python3
"""
story:propose - 创建创作意图

参考 OpenSpec 的 proposal.md，为小说创作提供结构化的意图定义。
使用 JSON 作为配置文件格式。
"""

import os
import sys
import json
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

def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


# ============================================================================
# 工具函数（从 paths.py 导入）
# ============================================================================

from .paths import find_project_root, load_config, save_config

def parse_target(target: str):
    """解析目标（章节/卷/场景）"""
    target = target.strip().lower()

    if target.startswith('卷'):
        return ('volume', target.replace('卷', '').strip())
    elif target.startswith('章') or target.startswith('第'):
        import re
        match = re.search(r'(\d+)', target)
        if match:
            return ('chapter', int(match.group(1)))
    elif target.startswith('场景'):
        return ('scene', target.replace('场景', '').strip())
    elif target == '概念' or target == 'concept':
        return ('concept', 'story')
    else:
        if target.isdigit():
            return ('volume', int(target))

    return ('chapter', 1)  # 默认第一章

def create_proposal(root: Path, target_type: str, target_id: str, title: str = None):
    """创建创作意图"""

    # 确定目录
    if target_type == 'concept':
        proposals_dir = root / 'SPECS' / 'meta' / 'proposals'
    elif target_type == 'volume':
        proposals_dir = root / 'OUTLINE' / f'volume-{int(target_id):03d}' / 'proposals'
    else:
        proposals_dir = root / 'OUTLINE' / 'proposals'

    proposals_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d')
    if target_type == 'concept':
        filename = f"{timestamp}-story-concept-proposal.md"
    else:
        filename = f"{timestamp}-{target_type}-{target_id}-proposal.md"

    filepath = proposals_dir / filename

    # 读取故事概念作为参考
    concept_path = root / 'SPECS' / 'meta' / 'story-concept.md'
    logline = ""
    if concept_path.exists():
        logline = concept_path.read_text(encoding='utf-8')

    # 生成 proposal 内容
    if target_type == 'concept':
        content = f"""# 创作意图：{title or '故事概念'}

## 意图
（描述这次创作的目的）

## 涉及设定
- 人物：
- 世界观：
- 主题：

## 约束条件
- 字数限制：
- 风格要求：
- 禁止内容：

## 参考
{logline[:500] if logline else '(无)'}
"""
    else:
        content = f"""# 创作意图：{target_type.capitalize()} {target_id}

## 意图
这{target_type}要讲述什么？

## 与整体故事的关系
如何服务于故事主题？

## 涉及设定
- 关联人物：
- 涉及世界观：
- 伏笔/呼应：

## 核心场景
（列出必须包含的关键场景）

## 情绪目标
读者应该感受到什么？

## 字数预期
约 xxx 字

## 参考
{logline[:500] if logline else '(无)'}
"""

    filepath.write_text(content, encoding='utf-8')
    return filepath

def show_help():
    """显示帮助"""
    print("""
================================================================================
              [PROPOSAL] 创作意图 - 创建提案
================================================================================

用法：
  python story.py propose [目标] [标题]

示例：
  python story.py propose                    # 交互式创建
  python story.py propose 第一章              # 创建第一章提案
  python story.py propose 卷1                # 创建第一卷提案
  python story.py propose 概念               # 创建故事概念提案

参数：
  目标      可选，章节/卷/概念
  标题      可选，提案标题
""")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='创建创作意图')
    parser.add_argument('target', nargs='?', help='目标（第一章/卷1/概念）')
    parser.add_argument('title', nargs='?', help='提案标题')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式（Agent 驱动）')

    args = parser.parse_args()

    # 查找项目
    root = find_project_root()
    if not root:
        print(f"  [ERROR] 未找到项目目录（请在包含 story.json 的目录下运行）")
        sys.exit(1)

    print(f"\n[PROPOSAL] 创建创作意图")
    print(f"  位置：{root}")
    print()

    # 解析目标
    if args.target:
        target_type, target_id = parse_target(args.target)
    elif args.non_interactive:
        print(f"  [ERROR] 非交互模式必须指定 target 参数")
        print(f"  用法：story:propose <target> [title]")
        sys.exit(1)
    else:
        print("  选择目标类型：")
        print("    1. 故事概念")
        print("    2. 卷")
        print("    3. 章节")
        choice = input("  选择 [1-3]: ").strip()
        if choice == '1':
            target_type, target_id = 'concept', 'story'
        elif choice == '2':
            target_id = input("  卷号: ").strip()
            target_type = 'volume'
        else:
            target_id = input("  章号: ").strip() or '1'
            target_type = 'chapter'

    # 创建提案
    filepath = create_proposal(root, target_type, target_id, args.title)

    print(f"  [OK] 已创建：{filepath.relative_to(root)}")
    print()

if __name__ == '__main__':
    main()
