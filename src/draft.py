#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:draft - 用户起草 → AI 补全

基于用户填写的 USER-CORE 区域，AI 自动补全 AI-EXPAND 区域。

支持：
- draft character <name> - 补全角色卡
- draft meta - 补全总纲
- draft world <category> - 补全世界观
- draft --all - 批量补全所有待处理文档
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .paths import find_project_root, load_config, load_project_paths
from .define import parse_character_frontmatter, parse_world_frontmatter


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
# 标记常量
# ============================================================================

USER_CORE_START = "<!-- USER-CORE:START -->"
USER_CORE_END = "<!-- USER-CORE:END -->"
AI_EXPAND_START = "<!-- AI-EXPAND:START -->"
AI_EXPAND_END = "<!-- AI-EXPAND:END -->"


# ============================================================================
# 模板解析函数
# ============================================================================

def parse_user_core(content: str) -> Optional[str]:
    """
    从文档内容中提取 USER-CORE 区域。

    Args:
        content: 完整的文档内容

    Returns:
        USER-CORE 区域的内容，如果未找到返回 None
    """
    if USER_CORE_START not in content or USER_CORE_END not in content:
        return None

    start_idx = content.find(USER_CORE_START) + len(USER_CORE_START)
    end_idx = content.find(USER_CORE_END, start_idx)

    if start_idx >= end_idx:
        return None

    return content[start_idx:end_idx].strip()


def has_ai_expand(content: str) -> bool:
    """检查文档是否已有 AI-EXPAND 区域。"""
    return AI_EXPAND_START in content and AI_EXPAND_END in content


def is_ai_expand_empty(content: str) -> bool:
    """检查 AI-EXPAND 区域是否为空。"""
    if not has_ai_expand(content):
        return True

    start_idx = content.find(AI_EXPAND_START) + len(AI_EXPAND_START)
    end_idx = content.find(AI_EXPAND_END, start_idx)

    if start_idx >= end_idx:
        return True

    expand_content = content[start_idx:end_idx].strip()
    return len(expand_content) == 0 or expand_content.startswith("（AI 基于")


def replace_ai_expand(content: str, new_expand_content: str) -> str:
    """
    替换文档中的 AI-EXPAND 区域。

    Args:
        content: 原始文档内容
        new_expand_content: 新的 AI-EXPAND 内容（不含标记）

    Returns:
        替换后的完整文档内容
    """
    if AI_EXPAND_START not in content or AI_EXPAND_END not in content:
        # 如果没有 AI-EXPAND 区域，添加到文档末尾
        separator = "\n\n---\n\n" if content.strip() else ""
        return f"{content.rstrip()}{separator}{AI_EXPAND_START}\n{new_expand_content.rstrip()}\n{AI_EXPAND_END}\n"

    start_idx = content.find(AI_EXPAND_START)
    end_idx = content.find(AI_EXPAND_END, start_idx) + len(AI_EXPAND_END)

    new_expand_full = f"{AI_EXPAND_START}\n{new_expand_content.rstrip()}\n{AI_EXPAND_END}"
    return content[:start_idx] + new_expand_full + content[end_idx:]


# ============================================================================
# 核心设定加载器
# ============================================================================

