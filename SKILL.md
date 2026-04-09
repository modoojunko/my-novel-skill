---
name: my-novel
description: 用户提到"小说"、"写小说"、"小说工作流"、"写章节"、"大纲"、"卷管理"、"归档章节"、"小说进度"，或对已初始化的 novel-workflow 项目执行任何操作（查看状态、编辑大纲、写作、归档等）。
---

# my-novel -- AI 辅助小说写作工作流

> 把小说创作拆解为结构化的工作流：概念 -> 设定 -> 大纲 -> 写作 -> 归档。每一层都有明确的输入输出，AI 在每一层发挥不同作用。

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

### 思维模式

处理小说相关请求时，先回答三个问题：

1. **当前在哪一步？** 是构思阶段、大纲阶段、还是写作阶段？不同的阶段提供不同粒度的帮助
2. **用户需要什么？** 是项目管理（初始化/查看状态），还是创作辅助（写大纲/写正文）？
3. **设定是否一致？** 写作和大纲编辑时，时刻对照 SPECS/ 里的设定，避免前后矛盾

## 工具选择框架

```mermaid
flowchart TD
    A[用户请求] --> B{项目已初始化？}
    B -->|否| C[story:init]
    B -->|是| D{请求类型？}
    D -->|开始新章节/继续写| E[story:write]
    D -->|写大纲/看大纲结构| F[story:outline]
    D -->|卷管理/初始化卷| G[story:volume]
    D -->|创建创作意图| H[story:propose]
    D -->|章节定稿/归档| I[story:archive]
    D -->|查看进度/状态| J[story:status]
    D -->|讨论情节/人物/世界观| K[AI 创作辅助]
    K --> L{具体方向？}
    L -->|人物讨论| M[读 SPECS/characters/ -> 建议]
    L -->|世界观扩展| N[读 SPECS/world/ -> 扩写]
    L -->|情节推演| O[读 OUTLINE/ -> 按大纲推演]
```

**兜底规则**：用户提到"小说"但没有具体指令 -> 运行 `story:status` 展示当前项目状态。

## AI 协作写作工作流

> 核心理念：**Agent 写 → 人改 → Agent 学 → 减少修改**
>
> 这个 skill 是给 AI Agent 用的，Agent 本身有大模型能力。skill 提供结构化的 prompt 模板、差异分析、风格学习，让 Agent 的输出越来越符合用户的写作风格。

### 完整工作流

```mermaid
flowchart LR
    A[story:write 5] --> B[生成 Agent Prompt]
    B --> C[Agent 生成内容]
    C --> D[story:review --ai <文件>]
    D --> E[用户修改]
    E --> F[story:review]
    F --> G[差异分析]
    G --> H[story:learn]
    H --> I[提取风格模式]
    I --> J[更新 STYLE/prompts/]
    J --> K[下次 write 更精准]
    K --> C
```

### 工作流详解

| 阶段 | 命令 | 说明 |
|------|------|------|
| 1. 生成 Prompt | `story:write 5 --show` | 生成 Agent 写作 Prompt 模板 |
| 2. AI 生成 | Agent 收到 Prompt | Agent 使用内置大模型生成内容 |
| 3. 导入内容 | `story:review 5 --ai <文件>` | 导入 AI 生成的内容 |
| 4. 用户修改 | 在章节文件中修改 | 人工作为审核者和修改者 |
| 5. 差异分析 | `story:review 5` | 对比 AI vs 人的差异，计算修改率 |
| 6. 风格学习 | `story:learn 5` | 从修改中提取风格模式 |
| 7. 查看进度 | `story:stats` | 查看学习进度和修改率趋势 |

### 目录结构变更

```
{项目根}/
  STYLE/                    # [NEW] 风格学习数据
  ├── profile.json          # 用户风格档案
  ├── prompts/              # [NEW] 可复用的 prompt 片段
  │   ├── vocabulary.md     # 词汇偏好
  │   ├── sentence.md       # 句式偏好
  │   ├── pacing.md         # 节奏偏好
  │   └── full_guide.md     # 完整风格指南
  └── history/              # 修改历史记录
      └── chapter-005/
          ├── ai_raw.md     # AI 原始生成
          ├── human_final.md # 人的最终版本
          └── analysis.json  # 差异分析结果
```

### 风格学习机制

**不依赖 fine-tune**，采用 Prompt Engineering 方案：

1. **差异提取**：分析人修改了哪些词/句式
2. **模式生成**：生成可注入 Agent Prompt 的 Markdown 片段
3. **渐进优化**：学习越多，Agent 输出越接近用户风格

**目标**：修改率从初始 50% 逐步降低到 15%

## 前置检查

除 `init` 外，所有工作流先执行：

1. 检查当前工作目录是否有 `story.json` -> 有就用当前目录作为项目根
2. 没有 -> 向上遍历目录（最多 10 层）查找 `story.json`
3. 都没有 -> 提示用户先 `story:init` 初始化项目

找到项目根后，读取 `story.json` 获取配置信息（书名、结构、进度等），后续工作流都需要这个配置。

## 命令参考

| 命令 | 功能 | 典型参数 |
|------|------|---------|
| `story:init` | 初始化小说项目 | `[--non-interactive] [--chapters-per-volume N] [--world TEXT] [--characters JSON] [--volume-titles JSON]` |
| `story:propose` | 创建创作意图 | `[目标] [标题] [--non-interactive]` |
| `story:plan` | 规划流水线 | `[--volume N] [--chapters N] [--interactive] [--revise] [--confirm] [--non-interactive] [--conflict TEXT] [--arc TEXT] [--events TEXT] [--tone TEXT]` |
| `story:define` | 设定库管理 | `[character/world] [名称] [--list/--view/--edit/--delete] [--non-interactive] [--force] [--cognition JSON] [--category TEXT]` |
| `story:volume` | 卷管理 | `[卷号] [--init] [--init-all] [--list]` |
| `story:outline` | 编辑大纲 | `[target] [--list] [--draft N] [--revise] [--confirm] [--all] [--volume N]` |
| `story:write` | 写作模式 | `[章节号] [--draft] [--revise] [--confirm] [--show] [--prompt]` |
| `story:review` | 人机差异对比 | `[章节号] [--ai FILE] [--stat] [--diff]` |
| `story:learn` | 风格学习引擎 | `[章节号] [--force]` |
| `story:style` | 风格档案管理 | `[--prompts] [--full] [--reset] [--force]` |
| `story:stats` | 学习进度+字数统计 | `[--words] [--learning] [--trend] [--export FILE]` |
| `story:update-specs` | 写作后更新设定 | `[章节] [--auto] [--view] [-v 卷号]` |
| `story:recall` | 章节回顾 | `[章节/范围] [--recent N] [--full] [--snapshot]` |
| `story:snapshot` | 章节设定快照 | `[章节号] [--view] [--list] [--prompt] [--volume N]` |
| `story:export` | 导出小说 | `[范围] [--format txt/docx] [--volume N] [-o 文件名]` |
| `story:archive` | 定稿归档 | `[章节号] [--preview] [--dry-run]` |
| `story:status` | 查看项目状态 | `[--json]` |

