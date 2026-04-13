---
title: 自动防重复机制设计文档
date: 2026-04-13
feature: anti-repeat-mechanism
status: draft
---

# 自动防重复机制设计

## 概述

防止 AI 在写小说时重复前几章的场景、对话、行为模式。

## 问题背景

在使用 my-novel-skill 写小说过程中，遇到以下重复问题：
- 后续章节大量重复前几章的场景描写、对话模式、人物行为
- 不同案件的清理模式完全照搬（"门锁换了+证人失忆"）
- 人物内心斗争重复（"想敲门又不敢"写了多次）

## 需求

### 核心需求
1. 在生成正文前，自动检查与前5章的重复内容
2. 从章节快照中提取细粒度场景（每个独立事件算一个场景）
3. 生成"本章禁止重复内容清单"（完整列出前5章所有场景）
4. 提供"建议的新场景"作为替代选项

### 非目标
- 不做文本相似度计算（只基于结构化快照）
- 不强制阻止重复（只在提示词中警告）
- 不修改已写好的章节

## 方案选择

选择 **方案一：轻量级集成**

### 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| 方案一：轻量级集成 | 改动最小、风险低、直接集成到现有流程 | 功能相对简单 |
| 方案二：独立 Pipeline | 职责分离清晰、可独立运行 | 改动较大 |
| 方案三：交互式 Review | 用户可调整、更灵活 | 增加用户操作步骤 |

### 选择理由
- 满足当前所有需求
- 改动最小，最快可用
- 未来可轻松演进到其他方案

## 架构设计

### 整体架构

```
chapter-N 要写了
    ↓
load 前5章的 snapshot
    ↓
anti_repeat.py 提取场景
    ↓
生成 "禁止清单" + "建议新场景"
    ↓
prompt.py 合并到最终提示词
```

### 模块结构

```
src_v2/
  ├── anti_repeat.py       [NEW] 防重复核心逻辑
  ├── prompt.py            [MODIFIED] 集成防重复
  └── ... (其他模块不变)
```

## 详细设计

### 1. `src_v2/anti_repeat.py` 模块

#### 核心函数

##### `extract_scenes_from_snapshots()`
```python
def extract_scenes_from_snapshots(
    snapshots_dir: Path,
    volume_num: int,
    current_chapter: int,
    lookback: int = 5
) -> List[Dict[str, Any]]:
    """
    从前N章快照中提取场景

    Args:
        snapshots_dir: 快照目录
        volume_num: 当前卷号
        current_chapter: 当前章节号
        lookback: 回顾多少章（默认5）

    Returns:
        场景列表，每个场景包含：
        {
            'chapter': 章节号,
            'type': 'event'|'character'|'info',
            'content': 场景内容,
            'source': 'events_happened'|'characters_introduced'|'info_revealed'
        }
    """
```

##### `generate_forbidden_list()`
```python
def generate_forbidden_list(
    scenes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    生成禁止重复清单

    Returns:
        {
            'all_scenes': [...],  # 所有场景扁平列表
            'by_type': {
                'event': [...],
                'character': [...],
                'info': [...]
            },
            'by_chapter': {
                '1': [...],
                '2': [...]
            }
        }
    """
```

##### `generate_suggested_scenes()`
```python
def generate_suggested_scenes(
    forbidden_list: Dict[str, Any],
    chapter_outline: Dict[str, Any],
    heuristics: Optional[List[Dict[str, str]]] = None
) -> List[str]:
    """
    基于禁止清单和本章大纲，生成建议的新场景

    Args:
        forbidden_list: 禁止清单
        chapter_outline: 本章大纲
        heuristics: 启发式规则库

    Returns:
        建议的新场景列表
    """
```

#### 启发式规则库

默认提供的启发式规则（可在 story.yaml 中配置）。

**匹配方式**：使用正则表达式匹配（`re.search()`），如果 pattern 中包含 `|` 则表示"或"关系。

```yaml
heuristics:
  - pattern: "现场勘查|勘查现场|检查现场"
    suggestion: "让证人主动找上门来提供线索"
  - pattern: "门卫.*不记得|失忆.*证人"
    suggestion: "证人记得，但因为害怕而有所隐瞒"
  - pattern: "想敲门.*不敢|犹豫.*敲门"
    suggestion: "直接推门进去，发现门没锁"
  - pattern: "换了新锁|门锁被换"
    suggestion: "门锁没换，但钥匙孔里有东西"
```

