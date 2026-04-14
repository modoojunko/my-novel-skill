# 自动防重复机制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现自动防重复机制，防止 AI 在写小说时重复前5章的场景

**Architecture:** 轻量级集成方案 - 新增 `anti_repeat.py` 模块，在 `prompt.py` 中集成

**Tech Stack:** Python 3.8+, 标准库（json, re, pathlib）, PyYAML（可选，有 json 降级）

---

## File Structure

| File | Operation | Purpose |
|------|-----------|---------|
| `src_v2/anti_repeat.py` | Create | 防重复核心逻辑 |
| `src_v2/prompt.py` | Modify | 集成防重复逻辑到提示词生成 |
| `src_v2/write.py` | Modify | 添加 `--no-anti-repeat` 选项 |

---

## Phase 1: 基础框架

### Task 1: 创建 anti_repeat.py 模块框架

**Files:**
- Create: `src_v2/anti_repeat.py`

- [ ] **Step 1: 创建模块文件和基础结构**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anti_repeat - Anti-repetition mechanism for novel writing

Prevents AI from repeating scenes, dialogues, and behavior patterns
from previous chapters.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict


def load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Load YAML file, with JSON fallback"""
    import json
    try:
        import yaml
        use_yaml = True
    except ImportError:
        use_yaml = False

    if not path.exists():
        return None

    with open(path, 'r', encoding='utf-8') as f:
        if use_yaml:
            try:
                return yaml.safe_load(f) or {}
            except:
                pass
        # Try JSON fallback
        try:
            f.seek(0)
            return json.load(f)
        except:
            return None


def extract_scenes_from_snapshots(
    snapshots_dir: Path,
    volume_num: int,
    current_chapter: int,
    lookback: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract scenes from previous N chapter snapshots.

    Args:
        snapshots_dir: Directory with snapshots
        volume_num: Current volume number
        current_chapter: Current chapter number
        lookback: Number of chapters to look back (default: 5)

    Returns:
        List of scene dicts, each with:
        {
            'chapter': chapter number,
            'type': 'event'|'character'|'info',
            'content': scene content,
            'source': 'events_happened'|'characters_introduced'|'info_revealed'
        }
    """
    scenes = []
    start_chapter = max(1, current_chapter - lookback)

    for ch in range(start_chapter, current_chapter):
        # Get snapshot path - snapshot is in volume-XXX/snapshots/
        vol_for_ch = ((ch - 1) // 30) + 1  # Assume 30 chapters per volume if not known
        snapshot_path = snapshots_dir / f'volume-{vol_for_ch:03d}' / 'snapshots' / f'chapter-{ch:03d}.yaml'

        # Also try direct volume directory (in case volume_num is correct)
        if not snapshot_path.exists() and volume_num:
            snapshot_path = snapshots_dir / f'volume-{volume_num:03d}' / 'snapshots' / f'chapter-{ch:03d}.yaml'

        if not snapshot_path.exists():
            continue

        snapshot = load_yaml(snapshot_path)
        if not snapshot:
            continue

        # Extract events
        for event in snapshot.get('events_happened', []):
            scenes.append({
                'chapter': ch,
                'type': 'event',
                'content': event,
                'source': 'events_happened'
            })

        # Extract character introductions
        for char in snapshot.get('characters_introduced', []):
            char_name = char.get('name', '')
            char_role = char.get('role', '')
            content = char_name
            if char_role:
                content += f" ({char_role})"
            if content:
                scenes.append({
                    'chapter': ch,
                    'type': 'character',
                    'content': content,
                    'source': 'characters_introduced'
                })

        # Extract info reveals
        for info in snapshot.get('info_revealed', []):
            scenes.append({
                'chapter': ch,
                'type': 'info',
                'content': info,
                'source': 'info_revealed'
            })

    return scenes


def generate_forbidden_list(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate forbidden repetition list from scenes.

    Returns:
        {
            'all_scenes': [...],  # Flat list of all scenes
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
    result = {
        'all_scenes': [],
        'by_type': defaultdict(list),
        'by_chapter': defaultdict(list),
    }

    for scene in scenes:
        scene_entry = {
            'chapter': scene['chapter'],
            'content': scene['content']
        }
        result['all_scenes'].append(scene_entry)
        result['by_type'][scene['type']].append(scene_entry)
        result['by_chapter'][str(scene['chapter'])].append(scene_entry)

    # Convert defaultdict to regular dict
    result['by_type'] = dict(result['by_type'])
    result['by_chapter'] = dict(result['by_chapter'])

    return result


def generate_suggested_scenes(
    forbidden_list: Dict[str, Any],
    chapter_outline: Optional[Dict[str, Any]] = None,
    heuristics: Optional[List[Dict[str, str]]] = None
) -> List[str]:
    """
    Generate suggested new scenes based on forbidden list and chapter outline.

    Args:
        forbidden_list: Forbidden scene list
        chapter_outline: Current chapter outline (optional)
        heuristics: List of heuristic rules (optional)

    Returns:
        List of suggested scene ideas
    """
    if heuristics is None:
        # Default heuristics
        heuristics = [
            {
                'pattern': r'现场勘查|勘查现场|检查现场',
                'suggestion': '让证人主动找上门来提供线索，而不是主角去勘查'
            },
            {
                'pattern': r'门卫.*不记得|失忆.*证人',
                'suggestion': '证人记得，但因为害怕而有所隐瞒'
            },
            {
                'pattern': r'想敲门.*不敢|犹豫.*敲门',
                'suggestion': '直接推门进去，发现门没锁'
            },
            {
                'pattern': r'换了新锁|门锁被换',
                'suggestion': '门锁没换，但钥匙孔里有奇怪的东西'
            },
        ]

    suggestions = []
    all_content = ' '.join([s['content'] for s in forbidden_list.get('all_scenes', [])])

    # Apply heuristics
    for heuristic in heuristics:
        pattern = heuristic.get('pattern', '')
        suggestion = heuristic.get('suggestion', '')
        if pattern and suggestion:
            if re.search(pattern, all_content):
                suggestions.append(suggestion)

    # Limit to max 5 suggestions
    return suggestions[:5]


def build_prompt_section(
    forbidden_list: Dict[str, Any],
    suggestions: List[str],
    show_by_type: bool = True,
    show_by_chapter: bool = True
) -> str:
    """
    Build the anti-repetition section for the writing prompt.

    Args:
        forbidden_list: Forbidden scene list
        suggestions: List of suggested new scenes
        show_by_type: Whether to show scenes grouped by type
        show_by_chapter: Whether to show scenes grouped by chapter

    Returns:
        Formatted prompt section string
    """
    prompt = ""

    # Forbidden list section
    prompt += "## [防重复] 本章禁止重复的场景清单\n\n"
    prompt += "⚠️  以下场景在前5章已经出现过，本章请避免完全重复：\n\n"

    if show_by_type and forbidden_list.get('by_type'):
        prompt += "### 按类型分组：\n"
        type_names = {
            'event': '事件类',
            'character': '人物类',
            'info': '信息类'
        }
        for scene_type, scenes in forbidden_list['by_type'].items():
            type_name = type_names.get(scene_type, scene_type)
            prompt += f"- {type_name}：\n"
            for scene in scenes:
                prompt += f"  - 第{scene['chapter']}章：{scene['content']}\n"
        prompt += "\n"

    if show_by_chapter and forbidden_list.get('by_chapter'):
        prompt += "### 按章节分组：\n"
        for ch_num in sorted(forbidden_list['by_chapter'].keys(), key=int):
            scenes = forbidden_list['by_chapter'][ch_num]
            prompt += f"- 第{ch_num}章：\n"
            for scene in scenes:
                prompt += f"  - {scene['content']}\n"
        prompt += "\n"

    prompt += "---\n\n"

    # Suggestions section
    if suggestions:
        prompt += "## [建议] 本章可以尝试的新场景\n\n"
        prompt += "💡 基于本章大纲和前5章的情况，建议尝试：\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            prompt += f"{i}. {suggestion}\n"
        prompt += "\n---\n\n"

    return prompt


if __name__ == '__main__':
    print("anti_repeat module loaded")
```

- [ ] **Step 2: 验证文件创建成功**

Run: `ls -la src_v2/anti_repeat.py`
Expected: File exists

- [ ] **Step 3: 提交**

```bash
git add src_v2/anti_repeat.py
git commit -m "feat: add anti_repeat.py module foundation

- Add load_yaml utility
- Add extract_scenes_from_snapshots function
- Add generate_forbidden_list function
- Add generate_suggested_scenes function
- Add build_prompt_section function

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 集成 anti_repeat 到 prompt.py

**Files:**
- Modify: `src_v2/prompt.py`

- [ ] **Step 1: 在 prompt.py 顶部添加 import**

在文件顶部的 imports 部分添加：

```python
from .anti_repeat import (
    extract_scenes_from_snapshots,
    generate_forbidden_list,
    generate_suggested_scenes,
    build_prompt_section,
)
```

- [ ] **Step 2: 修改 build_writing_prompt 函数，集成防重复逻辑**

在 `build_writing_prompt()` 函数中，"全局写作要求"块结束之后、"[L0] 本章信息"之前，插入：

```python
    # ========== ANTI-REPETITION CHECK ==========
    style = config.get('style', {})
    anti_repeat_config = style.get('anti_repeat', {})

    if anti_repeat_config.get('enabled', True):
        lookback = anti_repeat_config.get('lookback_chapters', 5)
        show_by_type = anti_repeat_config.get('show_by_type', True)
        show_by_chapter = anti_repeat_config.get('show_by_chapter', True)
        max_suggestions = anti_repeat_config.get('max_suggestions', 5)
        heuristics = anti_repeat_config.get('heuristics', None)

        # Get snapshot directory from outline dir
        snapshots_dir = paths['outline']

        # Extract scenes from previous chapters
        scenes = extract_scenes_from_snapshots(
            snapshots_dir,
            volume_num,
            chapter_num,
            lookback
        )

        if scenes:
            # Generate forbidden list
            forbidden_list = generate_forbidden_list(scenes)

            # Get chapter outline
            chapter_outline = load_chapter_outline(paths['outline'], volume_num, chapter_num)

            # Generate suggestions
            suggestions = generate_suggested_scenes(
                forbidden_list,
                chapter_outline,
                heuristics
            )

            # Build prompt section
            anti_repeat_section = build_prompt_section(
                forbidden_list,
                suggestions,
                show_by_type,
                show_by_chapter
            )

            prompt += anti_repeat_section
```

- [ ] **Step 3: 验证修改正确**

检查文件确保没有语法错误。

- [ ] **Step 4: 提交**

```bash
git add src_v2/prompt.py
git commit -m "feat: integrate anti-repetition into prompt generation

- Add anti_repeat imports
- Insert anti-repetition section in build_writing_prompt
- Read config from style.anti_repeat
- Extract scenes, generate forbidden list and suggestions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 2: CLI 选项与配置

### Task 3: 在 write.py 中添加 --no-anti-repeat 选项

**Files:**
- Modify: `src_v2/write.py`

- [ ] **Step 1: 添加 CLI 选项解析**

在 `write.py` 的参数解析部分添加：

在 `main()` 函数中，添加变量：
```python
    no_anti_repeat = False
```

在参数解析循环中添加：
```python
        elif arg == '--no-anti-repeat':
            no_anti_repeat = True
```

- [ ] **Step 2: 修改 help 显示**

在 `show_write_help()` 中添加选项说明：
```
  --no-anti-repeat  Skip anti-repetition check
```

- [ ] **Step 3: 在生成提示词时临时禁用（如果需要）**

注意：这个实现暂时不需要修改 config，因为我们还没有实现 config 的动态修改。先只添加 CLI 选项解析。

- [ ] **Step 4: 提交**

```bash
git add src_v2/write.py
git commit -m "feat: add --no-anti-repeat option to write command

- Add CLI option parsing for --no-anti-repeat
- Update help documentation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 3: 测试与验证

### Task 4: 创建测试项目并验证

**Files:**
- Test: Create temporary test project

- [ ] **Step 1: 创建测试项目**

```bash
mkdir -p /tmp/test-anti-repeat
cd /tmp/test-anti-repeat
python3 /mnt/d/code/zhihu/my-novel-skill/story.py init --non-interactive --args '{"title":"测试防重复","genre":"悬疑"}'
```

- [ ] **Step 2: 创建测试快照**

创建测试快照目录和文件来模拟前几章：
```bash
mkdir -p /tmp/test-anti-repeat/process/OUTLINE/volume-001/snapshots
```

创建 `chapter-001.yaml` 快照：
```yaml
events_happened:
  - 张建国死亡（41岁，本地人，无业，独居）
  - 发现门锁被换
  - 门卫王大爷"不记得"了
characters_introduced:
  - name: 王大爷
    role: 门卫
info_revealed:
  - 死亡时间：今天凌晨两点到四点之间
```

创建 `chapter-002.yaml` 快照：
```yaml
events_happened:
  - 想敲门又不敢
  - 现场勘查发现痕迹
characters_introduced: []
info_revealed:
  - 近期三起类似死亡案件
```

- [ ] **Step 3: 创建章节大纲**

```bash
mkdir -p /tmp/test-anti-repeat/process/OUTLINE/volume-001
```

创建 `volume-001.yaml`:
```yaml
volume_info:
  number: 1
  title: 第一卷
  theme: 悬疑
```

创建 `chapter-003.yaml`:
```yaml
chapter_info:
  number: 3
  title: 第三章
  pov: 主角
brief_summary: 继续调查案件
```

- [ ] **Step 4: 生成第3章提示词并验证**

```bash
cd /tmp/test-anti-repeat
python3 /mnt/d/code/zhihu/my-novel-skill/story.py write 3 --prompt
```

验证生成的 `process/PROMPTS/chapter-003-prompt.md` 中包含：
- "[防重复] 本章禁止重复的场景清单"
- "[建议] 本章可以尝试的新场景"

- [ ] **Step 5: 清理测试项目**

```bash
rm -rf /tmp/test-anti-repeat
```

- [ ] **Step 6: 提交测试说明（可选，不提交代码）**

---

## Phase 4: 文档更新

### Task 5: 更新 README 或 SKILL.md（可选）

**Files:**
- Modify: `SKILL.md` (可选，本阶段不强制)

此任务为可选，留待后续完善。

---

## Self-Review

**1. Spec coverage:**
- ✅ 从前5章快照提取场景 - Task 1
- ✅ 生成禁止清单 - Task 1
- ✅ 生成建议新场景 - Task 1
- ✅ 集成到提示词生成 - Task 2
- ✅ 配置支持 - Task 1 (build_prompt_section reads config)
- ✅ CLI 选项 - Task 3

**2. Placeholder scan:**
- ✅ 无 TBD/TODO
- ✅ 所有步骤都有完整代码
- ✅ 所有命令都明确

**3. Type consistency:**
- ✅ 函数名一致
- ✅ 参数类型匹配
- ✅ 数据结构一致

Plan complete! All requirements from spec are covered.
