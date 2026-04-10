#!/usr/bin/env python3
"""
卷纲生成与章节拆分模块

支持：
- 卷纲草稿生成（从主线文件或交互式问答）
- 卷纲讨论修改（--revise）
- 卷纲确认定稿（--confirm）
- 章节拆分（--chapters）
- 章节讨论修改与确认
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import re

# ============================================================
# Stage 管理辅助函数
# ============================================================

def get_root():
    """获取项目根目录"""
    return Path.cwd()


def load_config(root: Optional[Path] = None) -> Dict[str, Any]:
    """加载项目配置"""
    if root is None:
        root = get_root()
    config_path = root / "story.json"
    if not config_path.exists():
        print(f"  错误：未找到 story.json，请先运行 story:init")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(root: Path, config: Dict[str, Any]) -> None:
    """保存项目配置"""
    config_path = root / "story.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_pipeline_state(root: Path) -> Dict[str, Any]:
    """加载/初始化流水线状态"""
    config = load_config(root)
    if "pipeline" not in config:
        config["pipeline"] = {
            "volumes": {},
            "chapters": {}
        }
    return config["pipeline"]


def save_pipeline_state(root: Path, pipeline: Dict[str, Any]) -> None:
    """保存流水线状态"""
    config = load_config(root)
    config["pipeline"] = pipeline
    save_config(root, config)


def get_chapter_stage(chapter_num: int, root: Optional[Path] = None) -> str:
    """获取章节 stage"""
    if root is None:
        root = get_root()
    pipeline = load_pipeline_state(root)
    return pipeline["chapters"].get(str(chapter_num), {}).get("stage", "")


def update_chapter_stage(chapter_num: int, new_stage: str, root: Optional[Path] = None) -> None:
    """更新章节 stage"""
    if root is None:
        root = get_root()
    pipeline = load_pipeline_state(root)
    if str(chapter_num) not in pipeline["chapters"]:
        pipeline["chapters"][str(chapter_num)] = {}
    pipeline["chapters"][str(chapter_num)]["stage"] = new_stage
    save_pipeline_state(root, pipeline)


def get_volume_stage(volume_num: int, root: Optional[Path] = None) -> str:
    """获取卷 stage"""
    if root is None:
        root = get_root()
    pipeline = load_pipeline_state(root)
    return pipeline["volumes"].get(str(volume_num), {}).get("stage", "")


def update_volume_stage(volume_num: int, new_stage: str, root: Optional[Path] = None) -> None:
    """更新卷 stage"""
    if root is None:
        root = get_root()
    pipeline = load_pipeline_state(root)
    if str(volume_num) not in pipeline["volumes"]:
        pipeline["volumes"][str(volume_num)] = {}
    pipeline["volumes"][str(volume_num)]["stage"] = new_stage
    save_pipeline_state(root, pipeline)


def init_chapter_stages(root: Path, volume_num: int, chapter_count: int, from_chapter: int = 1) -> None:
    """批量初始化章节 stage"""
    pipeline = load_pipeline_state(root)
    for i in range(chapter_count):
        ch_num = from_chapter + i
        if str(ch_num) not in pipeline["chapters"]:
            pipeline["chapters"][str(ch_num)] = {}
        pipeline["chapters"][str(ch_num)]["stage"] = "outline-draft"
        pipeline["chapters"][str(ch_num)]["volume"] = volume_num
    save_pipeline_state(root, pipeline)


# ============================================================
# 工具函数
# ============================================================

def read_main_story(root: Path) -> Optional[str]:
    """读取主线故事文件"""
    # 可能的文件名
    candidates = [
        root / "story-concept.md",
        root / "story-main.md",
        root / "MAIN.md",
        root / "main.md",
    ]
    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return None


def get_volume_dir(root: Path, volume_num: int) -> Path:
    """获取卷目录"""
    return root / "OUTLINE" / f"volume-{volume_num:03d}"


def get_volume_outline_file(root: Path, volume_num: int) -> Path:
    """获取卷纲文件路径"""
    return get_volume_dir(root, volume_num) / f"volume-{volume_num:03d}-outline.md"


def parse_chapter_args(chapter_arg: str) -> tuple:
    """解析章节参数，支持单章或范围"""
    if "-" in chapter_arg:
        parts = chapter_arg.split("-")
        return (int(parts[0]), int(parts[1]))
    else:
        num = int(chapter_arg)
        return (num, num)


# ============================================================
# 卷纲生成
# ============================================================

def generate_volume_outline_prompt(root: Path, volume_num: int, main_story: str, config: Dict) -> str:
    """生成卷纲的 Prompt"""
    meta = config.get("meta", {})
    genre = meta.get("genre", "未知")
    theme = meta.get("theme", "未知")
    target_words = meta.get("targetWords", "未知")
    total_volumes = meta.get("volumes", 1)
    title = meta.get("title", "未命名小说")

    prompt = f"""# 卷纲生成任务

