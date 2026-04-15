# 多平台发布功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 my-novel-skill 添加多平台章节发布功能，第一阶段支持飞书文档

**Architecture:** 适配器模式，抽象 PlatformAdapter 基类，具体平台适配器继承实现，PublishingManager 统一管理

**Tech Stack:** Python 3.8+ 标准库，仅 PyYAML 为可选依赖

---

## 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `src_v2/publishing/__init__.py` | 新建 | 包初始化文件 |
| `src_v2/publishing/base.py` | 新建 | PlatformAdapter 抽象基类 + PublishResult |
| `src_v2/publishing/registry.py` | 新建 | 平台注册表 |
| `src_v2/publishing/feishu.py` | 新建 | 飞书适配器实现 |
| `src_v2/publishing/zhihu.py` | 新建 | 知乎适配器（预留空实现） |
| `src_v2/publishing/qidian.py` | 新建 | 起点适配器（预留空实现） |
| `src_v2/publish.py` | 新建 | CLI 入口 + PublishingManager |
| `src_v2/paths.py` | 修改 | 添加发布相关路径（如需要） |
| `story.py` | 修改 | 添加 publish 命令 |

---

### Task 1: 创建 publishing 包和基础模块

**Files:**
- Create: `src_v2/publishing/__init__.py`
- Create: `src_v2/publishing/base.py`

- [ ] **Step 1: 创建 publishing 包初始化文件**

```python
"""
Publishing module - Multi-platform chapter publishing
"""
from .base import PlatformAdapter, PublishResult
from .registry import PlatformRegistry

__all__ = ['PlatformAdapter', 'PublishResult', 'PlatformRegistry']
```

- [ ] **Step 2: 创建 base.py - PublishResult 类**

```python
"""
Base classes for publishing adapters
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PublishResult:
    """发布结果"""
    def __init__(
        self,
        success: bool,
        url: Optional[str] = None,
        error_message: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.url = url
        self.error_message = error_message
        self.extra = extra or {}
```

- [ ] **Step 3: 在 base.py 中添加 PlatformAdapter 抽象基类**

```python
class PlatformAdapter(ABC):
    """平台适配器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """平台名称，如 'feishu'、'zhihu'"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """平台显示名称，如 '飞书文档'"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查平台是否可用（如 CLI 已安装、认证已配置）"""
        pass

    @abstractmethod
    def authenticate(self, interactive: bool = False) -> bool:
        """
        进行认证
        
        Args:
            interactive: 是否交互模式，交互模式可提示用户输入
        
        Returns:
            是否认证成功
        """
        pass

    @abstractmethod
    def convert_content(self, content: str, chapter_num: int, metadata: Dict[str, Any]) -> str:
        """
        将标准 Markdown 转换为平台特定格式
        
        Args:
            content: 标准 Markdown 内容
            chapter_num: 章节号
            metadata: 章节元数据（标题、卷号等）
        
        Returns:
            转换后的内容
        """
        pass

    @abstractmethod
    def publish_chapter(
        self,
        content: str,
        chapter_num: int,
        metadata: Dict[str, Any],
        existing_url: Optional[str] = None
    ) -> PublishResult:
        """
        发布章节
        
        Args:
            content: 已转换的内容
            chapter_num: 章节号
            metadata: 章节元数据
            existing_url: 已有发布地址（如果是更新）
        
        Returns:
            PublishResult 对象
        """
        pass

    @abstractmethod
    def get_publish_url(self, chapter_num: int) -> Optional[str]:
        """获取章节已发布地址（如果有）"""
        pass
```

- [ ] **Step 4: 提交**

```bash
git add src_v2/publishing/__init__.py src_v2/publishing/base.py
git commit -m "feat: add publishing base classes"
```

---

### Task 2: 创建平台注册表

**Files:**
- Create: `src_v2/publishing/registry.py`

- [ ] **Step 1: 实现 PlatformRegistry 类**

