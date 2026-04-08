---
name: my-novel-skill 改进计划
overview: 补全缺失的 define 命令，增强字数统计功能，让 my-novel-skill 从"工作流管理工具"升级为更完整的 AI 协作写作助手
todos:
  - id: create-define-module
    content: 新建 src/define.py，实现设定库管理命令
    status: pending
  - id: update-init-py
    content: 更新 src/__init__.py，导出 define 模块
    status: pending
    dependencies:
      - create-define-module
  - id: update-story-py
    content: 更新 story.py，注册 define 命令
    status: pending
    dependencies:
      - create-define-module
  - id: enhance-stats-words
    content: 增强 src/stats.py，添加实际写作字数统计
    status: pending
  - id: update-skill-docs
    content: 更新 SKILL.md 文档，添加 define 和 stats 增强说明
    status: pending
    dependencies:
      - create-define-module
      - enhance-stats-words
---

## 需求概述

为 my-novel-skill 补充两个关键功能：

1. **define 命令**：管理人物卡和世界观设定库
2. **增强 stats 命令**：添加实际写作字数统计

## 详细需求

### define 命令（设定库管理）

- **列出设定**：`story:define --list` 列出所有人物卡和世界观条目
- **创建/编辑人物卡**：`story:define character <名字>` 创建或编辑人物设定文件
- **创建/编辑世界观**：`story:define world <名称>` 创建或编辑世界观文件
- **查看设定**：`story:define view <名字>` 查看特定设定
- **删除设定**：`story:define delete <名字>` 删除设定
- **搜索**：`story:define --search <关键词>` 搜索设定内容

人物卡模板包含：姓名、身份、性格、外貌、背景、人物弧光、关系网络
世界观模板包含：名称、类型、核心规则、详细描述

### 增强 stats 命令（写作字数统计）

- **实际字数统计**：扫描 CONTENT/ 目录，统计所有章节的实际中文字数
- **按卷显示**：分别显示每卷的完成字数和进度
- **总体进度**：当前字数 / 目标字数，完成百分比
- **进度条可视化**：ASCII 进度条
- **导出报告**：`--export` 支持导出 JSON 格式报告

### 更新的目录结构

```
SPECS/
  characters/           # 人物设定
    <角色名>.md        # 人物卡
  world/                # 世界观
    <世界观名>.md      # 世界观文件
  meta/
    story-concept.md    # 故事概念
```

### 人物卡格式

```markdown
# 角色名

## 基本信息
- 姓名：
- 身份/职位：
- 年龄：

## 外貌特征
- 身高、体型：
- 特征/标志：

## 性格特点
- 核心性格：
- 优点：
- 缺点/弱点：

## 背景故事
- 出身：
- 关键事件：
- 动机/目标：

## 人物弧光
- 起点：
- 转折点：
- 终点：

## 关系网络
- 与 XXX 的关系：
- 与 XXX 的关系：
```

### 世界观格式

```markdown
# 世界观名称

## 基本信息
- 类型：（地理/社会/魔法体系/科技/文化...）
- 重要程度：（核心/重要/次要）

## 核心规则
- 规则1：
- 规则2：

## 详细描述
[详细内容]

## 与故事的关系
[如何影响主线]
```

## 技术方案

### 技术栈

- **语言**：Python 3.x（纯标准库，不添加额外依赖）
- **文件格式**：Markdown（设定文件）+ JSON（配置）
- **CLI 框架**：argparse（已有）

### 实现架构

#### 1. src/define.py 模块

```
src/define.py
├── main()              # CLI 入口
├── list_specs()        # 列出所有设定
├── create_character()  # 创建人物卡
├── create_world()      # 创建世界观
├── view_spec()         # 查看设定
├── delete_spec()       # 删除设定
├── search_specs()      # 搜索设定
└── 辅助函数
    ├── get_template()  # 获取模板
    ├── save_spec()     # 保存设定
    └── load_spec()     # 读取设定
```

#### 2. src/stats.py 增强

在现有 stats.py 基础上添加：

```
src/stats.py (新增)
├── count_content_words()   # 扫描 CONTENT/ 统计字数
├── show_word_stats()      # 显示写作字数统计
├── calculate_volume_stats() # 按卷统计
└── show_word_progress()    # 显示进度条
```

#### 3. story.py 更新

- 导入 define 模块
- 注册 define 命令

#### 4. src/**init**.py 更新

- 添加 define 到导出列表

### 关键实现细节

#### 字数统计算法

```python
def count_chinese_chars(text: str) -> int:
    """统计中文字符数（不含标点和空格）"""
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            count += 1
    return count
```

#### 目录遍历

- 递归扫描 CONTENT/ 目录
- 跳过 tasks.md、.draft 等非正文文件
- 按 volume-{N}/chapter-{NNN}.md 模式匹配

### 数据流

```
用户执行 story:define character 张三
  → 检查 SPECS/characters/ 是否存在
  → 加载人物卡模板
  → 交互式收集信息（或 --non-interactive 模式）
  → 保存到 SPECS/characters/张三.md

用户执行 story:stats --words
  → 扫描 CONTENT/ 所有章节文件
  → 统计每章中文字数
  → 按卷汇总
  → 读取 story.json 的 target_words
  → 显示进度
```