# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

my-novel-skill (v2) 是一个 AI 辅助小说写作的 CLI 工具，使用 Python 3.8+ 开发，仅使用标准库。采用**主 Agent + 子 Agent 分离架构**，将小说创作流程结构化管理。

## 代码架构

### 模块结构（v2）

```
story.py                # CLI 入口点，分发到 src_v2/ 各模块
src_v2/
  ├── paths.py          # 统一路径解析（所有路径都用这个！）
  ├── cli.py            # CLI 工具库（颜色输出、交互/非交互模式、JSON 模式）
  ├── init.py           # 项目初始化
  ├── status.py         # 项目状态查看
  ├── collect.py        # 信息收集（core, protagonist, volume）
  ├── world.py          # 世界观设定管理（basic, faction, history, power, organization, location）
  ├── plan.py           # 卷纲/章节大纲规划
  ├── outline.py        # 大纲编辑
  ├── write.py          # 写作模式（生成 Agent Prompt）
  ├── prompt.py         # 提示词生成引擎
  ├── character.py      # 角色管理（六层认知模型）
  ├── character_knowledge.py  # 角色认知约束
  ├── snapshot.py       # 章节设定快照
  ├── timeline.py       # 时间线管理
  ├── consistency.py    # 一致性检查
  ├── anti_repeat.py    # 防重复机制
  ├── archive.py        # 定稿归档
  ├── export.py         # 导出功能
  ├── progress.py       # 进度管理
  └── templates.py      # 提示词模板管理
```

### 核心架构模式（v2）

**1. 三目录设计**
- `project_root`: story.yaml/story.json（配置中心）
- `process_dir`: process/（INFO, OUTLINE, PROMPTS, TEMPLATES）- 过程管理产物
- `output_dir`: output/（CONTENT, EXPORT, ARCHIVE）- 最终小说内容

**始终使用 `paths.load_project_paths(root)` 获取路径——永远不要硬编码！**

**2. 主 Agent + 子 Agent 分离**
- **主 Agent**：与用户对话，收集信息，管理进度，生成提示词
- **子 Agent**：只根据完整提示词写正文，不记忆之前的对话

**3. 数据格式**
- 优先使用 YAML（人类可读），无 PyYAML 时自动降级到 JSON
- 所有文件 UTF-8 编码
- 使用 `pathlib.Path` 进行路径操作

**4. 角色六层认知模型**
- L1 世界观 → L2 自我定义 → L3 价值观 → L4 核心能力 → L5 技能 → L6 环境
- POV（视角）约束强制每个角色只能知道其应该知道的信息

**5. 提示词分层摘要**
- L0（必须有）：本章大纲、任务清单、POV 认知约束（~30% tokens）
- L1（很重要）：本卷大纲、主角设定、前 3 章快照（~30% tokens）
- L2（有用）：其他配角、前 4-10 章极简摘要（~20% tokens）
- L3（可选）：更早章节、世界观细节（按需加载，~20% tokens）

**6. 统一 CLI 模式**
- 交互模式：用户问答输入
- 非交互模式：`--non-interactive --args '{"key":"value"}'`
- JSON 模式：`--json` 输出机器可读格式

### 重要约定

1. **零依赖**：仅使用 Python 标准库，PyYAML 为可选依赖
2. **UTF-8 优先**：所有文件使用 UTF-8 编码
3. **Pathlib**：使用 `pathlib.Path` 进行路径操作
4. **配置中心**：`story.yaml`（或 `story.json`）是项目配置的唯一事实来源
5. **写一卷规划一卷**：渐进式创作，避免前期负担过重
6. **设定快照**：每章结束后生成快照，防止剧情 inconsistency

## 常见开发任务

### 运行项目

```bash
# 显示帮助
python story.py --help

# 初始化测试项目
python story.py init --non-interactive --title "测试小说" --genre "玄幻" --words 500000 --volumes 3

# 查看状态
python story.py status

# 世界观管理
python story.py world list
python story.py world basic
python story.py world faction "破晓组织"
```

### 命令参考

| 命令 | 功能 |
|------|------|
| `story init` | 初始化新项目 |
| `story status` | 查看项目状态 |
| `story collect <target>` | 收集信息（core, protagonist, volume <num>） |
| `story world <target>` | 世界观设定（basic, timeline, faction, history, power, organization, location, list） |
| `story plan volume <num>` | 规划卷大纲 |
| `story plan chapter <vol> <num>` | 规划章节大纲 |
| `story write <num> --prompt` | 生成章节提示词 |
| `story archive <num>` | 归档已完成章节 |
| `story export` | 导出小说 |

### 添加新命令

1. 创建 `src_v2/newcommand.py`，包含使用 `argparse` 的 `main()` 函数
2. 在 `story.py` 中导入并添加到 commands 字典
3. 使用 `src_v2/cli.py` 中的工具函数处理交互/非交互/JSON 模式
4. 所有路径操作使用 `src_v2/paths.py`

### 关键文件参考

| 文件 | 用途 |
|------|------|
| `src_v2/paths.py` | 所有路径解析函数 |
| `src_v2/cli.py` | CLI 工具库（颜色、输入、JSON 模式） |
| `SKILL.md` | 项目技能定义 |
| `README.md` | 用户文档 |

## Git

- 主分支：`main`
- 新功能应使用功能分支
- 推荐使用约定式提交

## 相关文档

- **README.md** - 用户文档
- **SKILL.md** - 技能定义
