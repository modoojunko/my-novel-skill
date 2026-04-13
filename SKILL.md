---
name: my-novel-v2
description: 用户提到"小说"、"写小说"、"小说工作流"、"写章节"、"大纲"、"卷管理"、"归档章节"、"小说进度"，或对已初始化的 novel-workflow v2 项目执行任何操作（查看状态、编辑大纲、写作、归档等）。
---

# my-novel-v2 -- AI 辅助小说写作工作流（简化版）

> 主 Agent 管流程 + 子 Agent 写正文。三目录设计 + 全 YAML 数据格式 + 智能提示词分层摘要 + 角色六层认知模型。

## 📖 Agent 操作指南

**本项目使用 v2 简化架构，核心特点：**

1. **主 Agent + 子 Agent 分离**：主 Agent 负责收集信息和生成提示词，子 Agent 负责写正文
2. **三目录设计**：
   - `project_root`: story.yaml + templates/
   - `process/`: 过程管理产物（INFO, OUTLINE, PROMPTS, TEMPLATES）
   - `output/`: 最终正文（CONTENT, EXPORT, ARCHIVE）
3. **零依赖**：仅使用 Python 标准库，yaml 可选（json 自动降级）
4. **写一卷规划一卷**：渐进式创作，避免前期负担过重

## 核心理念

**AI 问核心 → AI 扩写 → 用户确认**，每个阶段都遵循这个模式。

### 整体流程

```
【第一阶段：项目初始化 & 前置信息（只做一次）】
1. init —— 创建项目
2. collect core —— 收集小说核心信息
3. collect protagonist —— 创建主角

【第二阶段：第 N 卷规划（每卷开始前做）】
4. plan volume N —— 规划第 N 卷
5. plan chapter N M —— 规划第 M 章

【第三阶段：每章写作（循环）】
6. write M --prompt —— 生成第 M 章提示词
7. 子 Agent 写正文
8. archive M —— 归档第 M 章
```

## 命令参考（v2）

| 命令 | 功能 |
|------|------|
| `story init` | 初始化新项目 |
| `story status` | 查看项目状态 |
| `story collect <target>` | 收集信息（core, protagonist, volume <num>） |
| `story plan volume <num>` | 规划卷大纲 |
| `story plan chapter <vol> <num>` | 规划章节大纲 |
| `story write <num> --prompt` | 生成章节提示词 |
| `story archive <num>` | 归档已完成章节 |
| `story export` | 导出小说 |

## 目录结构速查（v2）

```
{项目根}/
  story.yaml                        # 配置 + 总进度（YAML，json 降级）
  process/                          # 过程管理产物
    INFO/                           # 收集到的信息
      01-core.yaml                   # 小说核心信息
      characters/                    # 角色分类目录
        protagonist/                  # 主角（完整设定）
        main_cast/                    # 主角团（完整设定）
        supporting/                   # 次要配角（简化设定）
        guest/                        # 路人（极简设定）
    OUTLINE/                        # 大纲草稿
      volume-001.yaml               # 卷大纲
      volume-001/
        chapter-001.yaml            # 章大纲
        snapshots/                   # 章节设定快照
    PROMPTS/                        # 生成的提示词
      chapter-001-prompt.md
    TEMPLATES/                      # 提示词模板
      collect/                       # 收集阶段的问题模板
      expand/                        # 扩写阶段的提示词模板
    progress.yaml                   # 统一进度管理
  output/                           # 最终正文、归档
    CONTENT/
      volume-001/
        chapter-001.md               # 正文
        chapter-001.tasks.md         # 任务清单
    EXPORT/                         # 导出文件
    ARCHIVE/                        # 已归档章节
```

## 关键机制（v2 核心）

### 1. 角色六层认知模型

每个主角/主角团角色都有：
- **L1 世界观**：角色如何看待这个世界
- **L2 自我定义**：角色认为自己是谁
- **L3 价值观**：什么对角色最重要
- **L4 核心能力**：角色天生/已掌握的能力
- **L5 技能**：后天学习的技能
- **L6 环境**：角色当前所处环境

### 2. 提示词分层摘要（避免被截断）

| 层级 | 内容 | 处理方式 | Token 预算 |
|------|------|----------|-----------|
| **L0 必须有** | 本章大纲、本章任务清单、当前 POV 角色认知 | 全文保留 | ~30% |
| **L1 很重要** | 本卷大纲、主角设定、前 3 章快照摘要 | 全文保留 | ~30% |
| **L2 有用** | 其他重要配角设定、前 4-10 章快照极简摘要 | 智能摘要 | ~20% |
| **L3 可选** | 更早的章节、世界观细节 | 只在需要时加载 | ~20% |

### 3. 设定快照（防止乱写前面剧情）

每写完一章，生成该章结束时的设定快照，记录：
- 哪些情节已发生
- 哪些角色已出场
- 哪些信息已 revealed
- 人物状态变化（心理、关系等）
- 伏笔埋设情况

### 4. POV 认知约束（防止角色提前知道后面剧情）

每个角色有独立的认知状态，严格遵守：
- ✅ 可以写该角色看到、听到、推理出的信息
- ❌ 不能写该角色不可能知道的信息
- ❌ 不能直呼其名不认识的角色

## 用户说"开始写小说"后的引导流程

1. **检查是否在项目中**：如果没有 story.yaml，先引导 `story init`
2. **检查核心信息**：如果没有 01-core.yaml，引导 `story collect core`
3. **检查主角**：如果没有主角，引导 `story collect protagonist`
4. **检查卷大纲**：如果没有 volume-001.yaml，引导 `story plan volume 1`
5. **开始写作**：引导 `story write 1 --prompt`

## v2 与 v1 的主要区别

| 特性 | v1 | v2 |
|------|-----|-----|
| 架构 | 单 Agent | 主 Agent + 子 Agent |
| 目录 | 单目录混合 | 三目录分离（process/output/templates） |
| 数据格式 | JSON + Markdown | 全 YAML（JSON 降级） |
| 角色系统 | 基础设定 | 六层认知模型 |
| 提示词 | 简单组合 | 分层智能摘要 |
| 创作方式 | 一次性规划 | 写一卷规划一卷 |
