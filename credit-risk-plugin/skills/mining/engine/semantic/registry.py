"""
主题注册表。

管理所有可用的语义特征主题。
"""

from __future__ import annotations

from typing import Type

from .base import ThemeBase

# 内置主题
from .themes.consistency import ConsistencyTheme
from .themes.velocity import VelocityTheme
from .themes.cashout import CashoutTheme


class ThemeRegistry:
    """主题注册表。

    单例模式，管理所有可用的主题。
    """

    _instance: "ThemeRegistry | None" = None
    _themes: dict[str, Type[ThemeBase]]

    def __new__(cls) -> "ThemeRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._themes = {}
            cls._instance._register_builtin_themes()
        return cls._instance

    def _register_builtin_themes(self) -> None:
        """注册内置主题。"""
        self.register(ConsistencyTheme)
        self.register(VelocityTheme)
        self.register(CashoutTheme)

    def register(self, theme_class: Type[ThemeBase]) -> None:
        """注册主题。"""
        instance = theme_class()
        self._themes[instance.name] = theme_class

    def get(self, name: str) -> ThemeBase | None:
        """获取主题实例。"""
        theme_class = self._themes.get(name)
        return theme_class() if theme_class else None

    def list_themes(self) -> list[str]:
        """列出所有已注册的主题名称。"""
        return list(self._themes.keys())

    def get_all_specs(self, themes: list[str] | None = None) -> list:
        """获取指定主题（或全部）的特征规格。"""
        from .base import FeatureSpec

        all_specs: list[FeatureSpec] = []
        theme_names = themes if themes else self.list_themes()

        for name in theme_names:
            theme = self.get(name)
            if theme:
                all_specs.extend(theme.feature_specs())

        return all_specs


# 全局注册表实例
_registry: ThemeRegistry | None = None


def get_registry() -> ThemeRegistry:
    """获取全局主题注册表。"""
    global _registry
    if _registry is None:
        _registry = ThemeRegistry()
    return _registry


def register_theme(theme_class: Type[ThemeBase]) -> None:
    """注册新主题到全局注册表。"""
    get_registry().register(theme_class)


def list_themes() -> list[str]:
    """列出所有已注册的主题。"""
    return get_registry().list_themes()


def get_theme(name: str) -> ThemeBase | None:
    """获取主题实例。"""
    return get_registry().get(name)
