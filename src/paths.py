#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paths - 公共路径解析模块

提供统一的项目根目录查找、配置加载、路径解析功能。
所有模块通过此模块获取路径，消除 find_project_root() / load_config() 重复。

三目录设计：
- project_root: 小说项目目录（SPECS/OUTLINE/STYLE/templates）
- process_dir:  过程文件目录（draft/summaries/snapshots/proposals/prompts）
- output_dir:   最终输出目录（volume-NNN/export/archive）

向后兼容：若 story.json 中没有 paths 字段，所有路径回退到 project_root。
"""

import json
from pathlib import Path
from typing import Optional, Dict


# ============================================================================
# 项目根目录查找
# ============================================================================

def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """
    从给定目录（默认 cwd）向上查找包含 story.json 的项目根目录。

    Args:
        start: 起始查找目录，默认为当前工作目录

    Returns:
        项目根目录 Path，未找到返回 None
    """
    if start is None:
        start = Path.cwd()
    current = start
    for _ in range(10):
        if (current / 'story.json').exists() or (current / 'story.yml').exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


# ============================================================================
# 配置文件读写
# ============================================================================

def load_config(root: Path) -> dict:
    """
    加载项目配置文件（story.json 或 story.yml）。

    Args:
        root: 项目根目录

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
    """
    config_path = root / 'story.json'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    config_path = root / 'story.yml'
    if config_path.exists():
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    raise FileNotFoundError(f"配置文件不存在: {root / 'story.json'}")


def save_config(root: Path, config: dict) -> None:
    """
    保存配置到 story.json。

    Args:
        root: 项目根目录
        config: 配置字典
    """
    config_path = root / 'story.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ============================================================================
# 路径解析（三目录设计核心）
# ============================================================================

def resolve_path(root: Path, path_key: str, default_subdir: str) -> Path:
    """
    从 story.json 的 paths 字段解析路径，向后兼容。

    优先级：
    1. story.json paths[path_key] 是绝对路径 → 直接使用
    2. story.json paths[path_key] 是相对路径 → 相对于 root 解析
    3. story.json 无 paths 或无该 key → root / default_subdir

    Args:
        root: 项目根目录
        path_key: story.json paths 中的键名
        default_subdir: 兼容回退时的子目录名（如 'CONTENT', 'ARCHIVE'）

    Returns:
        解析后的绝对路径
    """
    try:
        config = load_config(root)
    except FileNotFoundError:
        return root / default_subdir

    paths = config.get('paths', {})
    if not paths:
        return root / default_subdir

    value = paths.get(path_key)
    if not value:
        return root / default_subdir

    p = Path(value)
    if p.is_absolute():
        return p
    return root / value


def load_project_paths(root: Path) -> Dict[str, Path]:
    """
    一次性加载所有项目路径，返回结构化字典。

    基于 story.json 的 paths 字段解析，缺失字段使用向后兼容默认值。

    三目录映射：
    - project_root 下的子目录：SPECS, OUTLINE, STYLE, templates
    - process_dir  下的子目录：draft, summaries, snapshots, proposals, prompts
    - output_dir   下的子目录：volume-NNN, export, archive

    Args:
        root: 项目根目录

    Returns:
        包含所有路径的字典，键名如下：
        - root:           项目根目录
        - process_dir:    过程文件目录
        - output_dir:     最终输出目录
        - specs:          SPECS/
        - characters:     SPECS/characters/
        - world:          SPECS/world/
        - meta:           SPECS/meta/
        - outline:        OUTLINE/
        - style:          STYLE/
        - style_prompts:  STYLE/prompts/
        - style_history:  STYLE/history/
        - templates:      templates/
        - draft:          过程目录/draft/
        - summaries:      过程目录/summaries/
        - snapshots:      过程目录/snapshots/
        - proposals:      过程目录/proposals/
        - prompts:        过程目录/prompts/
        - export:         输出目录/export/
        - archive:        输出目录/archive/
    """
    # 读取三大主目录
    try:
        config = load_config(root)
        paths_cfg = config.get('paths', {})
    except FileNotFoundError:
        paths_cfg = {}

    # 三大主目录
    project_root = root

    raw_process = paths_cfg.get('process_dir')
    if raw_process:
        p = Path(raw_process)
        process_dir = p if p.is_absolute() else root / raw_process
    else:
        process_dir = root

    raw_output = paths_cfg.get('output_dir')
    if raw_output:
        p = Path(raw_output)
        output_dir = p if p.is_absolute() else root / raw_output
    else:
        output_dir = root

    # 构建完整路径字典
    return {
        # 三大主目录
        'root': project_root,
        'process_dir': process_dir,
        'output_dir': output_dir,

        # project_root 下的子目录（设定与大纲）
        'specs': project_root / 'SPECS',
        'characters': project_root / 'SPECS' / 'characters',
        'world': project_root / 'SPECS' / 'world',
        'meta': project_root / 'SPECS' / 'meta',
        'outline': project_root / 'OUTLINE',
        'style': project_root / 'STYLE',
        'style_prompts': project_root / 'STYLE' / 'prompts',
        'style_history': project_root / 'STYLE' / 'history',
        'templates': project_root / 'templates',

        # process_dir 下的子目录（AI 生成的中间产物）
        'draft': process_dir / 'draft',
        'summaries': process_dir / 'summaries',
        'snapshots': process_dir / 'snapshots',
        'proposals': process_dir / 'proposals',
        'prompts': process_dir / 'prompts',

        # output_dir 下的子目录（小说正文与导出）
        'export': output_dir / 'export',
        'archive': output_dir / 'archive',
    }


def get_volume_dir(paths: Dict[str, Path], volume_num: int, dir_type: str = 'content') -> Path:
    """
    获取指定卷的目录路径。

    Args:
        paths: load_project_paths() 返回的路径字典
        volume_num: 卷号（1-based）
        dir_type: 目录类型
            - 'content':  正文目录（output_dir/volume-NNN/）
            - 'outline':  大纲目录（project_root/OUTLINE/volume-NNN/）
            - 'snapshots': 快照目录（project_root/OUTLINE/volume-NNN/snapshots/）
            - 'summaries': 摘要目录（project_root/OUTLINE/volume-NNN/summaries/）

    Returns:
        卷目录的绝对路径
    """
    vol_name = f'volume-{volume_num:03d}'

    if dir_type == 'content':
        return paths['output_dir'] / vol_name
    elif dir_type == 'outline':
        return paths['outline'] / vol_name
    elif dir_type == 'snapshots':
        return paths['outline'] / vol_name / 'snapshots'
    elif dir_type == 'summaries':
        return paths['outline'] / vol_name / 'summaries'
    else:
        raise ValueError(f"未知目录类型: {dir_type}")


def get_chapter_path(paths: Dict[str, Path], chapter_num: int,
                     chapters_per: int = 30, file_type: str = 'content') -> Path:
    """
    获取章节文件路径。

    Args:
        paths: load_project_paths() 返回的路径字典
        chapter_num: 章节号（1-based）
        chapters_per: 每卷章节数
        file_type: 文件类型
            - 'content': 正文（output_dir/volume-NNN/chapter-NNN.md）
            - 'outline': 章节细纲（OUTLINE/volume-NNN/chapter-NNN.md）
            - 'tasks':   任务清单（output_dir/volume-NNN/chapter-NNN.tasks.md）
            - 'draft':   AI 草稿（process_dir/draft/chapter-NNN.ai-draft.md）

    Returns:
        章节文件的绝对路径
    """
    volume_num = ((chapter_num - 1) // chapters_per) + 1
    vol_name = f'volume-{volume_num:03d}'
    ch_name = f'chapter-{chapter_num:03d}'

    if file_type == 'content':
        return paths['output_dir'] / vol_name / f'{ch_name}.md'
    elif file_type == 'outline':
        return paths['outline'] / vol_name / f'{ch_name}.md'
    elif file_type == 'tasks':
        return paths['output_dir'] / vol_name / f'{ch_name}.tasks.md'
    elif file_type == 'draft':
        return paths['draft'] / f'{ch_name}.ai-draft.md'
    else:
        raise ValueError(f"未知文件类型: {file_type}")


def get_volume_outline_path(paths: Dict[str, Path], volume_num: int) -> Path:
    """
    获取卷大纲文件路径（OUTLINE/volume-NNN.md）。

    Args:
        paths: load_project_paths() 返回的路径字典
        volume_num: 卷号

    Returns:
        卷大纲文件绝对路径
    """
    return paths['outline'] / f'volume-{volume_num:03d}.md'
