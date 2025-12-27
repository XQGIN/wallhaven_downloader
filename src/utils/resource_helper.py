# -*- coding: utf-8 -*-
"""
资源路径处理工具
用于处理资源文件的绝对路径
"""

import os
import sys


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
    try:
        # PyInstaller 创建临时文件夹，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        # 未打包时，使用当前工作目录
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    return os.path.join(base_path, relative_path)


def get_app_data_dir() -> str:
    """
    获取应用数据目录
    
    Returns:
        str: 应用数据目录路径
    """
    if sys.platform == 'win32':
        # Windows: %APPDATA%\WallhavenDownloader
        app_data = os.getenv('APPDATA', os.path.expanduser('~'))
        return os.path.join(app_data, 'WallhavenDownloader')
    elif sys.platform == 'darwin':
        # macOS: ~/Library/Application Support/WallhavenDownloader
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'WallhavenDownloader')
    else:
        # Linux: ~/.config/WallhavenDownloader
        return os.path.join(os.path.expanduser('~'), '.config', 'WallhavenDownloader')


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


__all__ = ['resource_path', 'get_app_data_dir', 'ensure_dir']
