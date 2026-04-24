# Skill 工作流与章节大纲 Schema 设计

## 背景

SKILL.md Phase 2（每卷开始前）只有一句话"直接编辑 story.yaml 规划卷大纲和章节大纲"，没有具体格式说明，导致：
1. Agent 不知道章节大纲的数据结构
2. `story write N --prompt` 的回退逻辑依赖 `chapter_summaries`，但 key 类型不匹配导致查找失败

## 解决方案

### 1. SKILL.md Phase 2 添加完整 Schema 示例

**卷大纲格式（写入 `outlines.volumes.{n}`）：**

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
        ...
```

**章节大纲格式（写入 `outlines.chapters."{vol}-{ch}"`）：**

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

### 2. 修复 prompt.py key 类型查找 bug

`prompt.py` 中 `chapter_summaries` 查找需要同时尝试 string 和 int：

```python
# 现有代码（只查 string key）
ch_summary = chapter_summaries.get(str(chapter_in_volume))

# 修复后（同时尝试 string 和 int key）
ch_summary = chapter_summaries.get(str(chapter_in_volume)) or chapter_summaries.get(chapter_in_volume)
```

### 3. 数据层级说明

- `outlines.volumes.{n}.chapter_summaries.{ch}` — 每卷创建时的一句话概要，**必须提供**
- `outlines.chapters."{vol}-{ch}"` — 完整章节大纲（可选），**推荐提供**让 L0 更丰富

当 `outlines.chapters` 有数据时，`story write N --prompt` 显示完整章节大纲。
当 `outlines.chapters` 无数据时，回退到 `chapter_summaries`（一句话概要）。

## 修改文件

1. **SKILL.md** - Phase 2 添加完整 Schema 示例
2. **src_v2/prompt.py:722** - 修复 chapter_summaries key 类型查找