def load_core_context(paths: Dict[str, Path], target_type: str, target_name: str) -> Dict[str, str]:
    """
    加载小说核心设定上下文，用于注入 draft prompt。

    加载策略：
    - 总纲：全文加载（超长时智能截断，8000字符上限）
    - 世界观：全文加载，按类别分组（每个文件3000字符上限）
    - 其他角色：列表 + 标签（不加载完整内容）
    - 约束清单：从总纲中提取明确的规则

    Args:
        paths: 项目路径字典
        target_type: 'character' | 'world' | 'meta'
        target_name: 目标名称（角色名/世界观类别等）

    Returns:
        {
            'meta': 总纲内容,
            'world_summary': 世界观内容（按类别分组）,
            'character_list': 已有角色列表,
            'constraints': 约束清单
        }
    """
    context = {
        'meta': '',
        'world_summary': '',
        'character_list': '',
        'constraints': ''
    }

    # 1. 加载总纲
    meta_path = paths['outline'] / 'meta.md'
    if meta_path.exists():
        content = meta_path.read_text(encoding='utf-8')
        if len(content) > 8000:
            content = content[:8000] + "\n\n（... 总纲过长，已截断）"
        context['meta'] = content

    # 2. 加载世界观（全文，按类别）
    world_dir = paths['world']
    if world_dir.exists():
        world_entries = []
        for world_file in sorted(world_dir.glob('*.md')):
            fm = parse_world_frontmatter(world_file)
            name = fm.get('name', world_file.stem)
            category = fm.get('category', '其他')

            content = world_file.read_text(encoding='utf-8')
            if len(content) > 3000:
                content = content[:3000] + "\n\n（... 已截断）"

            world_entries.append(f"### {category}：{name}\n\n{content}\n")

        if world_entries:
            context['world_summary'] = "\n".join(world_entries)

    # 3. 加载角色列表（只列名字 + 标签，不加载完整内容）
    chars_dir = paths['characters']
    if chars_dir.exists():
        char_list = []
        for char_file in sorted(chars_dir.glob('*.md')):
            if char_file.stem == target_name and target_type == 'character':
                continue
            fm = parse_character_frontmatter(char_file)
            name = fm.get('name', char_file.stem)
            occupation = fm.get('occupation', '')
            status = fm.get('status', '')
            tags = fm.get('tags', [])

            line = f"- {name}"
            if occupation:
                line += f"（{occupation}）"
            if status and status != '存活':
                line += f" [{status}]"
            if tags and tags != [name]:
                if isinstance(tags, list):
                    tag_str = ', #'.join(tags[:3])
                else:
                    tag_str = str(tags)[:50]
                line += f" #{tag_str}"

            char_list.append(line)

        if char_list:
            context['character_list'] = "已有角色：\n" + "\n".join(char_list)

    # 4. 提取约束清单（从总纲中找明确的"规则"）
    constraints = []
    if context['meta']:
        for line in context['meta'].split('\n'):
            line = line.strip()
            if line and (('必须' in line) or ('设定' in line) or ('规则' in line) or ('⚠️' in line)):
                constraints.append(f"- {line}")

    if constraints:
        context['constraints'] = "\n".join(constraints)

    return context


# ============================================================================
# 文档扫描函数
# ============================================================================

def scan_character_files(root: Path, paths: Dict[str, Path]) -> List[Tuple[Path, str]]:
    """
    扫描所有角色文件，检测状态。

    Returns:
        List of (path, status) tuples. Status: 'need-expand' | 'expanded' | 'no-core'
    """
    chars_dir = paths['characters']
    if not chars_dir.exists():
        return []

    results = []
    for char_file in chars_dir.glob("*.md"):
        content = char_file.read_text(encoding="utf-8")
        user_core = parse_user_core(content)

        if user_core is None:
            results.append((char_file, "no-core"))
        elif not has_ai_expand(content) or is_ai_expand_empty(content):
            results.append((char_file, "need-expand"))
        else:
            results.append((char_file, "expanded"))

    return results


def scan_world_files(root: Path, paths: Dict[str, Path]) -> List[Tuple[Path, str]]:
    """
    扫描所有世界观文件，检测状态。
    """
    world_dir = paths['world']
    if not world_dir.exists():
        return []

    results = []
    for world_file in world_dir.glob("*.md"):
        content = world_file.read_text(encoding="utf-8")
        user_core = parse_user_core(content)

        if user_core is None:
            results.append((world_file, "no-core"))
        elif not has_ai_expand(content) or is_ai_expand_empty(content):
            results.append((world_file, "need-expand"))
        else:
            results.append((world_file, "expanded"))

    return results


def scan_meta_file(root: Path, paths: Dict[str, Path]) -> Optional[Tuple[Path, str]]:
    """
    扫描总纲文件，检测状态。
    """
    meta_path = paths['outline'] / "meta.md"
    if not meta_path.exists():
        return None

    content = meta_path.read_text(encoding="utf-8")
    user_core = parse_user_core(content)

    if user_core is None:
        return (meta_path, "no-core")
    elif not has_ai_expand(content) or is_ai_expand_empty(content):
        return (meta_path, "need-expand")
    else:
        return (meta_path, "expanded")


