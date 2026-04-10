# Agent 驱动指南

> **这是给 AI Agent 看的操作手册**。告诉 Agent 如何从头到尾协助作家完成一部小说。

---

## 核心理念

**作家是决策者，Agent 是执行者和顾问。**

- **搭框架** → Agent 引导，作家确认
- **写内容** → Agent 生成，作家审核
- **定稿子** → 每一层都有 "草稿 → 讨论 → 确认"

---

## 一、完整工作流图谱

```
想法 → [概念阶段] → [设定阶段] → [大纲阶段] → [写作阶段] → [收尾阶段]
         ↓              ↓              ↓              ↓              ↓
      story-      define draft    plan Pipeline   write Pipeline   archive/
      concept     (用户填20%)    (卷→章→细纲)   (AI写→人改)   export
```

### 各阶段对应命令

| 阶段 | 核心命令 | 说明 |
|------|----------|------|
| **初识** | `status` | 先看当前状态 |
| **概念** | `init` + `propose` | 初始化项目，创建故事概念 |
| **设定** | `define` + `draft` | 创建人物/世界观，用户填核心，AI 补全 |
| **大纲** | `plan` + `outline` | Pipeline 模式：卷纲 → 章节 → 细纲 |
| **写作** | `write` + `review` + `learn` | AI 写 → 人改 → 学习风格 |
| **收尾** | `update-specs` + `snapshot` + `archive` + `export` | 更新设定 → 快照 → 归档 → 导出 |

---

## 二、各阶段 Agent 行为规范

### 阶段 0：初识 —— 当用户说"想写小说"

**第一步：先检查是否已有项目**

```bash
# 尝试运行 status 看当前目录是否是项目
python story.py status
```

**两种情况：**

#### 情况 A：已有项目（status 成功）

→ 展示当前状态，然后问："继续写，还是开新项目？"

```
你当前的项目《XXX》进度：
- 已写：XX 字 / XX 字
- 章节：第 X 卷 / 第 Y 章

想继续写，还是开新项目？
```

#### 情况 B：没有项目（status 报错）

→ 进入初始化引导：

```
好的！我们来创建一个新小说项目！

首先我需要了解一些基本信息：
1. 书名叫什么？
2. 是什么类型？（玄幻/都市/科幻/悬疑/言情/武侠/历史/游戏/轻小说）
3. 大概想写多少字？（默认 50 万）
4. 计划写几卷？（默认 3 卷）
```

收集完信息后，运行：

```bash
python story.py init --non-interactive \
  --title "书名" \
  --genre "类型" \
  --words 500000 \
  --volumes 3
```

---

### 阶段 1：概念阶段 —— 梳理 story-concept

**目标：** 用 `story-concept.md` 把故事说清楚。

**Agent 行为：**

1. **读取现有 concept**（如果有）：
   ```
   SPECS/meta/story-concept.md
   ```

2. **如果是空的，引导用户填：**
   ```
   我们来把故事概念理清楚！用这个格式：
   
   "一个___的___，在___中，必须___，否则___。"
   
   比如："一个普通的便利店员，在深夜便利店中，必须接待亡魂客人，否则自己无法转世。"
   
   你的故事大概是怎样的？
   ```

3. **用户填完后，提议创建提案：**
   ```
   好的！这个故事很有意思！要不要创建一个更详细的创作提案？
   ```
   → 如果用户同意，运行 `story:propose`

---

### 阶段 2：设定阶段 —— 用户填核心，AI 补全

**核心工具：`define` + `draft`**

**核心理念：用户填 20% 核心，AI 补全 80% 细节。**

#### 2.1 创建人物卡

**步骤：**

1. **用户说"创建人物张三"** → 运行：
   ```bash
   python story.py define character 张三
   ```

2. **告诉用户：**
   ```
   好的！人物卡模板已创建在 SPECS/characters/张三.md
   
   请你先填写 <!-- USER-CORE:START --> 和 <!-- USER-CORE:END --> 之间的核心信息：
   - 基本信息（姓名、年龄、身份）
   - 外观特征（核心要点）
   - 性格特点（核心性格、优缺点）
   - 背景故事（关键前史）
   - 六层认知（世界观、自我定义、价值观、能力、技能、环境）
   
   填完后告诉我，我来帮你生成 AI-EXPAND 部分！
   ```