别名：`s`->status, `p`->propose, `n`->plan, `v`->volume, `w`->write, `a`->archive, `o`->outline, `i`->init, `r`->review, `l`->learn, `t`->style, `u`->stats, `sp`->snapshot

---

## 工作流 0：init（初始化小说项目）[MIXED]

初始化创建完整的目录结构和配置文件。交互模式下由用户填写信息，非交互模式使用默认值。

### 执行步骤

#### 第一段：收集信息 [REASONING]

1. **确认项目位置**：默认当前目录，用户可指定路径
2. **交互式收集**（非交互模式跳过此步）：
   - 书名（必填）
   - 类型选择：玄幻/都市/科幻/悬疑/言情/武侠/历史/游戏/轻小说/其他
   - 目标字数（默认 500000）
   - 计划卷数（默认 3）
   - 每卷章节数（默认 30）
   - 故事概要（格式提示："一个___的___，在___中，必须___，否则___。"）
   - 主要人物（姓名 + 身份 + 描述，可添加多个，回车结束）
   - 世界观/背景（可选）
   - 每卷名称和主题（交互式逐卷填写）

#### 第二段：创建项目结构 [PROCEDURE]

```bash
python {STORY_DIR}/story.py init [路径] [--non-interactive] \
  [--title "书名"] [--genre "类型"] [--words 500000] [--volumes 3] [--logline "概要"] \
  [--chapters-per-volume 30] [--world "世界观"] \
  [--characters '[{"name":"张三","role":"主角","desc":"剑客"}]'] \
  [--volume-titles '[{"title":"风起","theme":"热血"}]']
```

脚本会自动创建：

```
{项目根}/
  story.json              # 配置文件（书名/结构/进度/风格）
  SPECS/
    characters/           # 人物设定
    world/                # 世界观
    meta/
      story-concept.md    # 故事概念文件
  OUTLINE/
    meta.md               # 总大纲
    volume-001.md           # 各卷大纲
    volume-001/             # 各卷章节细纲、快照、摘要
      chapter-001.md
      snapshots/
      summaries/
  CONTENT/
    volume-001/             # 各卷正文
      chapter-001.md
    draft/                # 草稿
    summaries/             # 章节摘要
  STYLE/
    prompts/              # 风格提示词
    history/              # 风格历史
  EXPORT/                  # 导出文件
  ARCHIVE/                # 归档
  templates/              # 模板（chapter.md / character.md / scene.md / outline.md）
  README.md
  .gitignore
```

#### 第三段：引导用户 [REASONING]

初始化完成后，告知用户目录结构和下一步操作建议：
- `story:propose` -> 创建更详细的创作意图
- `story:volume --init-all` -> 初始化所有卷的目录
- `story:outline --init-chapters 1` -> 初始化第一卷的章节大纲

### story.json 配置结构

```json
{
  "meta": { "version": "1.0", "created": "YYYY-MM-DD", "language": "zh-CN" },
  "book": { "title": "书名", "genre": "类型", "target_words": 500000, "current_words": 0 },
  "story": { "logline": "概要", "world": "世界观", "tone": "热血/成长" },
  "structure": {
    "volumes": 3,
    "chapters_per_volume": 30,
    "volume_titles": [
      { "num": 1, "title": "卷名", "theme": "主题" }
    ]
  },
  "paths": {
    "process_dir": "过程文件目录（可选，默认项目根）",
    "output_dir": "最终输出目录（可选，默认项目根/CONTENT）"
  },
  "progress": {
    "current_volume": 1,
    "current_chapter": 0,
    "written_chapters": [],
    "archived_chapters": []
  },
  "style": { "pov": "third", "tense": "past", "tone": "serious" }
}
```

---

## 工作流 1：propose（创建创作意图）[REASONING]

在正式写作前，为特定目标（概念/卷/章节）创建结构化的创作意图文档。

### 触发条件

- 用户说"创建提案"、"写个 proposal"、"这个卷/章想写什么"
- 用户想明确某一卷/章的写作方向

### 执行步骤

1. 确定目标类型：
   - `概念`/`concept` -> 故事概念提案
   - `卷N` -> 指定卷的提案
   - `第N章`/`章N` -> 指定章节的提案
   - 不指定 -> AI 引导用户选择

2. 如果是 AI 模式，根据已有信息（story.json、大纲、设定）生成结构化提案，而非创建空模板

3. 提案文件保存到：
   - 概念：`SPECS/meta/proposals/{日期}-story-concept-proposal.md`
   - 卷：`OUTLINE/volume-001/proposals/{日期}-volume-001-proposal.md`
   - 章节：`OUTLINE/proposals/{日期}-chapter-N-proposal.md`

4. 提案内容应包含：
   - 意图描述
   - 与整体故事的关系
   - 涉及的人物和世界观设定
   - 核心场景
   - 情绪目标（读者应该感受到什么）
   - 字数预期

### CLI 调用

```bash
python {STORY_DIR}/story.py propose [目标] [标题]
# 例：story.py propose 卷1 "风起天南的故事弧"
```

---

## 工作流 2：define（设定库管理）[PROCEDURE]

管理人物卡和世界观设定，统一存储在 `SPECS/` 目录下。

### 触发条件

- 用户说"人物"、"角色"、"设定"、"世界观"
- 用户说"创建角色"、"添加设定"
- 用户说"查看所有人物"

### 执行步骤

#### 人物管理

```bash
# 列出所有人物
python {STORY_DIR}/story.py define character --list

# 查看人物详情
python {STORY_DIR}/story.py define character 张三 --view

# 创建新人物（交互式）
python {STORY_DIR}/story.py define character 张三

# 编辑人物（打开编辑器）
python {STORY_DIR}/story.py define character 张三 --edit

# 删除人物（带确认和备份）
python {STORY_DIR}/story.py define character 张三 --delete
```

#### 世界观管理

```bash
# 列出所有世界观设定
python {STORY_DIR}/story.py define world --list

# 查看世界观详情
python {STORY_DIR}/story.py define world 地理 --view

# 创建新世界观（交互式，需选择类别）
python {STORY_DIR}/story.py define world 地理

# 编辑世界观
python {STORY_DIR}/story.py define world 地理 --edit

# 删除世界观
python {STODY_DIR}/story.py define world 地理 --delete
```

#### 搜索

```bash
# 全文搜索设定
python {STORY_DIR}/story.py define --search 关键词
```

#### 概览

```bash
# 显示所有设定概览
python {STORY_DIR}/story.py define
```

### 人物卡模板

