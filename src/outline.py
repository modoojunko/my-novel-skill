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

def expand_scene_outline(root, config, chapter_num, scene_num=None):
    """
    展开章节大纲中的场景细节。

    Args:
        chapter_num: 章节号
        scene_num: 场景序号（可选，不指定则显示所有场景）

    Returns:
        展开后的场景详情文本
    """
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = root / 'OUTLINE' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'

    if not chapter_path.exists():
        return None, f"章节大纲不存在: {chapter_path.name}"

    content = chapter_path.read_text(encoding='utf-8')

    # 解析场景列表
    # 格式: 1. [开场] 场景描述 - POV:xxx - 约800字
    scene_pattern = r'(\d+)\.\s*\[([^\]]+)\]\s*([^-]+?)\s*(?:-\s*(?:POV|POV人物):\s*([^\s-]+))?'
    scenes = []

    for match in re.finditer(scene_pattern, content):
        scene_idx = int(match.group(1))
        scene_type = match.group(2).strip()
        scene_desc = match.group(3).strip()
        pov = match.group(4).strip() if match.group(4) else ""

        scenes.append({
            'index': scene_idx,
            'type': scene_type,
            'description': scene_desc,
            'pov': pov
        })

    if not scenes:
        return None, "未找到场景列表，请确保大纲格式正确：\n  1. [开场] 场景描述 - POV:xxx"

    # 如果指定了场景号，过滤
    if scene_num is not None:
        scenes = [s for s in scenes if s['index'] == scene_num]
        if not scenes:
            return None, f"未找到第 {scene_num} 个场景"

    return scenes, None


def format_expanded_scene(scene: dict) -> str:
    """格式化展开后的场景详情"""
    lines = []
    lines.append(c('=' * 60, Colors.CYAN))
    lines.append(c(f'  场景 {scene["index"]}：{scene["description"]}', Colors.BOLD))
    lines.append(c('=' * 60, Colors.CYAN))
    lines.append('')

    lines.append(f"  {c('类型:', Colors.DIM)} {scene['type']}")
    if scene['pov']:
        lines.append(f"  {c('POV:', Colors.DIM)} {scene['pov']}")
    lines.append('')

    # 生成展开模板
    lines.append(c('  📝 展开模板', Colors.YELLOW))
    lines.append('  ' + '-' * 40)
    lines.append('')
    lines.append('  ** POV：{}'.format(scene['pov'] or '待定'))
    lines.append('')
    lines.append('  ** 地点：（待填充）')
    lines.append('  ** 时间：（待填充）')
    lines.append('  ** 预期字数：约 800-1500 字')
    lines.append('')
    lines.append('  ** 核心动作：')
    lines.append('     - （动作1）')
    lines.append('     - （动作2）')
    lines.append('     - （动作3）')
    lines.append('')
    lines.append('  ** 情绪基调：（待填充）')
    lines.append('')
    lines.append('  ** 可能需要的对话：')
    lines.append('     - （对话1）')
    lines.append('     - （对话2）')
    lines.append('')
    lines.append('  ** 关键细节：')
    lines.append('     - （细节1）')
    lines.append('     - （细节2）')
    lines.append('')
    lines.append('  ** 与上下文的衔接：')
    lines.append('     - 承接：（上一场景如何衔接）')
    lines.append('     - 铺垫：（为下一场景埋下什么）')
    lines.append('')

    return '\n'.join(lines)