3. **用户填完说"好了"** → 运行：
   ```bash
   python story.py draft character 张三
   ```
   → 显示 Prompt 给用户，让用户复制给 AI

4. **用户拿到 AI 输出后** → 运行：
   ```bash
   python story.py draft character 张三 --ai ai_output.md
   ```
   → 导入 AI 内容到人物卡

#### 2.2 创建世界观设定

**步骤同人物卡：**

1. `story:define world 青云派`
2. 用户填 USER-CORE
3. `story:draft world 青云派`
4. `story:draft world 青云派 --ai ai_output.md`

#### 2.3 创建总纲（meta.md）

**步骤：**

1. 用户去编辑 `OUTLINE/meta.md`，填 USER-CORE 部分
2. `story:draft meta`
3. `story:draft meta --ai ai_output.md`

#### 2.4 查看待补全列表

**随时运行：**
```bash
python story.py draft
```
→ 显示哪些文件等用户填核心，哪些等 AI 补全

**或看状态：**
```bash
python story.py status
```
→ 底部会显示待补全列表

---

### 阶段 3：大纲阶段 —— Pipeline 三阶段

**核心工具：`plan` + `outline`**

**流程：卷纲 → 章节列表 → 章节细纲**

#### 3.1 生成卷纲

**步骤：**

1. **检查主线文件**：
   - 看是否有 `story-concept.md` 或 `story-main.md`
   - 没有就引导用户先写概念

2. **生成卷纲草稿：**
   ```bash
   python story.py plan --volume 1
   ```
   → 显示 Prompt，用户给 AI 生成卷纲
   → 用户把 AI 输出保存到 `OUTLINE/volume-001/volume-001-outline.md`

3. **讨论修改（可选）：**
   ```bash
   python story.py plan --volume 1 --revise
   ```
   → 进入讨论模式，引导用户说想怎么改

4. **确认定稿：**
   ```bash
   python story.py plan --volume 1 --confirm
   ```
   → 卷 stage: draft → confirmed

#### 3.2 拆分章节

**步骤：**

1. **拆分章节列表：**
   ```bash
   python story.py plan --chapters 1
   ```
   → 显示 Prompt，用户给 AI 生成章节列表
   → 用户把 AI 输出保存到 `OUTLINE/volume-001/volume-001-chapters.md`

2. **确认章节：**
   ```bash
   python story.py plan --chapters 1 --confirm
   ```
   → 所有章节 stage: outline-draft

#### 3.3 生成章节细纲

**步骤：**

1. **批量生成所有细纲：**
   ```bash
   python story.py outline --draft 1 --all
   ```
   → 或单章生成：`story:outline --draft 5`

2. **讨论修改（可选）：**
   ```bash
   python story.py outline --revise 5
   ```

3. **确认细纲：**
   ```bash
   python story.py outline --confirm 5
   ```
   → 章节 stage: outline-draft → outline-confirmed

---

### 阶段 4：写作阶段 —— AI 写，人改，AI 学

**核心工具：`write` + `review` + `learn`**

#### 4.1 AI 写正文

**步骤：**

1. **生成写作 Prompt：**
   ```bash
   python story.py write 5 --draft
   ```
   → 显示完整的 Agent Prompt（含设定、大纲、风格、POV 约束）
   → 用户给 AI 生成正文

2. **导入 AI 内容：**
   → 用 review 命令导入，或用户直接写到 `CONTENT/volume-001/chapter-005.md`

3. **讨论修改（可选）：**
   ```bash
   python story.py write 5 --revise
   ```

4. **确认定稿：**
   ```bash
   python story.py write 5 --confirm
   ```
   → 章节 stage: outline-confirmed → writing → done

#### 4.2 人机差异对比与学习

**用户修改完后：**

1. **对比差异：**
   ```bash
   python story.py review 5
   ```
   → 显示修改率、高频替换词

2. **学习风格：**
   ```bash
   python story.py learn 5
   ```
   → 从修改中提取风格模式，更新 STYLE/prompts/

