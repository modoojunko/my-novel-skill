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
