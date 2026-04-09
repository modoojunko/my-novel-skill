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

## 基本信息

**别名/昵称**：{alias}
**性别**：{gender}
**年龄**：{age}
**职业/身份**：{occupation}
**状态**：{status}

## 外观特征

（描述外貌、穿着、标志性特征等）

## 性格特点

- **核心性格**：（如：冷静、果断、外冷内热）
- **优点**：（如：善于观察、行动力强）
- **缺点**：（如：不善表达、过于理性）
- **口头禅/习惯**：（如有）

## 背景故事

（人物的前史、成长经历、为什么会成为现在的样子）

## 六层认知

> 角色的深层驱动力，决定其在剧情中的抉择、情绪和说话方式。

### 我的世界观

（这个角色对世界的根本看法。如：正派相信正义终将战胜邪恶、宿命论者认为一切早已注定、犬儒主义者觉得世界本质是残酷的）
→ 影响角色面对事件时的态度和信念

### 我对自己定义

（我是个什么样的人。如：我是个普通但靠谱的人、我注定要成为王、我不过是个逃兵）
→ 影响角色的内心独白和行为动机

### 我的价值观

（在艰难决策上的取舍优先级。如：他人感受 > 真相 > 自己、家族荣耀 > 个人幸福、生存 > 道德）
→ 影响角色在冲突中的选择

### 我的能力

（角色解决问题的方式和核心能力。如：倾听与共情、洞察人心、过目不忘）
→ 决定角色是直接解决问题，还是需要学习成长

### 我的技能

（角色掌握的具体技能。如：整理货架、泡方便面、剑术、编程）
→ 角色日常行为的基础

### 我的环境

（角色所处的物理和社会环境。如：深夜便利店、贵族学院、战场前线）
→ 角色行为和认知的背景约束

## 人物关系

- **家人**：（如有）
- **挚友**：（如有）
- **对手/敌人**：（如有）
- **其他重要关系**：（如有）

## 角色弧

**起点**：（角色的初始状态/问题）
**转折点**：（经历什么事件发生改变）
**终点**：（角色最终的成长/变化）

## 本卷/本故事中的目标

（当前故事中角色想要达成的目标）

## 重要情节线

- （与该角色相关的重要事件/冲突）

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


def delete_character(chars_dir: Path, name: str):
    """删除人物卡"""
    char_file = chars_dir / f'{name}.md'
    if not char_file.exists():
        print(f"  {c(f'[ERROR] 人物不存在：{name}', Colors.RED)}")
        return False

    # 确认删除
    print(f"\n  {c('[警告] 此操作不可恢复！', Colors.RED)}")
    confirm = input(f"  确认删除人物「{name}」？(y/N): ").strip().lower()
    if confirm != 'y':
        print("  已取消")
        return False

    # 备份后删除
    backup_dir = root / 'ARCHIVE' / 'deleted'
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'{name}_{timestamp}.md'
    char_file.rename(backup_file)

    print(f"  {c('[OK] 已删除', Colors.GREEN)}")
    print(f"  备份位置：{backup_file.relative_to(root)}")
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


def collect_cognition_interactive(name: str) -> dict:
    """交互式收集六层认知"""
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


def create_character(chars_dir: Path, name: str, cognition_mode: bool = True):
    """创建新人物卡"""
    char_file = chars_dir / f'{name}.md'

    if char_file.exists():
        print(f"  {c(f'[ERROR] 人物已存在：{name}', Colors.RED)}")
        print(f"  使用 'story:define character {name} --view' 查看")
        print(f"  使用 'story:define character {name} --edit' 编辑")
        return False

    # 创建模板
    content = create_character_template(name)

    # 交互式收集六层认知
    if cognition_mode:
        try:
            cognition = collect_cognition_interactive(name)
            content = apply_cognition_to_template(content, cognition)
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

## 概述

（简要描述这个世界观元素）

## 详细描述

（详细的设定内容）

## 规则/限制

（如有特殊的规则或限制）

## 与其他设定的关联

- （关联的人物/世界观元素）

## 备注

（额外的备注信息）

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


def delete_world(world_dir: Path, name: str):
    """删除世界观条目"""
    world_file = world_dir / f'{name}.md'
    if not world_file.exists():
        print(f"  {c(f'[ERROR] 设定不存在：{name}', Colors.RED)}")
        return False

    print(f"\n  {c('[警告] 此操作不可恢复！', Colors.RED)}")
    confirm = input(f"  确认删除设定「{name}」？(y/N): ").strip().lower()
    if confirm != 'y':
        print("  已取消")
        return False

    backup_dir = root / 'ARCHIVE' / 'deleted'
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'{name}_{timestamp}.md'
    world_file.rename(backup_file)

    print(f"  {c('[OK] 已删除', Colors.GREEN)}")
    print(f"  备份位置：{backup_file.relative_to(root)}")
    return True


def create_world(world_dir: Path, name: str):
    """创建新的世界观条目"""
    world_file = world_dir / f'{name}.md'

    if world_file.exists():
        print(f"  {c(f'[ERROR] 设定已存在：{name}', Colors.RED)}")
        print(f"  使用 'story:define world {name} --view' 查看")
        print(f"  使用 'story:define world {name} --edit' 编辑")
        return False

    # 选择类别
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
        if spec_type == 'character':
            delete_character(chars_dir, name)
        else:
            delete_world(world_dir, name)
        return

    # 创建（默认操作）
    if spec_type == 'character':
        create_character(chars_dir, name)
    else:
        create_world(world_dir, name)


if __name__ == '__main__':
    main()
