"""
Feishu adapter - publish chapters to Feishu Docs via larksuite/cli
(https://github.com/larksuite/cli)
"""
import sys
import subprocess
import os
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from .base import PlatformAdapter, PublishResult


class FeishuAdapter(PlatformAdapter):
    """飞书文档适配器"""

    def __init__(self):
        self._folder_id: Optional[str] = None
        self._config: Dict[str, Any] = {}
        self._cli_cmd: Optional[str] = None  # 'lark' 或 'feishu'

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

    def _find_cli(self) -> Optional[str]:
        """查找可用的飞书 CLI 命令"""
        for cmd in ['lark', 'feishu']:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return None

    def _run_cli_command(self, args: list, check: bool = True) -> tuple[bool, str, str]:
        """运行飞书 CLI 命令"""
        if not self._cli_cmd:
            self._cli_cmd = self._find_cli()
        if not self._cli_cmd:
            return False, "", "飞书 CLI 未找到"

        full_args = [self._cli_cmd] + args
        try:
            result = subprocess.run(
                full_args,
                capture_output=True,
                text=True,
                check=check
            )
            return True, result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stdout.strip(), e.stderr.strip()

    def is_available(self) -> bool:
        """检查飞书 CLI 是否可用"""
        if self._cli_cmd is None:
            self._cli_cmd = self._find_cli()
        return self._cli_cmd is not None

    def authenticate(self, interactive: bool = False) -> bool:
        """检查飞书 CLI 认证状态"""
        if not self.is_available():
            return False

        try:
            # 使用 lark auth status 或类似命令检查认证
            # 注意：lark CLI 可能没有专门的 auth status，尝试一个简单命令
            result = subprocess.run(
                [self._cli_cmd, "drive", "list", "--limit", "1"],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            if interactive:
                print(f"请运行 '{self._cli_cmd} auth login' 完成飞书认证")
            return False

    def convert_content(self, content: str, chapter_num: int, metadata: Dict[str, Any]) -> str:
        """
        将标准 Markdown 转换为飞书文档兼容格式

        处理：
        - 标题层级调整（H1 → H2，避免与文档标题冲突）
        - 移除不兼容的扩展语法
        - 保留基本格式
        """
        lines = content.split('\n')
        converted_lines = []

        for line in lines:
            # 调整标题层级：# → ##, ## → ###, 等等
            if line.startswith('#'):
                # 计算标题层级
                level = 0
                while level < len(line) and line[level] == '#':
                    level += 1
                if level > 0 and level < 6:
                    # 增加一级，最多到 H6
                    new_level = min(level + 1, 6)
                    converted_lines.append('#' * new_level + line[level:])
                else:
                    converted_lines.append(line)
            else:
                converted_lines.append(line)

        return '\n'.join(converted_lines)

    def publish_chapter(
        self,
        content: str,
        chapter_num: int,
        metadata: Dict[str, Any],
        existing_url: Optional[str] = None
    ) -> PublishResult:
        """
        发布章节到飞书文档

        注意：lark CLI 的具体命令需要根据实际安装的版本调整
        这里假设基本的命令结构，实际使用时可能需要微调
        """
        title = metadata.get('title', f"第{chapter_num}章")

        if not self._folder_id:
            return PublishResult(
                False,
                error_message="未配置飞书文件夹 ID，请在 story.yaml 中设置 publishing.platforms.feishu.folder_id"
            )

        try:
            # 创建临时文件存储内容
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.md', delete=False, encoding='utf-8'
            ) as f:
                f.write(content)
                temp_path = f.name

            try:
                # 尝试创建文档
                # 注意：这里的命令是示意性的，需要根据实际 lark CLI 调整
                # 可能的命令格式：
                # lark doc create --title "标题" --folder <folder_id> --file <path>
                # 或者：lark drive import --title "标题" --parent <folder_id> <path>

                # 首先尝试列出文件夹内容验证权限
                success, stdout, stderr = self._run_cli_command(
                    ["drive", "list", "--folder", self._folder_id, "--limit", "1"],
                    check=False
                )

                if not success:
                    # 列出失败，可能是命令格式不对，提供友好提示
                    return PublishResult(
                        False,
                        error_message=f"无法访问飞书文件夹。请确认：\n"
                                      f"1. folder_id 正确: {self._folder_id}\n"
                                      f"2. 已运行 'lark auth login' 完成认证\n"
                                      f"3. lark CLI 版本正确\n\n"
                                      f"CLI 输出: {stderr or stdout}"
                    )

                # 由于 lark CLI 命令可能因版本而异，这里提供一个通用实现
                # 实际使用时需要根据具体 CLI 调整
                return PublishResult(
                    False,
                    error_message="飞书 CLI 命令需要根据具体版本配置。\n"
                                  "请查看 https://github.com/larksuite/cli 文档，\n"
                                  "然后根据实际命令格式修改 FeishuAdapter.publish_chapter() 方法。"
                )

            finally:
                # 清理临时文件
                os.unlink(temp_path)

        except Exception as e:
            return PublishResult(
                False,
                error_message=f"发布失败: {str(e)}"
            )

    def get_publish_url(self, chapter_num: int) -> Optional[str]:
        """获取章节已发布地址（从本地状态查询）"""
        # 这个方法由 PublishingManager 通过状态跟踪
        return None
