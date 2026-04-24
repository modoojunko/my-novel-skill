# 大纲迁移到 story.yaml 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `story migrate outlines` 命令，将 process/OUTLINE yaml 文件迁移到 story.yaml。

**Architecture:** 在 migrate.py 新增 migrate_outlines 函数，扫描 yaml 文件并转换格式写入 story.yaml。

**Tech Stack:** Python 3.8+，仅标准库

---

## Task 1: 新增 migrate_outlines 函数

**Files:**
- Modify: `src_v2/migrate.py`

- [ ] **Step 1: 添加 load_yaml 辅助函数（如没有）**

migrate.py 中已有 `_load_yaml_or_json`，检查是否可直接使用。如有 yaml 库则用 yaml.safe_load，否则用 json。

- [ ] **Step 2: 添加 migrate_outlines 函数**

在 `migrate_project` 函数之前添加：

```python
def migrate_outlines(paths: dict, config: dict, delete: bool = False) -> dict:
    """Migrate outline yaml files to story.yaml

    Args:
        paths: project paths dict
        config: story.yaml config dict (modified in place)
        delete: if True, delete yaml files after migration

    Returns:
        dict with 'migrated' (list of keys), 'errors' (list), 'deleted' (list)
    """
    outline_dir = paths['outline']
    migrated = []
    errors = []
    deleted = []

    # Scan volume directories
    for vol_dir in sorted(outline_dir.glob('volume-*')):
        if not vol_dir.is_dir():
            continue
        vol_num = int(vol_dir.name.split('-')[1])

        # Scan chapter yaml files
        for ch_file in sorted(vol_dir.glob('chapter-*.yaml')):
            ch_num = int(ch_file.stem.split('-')[1])
            try:
                data = _load_yaml_or_json(ch_file)
                if not data:
                    continue

                ch_key = f"{vol_num}-{ch_num}"

                # Convert to nested format
                migrated_data = {
                    'summary': data.get('summary', ''),
                    'key_scenes': data.get('key_scenes', []),
                    'chapter_info': {
                        'number': data.get('chapter'),
                        'volume': data.get('volume'),
                        'title': data.get('title', ''),
                        'pov': data.get('pov', ''),
                    }
                }

                # Write to config
                if 'outlines' not in config:
                    config['outlines'] = {}
                if 'chapters' not in config['outlines']:
                    config['outlines']['chapters'] = {}
                config['outlines']['chapters'][ch_key] = migrated_data
                migrated.append(ch_key)

                # Delete if requested
                if delete:
                    ch_file.unlink()
                    deleted.append(ch_key)

            except Exception as e:
                errors.append(f"{vol_num}-{ch_num}: {str(e)}")

    return {'migrated': migrated, 'errors': errors, 'deleted': deleted}
```

- [ ] **Step 3: 添加 outlines 子命令处理**

在 `main()` 函数中，找到处理逻辑的位置，添加：

在 `main()` 中解析 `sys.argv` 查找 `outlines` 子命令：

```python
# Check for outlines subcommand
if len(sys.argv) >= 2 and sys.argv[1] == 'outlines':
    # story migrate outlines [--delete]
    delete = '--delete' in sys.argv
    filtered = [a for a in sys.argv[2:] if a not in ('--delete', '--json', '--non-interactive')]
    sys.argv = ['story-migrate'] + filtered

    root = find_project_root()
    if not root:
        cli.error_message("Not in a novel project")
    config = load_config(root)
    paths = load_project_paths(root)

    result = migrate_outlines(paths, config, delete=delete)
    if result['migrated']:
        save_config(root, config)

    if cli.is_json_mode():
        cli.output_json(result)
    else:
        cli.print_out(f"  {cli.c(f'Migrated {len(result[\"migrated\"])} chapters', cli.Colors.GREEN)}")
        if result['errors']:
            cli.print_out(f"  {cli.c(f'Errors: {len(result[\"errors\"])}', cli.Colors.RED)}")
        if result['deleted']:
            cli.print_out(f"  {cli.c(f'Deleted {len(result[\"deleted\"])} files', cli.Colors.YELLOW)}")
    return
```

- [ ] **Step 4: 更新 show_migrate_help**

添加 outlines 命令说明：
```
  story migrate outlines        Migrate outline yaml files to story.yaml
  story migrate outlines --delete  Migrate and delete yaml files
```

- [ ] **Step 5: 验证语法**

Run: `python3 -c "import ast; ast.parse(open('src_v2/migrate.py').read()); print('Syntax OK')"`

- [ ] **Step 6: 提交**

```bash
git add src_v2/migrate.py
git commit -m "feat: story migrate outlines 迁移章节大纲到 story.yaml"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 2: 更新 SKILL.md 命令参考表

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: 添加 migrate 命令行**

在命令参考表中找到 `story migrate` 行（如有）并更新说明。

如果没有，在合适位置添加：
```
| `story migrate outlines [--delete]` | 迁移 outline yaml 到 story.yaml | 迁移旧项目大纲数据 |
```

- [ ] **Step 2: 提交**

```bash
git add SKILL.md
git commit -m "docs: SKILL.md 添加 migrate outlines 命令说明"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Task 3: 测试项目迁移验证

**Files:**
- Test: `/mnt/d/novels/lingchen-647-v2/`

- [ ] **Step 1: 运行迁移（不带 delete）**

```bash
cd /mnt/d/novels/lingchen-647-v2
python3 /home/zhuke/my-novel-skill/story.py migrate outlines
```

验证 story.yaml 中 outlines.chapters 有数据。

- [ ] **Step 2: 确认 yaml 文件保留**

检查 `process/OUTLINE/volume-001/chapter-*.yaml` 仍然存在。

- [ ] **Step 3: 运行 delete 迁移**

```bash
python3 /home/zhuke/my-novel-skill/story.py migrate outlines --delete
```

- [ ] **Step 4: 确认 yaml 文件已删除**

检查 `process/OUTLINE/volume-001/chapter-*.yaml` 已不存在。

- [ ] **Step 5: 验证 story write 3 --prompt 正常工作**

---

## 验证清单

- [ ] `migrate_outlines` 函数正确转换格式
- [ ] `story migrate outlines` 命令可执行
- [ ] `story migrate outlines --delete` 删除 yaml 文件
- [ ] SKILL.md 包含 migrate outlines 命令说明
- [ ] 测试项目迁移后 story write 3 --prompt 显示完整章节大纲
