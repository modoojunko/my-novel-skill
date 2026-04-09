#!/usr/bin/env python3
"""
story:update-specs - 更新角色设定和检测新信息

功能：
1. 扫描章节内容，检测新揭示的角色名、信息
2. 自动更新角色设定文件中的"当前状态"章节
3. 同步更新 story.json 中的 pov_states 快照
4. 生成本章摘要供后续章节参考

Usage:
  story:update-specs <章节号>     # 扫描指定章节并更新设定
  story:update-specs --dry-run    # 预览变更，不实际写入
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from .paths import find_project_root, load_config, save_config, load_project_paths


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





def read_character_pov_state(root: Path, char_name: str, paths: dict = None) -> dict:
    """读取角色的POV认知状态"""
    if paths is None:
        paths = load_project_paths(root)
    char_file = paths['characters'] / f'{char_name}.md'
    if not char_file.exists():
        return {}
    
    content = char_file.read_text(encoding='utf-8')
    
    # 查找"当前状态"章节
    state_start = content.find('## 当前状态')
    if state_start == -1:
        return {}
    
    state_section = content[state_start:]
    
    # 解析已知角色表格
    known_chars = []
    unknown_chars = []
    known_info = []
    pending_reveals = []
    
    # 解析已知角色表格
    table_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
    matches = re.findall(table_pattern, state_section)
    for match in matches:
        name, relation, source, chapter = match
        if name.strip() and name.strip() != '角色':
            known_chars.append({
                'name': name.strip(),
                'relationship': relation.strip(),
                'source': source.strip(),
                'chapter': chapter.strip()
            })
    
    # 解析未知角色列表
    unknown_pattern = r'-\s*\[\s*\]\s*([^\n]+)'
    unknown_matches = re.findall(unknown_pattern, state_section)
    for match in unknown_matches:
        char_name_clean = match.split('（')[0].split('(')[0].strip()
        if char_name_clean:
            unknown_chars.append(char_name_clean)
    
    # 解析已掌握信息
    info_section = state_section.find('### 已掌握信息')
    pending_section = state_section.find('### 待揭示信息')
    
    if info_section != -1:
        info_end = pending_section if pending_section != -1 else len(state_section)
        info_text = state_section[info_section:info_end]
        info_items = re.findall(r'-\s+(.+)', info_text)
        known_info = [item.strip() for item in info_items if item.strip()]
    
    if pending_section != -1:
        pending_text = state_section[pending_section:]
        pending_items = re.findall(r'-\s*\[\s*\]\s+(.+)', pending_text)
        pending_reveals = [item.strip() for item in pending_items if item.strip()]
    
    return {
        'known_characters': known_chars,
        'unknown_characters': unknown_chars,
        'known_info': known_info,
        'pending_reveals': pending_reveals
    }


def update_character_pov_state(root: Path, char_name: str, new_known_char: dict = None,
                               new_known_info: str = None, revealed_item: str = None,
                               paths: dict = None) -> bool:
    """更新角色设定文件中的当前状态"""
    if paths is None:
        paths = load_project_paths(root)
    char_file = paths['characters'] / f'{char_name}.md'
    if not char_file.exists():
        return False
    
    content = char_file.read_text(encoding='utf-8')
    
    # 查找"当前状态"章节
    state_start = content.find('## 当前状态')
    if state_start == -1:
        return False
    
    # 添加新已知角色
    if new_known_char:
        # 在已知角色表格后添加新行
        table_end = content.find('\n\n### 未知', state_start)
        if table_end == -1:
            table_end = content.find('\n\n### 已掌握', state_start)
        
        if table_end != -1:
            new_row = f"| {new_known_char['name']} | {new_known_char['relationship']} | {new_known_char['source']} | {new_known_char['chapter']} |\n"
            content = content[:table_end] + new_row + content[table_end:]
        
        # 从未知列表中移除
        if new_known_char['name'] in str(content):
            unknown_pattern = rf"- \[ \] {re.escape(new_known_char['name'])}[^\n]*\n"
            content = re.sub(unknown_pattern, '', content)
    
    # 添加新已知信息
    if new_known_info:
        info_section = content.find('### 已掌握信息', state_start)
        pending_section = content.find('### 待揭示信息', state_start)
        
        if info_section != -1:
            insert_pos = pending_section if pending_section != -1 else len(content)
            new_info_line = f"- {new_known_info}\n"
            # 检查是否已存在
            if new_known_info not in content[info_section:insert_pos]:
                content = content[:insert_pos] + new_info_line + content[insert_pos:]
    
    # 标记待揭示项为已揭示
    if revealed_item:
        pending_pattern = rf"(- \[ \] {re.escape(revealed_item)})"
        content = re.sub(pending_pattern, r"- [x] \2（已揭示）", content)
    
    char_file.write_text(content, encoding='utf-8')
    return True


def scan_chapter_for_revelations(root: Path, chapter_num: int, volume_num: int, paths: dict = None) -> dict:
    """扫描章节内容，检测新揭示的信息"""
    if paths is None:
        paths = load_project_paths(root)
    chapter_path = paths['output_dir'] / f'volume-{volume_num:03d}' / f'chapter-{chapter_num:03d}.md'
    outline_path = root / 'OUTLINE' / f'volume-{volume_num:03d}' / f'chapter-{chapter_num:03d}.md'
    
    if not chapter_path.exists():
        return None
    
    content = chapter_path.read_text(encoding='utf-8')
    
    # 从细纲获取POV角色
    pov_char = None
    if outline_path.exists():
        outline = outline_path.read_text(encoding='utf-8')
        pov_match = re.search(r'POV[:：]\s*(\S+)', outline)
        if pov_match:
            pov_char = pov_match.group(1).strip()
    
    if not pov_char:
        return None
    
    # 获取该POV角色的当前状态
    current_state = read_character_pov_state(root, pov_char, paths=paths)
    
    revelations = {
        'pov_character': pov_char,
        'new_known_characters': [],
        'new_known_info': [],
        'revealed_pending': []
    }
    
    # 检查未知角色是否被揭示
    for unknown_char in current_state.get('unknown_characters', []):
        # 简单检测：角色名是否出现在正文中
        # 注意：这只是一个启发式检测，可能需要人工确认
        if unknown_char in content:
            # 检查是否有获知途径的上下文
            # 例如：学生证、自我介绍、他人称呼等
            source = "未知途径"  # 默认
            
            # 启发式检测获知途径
            if '学生证' in content and unknown_char in content[max(0, content.find('学生证')-100):content.find('学生证')+100]:
                source = "学生证"
            elif '自我介绍' in content or '我叫' in content:
                source = "自我介绍"
            elif '说' in content or '问' in content:
                source = "他人称呼"
            
            revelations['new_known_characters'].append({
                'name': unknown_char,
                'source': source
            })
    
    # 检查待揭示信息是否被揭示
    for pending in current_state.get('pending_reveals', []):
        # 提取关键词进行匹配
        keywords = pending.split('的')
        if len(keywords) >= 2:
            keyword = keywords[1].strip() if len(keywords) > 1 else keywords[0].strip()
            if keyword and keyword in content:
                revelations['revealed_pending'].append(pending)
    
    return revelations


def generate_chapter_summary(root: Path, chapter_num: int, volume_num: int, paths: dict = None) -> str:
    """生成本章摘要"""
    if paths is None:
        paths = load_project_paths(root)
    chapter_path = paths['output_dir'] / f'volume-{volume_num:03d}' / f'chapter-{chapter_num:03d}.md'
    outline_path = root / 'OUTLINE' / f'volume-{volume_num:03d}' / f'chapter-{chapter_num:03d}.md'
    
    if not chapter_path.exists():
        return ""
    
    content = chapter_path.read_text(encoding='utf-8')
    outline = ""
    if outline_path.exists():
        outline = outline_path.read_text(encoding='utf-8')
    
    # 统计字数
    word_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    
    # 提取标题
    title_match = re.search(r'# 第\d+章[：:]\s*(.+)', content)
    title = title_match.group(1).strip() if title_match else "未命名"
    
    summary = f"""# 第{chapter_num}章摘要

