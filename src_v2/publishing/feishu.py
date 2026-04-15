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

    def get_publish_url(self, chapter_num: int) -> Optional[str]:
        """获取章节已发布地址（飞书适配器暂不支持查询）"""
        # 这个方法需要根据实际情况实现，可能需要从本地状态查询
        return None
