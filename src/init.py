#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:init - 初始化小说工作流项目

参考 OpenSpec init 命令，为小说创作提供标准化的项目结构。
使用 JSON 作为配置文件格式（无需额外依赖）。
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 颜色输出（使用 ASCII）
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

def welcome():
    print("""
+----------------------------------------------------+
|                                                    |
|              [INIT] Novel Workflow                 |
|                                                    |
|         从想法到成书的旅程                          |
|                                                    |
+----------------------------------------------------+
    """)

def input_with_default(prompt: str, default: str = "") -> str:
    """带默认值的输入"""
    if default:
        user_input = input(f"  {prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        return input(f"  {prompt}: ").strip()

def select_option(prompt: str, options: list) -> int:
    """选择菜单"""
    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        try:
            choice = int(input(f"  选择 [1-{len(options)}]: ").strip())
            if 1 <= choice <= len(options):
                return choice
        except ValueError:
            pass
        print(f"  {c('无效选择，请重新输入', Colors.RED)}")

def collect_basic_info() -> dict:
    """收集基本信息"""
    print(f"\n{c('[INFO] 基本信息', Colors.BOLD)}")
    print("-" * 50)

    info = {}

    # 书名
    info['title'] = input_with_default("书名")

    # 类型
    genre_options = ["玄幻", "都市", "科幻", "悬疑", "言情", "武侠", "历史", "游戏", "轻小说", "其他"]
    genre_idx = select_option("选择类型", genre_options)
    info['genre'] = genre_options[genre_idx - 1]

    # 目标字数
    target_words = input_with_default("目标字数（如：500000）", "500000")
    try:
        info['target_words'] = int(target_words)
    except ValueError:
        info['target_words'] = 500000

    # 结构
    volumes = input_with_default("计划卷数（如：3）", "3")
    try:
        info['volumes'] = int(volumes)
    except ValueError:
        info['volumes'] = 3

    chapters_per = input_with_default("每卷章节数（如：30）", "30")
    try:
        info['chapters_per_volume'] = int(chapters_per)
    except ValueError:
        info['chapters_per_volume'] = 30

    return info

def collect_volume_titles(volumes: int) -> list:
    """交互式收集每卷的名称和主题"""
    print(f"\n{c('[STRUCT] 卷结构', Colors.BOLD)}")
    print("-" * 50)
    print(f"  为每一卷命名（每个卷是一个独立故事弧，如「风起天南」「星海飞驰」）")
    print()

    volume_titles = []
    default_themes = ["起", "承", "转", "合", "续", "终"]
    for i in range(1, volumes + 1):
        dt = default_themes[(i - 1) % len(default_themes)]
        title = input_with_default(f"  卷{i} 名称", f"卷{i}")
        theme = input_with_default(f"  卷{i} 主题（一句话概括）", f"[{dt}] 待命名")
        volume_titles.append({
            "num": i,
            "title": title,
            "theme": theme
        })
        print()

    return volume_titles

def collect_story_concept() -> str:
    """收集故事概要"""
    print(f"\n{c('[LOG] 故事概要', Colors.BOLD)}")
    print("-" * 50)
    print("  简单描述你的故事（200字以内）：")
    print("  格式：一个___的___，在___中，必须___，否则___。")
    print()

    logline = input_with_default("故事概要")
    return logline

def collect_characters() -> list:
    """收集主要人物"""
    print(f"\n{c('[CHAR] 主要人物', Colors.BOLD)}")
    print("-" * 50)
    print("  至少添加一个主要人物（主角/重要配角）")
    print()

    characters = []
    while True:
        name = input_with_default(f"  人物 {len(characters) + 1} - 姓名（回车结束）")
        if not name:
            break

        char = {
            'name': name,
            'role': input_with_default(f"  {name} - 身份/职业"),
            'description': input_with_default(f"  {name} - 简短描述")
        }
        characters.append(char)
        print(f"  {c(f'+ 已添加：{name}', Colors.GREEN)}")

    return characters

def collect_world() -> str:
    """收集世界观"""
    print(f"\n{c('[WORLD] 世界观设定', Colors.BOLD)}")
    print("-" * 50)
    print("  简要描述故事背景（可选）")
    print()

    world = input_with_default("世界观/背景（跳过直接回车）")
    return world

def create_directory_structure(base_path: Path, volumes: int = 1):
    """创建目录结构"""
    print(f"\n{c('[DIR] 创建目录结构...', Colors.CYAN)}")

    dirs = [
        "SPECS/characters",
        "SPECS/world",
        "SPECS/meta",
        "OUTLINE",
        "CONTENT/draft",
        "ARCHIVE",
        "templates",
    ]

    # 按卷数创建 CONTENT/volume-N 目录
    for i in range(1, volumes + 1):
        dirs.append(f"CONTENT/volume-{i}")

    for d in dirs:
        full_path = base_path / d
        full_path.mkdir(parents=True, exist_ok=True)

    print(f"  {c('OK 目录结构创建完成', Colors.GREEN)}")

def create_config(base_path: Path, info: dict, logline: str, world: str, characters: list, volume_titles: list = None):
    """创建配置文件（JSON格式）"""
    print(f"\n{c('[CFG] 创建配置文件...', Colors.CYAN)}")

    # 构建 volume_titles，确保与卷数一致
    if volume_titles is None:
        volume_titles = []
        # 非交互模式下生成引导性默认值
        default_themes = ["起", "承", "转", "合", "续", "终"]
        for i in range(1, info['volumes'] + 1):
            dt = default_themes[(i - 1) % len(default_themes)]
            volume_titles.append({"num": i, "title": f"卷{i}", "theme": f"[{dt}] 待命名"})

    config = {
        "meta": {
            "version": "1.0",
            "created": datetime.now().strftime('%Y-%m-%d'),
            "updated": datetime.now().strftime('%Y-%m-%d'),
            "language": "zh-CN"
        },
        "book": {
            "title": info['title'],
            "author": os.environ.get('USER', 'Unknown'),
            "genre": info['genre'],
            "target_words": info['target_words'],
            "current_words": 0
        },
        "story": {
            "logline": logline,
            "world": world,
            "tone": "热血/成长"
        },
        "structure": {
            "volumes": info['volumes'],
            "chapters_per_volume": info['chapters_per_volume'],
            "volume_titles": volume_titles
        },
        "progress": {
            "current_volume": 1,
            "current_chapter": 0,
            "written_chapters": [],
            "archived_chapters": []
        },
        "specs": {
            "characters_dir": "SPECS/characters",
            "world_dir": "SPECS/world",
            "meta_dir": "SPECS/meta"
        },
        "paths": {
            "outline_dir": "OUTLINE",
            "content_dir": "CONTENT",
            "archive_dir": "ARCHIVE",
            "draft_dir": "CONTENT/draft",
            "templates_dir": "templates"
        },
        "style": {
            "pov": "third",
            "tense": "past",
            "tone": "serious"
        }
    }

    config_path = base_path / 'story.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"  {c('OK story.json', Colors.GREEN)}")

def create_story_concept(base_path: Path, logline: str, world: str):
    """创建故事概念文件"""
    concept_path = base_path / 'SPECS' / 'meta' / 'story-concept.md'

    content = f"""# 故事概念

## Logline
{logline}

## 核心主题
（待填充 - 如：复仇与成长、忠诚与背叛）

## 故事前提
（待填充 - 如果...那么...）

## 目标读者
（待填充）

## 参考作品
（待填充 - 喜欢的类似作品）

## 特殊规则
（待填充 - 如果有的话）
"""

    with open(concept_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  {c('OK SPECS/meta/story-concept.md', Colors.GREEN)}")

def create_character_files(base_path: Path, characters: list):
    """创建人物文件"""
    chars_dir = base_path / 'SPECS' / 'characters'

    for char in characters:
        filename = f"{char['name']}.md"
        filepath = chars_dir / filename

        content = f"""# {char['name']}

## 基本信息
- **身份/职业**: {char['role']}
- **状态**: 活跃

## 外貌
（待填充）

## 性格
（待填充）

## 背景故事
（待填充）

## 目标/动机
（待填充）

## 关键关系
（待填充）

## 发展轨迹
（待填充）
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  {c(f'OK SPECS/characters/{filename}', Colors.GREEN)}")

def create_outline_files(base_path: Path, info: dict, volume_titles: list = None):
    """创建大纲文件"""
    # meta.md - 总大纲
    meta_path = base_path / 'OUTLINE' / 'meta.md'
    volumes = info['volumes']
    chapters_per = info.get('chapters_per_volume', 30)

    # 构建 volume_titles，确保与卷数一致
    if volume_titles is None:
        volume_titles = []
        default_themes = ["起", "承", "转", "合", "续", "终"]
        for i in range(1, volumes + 1):
            dt = default_themes[(i - 1) % len(default_themes)]
            volume_titles.append({"num": i, "title": f"卷{i}", "theme": f"[{dt}] 待命名"})

    volumes_content = []
    for vt in volume_titles:
        title = vt.get('title', f"第{vt['num']}卷")
        theme = vt.get('theme', '')
        theme_str = f"：{theme}" if theme else ""
        volumes_content.append(f"## {title}{theme_str}")

    meta_content = f"""# 总大纲

## 故事概览
{info.get('logline', '(见 story-concept.md)')}

## 卷结构

{chr(10).join(volumes_content)}

## 主题线索
（待填充）

## 伏笔记录
（待填充）
"""

    with open(meta_path, 'w', encoding='utf-8') as f:
        f.write(meta_content)

    print(f"  {c('OK OUTLINE/meta.md', Colors.GREEN)}")

    # 为每一卷创建大纲文件
    for vt in volume_titles:
        vol_num = vt['num']
        title = vt.get('title', f"第{vol_num}卷")
        theme = vt.get('theme', '')

        vol_path = base_path / 'OUTLINE' / f'volume-{vol_num}.md'

        chapters_content = []
        for i in range(1, chapters_per + 1):
            chapters_content.append(f"### 第{i}章：xxx")

        theme_str = f"{theme}" if theme else "（待填充）"
        vol_content = f"""# 第{vol_num}卷：{title}

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

        with open(vol_path, 'w', encoding='utf-8') as f:
            f.write(vol_content)

        print(f"  {c(f'OK OUTLINE/volume-{vol_num}.md', Colors.GREEN)}")

def create_templates(base_path: Path):
    """创建模板文件"""
    templates_dir = base_path / 'templates'

    # 章节模板
    chapter_template = templates_dir / 'chapter.md'
    chapter_template.write_text("""# 第X章：章标题

## 本章目标
（待填充）

## POV角色
（待填充）

## 场景列表
1. 场景1
2. 场景2

## 情节点
（待填充）

## 关键对话
（待填充）

## 本章字数：约 3000 字
""", encoding='utf-8')

    # 人物模板
    character_template = templates_dir / 'character.md'
    character_template.write_text("""# 角色名

## 基本信息
- **身份/职业**:
- **年龄**:
- **状态**: 活跃/死亡/退场

## 外貌
（待填充）

## 性格
（待填充）

## 背景故事
（待填充）

## 目标/动机
（待填充）

## 关键关系
（待填充）

## 角色弧
（待填充）

## 标志性特征
（待填充）
""", encoding='utf-8')

    # 场景模板
    scene_template = templates_dir / 'scene.md'
    scene_template.write_text("""# 场景标题

## 基本信息
- **POV**:
- **地点**:
- **时间**:

## 场景类型
（对话/动作/内心独白/混合）

## 参与者
（待填充）

## 场景目标
（待填充）

## 情绪曲线
（待填充）

## 关键细节
（待填充）

## 本场景字数：约 xxx 字
""", encoding='utf-8')

    # 大纲模板
    outline_template = templates_dir / 'outline.md'
    outline_template.write_text("""# 大纲模板

## 章节/卷标题

### 核心事件
（待填充）

### 转折点
（待填充）

### 伏笔/呼应
（待填充）

### 预期字数
（待填充）
""", encoding='utf-8')

    print(f"  {c('OK templates/*.md', Colors.GREEN)}")

def create_readme(base_path: Path, info: dict):
    """创建项目 README"""
    readme_path = base_path / 'README.md'

    readme_content = f"""# {info['title']}

## 故事概要
{info.get('logline', '(见 SPECS/meta/story-concept.md)')}

## 基本信息
- **类型**: {info['genre']}
- **目标字数**: {info['target_words']:,}
- **卷数**: {info['volumes']}
- **每卷章节数**: {info['chapters_per_volume']}

## 目录
- [设定库](SPECS/) - 人物、世界观等
- [大纲](OUTLINE/) - 故事结构
- [正文](CONTENT/) - 小说正文
- [归档](ARCHIVE/) - 已完成章节

## 进度
- 当前字数：0 / {info['target_words']:,}
- 完成度：0%

## 写作风格
- 视角：第三人称
- 时态：过去时
- 基调：待定

---
*由 Novel Workflow 生成*
"""

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"  {c('OK README.md', Colors.GREEN)}")

def create_gitignore(base_path: Path):
    """创建 .gitignore"""
    gitignore_path = base_path / '.gitignore'
    gitignore_content = """# 草稿和临时文件
*.draft
*.tmp
*.bak

# 编辑器
.vscode/
.idea/

# 系统文件
.DS_Store
Thumbs.db
"""

    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)

    print(f"  {c('OK .gitignore', Colors.GREEN)}")

