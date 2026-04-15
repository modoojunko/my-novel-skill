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