## 基本信息
- **标题**：{title}
- **字数**：约 {word_count} 字
- **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 本章大纲
{outline[:500] if outline else "（无细纲）"}

## 关键事件
（待人工填写）

## 新揭示信息
（待人工填写）

## 伏笔/钩子
（待人工填写）

## 后续衔接建议
（待人工填写）
"""
    return summary


def update_story_json_pov_states(root: Path, paths: dict = None):
    """更新 story.json 中的 pov_states 快照"""
    if paths is None:
        paths = load_project_paths(root)
    config = load_config(root)

    chars_dir = paths['characters']
    if not chars_dir.exists():
        return
    
    if 'pov_states' not in config:
        config['pov_states'] = {}
    
    for char_file in chars_dir.glob('*.md'):
        char_name = char_file.stem
        state = read_character_pov_state(root, char_name, paths=paths)
        if state:
            config['pov_states'][char_name] = state
    
    save_config(root, config)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='更新角色设定和检测新信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  story:update-specs 5              # 扫描第5章并更新设定
  story:update-specs 5 --dry-run    # 预览变更，不实际写入
        """
    )
    parser.add_argument('chapter', nargs='?', type=int, help='章节号')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='预览变更，不实际写入文件')
    parser.add_argument('--summary', '-s', action='store_true',
                        help='同时生成章节摘要')
    
    args = parser.parse_args()
    
    root = find_project_root()
    if not root:
        print(c("[ERROR] 未找到项目目录", Colors.RED))
        sys.exit(1)

    config = load_config(root)
    paths = load_project_paths(root)
    
    if not args.chapter:
        print(c("[ERROR] 请指定章节号，如 story:update-specs 5", Colors.RED))
        sys.exit(1)
    
    chapter_num = args.chapter
    chapters_per = config.get('structure', {}).get('chapters_per_volume', 30)
    volume_num = ((chapter_num - 1) // chapters_per) + 1
    
    print(f"\n{c('[UPDATE-SPECS]', Colors.CYAN)} 更新角色设定")
    print(f"  章节：第 {chapter_num} 章")
    print(f"  卷：第 {volume_num} 卷")
    if args.dry_run:
        print(f"  模式：{c('预览模式（不写入文件）', Colors.YELLOW)}")
    print()
    
    # 扫描章节
    revelations = scan_chapter_for_revelations(root, chapter_num, volume_num, paths=paths)
    
    if not revelations:
        print(c("  未检测到新揭示信息，或章节文件不存在", Colors.YELLOW))
        return
    
    pov_char = revelations['pov_character']
    print(f"  POV角色：{pov_char}")
    print()
    
    # 显示检测结果
    has_updates = False
    
    if revelations['new_known_characters']:
        has_updates = True
        print(c("  [检测] 新获知角色：", Colors.GREEN))
        for char in revelations['new_known_characters']:
            print(f"    + {char['name']}（通过{char['source']}获知）")
    
    if revelations['revealed_pending']:
        has_updates = True
        print(c("  [检测] 待揭示项已揭示：", Colors.GREEN))
        for item in revelations['revealed_pending']:
            print(f"    ✓ {item}")
    
    if not has_updates:
        print(c("  未检测到需要更新的内容", Colors.DIM))
    
    print()
    
    # 应用更新
    if not args.dry_run and has_updates:
        print(c("  [更新] 正在更新角色设定文件...", Colors.CYAN))
        
        for char in revelations['new_known_characters']:
            update_character_pov_state(
                root, pov_char,
                new_known_char={
                    'name': char['name'],
                    'relationship': '未知关系',
                    'source': char['source'],
                    'chapter': f'第{chapter_num}章'
                },
                paths=paths
            )
            print(f"    ✓ 已添加 {char['name']} 到已知角色列表")
        
        for item in revelations['revealed_pending']:
            update_character_pov_state(root, pov_char, revealed_item=item, paths=paths)
            print(f"    ✓ 已标记 '{item}' 为已揭示")
        
        # 更新 story.json 快照
        update_story_json_pov_states(root, paths=paths)
        print(f"    ✓ 已更新 story.json 中的 pov_states")
        
        print()
        print(c("  [完成] 角色设定已更新", Colors.GREEN))
    
    # 生成摘要
    if args.summary:
        summary = generate_chapter_summary(root, chapter_num, volume_num, paths=paths)
        summary_dir = paths['summaries']
        summary_dir.mkdir(exist_ok=True)
        summary_path = summary_dir / f'chapter-{chapter_num:03d}-summary.md'
        
        if not args.dry_run:
            summary_path.write_text(summary, encoding='utf-8')
        
        print()
        print(c(f"  [摘要] 已生成章节摘要：{summary_path.relative_to(root)}", Colors.CYAN))
    
    print()


if __name__ == '__main__':
    main()