def show_success(base_path: Path, info: dict):
    """显示成功信息"""
    print(f"""
+----------------------------------------------------+
|                                                    |
|          [OK] 初始化完成！                         |
|                                                    |
+----------------------------------------------------+

  项目：{c(info['title'], Colors.BOLD)}
  位置：{base_path}

  目录结构：
  -- SPECS/          设定库
  |   -- characters/ 人物设定
  |   -- world/     世界观
  |   -- meta/      故事概念
  -- OUTLINE/        大纲
  -- CONTENT/        正文
  -- ARCHIVE/        归档
  -- story.json      配置文件

  下一步：
    python story.py propose    创建创作意图
    python story.py outline    编辑大纲
    python story.py write      开始写作
    python story.py status     查看状态

""")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='初始化小说工作流项目')
    parser.add_argument('path', nargs='?', default='.', help='项目目录（默认当前目录）')
    parser.add_argument('--title', help='书名')
    parser.add_argument('--genre', help='类型')
    parser.add_argument('--words', type=int, help='目标字数')
    parser.add_argument('--volumes', type=int, help='卷数')
    parser.add_argument('--logline', help='故事概要')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式')

    args = parser.parse_args()

    # 确定项目路径
    base_path = Path(args.path).resolve()

    # 检查是否已初始化
    config_file = base_path / 'story.json'
    if config_file.exists():
        print(f"  {c('WARNING: 项目已初始化（发现 story.json）', Colors.YELLOW)}")
        response = input(f"  重新初始化将覆盖配置，是否继续？ [y/N]: ").strip().lower()
        if response != 'y':
            print("  取消初始化")
            sys.exit(0)

    welcome()

    # 收集信息
    if args.non_interactive:
        info = {
            'title': args.title or '我的小说',
            'genre': args.genre or '玄幻',
            'target_words': args.words or 500000,
            'volumes': args.volumes or 3,
            'chapters_per_volume': 30,
            'logline': args.logline or ''
        }
        logline = args.logline or ''
        characters = []
        world = ''
        volume_titles = None  # 将在 create_config 中生成默认值
    else:
        info = collect_basic_info()
        logline = collect_story_concept()
        info['logline'] = logline
        characters = collect_characters()
        world = collect_world()
        volume_titles = collect_volume_titles(info['volumes'])

    create_directory_structure(base_path, info['volumes'])
    create_config(base_path, info, logline, world, characters, volume_titles)
    create_story_concept(base_path, logline, world)
    create_character_files(base_path, characters)
    create_outline_files(base_path, info, volume_titles)
    create_templates(base_path)
    create_readme(base_path, info)
    create_gitignore(base_path)

    show_success(base_path, info)

if __name__ == '__main__':
    main()
