#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:write - 写作模式 + Agent Prompt 生成

提供两种写作方式：
1. 手动写作：创建文件框架，人工写作
2. Agent Prompt：生成结构化 Prompt，供 Agent 使用

Pipeline 模式：
- --draft: AI 根据细纲写正文草稿
- --revise: 讨论模式修改正文
- --confirm: 确认正文定稿

使用 JSON 作为配置文件格式。
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from .paths import find_project_root, load_config, save_config, load_project_paths
from .snapshot import read_recent_snapshots_for_prompt


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


def read_file_safely(path: Path, default: str = "") -> str:
    """安全读取文件，不存在返回默认值"""
    if path.exists():
        return path.read_text(encoding='utf-8')
    return default


def count_chinese_chars(text: str) -> int:
    """统计中文字符数（不含标点）"""
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            count += 1
    return count


def truncate_text(text: str, max_chars: int = 500, suffix: str = "...") -> str:
    """截断文本到指定字符数"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + suffix


# ============================================================================
# Pipeline Stage 管理
# ============================================================================

def load_pipeline_state(root: Path) -> dict:
    """加载/初始化流水线状态"""
    config_path = root / "story.json"
    if not config_path.exists():
        return {"volumes": {}, "chapters": {}}
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    if "pipeline" not in config:
        config["pipeline"] = {"volumes": {}, "chapters": {}}
    return config["pipeline"]


def save_pipeline_state(root: Path, pipeline: dict) -> None:
    """保存流水线状态"""
    config_path = root / "story.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["pipeline"] = pipeline
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_chapter_stage(chapter_num: int, root: Path) -> str:
    """获取章节 stage"""
    pipeline = load_pipeline_state(root)
    return pipeline["chapters"].get(str(chapter_num), {}).get("stage", "")


def update_chapter_stage(chapter_num: int, new_stage: str, root: Path) -> None:
    """更新章节 stage"""
    pipeline = load_pipeline_state(root)
    if str(chapter_num) not in pipeline["chapters"]:
        pipeline["chapters"][str(chapter_num)] = {}
    pipeline["chapters"][str(chapter_num)]["stage"] = new_stage
    save_pipeline_state(root, pipeline)


# ============================================================================
# Pipeline: 正文写作功能
# ============================================================================

def generate_writing_prompt(root: Path, chapter_num: int, volume_num: int, config: dict, paths: dict = None) -> str:
    """生成正文写作的 Prompt（用于 AI 写正文）"""
    if paths is None:
        paths = load_project_paths(root)
    meta = config.get("meta", {})
    title = meta.get("title", "未命名小说")
    genre = meta.get("genre", "未知")

    # 读取章节细纲
    outline_path = root / "OUTLINE" / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"
    chapter_outline = ""
    if outline_path.exists():
        chapter_outline = outline_path.read_text(encoding="utf-8")

    # 读取卷纲
    vol_outline_path = root / "OUTLINE" / f"volume-{volume_num:03d}" / f"volume-{volume_num:03d}-outline.md"
    volume_outline = ""
    if vol_outline_path.exists():
        volume_outline = vol_outline_path.read_text(encoding="utf-8")

    # 读取上一章结尾
    prev_ending = ""
    if chapter_num > 1:
        prev_path = paths['output_dir'] / f"volume-{volume_num:03d}" / f"chapter-{chapter_num-1:03d}.md"
        if prev_path.exists():
            content = prev_path.read_text(encoding="utf-8")
            if len(content) > 500:
                prev_ending = "..." + content[-500:]

    # 读取前序章节设定快照
    snapshots_context = read_recent_snapshots_for_prompt(root, chapter_num, count=3, volume_num=volume_num)

    # 读取风格档案
    style_path = root / "style" / "style.md"
    style_guide = ""
    if style_path.exists():
        style_guide = style_path.read_text(encoding="utf-8")

    # 读取人物设定
    characters = ""
    chars_dir = paths['characters']
    if chars_dir.exists():
        parts = []
        for char_file in sorted(chars_dir.glob("*.md")):
            parts.append(f"### {char_file.stem}\n")
            parts.append(char_file.read_text(encoding="utf-8"))
        characters = "\n".join(parts)

    # 从细纲中提取POV角色并生成约束
    pov_constraint = ""
    import re
    pov_match = re.search(r'POV[:：]\s*(\S+)', chapter_outline)
    if pov_match:
        pov_char = pov_match.group(1).strip()
        pov_constraint = generate_pov_constraint_prompt(root, pov_char)
    else:
        pov_constraint = "## POV视角约束\n\n（未在细纲中指定POV角色，请根据场景自行判断）\n"

    prompt = f"""# 第 {chapter_num} 章正文写作任务

## 基本信息
- **书名**：《{title}》
- **类型**：{genre}
- **当前卷**：第 {volume_num} 卷
- **当前章**：第 {chapter_num} 章

