#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
story:publish - Publish chapters to multiple platforms
"""
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from .paths import find_project_root, load_config, save_config, load_project_paths
from . import cli
from .publishing import get_registry, PublishResult
from .progress import load_progress, get_chapter_status


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.ENDC}"


def compute_content_hash(content: str) -> str:
    """计算内容 SHA-256 哈希"""
    return "sha256:" + hashlib.sha256(content.encode('utf-8')).hexdigest()


def get_publishing_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """获取 publishing 配置，如果不存在则初始化"""
    if 'publishing' not in config:
        config['publishing'] = {
            'chapters': {},
            'platforms': {}
        }
    return config['publishing']


def get_chapter_publish_status(publishing: Dict[str, Any], chapter_num: int, platform: str) -> Optional[Dict[str, Any]]:
    """获取章节在指定平台的发布状态"""
    chapters = publishing.get('chapters', {})
    chapter_key = str(chapter_num)
    if chapter_key not in chapters:
        return None
    return chapters[chapter_key].get(platform)


def set_chapter_publish_status(
    config: Dict[str, Any],
    chapter_num: int,
    platform: str,
    status: str,
    url: Optional[str] = None,
    error_message: Optional[str] = None,
    content_hash: Optional[str] = None,
    previous_hash: Optional[str] = None
) -> Dict[str, Any]:
    """设置章节发布状态"""
    publishing = get_publishing_config(config)
    chapters = publishing.setdefault('chapters', {})
    chapter_key = str(chapter_num)

    if chapter_key not in chapters:
        chapters[chapter_key] = {}

    chapter_status = {
        'status': status,
        'published_at': datetime.now().isoformat()
    }

    if url:
        chapter_status['url'] = url
    if error_message:
        chapter_status['error_message'] = error_message
    if content_hash:
        chapter_status['content_hash'] = content_hash
    if previous_hash:
        chapter_status['previous_hash'] = previous_hash

    chapters[chapter_key][platform] = chapter_status
    return config


class PublishingManager:
    """发布统一管理器"""

    def __init__(self, root: Path, config: Dict[str, Any], paths: Dict[str, Any]):
        self.root = root
        self.config = config
        self.paths = paths
        self.registry = get_registry()
        self.publishing = get_publishing_config(config)

    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """获取平台配置"""
        platforms = self.publishing.get('platforms', {})
        return platforms.get(platform, {})

    def set_platform_config(self, platform: str, platform_config: Dict[str, Any]) -> None:
        """设置平台配置"""
        platforms = self.publishing.setdefault('platforms', {})
        platforms[platform] = platform_config

    def get_adapter(self, platform: str):
        """获取并配置平台适配器"""
        adapter = self.registry.get(platform)
        if not adapter:
            return None

        # 如果适配器有 set_config 方法，设置配置
        platform_config = self.get_platform_config(platform)
        if hasattr(adapter, 'set_config'):
            adapter.set_config(platform_config)

        return adapter

    def load_chapter_content(self, chapter_num: int) -> Optional[str]:
        """加载已归档的章节内容"""
        # 先从 archive 目录找
        ch_name = f'chapter-{chapter_num:03d}.md'
        archive_file = self.paths['archive'] / ch_name

        if archive_file.exists():
            with open(archive_file, 'r', encoding='utf-8') as f:
                return f.read()

        # 如果 archive 没有，从 content 目录找
        structure = self.config.get('structure', {})
        chapters_per_volume = structure.get('chapters_per_volume', 30)
        volume_num = ((chapter_num - 1) // chapters_per_volume) + 1

        vol_name = f'volume-{volume_num:03d}'
        content_file = self.paths['content'] / vol_name / ch_name

        if content_file.exists():
            with open(content_file, 'r', encoding='utf-8') as f:
                return f.read()

        return None

    def should_publish(self, chapter_num: int, platform: str, content: str, force: bool = False) -> tuple[bool, Optional[str]]:
        """
        判断是否需要发布

        Returns:
            (should_publish, reason)
        """
        if force:
            return True, "强制发布"

        status = get_chapter_publish_status(self.publishing, chapter_num, platform)

        if not status:
            return True, "从未发布过"

        current_status = status.get('status')
        if current_status == 'failed':
            return True, "上次发布失败"

        content_hash = compute_content_hash(content)
        saved_hash = status.get('content_hash')

        if content_hash != saved_hash:
            return True, "内容已变更"

        return False, "内容未变更，且已成功发布"

    def publish_chapter(self, chapter_num: int, platform: str, force: bool = False) -> PublishResult:
        """发布单个章节"""
        # 获取适配器
        adapter = self.get_adapter(platform)
        if not adapter:
            return PublishResult(False, error_message=f"未知平台: {platform}")

        # 检查平台可用性
        if not adapter.is_available():
            return PublishResult(False, error_message=f"{adapter.display_name} 不可用，请检查 CLI 安装")

        # 加载章节内容
        content = self.load_chapter_content(chapter_num)
        if not content:
            return PublishResult(False, error_message=f"章节 {chapter_num} 内容未找到，请先归档")

        # 判断是否需要发布
        should_pub, reason = self.should_publish(chapter_num, platform, content, force)
        if not should_pub:
            return PublishResult(False, error_message=f"跳过发布: {reason}")

        # 获取现有状态
        existing_status = get_chapter_publish_status(self.publishing, chapter_num, platform)
        existing_url = existing_status.get('url') if existing_status else None
        previous_hash = existing_status.get('content_hash') if existing_status else None

        # 准备元数据
        structure = self.config.get('structure', {})
        chapters_per_volume = structure.get('chapters_per_volume', 30)
        volume_num = ((chapter_num - 1) // chapters_per_volume) + 1

        metadata = {
            'chapter_num': chapter_num,
            'volume_num': volume_num,
            'title': f"第{chapter_num}章"
        }

        # 转换内容
        converted_content = adapter.convert_content(content, chapter_num, metadata)

        # 发布
        result = adapter.publish_chapter(converted_content, chapter_num, metadata, existing_url)

        # 更新状态
        content_hash = compute_content_hash(content)

        if result.success:
            new_status = 'updated' if existing_status and existing_status.get('status') == 'published' else 'published'
            self.config = set_chapter_publish_status(
                self.config, chapter_num, platform, new_status,
                url=result.url, content_hash=content_hash,
                previous_hash=previous_hash if new_status == 'updated' else None
            )
        else:
            self.config = set_chapter_publish_status(
                self.config, chapter_num, platform, 'failed',
                error_message=result.error_message, content_hash=content_hash
            )

        # 保存配置
        save_config(self.root, self.config)

        return result

    def publish_all(self, platform: str, force: bool = False) -> List[tuple[int, PublishResult]]:
        """发布所有未发布的已归档章节"""
        # 获取所有已归档章节
        progress = load_progress(self.paths['process'])
        completed = progress.get('completed_chapters', [])

        results = []
        for chapter_num in completed:
            result = self.publish_chapter(chapter_num, platform, force)
            results.append((chapter_num, result))

        return results


def show_publish_help():
    print("""
