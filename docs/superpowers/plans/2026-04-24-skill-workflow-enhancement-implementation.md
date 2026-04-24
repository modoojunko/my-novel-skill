# SKILL.md Agent 操作规范完善实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 更新 SKILL.md Phase 1/3 流程 + 命令参考表补充 github 命令说明。

**Architecture:** 仅文档修改，无代码改动。

**Tech Stack:** 仅 markdown 文档

---

## Task 1: 更新 SKILL.md Phase 1 和 Phase 3

**Files:**
- Modify: `SKILL.md:40-52`（Phase 2/3 部分）

- [ ] **Step 1: 找到 Phase 1 位置**

在 SKILL.md 中找到（约第 40-46 行）：
```
【阶段 1：初始化】
story init → story collect core → story collect protagonist → story world basic
```

替换为：
```
【阶段 1：初始化】
story init → story collect core → story world basic → 用户确认 story.yaml

其中：
- collect core: 收集小说名、故事主线、核心设定
- world basic: 世界基础设定（可在 Phase 3 按需扩展）
- 用户确认: Agent 展示 story.yaml 内容，用户确认后才进入 Phase 2
```

- [ ] **Step 2: 找到 Phase 3 位置**

在 SKILL.md 中找到（约第 47-50 行）：
```
【阶段 3：每章写作循环】
（可选）story character update → story write N --prompt → 子 Agent 写正文 → story verify N → story archive N
```

替换为：
```
【阶段 3：每章写作循环】
1. story write N --prompt     生成提示词
2. 子 Agent 写正文             按提示词写第 N 章
3. story verify N              验证章节是否符合大纲
4. 展示验证报告                Agent 展示 verify 结果，告知用户查阅文档
5. 用户确认                    用户自行判断验证结果
6. story archive N             归档（如用户确认通过）
（可选）story character update  更新角色认知

验证结果处理：
- verify 通过 → 展示报告 → 用户确认 → archive
- verify 失败 → 展示问题 → 用户决定处理方式（重写/修改大纲/强制归档）
```

- [ ] **Step 3: 找到命令参考表中的 github 行**

在 SKILL.md 中找到命令参考表，确认 `story github` 是否已有说明。如果缺失，找到合适位置插入：
```
| `story github <action>` | GitHub Issue 管理（list/view/create） | 查看或创建工具问题 |
```

- [ ] **Step 4: 提交**

```bash
git add SKILL.md
git commit -m "docs: SKILL.md Phase 1/3 流程完善，添加用户确认环节"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## 验证清单

- [ ] Phase 1 包含：init → collect core → world basic → 用户确认 story.yaml
- [ ] Phase 3 包含：verify 后展示报告 + 用户确认环节
- [ ] 命令参考表包含 github 命令说明