```markdown
---
name: 张三
alias: 小三爷
gender: 男
age: 28
occupation: 剑客
status: 存活
tags: [主角, 剑客]
created: 2026-04-08
modified: 2026-04-08
---

# 张三

## 基本信息

**别名/昵称**：小三爷
**性别**：男
**年龄**：28
**职业/身份**：剑客
**状态**：存活

## 外观特征

（描述外貌、穿着、标志性特征等）

## 性格特点

- **核心性格**：（如：冷静、果断、外冷内热）
- **优点**：（如：善于观察、行动力强）
- **缺点**：（如：不善表达、过于理性）
- **口头禅/习惯**：（如有）

## 背景故事

（人物的前史、成长经历）

## 六层认知

> 角色的深层驱动力，决定其在剧情中的抉择、情绪和说话方式。

### 我的世界观

（这个角色对世界的根本看法。如：正派相信正义终将战胜邪恶、宿命论者认为一切早已注定）
→ 影响角色面对事件时的态度和信念

### 我对自己定义

（我是个什么样的人。如：我是个普通但靠谱的人、我注定要成为王）
→ 影响角色的内心独白和行为动机

### 我的价值观

（在艰难决策上的取舍优先级。如：他人感受 > 真相 > 自己、家族荣耀 > 个人幸福）
→ 影响角色在冲突中的选择

### 我的能力

（角色解决问题的方式和核心能力。如：倾听与共情、洞察人心、过目不忘）
→ 决定角色是直接解决问题，还是需要学习成长

### 我的技能

（角色掌握的具体技能。如：整理货架、泡方便面、剑术、编程）
→ 角色日常行为的基础

### 我的环境

（角色所处的物理和社会环境。如：深夜便利店、贵族学院、战场前线）
→ 角色行为和认知的背景约束

## 人物关系

- **家人**：（如有）
- **挚友**：（如有）
- **对手/敌人**：（如有）

## 角色弧

**起点**：（角色的初始状态）
**转折点**：（经历什么事件）
**终点**：（角色最终的成长/变化）

## 本卷/本故事中的目标

（当前故事中角色想要达成的目标）

## 当前状态（随剧情动态更新）

### 已知角色
| 角色 | 关系 | 获知途径 | 获知章节 |
|------|------|---------|---------|
| 李四 | 挚友 | 自我介绍 | 第1章 |
| 王五 | 对手 | 他人介绍 | 第3章 |

### 未知/待揭示角色
- [ ] 神秘人甲（预计第5章登场）

### 已掌握信息
- 江湖上流传的宝剑传说
- 李四的真实身份是...

### 待揭示信息
- [ ] 自己的身世之谜（预计第10章揭示）
- [ ] 师父的遗言真相（预计第8章揭示）
```

### 世界观类别

支持 9 种类别：
- 地理（地理位置、地形、气候）
- 历史（历史事件、时间线）
- 社会（社会结构、制度、文化习俗）
- 魔法/能力（魔法体系、超能力）
- 科技（科技水平、特殊技术）
- 生物（种族、怪物、特殊生物）
- 物品（重要道具、武器、神器）
- 组织（势力、门派、机构）
- 其他

### 文件存储

- 人物：`SPECS/characters/{姓名}.md`
- 世界观：`SPECS/world/{名称}.md`

---

## 工作流 3：volume（卷管理）[PROCEDURE]

管理小说的卷结构：初始化、查看状态、批量操作。

### 触发条件

- 用户说"查看卷"、"初始化卷"、"卷结构"
- 用户说"开始写第二卷"

### 执行步骤

根据操作类型选择命令：

| 操作 | 命令 | 说明 |
|------|------|------|
| 查看所有卷 | `--list` 或无参数 | 表格展示所有卷的大纲/章纲/正文状态 |
| 初始化所有卷 | `--init-all` | 批量创建卷目录和大纲文件，跳过已存在的 |
| 初始化指定卷 | `N --init` | 创建 CONTENT/volume-001/ 和 OUTLINE/volume-001.md |
| 查看指定卷 | `N`（无 --init） | 展示该卷的详细状态（大纲、章纲数、正文数） |

### CLI 调用

```bash
python {STORY_DIR}/story.py volume --list          # 列出所有卷
python {STORY_DIR}/story.py volume --init-all      # 初始化所有卷
python {STORY_DIR}/story.py volume 1 --init        # 初始化卷1
python {STORY_DIR}/story.py volume 1               # 查看卷1状态
```

### 状态列含义

- `[OK]` 大纲：OUTLINE/volume-001.md 是否存在

- `N/M` 章纲：已有章节大纲数 / 每卷章节数
- `[OK]` 正文：CONTENT/volume-001/ 是否存在

---

## 工作流 4：outline（编辑大纲）[MIXED]

大纲是写作的核心骨架。分为三个层级：总纲 -> 卷纲 -> 章节大纲。

### 触发条件

- 用户说"写大纲"、"看大纲"、"编辑大纲"
- 用户说"初始化章节大纲"
- 用户说"第一章大纲是什么"

### 三个层级

| 层级 | 文件 | 内容 |
|------|------|------|
| 总纲 | `OUTLINE/meta.md` | 故事概览、卷结构、主题线索、伏笔记录 |
| 卷纲 | `OUTLINE/volume-001.md` | 本卷主题、卷概述、主要事件、章节安排、高潮、伏笔 |
| 章纲 | `OUTLINE/volume-001/chapter-NNN.md` | 本章目标、POV、场景列表、情节点、关键对话、伏笔、预估字数 |

### 执行步骤

#### 第一段：确定操作 [REASONING]

1. 根据用户意图判断编辑哪个层级
2. 如果用户没有指定，先展示大纲结构树（`--list`），让用户选择

#### 第二段：操作大纲 [MIXED]

**查看结构**：
```bash
python {STORY_DIR}/story.py outline --list
```

**批量初始化章节大纲**（AI 在此基础上填充内容，而非留空模板）：
```bash
python {STORY_DIR}/story.py outline --init-chapters 1    # 初始化卷1的所有章节大纲
```

**编辑指定大纲**：
```bash
python {STORY_DIR}/story.py outline meta                 # 编辑总纲
python {STORY_DIR}/story.py outline 卷1                  # 编辑卷1大纲
python {STORY_DIR}/story.py outline 第5章                # 编辑第5章大纲
```

#### 第三段：AI 辅助填充 [REASONING]

当用户需要 AI 帮助编写大纲内容时：

1. **总纲**：读取 story.json 的 logline、volume_titles、人物设定，生成分卷主题和核心线索
2. **卷纲**：读取总纲 + 该卷的主题，生成本卷的起承转合和章节概述
3. **章纲**：读取卷纲 + 上下章节大纲，生成场景列表（结构化格式）

**章节大纲场景格式**：
```
1. [开场] 场景描述 - POV:xxx - 约800字
2. [发展] 场景描述 - POV:xxx - 约1200字
3. [转折] 场景描述 - POV:xxx - 约1000字
```

### 注意事项

- 编辑大纲时自动读取 story.json 获取卷名和主题（从 `structure.volume_titles`）
- 章节大纲的编号基于 `chapters_per_volume` 计算所属卷号
- 批量初始化跳过已存在的文件，不会覆盖

### outline 增强功能

#### Pipeline 模式：--draft / --revise / --confirm

在 Pipeline 流程中，outline 用于生成和确认章节细纲：

```bash
# AI 生成单章细纲草稿
python {STORY_DIR}/story.py outline --draft 5

# AI 批量生成本卷所有细纲
python {STORY_DIR}/story.py outline --draft 1 --all

# 讨论模式修改细纲
python {STORY_DIR}/story.py outline --revise 5

# 确认细纲定稿（stage → outline-confirmed）
python {STORY_DIR}/story.py outline --confirm 5
```

