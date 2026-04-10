#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:define - 设定库管理

管理人物卡和世界观设定。

使用 JSON 作为配置文件格式（兼容 Obsidian 双向链接）。
"""

import os
import sys
import json
import argparse
from pathlib import Path
from .paths import load_project_paths
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
    """确保设定目录存在"""
    chars_dir = root / 'SPECS' / 'characters'
    world_dir = root / 'SPECS' / 'world'
    chars_dir.mkdir(parents=True, exist_ok=True)
    world_dir.mkdir(parents=True, exist_ok=True)
    return chars_dir, world_dir


# ============================================================================
# 人物卡模板和操作
# ============================================================================

CHARACTER_TEMPLATE = """---
name: {name}
alias: {alias}
gender: {gender}
age: {age}
occupation: {occupation}
status: {status}
tags: [{tags}]
created: {created}
modified: {modified}
---

# {name}

<!-- USER-CORE:START -->

## 基本信息

**别名/昵称**：{alias}
**性别**：{gender}
**年龄**：{age}
**职业/身份**：{occupation}
**状态**：{status}

## 外观特征（核心）

（简要描述外貌、穿着、标志性特征等核心要点）

## 性格特点（核心）

- **核心性格**：（如：冷静、果断、外冷内热）
- **优点**：（如：善于观察、行动力强）
- **缺点**：（如：不善表达、过于理性）
- **口头禅/习惯**：（如有）

## 背景故事（核心）

（人物的关键前史、成长转折点、为什么会成为现在的样子）

## 六层认知（核心）

> 角色的深层驱动力，决定其在剧情中的抉择、情绪和说话方式。

### 我的世界观

（这个角色对世界的根本看法。如：正派相信正义终将战胜邪恶、宿命论者认为一切早已注定、犬儒主义者觉得世界本质是残酷的）

### 我对自己定义

（我是个什么样的人。如：我是个普通但靠谱的人、我注定要成为王、我不过是个逃兵）

### 我的价值观

（在艰难决策上的取舍优先级。如：他人感受 > 真相 > 自己、家族荣耀 > 个人幸福、生存 > 道德）

### 我的能力

（角色解决问题的方式和核心能力。如：倾听与共情、洞察人心、过目不忘）

### 我的技能

（角色掌握的具体技能。如：整理货架、泡方便面、剑术、编程）

### 我的环境

（角色所处的物理和社会环境。如：深夜便利店、贵族学院、战场前线）

## 人物关系（核心）

- **家人**：（如有）
- **挚友**：（如有）
- **对手/敌人**：（如有）
- **其他重要关系**：（如有）

## 角色弧（核心）

**起点**：（角色的初始状态/问题）
**转折点**：（经历什么事件发生改变）
**终点**：（角色最终的成长/变化）

## 本卷/本故事中的目标

（当前故事中角色想要达成的目标）

## 重要情节线

- （与该角色相关的重要事件/冲突）

<!-- USER-CORE:END -->

<!-- AI-EXPAND:START -->

（AI 基于 USER-CORE 的核心信息，在此处展开详细描述）

## 外观特征（详细）

### 整体形象

### 面部特征

### 穿着打扮

### 标志性细节

## 性格特点（详细）

### 日常表现

### 压力下的反应

### 成长变化

## 背景故事（详细）

### 童年经历

### 关键事件

### 对现在的影响

## 六层认知（详细）

### 我的世界观 - 详细说明

### 我对自己定义 - 详细说明

### 我的价值观 - 详细说明

### 我的能力 - 详细说明

### 我的技能 - 详细说明

### 我的环境 - 详细说明

## 人物关系（详细）

### 关系深度分析

### 互动模式

### 潜在冲突

## 角色弧（详细）

### 起点状态详解

### 转折点设计

### 终点成长体现

<!-- AI-EXPAND:END -->

---

