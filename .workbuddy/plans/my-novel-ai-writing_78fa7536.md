---
name: my-novel-ai-writing
overview: 为 my-novel skill 添加 AI 写作生成、审核、风格学习功能，形成人机协作写作闭环
todos:
  - id: rebuild-write-module
    content: 重构 src/write.py，添加 AI 生成章节能力
    status: completed
  - id: create-review-module
    content: 新增 src/review.py，实现人机差异对比和审核功能
    status: completed
    dependencies:
      - rebuild-write-module
  - id: create-learn-module
    content: 新增 src/learn.py，实现风格学习引擎（差异分析 + 模式提取）
    status: completed
    dependencies:
      - create-review-module
  - id: create-style-module
    content: 新增 src/style.py，实现风格档案管理和 system prompt 动态生成
    status: completed
    dependencies:
      - create-learn-module
  - id: create-stats-module
    content: 新增 src/stats.py，实现学习进度统计和趋势分析
    status: completed
    dependencies:
      - create-learn-module
  - id: update-story-entry
    content: 更新 story.py 入口，注册新命令
    status: completed
    dependencies:
      - create-review-module
      - create-style-module
  - id: update-skill-docs
    content: 更新 SKILL.md 文档，添加新命令说明和工作流
    status: completed
    dependencies:
      - update-story-entry
---

## 产品定位

将 my-novel 从「写作管理工具」升级为「AI 协作写作伙伴」，实现：

**核心理念**：Agent 写 -> 人改 -> Agent 学 -> 减少修改

**核心价值**：

1. **Agent 写作框架**：提供结构化的 prompt 模板、上下文管理
2. **人审核修改**：提供差异对比工具，人工调整 Agent 输出
3. **学习进化**：自动分析人的修改痕迹，提取写作风格偏好
4. **渐进自主**：生成风格 prompt 片段给 Agent，减少修改量

---

## 核心功能

### 1. Agent 写作模块（story:write 增强）

- 读取章节大纲、人物设定、上章结尾
- 生成结构化的 **Agent Prompt 模板**（不是直接调用 LLM）
- 支持分场景 prompt 生成
- Prompt 中包含风格指南片段

### 2. 人机协作审核

- Agent 生成后，用户可导入 AI 生成的文字
- 对比 AI 生成版 vs 用户修改版（diff）
- 记录修改操作（新增/删除/替换）
- 计算修改率

### 3. 风格学习引擎

- 归档时对比 AI 生成版 vs 人修改版
- 提取修改模式：常用词汇替换、句式偏好、节奏调整
- 生成 `STYLE/prompts/` 下的可复用 prompt 片段
- 供 Agent 下次写作时注入

### 4. 学习进度追踪

- 统计每章修改量（新增字/删除字/替换次数）
- 计算"修改占比"作为 Agent 质量指标
- 展示学习曲线（修改量趋势）
- 给出下一步建议

---

## 数据流设计

```
[大纲] + [设定] + [上章结尾] + [风格 Prompt]
         ↓
      [生成 Agent Prompt 模板]
         ↓
      [Agent 收到 Prompt，生成内容]
         ↓
      [用户审核] → [修改稿]
         ↓
      [差异分析] → [学习记录]
         ↓
      [提取模式] → [更新风格 Prompt]
```

---

## 用户交互流程

1. `story:write 5` → 生成 Agent 写作 Prompt
2. Agent 收到 Prompt → 生成内容
3. 用户导入 AI 内容 → 阅读并修改
4. `story:review 5` → 查看差异分析
5. `story:learn 5` → 从修改中学习风格
6. `story:style` → 查看学习到的风格
7. `story:stats` → 查看修改占比和学习进度

---

## 技术选型

### 架构原则

- **不调用 LLM**：只生成 prompt 模板和做差异分析
- **Agent 负责生成**：prompt 格式优化由 skill 处理
- **零外部依赖**：纯 Python + difflib

### 差异分析

- **库**：Python difflib（标准库）
- **指标**：
- 修改字数比 = 人修改字数 / 总字数
- 替换率 = 替换次数 / 生成段落数
- 高频替换词表

### 风格学习

