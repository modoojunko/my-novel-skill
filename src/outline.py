#!/usr/bin/env python3
"""
story:outline - 编辑大纲

提供交互式的大纲编辑功能。
使用 JSON 作为配置文件格式。

支持流水线模式：
- --draft: AI 生成章节细纲草稿
- --revise: 讨论模式修改细纲
- --confirm: 确认细纲定稿
"""

import os
import sys
import json
import re
import tempfile
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

def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


# ============================================================
# Pipeline Stage 管理（从 plan.py 复用）
# ============================================================

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


def get_volume_stage(volume_num: int, root: Path) -> str:
    """获取卷 stage"""
    pipeline = load_pipeline_state(root)
    return pipeline["volumes"].get(str(volume_num), {}).get("stage", "")


# ============================================================
# 章节细纲 AI 生成
# ============================================================

def generate_chapter_draft_prompt(root: Path, chapter_num: int, config: dict) -> str:
    """生成章节细纲的 Prompt"""
    meta = config.get("meta", {})
    chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    title = meta.get("title", "未命名小说")
    genre = meta.get("genre", "未知")

    # 读取卷纲
    vol_outline_path = root / "OUTLINE" / f"volume-{volume_num:03d}" / f"volume-{volume_num:03d}-outline.md"
    volume_outline = ""
    if vol_outline_path.exists():
        volume_outline = vol_outline_path.read_text(encoding="utf-8")

    # 读取上一章细纲（用于衔接）
    prev_chapter_outline = ""
    if chapter_num > 1:
        prev_path = root / "OUTLINE" / f"volume-{volume_num:03d}" / f"chapter-{chapter_num-1:03d}.md"
        if prev_path.exists():
            prev_chapter_outline = prev_path.read_text(encoding="utf-8")

    # 读取风格档案
    style_path = root / "style" / "style.md"
    style_guide = ""
    if style_path.exists():
        style_guide = style_path.read_text(encoding="utf-8")

    prompt = f"""# 第 {chapter_num} 章细纲生成任务

## 基本信息
- **书名**：{title}
- **类型**：{genre}
- **当前卷**：第 {volume_num} 卷
- **当前章**：第 {chapter_num} 章

## 卷纲摘要
{volume_outline[:1000] if volume_outline else "（暂无卷纲）"}

{"## 上一章摘要" if prev_chapter_outline else ""}
{prev_chapter_outline[:500] if prev_chapter_outline else ""}

## 风格指南
{style_guide[:500] if style_guide else "（暂无风格指南）"}

## 输出格式

请按以下结构输出第 {chapter_num} 章细纲：

```
# 第 {chapter_num} 章：xxx（章节主题）

## 本章目标
（本章要完成的核心任务，1-2句话）

## POV
（本章的主要视点人物）

## 情绪基调
（本章的情感色彩：紧张/温馨/虐心/热血...）

## 信息密度节奏
- **类型**：（slow / medium / fast / escalation）
- **与上章关系**：（承接 / 递进 / 爆发 / 缓冲）
- **本章事件密度**：高/中/低
- **字数分配**：各场景字数比例（如开场800/发展1200/转折1000/结尾500）

## 场景列表
1. [开场] 场景描述 - POV:xxx - 约800字
   - 核心动作：（发生什么）
   - 情绪：（此刻人物感受）
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

2. [发展] 场景描述 - POV:xxx - 约1200字
   - 核心动作：xxx
   - 情绪：xxx
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

3. [转折] 场景描述 - POV:xxx - 约1000字
   - 核心动作：xxx
   - 情绪：xxx
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

4. [结尾] 场景描述 - POV:xxx - 约500字
   - 悬念/衔接：（留下什么钩子）
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

## POV认知状态说明
每个场景的POV角色都有独立的认知边界。写作时必须参考该角色设定文件中的"当前状态"章节：
- **已知角色**：POV角色已经知道名字的人，可以直接称呼
- **未知角色**：POV角色尚未获知名字的人，必须用外貌/身份代称（如"那女孩"、"穿校服的学生"）
- **已掌握信息**：POV角色已经知道的事实
- **待揭示信息**：POV角色还不知道，将在本章或后续揭示的内容

## 关键对话
- 「角色1」：「台词内容」（目的/情绪）
- 「角色2」：「台词内容」（目的/情绪）

## 伏笔记录
- 伏笔1：埋下/呼应
- 伏笔2：...

## 与上章的衔接
（如何从上一章自然过渡到本章开头）

## 预期字数
约 3000-4000 字

---
*此细纲由 AI 生成，可使用 story:outline --revise {chapter_num} 进行讨论修改*
```
"""
    return prompt


