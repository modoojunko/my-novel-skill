# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在本代码库中工作的指导。

## 项目概述

my-novel-skill 是一个 AI 辅助小说写作的 CLI 工具，使用 Python 3.8+ 开发，仅使用标准库。它将小说创作结构化分为：**概念 → 设定 → 大纲 → 写作 → 归档** 五个阶段。

## 代码架构

### 模块结构

```
story.py                # CLI 入口点，分发到 src/ 各模块
src/
  ├── paths.py          # 统一路径解析（所有路径都用这个！）
  ├── init.py           # 项目初始化
  ├── propose.py        # 创作意图管理
  ├── plan.py           # 卷纲生成 + 章节拆分
  ├── draft.py          # AI 辅助设定补全
  ├── define.py         # 设定库管理（人物/世界观）
  ├── volume.py         # 卷管理
  ├── outline.py        # 大纲编辑
  ├── write.py          # 写作模式（生成 Agent Prompt）
  ├── review.py         # 人机差异对比
  ├── learn.py          # 风格学习引擎
  ├── style.py          # 风格档案管理
  ├── stats.py          # 进度统计
  ├── update_specs.py   # 写作后更新设定
  ├── recall.py         # 章节回顾
  ├── snapshot.py       # 章节设定快照
  ├── export.py         # 导出功能（txt/docx）
  ├── archive.py        # 定稿归档
  └── status.py         # 项目状态查看
```

### 核心架构模式

**1. 三目录设计**
- `project_root`: SPECS/, OUTLINE/, STYLE/, templates/（核心项目数据）
- `process_dir`: draft/, summaries/, snapshots/, proposals/, prompts/（AI 生成的中间产物）
- `output_dir`: volume-NNN/, export/, archive/（最终小说内容）

**始终使用 `paths.load_project_paths(root)` 获取路径——永远不要硬编码！**

**2. Pipeline 状态机**
- 卷状态：`draft` → `confirmed`
- 章节状态：`outline-draft` → `outline-confirmed` → `writing` → `done`
- 存储在 `story.json` 的 `pipeline` 字段中

**3. 角色认知模型**
- 六层认知模型：世界观 → 自我定义 → 价值观 → 能力 → 技能 → 环境
- POV（视角）约束强制每个角色只能知道其应该知道的信息
- 使用 `src/write.py` 中的 `generate_pov_constraint_prompt()` 和 `generate_cognition_prompt()`

### 重要约定

1. **全 UTF-8**：所有文件使用 UTF-8 编码
2. **Pathlib**：使用 `pathlib.Path` 进行路径操作
3. **配置中心**：`story.json` 是项目配置的唯一事实来源
4. **零依赖**：仅使用 Python 标准库，无需 pip 安装
5. **JSON 模式**：许多命令支持 `--json` 输出机器可读格式（参见 `docs/agent-guide/04-json-mode.md`）

## 常见开发任务

### 运行项目

```bash
# 显示帮助
python story.py --help

# 初始化测试项目
python story.py init --non-interactive --title "测试小说" --genre "玄幻" --words 500000 --volumes 3

# 查看状态
python story.py status
```

### 测试

项目包含测试目录：
- `test_define/` - 设定管理测试
- `test_novel/` - 小说工作流测试

查看测试目录中的测试脚本来运行现有测试。

### 添加新命令

1. 创建 `src/newcommand.py`，包含使用 `argparse` 的 `main()` 函数
2. 在 `story.py` 中导入并添加到 commands 字典
3. 如需要，添加别名
4. 所有路径操作使用 `src/paths.py`

### 关键文件参考

| 文件 | 用途 |
|------|------|
| `src/paths.py` | 所有路径解析函数 |
| `AGENT_GUIDE.md` | AI 助手如何使用此工具 |
| `SKILL.md` | 项目技能定义 |
| `docs/agent-guide/` | 模块化 Agent 指南文件 |

## Git

- 主分支：`main`
- 新功能应使用功能分支
- 推荐使用约定式提交

## 相关文档

- **README.md** - 用户文档
- **SKILL.md** - 技能定义
- **AGENT_GUIDE.md** - Agent 使用指南
- **docs/agent-guide/** - 详细的模块化文档
