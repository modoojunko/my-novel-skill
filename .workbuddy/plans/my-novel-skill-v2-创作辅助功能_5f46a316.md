---
name: my-novel-skill-v2-创作辅助功能
overview: 为 my-novel-skill 补充 6 个高频创作场景功能：章节回顾(recall)、自动衔接、导出(export)、场景灵感(scene)、大纲展开(outline expand)、大纲调整(outline swap)
todos:
  - id: create-recall-module
    content: 创建 src/recall.py - 章节回顾/摘要模块
    status: completed
  - id: create-export-module
    content: 创建 src/export.py - 导出 txt/docx 模块
    status: completed
  - id: enhance-write-continue
    content: 增强 src/write.py - 添加自动衔接功能
    status: completed
  - id: enhance-outline-expand
    content: 增强 src/outline.py - 添加 --expand 和 --swap 功能
    status: completed
  - id: create-scene-module
    content: 创建 src/scene.py - 场景灵感生成模块
    status: completed
    dependencies:
      - create-recall-module
  - id: update-init-export-dir
    content: 更新 src/init.py - 添加 EXPORT 目录创建
    status: completed
    dependencies:
      - create-export-module
  - id: update-story-py-commands
    content: 更新 story.py - 注册 recall, export, scene 命令
    status: completed
    dependencies:
      - create-recall-module
      - create-export-module
      - enhance-write-continue
      - enhance-outline-expand
      - create-scene-module
  - id: update-skill-docs
    content: 更新 SKILL.md - 添加新功能文档
    status: completed
    dependencies:
      - create-recall-module
      - create-export-module
      - enhance-write-continue
      - enhance-outline-expand
      - create-scene-module
  - id: update-readme
    content: 更新 README.md - 添加新命令说明
    status: completed
    dependencies:
      - update-skill-docs
---

# my-novel-skill v2 - 创作辅助功能

## 需求概述

精简为 4 个核心功能，解决小说家日常创作高频痛点。

## 功能列表

| # | 功能 | 描述 | 使用场景 |
| --- | --- | --- | --- |
| 1 | **recall** | 章节回顾/摘要 | "写第15章前，想快速看看13、14章发生了什么" |
| 2 | **export** | 导出 txt/docx | "写完了要导出发给编辑" |
| 3 | **outline --expand** | 展开场景细节 | "卡文了，大纲往下怎么写" |
| 4 | **outline --swap** | 调整章节顺序 | "第8章情节应该放到第10章" |


## 设计决策

### recall 与 update-specs 的关系

```
写完章节 → update-specs --auto
                    ↓
              生成摘要 → 保存到 OUTLINE/volume-N/summaries/chapter-005-summary.md
                    
story:recall 5 → 直接读摘要文件（秒开，无需重新分析）
```

**好处**：

- 写完就生成，不用等 recall 时再分析
- recall 秒开，直接读摘要文件
- 复用 update-specs 的章节分析逻辑

### 为什么去掉自动衔接和 scene

| 功能 | 原因 |
| --- | --- |
| ~~自动衔接~~ | 摘要已包含衔接信息，大纲的场景列表也告诉你怎么衔接 |
| ~~scene~~ | 大纲的场景列表（POV、地点、动作）本身就是场景灵感 |


## 功能详情

### 1. recall 命令

```
story:recall 5              # 查看第5章摘要
story:recall 3-5            # 查看第3到5章摘要
story:recall --recent 3      # 查看最近3章
```

**数据流**：

```
story:recall 5
  → 读取 OUTLINE/volume-N/summaries/chapter-005-summary.md
  → 显示摘要内容
  → 显示章节字数、POV人物、核心事件
```

### 2. export 命令

```
story:export                        # 导出整本书
story:export 1-10                   # 导出第1-10章
story:export --volume 1             # 导出第1卷
story:export 1-10 --format docx    # 指定格式（默认 txt）
```

**数据流**：

```
story:export 1-10 --format docx
  → 读取 CONTENT 第1-10章
  → 过滤 frontmatter 和任务注释
  → 合并内容
  → 生成 docx/txt 文件
  → 保存到 EXPORT/ 目录
```

### 3. outline --expand

```
story:outline --expand 8            # 展开第8章的场景细节
story:outline --expand 8 --scene 2 # 展开第8章第2个场景
```

**展开内容**：

```
## 场景1：张三来到青云门（展开）

** POV：张三
** 地点：青云门山门
** 时间：清晨
** 预期字数：500字

** 核心动作：
   - 张三抬头看山门牌匾
   - 回忆师父的叮嘱
   - 深呼吸，准备入门

** 情绪基调：紧张、期待、微微不安

** 可能需要的对话：
   - 守门弟子盘问
   - 张三报上名号
```

### 4. outline --swap

```
story:outline --swap 8 10         # 交换第8章和第10章
```

**行为**：

- 保留大纲内容不变
- 自动更新章节编号
- 需要确认后再执行

## 技术方案

### 技术栈

- Python 3.x（纯标准库，不添加额外依赖）
- 文件格式：Markdown（导出时转 txt/docx）
- 复用现有架构模式

### 模块设计

#### 1. src/recall.py [NEW]

```python
src/recall.py
├── main()                    # CLI 入口
├── read_summary()            # 读取预生成摘要
├── show_recall()             # 显示回顾结果
└── 辅助函数
    ├── parse_chapter_range() # 解析章节范围
    └── format_recall_view()  # 格式化显示
```

#### 2. src/export.py [NEW]

```python
src/export.py
├── main()                    # CLI 入口
├── export_chapters()        # 导出章节
├── convert_to_txt()         # 转为 txt
├── convert_to_docx()        # 转为 docx（纯 Python）
├── strip_frontmatter()      # 去除 frontmatter
└── 辅助函数
    ├── parse_export_range()  # 解析导出范围
    └── merge_chapters()      # 合并章节
```

#### 3. src/outline.py 增强

- 添加 `--expand` 功能：展开场景细节
- 添加 `--swap` 功能：交换章节顺序

## 目录结构变更

```
{项目根}/
  EXPORT/                    # [NEW] 导出文件目录
    novel-title-ch1-10.docx
    volume-1-export.txt
  OUTLINE/
    volume-N/
      summaries/             # [NEW] 章节摘要目录
        chapter-005-summary.md
        chapter-006-summary.md
```

## 实施计划

### 任务列表

| # | 任务 | 模块 | 依赖 |
| --- | --- | --- | --- |
| 1 | recall - 读取预生成摘要 | `src/recall.py` 🆕 | - |
| 2 | export - 导出 txt/docx | `src/export.py` 🆕 | - |
| 3 | outline --expand - 展开场景 | `src/outline.py` 增强 | - |
| 4 | outline --swap - 调整顺序 | `src/outline.py` 增强 | - |
| 5 | 整合：story.py | 注册命令 | 1,2,3,4 |
| 6 | 更新 SKILL.md | 文档 | 1,2,3,4 |
| 7 | 更新 README.md | 文档 | 6 |


### 执行顺序

```
第一批（独立，可并行）
  ├── recall.py
  ├── export.py
  ├── outline 增强（expand + swap）
  │
  ↓
第二批
  ├── story.py（注册命令）
  ├── SKILL.md
  └── README.md
```