def generate_chapter_draft(root: Path, chapter_num: int, config: dict, paths: dict = None, args_json: bool = False) -> None:
    """生成章节细纲草稿"""
    if paths is None:
        paths = load_project_paths(root)
    chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    vol_dir = root / "OUTLINE" / f"volume-{volume_num:03d}"
    vol_dir.mkdir(parents=True, exist_ok=True)

    chapter_path = vol_dir / f"chapter-{chapter_num:03d}.md"

    # 检查是否已有细纲
    if chapter_path.exists():
        if args_json:
            output_json_result({
                "error": "已有细纲",
                "target_file": str(chapter_path),
                "next_step": "使用 --revise 进入讨论模式，或 --confirm 确认定稿"
            })
        else:
            print(f"\n  ⚠️  第 {chapter_num} 章已有细纲：{chapter_path}")
            print(f"  使用 --revise 进入讨论模式，或 --confirm 确认定稿")
        return

    # 生成 Prompt
    prompt = generate_chapter_draft_prompt(root, chapter_num, config)

    # 保存 Prompt
    prompt_dir = get_prompt_storage_dir(root, paths)
    prompt_filename = f"outline-draft-chapter-{chapter_num:03d}-prompt.md"
    prompt_file = save_prompt_to_file(prompt, prompt_dir, prompt_filename)

    # 构建导入命令
    import_cmd = f"story outline --draft {chapter_num} --ai <your_output_file>"

    if args_json:
        # JSON 模式输出
        result = {
            "type": "outline-draft",
            "target": f"chapter-{chapter_num:03d}",
            "prompt_file": str(prompt_file),
            "prompt_content": prompt,
            "next_step": "请基于这个 prompt 生成章节细纲内容，只返回完整的章节细纲内容",
            "import_command": import_cmd,
            "target_file": str(chapter_path)
        }
        output_json_result(result)
    else:
        # 普通模式输出
        print(f"\n{c('═' * 80, Colors.CYAN)}")
        print(f"  {c('🤖 给 AI Agent 的 Prompt', Colors.BOLD)}")
        print(f"{c('═' * 80, Colors.CYAN)}\n")
        print(prompt)
        print(f"\n{c('═' * 80, Colors.CYAN)}")
        print(f"  {c('📋 Agent 操作指南', Colors.BOLD)}")
        print(f"{c('═' * 80, Colors.CYAN)}\n")
        print(f"  1. 基于上面的 Prompt 生成章节细纲")
        print(f"  2. 只返回完整的章节细纲内容")
        print(f"  3. 将你的输出保存到临时文件，或直接传递给 --ai 选项")
        print(f"  4. 运行：{c(import_cmd, Colors.BOLD)}")
        print(f"\n  💡 Prompt 已保存到：{c(prompt_file, Colors.DIM)}")
        print(f"{c('═' * 80, Colors.CYAN)}\n")

    # 更新 stage
    update_chapter_stage(chapter_num, "outline-draft", root)
    if not args_json:
        print(f"\n  ✓ 第 {chapter_num} 章 stage 已更新为: outline-draft")


