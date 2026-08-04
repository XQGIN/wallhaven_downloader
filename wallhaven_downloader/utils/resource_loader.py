# -*- coding: utf-8 -*-
"""
资源加载优化器

优化资源加载顺序，减少启动时间
需求：14.8 - 启动渲染性能
"""

import os
import time
from typing import Dict, Optional, Any
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import QObject, pyqtSignal

try:
    from utils.logger import get_logger
except ImportError:
    from wallhaven_downloader.utils.logger import get_logger

logger = get_logger(__name__)


class ResourceLoader(QObject):
    """
    资源加载优化器
    
    负责优化资源加载顺序，实现资源缓存和延迟加载
    
    功能：
    - 资源缓存
    - 延迟加载
    - 优先级管理
    - 预加载
    """
    
    # 信号
    resource_loaded = pyqtSignal(str, object)  # 资源加载完成（资源名，资源对象）
    resource_failed = pyqtSignal(str, str)  # 资源加载失败（资源名，错误信息）
    
    # 资源类型
    TYPE_PIXMAP = "pixmap"
    TYPE_ICON = "icon"
    TYPE_FONT = "font"
    TYPE_DATA = "data"
    
    def __init__(self):
        super().__init__()
        self.cache: Dict[str, Any] = {}
        self.loading_queue: Dict[str, int] = {}  # 资源名 -> 优先级
        self.is_loading = False
        
        logger.info("资源加载优化器初始化")
    
    def load_pixmap(
        self,
        name: str,
        path: str,
        priority: int = 0,
        cache: bool = True
    ) -> Optional[QPixmap]:
        """
        加载图片资源
        
        Args:
            name: 资源名称
            path: 资源路径
            priority: 优先级（数字越小优先级越高）
            cache: 是否缓存
            
        Returns:
            QPixmap对象，如果加载失败返回None
        """
        # 检查缓存
        if cache and name in self.cache:
            logger.debug(f"从缓存加载图片: {name}")
            return self.cache[name]
        
        # 加载图片
        try:
            start_time = time.time()
            
            pixmap = QPixmap(path)
            if pixmap.isNull():
                logger.warning(f"图片加载失败: {path}")
                self.resource_failed.emit(name, "图片加载失败")
                return None
            
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"图片加载成功: {name}, 耗时: {elapsed:.2f}ms")
            
            # 缓存
            if cache:
                self.cache[name] = pixmap
            
            # 发送信号
            self.resource_loaded.emit(name, pixmap)
            
            return pixmap
            
        except Exception as e:
            logger.error(f"图片加载异常: {path}, 错误: {str(e)}")
            self.resource_failed.emit(name, str(e))
            return None
    
    def load_icon(
        self,
        name: str,
        path: str,
        priority: int = 0,
        cache: bool = True
    ) -> Optional[QIcon]:
        """
        加载图标资源
        
        Args:
            name: 资源名称
            path: 资源路径
            priority: 优先级（数字越小优先级越高）
            cache: 是否缓存
            
        Returns:
            QIcon对象，如果加载失败返回None
        """
        # 检查缓存
        if cache and name in self.cache:
            logger.debug(f"从缓存加载图标: {name}")
            return self.cache[name]
        
        # 加载图标
        try:
            start_time = time.time()
            
            icon = QIcon(path)
            if icon.isNull():
                logger.warning(f"图标加载失败: {path}")
                self.resource_failed.emit(name, "图标加载失败")
                return None
            
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"图标加载成功: {name}, 耗时: {elapsed:.2f}ms")
            
            # 缓存
            if cache:
                self.cache[name] = icon
            
            # 发送信号
            self.resource_loaded.emit(name, icon)
            
            return icon
            
        except Exception as e:
            logger.error(f"图标加载异常: {path}, 错误: {str(e)}")
            self.resource_failed.emit(name, str(e))
            return None
    
    def load_font(
        self,
        name: str,
        path: str,
        size: int = 12,
        priority: int = 0,
        cache: bool = True
    ) -> Optional[QFont]:
        """
        加载字体资源
        
        Args:
            name: 资源名称
            path: 资源路径
            size: 字体大小
            priority: 优先级（数字越小优先级越高）
            cache: 是否缓存
            
        Returns:
            QFont对象，如果加载失败返回None
        """
        # 检查缓存
        cache_key = f"{name}_{size}"
        if cache and cache_key in self.cache:
            logger.debug(f"从缓存加载字体: {cache_key}")
            return self.cache[cache_key]
        
        # 加载字体
        try:
            start_time = time.time()
            
            from PyQt5.QtGui import QFontDatabase
            
            font_id = QFontDatabase.addApplicationFont(path)
            if font_id == -1:
                logger.warning(f"字体加载失败: {path}")
                self.resource_failed.emit(name, "字体加载失败")
                return None
            
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if not font_families:
                logger.warning(f"字体家族获取失败: {path}")
                self.resource_failed.emit(name, "字体家族获取失败")
                return None
            
            font = QFont(font_families[0], size)
            
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"字体加载成功: {name}, 耗时: {elapsed:.2f}ms")
            
            # 缓存
            if cache:
                self.cache[cache_key] = font
            
            # 发送信号
            self.resource_loaded.emit(name, font)
            
            return font
            
        except Exception as e:
            logger.error(f"字体加载异常: {path}, 错误: {str(e)}")
            self.resource_failed.emit(name, str(e))
            return None
    
    def preload_resources(self, resources: Dict[str, Dict[str, Any]]):
        """
        预加载资源
        
        Args:
            resources: 资源字典，格式：
                {
                    "resource_name": {
                        "type": "pixmap|icon|font",
                        "path": "resource_path",
                        "priority": 0,
                        "cache": True,
                        ...其他参数
                    }
                }
        """
        logger.info(f"开始预加载 {len(resources)} 个资源")
        
        # 按优先级排序
        sorted_resources = sorted(
            resources.items(),
            key=lambda x: x[1].get("priority", 0)
        )
        
        # 加载资源
        for name, config in sorted_resources:
            resource_type = config.get("type")
            path = config.get("path")
            priority = config.get("priority", 0)
            cache = config.get("cache", True)
            
            if not path or not os.path.exists(path):
                logger.warning(f"资源路径不存在: {path}")
                continue
            
            if resource_type == self.TYPE_PIXMAP:
                self.load_pixmap(name, path, priority, cache)
            elif resource_type == self.TYPE_ICON:
                self.load_icon(name, path, priority, cache)
            elif resource_type == self.TYPE_FONT:
                size = config.get("size", 12)
                self.load_font(name, path, size, priority, cache)
            else:
                logger.warning(f"未知的资源类型: {resource_type}")
        
        logger.info("资源预加载完成")
    
    def get_cached_resource(self, name: str) -> Optional[Any]:
        """获取缓存的资源"""
        return self.cache.get(name)
    
    def clear_cache(self):
        """清除缓存"""
        logger.info("清除资源缓存")
        self.cache.clear()
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)
    
    def remove_from_cache(self, name: str):
        """从缓存中移除资源"""
        if name in self.cache:
            del self.cache[name]
            logger.debug(f"从缓存中移除资源: {name}")


# 全局资源加载器实例
_resource_loader_instance = None


def get_resource_loader() -> ResourceLoader:
    """获取全局资源加载器实例"""
    global _resource_loader_instance
    if _resource_loader_instance is None:
        _resource_loader_instance = ResourceLoader()
    return _resource_loader_instance
