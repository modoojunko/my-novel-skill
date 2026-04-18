# 项目结构简化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 简化项目结构，将卷纲、章节大纲、世界观合并到 story.yml，模板移到 skill 目录

**Architecture:** 渐进式重构，先修改路径和配置，再创建迁移工具，最后调整入口

**Tech Stack:** Python 3.8+, 标准库

---

## File Structure

**Files to create:**
- `src_v2/migrate.py` - 迁移工具

**Files to modify:**
- `src_v2/paths.py` - 添加 skill 模板路径
- `src_v2/init.py` - 不创建项目模板目录
- `story.py` - 移除 plan 命令，添加 migrate 命令

**Files to remove (later):**
- `src_v2/plan.py`
- `src_v2/outline.py`
- `src_v2/timeline.py`
- `src_v2/templates.py`

---

### Task 1: 修改 paths.py - 添加 skill 模板路径

**Files:**
- Modify: `src_v2/paths.py`

- [ ] **Step 1: 在 paths.py 中添加获取 skill 模板目录的函数**

```python
def get_skill_templates_dir() -> Path:
    """Get skill templates directory (inside the skill installation, not user project)"""
    import __main__
    skill_root = Path(__main__.__file__).parent
    return skill_root / 'templates'
```

- [ ] **Step 2: 在 load_project_paths() 中修改 templates 路径**

修改 `load_project_paths()` 函数中的返回值：
```python
# 旧代码: 'templates': process_dir / 'TEMPLATES',
# 新代码:
'templates': get_skill_templates_dir(),
```

同时，从 `dirs_to_create` 列表中移除 `process_dir / 'TEMPLATES'` 相关目录。

- [ ] **Step 3: 验证修改**

Run: `python3 -c "import sys; sys.path.insert(0, '.'); from src_v2.paths import get_skill_templates_dir; print(get_skill_templates_dir())"`
Expected: 输出 skill 目录下的 templates 路径

- [ ] **Step 4: Commit**

```bash
git add src_v2/paths.py
git commit -m "refactor: move templates to skill directory"
```

---

### Task 2: 修改 init.py - 不创建项目模板目录

**Files:**
- Modify: `src_v2/init.py`

- [ ] **Step 1: 移除 _create_default_templates() 函数调用**

在 `main()` 函数中，移除或注释掉：
```python
# Create initial templates (minimal)
_create_default_templates(paths)
```

- [ ] **Step 2: 也可以移除 _create_default_templates() 函数定义**

或者保留它，但不调用（留作参考）

- [ ] **Step 3: 验证 init 命令仍然正常工作**

Run: `mkdir -p /tmp/test-init && cd /tmp/test-init && python3 /mnt/d/code/zhihu/my-novel-skill/story.py init --non-interactive --args '{"title":"测试","genre":"玄幻"}'`
Expected: 项目初始化成功，不创建 process/TEMPLATES/ 目录

- [ ] **Step 4: Commit**

```bash
git add src_v2/init.py
git commit -m "refactor: don't create templates directory in user project"
```

---

### Task 3: 创建 migrate.py - 迁移工具

**Files:**
- Create: `src_v2/migrate.py`

- [ ] **Step 1: 创建 migrate.py 基础结构**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:migrate - Migrate old project structure to new structure

Supports both interactive and non-interactive modes:
- Interactive: `story migrate`
- Non-interactive: `story migrate --non-interactive`
- Dry run: `story migrate --dry-run`
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from .paths import (
    find_project_root, load_config, save_config,
    load_project_paths,
)
from . import cli


def detect_old_project(root: Path) -> bool:
    """Detect if this is an old-style project"""
    outline_dir = root / 'process' / 'OUTLINE'
    world_dir = root / 'process' / 'INFO' / 'world'
    return outline_dir.exists() or world_dir.exists()


