# my-novel-v2 - AI 辅助小说写作工作流

> 简化版 AI 辅助小说写作工具：主 Agent 管流程 + 子 Agent 写正文

## 核心特性

- ✅ **主 Agent + 子 Agent 架构** - 职责分离，避免"忘事"
- ✅ **两目录设计** - process/output 清晰分离
- ✅ **零依赖** - 仅使用 Python 标准库
- ✅ **全 YAML 数据格式** - 人类可读，易于编辑
- ✅ **写一卷规划一卷** - 渐进式创作，无前期负担
- ✅ **角色六层认知模型** - 世界观/自我定义/价值观/能力/技能/环境
- ✅ **智能提示词分层摘要** - 避免被截断，关键信息优先
- ✅ **设定快照机制** - 防止剧情 inconsistency
- ✅ **POV 认知约束** - 防止角色提前知道后面剧情

## 快速开始

### 安装

```bash
# 克隆项目
git clone <repository-url> my-novel-v2
cd my-novel-v2

# 无需 pip install，仅需 Python 3.8+
```

### 创建你的第一部小说

```bash
# 1. 创建项目目录
mkdir my-first-novel
cd my-first-novel

# 2. 初始化项目
python /path/to/my-novel-v2/story.py init

# 3. 收集核心信息
python /path/to/my-novel-v2/story.py collect core

# 4. 创建主角
python /path/to/my-novel-v2/story.py collect protagonist

# 5. 规划第一卷
python /path/to/my-novel-v2/story.py plan volume 1

# 6. 生成第一章提示词
python /path/to/my-novel-v2/story.py write 1 --prompt
```

## 完整命令列表

| 命令 | 功能 |
|------|------|
| `story init` | 初始化新项目 |
| `story status` | 查看项目状态 |
| `story collect core` | 收集小说核心信息 |
| `story collect protagonist` | 创建主角 |
| `story collect volume <num>` | 收集卷信息 |
| `story plan volume <num>` | 规划卷大纲 |
| `story plan chapter <vol> <num>` | 规划章节大纲 |
| `story write <num> --prompt` | 生成章节提示词 |
| `story archive <num>` | 归档已完成章节 |
| `story export` | 导出小说 |

## 项目结构

```
你的小说项目/
├── story.yaml                    # 配置 + 总进度
├── process/                      # 过程管理产物
│   ├── INFO/                     # 收集到的信息
│   │   ├── 01-core.yaml          # 小说核心信息
│   │   └── characters/            # 角色分类
│   │       ├── protagonist/       # 主角（完整设定）
│   │       ├── main_cast/         # 主角团（完整设定）
│   │       ├── supporting/        # 次要配角（简化设定）
│   │       └── guest/            # 路人（极简设定）
│   ├── OUTLINE/                  # 大纲草稿
│   │   ├── volume-001.yaml       # 卷大纲
│   │   └── volume-001/           # 章节大纲 + 快照
│   ├── PROMPTS/                  # 生成的提示词
│   └── TEMPLATES/                # 提示词模板
└── output/                       # 最终正文
    ├── CONTENT/                  # 小说正文
    ├── EXPORT/                   # 导出文件
    └── ARCHIVE/                  # 已归档章节
```

## 核心设计理念

### 1. 主 Agent + 子 Agent 分离

- **主 Agent**：与用户对话，收集信息，管理进度，生成提示词
- **子 Agent**：只根据完整提示词写正文，不记忆之前的对话

### 2. 提示词分层摘要

为了避免提示词过长被截断，采用四层优先级：

- **L0（必须有）**：本章大纲、任务清单、POV 认知约束
- **L1（很重要）**：本卷大纲、主角设定、前 3 章快照
- **L2（有用）**：其他配角设定、前 4-10 章极简摘要
- **L3（可选）**：更早章节、世界观细节（按需加载）

### 3. 角色六层认知模型

每个主角/主角团都有完整的六层认知：

1. **世界观** - 角色如何看待这个世界
2. **自我定义** - 角色认为自己是谁
3. **价值观** - 什么对角色最重要
4. **核心能力** - 角色天生/已掌握的能力
5. **技能** - 后天学习的技能
6. **环境** - 角色当前所处环境

### 4. 写一卷规划一卷

不用一开始就想完整本书，先写好第一卷，再规划第二卷。

## 作为 Claude Skill 使用

本项目设计为 Claude Code / WorkBuddy 的 skill。安装后，当你提到"写小说"、"小说大纲"等关键词时，skill 会自动激活。

## 与 v1 的区别

my-novel-v2 是对原 my-novel-skill 的完全重写：

| 特性 | v1 | v2 |
|------|-----|-----|
| 架构 | 单 Agent | 主 Agent + 子 Agent |
| 目录 | 单目录混合 | 三目录分离 |
| 数据格式 | JSON + Markdown | 全 YAML（JSON 降级） |
| 角色系统 | 基础设定 | 六层认知模型 |
| 提示词 | 简单组合 | 分层智能摘要 |
| 创作方式 | 一次性规划 | 写一卷规划一卷 |

## 开发

```bash
# 运行测试
python -c "from src_v2 import paths, init, status; print('OK')"

# 查看帮助
python story.py --help
```

## 许可证

MIT License