**stage 流转**：outline-draft → outline-confirmed

#### --expand（展开场景细节）

当卡文时，使用此功能展开场景的详细写作提示：

```bash
# 展开第5章所有场景
python {STORY_DIR}/story.py outline --expand 5

# 只展开第5章第2个场景
python {STORY_DIR}/story.py outline --expand 5 --scene 2
```

**展开输出示例**：
```
============================================================
  场景 2：张三遇见李四
============================================================

  类型: 发展
  POV: 张三

  📝 展开模板
  ----------------------------------------

  ** POV：张三
  ** 地点：（待填充）
  ** 时间：（待填充）
  ** 预期字数：约 800-1500 字

  ** 核心动作：
     - （动作1）
     - （动作2）

  ** 情绪基调：（待填充）

  ** 可能需要的对话：
     - （对话1）
     - （对话2）

  ** 关键细节：
     - （细节1）
     - （细节2）

  ** 与上下文的衔接：
     - 承接：（上一场景如何衔接）
     - 铺垫：（为下一场景埋下什么）
```

#### --swap（交换章节顺序）

调整大纲中的章节顺序：

```bash
# 交换第8章和第10章的大纲
python {STORY_DIR}/story.py outline --swap 8 10
```

**注意**：只交换大纲内容，不移动实际的章节正文文件。

---

## 工作流 5：write（写作模式）[MIXED]

正式写作阶段。为指定章节创建正文文件和任务清单，展示相关参考信息。

### 触发条件

- 用户说"开始写"、"写第N章"、"继续写"
- 用户说"写作模式"

### 执行步骤

#### 第一段：初始化章节 [PROCEDURE]

```bash
python {STORY_DIR}/story.py write [章节号]
# 不指定章节号则自动取 current_chapter + 1
```

脚本会：
1. 创建 `CONTENT/volume-001/chapter-NNN.md`（如果不存在）
2. 创建 `CONTENT/volume-001/chapter-NNN.tasks.md`（写作任务清单）
3. 更新 story.json 的 `progress.current_chapter` 和 `progress.written_chapters`

#### 第二段：展示写作上下文 [REASONING]

写作前，AI 应主动收集并展示以下信息：

1. **章节大纲**：读取 `OUTLINE/volume-001/chapter-NNN.md`，展示场景列表和本章目标
2. **上章回顾**（如果有）：读取上一章正文的最后 500 字，确保衔接
3. **人物设定**：读取本章涉及角色的 `SPECS/characters/xxx.md`
4. **伏笔检查**：检查前序大纲中的"伏笔记录"，确认本章是否需要回收/埋设

#### 第三段：AI 辅助写作 [REASONING]

根据用户的写作需求提供不同层次的辅助：

| 需求 | AI 行为 |
|------|---------|
| "帮我写这一章" | 按大纲的场景列表逐场景写作，严格遵循 POV 和字数预期 |
| "给我一个开头" | 基于上章结尾和本章目标，写 300-500 字的开场 |
| "这段对话不太对" | 基于人物设定调整对话风格和语气 |
| "检查连贯性" | 读取前几章正文，检查情节和人物是否一致 |

### 写作规范

- **POV 一致性**：每章保持同一 POV 角色（除非大纲明确要求切换）
- **场景过渡**：场景之间有明确的过渡段落
- **字数控制**：每个场景尽量控制在预期字数的 +-20% 范围内
- **设置检查**：涉及人物性格/外貌/背景时，对照 SPECS/characters/ 确保一致
- **认知驱动**：角色的态度、选择和行为必须符合其六层认知设定：
  - **世界观** → 面对事件时的态度和信念以此为根基
  - **价值观** → 在两难冲突中的取舍优先级
  - **能力/技能** → 角色只能做其能力范围内的事，超出范围需要学习或求助

### 任务清单格式

```markdown
# 任务清单：第N章

## 写作前检查
- [ ] 回顾本章大纲
- [ ] 确认 POV 角色
- [ ] 列出本章关键场景

## 场景任务
- [ ] 场景 1：开场/设定
- [ ] 场景 2：发展
- [ ] 场景 3：转折/高潮

## 收尾任务
- [ ] 检查情节连贯性
- [ ] 添加过渡
- [ ] 初步自检（错字、语病）

## 预期字数
约 3000 字
```

### write 命令增强：Pipeline 模式

在 Pipeline 流程中，write 用于根据细纲写正文：

```bash
# AI 根据细纲写正文草稿（stage → writing）
python {STORY_DIR}/story.py write 5 --draft

# 讨论模式修改正文
python {STORY_DIR}/story.py write 5 --revise

# 确认正文定稿（stage → done）
python {STORY_DIR}/story.py write 5 --confirm
```

**stage 流转**：outline-confirmed → writing → review → done

### write 命令增强：生成 Agent Prompt

`story:write` 不再只是创建文件，而是生成结构化的 Agent Prompt 模板：

```bash
python {STORY_DIR}/story.py write 5 --show    # 显示完整 Prompt
python {STORY_DIR}/story.py write 5 --prompt  # 仅显示 Prompt 部分
python {STORY_DIR}/story.py write 5 --context # 仅显示上下文部分
```

**Agent Prompt 模板结构**：

```markdown
## 写作任务
章节：第5章
卷：第1卷「风起天南」
POV：张三

## 章节大纲
[从 OUTLINE 读取]

## 场景列表
1. [开场] 场景描述 - POV:张三 - 约800字
2. [发展] 场景描述 - POV:张三 - 约1200字
...

## 人物设定
[从 SPECS 读取相关人物]

## 世界观约束
[从 SPECS/world 读取相关设定]

## 风格指南
[从 STYLE/prompts/ 读取最新模式]

## 上章结尾
[读取上一章最后 500 字]

## POV视角约束（重要！）
你当前是 **张三** 的视角。

**⚠️ 严格遵守以下信息边界：**

**已知道的角色**（可以直接称呼名字）：
  - 李四：挚友（通过自我介绍获知）

**不知道的角色**（禁止直呼其名，用外貌/身份代称）：
  - 王五：必须用代称（如'那个黑衣人'、'拿剑的陌生人'）

**已掌握的信息**：
  - 江湖上流传的宝剑传说

**禁止提前揭示的信息**：
  - ❌ 自己的身世之谜
  - ❌ 师父的遗言真相

**写作规则**：
1. 只能描述张三能看到、听到、感知到的事物
2. 对未知角色，用外貌特征或身份代称
3. 禁止写出张三不可能知道的信息
4. 禁止直接描述其他角色的内心想法

## 写作要求
- 字数：约 3000 字
- POV：必须保持张三视角，遵守上述POV约束
- 禁止：[STYLE/avoid.md 中的内容]
- 逻辑：严格遵守POV角色的认知边界，禁止写出该角色不可能知道的信息

## 角色认知驱动（核心！）

角色 **张三** 的深层认知决定了其行为逻辑：

**世界观**：正义终将战胜邪恶
→ 面对事件时的态度和信念以此为根基

**自我定义**：我是个普通但靠谱的人
→ 内心独白和行为动机由此驱动

**价值观**：他人感受 > 真相 > 自己
→ 在两难冲突中的取舍优先级

**核心能力**：倾听与共情
→ 角色可以直接用共情解决问题

**技能**：整理货架、泡方便面
→ 角色日常行为的基础

**环境**：深夜便利店
→ 角色行为受此环境约束和塑造

**写作规则**：
1. 张三的态度和信念必须符合其世界观
2. 面对两难选择时，优先级必须符合其价值观
3. 角色只能做其能力/技能范围内的事，超出范围需要学习或求助
4. 角色对环境的反应必须符合其生活背景
```

