#!/usr/bin/env python3
"""
story:archive - 定稿归档

参考 OpenSpec 的 archive 功能，将完成的章节归档。
使用 JSON 作为配置文件格式。
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"

def find_project_root():
    """查找项目根目录"""
    cwd = Path.cwd()
    current = cwd
    for _ in range(10):
        if (current / 'story.json').exists() or (current / 'story.yml').exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None

def load_config(root):
    """加载配置"""
    config_path = root / 'story.json'
    if not config_path.exists():
        config_path = root / 'story.yml'
    
    if config_path.suffix == '.json':
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

def save_config(root, config):
    """保存配置"""
    config_path = root / 'story.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def count_words(text: str) -> int:
    """统计字数"""
    chinese = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    english = len([w for w in text.split() if w.strip('.,!?;:()[]{}')])
    return chinese + english

def archive_chapter(root, config, chapter_num, dry_run=False):
    """归档章节"""
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = root / 'CONTENT' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'
    tasks_path = root / 'CONTENT' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.tasks.md'
    outline_path = root / 'OUTLINE' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'

    if not chapter_path.exists():
        print(f"  [ERROR] 章节 {chapter_num} 不存在，请先 story:write {chapter_num}")
        return False

    date_str = datetime.now().strftime('%Y-%m-%d')
    archive_name = f"{date_str}-chapter-{chapter_num:03d}"
    archive_dir = root / 'ARCHIVE' / archive_name
    archive_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print(f"  [DRY RUN] 将归档到：{archive_dir.relative_to(root)}")
        return True

    final_content = chapter_path.read_text(encoding='utf-8')
    word_count = count_words(final_content)
    final_path = archive_dir / 'final.md'
    final_path.write_text(final_content, encoding='utf-8')

    if tasks_path.exists():
        shutil.copy2(tasks_path, archive_dir / 'tasks.md')

    if outline_path.exists():
        shutil.copy2(outline_path, archive_dir / 'outline.md')

    delta_path = archive_dir / 'delta-spec.md'
    delta_content = f"""# 变更规格：第{chapter_num}章

## 变更日期
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 字数统计
- 正文：{word_count:,} 字

## 变更类型

### ADDED 内容
（新增的场景/情节）

### MODIFIED 内容
（修改的内容）

### REMOVED 内容
（删除的内容）

## 归档原因
（待填写）

## 后续计划
（待填写）
"""
    delta_path.write_text(delta_content, encoding='utf-8')

    meta = {
        'chapter': chapter_num,
        'volume': volume_num,
        'archived_at': datetime.now().isoformat(),
        'word_count': word_count,
        'files': []
    }
    for f in [final_path.name, 'tasks.md', 'outline.md', 'delta-spec.md']:
        if (archive_dir / f).exists():
            meta['files'].append(f)
    
    meta_path = archive_dir / '.meta.json'
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    if chapter_num not in config['progress']['archived_chapters']:
        config['progress']['archived_chapters'].append(chapter_num)

    book = config.get('book', {})
    current_words = book.get('current_words', 0)
    book['current_words'] = current_words + word_count
    config['book'] = book

    save_config(root, config)

    return True, archive_dir, word_count

def show_archive_preview(root, config, chapter_num):
    """显示归档预览"""
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1

    chapter_path = root / 'CONTENT' / f'volume-{volume_num}' / f'chapter-{chapter_num:03d}.md'

    if not chapter_path.exists():
        return False

    content = chapter_path.read_text(encoding='utf-8')
    word_count = count_words(content)

    print(f"""
================================================================================
                    [ARCHIVE] 归档预览：第{chapter_num}章
================================================================================

  归档位置：ARCHIVE/{datetime.now().strftime('%Y-%m-%d')}-chapter-{chapter_num:03d}/

  将包含：
    |-- final.md       最终版本
    |-- tasks.md       任务清单
    |-- outline.md     章节大纲
    |-- delta-spec.md   变更规格
    +-- .meta.json      元数据

  字数：{word_count:,} 字
""")

    return True

def main():
    import argparse

    parser = argparse.ArgumentParser(description='归档章节')
    parser.add_argument('chapter', nargs='?', type=int, help='章节号')
    parser.add_argument('--preview', '-p', action='store_true', help='预览归档')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行')

    args = parser.parse_args()

    root = find_project_root()
    if not root:
        print(f"  [ERROR] 未找到项目目录")
        sys.exit(1)

    config = load_config(root)

    chapter_num = args.chapter
    if not chapter_num:
        chapter_num = config['progress'].get('current_chapter', 0)
        if chapter_num == 0:
            print(f"  [ERROR] 未指定章节号")
            print(f"  用法：python story.py archive <章节号>")
            sys.exit(1)

    if args.preview:
        if show_archive_preview(root, config, chapter_num):
            return
        else:
            sys.exit(1)

    print(f"\n[ARCHIVE] 归档章节")
    print(f"  章节：第{chapter_num}章")
    print()

    result = archive_chapter(root, config, chapter_num, dry_run=args.dry_run)

    if result is True:
        if args.dry_run:
            print(f"\n  [OK] 模拟归档完成")
        else:
            print(f"\n  [OK] 归档完成！")
    elif isinstance(result, tuple):
        _, archive_dir, word_count = result
        print(f"\n  [OK] 归档完成！")
        print(f"  位置：{archive_dir.relative_to(root)}")
        print(f"  字数：{word_count:,}")
        print(f"  总字数：{config['book'].get('current_words', 0):,}")
    else:
        sys.exit(1)

    print()

if __name__ == '__main__':
    main()
