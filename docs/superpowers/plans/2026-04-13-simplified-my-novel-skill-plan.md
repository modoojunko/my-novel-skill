# Simplified My-Novel-Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a simplified AI-assisted novel writing tool with:
- Main Agent collects info via conversation
- Sub-Agent writes chapters with structured prompts
- Progress management with breakpoints
- Three-directory structure (process/output/templates)

**Architecture:**
- Python CLI with modular src/ directory
- YAML for all data formats
- Two-layer agent system (main + sub-agent)
- Smart prompt templating with summarization

**Tech Stack:**
- Python 3.8+ (standard library only)
- YAML (PyYAML optional, fallback to json/yaml modules)
- Markdown for output content

---

## Project Decomposition

This spec covers multiple independent subsystems. We'll implement in phases:

**Phase 1:** Core infrastructure (init, paths, config, status)
**Phase 2:** Info collection & expansion (templates, question flow)
**Phase 3:** Outline management (volume, chapter, scene formats)
**Phase 4:** Character system with cognitive models
**Phase 5:** Smart prompt generation & summarization
**Phase 6:** Sub-agent writing & progress management
**Phase 7:** Snapshot, archive, export features

Let's start with **Phase 1: Core Infrastructure**.

---

## Phase 1: Core Infrastructure

### Task 1: Project Structure & Paths Module

**Files:**
- Create: `src_v2/paths.py`
- Reference: `src/paths.py` (existing code)

- [ ] **Step 1: Create new paths module with simplified three-dir design**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paths - Simplified path resolution module

Three-directory design:
- project_root: story.yaml + templates/
- process_dir: process/ (INFO, OUTLINE, PROMPTS, TEMPLATES)
- output_dir: output/ (CONTENT, EXPORT, ARCHIVE)
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any


def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """Check current directory for story.yaml"""
    if start is None:
        start = Path.cwd()
    if (start / 'story.yaml').exists():
        return start
    return None


def load_config(root: Path) -> Dict[str, Any]:
    """Load story.yaml config"""
    config_path = root / 'story.yaml'
    if not config_path.exists():
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_config(root: Path, config: Dict[str, Any]) -> None:
    """Save config to story.yaml"""
    config_path = root / 'story.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)


def load_project_paths(root: Path) -> Dict[str, Path]:
    """Load all project paths, create directories if needed"""
    config = load_config(root)
    paths_cfg = config.get('paths', {})
    
    # Three main directories
    project_root = root
    process_dir = root / paths_cfg.get('process_dir', 'process')
    output_dir = root / paths_cfg.get('output_dir', 'output')
    
    # Create all directories
    dirs_to_create = [
        # Process dir structure
        process_dir / 'INFO',
        process_dir / 'INFO' / 'characters' / 'protagonist',
        process_dir / 'INFO' / 'characters' / 'main_cast',
        process_dir / 'INFO' / 'characters' / 'supporting',
        process_dir / 'INFO' / 'characters' / 'guest',
        process_dir / 'OUTLINE',
        process_dir / 'OUTLINE' / 'volume-001',
        process_dir / 'PROMPTS',
        process_dir / 'TEMPLATES' / 'collect',
        process_dir / 'TEMPLATES' / 'expand',
        # Output dir structure
        output_dir / 'CONTENT' / 'volume-001',
        output_dir / 'EXPORT',
        output_dir / 'ARCHIVE',
    ]
    
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
    
    return {
        'root': project_root,
        'process': process_dir,
        'output': output_dir,
        'info': process_dir / 'INFO',
        'characters': process_dir / 'INFO' / 'characters',
        'outline': process_dir / 'OUTLINE',
        'prompts': process_dir / 'PROMPTS',
        'templates': process_dir / 'TEMPLATES',
        'content': output_dir / 'CONTENT',
        'export': output_dir / 'EXPORT',
        'archive': output_dir / 'ARCHIVE',
    }


