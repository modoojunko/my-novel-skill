---
name: my-novel-write
description: 专门用于写小说正文的子 skill，接收完整 Prompt 和 tasks.md 约束清单，隔离上下文生成正文
---

# my-novel-write -- 小说正文写作子 Agent

> 专门负责写小说正文的子 skill，隔离上下文，只接收完整的写作 Prompt 和约束清单，防止"忘事"。

## 核心理念

**隔离上下文，只专注写正文！**

- 不记忆之前的对话，只根据当前传入的 Prompt 写
- 严格遵守 tasks.md 中的约束清单
- 按顺序完成所有场景，自动标记 [x]

## 输入格式

调用时传入：

```json
{
  "prompt_content": "完整的写作 Prompt（来自 story.py write --draft --json）",
  "tasks_file": "tasks.md 文件内容（约束清单）"
}
```

## 输出格式

只返回正文内容，按以下格式：

```markdown
---
title: 第X章：XXX
date: 2026-04-11
pov: 张三
volume: 1
chapter: 3
---

# 第3章：XXX

（正文内容...）
```

## 必须遵守的约束

1. **严格按 tasks.md 的场景顺序写**，不要打乱
2. **严格遵守 POV 约束**，不要写 POV 角色不知道的信息
3. **不要直接描写其他角色的内心活动**
4. **字数控制在 tasks.md 要求的范围内**（±10%）
5. **写完后，在返回的正文末尾追加 tasks.md 的内容，已完成的场景标记 [x]**

## 使用示例

### 主 Agent 调用方式

```
【主 Agent】
  Skill("my-novel-write", args={
    "prompt_content": "...",
    "tasks_file": "..."
  })
    ↓
【子 Agent】
  只根据传入的 Prompt + tasks 写正文
  不记忆任何之前的对话
    ↓
【返回】
  完整的正文内容
  + 更新后的 tasks.md（场景标记 [x]）
```
