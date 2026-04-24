# 大纲存储架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将卷大纲和章节大纲从单独的 yaml 文件迁移到 story.yaml 中，实现单一数据源。

**Architecture:** 修改 `outline.py` 的 4 个函数（load/save volume+chapter outlines），从 story.yaml 的 `outlines.volumes.{n}` 和 `outlines.chapters.{vol-ch}` 读写数据。保持向后兼容（yaml 文件作为 fallback）。

**Tech Stack:** Python 3.8+, 仅使用标准库

---

## 文件修改

- Modify: `src_v2/outline.py:148-166` (load_volume_outline, save_volume_outline, load_chapter_outline, save_chapter_outline)

---

## Task 1: 修改 load_volume_outline

**Files:**
- Modify: `src_v2/outline.py:148-150`

- [ ] **Step 1: 添加必要的 import**

在 outline.py 顶部添加（如果还没有）：
```python
from .paths import find_project_root, load_config, save_config
```

- [ ] **Step 2: 修改 load_volume_outline 函数**

将：
```python
def load_volume_outline(outline_dir: Path, volume_num: int) -> Optional[Dict[str, Any]]:
    """Load a volume outline"""
    return load_yaml(get_volume_path(outline_dir, volume_num))
```

改为：
```python
def load_volume_outline(outline_dir: Path, volume_num: int) -> Optional[Dict[str, Any]]:
    """Load a volume outline from story.yaml, fallback to yaml file"""
    root = find_project_root()
    if root:
        config = load_config(root)
        outlines = config.get('outlines', {})
        volumes = outlines.get('volumes', {})
        vol_key = str(volume_num)
        if vol_key in volumes:
            return volumes[vol_key]
    # Fallback to yaml file
    return load_yaml(get_volume_path(outline_dir, volume_num))
```

- [ ] **Step 3: 验证语法**

Run: `python3 -c "import ast; ast.parse(open('src_v2/outline.py').read()); print('Syntax OK')"`

- [ ] **Step 4: Commit**

```bash
git add src_v2/outline.py
git commit -m "refactor: outline.py load_volume_outline 从 story.yaml 读取"
```

---

## Task 2: 修改 save_volume_outline

**Files:**
- Modify: `src_v2/outline.py:153-155`

- [ ] **Step 1: 修改 save_volume_outline 函数**

将：
```python
def save_volume_outline(outline_dir: Path, volume_num: int, data: Dict[str, Any]) -> None:
    """Save a volume outline"""
    save_yaml(get_volume_path(outline_dir, volume_num), data)
```

改为：
```python
def save_volume_outline(outline_dir: Path, volume_num: int, data: Dict[str, Any]) -> None:
    """Save a volume outline to story.yaml"""
    root = find_project_root()
    if root:
        config = load_config(root)
        if 'outlines' not in config:
            config['outlines'] = {}
        if 'volumes' not in config['outlines']:
            config['outlines']['volumes'] = {}
        config['outlines']['volumes'][str(volume_num)] = data
        save_config(root, config)
```

- [ ] **Step 2: 验证语法**

Run: `python3 -c "import ast; ast.parse(open('src_v2/outline.py').read()); print('Syntax OK')"`

- [ ] **Step 3: Commit**

```bash
git add src_v2/outline.py
git commit -m "refactor: outline.py save_volume_outline 写入 story.yaml"
```

---

## Task 3: 修改 load_chapter_outline

**Files:**
- Modify: `src_v2/outline.py:158-160`

- [ ] **Step 1: 修改 load_chapter_outline 函数**

将：
```python
def load_chapter_outline(outline_dir: Path, volume_num: int, chapter_num: int) -> Optional[Dict[str, Any]]:
    """Load a chapter outline"""
    return load_yaml(get_chapter_path(outline_dir, volume_num, chapter_num))
```

改为：
```python
def load_chapter_outline(outline_dir: Path, volume_num: int, chapter_num: int) -> Optional[Dict[str, Any]]:
    """Load a chapter outline from story.yaml, fallback to yaml file"""
    root = find_project_root()
    if root:
        config = load_config(root)
        outlines = config.get('outlines', {})
        chapters = outlines.get('chapters', {})
        ch_key = f"{volume_num}-{chapter_num}"
        if ch_key in chapters:
            return chapters[ch_key]
    # Fallback to yaml file
    return load_yaml(get_chapter_path(outline_dir, volume_num, chapter_num))
```

- [ ] **Step 2: 验证语法**

Run: `python3 -c "import ast; ast.parse(open('src_v2/outline.py').read()); print('Syntax OK')"`

- [ ] **Step 3: Commit**

```bash
git add src_v2/outline.py
git commit -m "refactor: outline.py load_chapter_outline 从 story.yaml 读取"
```

---

## Task 4: 修改 save_chapter_outline

**Files:**
- Modify: `src_v2/outline.py:163-166`

- [ ] **Step 1: 修改 save_chapter_outline 函数**

将：
```python
def save_chapter_outline(outline_dir: Path, volume_num: int, chapter_num: int, data: Dict[str, Any]) -> None:
    """Save a chapter outline"""
    get_chapter_dir(outline_dir, volume_num).mkdir(parents=True, exist_ok=True)
    save_yaml(get_chapter_path(outline_dir, volume_num, chapter_num), data)
```

改为：
```python
def save_chapter_outline(outline_dir: Path, volume_num: int, chapter_num: int, data: Dict[str, Any]) -> None:
    """Save a chapter outline to story.yaml"""
    root = find_project_root()
    if root:
        config = load_config(root)
        if 'outlines' not in config:
            config['outlines'] = {}
        if 'chapters' not in config['outlines']:
            config['outlines']['chapters'] = {}
        ch_key = f"{volume_num}-{chapter_num}"
        config['outlines']['chapters'][ch_key] = data
        save_config(root, config)
```

- [ ] **Step 2: 验证语法**

Run: `python3 -c "import ast; ast.parse(open('src_v2/outline.py').read()); print('Syntax OK')"`

- [ ] **Step 3: Commit**

```bash
git add src_v2/outline.py
git commit -m "refactor: outline.py save_chapter_outline 写入 story.yaml"
```

---

## Task 5: 集成测试

**Files:**
- None (manual test)

- [ ] **Step 1: 检查是否有小说项目**

如果没有，跳过测试。如果有：
```bash
cd /path/to/novel-project
python3 story.py status
```

- [ ] **Step 2: 运行 story write N --prompt 测试**

```bash
python3 story.py write 12 --prompt
```

验证 L0（章概要）和 L1（卷信息）部分正确显示。

- [ ] **Step 3: 如有需要，运行 story plan volume 重新生成大纲**

```bash
python3 story.py plan volume 2
```

验证数据写入 story.yaml（可用 `grep -A 5 "outlines:" story.yaml` 检查）。

---

## 验证清单

- [ ] load_volume_outline 从 story.yaml 读取
- [ ] save_volume_outline 写入 story.yaml
- [ ] load_chapter_outline 从 story.yaml 读取
- [ ] save_chapter_outline 写入 story.yaml
- [ ] story write N --prompt 生成正确的 L0/L1 内容
- [ ] 向后兼容：yaml 文件仍然可读取（如果 story.yaml 没有数据）
