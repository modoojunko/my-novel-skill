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

from src import init, propose, volume, outline, write, review, learn, style, stats, archive, status, define, update_specs, recall, export

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
  define        管理设定库
  volume        卷管理（初始化/查看/批量操作）
  outline       编辑大纲
  write         写作模式（生成 Agent Prompt）
  review        人机差异对比与审核
  learn         风格学习引擎
  style         风格档案管理
  stats         学习进度统计
  archive       定稿归档
  status        查看项目状态
  update-specs  写作后自动更新设定库
  recall        章节回顾（查看摘要）
  export        导出小说（txt/docx）

示例：
  story:init                      # 初始化项目
  story:propose 第一章             # 创建第一章提案
  story:define character 张三     # 管理人物设定
  story:volume --list             # 查看卷结构
  story:volume --init-all         # 初始化所有卷
  story:outline --list            # 列出大纲
  story:outline --init-chapters 1  # 初始化卷1的章节大纲
  story:outline --expand 5        # 展开第5章场景细节
  story:outline --swap 8 10       # 交换第8章和第10章大纲
  story:write 1                   # 生成第1章 Agent Prompt
  story:review 1 --ai ai.md       # 导入AI内容并对比差异
  story:learn 1                   # 学习第1章风格
  story:recall 5                  # 查看第5章摘要
  story:recall --recent 3         # 查看最近3章摘要
  story:export 1-10               # 导出第1-10章
  story:export --format docx      # 导出为 Word 文档
  story:update-specs 5            # 分析第5章并更新设定库
  story:style                     # 查看风格档案
  story:stats                     # 查看学习进度
  story:archive 1                  # 归档第一章
  story:status                    # 查看状态

AI 协作写作流程：
  1. story:write 5             # 生成 Agent Prompt
  2. Agent 收到 Prompt → 生成内容
  3. story:review 5 --ai <文件>  # 导入 AI 内容
  4. 用户修改章节文件
  5. story:review 5            # 对比差异
  6. story:learn 5             # 学习风格
  7. story:update-specs 5      # 检测新设定 + 生成摘要 ← 新增!
  8. story:recall 5           # 回顾本章摘要 ← 新增!
  9. story:stats               # 查看进度
  10. story:export 1-10        # 导出交稿 ← 新增!

查看命令帮助：
  story:write --help
  story:review --help
  story:learn --help
  story:recall --help
  story:export --help
  story:outline --help
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
    }

    # 别名
    aliases = {
        's': 'status',
        'p': 'propose',
        'v': 'volume',
        'w': 'write',
        'r': 'review',
        'l': 'learn',
        't': 'style',  # t for style (tè色)
        'u': 'stats',  # u for usage/stats
        'a': 'archive',
        'o': 'outline',
        'i': 'init',
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
