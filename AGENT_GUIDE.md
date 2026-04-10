# Agent 驱动指南

> **这是给 AI Agent 看的操作手册**。告诉 Agent 如何从头到尾协助作家完成一部小说。

---

## 📂 指南结构

本文档已拆分为模块化文件，按需加载：

| 文件 | 内容 | 何时加载 |
|------|------|---------|
| **AGENT_GUIDE.md**（本文件）| 核心理念 + 导航索引 | **总是加载** |
| [docs/agent-guide/01-workflow.md](docs/agent-guide/01-workflow.md) | 完整工作流图谱 + 各阶段 Agent 行为规范 | 初识用户 / 进入新阶段时 |
| [docs/agent-guide/02-decision-table.md](docs/agent-guide/02-decision-table.md) | 状态机决策表 + 下一步建议 | 运行 `story:status` 后 |
| [docs/agent-guide/03-prompt-templates.md](docs/agent-guide/03-prompt-templates.md) | 对话模板库 | 需要引导用户时 |
| [docs/agent-guide/04-json-mode.md](docs/agent-guide/04-json-mode.md) | **JSON 模式使用详解（核心！）** | 需要执行命令生成内容时 |
| [docs/agent-guide/05-examples.md](docs/agent-guide/05-examples.md) | 完整对话流示例 | 需要参考完整流程时 |

---

## 核心理念

**作家是决策者，Agent 是执行者和顾问。**

- **搭框架** → Agent 引导，作家确认
- **写内容** → Agent 生成，作家审核
- **定稿子** → 每一层都有 "草稿 → 讨论 → 确认"

---

## 一、完整工作流图谱（速览）

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

## 二、关键提醒（必读）

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

## 三、快速导航

### 常见场景

| 用户说 | 加载文件 |
|--------|---------|
| "我想写小说" | [01-workflow.md](docs/agent-guide/01-workflow.md) 阶段 0 |
| "帮我生成卷纲" | [01-workflow.md](docs/agent-guide/01-workflow.md) 阶段 3 |
| "帮我写第五章" | [04-json-mode.md](docs/agent-guide/04-json-mode.md)（核心！） |
| "下一步做什么？" | [02-decision-table.md](docs/agent-guide/02-decision-table.md) |
| "给我个例子" | [05-examples.md](docs/agent-guide/05-examples.md) |

### 核心循环

**记住这个循环：**
```
看状态 → 提建议 → 执行命令 --json → 直接生成 → 自动导入 → 下一步
```

**核心原则：**
1. 永远先运行 `story:status`
2. 用户是决策者，Agent 是执行者
3. **你自己就是 AI！** 不需要让用户复制 prompt 给另一个 AI
4. 每一层都有 "草稿 → 讨论 → 确认"
5. 先结构后内容，先大纲后正文

---

**祝创作顺利！** 🎉
