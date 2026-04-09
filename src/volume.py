#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:volume - 卷管理

初始化/查看/管理小说卷结构。
使用 JSON 作为配置文件格式。
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from .paths import find_project_root, load_config, save_config, load_project_paths

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

def get_volume_info(config, volume_num):
    """从 config 中获取指定卷的名称和主题"""
    volume_titles = config.get('structure', {}).get('volume_titles', [])
    for vt in volume_titles:
        if vt.get('num') == volume_num:
            return vt.get('title', f'卷{volume_num}'), vt.get('theme', '')
    return f'卷{volume_num}', ''

def init_volume(root, config, volume_num, paths=None):
    """初始化单卷（创建目录和大纲文件）"""
    if paths is None:
        paths = load_project_paths(root)
    volumes = config.get('structure', {}).get('volumes', 1)
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    title, theme = get_volume_info(config, volume_num)

    created = []

    # 1. 创建 output_dir/volume-NNN/ 目录
    vol_content_dir = paths['output_dir'] / f'volume-{volume_num:03d}'
    if not vol_content_dir.exists():
        vol_content_dir.mkdir(parents=True, exist_ok=True)
        created.append(f'volume-{volume_num:03d}/')

    # 2. 创建 OUTLINE/volume-NNN/ 目录
    vol_outline_dir = root / 'OUTLINE' / f'volume-{volume_num:03d}'
    if not vol_outline_dir.exists():
        vol_outline_dir.mkdir(parents=True, exist_ok=True)
        created.append(f'OUTLINE/volume-{volume_num:03d}/')

    # 3. 创建 OUTLINE/volume-NNN.md 卷大纲文件
    vol_outline_path = root / 'OUTLINE' / f'volume-{volume_num:03d}.md'
    if not vol_outline_path.exists():
        chapters_content = []
        for i in range(1, chapters_per + 1):
            chapters_content.append(f"### 第{i}章：xxx")

        theme_str = f"{theme}" if theme else "（待填充）"
        vol_content = f"""# 第{volume_num}卷：{title}

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
        vol_outline_path.write_text(vol_content, encoding='utf-8')
        created.append(f'OUTLINE/volume-{volume_num:03d}.md')

    return created

def init_all_volumes(root, config, paths=None):
    """批量初始化所有卷，跳过已存在的"""
    if paths is None:
        paths = load_project_paths(root)
    volumes = config.get('structure', {}).get('volumes', 1)

    results = []
    for v in range(1, volumes + 1):
        created = init_volume(root, config, v, paths=paths)
        title, _ = get_volume_info(config, v)
        if created:
            results.append((v, title, created))
        else:
            results.append((v, title, []))

    return results

def show_volume_status(root, config, volume_num, paths=None):
    """显示单卷状态"""
    if paths is None:
        paths = load_project_paths(root)
    title, theme = get_volume_info(config, volume_num)
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)

    print(f"\n{'=' * 60}")
    print(f"  第{volume_num}卷：{c(title, Colors.BOLD)}")
    if theme:
        print(f"  主题：{theme}")
    print(f"{'=' * 60}")

    # 检查各部分状态
    vol_outline = root / 'OUTLINE' / f'volume-{volume_num:03d}.md'
    vol_outline_dir = root / 'OUTLINE' / f'volume-{volume_num:03d}'
    vol_content_dir = paths['output_dir'] / f'volume-{volume_num:03d}'

    outline_status = '[OK]' if vol_outline.exists() else '[  ]'
    outline_dir_status = '[OK]' if vol_outline_dir.exists() else '[  ]'
    content_status = '[OK]' if vol_content_dir.exists() else '[  ]'

    print(f"\n  目录/文件状态：")
    print(f"    {outline_status} OUTLINE/volume-{volume_num:03d}.md  卷大纲")
    print(f"    {outline_dir_status} OUTLINE/volume-{volume_num:03d}/      章节大纲目录")
    print(f"    {content_status} volume-{volume_num:03d}/      正文目录")

    # 统计章节大纲
    if vol_outline_dir.exists():
        chapter_outlines = list(vol_outline_dir.glob('chapter-*.md'))
        print(f"\n  章节大纲：{len(chapter_outlines)} / {chapters_per}")
        if chapter_outlines:
            for ch in sorted(chapter_outlines)[:10]:
                print(f"    [OK] {ch.name}")
            if len(chapter_outlines) > 10:
                print(f"    ... 还有 {len(chapter_outlines) - 10} 个")
    else:
        print(f"\n  章节大纲：0 / {chapters_per}")

    # 统计正文
    if vol_content_dir.exists():
        chapter_files = list(vol_content_dir.glob('chapter-*.md'))
        print(f"  正文文件：{len(chapter_files)}")
    else:
        print(f"  正文文件：0")

    print()

def show_all_volumes(root, config, paths=None):
    """显示所有卷概览"""
    if paths is None:
        paths = load_project_paths(root)
    volumes = config.get('structure', {}).get('volumes', 1)
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)

    print(f"\n{'=' * 70}")
    print(f"  {c('[VOLUME] 卷结构概览', Colors.BOLD)}")
    print(f"{'=' * 70}")
    print()
    print(f"  {'卷号':<6} {'名称':<16} {'主题':<24} {'大纲':<6} {'章纲':<8} {'正文':<6}")
    print(f"  {'-' * 6} {'-' * 16} {'-' * 24} {'-' * 6} {'-' * 8} {'-' * 6}")

    for v in range(1, volumes + 1):
        title, theme = get_volume_info(config, v)
        theme_display = theme[:22] + '..' if len(theme) > 24 else theme

        vol_outline = root / 'OUTLINE' / f'volume-{v:03d}.md'
        vol_outline_dir = root / 'OUTLINE' / f'volume-{v:03d}'
        vol_content_dir = paths['output_dir'] / f'volume-{v:03d}'

        outline_status = '[OK]' if vol_outline.exists() else '[  ]'
        content_status = '[OK]' if vol_content_dir.exists() else '[  ]'

        # 章节大纲数
        if vol_outline_dir.exists():
            ch_count = len(list(vol_outline_dir.glob('chapter-*.md')))
            ch_status = f'{ch_count}/{chapters_per}'
        else:
            ch_status = f'0/{chapters_per}'

        print(f"  卷{v:<4} {title:<16} {theme_display:<24} {outline_status:<6} {ch_status:<8} {content_status:<6}")

    print()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='卷管理')
    parser.add_argument('volume', nargs='?', type=int, help='卷号')
    parser.add_argument('--init', '-i', action='store_true', help='初始化指定卷')
    parser.add_argument('--init-all', action='store_true', help='初始化所有卷')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有卷状态')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  [ERROR] 未找到项目目录（请在包含 story.json 的目录下运行）")
        sys.exit(1)

    config = load_config(root)
    paths = load_project_paths(root)
    volumes = config.get('structure', {}).get('volumes', 1)

    # 默认行为：列出所有卷
    if not args.volume and not args.init_all:
        show_all_volumes(root, config, paths=paths)
        return

    # --init-all：批量初始化
    if args.init_all:
        print(f"\n[VOLUME] 批量初始化所有卷（共 {volumes} 卷）")
        print()

        results = init_all_volumes(root, config, paths=paths)
        for vol_num, title, created in results:
            if created:
                print(f"  [OK] 卷{vol_num}「{title}」已创建：")
                for item in created:
                    print(f"       + {item}")
            else:
                print(f"  [--] 卷{vol_num}「{title}」已存在，跳过")

        print()
        show_all_volumes(root, config, paths=paths)
        return

    # 指定卷号
    if args.volume:
        if args.volume < 1 or args.volume > volumes:
            print(f"  [ERROR] 卷号 {args.volume} 超出范围（1-{volumes}）")
            sys.exit(1)

        if args.init:
            # 初始化指定卷
            title, _ = get_volume_info(config, args.volume)
            created = init_volume(root, config, args.volume, paths=paths)
            if created:
                print(f"\n  [OK] 卷{args.volume}「{title}」已创建：")
                for item in created:
                    print(f"       + {item}")
            else:
                print(f"\n  [--] 卷{args.volume}「{title}」已存在，无需初始化")
            print()
        else:
            # 查看指定卷状态
            show_volume_status(root, config, args.volume, paths=paths)

if __name__ == '__main__':
    main()
