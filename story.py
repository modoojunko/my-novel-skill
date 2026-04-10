#!/usr/bin/env python3
"""
Novel Workflow CLI

小说写作工作流命令行工具。
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src import init, propose, plan, volume, outline, write, review, learn, style, stats, archive, status, define, update_specs, recall, export, snapshot, draft

def show_banner():
    """显示横幅"""
    print("""
+----------------------------------------------------+
|                                                    |
|          [BOOK] Novel Workflow v1.0                |
|                                                    |
|          AI 辅助小说写作工作流                      |
|                                                    |
+----------------------------------------------------+
    """)

def show_help():
    """显示帮助"""
    print("""
用法：story <命令> [选项]

可用命令：
  init          初始化小说项目
  propose       创建创作意图
  plan          规划流水线（卷纲生成 + 章节拆分）
  define        管理设定库
  volume        卷管理（初始化/查看/批量操作）
  outline       编辑大纲（生成章节细纲）
  write         写作模式（生成 Agent Prompt）
  review        人机差异对比与审核
  learn         风格学习引擎
  style         风格档案管理
  stats         学习进度统计
  archive       定稿归档
  status        查看项目状态
  update-specs  写作后自动更新设定库
  recall        章节回顾（查看摘要/快照）
  snapshot      章节设定快照（记录设定状态）
  export        导出小说（txt/docx）

示例：
  story:init                      # 初始化项目
  story:propose 第一章             # 创建第一章提案
  story:plan --volume 1           # 生成卷1卷纲（读取主线）
  story:plan --volume 1 --interactive # 交互式生成卷纲
  story:plan --volume 1 --revise  # 讨论修改卷纲
  story:plan --volume 1 --confirm # 确认卷纲定稿
  story:plan --chapters 1         # 拆分卷1章节
  story:outline --draft 5         # AI生成第5章细纲
  story:outline --draft 1 --all   # 批量生成卷1所有细纲
  story:outline --revise 5        # 讨论修改细纲
  story:outline --confirm 5        # 确认细纲定稿
  story:write 5 --draft           # AI根据细纲写正文
  story:write 5 --revise          # 讨论修改正文
  story:write 5 --confirm         # 确认正文定稿
  story:recall 5                  # 查看第5章摘要
  story:recall --recent 3         # 查看最近3章摘要
  story:export 1-10               # 导出第1-10章
  story:export --format docx      # 导出为 Word 文档
  story:status                    # 查看流水线状态

Pipeline 流水线模式：
  规划阶段：
    story:plan --volume N         → AI生成卷纲草稿
    story:plan --volume N --revise → 讨论修改
    story:plan --volume N --confirm → 确认定稿
    story:plan --chapters N        → AI拆分章节
    story:plan --chapters N --confirm → 确认章节

  写作阶段：
    story:outline --draft N --all  → 批量生成细纲
    story:outline --revise N       → 讨论修改
    story:outline --confirm N      → 确认细纲
    story:write N --draft          → AI写正文
    story:write N --revise         → 讨论修改
    story:write N --confirm        → 确认定稿

查看命令帮助：
  story:plan --help
  story:write --help
  story:outline --help
  story:review --help
""")

def main():
    if len(sys.argv) < 2:
        show_banner()
        show_help()
        sys.exit(0)

    cmd = sys.argv[1].lower()

    # 命令映射
    commands = {
        'init': init,
        'propose': propose,
        'plan': plan,
        'draft': draft,
        'volume': volume,
        'outline': outline,
        'write': write,
        'review': review,
        'learn': learn,
        'style': style,
        'stats': stats,
        'archive': archive,
        'status': status,
        'define': define,
        'update-specs': update_specs,
        'recall': recall,
        'export': export,
        'snapshot': snapshot,
    }

    # 别名
    aliases = {
        's': 'status',
        'p': 'propose',
        'n': 'plan',   # n for plan
        'v': 'volume',
        'w': 'write',
        'r': 'review',
        'l': 'learn',
        't': 'style',  # t for style (tè色)
        'u': 'stats',  # u for usage/stats
        'a': 'archive',
        'o': 'outline',
        'i': 'init',
        'sp': 'snapshot',  # sp for snapshot
    }

    # 处理别名
    if cmd in aliases:
        cmd = aliases[cmd]

    if cmd == 'help' or cmd == '--help' or cmd == '-h':
        show_banner()
        show_help()
        sys.exit(0)

    # 执行命令
    if cmd in commands:
        if commands[cmd] is None:
            print(f"  命令 '{cmd}' 尚未实现")
            sys.exit(1)
        # 将剩余参数传递给子命令
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        try:
            commands[cmd].main()
        except KeyboardInterrupt:
            print("\n  已取消")
            sys.exit(130)
    else:
        print(f"  未知命令：{cmd}")
        print("  使用 'story --help' 查看可用命令")
        sys.exit(1)

if __name__ == '__main__':
    main()
