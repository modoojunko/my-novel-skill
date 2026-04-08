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

from src import init, propose, volume, outline, write, archive, status

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
  init      初始化小说项目
  propose   创建创作意图
  define    管理设定库
  volume    卷管理（初始化/查看/批量操作）
  outline   编辑大纲
  write     写作模式
  archive   定稿归档
  status    查看项目状态

示例：
  story:init                   # 初始化项目
  story:propose 第一章          # 创建第一章提案
  story:volume --list          # 查看卷结构
  story:volume --init-all      # 初始化所有卷
  story:outline --list         # 列出大纲
  story:outline --init-chapters 1  # 初始化卷1的章节大纲
  story:write 1                # 开始写第一章
  story:archive 1              # 归档第一章
  story:status                 # 查看状态

查看命令帮助：
  story:init --help
  story:propose --help
  等等...
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
        'archive': archive,
        'status': status,
        'define': None,  # 待实现
    }

    # 别名
    aliases = {
        's': 'status',
        'p': 'propose',
        'v': 'volume',
        'w': 'write',
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
