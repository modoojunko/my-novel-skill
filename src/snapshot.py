#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:snapshot - 章节设定快照

每个章节确认定稿时，对所有设定做一次快照，记录：
- 人物当前状态（六层认知演进）
- 剧情进度
- 伏笔追踪
- 已用场景模式
- 下章开头要点

快照用于：
1. 写新章节时注入 Prompt（解决场景重复/伏笔遗漏/心理过渡缺失）
2. 讨论时参考（recall --snapshot）
3. 伏笔跨章追踪
"""

import os
import sys
import json
import argparse
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



# ============================================================================
# 工具函数
# ============================================================================


# ============================================================================
# 快照路径与读写
# ============================================================================

def get_snapshot_path(root: Path, chapter_num: int, volume_num: int = None) -> Path:
    """获取章节快照文件路径"""
    if volume_num is None:
        config = load_config(root)
        chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
        volume_num = ((chapter_num - 1) // chapters_per) + 1

    snapshot_dir = root / "OUTLINE" / f"volume-{volume_num:03d}" / "snapshots"
    return snapshot_dir / f"chapter-{chapter_num:03d}-snapshot.md"


def read_chapter_snapshot(root: Path, chapter_num: int, volume_num: int = None) -> str:
    """读取章节快照内容"""
    path = get_snapshot_path(root, chapter_num, volume_num)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def read_recent_snapshots(root: Path, chapter_num: int, count: int = 3, volume_num: int = None) -> str:
    """读取最近 N 章的快照内容（用于注入写作 Prompt）
    
    从 chapter_num 往前数 count 章，按顺序拼接。
    """
    if volume_num is None:
        config = load_config(root)
        chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
        volume_num = ((chapter_num - 1) // chapters_per) + 1

    parts = []
    start = max(1, chapter_num - count)
    for n in range(start, chapter_num):
        content = read_chapter_snapshot(root, n, volume_num)
        if content:
            parts.append(content)

    if not parts:
        return ""

    header = "## 前序章节设定快照（最近 {} 章）\n\n".format(len(parts))
    return header + "\n---\n".join(parts)


def read_recent_snapshots_for_prompt(root: Path, chapter_num: int, count: int = 3, volume_num: int = None) -> str:
    """读取并格式化最近 N 章快照，用于注入写作 Prompt
    
    与 read_recent_snapshots 不同，这个函数输出更精炼的格式，
    只保留关键信息供 AI 快速参考。
    """
    if volume_num is None:
        config = load_config(root)
        chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)
        volume_num = ((chapter_num - 1) // chapters_per) + 1

    parts = []
    start = max(1, chapter_num - count)
    for n in range(start, chapter_num):
        content = read_chapter_snapshot(root, n, volume_num)
        if content:
            # 提取关键信息，去掉 frontmatter
            clean = _strip_frontmatter(content)
            parts.append(clean)

    if not parts:
        return ""

    lines = []
    lines.append("## 前序章节设定快照")
    lines.append("")
    lines.append(f"以下是最近 {len(parts)} 章结束时的设定状态，写作时请参考：")
    lines.append("")

    for i, content in enumerate(parts):
        ch_num = start + i
        lines.append(f"### 第 {ch_num} 章结束时的状态")
        lines.append("")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)


def _strip_frontmatter(text: str) -> str:
    """去掉 YAML frontmatter"""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text.strip()


# ============================================================================
# 快照生成
# ============================================================================

SNAPSHOT_TEMPLATE = """---
chapter: {chapter_num}
volume: {volume_num}
created: {date}
word_count: {word_count}
---

# 第 {chapter_num} 章设定快照

> 本快照记录第 {chapter_num} 章确认定稿时，所有设定的状态。

## 人物状态

| 角色 | 当前心理/状态 | 对外部看法 | 认知变化（vs 上章）|
|------|-------------|-----------|-------------------|
{character_rows}

## 剧情进度

- **主线位置**：{mainline_pos}
- **本章关键事件**：{key_events}
- **下章衔接点**：{next_hook}

## 伏笔追踪

{foreshadowing}

## 已用场景模式

{used_scenes}

## 下章开头要点

