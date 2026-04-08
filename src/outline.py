#!/usr/bin/env python3
"""
story:outline - 编辑大纲

提供交互式的大纲编辑功能。
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

def save_config(root, config):
    """保存配置"""
    config_path = root / 'story.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def ensure_outline_dirs(root, volumes):
    """确保大纲目录存在"""
    outline_dir = root / 'OUTLINE'
    outline_dir.mkdir(exist_ok=True)

    for i in range(1, volumes + 1):
        vol_dir = outline_dir / f'volume-{i}'
        vol_dir.mkdir(exist_ok=True)

def edit_meta_outline(root, config):
    """编辑总大纲"""
    meta_path = root / 'OUTLINE' / 'meta.md'

    existing = ""
    if meta_path.exists():
        existing = meta_path.read_text(encoding='utf-8')

    print(f"\n[OUTLINE] 编辑总大纲")
    print(f"  文件：{meta_path.relative_to(root)}")
    print(f"  提示：按 Enter 使用现有内容，q 退出编辑")
    print()

    if existing:
        print(c("现有内容：", Colors.DIM))
        print("-" * 50)
        print(existing[:500])
        if len(existing) > 500:
            print(f"... ({len(existing)} 字符)")
        print("-" * 50)
        print()

    return meta_path

def edit_volume_outline(root, config, volume_num):
    """编辑分卷大纲"""
    vol_path = root / 'OUTLINE' / f'volume-{volume_num}.md'

    vol_path.parent.mkdir(exist_ok=True)

    volumes = config.get('structure', {}).get('volumes', 1)
    chapters = config.get('structure', {}).get('chapters_per_volume', 30)

    # 从 volume_titles 获取卷名和主题
    volume_titles = config.get('structure', {}).get('volume_titles', [])
    title = f'卷{volume_num}'
    theme = ''
    for vt in volume_titles:
        if vt.get('num') == volume_num:
            title = vt.get('title', f'卷{volume_num}')
            theme = vt.get('theme', '')
            break

    if not vol_path.exists():
        chapters_content = []
        for i in range(1, chapters + 1):
            chapters_content.append(f"### 第{i}章：xxx")

        theme_str = f"{theme}" if theme else "（待填充）"
        content = f"""# 第{volume_num}卷：{title}

## 本卷主题
{theme_str}

## 卷概述
（待填充 - 本卷的起承转合）

## 主要事件
（待填充）

## 章节安排

{chr(10).join(chapters_content)}

## 本卷高潮
（待填充）

## 伏笔/呼应
（待填充）
"""
        vol_path.write_text(content, encoding='utf-8')

    print(f"\n[OUTLINE] 编辑第{volume_num}卷大纲")
    print(f"  文件：{vol_path.relative_to(root)}")
    print()

    return vol_path

def edit_chapter_outline(root, config, chapter_num):
    """编辑章节大纲"""
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    vol_dir = root / 'OUTLINE' / f'volume-{volume_num}'
    vol_dir.mkdir(exist_ok=True)

    chapter_path = vol_dir / f'chapter-{chapter_num:03d}.md'

    if not chapter_path.exists():
        content = f"""# 第{chapter_num}章：xxx

## 本章目标
（待填充）

## POV
（待填充）

## 场景列表
1. [开场] 场景描述 - POV:xxx - 约800字
2. [发展] 场景描述 - POV:xxx - 约1200字
3. [转折] 场景描述 - POV:xxx - 约1000字

## 情节点
（待填充）

## 关键对话
（待填充）

## 伏笔记录
（待填充）

## 预期字数
约 3000 字
"""
        chapter_path.write_text(content, encoding='utf-8')

    print(f"\n[OUTLINE] 编辑第{chapter_num}章大纲")
    print(f"  文件：{chapter_path.relative_to(root)}")
    print()

    return chapter_path

def init_volume_chapters(root, config, volume_num):
    """批量初始化某卷下所有章节大纲"""
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    start_chapter = (volume_num - 1) * chapters_per + 1
    end_chapter = volume_num * chapters_per

    created = []
    skipped = []

    for ch_num in range(start_chapter, end_chapter + 1):
        vol_dir = root / 'OUTLINE' / f'volume-{volume_num}'
        vol_dir.mkdir(exist_ok=True)
        chapter_path = vol_dir / f'chapter-{ch_num:03d}.md'

        if not chapter_path.exists():
            content = f"""# 第{ch_num}章：xxx

