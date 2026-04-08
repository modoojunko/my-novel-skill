#!/usr/bin/env python3
"""
story:write - 写作模式

提供任务驱动的写作执行功能。
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

def get_chapter_path(root, chapter_num, volume_num=None):
    """获取章节文件路径"""
    if volume_num is None:
        chapters_per = 30
        volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = root / 'CONTENT' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'
    return chapter_path, volume_num

def create_chapter_tasks(chapter_num):
    """创建章节写作任务"""
    tasks = f"""# 任务清单：第{chapter_num}章

## 写作前检查
- [ ] 回顾本章大纲
- [ ] 确认 POV 角色
- [ ] 列出本章关键场景

## 场景任务
- [ ] 场景 1：开场/设定
- [ ] 场景 2：发展
- [ ] 场景 3：转折/高潮

## 收尾任务
- [ ] 检查情节连贯性
- [ ] 添加过渡
- [ ] 初步自检（错字、语病）

## 预期字数
约 3000 字

---
*由 Novel Workflow 生成 @ {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    return tasks

def init_chapter(root, config, chapter_num):
    """初始化章节"""
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    vol_dir = root / 'CONTENT' / f'volume-{volume_num}'
    vol_dir.mkdir(parents=True, exist_ok=True)

    chapter_path = vol_dir / f'chapter-{chapter_num:03d}.md'
    tasks_path = vol_dir / f'chapter-{chapter_num:03d}.tasks.md'

    outline_path = root / 'OUTLINE' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'

    if not chapter_path.exists():
        content = f"""# 第{chapter_num}章：xxx

（在此开始写作...）

"""
        chapter_path.write_text(content, encoding='utf-8')

    if not tasks_path.exists():
        tasks_path.write_text(create_chapter_tasks(chapter_num), encoding='utf-8')

    config['progress']['current_chapter'] = chapter_num
    config['progress']['current_volume'] = volume_num
    if chapter_num not in config['progress']['written_chapters']:
        config['progress']['written_chapters'].append(chapter_num)
    save_config(root, config)

    return chapter_path, tasks_path, volume_num

def show_chapter_info(chapter_num, volume_num):
    """显示章节信息"""
    print(f"""
================================================================================
                    [WRITE] 写作模式：第{chapter_num}章
================================================================================
    """)

def show_guide():
    """显示写作指南"""
    print("""
[GUIDE] 写作指南：

1. 打开生成的 .md 文件开始写作
2. 参考 .tasks.md 中的任务清单
3. 可以参考 OUTLINE 目录下的章节大纲
4. 查阅 SPECS/ 了解人物和世界观设定

[TIPS] 提示：
- 写完后可以用 story:archive 归档
- 用 story:status 查看进度
- 用 story:define 管理设定
""")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='写作模式')
    parser.add_argument('chapter', nargs='?', type=int, help='章节号')
    parser.add_argument('--new', '-n', action='store_true', help='创建新章节')
    parser.add_argument('--continue', '-c', dest='continue_chapter', metavar='N',
                        help='继续写第 N 章')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  [ERROR] 未找到项目目录")
        sys.exit(1)

    config = load_config(root)

    chapter_num = args.chapter
    if not chapter_num:
        chapter_num = config['progress'].get('current_chapter', 0) + 1

    chapter_path, tasks_path, volume_num = init_chapter(root, config, chapter_num)

    show_chapter_info(chapter_num, volume_num)

    print(f"  [FILE] 章节文件：{chapter_path.relative_to(root)}")
    print(f"  [TASK] 任务清单：{tasks_path.relative_to(root)}")
    print(f"  [REF]  大纲参考：OUTLINE/volume-{volume_num}/chapter-{chapter_num:03d}.md")
    print(f"  [SPEC] 设定参考：SPECS/")
    print()

    outline_path = root / 'OUTLINE' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'
    if outline_path.exists():
        outline = outline_path.read_text(encoding='utf-8')
        print(f"  [PREVIEW] 本章大纲预览：")
        print('-' * 70)
        lines = outline.split('\n')[:20]
        for line in lines:
            if line.strip():
                print(f"  {line}")
        if len(outline.split('\n')) > 20:
            print(f"  ...")
        print('-' * 70)
        print()

    show_guide()

if __name__ == '__main__':
    main()