## 章节细纲
{chapter_outline if chapter_outline else "（暂无细纲，请根据卷纲自由发挥）"}

## 卷纲背景
{truncate_text(volume_outline, 800) if volume_outline else "（暂无卷纲）"}

## 上章结尾（需要衔接）
{truncate_text(prev_ending, 500) if prev_ending else "（本章为第一章）"}

{snapshots_context if snapshots_context else ""}

## 人物设定参考
{characters[:500] if characters else "（暂无人物设定）"}

## 风格指南
{truncate_text(style_guide, 500) if style_guide else "（暂无风格指南，请保持自然流畅）"}

{pov_constraint}

{generate_cognition_prompt(root, pov_match.group(1).strip()) if pov_match else ""}

## 写作要求

1. **字数**：3000-4000 字
2. **POV**：严格按照细纲中的 POV 视角写作，遵守上述POV约束
3. **场景**：按照细纲中的场景列表展开
4. **衔接**：开头必须自然衔接上章结尾
5. **风格**：遵循上述风格指南
6. **逻辑**：严格遵守POV角色的认知边界，禁止写出该角色不可能知道的信息

## 输出格式

请直接输出正文内容，不需要额外说明。正文格式：

```
# 第 {chapter_num} 章：xxx（章节主题）

（正文内容...）
```