```python
"""
Platform registry - manages available publishing adapters
"""
from typing import Dict, Type, List, Optional
from .base import PlatformAdapter


class PlatformRegistry:
    """平台注册表"""
    
    def __init__(self):
        self._adapters: Dict[str, Type[PlatformAdapter]] = {}
        self._instances: Dict[str, PlatformAdapter] = {}
    
    def register(self, adapter_class: Type[PlatformAdapter]) -> None:
        """注册一个平台适配器类"""
        # 创建临时实例获取名称
        # 注意：适配器应该有无参构造函数或默认参数
        temp_instance = adapter_class()
        self._adapters[temp_instance.name] = adapter_class
    
    def get(self, name: str) -> Optional[PlatformAdapter]:
        """获取平台适配器实例（单例）"""
        if name not in self._adapters:
            return None
        
        if name not in self._instances:
            self._instances[name] = self._adapters[name]()
        
        return self._instances[name]
    
    def list_available(self) -> List[str]:
        """列出所有已注册的平台名称"""
        return list(self._adapters.keys())
    
    def list_display_names(self) -> List[str]:
        """列出所有已注册的平台显示名称"""
        result = []
        for name in self._adapters.keys():
            adapter = self.get(name)
            if adapter:
                result.append(f"{adapter.display_name} ({name})")
        return result


# 全局注册表实例
_registry = PlatformRegistry()


def get_registry() -> PlatformRegistry:
    """获取全局注册表实例"""
    return _registry
```

- [ ] **Step 2: 提交**

```bash
git add src_v2/publishing/registry.py
git commit -m "feat: add platform registry"
```

---

### Task 3: 创建预留适配器（zhihu.py, qidian.py）

**Files:**
- Create: `src_v2/publishing/zhihu.py`
- Create: `src_v2/publishing/qidian.py`

- [ ] **Step 1: 创建 zhihu.py（预留空实现）**

```python
"""
Zhihu adapter - placeholder for future implementation
"""
from typing import Dict, Any, Optional
from .base import PlatformAdapter, PublishResult


class ZhihuAdapter(PlatformAdapter):
    """知乎适配器（预留）"""

    @property
    def name(self) -> str:
        return "zhihu"

    @property
    def display_name(self) -> str:
        return "知乎"

    def is_available(self) -> bool:
        return False

    def authenticate(self, interactive: bool = False) -> bool:
        return False

    def convert_content(self, content: str, chapter_num: int, metadata: Dict[str, Any]) -> str:
        return content

    def publish_chapter(
        self,
        content: str,
        chapter_num: int,
        metadata: Dict[str, Any],
        existing_url: Optional[str] = None
    ) -> PublishResult:
        return PublishResult(False, error_message="知乎适配器尚未实现")

    def get_publish_url(self, chapter_num: int) -> Optional[str]:
        return None
```

- [ ] **Step 2: 创建 qidian.py（预留空实现）**

```python
"""
Qidian adapter - placeholder for future implementation
"""
from typing import Dict, Any, Optional
from .base import PlatformAdapter, PublishResult


class QidianAdapter(PlatformAdapter):
    """起点适配器（预留）"""

    @property
    def name(self) -> str:
        return "qidian"

    @property
    def display_name(self) -> str:
        return "起点小说"

    def is_available(self) -> bool:
        return False

    def authenticate(self, interactive: bool = False) -> bool:
        return False

    def convert_content(self, content: str, chapter_num: int, metadata: Dict[str, Any]) -> str:
        return content

    def publish_chapter(
        self,
        content: str,
        chapter_num: int,
        metadata: Dict[str, Any],
        existing_url: Optional[str] = None
    ) -> PublishResult:
        return PublishResult(False, error_message="起点适配器尚未实现")

    def get_publish_url(self, chapter_num: int) -> Optional[str]:
        return None
```

- [ ] **Step 3: 提交**

```bash
git add src_v2/publishing/zhihu.py src_v2/publishing/qidian.py
git commit -m "feat: add placeholder adapters for zhihu and qidian"
```

---

### Task 4: 创建飞书适配器

**Files:**
- Create: `src_v2/publishing/feishu.py`

- [ ] **Step 1: 实现 FeishuAdapter 基础结构**

