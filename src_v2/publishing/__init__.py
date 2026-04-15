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
