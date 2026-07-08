"""Public desktop shell exports."""

from .app import DesktopApp
from .navigation import NavigationItem, NavigationModel
from .view_registry import DesktopView, ViewRegistry

__all__ = [
    "DesktopApp",
    "DesktopView",
    "NavigationModel",
    "NavigationItem",
    "ViewRegistry",
]
