# Skill 工作流与章节大纲 Schema 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 SKILL.md Phase 2 添加完整 schema 示例，并修复 chapter_summaries key 类型查找 bug。

**Architecture:** 两个独立改动：SKILL.md 文档更新 + prompt.py 一行代码修复。

**Tech Stack:** Python 3.8+，仅标准库

---

## Task 1: 修复 prompt.py chapter_summaries key 类型查找 bug

**Files:**
- Modify: `src_v2/prompt.py:722`

- [ ] **Step 1: 修复 chapter_summaries 查找**

将 `src_v2/prompt.py:722`：
```python
ch_summary = chapter_summaries.get(str(chapter_in_volume))
```
改为：
```python
ch_summary = chapter_summaries.get(str(chapter_in_volume)) or chapter_summaries.get(chapter_in_volume)
```

- [ ] **Step 2: 验证语法**

Run: `python3 -c "import ast; ast.parse(open('src_v2/prompt.py').read()); print('Syntax OK')"`

- [ ] **Step 3: 提交**

```bash
git add src_v2/prompt.py
git commit -m "fix: prompt.py chapter_summaries 同时尝试 string 和 int key"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 2: 更新 SKILL.md Phase 2 添加 Schema 示例

**Files:**
- Modify: `SKILL.md:40-52`

- [ ] **Step 1: 找到 Phase 2 的位置**

在 SKILL.md 中找到：
```
【阶段 2：每卷开始前】
直接编辑 story.yaml 规划卷大纲和章节大纲
```

- [ ] **Step 2: 在 SKILL.md 末尾添加附录**

在 SKILL.md 末尾（在 `## 📁 目录结构` 章节之后）添加：

```markdown
## 附录 A：story.yaml 大纲 Schema

### 卷大纲格式（写入 `outlines.volumes.{n}`）

```yaml
outlines:
  volumes:
    "2":
      title: "第2卷标题"
      theme: "本卷主题"
      structure:
        opening: "开场描述"
        development: "发展描述"
        climax: "高潮描述"
        ending: "结局描述"
      chapter_summaries:
        "1": "第1章一句话概要"
        "2": "第2章一句话概要"
        "12": "第12章一句话概要"
```

### 章节大纲格式（写入 `outlines.chapters."{vol}-{ch}"`）

```yaml
outlines:
  chapters:
    "2-12":              # "卷-章" 格式的 key
      summary: "第12章详细概要（300-500字）"
      key_scenes:
        - "场景1: 地点+POV+关键动作"
        - "场景2: ..."
      chapter_info:
        number: 12
        title: "第12章标题"
        pov: "林悦"
```

### 数据层级说明

- `outlines.volumes.{n}.chapter_summaries.{ch}` — 每卷创建时的一句话概要，**必须提供**
- `outlines.chapters."{vol}-{ch}"` — 完整章节大纲（可选），推荐提供让 L0 更丰富

当 `outlines.chapters` 有数据时，`story write N --prompt` 显示完整章节大纲。
当 `outlines.chapters` 无数据时，回退到 `chapter_summaries`（一句话概要）。
```

- [ ] **Step 3: 更新 Phase 2 引用附录**

将 Phase 2 段落改为：
```markdown
【阶段 2：每卷开始前】
直接编辑 story.yaml 规划卷大纲和章节大纲。详见"附录 A：story.yaml 大纲 Schema"。
```

- [ ] **Step 4: 提交**

```bash
git add SKILL.md
git commit -m "docs: SKILL.md Phase 2 添加章节大纲 schema 示例"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## 验证清单

- [ ] `story write 12 --prompt` 对 chapter 12 正确显示 L0 摘要（修复后）
- [ ] SKILL.md Phase 2 包含完整 schema 示例
