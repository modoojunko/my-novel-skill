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