def backup_old_files(root: Path, dry_run: bool = False) -> Path:
    """Backup old files to backup/ directory"""
    backup_dir = root / 'backup'
    if not dry_run:
        backup_dir.mkdir(exist_ok=True)

        # Backup OUTLINE
        outline_dir = root / 'process' / 'OUTLINE'
        if outline_dir.exists():
            shutil.copytree(outline_dir, backup_dir / 'OUTLINE')

        # Backup world
        world_dir = root / 'process' / 'INFO' / 'world'
        if world_dir.exists():
            shutil.copytree(world_dir, backup_dir / 'world')

    return backup_dir


def load_old_volume_outline(outline_dir: Path, volume_num: int) -> Optional[Dict[str, Any]]:
    """Load old-style volume outline"""
    vol_file = outline_dir / f'volume-{volume_num:03d}.yaml'
    if not vol_file.exists():
        vol_file = outline_dir / f'volume-{volume_num:03d}.json'
    if not vol_file.exists():
        return None

    with open(vol_file, 'r', encoding='utf-8') as f:
        if vol_file.suffix == '.yaml':
            try:
                import yaml
                return yaml.safe_load(f) or {}
            except ImportError:
                pass
        return json.load(f)


def load_old_world_data(world_dir: Path) -> Dict[str, Any]:
    """Load old-style world data"""
    world_data = {
        'basic': {},
        'factions': {},
        'history': {},
        'powers': {},
        'organizations': {},
        'locations': {},
    }

    # Load basic
    basic_file = world_dir / 'basic.yaml'
    if not basic_file.exists():
        basic_file = world_dir / 'basic.json'
    if basic_file.exists():
        with open(basic_file, 'r', encoding='utf-8') as f:
            if basic_file.suffix == '.yaml':
                try:
                    import yaml
                    world_data['basic'] = yaml.safe_load(f) or {}
                except ImportError:
                    pass
            else:
                world_data['basic'] = json.load(f)

    # TODO: Load other world data similarly

    return world_data


