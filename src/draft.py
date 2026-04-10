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
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .paths import find_project_root, load_config, load_project_paths


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
    return len(expand_content) == 0 or expand_content == "（AI 基于...生成）"


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


def build_expansion_prompt(user_core: str, template_name: str) -> str:
    """
    构建 AI 补全的 prompt。

    Args:
        user_core: USER-CORE 内容
        template_name: 模板名

    Returns:
        完整的 prompt
    """
    template = load_prompt_template(template_name)
    if not template:
        return ""
    return template.replace("{user_core_content}", user_core)


def main():
    """入口函数（占位）"""
    print("draft module loaded")


if __name__ == '__main__':
    main()