---
*此 Prompt 用于生成正文草稿，可使用 story:write {chapter_num} --revise 进行讨论修改*
"""
    return prompt


def draft_chapter(root: Path, chapter_num: int, paths: dict = None) -> None:
    """生成章节正文草稿"""
    if paths is None:
        paths = load_project_paths(root)
    config = load_config(root)
    chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    # 检查细纲是否已确认
    stage = get_chapter_stage(chapter_num, root)
    if stage not in ["outline-confirmed", "writing"]:
        print(f"\n  ⚠️  第 {chapter_num} 章细纲尚未确认（stage: {stage or '未设置'}）")
        print(f"  建议先使用 story:outline --draft {chapter_num} 生成细纲")
        print(f"  然后使用 story:outline --confirm {chapter_num} 确认细纲")
        print(f"\n  如需强制生成正文，请先确认细纲")
        return

    vol_dir = root / "OUTLINE" / f"volume-{volume_num:03d}"
    vol_dir.mkdir(parents=True, exist_ok=True)

    prompt = generate_writing_prompt(root, chapter_num, volume_num, config, paths=paths)

    print(f"\n{'='*60}")
    print(f"  第 {chapter_num} 章正文写作 Prompt")
    print(f"{'='*60}\n")
    print(prompt)

    # 保存 Prompt
    prompt_file = vol_dir / f"chapter-{chapter_num:03d}-writing-prompt.md"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"\n  💡 Prompt 已保存到：{prompt_file}")
    print(f"\n  下一步：")
    print(f"    1. 将此 Prompt 发送给 AI 获取正文草稿")
    print(f"    2. 将 AI 返回的内容保存到 CONTENT/volume-{volume_num:03d}/chapter-{chapter_num:03d}.md")
    print(f"    3. 使用 story:write {chapter_num} --revise 进行讨论修改")
    print(f"    4. 确认后使用 story:write {chapter_num} --confirm")

    # 更新 stage
    update_chapter_stage(chapter_num, "writing", root)
    print(f"\n  ✓ 第 {chapter_num} 章 stage 已更新为: writing")


def revise_chapter(root: Path, chapter_num: int, paths: dict = None) -> None:
    """讨论模式修改正文"""
    if paths is None:
        paths = load_project_paths(root)
    config = load_config(root)
    chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = paths['output_dir'] / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"

    if not chapter_path.exists():
        print(f"\n  错误：第 {chapter_num} 章还没有正文文件")
        print(f"  请先使用 story:write {chapter_num} --draft 生成正文草稿")
        return

    current_stage = get_chapter_stage(chapter_num, root)
    print(f"\n  📝 第 {chapter_num} 章当前 stage: {current_stage or '未设置'}")
    print(f"\n  请告诉我你想如何修改正文：")
    print(f"     1. 修改某个场景的内容")
    print(f"     2. 调整对话")
    print(f"     3. 优化某个段落")
    print(f"     4. 修改结尾/衔接")
    print(f"     5. 其他修改")
    print(f"\n  修改完成后，将新内容保存到：{chapter_path}")
    print(f"  然后使用 story:write {chapter_num} --confirm 确认定稿")


def confirm_chapter(root: Path, chapter_num: int, paths: dict = None) -> None:
    """确认章节正文定稿"""
    if paths is None:
        paths = load_project_paths(root)
    config = load_config(root)
    chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = paths['output_dir'] / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"

    if not chapter_path.exists():
        print(f"\n  错误：第 {chapter_num} 章还没有正文文件")
        print(f"  请先使用 story:write {chapter_num} --draft 生成正文草稿")
        return

    update_chapter_stage(chapter_num, "done", root)

    # 统计字数
    content = chapter_path.read_text(encoding="utf-8")
    word_count = sum(1 for c in content if "\u4e00" <= c <= "\u9fff")

    print(f"\n  ✓ 第 {chapter_num} 章正文已确认定稿")
    print(f"  ✓ stage 已更新为: done")
    print(f"  ✓ 章节字数：约 {word_count} 字")
    print(f"\n  恭喜完成本章！")
    print(f"\n  下一步建议：")
    print(f"    story:snapshot {chapter_num}      →  生成设定快照（推荐！）")
    print(f"    story:update-specs {chapter_num}  →  检测新设定并生成摘要")
    print(f"    story:write {chapter_num + 1} --draft  →  继续下一章")


# ============================================================================
# 上下文读取函数
# ============================================================================


# ============================================================================
# 上下文读取函数
# ============================================================================

def get_chapter_path(root, chapter_num, volume_num=None, paths=None):
    """获取章节文件路径"""
    if paths is None:
        paths = load_project_paths(root)
    chapters_per = 30
    if volume_num is None:
        volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = paths['output_dir'] / f'volume-{volume_num:03d}' / f'chapter-{chapter_num:03d}.md'
    return chapter_path, volume_num


def read_chapter_outline(root, chapter_num, volume_num):
    """读取章节大纲"""
    outline_path = root / 'OUTLINE' / f'volume-{volume_num:03d}' / f'chapter-{chapter_num:03d}.md'
    return read_file_safely(outline_path)


def read_volume_outline(root, volume_num):
    """读取卷大纲"""
    vol_path = root / 'OUTLINE' / f'volume-{volume_num:03d}.md'
    return read_file_safely(vol_path)


def read_meta_outline(root):
    """读取总大纲"""
    meta_path = root / 'OUTLINE' / 'meta.md'
    return read_file_safely(meta_path)


def read_previous_chapter_ending(root, chapter_num, volume_num):
    """读取上一章结尾（500字）"""
    if chapter_num <= 1:
        return ""

    prev_chapter = chapter_num - 1
    prev_path, _ = get_chapter_path(root, prev_chapter, volume_num)

    if not prev_path.exists():
        return ""

    content = prev_path.read_text(encoding='utf-8')
    # 去掉 frontmatter 和标题
    lines = content.split('\n')
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

    full_text = '\n'.join(content_lines).strip()
    # 取最后 500 字
    if len(full_text) > 500:
        return "..." + full_text[-500:]
    return full_text


def read_characters_specs(root, paths=None):
    """读取人物设定"""
    if paths is None:
        paths = load_project_paths(root)
    chars_dir = paths['characters']
    if not chars_dir.exists():
        return ""

    result = []
    for char_file in sorted(chars_dir.glob('*.md')):
        result.append(f"\n### {char_file.stem}\n")
        result.append(char_file.read_text(encoding='utf-8'))

    return '\n'.join(result)


def read_character_pov_state(root: Path, char_name: str, paths: dict = None) -> dict:
    """读取角色的POV认知状态"""
    if paths is None:
        paths = load_project_paths(root)
    char_file = paths['characters'] / f'{char_name}.md'
    if not char_file.exists():
        return {}
    
    content = char_file.read_text(encoding='utf-8')
    
    # 查找"当前状态"章节
    state_start = content.find('## 当前状态')
    if state_start == -1:
        return {}
    
    state_section = content[state_start:]
    
    # 解析已知角色表格
    known_chars = []
    unknown_chars = []
    known_info = []
    pending_reveals = []
    
    # 简单解析：查找表格行
    import re
    
    # 解析已知角色表格 (| 角色 | 关系 | 获知途径 | 获知章节 |)
    table_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
    matches = re.findall(table_pattern, state_section)
    for match in matches:
        name, relation, source, chapter = match
        if name.strip() and name.strip() != '角色':  # 跳过表头
            known_chars.append({
                'name': name.strip(),
                'relationship': relation.strip(),
                'source': source.strip(),
                'chapter': chapter.strip()
            })
    
    # 解析未知角色列表 (- [ ] 角色名)
    unknown_pattern = r'-\s*\[\s*\]\s*([^\n]+)'
    unknown_matches = re.findall(unknown_pattern, state_section)
    for match in unknown_matches:
        # 只提取角色名（去掉括号里的说明）
        char_name_clean = match.split('（')[0].split('(')[0].strip()
        if char_name_clean:
            unknown_chars.append(char_name_clean)
    
    # 解析已掌握信息
    info_section = state_section.find('### 已掌握信息')
    pending_section = state_section.find('### 待揭示信息')
    
    if info_section != -1:
        info_end = pending_section if pending_section != -1 else len(state_section)
        info_text = state_section[info_section:info_end]
        info_items = re.findall(r'-\s+(.+)', info_text)
        known_info = [item.strip() for item in info_items if item.strip()]
    
    if pending_section != -1:
        pending_text = state_section[pending_section:]
        pending_items = re.findall(r'-\s*\[\s*\]\s+(.+)', pending_text)
        pending_reveals = [item.strip() for item in pending_items if item.strip()]
    
    return {
        'known_characters': known_chars,
        'unknown_characters': unknown_chars,
        'known_info': known_info,
        'pending_reveals': pending_reveals
    }


def generate_pov_constraint_prompt(root: Path, pov_char: str, paths: dict = None) -> str:
    """生成POV视角约束Prompt"""
    if not pov_char or pov_char == '旁白':
        return """## POV视角约束