---

## 工作流 6：review（人机差异对比）[PROCEDURE]

AI 生成内容后，用户修改，然后进行差异对比。

### 触发条件

- 用户说"对比差异"、"查看修改"、"审核"
- 用户完成了 AI 内容的修改

### 执行步骤

```bash
# 导入 AI 生成的内容
python {STORY_DIR}/story.py review 5 --ai content.md

# 对比差异
python {STORY_DIR}/story.py review 5

# 仅显示统计
python {STORY_DIR}/story.py review 5 --stat

# 预览 diff 格式
python {STORY_DIR}/story.py review 5 --diff
```

### 差异分析输出

```
═══════════════════════════════════════
        第5章 差异分析报告
═══════════════════════════════════════

  基础统计
  --------------------------------------------------
  AI 生成字数：3200 字
  用户修改字数：480 字
  修改占比：15.0%

  详细统计
  --------------------------------------------------
  新增：120 字 (3 处)
  删除：80 字 (2 处)
  替换：8 处
  未改动：50 处

  高频替换
  --------------------------------------------------
  "非常" -> "极其" (3次)
  "他慢慢地" -> "他" (2次)

  建议
  --------------------------------------------------
  [OK] 修改率很低，AI 写作质量很好！
```

---

## 工作流 7：learn（风格学习引擎）[PROCEDURE]

从审核历史中提取修改模式，生成可复用的风格 Prompt。

### 触发条件

- 用户说"学习风格"、"提取模式"
- 完成了章节审核后

### 执行步骤

```bash
# 学习单个章节
python {STORY_DIR}/story.py learn 5

# 学习所有审核过的章节
python {STORY_DIR}/story.py learn

# 强制重新学习
python {STORY_DIR}/story.py learn --force
```

### 学习流程

1. 读取 `STYLE/history/chapter-005/analysis.json`
2. 提取词汇替换模式（高频词）
3. 提取句式偏好（短句/长句）
4. 提取节奏偏好（快/慢节奏）
5. 更新 `STYLE/prompts/*.md` 文件

### 生成的文件

```markdown
<!-- STYLE/prompts/vocabulary.md -->

## 词汇偏好

### 替换规则
- "非常" -> "极其" / "格外"
- "慢慢地" -> 删除或替换为具体动作
- "说道" -> "开口" / "应道"

### 避免词汇
- 过度使用的形容词
- 陈词滥调
```

---

## 工作流 8：style（风格档案管理）[PROCEDURE]

查看和管理已学习的风格档案。

### 触发条件

- 用户说"查看风格"、"风格档案"
- 想了解 AI 学到了什么

### 执行步骤

```bash
# 查看风格档案
python {STORY_DIR}/story.py style

# 查看可复用的 prompt 片段
python {STORY_DIR}/story.py style --prompts

# 查看完整风格指南
python {STORY_DIR}/story.py style --full

# 重置风格数据（--force 跳过确认）
python {STORY_DIR}/story.py style --reset [--force]
```

### 风格档案输出

```
============================================================
         风格档案
============================================================

  创建时间：2026-04-08
  学习章节：3 章
  平均修改率：32.5%
  目标修改率：15.0%

------------------------------------------------------------
  风格档案路径：STYLE/profile.json
  Prompt 片段：STYLE/prompts/
------------------------------------------------------------
```

---

## 工作流 9：stats（学习进度统计 + 字数统计）[PROCEDURE]

展示 AI 写作学习进度、修改率趋势，以及实际写作字数统计。

### 触发条件

- 用户说"学习进度"、"修改率"、"统计"、"字数"
- 想了解 AI 学得怎么样了
- 想了解实际写作进度

### 执行步骤

```bash
# 查看完整统计（字数 + 学习）
python {STORY_DIR}/story.py stats

# 仅显示字数统计
python {STORY_DIR}/story.py stats --words

# 仅显示学习进度
python {STORY_DIR}/story.py stats --learning

# 查看修改率趋势图
python {STORY_DIR}/story.py stats --trend

# 导出报告
python {STORY_DIR}/story.py stats --export report.json
```

### 字数统计输出

```
============================================================
              写作字数统计
============================================================

  已完成字数：125,600 字
  目标字数：500,000 字
  草稿字数：8,200 字（未完成）

  总体进度：[██░░░░░░░░] 25.1%
  差距：374,400 字

  章节字数：
  --------------------------------------------------
  卷1 (15章, 125,600字)
    ✓ 第1章  [██████████████] 8,200字
    ✓ 第2章  [█████████████░] 7,800字
    ...

  写作效率：
  --------------------------------------------------
  平均每章：8,373 字
  目标每章：5,000 字
  效率比：167%
```

### 学习进度输出

```
============================================================
             AI 写作学习进度
============================================================

  已学习章节：3 章
  当前修改率：32.5%
  目标修改率：15.0%

  学习进度：[████░░░░░░] 35%

  修改率趋势：
  --------------------------------------------------
  第1章 [████████████░░░░░░░░░░░░░░░░░░░░] 45.0% ☆
  第2章 [██████████░░░░░░░░░░░░░░░░░░░░░░] 38.0% ☆
  第3章 [████████░░░░░░░░░░░░░░░░░░░░░░░] 32.0% ★

  建议：
  --------------------------------------------------
  → 继续学习 2-3 章，修改率将继续下降
```

### 趋势图输出

```
============================================================
             修改率趋势
============================================================

  45.0% |███
  40.0% |   ███
  35.0% |       ████
  30.0% |           ████
  25.0% |
  20.0% |
  15.0% |                   █ target
      ----------------------------------------
             第1章  第2章  第3章

  趋势分析：从 45.0% 到 32.0% (下降 ↓)
```

---

## 工作流 10：update-specs（写作后自动更新设定）[PROCEDURE]

分析章节内容，检测新揭示的角色名、信息，自动更新角色设定文件中的"当前状态"章节。

### 触发条件

- 写完章节后说"更新设定"、"检测新角色"
- 需要更新POV角色的认知状态
- 写作流程最后一步（推荐）

### 执行步骤

```bash
# 分析章节，查看检测到的新设定
python {STORY_DIR}/story.py update-specs 5

# 预览变更，不实际写入
python {STORY_DIR}/story.py update-specs 5 --dry-run

# 同时生成章节摘要
python {STORY_DIR}/story.py update-specs 5 --summary
```

### POV 动态状态系统

**核心概念**：每个POV角色都有独立的认知状态，随剧情推进动态更新。

```
写第N章前:
  读取角色当前状态 → 生成POV约束Prompt → AI写作(受限视角)

写第N章后:
  扫描新揭示信息 → 更新角色状态文件 → 同步到story.json → 供下章使用
```