def generate_all_chapter_drafts(root: Path, volume_num: int, config: dict) -> None:
    """批量生成本卷所有章节细纲"""
    chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
    start_chapter = (volume_num - 1) * chapters_per + 1
    end_chapter = volume_num * chapters_per

    print(f"\n{'='*60}")
    print(f"  批量生成卷 {volume_num} 的章节细纲")
    print(f"{'='*60}")
    print(f"\n  卷 {volume_num} 共 {chapters_per} 章（第 {start_chapter} - {end_chapter} 章）")
    print(f"  将为每章生成细纲生成 Prompt...\n")

    generated = []
    skipped = []

    for ch_num in range(start_chapter, end_chapter + 1):
        vol_dir = root / "OUTLINE" / f"volume-{volume_num:03d}"
        vol_dir.mkdir(parents=True, exist_ok=True)
        chapter_path = vol_dir / f"chapter-{ch_num:03d}.md"

        if chapter_path.exists():
            skipped.append(ch_num)
            continue

        # 生成 Prompt
        prompt = generate_chapter_draft_prompt(root, ch_num, config)
        prompt_file = vol_dir / f"chapter-{ch_num:03d}-draft-prompt.md"

        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        # 更新 stage
        update_chapter_stage(ch_num, "outline-draft", root)
        generated.append(ch_num)

    if generated:
        print(f"  ✓ 已生成 {len(generated)} 个 Prompt：")
        for ch in generated[:5]:
            print(f"       + chapter-{ch:03d}-draft-prompt.md")
        if len(generated) > 5:
            print(f"       ... 还有 {len(generated) - 5} 个")
    if skipped:
        print(f"  -- 已跳过 {len(skipped)} 个已有细纲的章节")

    print(f"\n  下一步：")
    print(f"    1. 将 Prompt 文件发送给 AI 获取细纲草稿")
    print(f"    2. 将 AI 返回的内容保存为 chapter-XXX.md")
    print(f"    3. 使用 story:outline --revise {start_chapter} 逐章讨论修改")
    print(f"    4. 全部确认后使用 story:write {start_chapter} --draft 开始写正文")


def revise_chapter_outline(root: Path, chapter_num: int, config: dict) -> None:
    """讨论模式修改章节细纲"""
    chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = root / "OUTLINE" / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"

    if not chapter_path.exists():
        print(f"\n  错误：第 {chapter_num} 章还没有细纲文件")
        print(f"  请先使用 story:outline --draft {chapter_num} 生成细纲")
        return

    current_stage = get_chapter_stage(chapter_num, root)
    print(f"\n  📝 第 {chapter_num} 章当前 stage: {current_stage or '未设置'}")
    print(f"\n  请告诉我你想如何修改细纲：")
    print(f"     1. 调整场景顺序/数量")
    print(f"     2. 修改 POV")
    print(f"     3. 调整情绪基调")
    print(f"     4. 修改关键对话")
    print(f"     5. 其他修改")
    print(f"\n  修改完成后，将新内容保存到：{chapter_path}")
    print(f"  然后使用 story:outline --confirm {chapter_num} 确认定稿")


def confirm_chapter_outline(root: Path, chapter_num: int) -> None:
    """确认章节细纲定稿"""
    chapters_per = 30  # 默认值
    try:
        config_path = root / "story.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
    except:
        pass

    volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = root / "OUTLINE" / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"

    if not chapter_path.exists():
        print(f"\n  错误：第 {chapter_num} 章还没有细纲文件")
        print(f"  请先使用 story:outline --draft {chapter_num} 生成细纲")
        return

    update_chapter_stage(chapter_num, "outline-confirmed", root)

    print(f"\n  ✓ 第 {chapter_num} 章细纲已确认定稿")
    print(f"  ✓ stage 已更新为: outline-confirmed")
    print(f"\n  下一步建议：")
    print(f"    story:write {chapter_num} --draft  →  AI 根据细纲写正文")
    print(f"    story:outline --revise {chapter_num}  →  继续修改细纲")