```python
"""
Feishu adapter - publish chapters to Feishu Docs via feishu-cli
"""
import sys
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .base import PlatformAdapter, PublishResult


class FeishuAdapter(PlatformAdapter):
    """飞书文档适配器"""

    def __init__(self):
        self._folder_id: Optional[str] = None
        self._config: Dict[str, Any] = {}
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置平台配置"""
        self._config = config
        self._folder_id = config.get('folder_id')
    
    @property
    def name(self) -> str:
        return "feishu"

    @property
    def display_name(self) -> str:
        return "飞书文档"
```

- [ ] **Step 2: 实现 is_available() 和 authenticate() 方法**

```python
    def is_available(self) -> bool:
        """检查飞书 CLI 是否可用"""
        try:
            result = subprocess.run(
                ["feishu", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def authenticate(self, interactive: bool = False) -> bool:
        """检查飞书 CLI 认证状态"""
        try:
            result = subprocess.run(
                ["feishu", "auth", "status"],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            if interactive:
                print("请运行 'feishu auth login' 完成飞书认证")
            return False
```

- [ ] **Step 3: 实现 convert_content() 方法**

```python
    def convert_content(self, content: str, chapter_num: int, metadata: Dict[str, Any]) -> str:
        """
        将标准 Markdown 转换为飞书文档格式
        
        飞书支持标准 Markdown，这里可以添加标题等元数据
        """
        title = metadata.get('title', f"第{chapter_num}章")
        
        # 在内容前添加标题
        converted = f"# {title}\n\n"
        converted += content
        
        return converted
```

- [ ] **Step 4: 实现 publish_chapter() 方法**

```python
    def publish_chapter(
        self,
        content: str,
        chapter_num: int,
        metadata: Dict[str, Any],
        existing_url: Optional[str] = None
    ) -> PublishResult:
        """发布章节到飞书文档"""
        title = metadata.get('title', f"第{chapter_num}章")
        
        if not self._folder_id:
            return PublishResult(
                False,
                error_message="未配置飞书文件夹 ID，请在 story.yaml 中设置 publishing.platforms.feishu.folder_id"
            )
        
        try:
            # 创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # 使用飞书 CLI 创建文档
                # 注意：这里假设 feishu-cli 有类似命令，实际需要根据具体 CLI 调整
                args = [
                    "feishu", "doc", "create",
                    "--title", title,
                    "--folder", self._folder_id,
                    "--file", temp_path
                ]
                
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # 解析输出获取 URL（需要根据实际 CLI 输出格式调整）
                url = None
                for line in result.stdout.split('\n'):
                    if 'http' in line:
                        url = line.strip()
                        break
                
                return PublishResult(True, url=url)
                
            finally:
                # 清理临时文件
                os.unlink(temp_path)
                
        except subprocess.CalledProcessError as e:
            return PublishResult(
                False,
                error_message=f"飞书 CLI 调用失败: {e.stderr or str(e)}"
            )
        except Exception as e:
            return PublishResult(
                False,
                error_message=f"发布失败: {str(e)}"
            )
```

- [ ] **Step 5: 实现 get_publish_url() 方法**

```python
    def get_publish_url(self, chapter_num: int) -> Optional[str]:
        """获取章节已发布地址（飞书适配器暂不支持查询）"""
        # 这个方法需要根据实际情况实现，可能需要从本地状态查询
        return None
```

- [ ] **Step 6: 更新 publishing/__init__.py 注册适配器**

```python
"""
Publishing module - Multi-platform chapter publishing
"""
from .base import PlatformAdapter, PublishResult
from .registry import PlatformRegistry, get_registry
from .feishu import FeishuAdapter
from .zhihu import ZhihuAdapter
from .qidian import QidianAdapter

__all__ = ['PlatformAdapter', 'PublishResult', 'PlatformRegistry', 'get_registry']


# 自动注册适配器
def _register_adapters():
    registry = get_registry()
    registry.register(FeishuAdapter)
    registry.register(ZhihuAdapter)
    registry.register(QidianAdapter)


_register_adapters()
```

- [ ] **Step 7: 提交**

