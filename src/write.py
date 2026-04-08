#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:write - 写作模式 + Agent Prompt 生成

提供两种写作方式：
1. 手动写作：创建文件框架，人工写作
2. Agent Prompt：生成结构化 Prompt，供 Agent 使用

使用 JSON 作为配置文件格式。
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


def save_config(root, config):
    """保存配置"""
    config_path = root / 'story.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


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
# 上下文读取函数
# ============================================================================

def get_chapter_path(root, chapter_num, volume_num=None):
    """获取章节文件路径"""
    chapters_per = 30
    if volume_num is None:
        volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = root / 'CONTENT' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'
    return chapter_path, volume_num


def read_chapter_outline(root, chapter_num, volume_num):
    """读取章节大纲"""
    outline_path = root / 'OUTLINE' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'
    return read_file_safely(outline_path)


def read_volume_outline(root, volume_num):
    """读取卷大纲"""
    vol_path = root / 'OUTLINE' / f'volume-{volume_num}.md'
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


def read_characters_specs(root):
    """读取人物设定"""
    chars_dir = root / 'SPECS' / 'characters'
    if not chars_dir.exists():
        return ""

    result = []
    for char_file in sorted(chars_dir.glob('*.md')):
        result.append(f"\n### {char_file.stem}\n")
        result.append(char_file.read_text(encoding='utf-8'))

    return '\n'.join(result)


def read_world_specs(root):
    """读取世界观设定"""
    world_dir = root / 'SPECS' / 'world'
    if not world_dir.exists():
        return ""

    result = []
    for world_file in sorted(world_dir.glob('*.md')):
        result.append(f"\n### {world_file.stem}\n")
        result.append(world_file.read_text(encoding='utf-8'))

    return '\n'.join(result)


def read_style_prompts(root):
    """读取风格提示（如果存在）"""
    style_dir = root / 'STYLE' / 'prompts'
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


def read_story_concept(root):
    """读取故事概念"""
    concept_path = root / 'SPECS' / 'meta' / 'story-concept.md'
    return read_file_safely(concept_path)


def read_style_avoid(root):
    """读取风格禁忌（如果存在）"""
    avoid_path = root / 'STYLE' / 'avoid.md'
    if avoid_path.exists():
        content = avoid_path.read_text(encoding='utf-8')
        return content.split('## 避免')[1] if '## 避免' in content else content
    return ""


# ============================================================================
# Agent Prompt 生成
# ============================================================================

def generate_agent_prompt(root, config, chapter_num, volume_num):
    """生成 Agent 写作 Prompt"""

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
    style_prompts = read_style_prompts(root)
    style_avoid = read_style_avoid(root)

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
    characters = read_characters_specs(root)
    if characters:
        prompt_parts.append("## 人物设定\n")
        prompt_parts.append(characters.strip())
        prompt_parts.append("")

    # 5. 世界观约束
    world = read_world_specs(root)
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

    # 8. 写作要求
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
    prompt_parts.append("- 禁止：错别字、语法错误、POV 混乱")

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
    print(f"  - 章节大纲：OUTLINE/volume-{volume_num}/chapter-{chapter_num:03d}.md")
    print(f"  - 卷大纲：OUTLINE/volume-{volume_num}.md")
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


def init_chapter(root, config, chapter_num):
    """初始化章节"""
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    vol_dir = root / 'CONTENT' / f'volume-{volume_num}'
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

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  {c('[ERROR] 未找到项目目录，请先运行 story:init', Colors.RED)}")
        sys.exit(1)

    config = load_config(root)

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

    # 如果只是生成 Prompt（不创建文件）
    if args.show or args.prompt:
        prompt = generate_agent_prompt(root, config, chapter_num, volume_num)

        if args.prompt:
            show_prompt_only(prompt)
        else:
            show_full_context(root, config, chapter_num, volume_num)

        print(f"""
{c('[TIP] 使用建议：', Colors.YELLOW)}
  1. 将上述 Prompt 发送给 AI Agent
  2. Agent 生成内容后，使用以下命令导入对比：
     python story.py write {chapter_num} --ai-import <文件路径>
  3. 或直接在 CONTENT/volume-{volume_num}/chapter-{chapter_num:03d}.md 中查看
""")
        return

    # 传统写作模式：初始化章节
    chapter_path, tasks_path, volume_num = init_chapter(root, config, chapter_num)

    show_write_mode(chapter_num, volume_num)

    print(f"  [FILE] 章节文件：{chapter_path.relative_to(root)}")
    print(f"  [TASK] 任务清单：{tasks_path.relative_to(root)}")
    print(f"  [REF]  大纲参考：OUTLINE/volume-{volume_num}/chapter-{chapter_num:03d}.md")
    print(f"  [SPEC] 设定参考：SPECS/")
    print()

    # 显示章节大纲预览
    outline_path = root / 'OUTLINE' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'
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
