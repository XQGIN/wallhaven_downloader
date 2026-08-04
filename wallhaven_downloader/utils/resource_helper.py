# -*- coding: utf-8 -*-
"""
资源路径处理工具
用于处理资源文件的绝对路径
"""

import os
import sys


def get_app_root() -> str:
    """
    获取应用程序根目录。

    打包后：可执行文件所在目录（sys.executable 的父目录）。
    开发时：项目根目录（本文件位于 wallhaven_downloader/utils/，上两级为项目根）。
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_resources_dir() -> str:
    """
    获取资源目录绝对路径。

    打包后：<应用根目录>/resources
    开发时：项目根目录（icon、locales、settings.json 等资源所在位置）
    """
    if getattr(sys, "frozen", False):
        return os.path.join(get_app_root(), "resources")
    return get_app_root()


def resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，无论程序是直接运行还是被打包

    Args:
        relative_path: 相对路径

    Returns:
        str: 绝对路径

    Examples:
        >>> icon_path = resource_path("icon/logo.png")
        >>> font_path = resource_path("font/NanoByongGyeHei-Regular.ttf")
    """
    return os.path.join(get_resources_dir(), relative_path)


def get_app_data_dir() -> str:
    """
    获取应用数据目录

    Returns:
        str: 应用数据目录路径
    """
    if sys.platform == "win32":
        # Windows: %APPDATA%\WallhavenDownloader
        app_data = os.getenv("APPDATA", os.path.expanduser("~"))
        return os.path.join(app_data, "WallhavenDownloader")
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/WallhavenDownloader
        return os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "WallhavenDownloader",
        )
    else:
        # Linux: ~/.config/WallhavenDownloader
        return os.path.join(os.path.expanduser("~"), ".config", "WallhavenDownloader")


def ensure_dir(directory: str) -> str:
    """
    确保目录存在，不存在则创建

    Args:
        directory: 目录路径

    Returns:
        str: 目录路径
    """
    os.makedirs(directory, exist_ok=True)
    return directory


__all__ = [
    "resource_path",
    "get_resources_dir",
    "get_app_root",
    "get_app_data_dir",
    "ensure_dir",
]