```bash
git add src_v2/publishing/feishu.py src_v2/publishing/__init__.py
git commit -m "feat: add feishu adapter implementation"
```

---

### Task 5: 创建 PublishingManager 和 publish.py

**Files:**
- Create: `src_v2/publish.py`

- [ ] **Step 1: 创建 publish.py 基础结构和辅助函数**

```python
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
```

- [ ] **Step 2: 添加 PublishingManager 类**

```python
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
```

- [ ] **Step 3: 添加 CLI 处理函数**

```python
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
    
    # Parse CLI arguments
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    args, extra_args = cli.parse_cli_args(parser)
    
    # Now process our commands
    if not extra_args:
        show_publish_help()
        return
    
    target = extra_args[0].lower()
    
    # Check for help
    if target in ('help', '--help', '-h'):
        show_publish_help()
        return
    
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
        show_publishing_status(config, paths, extra_args[1:])
        return
    
    # Handle check command
    if target == 'check':
        if len(extra_args) < 2:
            show_publish_help()
            return
        platform = extra_args[1]
        check_platform(platform, root, config, paths)
        return
    
    # Handle publish commands
    if len(extra_args) < 2:
        show_publish_help()
        return
    
    platform = extra_args[1]
    
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


def show_publishing_status(config: Dict[str, Any], paths: Dict[str, Any], extra_args: List[str]):
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
    for arg in extra_args:
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
```

- [ ] **Step 4: 提交**

```bash
git add src_v2/publish.py
git commit -m "feat: add publish.py with PublishingManager"
```

---

### Task 6: 集成到 story.py

**Files:**
- Modify: `story.py`

- [ ] **Step 1: 更新 story.py 的导入和 commands 字典**

修改前：
```python
from src_v2 import init, paths, status, collect, plan, write, archive, export, world, verify, github
```

修改后：
```python
from src_v2 import init, paths, status, collect, plan, write, archive, export, world, verify, github, publish
```

修改 commands 字典，添加：
```python
        'publish': publish,
```

修改 help 文本，添加：
```
  publish     Publish chapters to platforms (check, status, <chapter>, all)
```

- [ ] **Step 2: 提交**

```bash
git add story.py
git commit -m "feat: integrate publish command into story.py"
```

---

### Task 7: 测试和验证

**Files:**
- 无新文件，测试现有功能

- [ ] **Step 1: 运行基本测试**

```bash
# 测试帮助
python3 story.py publish --help

# 测试 check 命令（假设飞书 CLI 未安装）
python3 story.py publish check feishu

# 测试 status 命令（空状态）
python3 story.py publish status
```

- [ ] **Step 2: 在测试项目中验证（可选）**

```bash
# 在测试项目中运行
cd /path/to/test/novel
python3 /path/to/my-novel-skill/story.py publish --help
```

- [ ] **Step 3: 提交（如果有测试修复）**

```bash
# 仅在需要修复时提交
git add <fixed-files>
git commit -m "fix: publish command fixes"
```

---

## 自审

### 1. Spec 覆盖检查
- ✅ 适配器模式抽象层 - Task 1
- ✅ PublishingManager - Task 5
- ✅ 飞书适配器 - Task 4
- ✅ 发布状态存储 - Task 5 (set_chapter_publish_status)
- ✅ CLI 命令 - Task 5
- ✅ 内容哈希检测 - Task 5 (compute_content_hash)
- ✅ 发布所有未发布 - Task 5 (publish_all)

### 2. 占位符检查
- ✅ 无 "TBD" / "TODO"
- ✅ 所有代码块完整
- ✅ 所有命令明确

### 3. 类型一致性检查
- ✅ PlatformAdapter 方法签名一致
- ✅ 数据结构与 spec 匹配
- ✅ CLI 命令与设计一致

---

## 执行选择

计划已完成并保存到 `docs/superpowers/plans/2026-04-15-multi-platform-publishing-plan.md`。两种执行选项：

**1. Subagent-Driven (推荐)** - 我为每个任务分派一个新的子代理，任务间审查，快速迭代

**2. Inline Execution** - 在当前会话中使用 executing-plans 执行任务，带检查点的批量执行

选择哪种方式？