### 2. `src_v2/prompt.py` 集成

在 `build_writing_prompt()` 函数中，在"全局写作要求"之后、"[L0] 本章信息"之前插入防重复内容。

#### 提示词新增内容

```markdown
## [防重复] 本章禁止重复的场景清单

⚠️  以下场景在前5章已经出现过，本章请避免完全重复：

### 按类型分组：
- 事件类：
  - 第1章：张建国死亡（41岁，本地人，无业，独居）
  - 第1章：发现门锁被换
  - 第2章：门卫王大爷"不记得"了
  - ...

### 按章节分组：
- 第1章：
  - ...
- 第2章：
  - ...

---

## [建议] 本章可以尝试的新场景

💡 基于本章大纲和前5章的情况，建议尝试：

1. （替代"现场勘查"）：让证人主动找上门来
2. （替代"证人失忆"）：证人记得，但因为害怕而不敢直接说
3. （替代"想敲门又不敢"）：直接推门进去，发现门没锁
4. ...

---
```

### 3. `story.yaml` 配置

新增 `style.anti_repeat` 配置：

```yaml
style:
  # ... (现有配置) ...

  # 防重复机制配置
  anti_repeat:
    enabled: true                    # 是否启用防重复
    lookback_chapters: 5             # 检查前几章
    show_by_type: true               # 在提示词中显示按类型分组
    show_by_chapter: true            # 在提示词中显示按章节分组
    max_suggestions: 5               # 最多生成多少个建议新场景
    # 启发式规则库（可以自定义）
    heuristics:
      - pattern: "现场勘查|勘查现场|检查现场"
        suggestion: "让证人主动找上门来提供线索"
      - pattern: "门卫.*不记得|失忆.*证人"
        suggestion: "证人记得，但因为害怕而有所隐瞒"
      - pattern: "想敲门.*不敢|犹豫.*敲门"
        suggestion: "直接推门进去，发现门没锁"
```

### 4. CLI 选项

在 `write.py` 中新增选项：

```bash
story write <num> --prompt --no-anti-repeat
```

跳过防重复检查（用于特殊情况）。

## 数据格式

### 场景数据结构

```python
{
    'chapter': 1,           # 章节号
    'type': 'event',        # 'event' | 'character' | 'info'
    'content': '张建国死亡...',  # 场景内容
    'source': 'events_happened'  # 来源字段
}
```

### 禁止清单数据结构

```python
{
    'all_scenes': [
        # 所有场景的扁平列表
    ],
    'by_type': {
        'event': [...],
        'character': [...],
        'info': [...]
    },
    'by_chapter': {
        '1': [...],
        '2': [...]
    }
}
```

## 实现计划

### Phase 1: 基础框架
1. 创建 `src_v2/anti_repeat.py`
2. 实现 `extract_scenes_from_snapshots()`
3. 实现 `generate_forbidden_list()`

### Phase 2: 建议生成
1. 实现 `generate_suggested_scenes()`
2. 实现启发式规则匹配
3. 添加默认启发式规则库

### Phase 3: 集成
1. 修改 `prompt.py` 集成防重复逻辑
2. 在提示词中格式化输出
3. 添加配置支持

### Phase 4: 测试
1. 单元测试
2. 集成测试
3. 实际项目测试

## 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 禁止清单太长，占用太多 token | 高 | 中 | 提供开关、可配置分组显示 |
| 启发式规则不够智能 | 中 | 高 | 规则可配置、允许用户自定义 |
| 过度限制创作 | 中 | 低 | 提供 --no-anti-repeat 跳过选项 |

## 成功标准

1. 能正确从前5章快照中提取场景
2. 生成的提示词中包含禁止清单和建议新场景
3. 用户反馈重复场景明显减少
4. 不影响现有的提示词生成功能

## 后续扩展

1. 支持文本相似度分析（方案二演进）
2. 添加交互式 review 模式（方案三演进）
3. 集成到 chapter archive 阶段，自动学习重复模式
4. 支持按角色类型、场景类型分别配置