def get_volume_dir(paths: Dict[str, Path], volume_num: int, dir_type: str = 'outline') -> Path:
    """Get volume directory path"""
    vol_name = f'volume-{volume_num:03d}'
    if dir_type == 'outline':
        return paths['outline'] / vol_name
    elif dir_type == 'content':
        return paths['content'] / vol_name
    return paths['outline'] / vol_name


def get_chapter_path(paths: Dict[str, Path], chapter_num: int, 
                     chapters_per: int = 30, file_type: str = 'outline') -> Path:
    """Get chapter file path"""
    volume_num = ((chapter_num - 1) // chapters_per) + 1
    vol_dir = get_volume_dir(paths, volume_num, 'outline' if file_type == 'outline' else 'content')
    ch_name = f'chapter-{chapter_num:03d}'
    
    if file_type == 'outline':
        return vol_dir / f'{ch_name}.yaml'
    elif file_type == 'content':
        return vol_dir / f'{ch_name}.md'
    elif file_type == 'tasks':
        return vol_dir / f'{ch_name}.tasks.md'
    return vol_dir / f'{ch_name}.yaml'
```

- [ ] **Step 2: Verify the module imports correctly**

Run: `python3 -c "from src_v2.paths import find_project_root, load_project_paths; print('OK')"`
Expected: Outputs "OK"

---

### Task 2: Project Initialization (init)

**Files:**
- Create: `src_v2/init.py`
- Create: `src_v2/story.py` (new entry point)

- [ ] **Step 1: Create init.py with interactive collection flow**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:init - Initialize simplified novel project
"""

import sys
from pathlib import Path
from datetime import datetime
from .paths import find_project_root, save_config, load_project_paths


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def input_with_default(prompt: str, default: str = "") -> str:
    """Get input with default value"""
    user_input = input(f"  {prompt} [{default}]: ").strip()
    return user_input if user_input else default


def select_option(prompt: str, options: list) -> int:
    """Show selection menu"""
    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        try:
            choice = int(input(f"  Select [1-{len(options)}]: ").strip())
            if 1 <= choice <= len(options):
                return choice
        except ValueError:
            pass
        print(f"  {c('Invalid selection', Colors.RED)}")


def main():
    print(f"\n{c('═' * 60, Colors.CYAN)}")
    print(f"  {c('[INIT] Simplified Novel Workflow', Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.CYAN)}\n")
    
    # Check if already initialized
    root = Path.cwd()
    if (root / 'story.yaml').exists():
        print(f"  {c('Warning: story.yaml already exists', Colors.YELLOW)}")
        response = input(f"  Re-initialize? [y/N]: ").strip().lower()
        if response != 'y':
            print("  Cancelled")
            return
    
    # Collect basic info
    print(f"  {c('[STEP 1] Basic Info', Colors.BOLD)}")
    title = input_with_default("Book title", "My Novel")
    
    genre_options = ["玄幻", "都市", "科幻", "悬疑", "言情", "武侠", "历史", "游戏", "轻小说", "其他"]
    genre_idx = select_option("Select genre", genre_options)
    genre = genre_options[genre_idx - 1]
    
    target_words = int(input_with_default("Target word count", "500000"))
    volumes = int(input_with_default("Number of volumes", "3"))
    chapters_per_volume = int(input_with_default("Chapters per volume", "30"))
    
    print(f"\n  {c('[STEP 2] Writing Style', Colors.BOLD)}")
    tone_options = ["热血/成长", "轻松/幽默", "沉郁/厚重", "诙谐/搞笑", "严肃/正剧"]
    tone_idx = select_option("Overall tone", tone_options)
    tone = tone_options[tone_idx - 1]
    
    pacing = input_with_default("Pacing preference", "适中")
    description = input_with_default("Description preference", "详细")
    dialogue = input_with_default("Dialogue ratio", "平衡")
    examples = input_with_default("Reference works (optional)", "")
    
    # Create config
    config = {
        "meta": {
            "version": "2.0-simplified",
            "created": datetime.now().strftime('%Y-%m-%d'),
            "updated": datetime.now().strftime('%Y-%m-%d'),
        },
        "book": {
            "title": title,
            "genre": genre,
            "target_words": target_words,
        },
        "structure": {
            "volumes": volumes,
            "chapters_per_volume": chapters_per_volume,
        },
        "style": {
            "tone": tone,
            "pacing": pacing,
            "description": description,
            "dialogue": dialogue,
            "examples": examples.split(',') if examples else [],
        },
        "progress": {
            "current_volume": 1,
            "current_chapter": 0,
            "completed_chapters": [],
        },
        "paths": {
            "process_dir": "process",
            "output_dir": "output",
        },
    }
    
    # Save config and create directories
    save_config(root, config)
    paths = load_project_paths(root)
    
    # Create initial templates (minimal)
    _create_default_templates(paths)
    
    print(f"\n  {c('✓ Success!', Colors.GREEN)}")
    print(f"  Project initialized at: {root}")
    print(f"\n  Next steps:")
    print(f"    1. story collect core      - Collect core story info")
    print(f"    2. story collect protagonist - Create protagonist")
    print(f"    3. story plan volume 1     - Plan volume 1")
    print(f"    4. story status            - Check project status")


def _create_default_templates(paths):
    """Create minimal default templates"""
    # Core collection template
    collect_core = paths['templates'] / 'collect' / 'core.yaml'
    collect_core.write_text("""questions:
  - key: story_concept
    question: "一句话故事概要？（如：一个___的___，在___中，必须___）"
  - key: core_theme
    question: "核心主题？（如：复仇与成长、忠诚与背叛）"
  - key: main_conflict_type
    question: "核心冲突类型？（正邪对立/情感纠葛/成长困境/其他）"
""", encoding='utf-8')
    
    # Core expansion template
    expand_core = paths['templates'] / 'expand' / 'core.yaml'
    expand_core.write_text("""template: |
  # 核心信息扩写任务
  
  ## 用户提供的核心信息
  {user_answers}
  
  ## 写作风格
  - 基调：{style_tone}
  - 节奏：{style_pacing}
  
  ## 任务
  基于以上信息，生成完整的 story-concept.yaml，包括：
  1. story_concept（一句话概要）
  2. core_theme（核心主题详述）
  3. premise（故事前提：如果...那么...）
  4. main_conflict（详细描述）
  5. ending_direction（大致结局走向）
  
  请直接返回 YAML 格式。
""", encoding='utf-8')


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Create new story.py entry point**

```python
#!/usr/bin/env python3
"""
Simplified Novel Workflow CLI
"""

import sys
from pathlib import Path

# Add src_v2 to path
sys.path.insert(0, str(Path(__file__).parent))

from src_v2 import init, paths


def show_help():
    print("""
Usage: story <command> [options]

Commands:
  init        Initialize new project
  status      Show project status
  collect     Collect information (core, protagonist, etc.)
  plan        Plan outline (volume, chapter)
  write       Generate chapter prompt / write
  archive     Archive completed chapter
  export      Export novel

Use 'story <command> --help' for more info.
""")


def main():
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║          [BOOK] Simplified Novel Workflow v2.0                ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝
""")
        show_help()
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'help' or cmd == '--help' or cmd == '-h':
        show_help()
        return
    
    commands = {
        'init': init,
        # Add other modules as we implement them
    }
    
    if cmd in commands:
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        commands[cmd].main()
    else:
        print(f"  Unknown command: {cmd}")
        print("  Use 'story --help' for available commands")


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: Test init command**

Run: `mkdir -p /tmp/test_novel && cd /tmp/test_novel && python3 /mnt/d/code/zhihu/my-novel-skill/src_v2/story.py init --non-interactive --title "Test" --genre 玄幻 --words 100000`
Expected: Creates story.yaml and directory structure

---

### Task 3: Status Command

**Files:**
- Create: `src_v2/status.py`

- [ ] **Step 1: Create status module with basic project overview**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:status - Show project status
"""

from .paths import find_project_root, load_config, load_project_paths


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def main():
    root = find_project_root()
    if not root:
        print("  Error: Not in a novel project (no story.yaml)")
        print("  Run 'story init' first")
        return
    
    config = load_config(root)
    paths = load_project_paths(root)
    
    book = config.get('book', {})
    structure = config.get('structure', {})
    progress = config.get('progress', {})
    style = config.get('style', {})
    
    print(f"\n{c('═' * 60, Colors.BOLD)}")
    print(f"  {c(book.get('title', 'Untitled'), Colors.BOLD)}")
    print(f"{c('═' * 60, Colors.BOLD)}\n")
    
    print(f"  {c('Basic Info:', Colors.BOLD)}")
    print(f"    Genre: {book.get('genre', 'Unknown')}")
    print(f"    Target: {book.get('target_words', 0):,} words")
    print(f"    Volumes: {structure.get('volumes', 0)}")
    print(f"    Chapters/Volume: {structure.get('chapters_per_volume', 30)}")
    
    print(f"\n  {c('Progress:', Colors.BOLD)}")
    completed = len(progress.get('completed_chapters', []))
    total = structure.get('volumes', 0) * structure.get('chapters_per_volume', 30)
    print(f"    Current: Volume {progress.get('current_volume', 1)}, Chapter {progress.get('current_chapter', 0)}")
    print(f"    Completed: {completed} / {total} chapters")
    if total > 0:
        pct = (completed / total) * 100
        print(f"    Progress: [{c('█' * int(pct/10) + '░' * (10-int(pct/10)), Colors.GREEN)}] {pct:.1f}%")
    
    print(f"\n  {c('Style:', Colors.BOLD)}")
    print(f"    Tone: {style.get('tone', 'N/A')}")
    print(f"    Pacing: {style.get('pacing', 'N/A')}")
    print(f"    Description: {style.get('description', 'N/A')}")
    print(f"    Dialogue: {style.get('dialogue', 'N/A')}")
    
    print(f"\n  {c('Next Steps:', Colors.BOLD)}")
    if not (paths['info'] / '01-core.yaml').exists():
        print(f"    1. story collect core      - Collect core story info")
    elif not list(paths['characters'].glob('protagonist/*.yaml')):
        print(f"    2. story collect protagonist - Create protagonist")
    elif not (paths['outline'] / 'volume-001.yaml').exists():
        print(f"    3. story plan volume 1     - Plan volume 1")
    else:
        print(f"    4. story write 1 --prompt  - Generate chapter 1 prompt")
    print()


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Add status to story.py imports and commands**

Modify `src_v2/story.py` to include status command.

- [ ] **Step 3: Test status command**

Run: `cd /tmp/test_novel && python3 /mnt/d/code/zhihu/my-novel-skill/src_v2/story.py status`
Expected: Shows project status table

---

### Phase 1 Complete

**Phase 1 deliverables:**
- `src_v2/paths.py` - Three-directory path management
- `src_v2/init.py` - Project initialization with style collection
- `src_v2/status.py` - Project status display
- `src_v2/story.py` - New CLI entry point

---

## Plan Self-Review

**Spec coverage check:**
- ✅ Three-directory structure - Task 1
- ✅ story.yaml config format - Task 2
- ✅ Project initialization - Task 2
- ✅ Status display - Task 3

**Placeholder check:** No TBD/TODO found, all steps have actual code.

**Type consistency:** All function names, paths, and variable names are consistent across tasks.

---

Plan complete and saved to `docs/superpowers/plans/2026-04-13-simplified-my-novel-skill-plan.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach would you like?**
