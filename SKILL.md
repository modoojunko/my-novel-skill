---
name: my-novel
description: 用户提到"小说"、"写小说"、"小说工作流"、"写章节"、"大纲"、"卷管理"、"归档章节"、"小说进度"，或对已初始化的 novel-workflow 项目执行任何操作（查看状态、编辑大纲、写作、归档等）。
---

# my-novel -- AI 辅助小说写作工作流

> 把小说创作拆解为结构化的工作流：概念 -> 设定 -> 大纲 -> 写作 -> 归档。每一层都有明确的输入输出，AI 在每一层发挥不同作用。

## 📖 Agent 操作指南

**如果你是 AI Agent，请先阅读：[AGENT_GUIDE.md](./AGENT_GUIDE.md)**

这份指南告诉你：
- 如何从头到尾协助作家完成一部小说
- 每个阶段该做什么、问什么、提供什么
- 如何根据项目状态建议下一步
- 各阶段的对话模板
- **如何直接使用 `--json` 模式自动执行，无需用户复制粘贴**

## 核心理念

小说写作最怕"写到一半发现结构崩了"。这个工作流的核心是 **先结构后内容，先大纲后正文**。

参考 OpenSpec 的软件工程实践（proposal -> specs -> design -> tasks -> implement -> archive），将小说创作映射为类似的分层流程：

| 层级 | 对应 | 产出 |
|------|------|------|
| 概念 | proposal | story-concept.md（故事概要/核心主题） |
| 设定 | specs | SPECS/（人物、世界观、元设定） |
| 大纲 | design | OUTLINE/（总纲 -> 卷纲 -> 章节大纲） |
| 正文 | implement | CONTENT/（按卷/章节组织的正文） |
| 归档 | archive | ARCHIVE/（定稿 + 变更记录） |

### 关键设计决策

1. **卷是独立故事弧**：每卷有自己的名称、主题、高潮，不是简单地把章节分组
2. **章节大纲含场景列表**：每个章节大纲预排场景，标注 POV 和预估字数，写作时有据可依
3. **归档保留完整上下文**：每章归档时同时保存正文、任务清单、大纲、变更记录，方便回溯
4. **风格学习系统**：从用户修改中提取风格模式，让 AI 输出越来越符合用户风格
5. **POV 认知约束**：严格的视角约束系统，防止角色出现"上帝视角"

### 子 Agent 架构（核心！）

> 核心理念：**主 Agent 管流程，子 Agent 写正文，职责分离防止"忘事"**

```
主 Agent（当前对话）
    ↓ 准备完整 Prompt + tasks.md 约束清单
    ↓ 调用
子 Agent（隔离上下文，skills/my-novel-write）
    ↓ 只根据 Prompt + tasks.md 写正文
    ↓ 输出
三个文件：
  - chapter-003.md（正文）
  - chapter-003.tasks.md（约束清单，场景已标记 [x]）
  - chapter-003.history.md（修改历史）
```

**关键设计：**
1. **子 Agent 隔离**：不记忆之前的对话，只接收当前 Prompt，避免"忘事"
2. **tasks.md 约束**：从给用户的鸡肋清单 → 给子 Agent 的硬性约束
3. **history.md 记录**：记录整个修改过程（用户直接改 / 用户提要求改）
4. **简化流程**：暂时去掉 review/learn，减少复杂度

### 写作阶段流程

```
用户："帮我写第 3 章"
    ↓
主 Agent：
  1. 运行 `story write 3 --draft --json`
  2. 生成 chapter-003.tasks.md（约束清单）
  3. 调用子 Agent my-novel-write
    ↓
子 Agent：
  - 只根据完整 Prompt + tasks.md 写正文
  - 输出：chapter-003.md + 更新后的 tasks.md + history.md
    ↓
用户审阅修改：
  - 方式 A：直接改 chapter-003.md → 自动追加到 history.md
  - 方式 B：说"把对话改幽默点" → 主 Agent 调用子 Agent 改 → 记录到 history.md
    ↓
用户："定稿了"
    ↓
主 Agent 一步步引导收尾：
  1. update-specs？[用户确认] → 执行
  2. snapshot？[用户确认] → 执行
  3. archive？[用户确认] → 执行
```

## 命令参考