def get_all_pending_files(root: Path, paths: Dict[str, Path], file_type: Optional[str] = None) -> List[Tuple[Path, str]]:
    """
    获取所有待补全的文件。

    Args:
        root: 项目根目录
        paths: 路径字典
        file_type: 筛选类型（'character' | 'meta' | 'world' | None）

    Returns:
        List of (path, type) tuples
    """
    pending = []

    if file_type is None or file_type == "character":
        for path, status in scan_character_files(root, paths):
            if status == "need-expand":
                pending.append((path, "character"))

    if file_type is None or file_type == "meta":
        meta_result = scan_meta_file(root, paths)
        if meta_result and meta_result[1] == "need-expand":
            pending.append((meta_result[0], "meta"))

    if file_type is None or file_type == "world":
        for path, status in scan_world_files(root, paths):
            if status == "need-expand":
                pending.append((path, "world"))

    return pending


# ============================================================================
# Prompt 模板加载
# ============================================================================

def get_prompt_dir() -> Path:
    """获取 prompt 模板目录。"""
    return Path(__file__).parent / "prompts"


def load_prompt_template(template_name: str) -> str:
    """
    加载指定的 prompt 模板。

    Args:
        template_name: 模板名（不含 .md 后缀）

    Returns:
        模板内容
    """
    prompt_path = get_prompt_dir() / f"{template_name}.md"
    if not prompt_path.exists():
        return ""
    return prompt_path.read_text(encoding="utf-8")


def build_expansion_prompt(user_core: str, template_name: str,
                          core_context: Dict[str, str], target_name: str) -> str:
    """
    构建 AI 补全的 prompt，包含核心设定上下文。

    Args:
        user_core: USER-CORE 内容
        template_name: 模板名
        core_context: load_core_context() 返回的核心设定字典
        target_name: 目标名称（角色名/世界观类别等）

    Returns:
        完整的 prompt
    """
    template = load_prompt_template(template_name)
    if not template:
        return ""

    # 构建各 section
    meta_section = ""
    if core_context.get('meta'):
        meta_section = "## 总纲概要\n\n" + core_context['meta']

    world_section = ""
    if core_context.get('world_summary'):
        world_section = "## 世界观背景\n\n" + core_context['world_summary']

    character_list_section = ""
    if core_context.get('character_list'):
        character_list_section = "## 已有角色\n\n" + core_context['character_list']

    constraints_section = ""
    if core_context.get('constraints'):
        constraints_section = "## 重要约束\n\n" + core_context['constraints']

    # 替换模板变量
    prompt = template.replace("{user_core_content}", user_core)
    prompt = prompt.replace("{character_name}", target_name)
    prompt = prompt.replace("{target_name}", target_name)
    prompt = prompt.replace("{meta_section}", meta_section)
    prompt = prompt.replace("{world_section}", world_section)
    prompt = prompt.replace("{character_list_section}", character_list_section)
    prompt = prompt.replace("{constraints_section}", constraints_section)

    return prompt


# ============================================================================
# CLI 命令实现
# ============================================================================

def show_banner():
    """显示横幅"""
    print("""
+----------------------------------------------------+
|                                                    |
|           [DRAFT] 用户起草 → AI 补全               |
|                                                    |
+----------------------------------------------------+
    """)


def show_preview(title: str, content: str):
    """显示预览内容。"""
    print(f"\n{c('═' * 60, Colors.CYAN)}")
    print(f"  {c('预览', Colors.BOLD)}：{title}")
    print(f"{c('═' * 60, Colors.CYAN)}\n")
    print(content)
    print(f"\n{c('═' * 60, Colors.CYAN)}")
    print(f"  使用 --force 确认写入，或 --interactive 逐段确认")
    print(f"{c('═' * 60, Colors.CYAN)}\n")


def show_pending_list(root: Path, paths: Dict[str, Path]):
    """显示待补全文件列表。"""
    pending = get_all_pending_files(root, paths)

    if not pending:
        print(f"  {c('OK', Colors.GREEN)} 没有待补全的文件")
        return

    print(f"\n{c('待补全文件', Colors.BOLD)}")
    print(c('-' * 50, Colors.CYAN))

    for path, file_type in pending:
        type_label = {
            'character': '角色',
            'meta': '总纲',
            'world': '世界观'
        }.get(file_type, file_type)
        print(f"  [{type_label}] {path.name}")

    print(c('-' * 50, Colors.CYAN))
    print(f"  共 {len(pending)} 个文件待补全\n")