Usage: story publish <target> <platform> [options]

Targets:
  <chapter_num>          Publish a single chapter (e.g., 5)
  all                    Publish all archived chapters

Commands:
  status                 Show publishing status
  check <platform>       Check if platform is available

Options:
  --force                Force publish even if already published
  --json                 Output JSON format
  --non-interactive      Non-interactive mode

Examples:
  story publish 1 feishu
  story publish all feishu
  story publish status
  story publish check feishu
""")


def main():
    if len(sys.argv) < 2:
        show_publish_help()
        return

    # Check for help first
    if sys.argv[1] in ('help', '--help', '-h'):
        show_publish_help()
        return

    # First, extract --json, --non-interactive, --args from anywhere in args
    # and set cli module's global state manually
    json_mode = '--json' in sys.argv
    non_interactive = '--non-interactive' in sys.argv

    # Find and parse --args if present
    args_dict = {}
    if '--args' in sys.argv:
        args_idx = sys.argv.index('--args')
        if args_idx + 1 < len(sys.argv):
            try:
                import json
                args_dict = json.loads(sys.argv[args_idx + 1])
            except json.JSONDecodeError:
                pass

    # Set cli module's global state manually
    cli._json_mode = json_mode
    cli._non_interactive = non_interactive
    cli._args = args_dict

    # Now filter out the global options and process subcommand
    filtered_args = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ('--json', '--non-interactive'):
            i += 1
        elif arg == '--args':
            i += 2
        else:
            filtered_args.append(arg)
            i += 1

    if not filtered_args:
        show_publish_help()
        return

    target = filtered_args[0].lower()

    # Find project root
    root = find_project_root()
    if not root:
        cli.print_out("  Error: Not in a novel project (no story.yaml/story.json)")
        cli.print_out("  Run 'story init' first")
        return

    config = load_config(root)
    paths = load_project_paths(root)

    # Parse options
    force = '--force' in sys.argv

    # Handle status command
    if target == 'status':
        show_publishing_status(config, paths, filtered_args[1:])
        return

    # Handle check command
    if target == 'check':
        if len(filtered_args) < 2:
            show_publish_help()
            return
        platform = filtered_args[1]
        check_platform(platform, root, config, paths)
        return

    # Handle publish commands
    if len(filtered_args) < 2:
        show_publish_help()
        return

    platform = filtered_args[1]

    if cli.is_interactive() or not cli.is_json_mode():
        print(f"\n{c('═' * 60, Colors.BOLD)}")
        print(f"  {c('[PUBLISH]', Colors.BOLD)}")
        print(f"{c('═' * 60, Colors.BOLD)}\n")

    manager = PublishingManager(root, config, paths)

    if target == 'all':
        # Publish all
        results = manager.publish_all(platform, force)

        if cli.is_json_mode():
            json_results = []
            for ch_num, result in results:
                json_results.append({
                    'chapter': ch_num,
                    'success': result.success,
                    'url': result.url,
                    'error': result.error_message
                })
            cli.output_json({'success': True, 'results': json_results})
        else:
            success_count = sum(1 for _, r in results if r.success)
            print(f"  发布完成: {success_count}/{len(results)} 成功")
            for ch_num, result in results:
                if result.success:
                    status = c("✓", Colors.GREEN)
                    url = f" ({result.url})" if result.url else ""
                    print(f"    {status} 章节 {ch_num}{url}")
                else:
                    status = c("✗", Colors.RED)
                    print(f"    {status} 章节 {ch_num}: {result.error_message}")

    elif target.isdigit():
        # Publish single chapter
        chapter_num = int(target)
        result = manager.publish_chapter(chapter_num, platform, force)

        if cli.is_json_mode():
            cli.output_json({
                'success': result.success,
                'url': result.url,
                'error': result.error_message
            })
        else:
            if result.success:
                print(f"  {c('✓ 发布成功!', Colors.GREEN)}")
                if result.url:
                    print(f"  地址: {result.url}")
            else:
                print(f"  {c('✗ 发布失败', Colors.RED)}")
                print(f"  原因: {result.error_message}")

    else:
        show_publish_help()


def show_publishing_status(config: Dict[str, Any], paths: Dict[str, Any], filtered_args: List[str]):
    """显示发布状态"""
    publishing = get_publishing_config(config)
    chapters = publishing.get('chapters', {})

    if cli.is_interactive() or not cli.is_json_mode():
        print(f"\n{c('═' * 60, Colors.BOLD)}")
        print(f"  {c('[PUBLISH STATUS]', Colors.BOLD)}")
        print(f"{c('═' * 60, Colors.BOLD)}\n")

    # Filter by chapter or platform if specified
    filter_chapter = None
    filter_platform = None
    for arg in filtered_args:
        if arg.isdigit():
            filter_chapter = int(arg)
        else:
            filter_platform = arg

    if cli.is_json_mode():
        # Output JSON
        output = {}
        for ch_key, platforms in chapters.items():
            if filter_chapter and int(ch_key) != filter_chapter:
                continue
            chapter_output = {}
            for platform, status in platforms.items():
                if filter_platform and platform != filter_platform:
                    continue
                chapter_output[platform] = status
            if chapter_output:
                output[ch_key] = chapter_output
        cli.output_json({'success': True, 'status': output})
    else:
        # Output human-readable
        registry = get_registry()

        for ch_key in sorted(chapters.keys(), key=int):
            if filter_chapter and int(ch_key) != filter_chapter:
                continue

            platforms = chapters[ch_key]
            print(f"  {c(f'章节 {ch_key}:', Colors.BOLD)}")

            for platform, status in platforms.items():
                if filter_platform and platform != filter_platform:
                    continue

                adapter = registry.get(platform)
                display_name = adapter.display_name if adapter else platform

                status_text = status.get('status', 'unknown')
                if status_text == 'published':
                    status_color = Colors.GREEN
                elif status_text == 'updated':
                    status_color = Colors.CYAN
                elif status_text == 'failed':
                    status_color = Colors.RED
                else:
                    status_color = Colors.YELLOW

                url = status.get('url', '')
                url_text = f" → {url}" if url else ""

                print(f"    {display_name}: {c(status_text, status_color)}{url_text}")

                if status_text == 'failed' and 'error_message' in status:
                    print(f"      {c(status['error_message'], Colors.RED)}")

            print()


def check_platform(platform: str, root: Path, config: Dict[str, Any], paths: Dict[str, Any]):
    """检查平台可用性"""
    manager = PublishingManager(root, config, paths)
    adapter = manager.get_adapter(platform)

    if not adapter:
        if cli.is_json_mode():
            cli.output_json({'success': False, 'error': f'未知平台: {platform}'})
        else:
            print(f"  {c(f'未知平台: {platform}', Colors.RED)}")
        return

    if cli.is_interactive() or not cli.is_json_mode():
        print(f"\n{c('═' * 60, Colors.BOLD)}")
        print(f"  {c(f'[CHECK] {adapter.display_name}', Colors.BOLD)}")
        print(f"{c('═' * 60, Colors.BOLD)}\n")

    available = adapter.is_available()

    if cli.is_json_mode():
        cli.output_json({
            'success': True,
            'platform': platform,
            'display_name': adapter.display_name,
            'available': available
        })
    else:
        if available:
            print(f"  {c('✓ 平台可用', Colors.GREEN)}")
            authed = adapter.authenticate(interactive=False)
            if authed:
                print(f"  {c('✓ 已认证', Colors.GREEN)}")
            else:
                print(f"  {c('⚠ 未认证', Colors.YELLOW)}")
                print(f"  请运行 'feishu auth login' 完成认证")
        else:
            print(f"  {c('✗ 平台不可用', Colors.RED)}")
            print(f"  请检查飞书 CLI 是否已安装")


if __name__ == '__main__':
    main()