**状态存储位置**：
- 角色设定文件：`SPECS/characters/{角色名}.md` 中的"当前状态"章节
- JSON快照：`story.json` 中的 `pov_states` 字段（供程序快速读取）

**状态数据结构**：
```json
{
  "pov_states": {
    "林夜": {
      "known_characters": [
        {"name": "苏念", "relationship": "神秘顾客", "source": "学生证", "chapter": "第1章"}
      ],
      "unknown_characters": ["其他客人"],
      "known_info": ["便利店夜间营业", "苏念的手没有温度"],
      "pending_reveals": ["苏念的真实身份", "自己已死的事实"]
    }
  }
}
```

**写作时的POV约束**：
当使用 `story:write N --draft` 生成Prompt时，系统会：
1. 从细纲中提取POV角色
2. 读取该角色的认知状态
3. 在Prompt中注入POV约束：
   - 已知角色：可以直接称呼名字
   - 未知角色：必须用外貌/身份代称（如"那女孩"、"穿校服的学生"）
   - 已掌握信息：可以写出
   - 待揭示信息：禁止提前写出

### 检测内容

| 类型 | 检测方式 | 示例 |
|------|---------|------|
| 新获知角色 | 未知角色名出现在正文中 | 林夜通过学生证知道"苏念" |
| 待揭示项 | 待揭示列表中的关键词出现 | "亡魂"、"已死"等 |
| 新信息 | 启发式检测新事实 | 通过对话或观察获知的信息 |

---

## 工作流 11：recall（章节回顾）[PROCEDURE]

快速查看章节摘要或设定快照，回顾前文剧情和设定状态。

### 触发条件

- 用户说"回顾"、"前面写了什么"、"忘了上几章"
- 写新章节之前想快速看看前面的剧情
- 想看某章结束时所有设定的状态

### 执行步骤

```bash
# 查看单个章节摘要
python {STORY_DIR}/story.py recall 5

# 查看连续章节摘要
python {STORY_DIR}/story.py recall 3-5

# 查看最近 N 章
python {STORY_DIR}/story.py recall --recent 3

# 显示完整摘要（不截断）
python {STORY_DIR}/story.py recall 5 --full

# 查看章节设定快照（人物状态、剧情进度、伏笔等）
python {STORY_DIR}/story.py recall 5 --snapshot
```

### 摘要来源

摘要文件由 `story:update-specs` 命令生成，保存到：
```
OUTLINE/volume-001/summaries/chapter-005-summary.md
```

### 输出示例

```
============================================================
  第5章 摘要
============================================================

  字数: 3,200
  POV: 张三
  日期: 2026-04-08

  本章讲述张三来到青云门山脚，回忆师父临终嘱托，
  决定拜入青云门修行。途中遇见守门弟子李四...
```

---

## 工作流 11.5：snapshot（章节设定快照）[PROCEDURE]

每个章节确认定稿时，对所有设定做一次快照。快照记录该章结束时人物状态、剧情进度、伏笔追踪和已用场景，供后续章节写作和讨论时参考。

### 核心概念

快照不是独立的"记忆"系统，而是**所有设定在该章结束时的 snapshot**。人物卡演进到哪了、世界观认知变了没、伏笔挂在哪、场景用过哪些——全都在快照里。

### 触发条件

- 章节确认定稿后（`story:write N --confirm` 后自动提示）
- 用户说"快照"、"设定状态"、"现在人物什么状态"
- 讨论章节时需要回顾设定

### 执行步骤

```bash
# 为第5章生成设定快照
python {STORY_DIR}/story.py snapshot 5

# 查看第5章快照
python {STORY_DIR}/story.py snapshot 5 --view

# 列出所有快照
python {STORY_DIR}/story.py snapshot --list

# 仅显示 AI 填充 Prompt
python {STORY_DIR}/story.py snapshot 5 --prompt
```

### 快照文件结构

```markdown
# 第 N 章设定快照

## 人物状态
| 角色 | 当前心理/状态 | 对外部看法 | 认知变化（vs 上章）|
|------|-------------|-----------|-------------------|
| 林夜 | 逐渐接受自己已死的事实 | 对苏念产生信任 | 从抗拒到接纳 |

## 剧情进度
- **主线位置**：...
- **本章关键事件**：...
- **下章衔接点**：...

## 伏笔追踪
- [伏笔描述] → 已回收 / 待回收（预计第X章）
- 新增伏笔标注"（新增）"

## 已用场景模式
- 场景模式1（第1章、第3章）
- 场景模式2（第2章）

## 下章开头要点
- 人物位置：
- 情绪状态：
- 悬念/待续：
```

### 快照存储

```
OUTLINE/volume-001/snapshots/
  chapter-001-snapshot.md        # 第1章快照
  chapter-002-snapshot.md        # 第2章快照
  chapter-003-snapshot-prompt.md # 第3章 AI 填充 Prompt
```

### 快照如何被使用

1. **写作 Prompt 注入**：`story:write N --draft` 自动读取前 3 章快照注入 Prompt
2. **回顾查看**：`story:recall N --snapshot` 查看某章快照
3. **讨论参考**：讨论角色/情节时打开对应快照

### 快照生成流程

```
story:write N --confirm
  → 确认定稿
  → 提示：story:snapshot N

story:snapshot N
  → 读取本章正文 + 细纲 + 上章快照
  → 生成 AI 填充 Prompt
  → 保存模板到 snapshots/chapter-N-snapshot.md
  → Agent 填充后更新快照文件

story:write N+1 --draft
  → 读取 snapshots/chapter-(N-2) 到 chapter-N
  → 注入写作 Prompt
```

### 预期效果

- **A2（场景重复）**：写作 Prompt 知道已用场景，避免重复
- **A3（悬念悬置）**：伏笔追踪机制，跨章累积
- **A4（心理过渡）**：人物状态记录，写作时知道角色当前情绪
- **额外价值**：讨论时快速回顾所有设定当前状态

---

## 工作流 12：export（导出小说）[PROCEDURE]

将章节内容导出为 txt 或 docx 格式，方便发送给编辑或发布。

### 触发条件

- 用户说"导出"、"发稿"、"导出 Word"
- 写完想要导出分享

### 执行步骤

```bash
# 导出全部章节（默认 txt）
python {STORY_DIR}/story.py export

# 导出指定范围
python {STORY_DIR}/story.py export 1-10

# 导出单个章节
python {STORY_DIR}/story.py export 5

# 导出为 Word 文档
python {STORY_DIR}/story.py export 1-10 --format docx

# 导出指定卷
python {STORY_DIR}/story.py export --volume 1

# 指定输出文件名
python {STORY_DIR}/story.py export 1-5 -o my-novel-ch1-5.docx
```

### 导出目录

导出的文件保存在 `EXPORT/` 目录下：
```
EXPORT/
  《书名》-ch1-10.txt
  《书名》-volume-001.docx
```

### 格式说明

| 格式 | 说明 | 依赖 |
|------|------|------|
| txt | 纯文本，兼容性最好 | 无 |
| docx | Word 文档，格式丰富 | `pip install python-docx` |