- **方案**：提取用户偏好，生成 prompt 片段
- **输出**：可注入 Agent Prompt 的 Markdown 片段
- **粒度**：词汇替换、句式偏好、节奏偏好

### 架构设计

```
story.py (CLI 入口)
├── src/
│   ├── write.py        # [重构] Agent Prompt 生成
│   ├── review.py       # [NEW] 差异对比工具
│   ├── learn.py       # [NEW] 风格模式提取
│   ├── style.py       # [NEW] 风格 Prompt 管理
│   └── stats.py       # [NEW] 学习统计
└── SKILL.md          # [更新] 新命令文档
```

### 目录结构变更

```
{项目根}/
  story.json              # 新增 learning 字段
  STYLE/                  # [NEW] 风格学习数据
  ├── profile.json        # 用户风格档案
  ├── prompts/            # [NEW] 可复用的 prompt 片段
  │   ├── vocabulary.md    # 词汇偏好
  │   ├── sentence.md     # 句式偏好
  │   └── pacing.md       # 节奏偏好
  └── history/            # 修改历史记录
```

### API 设计

**story:write 增强**

```
python story.py write 5              # 生成 Agent Prompt
python story.py write 5 --show       # 显示完整 Prompt
python story.py write 5 --prompt     # 仅显示 Prompt 部分
python story.py write 5 --context     # 仅显示上下文部分
```

**story:review 差异对比**

```
python story.py review 5             # 对比差异
python story.py review 5 --ai <文本>  # 导入 AI 生成内容
python story.py review 5 --stat       # 仅显示统计
```

**story:learn 风格学习**

```
python story.py learn                # 学习所有修改
python story.py learn 5             # 学习第5章
python story.py learn --force       # 强制重新学习
```

**story:style 风格**

```
python story.py style                # 查看当前风格档案
python story.py style --prompts     # 查看可复用的 prompt 片段
python story.py style --reset       # 重置风格
```

**story:stats 统计**

```
python story.py stats               # 查看学习统计
python story.py stats --trend       # 查看趋势
python story.py stats --export      # 导出报告
```

---

## 实现细节

### Agent Prompt 模板结构

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

## 写作要求

- 字数：约 3000 字
- POV：必须保持张三视角
- 禁止：[STYLE/avoid.md 中的内容]
```

### 差异分析输出示例

```
═══════════════════════════════════════
        第5章 差异分析
═══════════════════════════════════════

  AI 生成字数：3200
  用户修改字数：480
  修改占比：15.0%

───────────────────────────────────────

  统计：
    新增：120 字
    删除：80 字
    替换：8 处

───────────────────────────────────────

  高频替换：
    "非常" → "极其" (3次)
    "他慢慢地" → "他" (2次)
    "说道" → "开口" (2次)

───────────────────────────────────────

  句式偏好：
    - 偏好短句，删除冗余修饰
    - 减少被动语态

═══════════════════════════════════════
```

### 风格 Prompt 片段示例

```markdown
<!-- STYLE/prompts/vocabulary.md -->

## 词汇偏好

### 替换规则
- "非常" → "极其" / "格外"
- "慢慢地" → 删除或替换为具体动作
- "说道" → "开口" / "应道" / 直接用引号

### 避免词汇
- 过度使用的形容词（如"美丽的"、"帅气的"）
- 陈词滥调（如"电光火石间"）
```

---

## 实施计划

### Phase 1: 基础框架

1. 重构 `src/write.py` - 生成 Agent Prompt
2. 新增 `src/review.py` - 差异对比

### Phase 2: 学习闭环

3. 新增 `src/learn.py` - 风格模式提取
4. 新增 `src/style.py` - 风格 Prompt 管理

### Phase 3: 追踪与文档

5. 新增 `src/stats.py` - 学习统计
6. 更新 `story.py` - 注册新命令
7. 更新 `SKILL.md` - 新命令文档

---

## 依赖关系

```
rebuild-write-module
       ↓
create-review-module
       ↓
create-learn-module ──→ create-style-module
       ↓                      ↓
create-stats-module ←─────────┘
       ↓
update-story-entry
       ↓
update-skill-docs
```