本场景使用**旁白视角**（全知视角）。

**注意**：即使是全知视角，也建议保持客观描述，不要直接揭示角色内心想法，而是通过动作、神态、对话来表现。
"""
    
    state = read_character_pov_state(root, pov_char, paths=paths)
    if not state:
        return f"""## POV视角约束

本场景使用**{pov_char}**的视角。

⚠️ 警告：未找到该角色的认知状态记录。请在 SPECS/characters/{pov_char}.md 中添加"当前状态"章节。
"""
    
    lines = []
    lines.append(f"## POV视角约束（重要！）")
    lines.append(f"")
    lines.append(f"你当前是 **{pov_char}** 的视角。")
    lines.append(f"")
    lines.append(f"**⚠️ 严格遵守以下信息边界：**")
    lines.append(f"")
    
    # 已知角色
    if state.get('known_characters'):
        lines.append(f"**已知道的角色**（可以直接称呼名字）：")
        for char in state['known_characters']:
            lines.append(f"  - {char['name']}：{char['relationship']}（通过{char['source']}获知）")
        lines.append(f"")
    
    # 未知角色
    if state.get('unknown_characters'):
        lines.append(f"**不知道的角色**（禁止直呼其名，用外貌/身份代称）：")
        for char in state['unknown_characters']:
            lines.append(f"  - {char}：必须用代称（如'那女孩'、'穿校服的学生'）")
        lines.append(f"")
    
    # 已掌握信息
    if state.get('known_info'):
        lines.append(f"**已掌握的信息**：")
        for info in state['known_info'][:5]:  # 最多显示5条
            lines.append(f"  - {info}")
        if len(state['known_info']) > 5:
            lines.append(f"  - ... 等共{len(state['known_info'])}条")
        lines.append(f"")
    
    # 待揭示信息
    if state.get('pending_reveals'):
        lines.append(f"**禁止提前揭示的信息**：")
        for reveal in state['pending_reveals'][:3]:  # 最多显示3条
            lines.append(f"  - ❌ {reveal}")
        if len(state['pending_reveals']) > 3:
            lines.append(f"  - ... 等共{len(state['pending_reveals'])}条")
        lines.append(f"")
    
    lines.append(f"**写作规则**：")
    lines.append(f"1. 只能描述{pov_char}能看到、听到、感知到的事物")
    lines.append(f"2. 对未知角色，用外貌特征或身份代称（如'马尾辫女孩'、'那个学生'）")
    lines.append(f"3. 禁止写出{pov_char}不可能知道的信息")
    lines.append(f"4. 禁止直接描述其他角色的内心想法")
    lines.append(f"")
    
    return '\n'.join(lines)


def read_character_cognition(root: Path, char_name: str, paths: dict = None) -> dict:
    """读取角色的六层认知"""
    if paths is None:
        paths = load_project_paths(root)
    char_file = paths['characters'] / f'{char_name}.md'
    if not char_file.exists():
        return {}
    
    content = char_file.read_text(encoding='utf-8')
    
    # 查找"六层认知"章节
    cognition_start = content.find('## 六层认知')
    if cognition_start == -1:
        return {}
    
    # 找到下一个同级或更高级标题作为结束
    cognition_section = content[cognition_start:]
    lines = cognition_section.split('\n')
    
    cognition = {}
    current_key = None
    current_content = []
    
    key_map = {
        '我的世界观': 'worldview',
        '我对自己定义': 'self_definition',
        '我的价值观': 'values',
        '我的能力': 'ability',
        '我的技能': 'skill',
        '我的环境': 'environment',
    }
    
    for line in lines[1:]:  # 跳过"## 六层认知"标题行
        # 遇到同级或更高级标题，停止
        if line.startswith('## ') and not line.startswith('### '):
            break
        # 遇到三级标题，切换当前 key
        if line.startswith('### '):
            # 保存前一个 key 的内容
            if current_key and current_content:
                text = '\n'.join(current_content).strip()
                # 去掉引用行和"影响"行
                clean_lines = []
                for l in text.split('\n'):
                    if l.startswith('> ') or l.startswith('→'):
                        continue
                    if l.strip():
                        clean_lines.append(l.strip())
                cognition[current_key] = '\n'.join(clean_lines)
            
            title = line.replace('### ', '').strip()
            current_key = key_map.get(title)
            current_content = []
        elif current_key:
            current_content.append(line)
    
    # 保存最后一个 key
    if current_key and current_content:
        text = '\n'.join(current_content).strip()
        clean_lines = []
        for l in text.split('\n'):
            if l.startswith('> ') or l.startswith('→'):
                continue
            if l.strip():
                clean_lines.append(l.strip())
        cognition[current_key] = '\n'.join(clean_lines)
    
    return cognition


def generate_cognition_prompt(root: Path, pov_char: str, paths: dict = None) -> str:
    """生成基于六层认知的角色行为约束 Prompt
    
    世界观 → 影响角色面对事件时的态度和信念
    价值观 → 影响角色在冲突中的选择
    能力/技能 → 角色当前能做什么，影响后续是学习还是直接解决
    """
    if not pov_char or pov_char == '旁白':
        return ""
    
    cognition = read_character_cognition(root, pov_char, paths=paths)
    if not cognition:
        return ""
    
    lines = []
    lines.append("## 角色认知驱动（核心！）")
    lines.append("")
    lines.append(f"角色 **{pov_char}** 的深层认知决定了其行为逻辑：")
    lines.append("")
    
    # 世界观 → 态度和信念
    if cognition.get('worldview') and cognition['worldview'] != '（待填写）':
        lines.append(f"**世界观**：{cognition['worldview']}")
        lines.append(f"→ 面对事件时的态度和信念以此为根基")
        lines.append("")
    
    # 自我定义 → 内心独白和行为动机
    if cognition.get('self_definition') and cognition['self_definition'] != '（待填写）':
        lines.append(f"**自我定义**：{cognition['self_definition']}")
        lines.append(f"→ 内心独白和行为动机由此驱动")
        lines.append("")
    
    # 价值观 → 冲突中的选择
    if cognition.get('values') and cognition['values'] != '（待填写）':
        lines.append(f"**价值观**：{cognition['values']}")
        lines.append(f"→ 在两难冲突中的取舍优先级")
        lines.append("")
    
    # 能力 → 解决问题的方式
    if cognition.get('ability') and cognition['ability'] != '（待填写）':
        lines.append(f"**核心能力**：{cognition['ability']}")
        ability_hint = "→ 角色可以直接解决问题，展现能力" if '（待填写）' not in cognition['ability'] else ""
        if ability_hint:
            lines.append(ability_hint)
        lines.append("")
    
    # 技能 → 日常行为基础
    if cognition.get('skill') and cognition['skill'] != '（待填写）':
        lines.append(f"**技能**：{cognition['skill']}")
        lines.append("")
    
    # 环境 → 背景约束
    if cognition.get('environment') and cognition['environment'] != '（待填写）':
        lines.append(f"**环境**：{cognition['environment']}")
        lines.append(f"→ 角色行为受此环境约束和塑造")
        lines.append("")
    
    lines.append("**写作规则**：")
    lines.append(f"1. {pov_char}的态度和信念必须符合其世界观")
    lines.append(f"2. 面对两难选择时，优先级必须符合其价值观")
    lines.append(f"3. 角色只能做其能力/技能范围内的事，超出范围需要学习或求助")
    lines.append(f"4. 角色对环境的反应必须符合其生活背景")
    lines.append("")
    
    return '\n'.join(lines)


def read_world_specs(root, paths=None):
    """读取世界观设定"""
    if paths is None:
        paths = load_project_paths(root)
    world_dir = paths['world']
    if not world_dir.exists():
        return ""

    result = []
    for world_file in sorted(world_dir.glob('*.md')):
        result.append(f"\n### {world_file.stem}\n")
        result.append(world_file.read_text(encoding='utf-8'))

    return '\n'.join(result)


def read_style_prompts(root, paths=None):
    """读取风格提示（如果存在）"""
    if paths is None:
        paths = load_project_paths(root)
    style_dir = paths['style_prompts']
    if not style_dir.exists():
        return ""

    parts = []
    for fname in ['vocabulary.md', 'sentence.md', 'pacing.md']:
        fpath = style_dir / fname
        if fpath.exists():
            parts.append(f"\n### {fname.replace('.md', '')}\n")
            parts.append(fpath.read_text(encoding='utf-8'))

    if not parts:
        return ""

    return '\n'.join(parts)


def read_story_concept(root, paths=None):
    """读取故事概念"""
    if paths is None:
        paths = load_project_paths(root)
    concept_path = paths['meta'] / 'story-concept.md'
    return read_file_safely(concept_path)


def read_style_avoid(root, paths=None):
    """读取风格禁忌（如果存在）"""
    if paths is None:
        paths = load_project_paths(root)
    avoid_path = paths['style'] / 'avoid.md'
    if avoid_path.exists():
        content = avoid_path.read_text(encoding='utf-8')
        return content.split('## 避免')[1] if '## 避免' in content else content
    return ""


# ============================================================================
# Agent Prompt 生成
# ============================================================================

def generate_agent_prompt(root, config, chapter_num, volume_num, paths=None):
    """生成 Agent 写作 Prompt"""
    if paths is None:
        paths = load_project_paths(root)

    # 获取卷信息
    volume_titles = config.get('structure', {}).get('volume_titles', [])
    volume_title = f"卷{volume_num}"
    volume_theme = ""
    for vt in volume_titles:
        if vt.get('num') == volume_num:
            volume_title = vt.get('title', f"卷{volume_num}")
            volume_theme = vt.get('theme', '')
            break

    # 获取风格指南
    style_prompts = read_style_prompts(root, paths=paths)
    style_avoid = read_style_avoid(root, paths=paths)

    # 构建 Prompt
    prompt_parts = []

    # 1. 写作任务
    prompt_parts.append("## 写作任务\n")
    prompt_parts.append(f"- 章节：第{chapter_num}章")
    prompt_parts.append(f"- 卷：第{volume_num}卷「{volume_title}」")
    if volume_theme:
        prompt_parts.append(f"- 卷主题：{volume_theme}")
    prompt_parts.append("")

    # 2. 章节大纲
    chapter_outline = read_chapter_outline(root, chapter_num, volume_num)
    if chapter_outline:
        prompt_parts.append("## 章节大纲\n")
        # 提取大纲中的关键内容（去掉 frontmatter）
        lines = chapter_outline.split('\n')
        in_frontmatter = False
        for line in lines:
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if line.strip():
                prompt_parts.append(line)
        prompt_parts.append("")
    else:
        prompt_parts.append("## 章节大纲\n（请参考 OUTLINE 目录下的章节大纲）\n")

    # 3. 场景列表
    if chapter_outline and '## 场景列表' in chapter_outline:
        lines = chapter_outline.split('\n')
        in_scenes = False
        scenes = []
        for line in lines:
            if '## 场景列表' in line:
                in_scenes = True
                continue
            if in_scenes and line.startswith('## '):
                break
            if in_scenes and line.strip():
                scenes.append(line)
        if scenes:
            prompt_parts.append("## 场景列表\n")
            prompt_parts.extend(scenes)
            prompt_parts.append("")

    # 4. 人物设定
    characters = read_characters_specs(root, paths=paths)
    if characters:
        prompt_parts.append("## 人物设定\n")
        prompt_parts.append(characters.strip())
        prompt_parts.append("")

    # 5. 世界观约束
    world = read_world_specs(root, paths=paths)
    if world:
        prompt_parts.append("## 世界观约束\n")
        prompt_parts.append(world.strip())
        prompt_parts.append("")

    # 6. 风格指南（核心！从学习模块生成）
    if style_prompts:
        prompt_parts.append("## 风格指南\n")
        prompt_parts.append("(以下是从你的修改中学习到的风格偏好)\n")
        prompt_parts.append(style_prompts.strip())
        prompt_parts.append("")

    if style_avoid:
        prompt_parts.append("## 写作禁忌\n")
        prompt_parts.append(style_avoid.strip())
        prompt_parts.append("")

    # 7. 上章结尾
    prev_ending = read_previous_chapter_ending(root, chapter_num, volume_num)
    if prev_ending:
        prompt_parts.append("## 上章结尾（需要衔接）\n")
        prompt_parts.append(truncate_text(prev_ending, 600))
        prompt_parts.append("")

    # 7.5 前序章节设定快照
    snapshots_context = read_recent_snapshots_for_prompt(root, chapter_num, count=3, volume_num=volume_num)
    if snapshots_context:
        prompt_parts.append(snapshots_context)
        prompt_parts.append("")

    # 8. POV约束（从细纲提取POV角色）
    pov_char = None
    if chapter_outline:
        import re
        pov_match = re.search(r'POV[:：]\s*(\S+)', chapter_outline)
        if pov_match:
            pov_char = pov_match.group(1).strip()
    
    pov_constraint = generate_pov_constraint_prompt(root, pov_char or "旁白", paths=paths)
    if pov_constraint:
        prompt_parts.append(pov_constraint)
        prompt_parts.append("")

    # 9. 角色认知驱动（从六层认知中提取）
    cognition_prompt = generate_cognition_prompt(root, pov_char or "", paths=paths)
    if cognition_prompt:
        prompt_parts.append(cognition_prompt)

    # 10. 写作要求
    prompt_parts.append("## 写作要求\n")
    prompt_parts.append(f"- 字数：约 2500-3500 字")
    if chapter_outline:
        for line in chapter_outline.split('\n'):
            if 'POV' in line.upper():
                prompt_parts.append(f"- POV：{line.split('POV', 1)[-1].strip()}")
                break
    prompt_parts.append("- 保持情节连贯，衔接上章结尾")
    if style_prompts:
        prompt_parts.append("- 遵循上述风格指南")
    prompt_parts.append("- 严格遵守POV角色的认知边界，禁止写出该角色不可能知道的信息")
    prompt_parts.append("- 禁止：错别字、语法错误、POV 混乱")
    prompt_parts.append("- 信息密度递增：每章的事件密度/冲突强度须比上章有所推进，高潮章的密度应显著高于铺垫章，禁止连续两章节奏相同")
    prompt_parts.append("- 场景重复限制：同一场景模式（如买商品、碰面等相似互动）最多完整描写2次，第3次起需侧面描写或一句话带过")

    return '\n'.join(prompt_parts)


def show_prompt_only(prompt: str):
    """仅显示 Prompt 部分"""
    print(prompt)


def show_full_context(root, config, chapter_num, volume_num):
    """显示完整上下文（包含读取的文件路径信息）"""
    print("\n" + "=" * 70)
    print(c(f"  Agent Prompt 生成器 - 第 {chapter_num} 章", Colors.BOLD))
    print("=" * 70 + "\n")

    # 显示引用的文件
    print(c("[INFO] 引用的文件：", Colors.CYAN))
    print(f"  - 章节大纲：OUTLINE/volume-{volume_num:03d}/chapter-{chapter_num:03d}.md")
    print(f"  - 卷大纲：OUTLINE/volume-{volume_num:03d}.md")
    print(f"  - 总大纲：OUTLINE/meta.md")
    print(f"  - 人物设定：SPECS/characters/")
    print(f"  - 世界观：SPECS/world/")
    style_dir = root / 'STYLE' / 'prompts'
    if style_dir.exists():
        print(f"  - 风格指南：STYLE/prompts/")
    print()

    print(c("[PROMPT] Agent Prompt 内容：", Colors.GREEN))
    print("-" * 70)
    print(prompt)
    print("-" * 70)


# ============================================================================
# 传统写作模式（保留原有功能）
# ============================================================================

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


def init_chapter(root, config, chapter_num, paths=None):
    """初始化章节"""
    if paths is None:
        paths = load_project_paths(root)
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    vol_dir = paths['output_dir'] / f'volume-{volume_num:03d}'
    vol_dir.mkdir(parents=True, exist_ok=True)

    chapter_path = vol_dir / f'chapter-{chapter_num:03d}.md'
    tasks_path = vol_dir / f'chapter-{chapter_num:03d}.tasks.md'

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


def show_write_mode(chapter_num, volume_num):
    """显示写作模式信息"""
    print(f"""