def swap_chapter_outlines(root, config, chapter_a: int, chapter_b: int):
    """
    交换两个章节的大纲顺序。

    注意：只交换大纲文件，不移动实际的章节内容。
    """
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)

    def get_paths(chapter_num):
        vol_num = ((chapter_num - 1) // chapters_per) + 1
        outline_dir = root / 'OUTLINE' / f'volume-{vol_num}'
        return vol_num, outline_dir / f'chapter-{chapter_num:03d}.md'

    # 获取两个章节的路径
    vol_a, path_a = get_paths(chapter_a)
    vol_b, path_b = get_paths(chapter_b)

    # 检查文件是否存在
    if not path_a.exists():
        return False, f"第 {chapter_a} 章大纲不存在"
    if not path_b.exists():
        return False, f"第 {chapter_b} 章大纲不存在"

    # 读取内容
    content_a = path_a.read_text(encoding='utf-8')
    content_b = path_b.read_text(encoding='utf-8')

    # 交换内容，但保持章节编号不变
    # 注意：这里不改变文件名的编号，因为大纲的编号是固定的
    # 只是交换文件内容

    # 创建临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.md') as tmp:
        tmp_path = Path(tmp.name)

    try:
        # 备份 A -> 临时
        tmp_path.write_text(content_a, encoding='utf-8')
        # B -> A
        path_a.write_text(content_b, encoding='utf-8')
        # 临时 -> B
        path_b.write_text(tmp_path.read_text(encoding='utf-8'), encoding='utf-8')
    finally:
        # 删除临时文件
        if tmp_path.exists():
            tmp_path.unlink()

    return True, None


def show_expand_help():
    """显示 expand 功能帮助"""
    print("""
使用示例：
  story:outline --expand 5           # 展开第5章所有场景
  story:outline --expand 5 --scene 2 # 只展开第5章第2个场景

场景格式要求：
  章节大纲中需要包含场景列表，格式如下：
    1. [开场] 张三来到青云门 - POV:张三
    2. [发展] 张三遇见李四 - POV:李四

  格式说明：
    - 数字编号：场景序号
    - [类型]：开场/发展/高潮/结尾 等
    - 描述：场景的主要内容
    - POV：视点人物（可选）
""")


def show_swap_help():
    """显示 swap 功能帮助"""
    print("""
使用示例：
  story:outline --swap 8 10          # 交换第8章和第10章的大纲

注意：
  - 只交换大纲文件的内容，不移动实际的章节内容文件
  - 章节编号保持不变，只交换大纲中的具体计划
  - 交换前请确认操作
""")


def main():
    import argparse
    import re  # 添加 re 模块

    parser = argparse.ArgumentParser(description='编辑大纲')
    parser.add_argument('target', nargs='?', help='目标（meta/卷1/章节1）')
    parser.add_argument('--list', '-l', action='store_true', help='列出大纲结构')
    parser.add_argument('--init-chapters', type=int, metavar='VOLUME',
                        help='批量初始化指定卷的所有章节大纲')
    # 新增：expand 功能
    parser.add_argument('--expand', '-e', type=int, metavar='CHAPTER',
                        help='展开场景细节')
    parser.add_argument('--scene', '-s', type=int, metavar='N',
                        help='指定要展开的场景序号')
    # 新增：swap 功能
    parser.add_argument('--swap', nargs=2, type=int, metavar=('A', 'B'),
                        help='交换两个章节的大纲顺序')

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

    # --expand：展开场景细节
    if args.expand:
        chapter_num = args.expand
        scene_num = args.scene

        print(f"\n{c('[OUTLINE] 展开场景细节', Colors.CYAN)}")
        print(f"  {c('章节:', Colors.DIM)} 第{chapter_num}章")
        if scene_num:
            print(f"  {c('场景:', Colors.DIM)} 第{scene_num}个")
        print()

        scenes, error = expand_scene_outline(root, config, chapter_num, scene_num)

        if error:
            print(f"  {c(f'[错误] {error}', Colors.RED)}")
            show_expand_help()
            sys.exit(1)

        for scene in scenes:
            output = format_expanded_scene(scene)
            print(output)
        return

    # --swap：交换章节顺序
    if args.swap:
        chapter_a, chapter_b = args.swap

        print(f"\n{c('[OUTLINE] 交换章节大纲', Colors.CYAN)}")
        print(f"  {c('交换:', Colors.DIM)} 第{chapter_a}章 <-> 第{chapter_b}章")
        print()

        success, error = swap_chapter_outlines(root, config, chapter_a, chapter_b)

        if not success:
            print(f"  {c(f'[错误] {error}', Colors.RED)}")
            sys.exit(1)

        print(c(f"  ✅ 已交换第{chapter_a}章和第{chapter_b}章的大纲", Colors.GREEN))
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
