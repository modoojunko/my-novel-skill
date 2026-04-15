---
name: my-novel-v2
description: 所有小说创作相关操作必须通过此 skill 处理，包括：项目初始化、信息收集、世界观设定、大纲规划、提示词生成、章节写作、验证归档、多平台发布等。触发场景：用户要求写小说、创建小说项目、收集小说信息、设定世界观、规划卷纲章节大纲、生成写作提示词、写章节、验证章节、归档章节、导出小说、发布章节到平台、查看小说进度、以及任何需要使用 my-novel-skill 工具的小说创作任务。
---

# my-novel-v2 -- AI 辅助小说写作工作流（简化版）

> 主 Agent 管流程 + 子 Agent 写正文。三目录设计 + 全 YAML 数据格式 + 智能提示词分层摘要 + 角色六层认知模型 + 多平台发布。

## 📖 Agent 操作指南

**本项目使用 v2 简化架构，核心特点：**

1. **主 Agent + 子 Agent 分离**：主 Agent 负责收集信息和生成提示词，子 Agent 负责写正文
2. **三目录设计**：
   - `project_root`: story.yaml（配置文件）
   - `process/`: 过程管理产物（INFO, OUTLINE, PROMPTS, TEMPLATES）
   - `output/`: 最终正文（CONTENT, EXPORT, ARCHIVE）
3. **零依赖**：仅使用 Python 标准库，yaml 可选（json 自动降级）
4. **写一卷规划一卷**：渐进式创作，避免前期负担过重
5. **多平台发布**：支持发布章节到飞书文档等平台

## 核心理念

**AI 问核心 → AI 扩写 → 用户确认**，每个阶段都遵循这个模式。

### 整体流程

```
【第一阶段：项目初始化 & 前置信息（只做一次）】
1. init —— 创建项目
2. collect core —— 收集小说核心信息
3. collect protagonist —— 创建主角
4. world basic —— 设定世界观基础

【第二阶段：第 N 卷规划（每卷开始前做）】
5. plan volume N —— 规划第 N 卷
6. plan chapter N M —— 规划第 M 章

【第三阶段：每章写作（循环）】
7. write M --prompt —— 生成第 M 章提示词
8. 子 Agent 写正文
9. verify M —— 验证章节是否符合大纲
10. archive M —— 归档第 M 章

【第四阶段：发布（可选）】
11. publish M feishu —— 发布第 M 章到飞书
12. publish status —— 查看发布状态
```

## 命令参考（v2）

| 命令 | 功能 |
|------|------|
| `story init` | 初始化新项目 |
| `story status` | 查看项目状态 |
| `story collect <target>` | 收集信息（core, protagonist, volume <num>） |
| `story world <target>` | 世界观管理（basic, faction, history, power, organization, location, list） |
| `story plan volume <num>` | 规划卷大纲 |
| `story plan chapter <vol> <num>` | 规划章节大纲 |
| `story write <num> --prompt` | 生成章节提示词 |
| `story verify <num>` | 验证章节是否符合大纲 |
| `story archive <num>` | 归档已完成章节 |
| `story export` | 导出小说 |
| `story github <subcommand>` | GitHub Issue 管理 |
| `story publish <target> <platform>` | 发布章节到平台（check, status, <chapter>, all） |

## 目录结构速查（v2）

```
{项目根}/
  story.yaml                        # 配置 + 总进度（YAML，json 降级）
  process/                          # 过程管理产物
    INFO/                           # 收集到的信息
      01-core.yaml                   # 小说核心信息
      world/                         # 世界观设定
        basic.yaml                    # 基础世界观
        factions/                     # 势力设定
        history.yaml                  # 历史设定
        powers/                       # 力量体系
        organizations/                # 组织设定
        locations/                    # 地点设定
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

### 5. 多平台发布机制

支持将已归档的章节发布到多个平台：
- **适配器模式**：每个平台有独立的适配器
- **内容哈希检测**：自动跳过未变更内容
- **发布状态追踪**：记录发布时间、URL、状态
- **支持平台**：
  - 飞书文档（feishu）
  - 知乎（zhihu，预留）
  - 起点（qidian，预留）

## 世界观管理

使用 `story world` 命令管理完整的世界观设定：

| 命令 | 功能 |
|------|------|
| `story world basic` | 设定基础世界观 |
| `story world faction <name>` | 设定/编辑势力 |
| `story world history` | 设定历史背景 |
| `story world power <name>` | 设定力量体系 |
| `story world organization <name>` | 设定组织 |
| `story world location <name>` | 设定地点 |
| `story world list` | 列出所有世界观设定 |

## 章节验证

使用 `story verify <num>` 验证章节内容是否符合大纲要求：
- 检查章节是否完成了大纲中的任务
- 检查是否有剧情 inconsistency
- 检查 POV 认知约束是否遵守

## 多平台发布

### 发布命令

| 命令 | 功能 |
|------|------|
| `story publish check <platform>` | 检查平台可用性 |
| `story publish status` | 查看发布状态 |
| `story publish <chapter> <platform>` | 发布单章到指定平台 |
| `story publish all <platform>` | 发布所有未发布章节 |
| `story publish ... --force` | 强制重新发布 |

### 平台配置

在 story.yaml 中配置平台信息：
```yaml
publishing:
  platforms:
    feishu:
      folder_id: "飞书文件夹ID"