---

## 工作流 13：archive（定稿归档）[PROCEDURE]

章节写作完成后，将正文和相关文件归档，记录变更。

### 触发条件

- 用户说"归档"、"定稿"、"完成这一章"
- 用户说"archive 第N章"

### 执行步骤

#### 第一段：预览（可选）[PROCEDURE]

```bash
python {STORY_DIR}/story.py archive [章节号] --preview
```

展示归档将包含的文件列表和字数统计。

#### 第二段：执行归档 [PROCEDURE]

```bash
python {STORY_DIR}/story.py archive [章节号]
# 或模拟运行：
python {STORY_DIR}/story.py archive [章节号] --dry-run
```

归档会创建以下结构：

```
ARCHIVE/{日期}-chapter-NNN/
  final.md         # 最终版本正文
  tasks.md         # 任务清单（如果有）
  outline.md       # 章节大纲（如果有）
  delta-spec.md    # 变更规格（自动生成）
  .meta.json       # 元数据（章节号/卷号/归档时间/字数/文件列表）
```

#### 第三段：更新进度 [PROCEDURE]

归档完成后自动更新：
- `progress.archived_chapters` 添加章节号
- `book.current_words` 累加本章字数
- 生成 delta-spec.md 记录变更类型（ADDED/MODIFIED/REMOVED）

### AI 辅助

归档后，AI 可以：
1. 生成归档摘要：本章的核心事件和字数
2. 检查进度：当前总字数/目标字数，完成百分比
3. 建议下一步：下一章的大纲是否就绪？是否需要补充设定？

---

## 工作流 14：plan（规划流水线）[MIXED]

卷纲生成与章节拆分，完整的 AI 辅助规划流程。

### 触发条件

- 用户说"生成卷纲"、"拆分章节"、"规划这一卷"
- 用户想用 AI 辅助设计卷结构

### 核心理念

**AI 负责骨架搭建，作者专注血肉填充**。通过"草稿 → 讨论 → 确认"三阶段迭代，确保大纲质量。

### Pipeline 流程

```mermaid
flowchart TD
    A[主线故事] --> B[story:plan --volume 1]
    B --> C[AI 生成卷纲草稿]
    C --> D[story:plan --volume 1 --revise]
    D --> E[作者讨论修改]
    E --> F[story:plan --volume 1 --confirm]
    F --> G[卷 stage: draft → confirmed]
    G --> H[story:plan --chapters 1]
    H --> I[AI 拆分章节]
    I --> J[story:plan --chapters 1 --confirm]
    J --> K[所有章节 stage: outline-draft]
    K --> L[story:outline --draft 1 --all]
    L --> M[AI 批量生成细纲]
    M --> N[story:outline --revise N]
    N --> O[story:outline --confirm N]
    O --> P[stage: outline-confirmed]
    P --> Q[story:write N --draft]
    Q --> R[AI 写正文]
    R --> S[story:write N --revise]
    S --> T[story:write N --confirm]
    T --> U[stage: done]
```

### Stage 状态

| 层级 | Stage 值 | 说明 |
|------|---------|------|
| 卷 | `draft` | 草稿，可修改 |
| 卷 | `confirmed` | 定稿 |
| 章节 | `outline-draft` | 细纲草稿 |
| 章节 | `outline-confirmed` | 细纲定稿 |
| 章节 | `writing` | 正在写正文 |
| 章节 | `review` | 审核中 |
| 章节 | `done` | 定稿完成 |

### 执行步骤

#### 第一段：卷纲生成 [REASONING]

```bash
# 读取主线文件生成卷纲
python {STORY_DIR}/story.py plan --volume 1

# 交互式问答生成卷纲
python {STORY_DIR}/story.py plan --volume 1 --interactive

# 讨论模式修改卷纲
python {STORY_DIR}/story.py plan --volume 1 --revise

# 确认卷纲定稿
python {STORY_DIR}/story.py plan --volume 1 --confirm
```

**交互式问答收集的信息**：
- 核心冲突
- 主角成长弧线
- 核心事件
- 情感基调

#### 第二段：章节拆分 [REASONING]

```bash
# AI 拆分章节列表
python {STORY_DIR}/story.py plan --chapters 1

# 讨论模式修改章节
python {STORY_DIR}/story.py plan --chapters 1 --revise

# 确认章节列表（批量初始化 stage）
python {STORY_DIR}/story.py plan --chapters 1 --confirm
```

**章节拆分输出格式**：
```
| 章节 | POV | 核心内容 | 字数预估 | 情绪基调 |
|------|-----|---------|---------|---------|
| 第1章 | 张三 | 开场：主角出场... | ~1500字 | 平静 |
```

#### 第三段：状态查看 [PROCEDURE]

```bash
# 查看流水线整体状态
python {STORY_DIR}/story.py plan --status

# 查看指定卷状态
python {STORY_DIR}/story.py plan --volume 1 --status
```

### stage 管理

Stage 信息保存在 `story.json` 的 `pipeline` 字段中：

```json
{
  "pipeline": {
    "volumes": {
      "1": { "stage": "confirmed" }
    },
    "chapters": {
      "1": { "stage": "outline-confirmed", "volume": 1 },
      "5": { "stage": "writing", "volume": 1 },
      "10": { "stage": "done", "volume": 1 }
    }
  }
}
```

### 关键设计决策

1. **Prompt 保存**：每次生成都保存 Prompt 到文件，方便复审和复用
2. **批量操作**：`--all` 支持批量生成，如 `story:outline --draft 1 --all`
3. **无感知的命令切换**：每个 `--confirm` 后自动提示下一步
4. **可回退**：确认后仍可通过 `--revise` 退回修改

### AI 辅助要点

生成卷纲时，AI 应该：
1. 读取 `story-concept.md` 或 `story-main.md` 作为主线参考
2. 参考 `story.json` 中的 genre、theme、volume_titles
3. 输出包含起承转合、核心事件、高潮设计、伏笔布局的完整卷纲
4. 明确标注与前后卷的衔接

---

## 工作流 12：status（查看项目状态）[PROCEDURE]

展示小说项目的整体进度和状态。

### 触发条件

- 用户说"进度"、"状态"、"写到哪了"
- 用户提到小说但没有具体指令（兜底行为）

### 执行步骤

```bash
python {STORY_DIR}/story.py status [--json]
```

展示信息包括：
- **基本信息**：书名、类型、目标字数
- **写作进度**：完成百分比（进度条）、章节进度、已归档数
- **设定库**：人物数、世界观条目数
- **存储**：草稿字数、正文字数
- **最近活动**：最近修改的 5 个文件

### AI 辅助

展示状态后，AI 可以根据当前进度给出建议：
- 刚初始化 -> 建议先完善大纲
- 大纲有了但没正文 -> 建议开始写作
- 写到某卷中间 -> 提醒检查伏笔一致性
- 接近目标字数 -> 建议考虑收尾

---

## AI 创作辅助指南

当用户的请求不是明确的命令，而是创作讨论时，AI 按以下原则辅助：

### 文本诊断

对小说文本进行 A/B/C 三维度质量诊断，Agent 直接读取章节正文并输出诊断报告。