def ensure_outline_dirs(root, volumes):
    """确保大纲目录存在"""
    outline_dir = root / 'OUTLINE'
    outline_dir.mkdir(exist_ok=True)

    for i in range(1, volumes + 1):
        vol_dir = outline_dir / f'volume-{i:03d}'
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
    vol_path = root / 'OUTLINE' / f'volume-{volume_num:03d}.md'

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

    vol_dir = root / 'OUTLINE' / f'volume-{volume_num:03d}'
    vol_dir.mkdir(exist_ok=True)

    chapter_path = vol_dir / f'chapter-{chapter_num:03d}.md'

    if not chapter_path.exists():
        content = f"""# 第{chapter_num}章：xxx

## 本章目标
（待填充）

## POV
（待填充 - 本章的主要视点人物）

## 情绪基调
（待填充 - 紧张/温馨/虐心/热血...）

## 信息密度节奏
- **类型**：（slow / medium / fast / escalation，待填充）
- **与上章关系**：（承接 / 递进 / 爆发 / 缓冲，待填充）
- **本章事件密度**：高/中/低（待填充）

## 场景列表
1. [开场] 场景描述 - POV:xxx - 约800字
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

2. [发展] 场景描述 - POV:xxx - 约1200字
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

3. [转折] 场景描述 - POV:xxx - 约1000字
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

## 情节点
（待填充）

## 关键对话
（待填充）

## 伏笔记录
（待填充）

## 预期字数
约 3000 字

## POV认知状态说明
写作时必须遵守POV角色的认知边界。参考该角色设定文件中的"当前状态"章节：
- **已知角色**：可以直接称呼名字
- **未知角色**：用外貌/身份代称（如"那女孩"、"穿校服的学生"）
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
        vol_dir = root / 'OUTLINE' / f'volume-{volume_num:03d}'
        vol_dir.mkdir(exist_ok=True)
        chapter_path = vol_dir / f'chapter-{ch_num:03d}.md'

        if not chapter_path.exists():
            content = f"""# 第{ch_num}章：xxx

## 本章目标
（待填充）

## POV
（待填充 - 本章的主要视点人物）

## 场景列表
1. [开场] 场景描述 - POV:xxx - 约800字
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

2. [发展] 场景描述 - POV:xxx - 约1200字
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

3. [转折] 场景描述 - POV:xxx - 约1000字
   - 认知状态引用：参考 SPECS/characters/[POV角色名].md 的"当前状态"章节

## 情节点
（待填充）

## 关键对话
（待填充）

## 伏笔记录
（待填充）

## 预期字数
约 3000 字

## POV认知状态说明
写作时必须遵守POV角色的认知边界。参考该角色设定文件中的"当前状态"章节：
- **已知角色**：可以直接称呼名字
- **未知角色**：用外貌/身份代称（如"那女孩"、"穿校服的学生"）
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
        vol_path = root / 'OUTLINE' / f'volume-{v:03d}.md'
        vol_status = '[OK]' if vol_path.exists() else '[ ]'
        print(f"  |-- volume-{v:03d}.md {vol_status}")

        vol_dir = root / 'OUTLINE' / f'volume-{v:03d}'
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

    chapter_path = root / 'OUTLINE' / f'volume-{volume_num:03d}' / f'chapter-{chapter_num:03d}.md'

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
        outline_dir = root / 'OUTLINE' / f'volume-{vol_num:03d}'
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


def output_json_result(result: dict) -> None:
    """输出 JSON 格式结果"""
    print(json.dumps(result, ensure_ascii=False, indent=2))


def get_prompt_storage_dir(root: Path, paths: dict) -> Path:
    """获取 prompt 存储目录"""
    prompt_dir = paths['outline'] / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    return prompt_dir


def save_prompt_to_file(prompt: str, prompt_dir: Path, filename: str) -> Path:
    """保存 prompt 到文件"""
    prompt_file = prompt_dir / filename
    prompt_file.write_text(prompt, encoding="utf-8")
    return prompt_file