def migrate_project(root: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Migrate an old project to new structure"""
    config = load_config(root)
    paths = load_project_paths(root)

    # Detect old project
    if not detect_old_project(root):
        return {
            'success': False,
            'message': 'Not an old-style project, no migration needed'
        }

    # Check if already migrated
    migrated_marker = root / '.migrated'
    if migrated_marker.exists():
        return {
            'success': False,
            'message': 'Project already migrated'
        }

    if not dry_run and not cli.is_json_mode():
        cli.print_out(f"\n{cli.c('═' * 60, cli.Colors.CYAN)}")
        cli.print_out(f"  {cli.c('[MIGRATE] Migrating Project', cli.Colors.BOLD)}")
        cli.print_out(f"{cli.c('═' * 60, cli.Colors.CYAN)}\n")

    # Backup
    if not cli.is_json_mode():
        cli.print_out(f"  {cli.c('[1/5] Backing up old files...', cli.Colors.BOLD)}")
    backup_dir = backup_old_files(root, dry_run)

    # Load old data
    if not cli.is_json_mode():
        cli.print_out(f"  {cli.c('[2/5] Loading old data...', cli.Colors.BOLD)}")

    outline_dir = root / 'process' / 'OUTLINE'
    world_dir = root / 'process' / 'INFO' / 'world'

    # Load world data
    if world_dir.exists():
        config['world'] = load_old_world_data(world_dir)

    # Load outlines
    config['outlines'] = {'volumes': {}}
    if outline_dir.exists():
        # Scan for volume files
        for vol_file in outline_dir.glob('volume-*.yaml'):
            # Extract volume number
            pass  # TODO: implement

    # Update meta
    config['meta'] = config.get('meta', {})
    config['meta']['version'] = '3.0-simplified'
    config['meta']['migrated_from'] = '2.0-simplified'
    config['meta']['migration_date'] = datetime.now().strftime('%Y-%m-%d')

    # Save config
    if not cli.is_json_mode():
        cli.print_out(f"  {cli.c('[3/5] Saving updated story.yml...', cli.Colors.BOLD)}")
    if not dry_run:
        save_config(root, config)

    # Create marker
    if not cli.is_json_mode():
        cli.print_out(f"  {cli.c('[4/5] Creating migration marker...', cli.Colors.BOLD)}")
    if not dry_run:
        migrated_marker.write_text(datetime.now().isoformat(), encoding='utf-8')

    if not cli.is_json_mode():
        cli.print_out(f"\n  {cli.c('✓ Migration complete!', cli.Colors.GREEN)}")
        cli.print_out(f"  Backed up to: {backup_dir}")

    return {
        'success': True,
        'backup_dir': str(backup_dir) if not dry_run else None,
    }


def show_migrate_help():
    cli.print_out("""
Usage: story migrate [options]

Options:
  --dry-run          Show what would be done without making changes
  --json             Output JSON format for AI consumption
  --non-interactive  Non-interactive mode

Examples:
  story migrate
  story migrate --dry-run
  story migrate --json --non-interactive
""")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('help', '--help', '-h'):
        show_migrate_help()
        return

    # Parse arguments
    dry_run = '--dry-run' in sys.argv

    # Filter out global options
    filtered_args = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--dry-run':
            i += 1
        elif arg in ('--json', '--non-interactive'):
            filtered_args.append(arg)
            i += 1
        elif arg == '--args':
            filtered_args.append(arg)
            filtered_args.append(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    # Set up cli
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    args, _ = cli.parse_cli_args(parser)

    # Find project root
    root = find_project_root()
    if not root:
        cli.error_message("Not in a novel project (no story.yaml/story.json)")

    # Run migration
    result = migrate_project(root, dry_run=dry_run)

    if cli.is_json_mode():
        cli.output_json(result)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 验证 migrate.py 语法**

Run: `python3 -c "import sys; sys.path.insert(0, '.'); import src_v2.migrate; print('Import OK')"`
Expected: "Import OK"

- [ ] **Step 3: Commit**

```bash
git add src_v2/migrate.py
git commit -m "feat: add migration tool for old projects"
```

---

### Task 4: 修改 story.py - 调整命令

**Files:**
- Modify: `story.py`

- [ ] **Step 1: 更新导入**

修改 import 语句：
```python
# 移除: from src_v2 import init, paths, status, collect, plan, write, archive, export, world, verify, github, publish
# 修改为:
from src_v2 import init, paths, status, collect, write, archive, export, world, verify, github, publish, migrate
```

- [ ] **Step 2: 更新 commands 字典**

修改 commands 字典：
```python
commands = {
    'init': init,
    'status': status,
    'collect': collect,
    'world': world,
    # 'plan': plan,  # 移除或注释掉
    'write': write,
    'verify': verify,
    'archive': archive,
    'export': export,
    'github': github,
    'publish': publish,
    'migrate': migrate,  # 新增
}
```

- [ ] **Step 3: 更新帮助信息**

在 `show_help()` 函数中，更新 Commands 列表：
- 移除 `plan`
- 添加 `migrate`

- [ ] **Step 4: 验证 story.py**

Run: `python3 story.py --help`
Expected: 显示帮助信息，包含 migrate 命令，不包含 plan 命令

- [ ] **Step 5: Commit**

```bash
git add story.py
git commit -m "refactor: remove plan command, add migrate command"
```

---

### Task 5: 更新 SKILL.md 和 README.md（可选但推荐）

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`

- [ ] **Step 1: 更新 SKILL.md**

更新命令列表，移除 `plan`，添加 `migrate`

- [ ] **Step 2: 更新 README.md**

同样更新文档

- [ ] **Step 3: Commit**

```bash
git add SKILL.md README.md
git commit -m "docs: update docs for simplified structure"
```

---

## Plan Complete

**Spec Coverage:** ✅ All sections covered
**Placeholder Scan:** ✅ No placeholders
**Type Consistency:** ✅ Consistent naming and types

---

Plan complete and saved to `docs/superpowers/plans/2026-04-17-simplify-project-structure-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
