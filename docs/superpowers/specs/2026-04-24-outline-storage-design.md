# 大纲存储架构重构设计

## 概述

将卷大纲和章节大纲从单独的 yaml 文件迁移到 story.yaml 中，实现单一数据源。

## 背景

当前架构：
- `process/OUTLINE/volume-XXX.yaml` - 卷大纲
- `process/OUTLINE/volume-XXX/chapter-YYY.yaml` - 章节大纲
- `story.yaml` - 只存配置（无大纲数据）

问题：
- 数据分散，story write 12 时因 yaml 文件不存在导致 L0/L1 为空
- 需要从 story.yaml 读取才能保证数据一致性

## story.yaml 新增结构

```yaml
outlines:
  volumes:
    "1":                    # volume number as string
      volume_info: {number: 1, title: "风起云涌", theme: "..."}
      structure: {opening: "...", development: "...", climax: "...", ending: "..."}
      key_plot_points: ["事件1", "事件2", ...]
      chapter_summaries:
        "1": "第1章概要..."
        "2": "第2章概要..."
      chapter_list:
        - {number: 1, title: "山村少年", pov: "林默"}
        - {number: 2, title: "...", pov: "..."}
  chapters:
    "1-3":                  # "volume-chapter" format
      chapter_info: {number: 3, title: "...", pov: "林悦"}
      summary: "..."
      scenes:
        - {title: "...", pov: "林悦", location: "...", type: "..."}
      key_scenes: [...]
```

## 修改范围

### 1. outline.py
- 修改 `load_volume_outline()` / `load_chapter_outline()` 从 story.yaml 读取
- 修改 `save_volume_outline()` / `save_chapter_outline()` 写入 story.yaml

### 2. plan.py
- 无需修改，调用 outline.py 的函数

### 3. prompt.py
- 无需修改，通过 outline.py 读取数据

### 4. 向后兼容
- 如果 story.yaml 中没有数据，回退到读取 yaml 文件
- 已有 yaml 文件保留作为历史数据

## 实现顺序

1. 修改 `outline.py` 的读写函数
2. 测试 `story plan volume 1` 数据写入 story.yaml
3. 测试 `story write 12 --prompt` 从 story.yaml 读取数据
4. 验证 L0/L1 部分正确显示

## 废弃文件

- `process/OUTLINE/volume-XXX.yaml` - 不再写入，已有数据保留
- `process/OUTLINE/volume-XXX/chapter-YYY.yaml` - 不再写入，已有数据保留