## 本章目标
（待填充）

## POV
（待填充）

## 场景列表
1. [开场] 场景描述 - POV:xxx - 约800字
2. [发展] 场景描述 - POV:xxx - 约1200字
3. [转折] 场景描述 - POV:xxx - 约1000字

## 情节点
（待填充）

## 关键对话
（待填充）

## 伏笔记录
（待填充）

## 预期字数
约 3000 字
"""
            chapter_path.write_text(content, encoding='utf-8')
            created.append(ch_num)
        else:
            skipped.append(ch_num)

    return created, skipped

def show_outline_tree(root, config):
    """显示大纲树状结构"""
    volumes = config.get('structure', {}).get('volumes', 1)
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)

    print(f"\n[TREE] 大纲结构")
    print('-' * 50)
    print("  OUTLINE/")
    print("  |-- meta.md")

    for v in range(1, volumes + 1):
        vol_path = root / 'OUTLINE' / f'volume-{v}.md'
        vol_status = '[OK]' if vol_path.exists() else '[ ]'
        print(f"  |-- volume-{v}.md {vol_status}")

        vol_dir = root / 'OUTLINE' / f'volume-{v}'
        if vol_dir.exists():
            chapters = list(vol_dir.glob('chapter-*.md'))
            for ch in sorted(chapters)[:5]:
                ch_status = '[OK]'
                print(f"  |   |-- {ch.name} {ch_status}")
            if len(chapters) > 5:
                print(f"  |   +-- ... 还有 {len(chapters) - 5} 个章节")

    print()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='编辑大纲')
    parser.add_argument('target', nargs='?', help='目标（meta/卷1/章节1）')
    parser.add_argument('--list', '-l', action='store_true', help='列出大纲结构')
    parser.add_argument('--init-chapters', type=int, metavar='VOLUME',
                        help='批量初始化指定卷的所有章节大纲')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  [ERROR] 未找到项目目录")
        sys.exit(1)

    config = load_config(root)

    volumes = config.get('structure', {}).get('volumes', 1)
    ensure_outline_dirs(root, volumes)

    # --init-chapters：批量初始化章节大纲
    if args.init_chapters:
        vol_num = args.init_chapters
        if vol_num < 1 or vol_num > volumes:
            print(f"  [ERROR] 卷号 {vol_num} 超出范围（1-{volumes}）")
            sys.exit(1)

        chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
        print(f"\n[OUTLINE] 批量初始化卷{vol_num}的章节大纲（共 {chapters_per} 章）")
        print()

        created, skipped = init_volume_chapters(root, config, vol_num)

        if created:
            print(f"  [OK] 已创建 {len(created)} 个章节大纲：")
            for ch_num in created[:10]:
                print(f"       + OUTLINE/volume-{vol_num}/chapter-{ch_num:03d}.md")
            if len(created) > 10:
                print(f"       ... 还有 {len(created) - 10} 个")
        if skipped:
            print(f"  [--] 已跳过 {len(skipped)} 个已存在的章节")

        print()
        return

    if args.list or not args.target:
        show_outline_tree(root, config)

    if args.target:
        target = args.target.strip().lower()

        if target == 'meta':
            path = edit_meta_outline(root, config)
            print(f"  [OK] 已打开：{path}")
        elif target.startswith('卷'):
            num = int(target.replace('卷', '').strip())
            path = edit_volume_outline(root, config, num)
            print(f"  [OK] 已打开：{path}")
        elif '章' in target or target.isdigit():
            import re
            match = re.search(r'(\d+)', target)
            if match:
                num = int(match.group(1))
                path = edit_chapter_outline(root, config, num)
                print(f"  [OK] 已打开：{path}")

    print(f"\n  提示：直接用编辑器打开对应的 .md 文件进行编辑")
    print()

if __name__ == '__main__':
    main()
