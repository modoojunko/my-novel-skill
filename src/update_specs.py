#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:update-specs - 写作后自动更新设定文档

分析章节内容，检测新人物、地点、世界观设定，
自动更新到 SPECS 目录。
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional


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


def get_chapter_path(root, chapter_num, volume_num=None):
    """获取章节文件路径"""
    chapters_per = 30
    if volume_num is None:
        volume_num = ((chapter_num - 1) // chapters_per) + 1
    chapter_path = root / 'CONTENT' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'
    return chapter_path


def get_existing_specs(root) -> Tuple[Set[str], Set[str]]:
    """获取已存在的设定名称"""
    chars_dir = root / 'SPECS' / 'characters'
    world_dir = root / 'SPECS' / 'world'
    
    existing_chars = set()
    existing_world = set()
    
    if chars_dir.exists():
        for f in chars_dir.glob('*.md'):
            existing_chars.add(f.stem)
    
    if world_dir.exists():
        for f in world_dir.glob('*.md'):
            existing_world.add(f.stem)
    
    return existing_chars, existing_world


def extract_content(text: str) -> str:
    """提取纯文本内容（去掉 frontmatter 和标题）"""
    lines = text.split('\n')
    content_lines = []
    in_frontmatter = False
    
    for line in lines:
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if line.startswith('# '):
            continue
        content_lines.append(line)
    
    return '\n'.join(content_lines)


# ============================================================================
# 设定检测器
# ============================================================================

def detect_characters(text: str) -> List[Dict[str, any]]:
    """检测人物名称"""
    characters = []
    seen = set()
    
    # 模式1：对话引号内的"XX说"、"XX道"、"XX问道"等
    speech_patterns = [
        r'[""''「『]([^""''「』]{2,8})[""''」』][说问道答喊叫吼叹笑哭吵骂讲唤斥]',
        r'[""''「『]([^""''「』]{2,8})[""''」』][，。]',
    ]
    
    for pattern in speech_patterns:
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            if name and 2 <= len(name) <= 6 and name not in seen:
                # 排除常见的非人名
                if not any(kw in name for kw in ['什么', '怎么', '为什么', '这个', '那个', '你的', '我的']):
                    seen.add(name)
                    characters.append({
                        'name': name,
                        'source': 'dialogue',
                        'context': text[max(0, match.start()-20):match.end()+20]
                    })
    
    # 模式2："XX的..."后跟动词（可能的POV描述）
    pov_patterns = [
        r'([\u4e00-\u9fff]{2,4})见[\u4e00-\u9fff]',
        r'([\u4e00-\u9fff]{2,4})想[\u4e00-\u9fff]',
        r'([\u4e00-\u9fff]{2,4})走向',
        r'([\u4e00-\u9fff]{2,4})来到',
        r'([\u4e00-\u9fff]{2,4})走进',
    ]
    
    for pattern in pov_patterns:
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            if name and name not in seen:
                seen.add(name)
                characters.append({
                    'name': name,
                    'source': 'narrative',
                    'context': text[max(0, match.start()-20):match.end()+20]
                })
    
    # 模式3：检测引号内的第一人称（对话内容中的名字）
    quote_pattern = r'[""''「『]([^""''「』]{1,30})[""''」』]'
    for match in re.finditer(quote_pattern, text):
        content = match.group(1)
        # 检测引号内提到的人名
        name_mentions = re.findall(r'[\u4e00-\u9fff]{2,4}(?=说|告诉|问|叫|是|在)', content)
        for name in name_mentions:
            if name and name not in seen and len(name) >= 2:
                seen.add(name)
                characters.append({
                    'name': name,
                    'source': 'reference',
                    'context': content
                })
    
    return characters


def detect_locations(text: str) -> List[Dict[str, any]]:
    """检测地点名称"""
    locations = []
    seen = set()
    
    # 地点指示词模式
    location_patterns = [
        # 来到/走进 + 地点
        (r'[来走]到(.{2,10})[，,]', 'arrival'),
        (r'走进?(.{2,10})[，,]', 'enter'),
        (r'来到?(.{2,10})[，,]', 'arrive'),
        # 位于/处在
        (r'位于(.+)', 'location'),
        (r'处在(.+)', 'location'),
        # 在 + 地点 + 的
        (r'在(.+)的', 'place'),
        # 常见的地点前缀
        (r'[到了](.+)城[，,]', 'city'),
        (r'[到了](.+)镇[，,]', 'town'),
        (r'[到了](.+)村[，,]', 'village'),
        (r'[到了](.+)殿[，,]', 'palace'),
        (r'[到了](.+)宫[，,]', 'palace'),
        (r'[到了](.+)山[，,]', 'mountain'),
        (r'[到了](.+)林[，,]', 'forest'),
        (r'[到了](.+)湖[，,]', 'lake'),
        (r'[到了](.+)河[，,]', 'river'),
    ]
    
    for pattern, loc_type in location_patterns:
        for match in re.finditer(pattern, text):
            location = match.group(1).strip()
            # 清理可能的标点和多余字符
            location = re.sub(r'[，。！？、：；""''「』].*$', '', location)
            location = location.strip()
            
            if location and 2 <= len(location) <= 10 and location not in seen:
                # 排除一些常见词
                exclude_words = ['哪里', '什么地方', '这里', '那里', '某处']
                if location not in exclude_words:
                    seen.add(location)
                    locations.append({
                        'name': location,
                        'type': loc_type,
                        'context': text[max(0, match.start()-30):match.end()+30]
                    })
    
    return locations


def detect_concepts(text: str) -> List[Dict[str, any]]:
    """检测世界观概念（组织、物品、特殊能力等）"""
    concepts = []
    seen = set()
    
    # 组织/门派模式
    org_patterns = [
        (r'加入(.+?)[社门派盟会党]', 'org'),
        (r'(.+)门[的]?', 'sect'),
        (r'(.+)派[的]?', 'sect'),
        (r'(.+)盟[的]?', 'alliance'),
        (r'(.+)宗[的]?', 'sect'),
    ]
    
    for pattern, concept_type in org_patterns:
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            if name and 2 <= len(name) <= 8 and name not in seen:
                seen.add(name)
                concepts.append({
                    'name': name,
                    'type': concept_type,
                    'context': text[max(0, match.start()-30):match.end()+30]
                })
    
    # 物品/神器模式
    item_patterns = [
        (r'[手持拿握佩戴](.+)剑', 'weapon'),
        (r'[手持拿握佩戴](.+)刀', 'weapon'),
        (r'(.+)神[器剑刀]', 'artifact'),
        (r'(.+)宝[剑物]', 'treasure'),
        (r'[获得得到拥有](.+)能力', 'ability'),
        (r'[掌握学会](.+)功法', 'technique'),
    ]
    
    for pattern, item_type in item_patterns:
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            if name and 2 <= len(name) <= 10 and name not in seen:
                seen.add(name)
                concepts.append({
                    'name': name,
                    'type': item_type,
                    'context': text[max(0, match.start()-30):match.end()+30]
                })
    
    return concepts


def get_context_snippet(text: str, keyword: str, snippet_len: int = 100) -> str:
    """获取关键词周围的文本片段"""
    idx = text.find(keyword)
    if idx == -1:
        return ""
    start = max(0, idx - snippet_len // 2)
    end = min(len(text), idx + len(keyword) + snippet_len // 2)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet.replace('\n', ' ').strip()


# ============================================================================
# 设定创建和更新
# ============================================================================

def ensure_specs_dirs(root):
    """确保设定目录存在"""
    chars_dir = root / 'SPECS' / 'characters'
    world_dir = root / 'SPECS' / 'world'
    chars_dir.mkdir(parents=True, exist_ok=True)
    world_dir.mkdir(parents=True, exist_ok=True)
    return chars_dir, world_dir


def create_character_spec(name: str, context: str = "") -> str:
    """创建人物卡内容"""
    today = datetime.now().strftime('%Y-%m-%d')
    return f"""---
name: {name}
alias: 
gender: 
age: 
occupation: 
status: 存活
tags: [新角色]
created: {today}
modified: {today}
---

# {name}

## 基本信息

**别名/昵称**：
**性别**：
**年龄**：
**职业/身份**：
**状态**：存活

## 外观特征

（描述外貌、穿着、标志性特征等）

## 性格特点

- **核心性格**：
- **优点**：
- **缺点**：
- **口头禅/习惯**：

## 背景故事

（人物的前史、成长经历）

## 人物关系

- **家人**：（如有）
- **挚友**：（如有）
- **对手/敌人**：（如有）

## 角色弧

**起点**：（角色的初始状态）
**转折点**：（经历什么事件）
**终点**：（角色最终的成长/变化）

## 本卷/本故事中的目标

（当前故事中角色想要达成的目标）

## 本章首次出现

> {context[:200] if context else '首次出现'}

---
*由 update-specs 自动创建 @ {today}*
"""


def create_world_spec(name: str, category: str, context: str = "") -> str:
    """创建世界观设定"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 分类对应的模板
    templates = {
        '地理': """（描述地理位置、地形地貌、气候环境、自然资源等）""",
        '历史': """（描述相关历史事件、时间线、起源传说等）""",
        '社会': """（描述社会结构、制度、文化习俗、礼仪传统等）""",
        '魔法/能力': """（描述能力来源、修炼方式、限制条件、使用代价等）""",
        '科技': """（描述科技水平、特殊技术、发明创造等）""",
        '生物': """（描述种族特性、怪物种类、生态习性等）""",
        '物品': """（描述物品外观、功能、来历、特殊属性等）""",
        '组织': """（描述组织结构、成员、宗旨、活动范围等）""",
        '其他': """（其他相关设定）""",
    }
    
    content_template = templates.get(category, templates['其他'])
    
    return f"""---
name: {name}
category: {category}
created: {today}
modified: {today}
---

# {name}

## 简介

（简要描述{name}）

## 详情

{content_template}

## 本章首次出现

> {context[:200] if context else '首次出现'}

---
*由 update-specs 自动创建 @ {today}*
"""


def prompt_choice(question: str, options: List[str]) -> int:
    """提示用户选择"""
    print(f"\n{c('[?] ' + question, Colors.CYAN)}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    
    while True:
        try:
            choice = input(c("\n请选择 (1-{}): ", Colors.YELLOW).format(len(options)))
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return idx
        except ValueError:
            pass
        print(c("无效选择，请重新输入", Colors.RED))


def ask_add_character(name: str, context: str) -> bool:
    """询问是否添加人物"""
    print(f"""
{c('='*60, Colors.HEADER)}
{c('  🆕 检测到新人物', Colors.GREEN)}
{c('='*60, Colors.HEADER)}
    """)
    print(f"  {c('人物名称:', Colors.BOLD)} {c(name, Colors.YELLOW)}")
    print(f"  {c('发现场景:', Colors.BOLD)}")
    print(f"  {c(context[:150] + '...' if len(context) > 150 else context, Colors.DIM)}")
    
    choice = prompt_choice(
        f"是否添加到人物设定库？",
        ["添加到人物库", "跳过"]
    )
    return choice == 0


def ask_add_world(name: str, context: str, suggested_type: str = "其他") -> Tuple[bool, str]:
    """询问是否添加世界观设定"""
    print(f"""
{c('='*60, Colors.HEADER)}
{c('  🆕 检测到新世界观', Colors.GREEN)}
{c('='*60, Colors.HEADER)}
    """)
    print(f"  {c('名称:', Colors.BOLD)} {c(name, Colors.YELLOW)}")
    print(f"  {c('建议类别:', Colors.BOLD)} {c(suggested_type, Colors.CYAN)}")
    print(f"  {c('发现场景:', Colors.BOLD)}")
    print(f"  {c(context[:150] + '...' if len(context) > 150 else context, Colors.DIM)}")
    
    categories = ['地理', '历史', '社会', '魔法/能力', '科技', '生物', '物品', '组织', '其他']
    
    choice = prompt_choice(
        f"是否添加到世界观设定库？",
        categories + ["跳过"]
    )
    
    if choice >= len(categories):
        return False, ""
    return True, categories[choice]


# ============================================================================
# 主功能
# ============================================================================

def analyze_chapter(root, chapter_num: int, volume_num: int = None) -> Dict:
    """分析章节内容，检测新设定"""
    
    # 获取章节路径
    if volume_num is None:
        chapters_per = 30
        volume_num = ((chapter_num - 1) // chapters_per) + 1
    
    chapter_path = get_chapter_path(root, chapter_num, volume_num)
    
    if not chapter_path.exists():
        print(f"  {c(f'[ERROR] 章节文件不存在: {chapter_path}', Colors.RED)}")
        return None
    
    # 读取内容
    content = chapter_path.read_text(encoding='utf-8')
    text = extract_content(content)
    
    # 获取已存在的设定
    existing_chars, existing_world = get_existing_specs(root)
    
    # 检测新设定
    characters = detect_characters(text)
    locations = detect_locations(text)
    concepts = detect_concepts(text)
    
    # 过滤已存在的设定
    new_chars = [c for c in characters if c['name'] not in existing_chars]
    new_locs = [l for l in locations if l['name'] not in existing_world]
    new_concepts = [k for k in concepts if k['name'] not in existing_world]
    
    return {
        'chapter': chapter_num,
        'volume': volume_num,
        'path': chapter_path,
        'new_characters': new_chars,
        'new_locations': new_locs,
        'new_concepts': new_concepts,
        'existing_chars': existing_chars,
        'existing_world': existing_world,
    }


def process_discovered_specs(root, analysis: Dict, auto_add: bool = False) -> Dict:
    """处理发现的设定，询问用户是否添加"""
    
    chars_dir, world_dir = ensure_specs_dirs(root)
    
    results = {
        'characters_added': [],
        'world_added': [],
        'skipped': [],
    }
    
    # 处理新人物
    for char in analysis['new_characters']:
        name = char['name']
        context = char.get('context', '')
        
        # 确认是人名（不是动词等）
        if any(kw in name for kw in ['来到', '走进', '看到', '听到', '感到', '觉得', '想到']):
            continue
        
        if auto_add:
            add = True
        else:
            add = ask_add_character(name, context)
        
        if add:
            char_path = chars_dir / f"{name}.md"
            char_path.write_text(create_character_spec(name, context), encoding='utf-8')
            results['characters_added'].append(name)
            print(f"  {c(f'✓ 已添加人物: {name}', Colors.GREEN)}")
        else:
            results['skipped'].append(name)
    
    # 处理新地点
    for loc in analysis['new_locations']:
        name = loc['name']
        context = loc.get('context', '')
        
        if auto_add:
            add, category = True, '地理'
        else:
            add, category = ask_add_world(name, context, '地理')
        
        if add:
            world_path = world_dir / f"{name}.md"
            world_path.write_text(create_world_spec(name, category, context), encoding='utf-8')
            results['world_added'].append(name)
            print(f"  {c(f'✓ 已添加地点: {name} ({category})', Colors.GREEN)}")
        else:
            results['skipped'].append(name)
    
    # 处理新概念
    type_to_category = {
        'org': '组织',
        'sect': '组织',
        'alliance': '组织',
        'weapon': '物品',
        'artifact': '物品',
        'treasure': '物品',
        'ability': '魔法/能力',
        'technique': '魔法/能力',
    }
    
    for concept in analysis['new_concepts']:
        name = concept['name']
        concept_type = concept.get('type', '其他')
        context = concept.get('context', '')
        category = type_to_category.get(concept_type, '其他')
        
        if auto_add:
            add = True
        else:
            add, _ = ask_add_world(name, context, category)
        
        if add:
            world_path = world_dir / f"{name}.md"
            world_path.write_text(create_world_spec(name, category, context), encoding='utf-8')
            results['world_added'].append(name)
            print(f"  {c(f'✓ 已添加概念: {name} ({category})', Colors.GREEN)}")
        else:
            results['skipped'].append(name)
    
    return results


def show_analysis_summary(analysis: Dict):
    """显示分析摘要"""
    
    print(f"""
{c('='*60, Colors.HEADER)}
{c('  📊 章节设定分析结果', Colors.CYAN)}
{c('='*60, Colors.HEADER)}
    """)
    
    print(f"  章节: 第{analysis['volume']}卷 第{analysis['chapter']}章")
    print(f"  文件: {analysis['path'].relative_to(Path.cwd())}")
    print()
    
    print(f"  {c('已有人物:', Colors.DIM)} {len(analysis['existing_chars'])} 个")
    print(f"  {c('已有世界观:', Colors.DIM)} {len(analysis['existing_world'])} 个")
    print()
    
    # 新人物
    new_chars = analysis['new_characters']
    if new_chars:
        print(f"  {c('🆕 新人物 ({}):', Colors.YELLOW).format(len(new_chars))}")
        for char in new_chars[:10]:  # 最多显示10个
            print(f"    • {char['name']}")
        if len(new_chars) > 10:
            print(f"    ... 还有 {len(new_chars) - 10} 个")
        print()
    else:
        print(f"  {c('🆕 新人物:', Colors.DIM)} 0 个")
        print()
    
    # 新地点
    new_locs = analysis['new_locations']
    if new_locs:
        print(f"  {c('🗺️ 新地点 ({}):', Colors.YELLOW).format(len(new_locs))}")
        for loc in new_locs[:10]:
            print(f"    • {loc['name']} ({loc.get('type', '')})")
        if len(new_locs) > 10:
            print(f"    ... 还有 {len(new_locs) - 10} 个")
        print()
    else:
        print(f"  {c('🗺️ 新地点:', Colors.DIM)} 0 个")
        print()
    
    # 新概念
    new_concepts = analysis['new_concepts']
    if new_concepts:
        print(f"  {c('💡 新概念 ({}):', Colors.YELLOW).format(len(new_concepts))}")
        for concept in new_concepts[:10]:
            print(f"    • {concept['name']} ({concept.get('type', '')})")
        if len(new_concepts) > 10:
            print(f"    ... 还有 {len(new_concepts) - 10} 个")
        print()
    else:
        print(f"  {c('💡 新概念:', Colors.DIM)} 0 个")
        print()


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='写作后自动更新设定文档 - 分析章节内容，检测并添加新设定',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python story.py update-specs 5              # 分析第5章
  python story.py update-specs 5 --auto        # 自动添加所有检测到的设定
  python story.py update-specs 5 --view        # 仅显示分析结果，不添加
  python story.py update-specs 5 -v 2         # 指定卷号

提示：
  写完章节后运行此命令，系统会检测新增的人物、地点、世界观，
  并询问你是否添加到设定库中。
        """
    )
    parser.add_argument('chapter', nargs='?', type=int, help='章节号')
    parser.add_argument('-v', '--volume', type=int, help='卷号')
    parser.add_argument('--auto', '-a', action='store_true', help='自动添加所有检测到的设定')
    parser.add_argument('--view', action='store_true', help='仅显示分析结果，不添加')
    
    args = parser.parse_args()
    
    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录，请先运行 story:init', Colors.RED)}")
        sys.exit(1)
    
    # 如果未指定章节，提示
    if not args.chapter:
        # 尝试从配置读取当前章节
        try:
            config = load_config(root)
            args.chapter = config['progress'].get('current_chapter', 1)
        except:
            args.chapter = 1
    
    print(f"\n{c('🔍 正在分析章节...', Colors.CYAN)}")
    
    # 分析章节
    analysis = analyze_chapter(root, args.chapter, args.volume)
    if not analysis:
        sys.exit(1)
    
    # 显示摘要
    show_analysis_summary(analysis)
    
    # 检查是否有新设定
    has_new = (
        len(analysis['new_characters']) > 0 or
        len(analysis['new_locations']) > 0 or
        len(analysis['new_concepts']) > 0
    )
    
    if not has_new:
        print(c("  ✅ 本章未发现新的设定", Colors.GREEN))
        print()
        return
    
    # 处理新设定
    if args.view:
        print(c("  📝 使用 --auto 自动添加，或 --view 重新查看", Colors.DIM))
        return
    
    if args.auto:
        print(c("\n  ⚡ 自动添加模式", Colors.YELLOW))
        results = process_discovered_specs(root, analysis, auto_add=True)
    else:
        print(c("\n  ⏳ 准备添加新设定...", Colors.CYAN))
        results = process_discovered_specs(root, analysis, auto_add=False)
    
    # 显示结果
    total_added = len(results['characters_added']) + len(results['world_added'])
    if total_added > 0:
        print(f"""
{c('='*60, Colors.GREEN)}
{c('  ✅ 更新完成!', Colors.GREEN)}
{c('='*60, Colors.GREEN)}

  新增人物: {len(results['characters_added'])} 个
  新增世界观: {len(results['world_added'])} 个
  跳过: {len(results['skipped'])} 个

  查看设定库: python story.py define
""")


if __name__ == '__main__':
    main()
