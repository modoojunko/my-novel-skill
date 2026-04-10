# 各阶段 Agent 行为规范

## 阶段 0：初识 —— 当用户说"想写小说"

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

## 阶段 1：概念阶段 —— 梳理 story-concept

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

## 阶段 2：设定阶段 —— 用户填核心，AI 补全

**核心工具：`define` + `draft`**

**核心理念：用户填 20% 核心，AI 补全 80% 细节。**

### 2.1 创建人物卡

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

### 2.2 创建世界观设定

**步骤同人物卡：**

1. `story:define world 青云派`
2. 用户填 USER-CORE
3. `story:draft world 青云派`
4. `story:draft world 青云派 --ai ai_output.md`

### 2.3 创建总纲（meta.md）

**步骤：**

1. 用户去编辑 `OUTLINE/meta.md`，填 USER-CORE 部分
2. `story:draft meta`
3. `story:draft meta --ai ai_output.md`

### 2.4 查看待补全列表

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

## 阶段 3：大纲阶段 —— Pipeline 三阶段

**核心工具：`plan` + `outline`**

**流程：卷纲 → 章节列表 → 章节细纲**

### 3.1 生成卷纲

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

### 3.2 拆分章节

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

### 3.3 生成章节细纲

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

## 阶段 4：写作阶段 —— AI 写，人改，AI 学

**核心工具：`write` + `review` + `learn`**

### 4.1 AI 写正文

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

### 4.2 人机差异对比与学习

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

## 阶段 5：收尾阶段 —— 更新设定、快照、归档、导出

**写完一章后，按顺序做：**

### 5.1 更新设定

```bash
python story.py update-specs 5
```
→ 分析章节内容，更新角色认知状态

### 5.2 设定快照

```bash
python story.py snapshot 5
```
→ 记录本章结束时的设定状态（人物心理、剧情进度、伏笔等）

### 5.3 回顾

```bash
python story.py recall 5
```
→ 查看本章摘要

### 5.4 归档

```bash
python story.py archive 5
```
→ 归档本章到 ARCHIVE/

### 5.5 导出（可选）

```bash
python story.py export 1-5 --format docx
```
→ 导出为 Word 文档