================================================================================
                    [WRITE] 写作模式：第{chapter_num}章
================================================================================
    """)


def show_write_guide():
    """显示写作指南"""
    print("""
[GUIDE] 写作指南：

1. 打开生成的 .md 文件开始写作
2. 参考 .tasks.md 中的任务清单
3. 可以参考 OUTLINE 目录下的章节大纲
4. 查阅 SPECS/ 了解人物和世界观设定

[TIPS] 提示：
- 写完后可以用 story:review <章节> 导入 AI 内容进行对比
- 用 story:learn <章节> 从修改中学习风格
- 用 story:style 查看当前风格档案
- 用 story:stats 查看学习进度
- 用 story:update-specs <章节> 检测新设定并更新文档 [推荐]
""")


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='写作模式 - 支持手动写作和 Agent Prompt 生成',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python story.py write 5                    # 初始化章节（手动写作模式）
  python story.py write 5 --show             # 生成并显示 Agent Prompt
  python story.py write 5 --prompt            # 仅显示 Prompt 部分
  python story.py write 5 --context           # 显示上下文信息

Pipeline 模式：
  python story.py write 5 --draft            # AI 根据细纲写正文草稿
  python story.py write 5 --revise            # 讨论模式修改正文
  python story.py write 5 --confirm           # 确认正文定稿

提示：
  使用 --show 或 --prompt 可以生成供 AI Agent 使用的结构化 Prompt。
  Agent 收到 Prompt 后生成内容，你可以通过 story:review 导入进行对比。
        """
    )
    parser.add_argument('chapter', nargs='?', type=int, help='章节号')
    parser.add_argument('--show', '-s', action='store_true',
                        help='生成并显示完整的 Agent Prompt')
    parser.add_argument('--prompt', '-p', action='store_true',
                        help='仅显示 Prompt 部分（不含路径信息）')
    parser.add_argument('--context', action='store_true',
                        help='显示上下文信息（引用的文件）')
    parser.add_argument('--ai-import', metavar='FILE',
                        help='导入 AI 生成的内容文件')
    parser.add_argument('--new', '-n', action='store_true',
                        help='强制创建新章节（覆盖已有）')
    # Pipeline 功能
    parser.add_argument('--draft', '-d', action='store_true',
                        help='AI 根据细纲写正文草稿')
    parser.add_argument('--revise', '-r', action='store_true',
                        help='讨论模式修改正文')
    parser.add_argument('--confirm', '-c', action='store_true',
                        help='确认正文定稿')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录，请先运行 story:init', Colors.RED)}")
        sys.exit(1)

    config = load_config(root)
    paths = load_project_paths(root)

    # 如果指定了 --ai-import，先处理导入
    if args.ai_import:
        import_ai_content(root, args.ai_import, args.chapter)
        return

    chapter_num = args.chapter
    if not chapter_num:
        chapter_num = config['progress'].get('current_chapter', 0) + 1

    # 计算卷号
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    # Pipeline: --draft 生成正文草稿
    if args.draft:
        if not chapter_num:
            print(f"  {c('[ERROR] 请指定章节号，如 story:write 5 --draft', Colors.RED)}")
            sys.exit(1)
        draft_chapter(root, chapter_num, paths=paths)
        return

    # Pipeline: --revise 讨论模式
    if args.revise:
        if not chapter_num:
            print(f"  {c('[ERROR] 请指定章节号，如 story:write 5 --revise', Colors.RED)}")
            sys.exit(1)
        revise_chapter(root, chapter_num, paths=paths)
        return

    # Pipeline: --confirm 确认正文
    if args.confirm:
        if not chapter_num:
            print(f"  {c('[ERROR] 请指定章节号，如 story:write 5 --confirm', Colors.RED)}")
            sys.exit(1)
        confirm_chapter(root, chapter_num, paths=paths)
        return

    # 如果只是生成 Prompt（不创建文件）
    if args.show or args.prompt:
        prompt = generate_agent_prompt(root, config, chapter_num, volume_num, paths=paths)

        if args.prompt:
            show_prompt_only(prompt)
        else:
            show_full_context(root, config, chapter_num, volume_num)

        print(f"""
{c('[TIP] 使用建议：', Colors.YELLOW)}
  1. 将上述 Prompt 发送给 AI Agent
  2. Agent 生成内容后，使用以下命令导入对比：
     python story.py write {chapter_num} --ai-import <文件路径>
  3. 或直接在 CONTENT/volume-{volume_num:03d}/chapter-{chapter_num:03d}.md 中查看
""")
        return

    # 传统写作模式：初始化章节
    chapter_path, tasks_path, volume_num = init_chapter(root, config, chapter_num, paths=paths)

    show_write_mode(chapter_num, volume_num)

    print(f"  [FILE] 章节文件：{chapter_path.relative_to(root)}")
    print(f"  [TASK] 任务清单：{tasks_path.relative_to(root)}")
    print(f"  [REF]  大纲参考：OUTLINE/volume-{volume_num:03d}/chapter-{chapter_num:03d}.md")
    print(f"  [SPEC] 设定参考：SPECS/")
    print()

    # 显示章节大纲预览
    outline_path = root / 'OUTLINE' / f'volume-{volume_num:03d}' / f'chapter-{chapter_num:03d}.md'
    if outline_path.exists():
        outline = outline_path.read_text(encoding='utf-8')
        print(f"  {c('[PREVIEW] 本章大纲预览：', Colors.CYAN)}")
        print('-' * 70)
        lines = outline.split('\n')[:20]
        for line in lines:
            if line.strip():
                print(f"  {line}")
        if len(outline.split('\n')) > 20:
            print(f"  ...")
        print('-' * 70)
        print()

    show_write_guide()