| 命令 | 功能 | 典型参数 |
|------|------|---------|
| `story:init` | 初始化小说项目 | `[--non-interactive] [--title "书名"] [--genre "类型"] [--words 500000] [--volumes 3]` |
| `story:status` | 查看项目状态 | `[--json]` |
| `story:propose` | 创建创作意图 | `[目标] [标题] [--non-interactive]` |
| `story:plan` | 规划流水线 | `[--volume N] [--chapters N] [--revise] [--confirm] [--json]` |
| `story:define` | 设定库管理 | `[character/world] [名称] [--list/--view/--edit/--delete]` |
| `story:draft` | 设定补全 | `[character/world/meta] [名称] [--ai 文件] [--json]` |
| `story:volume` | 卷管理 | `[卷号] [--init] [--init-all] [--list]` |
| `story:outline` | 编辑大纲 | `[target] [--list] [--draft N] [--revise] [--confirm] [--all] [--volume N]` |
| `story:write` | 写作模式 | `[章节号] [--draft] [--revise] [--confirm] [--show] [--json]` |
| `story:review` | 人机差异对比 | `[章节号] [--ai FILE] [--stat] [--diff]` |
| `story:learn` | 风格学习引擎 | `[章节号] [--force]` |
| `story:style` | 风格档案管理 | `[--prompts] [--full] [--reset] [--force]` |
| `story:stats` | 学习进度+字数统计 | `[--words] [--learning] [--trend] [--export FILE]` |
| `story:update-specs` | 写作后更新设定 | `[章节] [--auto] [--view] [-v 卷号]` |
| `story:recall` | 章节回顾 | `[章节/范围] [--recent N] [--full] [--snapshot]` |
| `story:snapshot` | 章节设定快照 | `[章节号] [--view] [--list] [--prompt] [--volume N]` |
| `story:export` | 导出小说 | `[范围] [--format txt/docx] [--volume N] [-o 文件名]` |
| `story:archive` | 定稿归档 | `[章节号] [--preview] [--dry-run]` |

别名：`s`->status, `p`->propose, `n`->plan, `v`->volume, `w`->write, `a`->archive, `o`->outline, `i`->init, `r`->review, `l`->learn, `t`->style, `u`->stats, `sp`->snapshot

## 目录结构速查

### 默认结构

```
{项目根}/
  story.json                        # 核心配置（JSON）
  SPECS/
    characters/{角色名}.md           # 人物设定
    world/*.md                      # 世界观
    meta/
      story-concept.md              # 故事概念
  OUTLINE/
    meta.md                         # 总大纲
    volume-001.md                     # 卷大纲
    volume-001/
      chapter-NNN.md                # 章节大纲
      snapshots/                    # 章节设定快照
      summaries/                    # 章节摘要
  CONTENT/
    volume-001/
      chapter-NNN.md                  # 正文
  STYLE/                              # 风格学习数据
    profile.json                      # 用户风格档案
    prompts/                          # 可复用的 prompt 片段
    history/                          # 修改历史记录
  EXPORT/                             # 导出文件
  ARCHIVE/                            # 归档
  templates/                          # 写作模板
```

### 自定义目录配置（story.json）

支持通过 `story.json` 中的 `paths` 字段自定义目录：

```json
{
  "paths": {
    "process_dir": "process",    // 过程文件目录（大纲、草稿等）
    "output_dir": "output",      // 最终输出目录（正文）
    "draft": "output/draft",     // 草稿目录
    "archive": "output/archive"  // 归档目录
  }
}
```

**重要：代码中应使用 `paths.load_project_paths(root)` 获取路径，不要硬编码！**

## 项目查找规则

除 `init` 外，所有工作流先执行：

1. 检查当前工作目录是否有 `story.json` -> 有就用当前目录作为项目根
2. **不会向上遍历父目录**（避免浪费 token）
3. 没有找到 -> 提示用户先 `story:init` 初始化项目

## 边界与防坑

**不要跳过大纲直接写作。** 没有章节大纲就写作，很容易写到一半发现结构崩了。如果用户急着写，至少花 3 分钟列个场景列表。

**归档是单向的。** 一旦归档，正文从 CONTENT/ 移到 ARCHIVE/，不会删除但不会自动同步后续修改。

**编码兼容性。** 所有文件使用 UTF-8 编码。

---

## 用户说"定稿了"之后的引导逻辑

当用户说"定稿了"、"可以了"、"就这样吧"等表示章节完成的话时，按以下三步引导，每一步都需要用户确认：

### 第一步：update-specs
```
好的！接下来按顺序收尾。

第一步：更新角色设定？
这会扫描本章内容，检测新揭示的角色和信息，并更新到人物设定中。

要执行吗？（是/否）
```
- 用户说"是" → 运行 `python story.py update-specs <章节号>`
- 用户说"否" → 跳过，进入第二步

### 第二步：snapshot
```
第二步：生成设定快照？
这会记录本章结束时的设定状态（人物心理、剧情进度、伏笔等），方便后续章节参考。

要执行吗？（是/否）
```
- 用户说"是" → 运行 `python story.py snapshot <章节号>`
- 用户说"否" → 跳过，进入第三步

### 第三步：archive
```
第三步：归档本章？
这会将本章归档到 archive 目录，保存完整上下文。

要执行吗？（是/否）
```
- 用户说"是" → 运行 `python story.py archive <章节号>`
- 用户说"否" → 跳过

### 全部完成后
```
完成！第 X 章已收尾。

想继续写下一章，还是先看看整体状态？
```

---

**再次提醒：AI Agent 请务必阅读 [AGENT_GUIDE.md](./AGENT_GUIDE.md) 了解完整操作流程！**