{next_chapter_start}
"""


def generate_snapshot_template(chapter_num: int, volume_num: int, root: Path, paths: dict = None) -> str:
    """生成快照模板（供 AI 或人工填写）"""
    if paths is None:
        paths = load_project_paths(root)
    # 尝试读取章节正文获取字数
    content_path = paths['output_dir'] / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"
    word_count = 0
    if content_path.exists():
        content = content_path.read_text(encoding="utf-8")
        word_count = sum(1 for ch in content if '\u4e00' <= ch <= '\u9fff')

    # 尝试读取上一章快照，提取伏笔和场景
    prev_snapshot = read_chapter_snapshot(root, chapter_num - 1, volume_num) if chapter_num > 1 else ""
    prev_foreshadowing = _extract_section(prev_snapshot, "## 伏笔追踪") if prev_snapshot else "（首章，暂无伏笔）"
    prev_scenes = _extract_section(prev_snapshot, "## 已用场景模式") if prev_snapshot else "（首章，暂无已用场景）"

    # 读取人物列表
    chars_dir = paths['characters']
    character_rows = ""
    if chars_dir.exists():
        for char_file in sorted(chars_dir.glob("*.md")):
            char_name = char_file.stem
            character_rows += f"| {char_name} | （待填写） | （待填写） | （待填写） |\n"
    if not character_rows:
        character_rows = "| （暂无人物设定） | | | |\n"

    return SNAPSHOT_TEMPLATE.format(
        chapter_num=chapter_num,
        volume_num=volume_num,
        date=datetime.now().strftime("%Y-%m-%d"),
        word_count=word_count,
        character_rows=character_rows.rstrip(),
        mainline_pos="（待填写）",
        key_events="（待填写）",
        next_hook="（待填写）",
        foreshadowing=prev_foreshadowing if prev_foreshadowing else "（待填写）",
        used_scenes=prev_scenes if prev_scenes else "（待填写）",
        next_chapter_start="（待填写：本章结束时的人物位置、情绪、悬念）",
    )


def generate_snapshot_prompt(chapter_num: int, volume_num: int, root: Path, paths: dict = None) -> str:
    """生成让 AI 填充快照的 Prompt"""
    if paths is None:
        paths = load_project_paths(root)
    # 读取章节正文
    content_path = paths['output_dir'] / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"
    chapter_content = ""
    if content_path.exists():
        chapter_content = content_path.read_text(encoding="utf-8")

    # 读取章节细纲
    outline_path = root / "OUTLINE" / f"volume-{volume_num:03d}" / f"chapter-{chapter_num:03d}.md"
    chapter_outline = ""
    if outline_path.exists():
        chapter_outline = outline_path.read_text(encoding="utf-8")

    # 读取上一章快照
    prev_snapshot = read_chapter_snapshot(root, chapter_num - 1, volume_num) if chapter_num > 1 else ""

    # 读取人物设定
    chars_dir = paths['characters']
    characters = ""
    if chars_dir.exists():
        parts = []
        for char_file in sorted(chars_dir.glob("*.md")):
            parts.append(f"### {char_file.stem}\n")
            parts.append(char_file.read_text(encoding="utf-8")[:500])
        characters = "\n".join(parts)

    prompt = f"""# 设定快照生成任务

请根据第 {chapter_num} 章的正文内容，生成该章结束时的设定快照。

## 章节正文

{chapter_content[:3000] if chapter_content else "（未找到正文）"}

## 章节细纲

{chapter_outline[:1000] if chapter_outline else "（未找到细纲）"}

## 上一章快照（参考对比）

{prev_snapshot if prev_snapshot else "（首章，无前序快照）"}

## 人物设定参考

{characters[:800] if characters else "（暂无人物设定）"}

## 输出要求

请按以下格式输出第 {chapter_num} 章的设定快照：

```markdown
# 第 {chapter_num} 章设定快照

## 人物状态

| 角色 | 当前心理/状态 | 对外部看法 | 认知变化（vs 上章）|
|------|-------------|-----------|-------------------|
| 角色名 | 本章结束时的心理状态 | 对其他角色/世界的看法 | 与上章相比的变化（首章填"首次登场"）|

## 剧情进度

- **主线位置**：当前主线推进到哪里
- **本章关键事件**：3-5 个关键事件
- **下章衔接点**：本章结尾留下了什么悬念/未完成的事

## 伏笔追踪

列出当前所有伏笔状态：
- [伏笔描述] → 已回收 / 待回收（预计第X章）
- 新增伏笔标注"（新增）"

## 已用场景模式

列出所有已用过的场景模式（包括前序章节），标注章节：
- 场景模式1（第1章、第3章）
- 场景模式2（第2章）

## 下章开头要点

- 人物位置：
- 情绪状态：
- 悬念/待续：
```