**触发条件**：
- 用户说"诊断"、"审查文本"、"AI 味"、"检查问题"
- 用户想审视 AI 生成或 AI+人协作的小说章节

**诊断维度**：

| 维度 | 类型 | 定义 | 修复方式 |
|------|------|------|---------|
| A 类 | Skill/框架问题 | 结构/逻辑/节奏/POV/伏笔断层/因果断裂 | 改规则就有效 |
| B 类 | 纯内容问题 | 人物单薄/冲突缺失/细节不足 | 补充内容 |
| C 类 | AI 味问题 | "像某种"/排比三连/情绪直白宣判 | 调整文风 |

**执行方式**：Agent 直接读取待诊断的章节文件（`CONTENT/volume-001/chapter-NNN.md`），参照 `src/diagnose_rules.md` 中的 A/B/C 检查清单逐项分析，按 `src/diagnose_prompts.md` 的框架输出诊断报告。

**诊断报告格式**：

```markdown
# 《书名》文本诊断报告

## 一、通读印象
（200字以内，主线/人物/节奏/氛围/逻辑印象）

## 二、A 类：Skill / 框架问题
### A1. 🔴 章节信息密度失衡
- 问题描述：...
- 原文引用：Ch2 L17 "..."
- 修复建议：...

## 三、B 类：纯内容问题
...

## 四、C 类：AI 味问题
...

## 五、总结建议
| 优先级 | 问题 | 修复方向 |
|--------|------|---------|
| 🔧 第一 | ... | ... |
```

**诊断完成后**：作者按严重程度迭代修改，Agent 可在下一轮对话中复诊。

### 人物讨论

1. 读取 `SPECS/characters/` 下相关人物文件
2. 基于已有设定讨论角色发展、人物关系、性格一致性
3. 如果讨论产生了新的设定，主动提出更新 SPECS 文件
4. **六层认知是角色的核心**：讨论角色行为时，优先对照其"世界观→态度、价值观→选择、能力→行为范围"

### 情节推演

1. 读取 `OUTLINE/meta.md`（总纲）和对应卷的大纲
2. 在大纲框架内推演情节发展，不要脱离已有结构
3. 推演时标注"伏笔"和"呼应"，提醒用户记录

### 世界观扩展

1. 读取 `SPECS/world/` 下的设定
2. 基于已有规则扩展，确保逻辑自洽
3. 如果需要新规则，建议创建新的世界观文件

### 连贯性检查

检查维度：
- 人物性格是否前后一致
- 时间线是否有矛盾
- 伏笔是否回收
- 称呼/地名是否统一
- 力量体系/世界观规则是否一致

---

## 目录结构速查

```
{项目根}/
  story.json                        # 核心配置（JSON，含 paths 三目录配置）
  SPECS/
    characters/{角色名}.md           # 人物设定
    world/*.md                      # 世界观
    meta/
      story-concept.md              # 故事概念
  OUTLINE/
    meta.md                         # 总大纲
    volume-001.md                     # 卷大纲（每卷一个）
    volume-001/
      chapter-NNN.md                # 章节大纲（每章一个）
      snapshots/                    # 章节设定快照
        chapter-NNN-snapshot.md     # 设定快照
        chapter-NNN-snapshot-prompt.md  # AI 填充 Prompt
      summaries/                    # 章节摘要
        chapter-NNN-summary.md      # 章节摘要

# === 以下三个目录可通过 story.json paths 字段自定义位置 ===

{output_dir}/                       # 最终输出目录（默认：项目根/CONTENT）
  volume-001/
    chapter-NNN.md                  # 正文
    chapter-NNN.tasks.md            # 任务清单

{process_dir}/                      # 过程文件目录（默认：项目根）
  draft/                            # 草稿（AI 生成内容暂存）
  summaries/                        # 章节摘要
  snapshots/                        # 备用快照目录
  proposals/                        # 提案目录
  prompts/                          # 提示词暂存

{output_dir}/export/                # 导出文件
{output_dir}/archive/               # 归档
  {日期}-chapter-NNN/
    final.md                        # 定稿
    outline.md                      # 归档时的大纲
    tasks.md                        # 归档时的任务
    delta-spec.md                   # 变更记录
    .meta.json                      # 归档元数据

STYLE/                              # 风格学习数据（在项目根下）
  profile.json                      # 用户风格档案
  prompts/                          # 可复用的 prompt 片段
    vocabulary.md                   # 词汇偏好
    sentence.md                     # 句式偏好
    pacing.md                       # 节奏偏好
    full_guide.md                   # 完整风格指南
  history/                          # 修改历史记录
    chapter-NNN/
      ai_raw.md                     # AI 原始生成
      human_final.md                # 人的最终版本
      analysis.json                 # 差异分析结果
templates/                          # 写作模板
```

### 三目录设计

story.json 中的 `paths` 字段控制三个主目录的位置：

```json
{
  "paths": {
    "process_dir": "过程文件目录路径（相对或绝对）",
    "output_dir": "最终输出目录路径（相对或绝对）"
  }
}
```

- **project_root**（项目根）：包含 `story.json`、`SPECS/`、`OUTLINE/`、`STYLE/`、`templates/`
- **process_dir**（过程文件目录）：AI 生成的中间产物，如 `draft/`、`summaries/`、`snapshots/`、`proposals/`、`prompts/`
- **output_dir**（最终输出目录）：小说正文 `volume-NNN/`、`export/`、`archive/`

**向后兼容**：若 `story.json` 无 `paths` 字段，所有路径回退到项目根目录（旧项目无需修改即可运行）。

## 边界与防坑

**不要跳过大纲直接写作。** 没有章节大纲就写作，很容易写到一半发现结构崩了。如果用户急着写，至少花 3 分钟列个场景列表。

**归档是单向的。** 一旦归档，正文从 CONTENT/ 移到 ARCHIVE/，不会删除但不会自动同步后续修改。如果用户想修改已归档章节，需要在 ARCHIVE/ 中直接编辑。

**卷号和章节号的计算依赖 `chapters_per_volume`。** 如果中途修改了每卷章节数，已有文件不会自动重新编号。建议在 init 阶段确定好结构，不要频繁调整。

**编码兼容性。** 所有文件使用 UTF-8 编码，输出避免 emoji（用 ASCII 符号替代），兼容 Windows GBK 终端。

**Agent 驱动模式。** 所有含交互输入的命令（init/define/propose/plan/style）均支持 `--non-interactive` 模式：Agent 与用户对话获取信息后，通过完整 CLI 参数调用脚本，脚本不再有 `input()` 阻塞。JSON 参数格式错误时给出清晰提示并退出。

## 多平台 Skill 目录

| 平台 | Skill 安装路径 |
|------|---------------|
| **WorkBuddy** | `~/.workbuddy/skills/my-novel/` |
| **Claude Code** | `~/.claude/skills/my-novel/` |
| **OpenClaw** | `~/.openclaw/skills/my-novel/` |

> `STORY_DIR` = 此 SKILL.md 所在目录。CLI 脚本位于 `{STORY_DIR}/story.py`。
> 调用时使用 `python {STORY_DIR}/story.py <command>` 执行命令。