请为小说《{title}》的第 {volume_num} 卷设计卷纲。

## 基本信息
- **类型**：{genre}
- **主题**：{theme}
- **目标字数**：{target_words}
- **总卷数**：{total_volumes}
- **当前卷**：第 {volume_num} 卷

## 主线故事
{main_story}

## 输出格式

请按以下结构输出第 {volume_num} 卷的卷纲：

```
# 第 {volume_num} 卷卷纲（草稿）

## 卷主题
（用一句话概括本卷的核心主题）

## 起承转合

### 起（卷首，约占 20%）
（开篇事件、背景设定）

### 承（发展，约占 30%）
（主要冲突、人物关系变化）

### 转（高潮，约占 30%）
（核心转折、高潮事件）

### 合（收尾，约占 20%）
（收束线索、埋下伏笔）

## 节奏曲线
（规划本章各章节的信息密度节奏，全局统筹，不要每章都同样节奏）
- 第X章：铺垫/慢热（信息密度低，氛围建立）
- 第X章：推进/上升（密度渐增，冲突展开）
- 第X章：高潮/爆发（密度峰值，重大揭示）
- 第X章：缓冲/回落（密度下降，情绪过渡）
（根据实际章节数调整，必须有明显的密度起伏，禁止连续两章节奏相同）

## 核心事件
1. ...
2. ...
3. ...
4. ...
5. ...

## 高潮设计
（本章最精彩的情节点）

## 伏笔布局
- 伏笔1：...
- 伏笔2：...

## 与前后卷的衔接
- **承接上卷**：...
- **启下卷**：...

---
*此卷纲由 AI 生成，可使用 story:plan --volume {volume_num} --revise 进行讨论修改*
"""
    return prompt


def generate_volume_outline(root: Path, volume_num: int, interactive: bool = False,
                            conflict: str = None, arc: str = None,
                            events: str = None, tone: str = None) -> None:
    """生成卷纲草稿"""
    config = load_config(root)
    volume_dir = get_volume_dir(root, volume_num)
    volume_dir.mkdir(parents=True, exist_ok=True)

    outline_file = get_volume_outline_file(root, volume_num)

    # 检查是否已有卷纲
    if outline_file.exists():
        print(f"\n  ⚠️  卷 {volume_num} 已有卷纲：{outline_file}")
        print(f"  使用 --revise 进入讨论模式，或 --confirm 确认定稿")
        return

    if interactive or conflict is not None:
        # 交互模式或非交互参数化模式
        main_story = run_interactive_main_story(config, conflict=conflict, arc=arc,
                                                 events=events, tone=tone)
    else:
        main_story = read_main_story(root)
        if not main_story:
            print(f"\n  错误：未找到主线故事文件（story-concept.md 或 story-main.md）")
            print(f"  请先创建主线文件，或使用 --interactive 进入问答模式")
            return

    prompt = generate_volume_outline_prompt(root, volume_num, main_story, config)

    # 保存 Prompt 到文件
    prompt_file = volume_dir / f"volume-{volume_num:03d}-outline-prompt.md"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    # 初始化卷 stage
    update_volume_stage(volume_num, "draft", root)

    if args.json:
        # JSON 模式输出
        result = {
            "type": "plan-volume-outline",
            "volume": volume_num,
            "prompt_file": str(prompt_file),
            "prompt_content": prompt,
            "next_step": "请基于这个 prompt 生成卷纲，包含起承转合、核心事件、高潮设计等",
            "target_file": str(outline_file),
            "stage_updated": "draft"
        }
        output_json_result(result)
    else:
        # 普通模式输出
        print(f"\n{'='*80}")
        print(f"  🤖 给 AI Agent 的 Prompt")
        print(f"{'='*80}\n")
        print(prompt)
        print(f"\n{'='*80}")
        print(f"  📋 Agent 操作指南")
        print(f"{'='*80}\n")
        print(f"  1. 基于上面的 Prompt 生成卷纲")
        print(f"  2. 卷纲要包含：起承转合、核心事件、高潮设计、伏笔布局")
        print(f"  3. 将你的输出保存到：{outline_file}")
        print(f"  4. 然后使用：story:plan --volume {volume_num} --revise 进行讨论修改")
        print(f"  5. 确认后使用：story:plan --volume {volume_num} --confirm")
        print(f"\n  💡 Prompt 已保存到：{prompt_file}")
        print(f"\n  ✓ 卷 {volume_num} stage 已更新为: draft")
        print(f"{'='*80}\n")


def run_interactive_main_story(config: Dict, conflict: str = None, arc: str = None,
                               events: str = None, tone: str = None) -> str:
    """收集主线信息（交互式或参数化）

    Args:
        config: 项目配置
        conflict: 核心冲突（有值时跳过交互）
        arc: 主角成长弧线
        events: 核心事件（逗号分隔）
        tone: 情感基调
    """
    # 非交互模式：使用参数
    if conflict is not None:
        core_conflict = conflict or "未填写"
        arc = arc or "未填写"
        if events:
            event_list = [e.strip() for e in events.split(',') if e.strip()]
            events_str = "\n".join([f"{i+1}. {e}" for i, e in enumerate(event_list)]) if event_list else "未填写"
        else:
            events_str = "未填写"
        tone = tone or "混合"
    else:
        # 交互模式
        print("\n" + "="*60)
        print("  交互式主线信息收集")
        print("="*60)
        print("\n  让我们一步步梳理你的故事主线...\n")

        print("-"*60)

        # 核心冲突
        print("\n  1. 核心冲突是什么？")
        print("     （主角面临的主要矛盾或困境）")
        core_conflict = input("  > ").strip()
        if not core_conflict:
            core_conflict = "未填写"

        # 主角弧线
        print("\n  2. 主角的成长弧线？")
        print("     （主角从...到...的转变）")
        arc = input("  > ").strip()
        if not arc:
            arc = "未填写"

        # 核心事件
        print("\n  3. 最重要的 2-3 个事件？")
        print("     （Enter 跳过）")
        event_list = []
        for i in range(1, 4):
            event = input(f"    事件{i}: ").strip()
            if event:
                event_list.append(event)
        events_str = "\n".join([f"{i+1}. {e}" for i, e in enumerate(event_list)]) if event_list else "未填写"

        # 情感基调
        print("\n  4. 故事的情感基调？")
        print("     （虐/甜/热血/悬疑/轻松...）")
        tone = input("  > ").strip() or "混合"

        print("\n" + "-"*60)

    # 组装主线
    main_story = f"""## 核心冲突
{core_conflict}

## 主角成长弧线
{arc}

## 核心事件
{events_str}

## 情感基调
{tone}
"""
    return main_story


def revise_volume_outline(root: Path, volume_num: int) -> None:
    """讨论模式修改卷纲"""
    outline_file = get_volume_outline_file(root, volume_num)

    if not outline_file.exists():
        print(f"\n  错误：卷 {volume_num} 还没有卷纲文件")
        print(f"  请先使用 story:plan --volume {volume_num} 生成卷纲")
        return

    current_stage = get_volume_stage(volume_num, root)
    print(f"\n  📝 卷 {volume_num} 当前 stage: {current_stage or '未设置'}")
    print(f"\n  请告诉我你想如何修改卷纲：")
    print(f"     1. 调整起承转合结构")
    print(f"     2. 增减核心事件")
    print(f"     3. 修改高潮设计")
    print(f"     4. 调整伏笔布局")
    print(f"     5. 其他修改")
    print(f"\n  你可以直接描述想要的修改，我会帮你调整。")
    print(f"\n  修改完成后，将新内容保存到：{outline_file}")
    print(f"  然后使用 story:plan --volume {volume_num} --confirm 确认定稿")


def confirm_volume_outline(root: Path, volume_num: int) -> None:
    """确认卷纲定稿"""
    outline_file = get_volume_outline_file(root, volume_num)

    if not outline_file.exists():
        print(f"\n  错误：卷 {volume_num} 还没有卷纲文件")
        print(f"  请先使用 story:plan --volume {volume_num} 生成卷纲")
        return

    print(f"\n  ✓ 确认卷 {volume_num} 卷纲定稿")
    update_volume_stage(volume_num, "confirmed", root)

    # 提示下一步
    print(f"\n  ✓ 卷 {volume_num} stage 已更新为: confirmed")
    print(f"\n  下一步建议：")
    print(f"    1. story:plan --chapters {volume_num}  → 拆分章节列表")
    print(f"    2. story:plan --chapters {volume_num} --interactive  → 交互式拆分")


# ============================================================
# 章节拆分
# ============================================================

def split_chapters_prompt(root: Path, volume_num: int, volume_outline: str, config: Dict) -> str:
    """生成章节拆分的 Prompt"""
    meta = config.get("meta", {})
    genre = meta.get("genre", "未知")
    theme = meta.get("theme", "未知")
    title = meta.get("title", "未命名小说")
    total_volumes = meta.get("volumes", 1)

    prompt = f"""# 章节拆分任务

请为小说《{title}》第 {volume_num} 卷拆分章节。

## 基本信息
- **类型**：{genre}
- **主题**：{theme}
- **总卷数**：{total_volumes}

## 卷纲
{volume_outline}

## 输出格式

请输出章节列表，格式如下：

```
| 章节 | POV | 核心内容 | 字数预估 | 情绪基调 |
|------|-----|---------|---------|---------|
| 第1章 | 张三 | 开场：主角出场，引入核心冲突 | ~1500字 | 平静 |
| 第2章 | 张三 | 冲突升级，主角做出选择 | ~2000字 | 紧张 |
| ... | ... | ... | ... | ... |
| 第N章 | XXX | 收尾：本卷结束，埋下悬念 | ~1500字 | 悬念 |
```

---
*此列表由 AI 生成，可使用 story:plan --chapters {volume_num} --revise 进行讨论修改*
"""
    return prompt


def split_chapters(root: Path, volume_num: int, interactive: bool = False) -> None:
    """拆分章节列表"""
    config = load_config(root)
    outline_file = get_volume_outline_file(root, volume_num)

    if not outline_file.exists():
        print(f"\n  错误：卷 {volume_num} 还没有卷纲文件")
        print(f"  请先使用 story:plan --volume {volume_num} --confirm 确认卷纲")
        return

    volume_dir = get_volume_dir(root, volume_num)
    chapters_file = volume_dir / f"volume-{volume_num:03d}-chapters.md"

    # 读取卷纲
    with open(outline_file, "r", encoding="utf-8") as f:
        volume_outline = f.read()

    prompt = split_chapters_prompt(root, volume_num, volume_outline, config)

    print(f"\n{'='*60}")
    print(f"  卷 {volume_num} 章节拆分 Prompt")
    print(f"{'='*60}\n")
    print(prompt)

    # 保存 Prompt
    prompt_file = volume_dir / f"volume-{volume_num:03d}-chapters-prompt.md"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"\n  💡 Prompt 已保存到：{prompt_file}")
    print(f"\n  下一步：")
    print(f"    1. 将此 Prompt 发送给 AI 获取章节列表")
    print(f"    2. 将 AI 返回的内容保存到 {chapters_file}")
    print(f"    3. 使用 story:plan --chapters {volume_num} --revise 进行讨论修改")
    print(f"    4. 确认后使用 story:plan --chapters {volume_num} --confirm")


def revise_chapters(root: Path, volume_num: int) -> None:
    """讨论模式修改章节列表"""
    volume_dir = get_volume_dir(root, volume_num)
    chapters_file = volume_dir / f"volume-{volume_num:03d}-chapters.md"

    if not chapters_file.exists():
        print(f"\n  错误：卷 {volume_num} 还没有章节列表")
        print(f"  请先使用 story:plan --chapters {volume_num} 生成章节列表")
        return

    print(f"\n  📝 卷 {volume_num} 章节列表讨论模式")
    print(f"\n  请告诉我你想如何调整章节：")
    print(f"     1. 调整章节数量（增减章节）")
    print(f"     2. 修改 POV 分配")
    print(f"     3. 调整章节顺序")
    print(f"     4. 修改核心内容描述")
    print(f"     5. 其他调整")
    print(f"\n  修改完成后，保存到：{chapters_file}")
    print(f"  然后使用 story:plan --chapters {volume_num} --confirm 确认")


def confirm_chapters(root: Path, volume_num: int) -> None:
    """确认章节列表"""
    volume_dir = get_volume_dir(root, volume_num)
    chapters_file = volume_dir / f"volume-{volume_num:03d}-chapters.md"

    if not chapters_file.exists():
        print(f"\n  错误：卷 {volume_num} 还没有章节列表")
        print(f"  请先使用 story:plan --chapters {volume_num} 生成章节列表")
        return

    # 解析章节数量
    with open(chapters_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 简单统计章节数量（数 | 第N章 出现的次数）
    import re
    chapters = re.findall(r'第(\d+)章', content)
    if chapters:
        chapter_count = len(chapters)

        # 初始化章节 stage
        init_chapter_stages(root, volume_num, chapter_count)

        print(f"\n  ✓ 确认卷 {volume_num} 的 {chapter_count} 个章节")
        print(f"\n  ✓ 已初始化所有章节 stage: outline-draft")
        print(f"\n  下一步建议：")
        print(f"    story:outline --draft {volume_num} --all  → 批量生成章节细纲")
        print(f"    story:outline --draft 1              → 生成单章细纲")
    else:
        print(f"\n  ⚠️  无法解析章节数量，请手动确认章节列表")
        print(f"\n  下一步建议：")
        print(f"    1. 确认 chapters 文件中的章节数量")
        print(f"    2. 运行 story:outline --draft {volume_num} --all 生成细纲")


# ============================================================
# 查看状态
# ============================================================

def show_volume_status(root: Path, volume_num: int) -> None:
    """显示卷的状态"""
    stage = get_volume_stage(volume_num, root)
    stage_icon = "✓" if stage == "confirmed" else "○" if stage == "draft" else "?"

    print(f"\n  卷 {volume_num}: [{stage or '未设置'}] {stage_icon}")

    outline_file = get_volume_outline_file(root, volume_num)
    if outline_file.exists():
        print(f"    卷纲: {outline_file}")

    volume_dir = get_volume_dir(root, volume_num)
    chapters_file = volume_dir / f"volume-{volume_num:03d}-chapters.md"
    if chapters_file.exists():
        print(f"    章节列表: {chapters_file}")


def show_pipeline_status(root: Path) -> None:
    """显示流水线整体状态"""
    config = load_config(root)
    pipeline = load_pipeline_state(root)
    volumes = pipeline.get("volumes", {})
    chapters = pipeline.get("chapters", {})

    meta = config.get("meta", {})
    title = meta.get("title", "未命名小说")

    print(f"\n{'='*60}")
    print(f"  创作流水线状态")
    print(f"{'='*60}")
    print(f"\n  书名：《{title}》")
    print(f"\n  卷状态：")
    if not volumes:
        print("    （暂无卷信息）")
    else:
        for vol_num in sorted(volumes.keys(), key=int):
            show_volume_status(root, int(vol_num))

    print(f"\n  章节状态：")
    if not chapters:
        print("    （暂无章节信息）")
    else:
        # 按卷分组显示
        by_volume = {}
        for ch_num, info in chapters.items():
            vol = info.get("volume", "?")
            if vol not in by_volume:
                by_volume[vol] = []
            by_volume[vol].append((ch_num, info))

        for vol in sorted(by_volume.keys(), key=lambda x: (x == "?", x)):
            if vol == "?":
                continue
            print(f"\n    卷 {vol}:")
            for ch_num, info in sorted(by_volume[vol], key=lambda x: int(x[0])):
                stage = info.get("stage", "?")
                icon = "✓" if stage == "done" else "●" if stage in ["writing", "review"] else "○"
                print(f"      第{ch_num}章: [{stage}] {icon}")

    print(f"\n  Stage 说明：")
    print(f"    卷: draft → confirmed")
    print(f"    章节: outline-draft → outline-confirmed → writing → review → done")


# ============================================================
# 主入口
# ============================================================

def output_json_result(result: dict):
    """输出 JSON 格式结果"""
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="卷纲生成与章节拆分",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  story:plan --volume 1                    # 生成卷1卷纲（读取主线文件）
  story:plan --volume 1 --interactive      # 交互式问答生成卷纲
  story:plan --volume 1 --revise           # 讨论模式修改卷纲
  story:plan --volume 1 --confirm          # 确认卷纲定稿

  story:plan --chapters 1                  # 拆分卷1章节
  story:plan --chapters 1 --revise         # 讨论章节拆分
  story:plan --chapters 1 --confirm        # 确认章节列表

  story:plan --status                      # 查看流水线状态
  story:plan --volume 1 --status           # 查看卷1详细状态
        """
    )

    parser.add_argument("--json", action="store_true", help="输出 JSON 格式（Agent 驱动模式）")
    parser.add_argument("--volume", "-v", type=int, metavar="N",
                        help="卷号")
    parser.add_argument("--chapters", "-c", type=int, metavar="N",
                        help="根据卷纲拆分章节")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="交互式问答模式")
    parser.add_argument("--revise", "-r", action="store_true",
                        help="讨论模式（进入修改讨论）")
    parser.add_argument("--confirm", action="store_true",
                        help="确认定稿")
    parser.add_argument("--status", "-s", action="store_true",
                        help="查看流水线状态")
    parser.add_argument("--non-interactive", action="store_true",
                        help="非交互模式（Agent 驱动，主线信息从参数读取）")
    parser.add_argument("--conflict", help="核心冲突")
    parser.add_argument("--arc", help="主角成长弧线")
    parser.add_argument("--events", help="核心事件（逗号分隔）")
    parser.add_argument("--tone", help="情感基调")

    args = parser.parse_args()

    root = get_root()

    # 状态查看
    if args.status:
        if args.volume:
            show_volume_status(root, args.volume)
        else:
            show_pipeline_status(root)
        return

    # 卷纲操作
    if args.volume:
        if args.confirm:
            confirm_volume_outline(root, args.volume)
        elif args.revise:
            revise_volume_outline(root, args.volume)
        else:
            # 非交互模式：用 --conflict/--arc/--events/--tone 参数
            # 交互模式：用 --interactive 进入问答
            # 默认：从文件读取主线
            if args.non_interactive:
                # 非交互模式至少需要 --conflict 或主线文件
                generate_volume_outline(root, args.volume, interactive=False,
                                        conflict=args.conflict, arc=args.arc,
                                        events=args.events, tone=args.tone)
            else:
                generate_volume_outline(root, args.volume, args.interactive)
        return

    # 章节拆分
    if args.chapters:
        if args.confirm:
            confirm_chapters(root, args.chapters)
        elif args.revise:
            revise_chapters(root, args.chapters)
        else:
            split_chapters(root, args.chapters, args.interactive)
        return

    # 无参数：显示帮助和状态
    parser.print_help()
    print("\n")
    show_pipeline_status(root)


if __name__ == "__main__":
    main()