def import_ai_content(root, file_path, chapter_num):
    """导入 AI 生成的内容"""
    ai_file = Path(file_path)
    if not ai_file.exists():
        print(f"  {c(f'[ERROR] 文件不存在：{file_path}', Colors.RED)}")
        sys.exit(1)

    content = ai_file.read_text(encoding='utf-8')

    # 计算章节所在卷
    chapters_per = 30
    if chapter_num:
        volume_num = ((chapter_num - 1) // chapters_per) + 1
    else:
        volume_num = 1
        chapter_num = 1

    # 保存到草稿目录
    draft_dir = root / 'CONTENT' / 'draft'
    draft_dir.mkdir(exist_ok=True)

    ai_draft_path = draft_dir / f'chapter-{chapter_num:03d}.ai-draft.md'
    ai_draft_path.write_text(content, encoding='utf-8')

    word_count = count_chinese_chars(content)

    print(f"""
{c('[OK] AI 内容已导入', Colors.GREEN)}

  章节：第{chapter_num}章
  字数：约 {word_count} 字
  文件：{ai_draft_path.relative_to(root)}

{c('[TIP] 下一步操作：', Colors.YELLOW)}
  1. 在 {chapter_path.relative_to(root)} 中查看/修改内容
  2. 使用 story:review {chapter_num} 对比差异
  3. 使用 story:learn {chapter_num} 从修改中学习风格
""")


if __name__ == '__main__':
    main()