*由 Novel Workflow 生成*
"""

CHARACTER_FIELDS = [
    ('name', '姓名', 'text'),
    ('alias', '别名/昵称', 'text'),
    ('gender', '性别', 'select', ['男', '女', '其他', '未知']),
    ('age', '年龄', 'text'),
    ('occupation', '职业/身份', 'text'),
    ('status', '状态', 'select', ['存活', '死亡', '失踪', '未知']),
    ('tags', '标签（逗号分隔）', 'text'),
]


def create_character_template(name: str) -> str:
    """创建人物卡模板"""
    now = datetime.now().strftime('%Y-%m-%d')
    return CHARACTER_TEMPLATE.format(
        name=name,
        alias='（待填写）',
        gender='未知',
        age='（待填写）',
        occupation='（待填写）',
        status='存活',
        tags=name,
        created=now,
        modified=now,
    )


def list_characters(chars_dir: Path):
    """列出所有人物"""
    md_files = sorted(chars_dir.glob('*.md'))
    if not md_files:
        print(f"  {c('[INFO] 暂无人物设定', Colors.DIM)}")
        print(f"  使用 'story:define character <姓名>' 创建新人物")
        return []

    print(f"\n{c('=' * 50, Colors.CYAN)}")
    print(c(f"  人物列表（共 {len(md_files)} 人）", Colors.BOLD))
    print(c('=' * 50, Colors.CYAN))

    characters = []
    for char_file in md_files:
        char = parse_character_frontmatter(char_file)
        status_icon = '🟢' if char.get('status') == '存活' else '🔴'
        tags = char.get('tags', [])
        if isinstance(tags, list):
            tags_str = ', '.join(tags)
        else:
            tags_str = str(tags)
        print(f"\n  {status_icon} {c(char.get('name', char_file.stem), Colors.GREEN)}")
        if char.get('alias'):
            print(f"     别名：{char.get('alias')}")
        if char.get('occupation'):
            print(f"     职业：{char.get('occupation')}")
        if char.get('gender') and char.get('age'):
            print(f"     {char.get('gender')} / {char.get('age')}岁")
        if tags_str and tags_str != char.get('name', ''):
            print(f"     标签：{c(tags_str, Colors.DIM)}")
        characters.append(char)

    print(f"\n{c('-' * 50, Colors.DIM)}")
    return characters


def parse_character_frontmatter(char_file: Path) -> dict:
    """解析人物卡 frontmatter"""
    content = char_file.read_text(encoding='utf-8')
    char = {'name': char_file.stem, 'file': char_file}

    # 解析 frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            for line in fm_text.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'tags':
                        # 解析 tags: [a, b, c]
                        value = value.strip('[]')
                        char[key] = [t.strip() for t in value.split(',') if t.strip()]
                    else:
                        char[key] = value

    return char


def view_character(chars_dir: Path, name: str):
    """查看人物详情"""
    char_file = chars_dir / f'{name}.md'
    if not char_file.exists():
        print(f"  {c(f'[ERROR] 人物不存在：{name}', Colors.RED)}")
        print(f"  使用 'story:define character --list' 查看所有人物")
        return None

    content = char_file.read_text(encoding='utf-8')
    print(f"\n{c('=' * 60, Colors.GREEN)}")
    print(c(f"  人物卡：{name}", Colors.BOLD + Colors.GREEN))
    print(c('=' * 60, Colors.GREEN))

    # 解析 frontmatter 显示关键信息
    char = parse_character_frontmatter(char_file)
    print(f"\n  {c('【基本信息】', Colors.CYAN)}")
    print(f"  姓名：{char.get('name', name)}")
    if char.get('alias'):
        print(f"  别名：{char.get('alias')}")
    if char.get('gender'):
        print(f"  性别：{char.get('gender')}")
    if char.get('age'):
        print(f"  年龄：{char.get('age')}")
    if char.get('occupation'):
        print(f"  职业：{char.get('occupation')}")
    if char.get('status'):
        status_color = Colors.GREEN if char.get('status') == '存活' else Colors.RED
        print(f"  状态：{c(char.get('status'), status_color)}")

    # 显示正文内容（跳过 frontmatter 和标题）
    lines = content.split('\n')
    in_frontmatter = False
    content_lines = []
    skip_title = True

    for line in lines:
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if skip_title and line.startswith('#'):
            skip_title = False
            continue
        if line.strip():
            content_lines.append(line)

    if content_lines:
        print(f"\n  {c('【详细内容】', Colors.CYAN)}")
        print('-' * 60)
        for line in content_lines[:50]:
            print(f"  {line}")
        if len(content_lines) > 50:
            print(f"\n  {c('...（更多内容请查看文件）', Colors.DIM)}")

    print(f"\n  {c('文件路径：', Colors.DIM)}{char_file}")
    return char


def edit_character(chars_dir: Path, name: str):
    """编辑人物卡"""
    char_file = chars_dir / f'{name}.md'

    if not char_file.exists():
        print(f"  {c(f'[ERROR] 人物不存在：{name}', Colors.RED)}")
        print(f"  使用 'story:define character {name}' 创建新人物")
        return False

    # 打开编辑器
    editor = os.environ.get('EDITOR', 'notepad' if sys.platform == 'win32' else 'nano')
    os.system(f'"{editor}" "{char_file}"')
    return True


def delete_character(chars_dir: Path, name: str, force: bool = False, paths: dict = None):
    """删除人物卡"""
    if paths is None:
        # 从 chars_dir 推导 root
        root = chars_dir.parent.parent  # chars_dir = SPECS/characters, root = project_root
        paths = load_project_paths(root)
    char_file = chars_dir / f'{name}.md'
    if not char_file.exists():
        print(f"  {c(f'[ERROR] 人物不存在：{name}', Colors.RED)}")
        return False

    # 确认删除（--force 跳过）
    if not force:
        print(f"\n  {c('[警告] 此操作不可恢复！', Colors.RED)}")
        confirm = input(f"  确认删除人物「{name}」？(y/N): ").strip().lower()
        if confirm != 'y':
            print("  已取消")
            return False

    # 备份后删除
    backup_dir = paths['archive'] / 'deleted'
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'{name}_{timestamp}.md'
    char_file.rename(backup_file)

    print(f"  {c('[OK] 已删除', Colors.GREEN)}")
    print(f"  备份位置：{backup_file}")
    return True


# 六层认知引导问题
COGNITION_LAYERS = [
    ('worldview', '我的世界观', '这个角色对世界的根本看法',
     ['正派相信正义终将战胜邪恶', '宿命论者认为一切早已注定',
      '犬儒主义者觉得世界本质是残酷的', '实用主义者相信适者生存']),
    ('self_definition', '我对自己定义', '我是个什么样的人',
     ['我是个普通但靠谱的人', '我注定要成为王', '我不过是个逃兵',
      '我是被选中的人']),
    ('values', '我的价值观', '在艰难决策上的取舍优先级',
     ['他人感受 > 真相 > 自己', '家族荣耀 > 个人幸福',
      '生存 > 道德', '自由 > 安全']),
    ('ability', '我的能力', '角色解决问题的方式和核心能力',
     ['倾听与共情——能让人感到被理解', '洞察人心——知道什么时候该说什么话',
      '过目不忘——信息就是武器', '坚韧不拔——靠意志力扛过一切']),
    ('skill', '我的技能', '角色掌握的具体技能',
     ['整理货架、泡方便面', '剑术、骑术',
      '编程、数据分析', '察言观色、谈判']),
    ('environment', '我的环境', '角色所处的物理和社会环境',
     ['深夜便利店——孤独但安全', '贵族学院——充满竞争和偏见',
      '战场前线——生死一瞬', '小城镇——人人相识，没有秘密']),
]


def collect_cognition_interactive(name: str, cognition: dict = None) -> dict:
    """收集六层认知（交互式或预填）

    Args:
        name: 角色名
        cognition: 预填的认知数据，有值时跳过交互直接使用
    """
    # 非交互模式：直接使用传入的 cognition
    if cognition:
        # 补全缺失字段
        for key, title, desc, examples in COGNITION_LAYERS:
            if key not in cognition or not cognition[key]:
                cognition[key] = '（待填写）'
        return cognition

    # 交互模式
    print(f"\n  {c('═══ 六层认知设定 ═══', Colors.BOLD + Colors.CYAN)}")
    print(f"  为「{name}」填充深层驱动力，让角色活起来。")
    print(f"  {c('（直接回车跳过，后续可编辑文件补充）', Colors.DIM)}")
    print()

    cognition = {}
    for key, title, desc, examples in COGNITION_LAYERS:
        print(f"  {c(f'【{title}】', Colors.YELLOW)}")
        print(f"  {c(desc, Colors.DIM)}")
        if examples:
            print(f"  {c('示例：', Colors.DIM)}")
            for ex in examples[:3]:
                print(f"    {c('•', Colors.DIM)} {ex}")
        value = input(f"\n  {title}：").strip()
        cognition[key] = value if value else '（待填写）'
        print()

    return cognition


def apply_cognition_to_template(content: str, cognition: dict) -> str:
    """将六层认知数据填入模板"""
    for key, value in cognition.items():
        # 替换模板中的占位内容
        # 每个认知层有对应的"（待填写）"提示
        patterns = {
            'worldview': '（这个角色对世界的根本看法。',
            'self_definition': '（我是个什么样的人。',
            'values': '（在艰难决策上的取舍优先级。',
            'ability': '（角色解决问题的方式和核心能力。',
            'skill': '（角色掌握的具体技能。',
            'environment': '（角色所处的物理和社会环境。',
        }
        if key in patterns and value != '（待填写）':
            # 找到对应的段落并替换
            old_text = patterns[key]
            if old_text in content:
                # 替换整个括号内容
                content = content.replace(old_text, value, 1)

    return content


def create_character(chars_dir: Path, name: str, cognition_mode: bool = True, cognition: dict = None):
    """创建新人物卡"""
    char_file = chars_dir / f'{name}.md'

    if char_file.exists():
        print(f"  {c(f'[ERROR] 人物已存在：{name}', Colors.RED)}")
        print(f"  使用 'story:define character {name} --view' 查看")
        print(f"  使用 'story:define character {name} --edit' 编辑")
        return False

    # 创建模板
    content = create_character_template(name)

    # 收集六层认知（有预填数据时跳过交互，无 cognition_mode 时跳过）
    if cognition_mode or cognition:
        try:
            cognition_data = collect_cognition_interactive(name, cognition=cognition)
            content = apply_cognition_to_template(content, cognition_data)
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {c('[INFO] 跳过六层认知，可后续编辑补充', Colors.DIM)}")

    char_file.write_text(content, encoding='utf-8')

    print(f"  {c('[OK] 人物卡已创建', Colors.GREEN)}")
    print(f"  文件：{char_file}")
    print(f"\n  {c('[下一步]', Colors.YELLOW)}")
    print(f"  1. 编辑人物卡：story:define character {name} --edit")
    print(f"  2. 查看人物卡：story:define character {name} --view")
    print(f"  3. 补充六层认知：编辑文件中的「六层认知」章节")
    print(f"  4. 在写作时，SPECS/characters/{name}.md 将自动加载到上下文")
    return True


# ============================================================================
# 世界观模板和操作
# ============================================================================

WORLD_TEMPLATE = """---
name: {name}
category: {category}
tags: [{tags}]
created: {created}
modified: {modified}
---