def get_prompt_storage_dir(root: Path, paths: Dict[str, Path]) -> Path:
    """获取 prompt 存储目录"""
    prompt_dir = paths['prompts']
    prompt_dir.mkdir(parents=True, exist_ok=True)
    return prompt_dir


def save_prompt_to_file(prompt: str, prompt_dir: Path, filename: str) -> Path:
    """保存 prompt 到文件"""
    prompt_file = prompt_dir / filename
    prompt_file.write_text(prompt, encoding="utf-8")
    return prompt_file


def output_json_result(result: Dict[str, Any]) -> None:
    """输出 JSON 格式结果"""
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='用户起草 → AI 补全')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式（Agent 驱动模式）')
    subparsers = parser.add_subparsers(title='子命令', dest='subcommand')

    # draft character <name>
    char_parser = subparsers.add_parser('character', help='补全角色卡')
    char_parser.add_argument('name', help='角色名')
    char_parser.add_argument('--preview', action='store_true', help='只预览不写入')
    char_parser.add_argument('--force', action='store_true', help='强制覆盖已有内容')
    char_parser.add_argument('--interactive', action='store_true', help='交互式确认')
    char_parser.add_argument('--ai', help='从文件导入 AI 生成内容')

    # draft meta
    meta_parser = subparsers.add_parser('meta', help='补全总纲')
    meta_parser.add_argument('--preview', action='store_true', help='只预览不写入')
    meta_parser.add_argument('--force', action='store_true', help='强制覆盖已有内容')
    meta_parser.add_argument('--interactive', action='store_true', help='交互式确认')
    meta_parser.add_argument('--ai', help='从文件导入 AI 生成内容')

    # draft world <category>
    world_parser = subparsers.add_parser('world', help='补全世界观')
    world_parser.add_argument('category', help='世界观分类')
    world_parser.add_argument('--preview', action='store_true', help='只预览不写入')
    world_parser.add_argument('--force', action='store_true', help='强制覆盖已有内容')
    world_parser.add_argument('--interactive', action='store_true', help='交互式确认')
    world_parser.add_argument('--ai', help='从文件导入 AI 生成内容')

    # draft --all
    all_parser = subparsers.add_parser('all', help='批量补全所有待处理文档')
    all_parser.add_argument('--preview', action='store_true', help='只列出不处理')
    all_parser.add_argument('--force', action='store_true', help='强制覆盖已有内容')
    all_parser.add_argument('--type', choices=['character', 'meta', 'world'], help='只处理指定类型')

    args = parser.parse_args()

    # 查找项目根目录
    root = find_project_root()
    if root is None:
        print(f"  {c('错误', Colors.RED)}: 未找到 story.json，请先运行 story:init")
        sys.exit(1)

    paths = load_project_paths(root)
    show_banner()

    if args.subcommand is None:
        # 默认显示待补全列表
        show_pending_list(root, paths)
        print("  使用以下命令补全：")
        print(f"    {c('story draft character <name>', Colors.BOLD)} - 补全指定角色")
        print(f"    {c('story draft meta', Colors.BOLD)} - 补全总纲")
        print(f"    {c('story draft world <category>', Colors.BOLD)} - 补全指定世界观")
        print(f"    {c('story draft all', Colors.BOLD)} - 批量补全所有")
        return

    if args.subcommand == 'all':
        # 批量处理
        if args.preview:
            show_pending_list(root, paths)
        else:
            print(f"  {c('TODO', Colors.YELLOW)}: 批量补全功能实现中")
    else:
        # 单个文件处理 - 显示 prompt 生成提示
        # 尝试找到文件并显示 prompt
        file_path = None
        template_type = None

        if args.subcommand == 'character':
            file_path = paths['characters'] / f"{args.name}.md"
            template_type = 'draft_character'
        elif args.subcommand == 'meta':
            file_path = paths['outline'] / "meta.md"
            template_type = 'draft_meta'
        elif args.subcommand == 'world':
            file_path = paths['world'] / f"{args.category}.md"
            template_type = 'draft_world'

        # 如果有 --ai 选项，导入 AI 生成的内容
        if args.ai:
            ai_file = Path(args.ai)
            if not ai_file.exists():
                print(f"  {c('错误', Colors.RED)}: AI 文件不存在: {ai_file}")
                sys.exit(1)

            ai_content = ai_file.read_text(encoding="utf-8")

            if not file_path or not file_path.exists():
                print(f"  {c('错误', Colors.RED)}: 目标文件不存在: {file_path}")
                sys.exit(1)

            content = file_path.read_text(encoding="utf-8")

            # 提取 AI 内容中的 AI-EXPAND 部分（如果有）
            ai_expand_start = ai_content.find(AI_EXPAND_START)
            ai_expand_end = ai_content.find(AI_EXPAND_END)

            if ai_expand_start != -1 and ai_expand_end != -1:
                extract_start = ai_expand_start + len(AI_EXPAND_START)
                extract_end = ai_expand_end
                ai_expand_content = ai_content[extract_start:extract_end].strip()
            else:
                ai_expand_content = ai_content.strip()

            # 检查是否需要确认
            if not args.force and has_ai_expand(content) and not is_ai_expand_empty(content):
                print(f"  {c('警告', Colors.YELLOW)}: AI-EXPAND 区域已有内容")
                response = input(f"  是否覆盖？ [y/N]: ").strip().lower()
                if response != 'y':
                    print("  已取消")
                    sys.exit(0)

            # 替换内容
            new_content = replace_ai_expand(content, ai_expand_content)

            if args.preview:
                show_preview(f"{file_path.name} 的新内容", new_content)
            else:
                file_path.write_text(new_content, encoding="utf-8")
                print(f"  {c('OK', Colors.GREEN)}: 已写入 {file_path}")

        elif file_path and file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            user_core = parse_user_core(content)

            if user_core:
                target_name = args.name if args.subcommand == 'character' else (
                    args.category if args.subcommand == 'world' else 'meta'
                )
                # 加载核心设定上下文
                core_context = load_core_context(paths, args.subcommand, target_name)
                prompt = build_expansion_prompt(user_core, template_type, core_context, target_name)

                # 保存 prompt 到文件
                prompt_dir = get_prompt_storage_dir(root, paths)
                prompt_filename = f"draft-{args.subcommand}-{target_name}-prompt.md"
                prompt_file = save_prompt_to_file(prompt, prompt_dir, prompt_filename)

                # 构建导入命令
                import_cmd = f"story draft {args.subcommand} {target_name} --ai <your_output_file>"

                if args.json:
                    # JSON 模式输出
                    result = {
                        "type": f"draft-{args.subcommand}",
                        "target": target_name,
                        "prompt_file": str(prompt_file),
                        "prompt_content": prompt,
                        "next_step": "请基于这个 prompt 生成 AI-EXPAND 内容，只返回 <!-- AI-EXPAND:START --> 和 <!-- AI-EXPAND:END --> 之间的内容",
                        "import_command": import_cmd,
                        "target_file": str(file_path)
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
                    print(f"  1. 基于上面的 Prompt 生成 AI-EXPAND 内容")
                    print(f"  2. 只返回 <!-- AI-EXPAND:START --> 和 <!-- AI-EXPAND:END --> 之间的内容")
                    print(f"  3. 将你的输出保存到临时文件，或直接传递给 --ai 选项")
                    print(f"  4. 运行：{c(import_cmd, Colors.BOLD)}")
                    print(f"\n  💡 Prompt 已保存到：{c(prompt_file, Colors.DIM)}")
                    print(f"{c('═' * 80, Colors.CYAN)}\n")
            else:
                if args.json:
                    output_json_result({
                        "error": "未找到 USER-CORE 区域",
                        "target_file": str(file_path)
                    })
                else:
                    print(f"  {c('错误', Colors.RED)}: 未找到 USER-CORE 区域")
        else:
            if args.json:
                output_json_result({
                    "error": "文件不存在",
                    "target_file": str(file_path) if file_path else None
                })
            else:
                print(f"  {c('错误', Colors.RED)}: 文件不存在: {file_path}")


if __name__ == '__main__':
    main()