def main():
    import argparse

    parser = argparse.ArgumentParser(description='编辑大纲')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式（Agent 驱动模式）')
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
    # Pipeline 功能
    parser.add_argument('--draft', '-d', type=int, metavar='CHAPTER',
                        help='AI 生成章节细纲草稿')
    parser.add_argument('--revise', '-r', action='store_true',
                        help='讨论模式修改细纲')
    parser.add_argument('--confirm', action='store_true',
                        help='确认细纲定稿')
    parser.add_argument('--all', '-a', action='store_true',
                        help='批量处理（需配合 --draft 使用）')
    parser.add_argument('--volume', '-v', type=int, metavar='N',
                        help='卷号（需配合 --draft --all 使用）')
    parser.add_argument('--ai', help='从文件导入 AI 生成内容')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        if args.json:
            output_json_result({"error": "未找到项目目录，请先运行 story:init"})
        else:
            print(f"  [ERROR] 未找到项目目录")
        sys.exit(1)

    config = load_config(root)
    paths = load_project_paths(root)

    volumes = config.get('structure', {}).get('volumes', 1)
    ensure_outline_dirs(root, volumes)

    # 如果有 --ai 选项，导入 AI 生成的内容
    if args.ai and args.draft:
        ai_file = Path(args.ai)
        if not ai_file.exists():
            if args.json:
                output_json_result({"error": f"AI 文件不存在: {ai_file}"})
            else:
                print(f"  {c('错误', Colors.RED)}: AI 文件不存在: {ai_file}")
            sys.exit(1)

        ai_content = ai_file.read_text(encoding="utf-8")
        chapter_num = args.draft
        chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
        volume_num = ((chapter_num - 1) // chapters_per) + 1
        chapter_path = paths['outline'] / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"

        if not chapter_path.parent.exists():
            chapter_path.parent.mkdir(parents=True, exist_ok=True)

        chapter_path.write_text(ai_content, encoding="utf-8")

        if args.json:
            output_json_result({
                "type": "outline-draft-imported",
                "target": f"chapter-{chapter_num:03d}",
                "target_file": str(chapter_path),
                "next_step": f"使用 story outline --revise {chapter_num} 进行讨论修改，或 story outline --confirm {chapter_num} 确认定稿"
            })
        else:
            print(f"  {c('OK', Colors.GREEN)}: 已写入 {chapter_path}")
        return

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
                print(f"       + OUTLINE/volume-{vol_num:03d}/chapter-{ch_num:03d}.md")
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

    # Pipeline: --draft 生成章节细纲
    if args.draft:
        chapter_num = args.draft

        if args.all and args.volume:
            # 批量生成
            generate_all_chapter_drafts(root, args.volume, config)
        else:
            # 单章生成
            generate_chapter_draft(root, chapter_num, config, paths=paths, args_json=args.json)
        return

    # Pipeline: --revise 讨论模式
    if args.revise:
        if not args.target:
            print(f"  错误：请指定要讨论的章节号，如 story:outline --revise 5")
            sys.exit(1)
        match = re.search(r'(\d+)', str(args.target))
        if not match:
            print(f"  错误：无法解析章节号")
            sys.exit(1)
        chapter_num = int(match.group(1))
        revise_chapter_outline(root, chapter_num, config)
        return

    # Pipeline: --confirm 确认细纲
    if args.confirm:
        if not args.target:
            print(f"  错误：请指定要确认的章节号，如 story:outline --confirm 5")
            sys.exit(1)
        match = re.search(r'(\d+)', str(args.target))
        if not match:
            print(f"  错误：无法解析章节号")
            sys.exit(1)
        chapter_num = int(match.group(1))
        confirm_chapter_outline(root, chapter_num)
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
            match = re.search(r'(\d+)', target)
            if match:
                num = int(match.group(1))
                path = edit_chapter_outline(root, config, num)
                print(f"  [OK] 已打开：{path}")

    print(f"\n  提示：直接用编辑器打开对应的 .md 文件进行编辑")
    print()

if __name__ == '__main__':
    main()
