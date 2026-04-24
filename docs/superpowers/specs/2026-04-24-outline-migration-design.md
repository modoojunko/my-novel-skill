# 大纲迁移到 story.yaml 设计

## 背景

当前架构：
- `process/OUTLINE/volume-XXX/chapter-YYY.yaml` - 章节大纲（yaml 文件）
- `outlines.chapters."vol-ch"` - story.yaml 中章节大纲（新格式）

目标：迁移旧 yaml 文件到 story.yaml，实现单一数据源。

## 迁移格式转换

**源格式（yaml 文件）：**
```yaml
chapter: 3
volume: 1
title: "消失的现场"
pov: "第三人称旁白，林悦视角为主"
summary: |
  章节概要内容...
key_scenes:
  - "场景1: ..."
  - "场景2: ..."
```

**目标格式（story.yaml）：**
```yaml
outlines:
  chapters:
    "1-3":                  # "vol-ch" 格式 key
      summary: "章节概要内容..."
      key_scenes:
        - "场景1: ..."
        - "场景2: ..."
      chapter_info:
        number: 3
        volume: 1
        title: "消失的现场"
        pov: "第三人称旁白，林悦视角为主"
```

## 实现

### 1. migrate.py 新增 migrate_outlines 函数

```python
def migrate_outlines(paths: dict, config: dict, delete: bool = False) -> dict:
    """Migrate outline yaml files to story.yaml"""
    outline_dir = paths['outline']
    migrated = []
    errors = []

    for vol_dir in sorted(outline_dir.glob('volume-*')):
        vol_num = int(vol_dir.name.split('-')[1])
        for ch_file in sorted(vol_dir.glob('chapter-*.yaml')):
            ch_num = int(ch_file.name.split('-')[1].split('.')[0])
            try:
                data = load_yaml(ch_file)
                if data:
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
                    # Write to story.yaml
                    if 'outlines' not in config:
                        config['outlines'] = {}
                    if 'chapters' not in config['outlines']:
                        config['outlines']['chapters'] = {}
                    config['outlines']['chapters'][ch_key] = migrated_data
                    migrated.append(ch_key)
            except Exception as e:
                errors.append(f"{vol_num}-{ch_num}: {e}")

    if migrated:
        save_config(find_project_root(), config)

    return {'migrated': migrated, 'errors': errors, 'deleted': []}
```

### 2. story migrate 命令扩展

新增 `story migrate outlines` 子命令：
```bash
story migrate outlines        # 迁移大纲到 story.yaml
story migrate outlines --delete  # 迁移后删除 yaml 文件
```

### 3. 测试项目迁移

测试项目 `/mnt/d/novels/lingchen-647-v2/`：
- `process/OUTLINE/volume-001/chapter-001.yaml` ~ `chapter-010.yaml` (10 chapters)
- 迁移后写入 `story.yaml.outlines.chapters."1-1"` ~ `"1-10"`

## 修改文件

1. **src_v2/migrate.py** - 新增 `migrate_outlines` 函数
2. **src_v2/migrate.py** - 新增 `migrate` CLI 入口
3. **SKILL.md** - 命令参考表更新
4. **测试项目** - 执行迁移验证