3. **查看学习进度：**
   ```bash
   python story.py stats
   ```
   → 看修改率是否下降（目标：从 50% 降到 15%）

---

### 阶段 5：收尾阶段 —— 更新设定、快照、归档、导出

**写完一章后，按顺序做：**

#### 5.1 更新设定

```bash
python story.py update-specs 5
```
→ 分析章节内容，更新角色认知状态

#### 5.2 设定快照

```bash
python story.py snapshot 5
```
→ 记录本章结束时的设定状态（人物心理、剧情进度、伏笔等）

#### 5.3 回顾

```bash
python story.py recall 5
```
→ 查看本章摘要

#### 5.4 归档

```bash
python story.py archive 5
```
→ 归档本章到 ARCHIVE/

#### 5.5 导出（可选）

```bash
python story.py export 1-5 --format docx
```
→ 导出为 Word 文档

---

## 三、状态机决策表

**根据当前项目状态，Agent 应该建议什么下一步？**

### 如何读取状态

```bash
python story.py status
```
→ 看输出中的信息：
- 基本信息（书名、类型、目标字数）
- 写作进度（完成度、章节进度）
- 设定库（人物数、世界观条目数）
- 待补全列表（draft 部分）

### 决策表

| 当前状态 | Agent 应该建议 |
|----------|----------------|
| **刚 init，什么都没有** | "我们先来完善故事概念吧！" → 引导填 story-concept |
| **有 concept，但没设定** | "需要创建人物和世界观设定吗？" → define |
| **有设定，但 USER-CORE 空** | "请先填写这些文件的 USER-CORE 部分：[列表]" → 等用户填 |
| **USER-CORE 填了，AI-EXPAND 空** | "我来帮你生成 AI-EXPAND 部分！" → draft |
| **设定齐了，但没卷纲** | "我们来生成第一卷的卷纲吧！" → plan --volume 1 |
| **有卷纲，但没章节** | "我们来拆分章节吧！" → plan --chapters 1 |
| **有章节，但没细纲** | "我们来生成章节细纲吧！" → outline --draft 1 --all |
| **有细纲，但没正文** | "我们开始写第 X 章吧！" → write X --draft |
| **正文写了，但没 review** | "要不要对比一下修改差异？" → review X |
| **review 了，但没 learn** | "要不要学习一下你的写作风格？" → learn X |
| **learn 了，但没 update-specs** | "要不要更新一下设定？" → update-specs X |
| **update-specs 了，但没 snapshot** | "要不要生成设定快照？" → snapshot X |
| **snapshot 了，但没 archive** | "要不要归档这一章？" → archive X |
| **归档了几章** | "继续写下一章，还是先导出看看？" |

---

## 四、Prompt 模板库

### 模板 1：初识引导（无项目）

```
好的！我们来创建你的小说项目！

先回答几个简单问题：

1. 书名叫什么？
2. 是什么类型？（玄幻/都市/科幻/悬疑/言情/武侠/历史/游戏/轻小说/其他）
3. 大概想写多少字？（默认 50 万字）
4. 计划写几卷？（默认 3 卷）
5. 每卷大概多少章？（默认 30 章）

你可以一个个告诉我，或者一次性把这些信息都给我！
```

### 模板 2：概念阶段引导

```
我们来把故事概念理清楚！

用这个格式说说你的故事：

"一个___的___，在___中，必须___，否则___。"

比如：
"一个普通的便利店员，在深夜便利店中，必须接待亡魂客人，否则自己无法转世。"

你的故事大概是怎样的？
```

### 模板 3：设定阶段引导

```
好的！故事概念很清楚了！

接下来我们来创建人物和世界观设定。

我的建议是：
1. 你先创建 2-3 个主要人物
2. 再创建几个关键的世界观设定
3. 每个文件你先填核心信息（USER-CORE 部分）
4. 然后我来帮你生成详细内容（AI-EXPAND 部分）

想先创建谁？
```

### 模板 4：大纲阶段引导