```

## 用户说"开始写小说"后的引导流程

1. **检查是否在项目中**：如果没有 story.yaml，先引导 `story init`
2. **检查核心信息**：如果没有 01-core.yaml，引导 `story collect core`
3. **检查主角**：如果没有主角，引导 `story collect protagonist`
4. **检查世界观**：可选引导 `story world basic`
5. **检查卷大纲**：如果没有 volume-001.yaml，引导 `story plan volume 1`
6. **开始写作**：引导 `story write 1 --prompt`

## v2 与 v1 的主要区别

| 特性 | v1 | v2 |
|------|-----|-----|
| 架构 | 单 Agent | 主 Agent + 子 Agent |
| 目录 | 单目录混合 | 三目录分离（process/output/templates） |
| 数据格式 | JSON + Markdown | 全 YAML（JSON 降级） |
| 角色系统 | 基础设定 | 六层认知模型 |
| 提示词 | 简单组合 | 分层智能摘要 |
| 创作方式 | 一次性规划 | 写一卷规划一卷 |
| 世界观 | 基础支持 | 完整框架（faction/history/power/organization/location） |
| 验证 | 无 | 章节验证机制 |
| 发布 | 无 | 多平台发布支持 |

## GitHub Issue 管理功能

my-novel-skill 集成了 GitHub Issue 查阅和创建功能，可以直接通过命令行提交和查看 issues。

### 前置条件

1. **安装 GitHub CLI**
   ```bash
   # Ubuntu/Debian
   (type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
   && sudo mkdir -p -m 755 /etc/apt/keyrings \
   && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
   && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
   && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
   && sudo apt update \
   && sudo apt install gh -y
   ```

2. **认证登录**
   ```bash
   gh auth login
   ```
   按照提示完成认证。

3. **检查状态**
   ```bash
   story github check
   ```

### GitHub 命令列表

| 命令 | 功能 |
|------|------|
| `story github check` | 检查 GitHub CLI 安装和认证状态 |
| `story github list` | 列出 Issues（默认显示开放的） |
| `story github view <number>` | 查看单个 Issue |
| `story github create` | 创建 Issue（交互式） |
| `story github bug` | 创建 Bug 报告 |
| `story github feature` | 创建功能需求 |

### 对话式 Issue 提交流程

当用户说"我要提一个 issue"、"发现一个 bug"或"有个功能建议"时，按以下流程处理：

#### 1. 确认 Issue 类型

询问用户：
```
你想提交什么类型的 issue？
1. 🐛 Bug 反馈 - 工具使用中遇到的问题
2. 🚀 功能需求 - 希望添加的新功能
3. 💬 其他 - 其他问题或建议
```

#### 2. 收集信息

根据类型引导用户提供必要信息：

**Bug 反馈：**
- 问题描述（关于工具的问题）
- 重现步骤
- 预期行为 vs 实际行为
- 错误信息（如果有）

**功能需求：**
- 需求描述（关于工具功能的建议）
- 使用场景
- 建议方案（可选）

#### 3. 使用对应命令提交

**Bug 反馈示例：**
```bash
story github bug \
  --title "story plan 命令执行出错" \
  --description "使用 story plan 命令时出现错误" \
  --steps "1. 执行 story plan chapter 1 2\n2. ..." \
  --expected "正常生成章节大纲" \
  --actual "报错退出" \
  --error-message "[粘贴错误信息]"
```

**功能需求示例：**
```bash
story github feature \
  --title "自动生成章节摘要" \
  --description "希望能自动生成章节内容摘要" \
  --use-case "写完一章后，自动生成该章的剧情摘要" \
  --suggestion "在 archive 命令中添加 --summary 选项"
```

#### 4. 提交后

- 显示 issue 编号和 URL
- 询问是否需要在浏览器中打开
- 告知用户可以随时查看或更新 issue

**注意：** Issue 内容应只关于 my-novel-skill 工具本身，不要包含具体小说内容、剧情设定等信息。