注意：
1. 人物状态要体现**演进**，不能只写初始设定
2. 伏笔追踪要**跨章累积**，包含前序章节的所有伏笔
3. 已用场景模式也要**跨章累积**
4. 下章开头要点要具体，方便写下一章时衔接
"""
    return prompt


def _extract_section(text: str, section_header: str) -> str:
    """从快照文本中提取某个章节的内容"""
    if not text:
        return ""
    
    lines = text.split("\n")
    in_section = False
    section_lines = []
    
    for line in lines:
        if line.strip() == section_header:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            section_lines.append(line)
    
    return "\n".join(section_lines).strip()


# ============================================================================
# 快照操作
# ============================================================================

def create_snapshot(root: Path, chapter_num: int, volume_num: int, paths: dict = None) -> None:
    """创建章节设定快照"""
    if paths is None:
        paths = load_project_paths(root)
    snapshot_path = get_snapshot_path(root, chapter_num, volume_num)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    if snapshot_path.exists():
        print(f"\n  ⚠️  第 {chapter_num} 章快照已存在：{snapshot_path}")
        print(f"  如需重新生成，请先删除旧文件")
        return

    # 生成 Prompt 让 AI 填充
    prompt = generate_snapshot_prompt(chapter_num, volume_num, root, paths=paths)

    # 同时生成模板保存
    template = generate_snapshot_template(chapter_num, volume_num, root, paths=paths)
    snapshot_path.write_text(template, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  第 {chapter_num} 章设定快照生成")
    print(f"{'='*60}\n")
    print(f"  快照模板已保存到：{snapshot_path}")
    print(f"\n  📋 AI 填充 Prompt：\n")
    print(prompt)
    
    # 保存 Prompt 文件
    prompt_path = snapshot_path.parent / f"chapter-{chapter_num:03d}-snapshot-prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    
    print(f"\n  💡 Prompt 已保存到：{prompt_path}")
    print(f"\n  下一步：")
    print(f"    1. 将 Prompt 发送给 AI，获取填充后的快照")
    print(f"    2. 将 AI 返回的内容保存到：{snapshot_path}")
    print(f"    3. 或手动编辑快照文件")


def view_snapshot(root: Path, chapter_num: int, volume_num: int = None) -> None:
    """查看章节设定快照"""
    content = read_chapter_snapshot(root, chapter_num, volume_num)
    
    if not content:
        print(f"\n  ⚠️  第 {chapter_num} 章快照不存在")
        print(f"  请先使用 story:snapshot {chapter_num} 生成快照")
        return

    clean = _strip_frontmatter(content)
    
    print(f"\n{'='*60}")
    print(f"  第 {chapter_num} 章设定快照")
    print(f"{'='*60}\n")
    print(clean)


def list_snapshots(root: Path, volume_num: int = None) -> None:
    """列出所有快照"""
    outline_dir = root / "OUTLINE"
    if not outline_dir.exists():
        print(f"\n  暂无快照")
        return

    found = False
    for vol_dir in sorted(outline_dir.glob("volume-*")):
        if not vol_dir.is_dir():
            continue
        snapshot_dir = vol_dir / "snapshots"
        if not snapshot_dir.exists():
            continue

        snapshots = sorted(snapshot_dir.glob("chapter-*-snapshot.md"))
        if not snapshots:
            continue

        vol_name = vol_dir.name
        print(f"\n  {c(vol_name, Colors.BOLD)}")
        for snap in snapshots:
            # 提取章节号
            import re
            match = re.search(r'chapter-(\d+)', snap.name)
            if match:
                ch_num = match.group(1)
                # 读取 frontmatter 获取日期
                content = snap.read_text(encoding="utf-8")
                date = ""
                if "created:" in content:
                    for line in content.split("\n"):
                        if line.startswith("created:"):
                            date = line.split(":", 1)[1].strip()
                            break
                print(f"    第 {int(ch_num):>3} 章  {c(date, Colors.DIM)}")
        found = True

    if not found:
        print(f"\n  暂无快照")


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='章节设定快照 - 记录每章结束时的设定状态',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  story:snapshot 5              # 为第5章生成设定快照
  story:snapshot 5 --view       # 查看第5章快照
  story:snapshot --list         # 列出所有快照
  story:snapshot 5 --prompt     # 仅显示 AI 填充 Prompt

说明：
  快照在章节确认定稿时自动生成（story:write N --confirm）。
  也可手动使用本命令生成。
  快照保存到 OUTLINE/volume-N/snapshots/chapter-NNN-snapshot.md
        """
    )
    parser.add_argument('chapter', nargs='?', type=int, help='章节号')
    parser.add_argument('--view', '-v', action='store_true',
                        help='查看章节快照')
    parser.add_argument('--list', '-l', action='store_true',
                        help='列出所有快照')
    parser.add_argument('--prompt', '-p', action='store_true',
                        help='仅显示 AI 填充 Prompt')
    parser.add_argument('--volume', type=int,
                        help='指定卷号（默认自动计算）')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录，请先运行 story:init', Colors.RED)}")
        sys.exit(1)

    config = load_config(root)
    paths = load_project_paths(root)
    chapters_per = config.get("structure", {}).get("chapters_per_volume", 30)

    # 列出所有快照
    if args.list:
        list_snapshots(root, args.volume)
        return

    if not args.chapter:
        print(f"  {c('[ERROR] 请指定章节号', Colors.RED)}")
        print(f"  用法：story:snapshot <章节号>")
        sys.exit(1)

    chapter_num = args.chapter
    volume_num = args.volume or ((chapter_num - 1) // chapters_per) + 1

    # 仅显示 Prompt
    if args.prompt:
        prompt = generate_snapshot_prompt(chapter_num, volume_num, root, paths=paths)
        print(prompt)
        return

    # 查看快照
    if args.view:
        view_snapshot(root, chapter_num, volume_num)
        return

    # 创建快照
    create_snapshot(root, chapter_num, volume_num, paths=paths)


if __name__ == '__main__':
    main()