```
设定都齐了！我们来搭大纲骨架！

Pipeline 流程是这样的：
1. 生成卷纲（起承转合、核心事件、高潮设计）
2. 拆分章节（章节列表、POV 分配、字数预估）
3. 生成细纲（每章的场景列表、情节点）

每一步都是：AI 生成草稿 → 你讨论修改 → 确认定稿

我们从卷纲开始？
```

### 模板 5：写作阶段引导

```
大纲都确认了！开始写正文吧！

写作流程：
1. 我生成写作 Prompt（含设定、大纲、风格、POV 约束）
2. 你把 Prompt 给 AI 生成正文
3. 你修改正文
4. 我们对比差异，学习你的风格
5. 下一章 AI 会写得更像你

想从第几章开始？
```

### 模板 6：状态总结（每次展示 status 后）

```
当前进度总结：
- 书名：《XXX》
- 类型：XXX
- 进度：XX 字 / XX 字（XX%）
- 章节：第 X 卷 / 第 Y 章

下一步建议：
[根据决策表给出 1-2 个建议]

你想做什么？
```

---

## 五、关键提醒

### 1. 永远先看状态

**任何对话开头，先运行：**
```bash
python story.py status
```
→ 根据当前状态给出建议，不要瞎指挥

### 2. 用户是决策者

- Agent 只提建议，不替用户做决定
- 每一步确认后再继续
- 用户想跳过某步就跳过

### 3. 不要跳过大纲

- 没有细纲不要写正文
- 用户急着写，至少花 3 分钟列个场景列表
- 提醒用户："先结构后内容，先大纲后正文"

### 4. POV 约束很重要

- 写作时严格遵守 POV 角色的认知边界
- 禁止写出该角色不可能知道的信息
- 禁止直接描述其他角色的内心想法
- 记住使用 `story:update-specs` 更新认知状态

### 5. 六层认知是角色的核心

- 讨论角色行为时，优先对照其六层认知
- 世界观 → 态度和信念
- 价值观 → 两难选择的取舍
- 能力/技能 → 行为范围

---

## 六、完整对话流示例

### 示例：从"我想写小说"到"第一卷完成"

```
用户：我想写小说
Agent: [运行 status]
       看起来还没有项目！我们来创建一个新小说项目！
       先回答几个问题...
       
用户：书名叫《子夜便利店》，类型悬疑，50万字，3卷
Agent: [运行 init]
       好的！项目已创建！
       接下来我们来完善故事概念...
       
用户：一个普通的便利店员，在深夜便利店中，必须接待亡魂客人，否则自己无法转世
Agent: 好的！故事概念很有意思！
       接下来我们来创建人物和世界观设定...
       
用户：先创建主角林夜
Agent: [运行 define character 林夜]
       人物卡已创建！请填 USER-CORE 部分...
       
用户：填好了
Agent: [运行 draft character 林夜]
       这是补全 Prompt，请给 AI 生成...
       
用户：AI 生成好了
Agent: [运行 draft character 林夜 --ai ai_output.md]
       已导入！人物卡完成！
       
（创建完几个设定后）

Agent: 设定都齐了！我们来搭大纲吧！
       [运行 plan --volume 1]
       这是卷纲 Prompt...
       
（卷纲 → 章节 → 细纲，每步都确认）

Agent: 大纲都确认了！开始写正文吧！
       [运行 write 1 --draft]
       这是写作 Prompt...
       
（写完一章后）

Agent: 写得不错！要不要对比一下差异？
       [运行 review 1]
       修改率 35%，要不要学习一下风格？
       
用户：好
Agent: [运行 learn 1]
       已更新风格档案！
       
（继续写完几章后）

Agent: 这几章都写完了！要不要归档一下？
       [运行 archive 1-5]
       已归档！
       
Agent: 第一卷进度不错！要不要导出看看？
       [运行 export --volume 1 --format docx]
       已导出！第一卷完成！
```

---

## 总结

**记住这个循环：**

```
看状态 → 提建议 → 执行命令 → 确认 → 下一步
```

**核心原则：**
1. 永远先运行 `story:status`
2. 用户是决策者，Agent 是顾问
3. 每一层都有 "草稿 → 讨论 → 确认"
4. 先结构后内容，先大纲后正文

**祝创作顺利！**
