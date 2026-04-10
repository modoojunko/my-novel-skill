# my-novel - AI 辅助小说写作 Skill

把小说创作拆解为结构化的工作流：**概念 → 设定 → 大纲 → 写作 → 归档**。

每个层级有明确的输入输出，AI 在每一层发挥不同作用。灵感归灵感，结构归结构。

---

## 🚀 快速开始（作家版）

### 三步写出你的小说

```
1. 搭框架 → 2. 写内容 → 3. 审核定稿
   (AI引导)     (AI辅助)      (你说了算)
```

### 具体怎么用？

**告诉 AI："我想写小说"**，然后 AI 会一步步引导你：

| 阶段 | 你做什么 | AI 做什么 |
|------|---------|----------|
| **1. 初始化** | 说书名叫什么、什么类型 | 自动创建项目结构 |
| **2. 写概念** | 用一句话说清楚故事 | 帮你梳理成 story-concept |
| **3. 创设定** | 填人物/世界观的**核心信息** (20%) | 帮你**补全细节** (80%) |
| **4. 搭大纲** | 确认卷纲、章节、细纲 | AI 生成草稿，你审核定稿 |
| **5. 写正文** | 修改 AI 写的内容 | AI 生成正文，学习你的风格 |
| **6. 收尾** | 确认归档 | 自动更新设定、生成快照、导出 |

---

## 🔧 快速开始（技术版）

### 安装

```powershell
# Windows (WorkBuddy)
.\install.ps1

# Windows (Claude Code)
.\install.ps1 claude

# Linux/macOS
./install.sh workbuddy
```

### 给 AI Agent 的操作手册

**如果你是 AI Agent，请务必阅读：[AGENT_GUIDE.md](./AGENT_GUIDE.md)**

这份指南告诉你：
- 如何从头到尾协助作家完成一部小说
- 每个阶段该做什么、问什么、提供什么
- 如何根据项目状态建议下一步
- 各阶段的对话模板

## 工作流概览

| 命令 | 用途 | 示例 |
|------|------|------|
| `init` | 初始化小说项目 | "新建一个玄幻小说项目" |
| `propose` | 创建创作意图 | "给第一章写个提案" |
| `define` | 管理设定库 | "创建人物张三"、"查看所有设定" |
| `volume` | 管理卷结构 | "查看所有卷的状态" |
| `plan` | 规划流水线 | "生成第一卷的卷纲"、"拆分章节" |
| `outline` | 编辑大纲 | "写第一卷前5章的章节大纲" |
| `outline --expand` | 展开场景细节 | "展开第5章的场景" |
| `outline --swap` | 交换章节顺序 | "把第8章和第10章换一下" |
| `write` | 写正文 | "开始写第1章" |
| `review` | 人机差异对比 | "对比AI写的和我改的" |
| `learn` | 风格学习引擎 | "从修改中学到风格" |
| `style` | 风格档案管理 | "查看学到的风格" |
| `stats` | 学习进度统计 | "看看学得怎么样了" |
| `update-specs` | 自动更新设定 | "分析章节检测新设定" |
| `recall` | 章节回顾 | "看看前面几章写了什么" |
| `export` | 导出小说 | "导出1-10章发编辑" |
| `archive` | 定稿归档 | "第1章写完了，归档" |
| `status` | 查看进度 | "写到哪了" |

## 项目结构

```
你的小说项目/
  story.json          # 核心配置
  SPECS/              # 设定库（人物、世界观）
  OUTLINE/            # 大纲（总纲 → 卷纲 → 章纲）
  CONTENT/            # 正文（按卷/章节组织）
  ARCHIVE/            # 归档（定稿 + 变更记录）
```

## 设计理念

参考 OpenSpec 的软件工程实践（proposal → specs → design → tasks → implement → archive），将小说创作映射为类似的分层流程：

- **概念**（proposal）→ 故事概要 / 核心主题
- **设定**（specs）→ 人物、世界观、元设定
- **大纲**（design）→ 总纲 → 卷纲 → 章节大纲
- **正文**（implement）→ 按卷/章节组织的正文
- **归档**（archive）→ 定稿 + 变更记录

## 核心文件

```
my-novel-skill/
  SKILL.md      # Skill 定义（AI 读取）
  story.py      # CLI 入口
  src/          # CLI 模块
  install.ps1   # Windows 安装脚本
  install.sh    # Linux/macOS 安装脚本
```

### CLI 模块

| 模块 | 功能 |
|------|------|
| `init` | 初始化小说项目 |
| `propose` | 创建创作意图 |
| `plan` | 规划流水线（卷纲生成/章节拆分） |
| `define` | 人物卡/世界观管理 |
| `volume` | 卷结构管理 |
| `outline` | 编辑大纲（含 Pipeline 模式） |
| `write` | 写作模式（生成 Agent Prompt） |
| `review` | 人机差异对比 |
| `learn` | 风格学习引擎 |
| `style` | 风格档案管理 |
| `stats` | 学习进度+字数统计 |
| `update_specs` | 写作后自动更新设定 |
| `recall` | 章节回顾 |
| `export` | 导出 txt/docx |
| `archive` | 定稿归档 |
| `status` | 项目状态 |

## AI 协作写作流程

### Pipeline v3 流水线

完整的人机协作写作流水线："AI 生成草稿 → 作者讨论修改 → 确认定稿"

```
主线 → [AI生成卷纲] → [人审/讨论] → 卷纲定稿
     → [AI拆章节] → [人审/讨论] → 章节列表定稿
     → [AI写章节细纲] → [人审/讨论] → 细纲定稿
     → [AI写正文] → [人审/讨论/修改] → 章节完成
```

**Pipeline 命令**：
| 命令 | 说明 |
|------|------|
| `story:plan --volume N` | AI 生成卷纲草稿 |
| `story:plan --volume N --revise` | 讨论修改卷纲 |
| `story:plan --volume N --confirm` | 确认卷纲定稿 |
| `story:plan --chapters N` | AI 拆分章节列表 |
| `story:outline --draft N --all` | 批量生成细纲 |
| `story:write N --draft` | AI 写正文草稿 |

### Stage 状态流转

- **卷**：`draft` → `confirmed`
- **章节**：`outline-draft` → `outline-confirmed` → `writing` → `review` → `done`

### 传统人机协作流程

```
1. story:write 5        # 生成 Agent Prompt
2. AI Agent 生成内容     # 基于 Prompt 创作
3. story:review 5 --ai <文件>  # 导入 AI 内容
4. 用户修改章节         # 人机协作
5. story:review 5       # 对比差异
6. story:learn 5        # 学习用户风格
7. story:update-specs 5 # 检测新设定 + 生成摘要
8. story:recall 5       # 回顾本章摘要
9. story:export 1-5     # 导出交稿
```

## 许可

MIT