# {name}

## 类别

{category}

<!-- USER-CORE:START -->

## 概述（核心）

（简要描述这个世界观元素的核心要点）

## 核心设定

（关键设定内容，用 bullet points 列出）

-
-
-

## 规则/限制（核心）

（如有特殊的规则或限制的核心要点）

## 与其他设定的关联（核心）

- （关联的人物/世界观元素）

<!-- USER-CORE:END -->

<!-- AI-EXPAND:START -->

（AI 基于 USER-CORE 的核心信息，在此处展开详细描述）

## 概述（详细）

### 背景起源

### 在世界中的位置

### 重要性和影响

## 核心设定（详细展开）

### 设定一详解

### 设定二详解

### 设定三详解

## 规则/限制（详细）

### 具体规则

### 例外情况

### 违反后果

## 与其他设定的关联（详细）

### 关系深度

### 相互影响

### 潜在冲突

## 历史演变

### 起源

### 发展历程

### 现状

## 实例/案例

### 典型例子

### 特殊案例

<!-- AI-EXPAND:END -->

---

*由 Novel Workflow 生成*
"""

WORLD_CATEGORIES = [
    ('地理', '地理位置、地形、气候等'),
    ('历史', '历史事件、时间线、文明发展'),
    ('社会', '社会结构、制度、文化习俗'),
    ('魔法/能力', '魔法体系、超能力设定'),
    ('科技', '科技水平、特殊技术'),
    ('生物', '种族、怪物、特殊生物'),
    ('物品', '重要道具、武器、神器'),
    ('组织', '势力、门派、机构'),
    ('其他', '其他类型的设定'),
]

WORLD_FIELDS = [
    ('name', '名称', 'text'),
    ('category', '类别', 'select'),
    ('tags', '标签（逗号分隔）', 'text'),
]


def create_world_template(name: str, category: str = '其他') -> str:
    """创建世界观条目模板"""
    now = datetime.now().strftime('%Y-%m-%d')
    return WORLD_TEMPLATE.format(
        name=name,
        category=category,
        tags=name,
        created=now,
        modified=now,
    )


def list_world(world_dir: Path):
    """列出所有世界观设定"""
    md_files = sorted(world_dir.glob('*.md'))
    if not md_files:
        print(f"  {c('[INFO] 暂无世界观设定', Colors.DIM)}")
        print(f"  使用 'story:define world <名称>' 创建新设定")
        return []

    print(f"\n{c('=' * 50, Colors.CYAN)}")
    print(c(f"  世界观设定列表（共 {len(md_files)} 项）", Colors.BOLD))
    print(c('=' * 50, Colors.CYAN))

    # 按类别分组
    categories = {}
    for world_file in md_files:
        world = parse_world_frontmatter(world_file)
        cat = world.get('category', '其他')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(world)

    for cat, items in sorted(categories.items()):
        print(f"\n  {c(f'【{cat}】', Colors.YELLOW)}")
        for world in items:
            print(f"    • {c(world.get('name', world['file'].stem), Colors.GREEN)}")

    print(f"\n{c('-' * 50, Colors.DIM)}")
    return md_files


def parse_world_frontmatter(world_file: Path) -> dict:
    """解析世界观条目 frontmatter"""
    content = world_file.read_text(encoding='utf-8')
    world = {'name': world_file.stem, 'file': world_file}

    # 解析 frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            for line in fm_text.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'tags':
                        value = value.strip('[]')
                        world[key] = [t.strip() for t in value.split(',') if t.strip()]
                    else:
                        world[key] = value

    return world


def view_world(world_dir: Path, name: str):
    """查看世界观条目详情"""
    world_file = world_dir / f'{name}.md'
    if not world_file.exists():
        print(f"  {c(f'[ERROR] 设定不存在：{name}', Colors.RED)}")
        print(f"  使用 'story:define world --list' 查看所有设定")
        return None

    content = world_file.read_text(encoding='utf-8')
    print(f"\n{c('=' * 60, Colors.GREEN)}")
    print(c(f"  世界观设定：{name}", Colors.BOLD + Colors.GREEN))
    print(c('=' * 60, Colors.GREEN))

    # 解析 frontmatter 显示关键信息
    world = parse_world_frontmatter(world_file)
    print(f"\n  {c('【基本信息】', Colors.CYAN)}")
    print(f"  名称：{world.get('name', name)}")
    if world.get('category'):
        print(f"  类别：{world.get('category')}")
    tags = world.get('tags', [])
    if isinstance(tags, list):
        tags_str = ', '.join(tags)
    else:
        tags_str = str(tags)
    if tags_str:
        print(f"  标签：{tags_str}")

    # 显示正文内容
    lines = content.split('\n')
    in_frontmatter = False
    content_lines = []
    skip_title = True

    for line in lines:
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if skip_title and line.startswith('#'):
            skip_title = False
            continue
        if line.strip():
            content_lines.append(line)

    if content_lines:
        print(f"\n  {c('【详细内容】', Colors.CYAN)}")
        print('-' * 60)
        for line in content_lines[:50]:
            print(f"  {line}")
        if len(content_lines) > 50:
            print(f"\n  {c('...（更多内容请查看文件）', Colors.DIM)}")

    print(f"\n  {c('文件路径：', Colors.DIM)}{world_file}")
    return world


def edit_world(world_dir: Path, name: str):
    """编辑世界观条目"""
    world_file = world_dir / f'{name}.md'

    if not world_file.exists():
        print(f"  {c(f'[ERROR] 设定不存在：{name}', Colors.RED)}")
        print(f"  使用 'story:define world {name}' 创建新设定")
        return False

    editor = os.environ.get('EDITOR', 'notepad' if sys.platform == 'win32' else 'nano')
    os.system(f'"{editor}" "{world_file}"')
    return True


def delete_world(world_dir: Path, name: str, force: bool = False, paths: dict = None):
    """删除世界观条目"""
    if paths is None:
        root = world_dir.parent.parent  # world_dir = SPECS/world, root = project_root
        paths = load_project_paths(root)
    world_file = world_dir / f'{name}.md'
    if not world_file.exists():
        print(f"  {c(f'[ERROR] 设定不存在：{name}', Colors.RED)}")
        return False

    # 确认删除（--force 跳过）
    if not force:
        print(f"\n  {c('[警告] 此操作不可恢复！', Colors.RED)}")
        confirm = input(f"  确认删除设定「{name}」？(y/N): ").strip().lower()
        if confirm != 'y':
            print("  已取消")
            return False

    backup_dir = paths['archive'] / 'deleted'
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'{name}_{timestamp}.md'
    world_file.rename(backup_file)

    print(f"  {c('[OK] 已删除', Colors.GREEN)}")
    print(f"  备份位置：{backup_file}")
    return True


def create_world(world_dir: Path, name: str, category: str = None):
    """创建新的世界观条目"""
    world_file = world_dir / f'{name}.md'

    if world_file.exists():
        print(f"  {c(f'[ERROR] 设定已存在：{name}', Colors.RED)}")
        print(f"  使用 'story:define world {name} --view' 查看")
        print(f"  使用 'story:define world {name} --edit' 编辑")
        return False

    # 选择类别（有 --category 参数时跳过交互）
    if category:
        # 验证类别是否合法
        valid_cats = [cat for cat, _ in WORLD_CATEGORIES]
        if category not in valid_cats:
            print(f"  {c(f'[WARN] 类别「{category}」不在预设列表中，仍将使用', Colors.YELLOW)}")
    else:
        print("\n  请选择类别：")
        for i, (cat, desc) in enumerate(WORLD_CATEGORIES, 1):
            print(f"    {i}. {cat} - {desc}")
        print()

        while True:
            try:
                choice = input("  选择类别 [1-9，默认 9 其他]: ").strip()
                if not choice:
                    category = '其他'
                    break
                idx = int(choice) - 1
                if 0 <= idx < len(WORLD_CATEGORIES):
                    category = WORLD_CATEGORIES[idx][0]
                    break
                print(f"  {c('[ERROR] 无效选择，请重新输入', Colors.RED)}")
            except ValueError:
                print(f"  {c('[ERROR] 请输入数字', Colors.RED)}")

    # 创建模板
    content = create_world_template(name, category)
    world_file.write_text(content, encoding='utf-8')

    print(f"\n  {c('[OK] 世界观设定已创建', Colors.GREEN)}")
    print(f"  文件：{world_file}")
    print(f"\n  {c('[下一步]', Colors.YELLOW)}")
    print(f"  1. 编辑设定：story:define world {name} --edit")
    print(f"  2. 查看设定：story:define world {name} --view")
    print(f"  3. 在写作时，SPECS/world/{name}.md 将自动加载到上下文")
    return True


# ============================================================================
# 搜索功能
# ============================================================================

def search_specs(chars_dir: Path, world_dir: Path, query: str):
    """搜索设定"""
    results = []

    # 搜索人物
    for char_file in chars_dir.glob('*.md'):
        if query.lower() in char_file.stem.lower():
            results.append(('character', char_file.stem))
        else:
            content = char_file.read_text(encoding='utf-8')
            if query.lower() in content.lower():
                results.append(('character', char_file.stem))

    # 搜索世界观
    for world_file in world_dir.glob('*.md'):
        if query.lower() in world_file.stem.lower():
            results.append(('world', world_file.stem))
        else:
            content = world_file.read_text(encoding='utf-8')
            if query.lower() in content.lower():
                results.append(('world', world_file.stem))

    if not results:
        print(f"\n  {c('[INFO] 未找到包含「{query}」的设定', Colors.DIM)}")
        return

    print(f"\n{c('=' * 50, Colors.CYAN)}")
    print(c(f"  搜索结果：{query}（共 {len(results)} 项）", Colors.BOLD))
    print(c('=' * 50, Colors.CYAN))

    for type_, name in results:
        type_label = '👤 人物' if type_ == 'character' else '🌍 世界观'
        print(f"\n  {type_label}：{c(name, Colors.GREEN)}")


# ============================================================================
# 主函数
# ============================================================================

root = None  # 全局变量，用于 delete 函数

def main():
    global root

    parser = argparse.ArgumentParser(
        description='设定库管理 - 人物卡和世界观设定',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 人物管理
  story:define character --list              # 列出所有人物
  story:define character 张三 --view          # 查看人物详情
  story:define character 张三 --edit          # 编辑人物
  story:define character 张三 --delete        # 删除人物
  story:define character 张三                 # 创建新人物

  # 世界观管理
  story:define world --list                  # 列出所有设定
  story:define world 地理 --view              # 查看世界观条目
  story:define world 地理 --edit              # 编辑
  story:define world 地理 --delete            # 删除
  story:define world 地理                     # 创建新设定

  # 搜索
  story:define --search 关键词               # 搜索设定
        """
    )

    parser.add_argument('type', nargs='?', choices=['character', 'world', 'char', 'c', 'w'],
                        help='设定类型：character(char/c) 或 world(w)')
    parser.add_argument('name', nargs='?', help='设定名称')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有设定')
    parser.add_argument('--view', '-v', action='store_true', help='查看设定详情')
    parser.add_argument('--edit', '-e', action='store_true', help='编辑设定')
    parser.add_argument('--delete', '-d', action='store_true', help='删除设定')
    parser.add_argument('--search', '-s', metavar='关键词', help='搜索设定')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式（Agent 驱动）')
    parser.add_argument('--force', '-f', action='store_true', help='跳过确认提示（删除等危险操作）')
    # 人物卡属性参数
    parser.add_argument('--alias', help='人物别名/绰号')
    parser.add_argument('--gender', help='性别')
    parser.add_argument('--age', help='年龄')
    parser.add_argument('--occupation', help='职业')
    parser.add_argument('--status', help='状态（存活/死亡/退场）')
    parser.add_argument('--tags', help='标签（逗号分隔）')
    parser.add_argument('--cognition', help='六层认知 JSON，格式：{"worldview":"...","self_definition":"...","values":"...","ability":"...","skill":"...","environment":"..."}')
    # 世界观参数
    parser.add_argument('--category', help='世界观类别（地理/历史/社会/魔法能力/科技/生物/物品/组织/其他）')

    args = parser.parse_args()

    # 检查是否在项目目录
    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录，请先运行 story:init', Colors.RED)}")
        sys.exit(1)

    chars_dir, world_dir = ensure_dirs(root)

    # 搜索模式
    if args.search:
        search_specs(chars_dir, world_dir, args.search)
        return

    # 没有指定类型时，显示帮助或默认列出
    if not args.type:
        # 显示概览
        print(f"\n{c('=' * 50, Colors.HEADER)}")
        print(c("  设定库管理", Colors.BOLD))
        print(c('=' * 50, Colors.HEADER))
        print(f"\n  {c('【人物】', Colors.CYAN)}")
        list_characters(chars_dir)
        print(f"\n  {c('【世界观】', Colors.CYAN)}")
        list_world(world_dir)
        print(f"\n  {c('使用说明：', Colors.YELLOW)}")
        print(f"  story:define character --list        # 列出人物")
        print(f"  story:define world --list           # 列出世界观")
        print(f"  story:define character <姓名>       # 创建人物")
        print(f"  story:define world <名称>             # 创建世界观")
        return

    # 统一类型名称
    type_map = {'char': 'character', 'c': 'character', 'w': 'world'}
    spec_type = type_map.get(args.type, args.type)

    # list 模式
    if args.list:
        if spec_type == 'character':
            list_characters(chars_dir)
        else:
            list_world(world_dir)
        return

    # 需要名称的操作
    if not args.name:
        if spec_type == 'character':
            list_characters(chars_dir)
        else:
            list_world(world_dir)
        return

    name = args.name

    # 查看
    if args.view:
        if spec_type == 'character':
            view_character(chars_dir, name)
        else:
            view_world(world_dir, name)
        return

    # 编辑
    if args.edit:
        if spec_type == 'character':
            edit_character(chars_dir, name)
        else:
            edit_world(world_dir, name)
        return

    # 删除
    if args.delete:
        # 非交互模式下删除必须 --force
        if args.non_interactive and not args.force:
            print(f"  {c('ERROR: 非交互模式下删除需要 --force 参数', Colors.RED)}")
            sys.exit(1)
        if spec_type == 'character':
            delete_character(chars_dir, name, force=args.force)
        else:
            delete_world(world_dir, name, force=args.force)
        return

    # 创建（默认操作）
    if spec_type == 'character':
        # 解析 cognition JSON
        cognition = None
        if args.cognition:
            try:
                cognition = json.loads(args.cognition)
                if not isinstance(cognition, dict):
                    print(f"  {c('ERROR: --cognition 必须是 JSON 对象', Colors.RED)}")
                    sys.exit(1)
            except json.JSONDecodeError as e:
                print(f"  {c(f'ERROR: --cognition JSON 解析失败: {e}', Colors.RED)}")
                sys.exit(1)

        # 非交互模式：cognition_mode 取决于是否有 --cognition
        # 交互模式：默认启用 cognition_mode
        if args.non_interactive:
            create_character(chars_dir, name, cognition_mode=False, cognition=cognition)
        else:
            create_character(chars_dir, name, cognition_mode=True, cognition=cognition)
    else:
        create_world(world_dir, name, category=args.category)


if __name__ == '__main__':
    main()
