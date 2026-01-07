# -*- coding: utf-8 -*-
"""
启动优化器

优化应用启动性能，实现分阶段加载
需求：14.8 - 启动渲染性能
"""

import time
from typing import Callable, Optional
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

try:
    from utils.logger import get_logger
    from utils.lazy_loader import get_lazy_loader
except ImportError:
    from wallhaven_downloader.utils.logger import get_logger
    from wallhaven_downloader.utils.lazy_loader import get_lazy_loader

logger = get_logger(__name__)


class StartupOptimizer(QObject):
    """
    启动优化器
    
    负责管理应用启动流程，实现分阶段加载
    
    启动阶段：
    1. 关键阶段（0-500ms）：核心UI组件、窗口框架
    2. 重要阶段（500-1000ms）：主要功能组件
    3. 次要阶段（1000-1500ms）：辅助功能组件
    4. 可选阶段（1500ms+）：非关键功能组件
    """
    
    # 信号
    stage_started = pyqtSignal(str)  # 阶段开始
    stage_completed = pyqtSignal(str, float)  # 阶段完成（阶段名，耗时）
    startup_completed = pyqtSignal(float)  # 启动完成（总耗时）
    
    # 启动阶段
    STAGE_CRITICAL = "critical"  # 关键阶段
    STAGE_IMPORTANT = "important"  # 重要阶段
    STAGE_SECONDARY = "secondary"  # 次要阶段
    STAGE_OPTIONAL = "optional"  # 可选阶段
    
    def __init__(self):
        super().__init__()
        self.lazy_loader = get_lazy_loader()
        self.start_time = 0
        self.stage_times = {}
        self.current_stage = None
        
        logger.info("启动优化器初始化")
    
    def start_optimization(self):
        """开始启动优化"""
        self.start_time = time.time()
        logger.info("开始启动优化")
        
        # 注册所有延迟加载任务
        self._register_tasks()
        
        # 开始加载
        self.lazy_loader.start_loading()
        
        # 监听完成信号
        self.lazy_loader.all_tasks_completed.connect(self._on_startup_completed)
    
    def _register_tasks(self):
        """注册延迟加载任务"""
        
        # === 关键阶段（0-500ms）：核心UI组件、窗口框架 ===
        # 这些组件必须立即加载，不延迟
        
        # 主题系统（优先级最高）
        self.lazy_loader.register_task(
            name="theme_system",
            loader=self._load_theme_system,
            priority=0,
            delay=0
        )
        
        # 基础UI框架
        self.lazy_loader.register_task(
            name="basic_ui_framework",
            loader=self._load_basic_ui_framework,
            priority=1,
            delay=0,
            dependencies=["theme_system"]
        )
        
        # === 重要阶段（500-1000ms）：主要功能组件 ===
        
        # 下载管理器
        self.lazy_loader.register_task(
            name="download_manager",
            loader=self._load_download_manager,
            priority=10,
            delay=100,
            dependencies=["basic_ui_framework"]
        )
        
        # 图片预览组件
        self.lazy_loader.register_task(
            name="image_preview",
            loader=self._load_image_preview,
            priority=11,
            delay=150,
            dependencies=["basic_ui_framework"]
        )
        
        # === 次要阶段（1000-1500ms）：辅助功能组件 ===
        
        # 设置面板
        self.lazy_loader.register_task(
            name="settings_panel",
            loader=self._load_settings_panel,
            priority=20,
            delay=300,
            dependencies=["basic_ui_framework"]
        )
        
        # 系统托盘
        self.lazy_loader.register_task(
            name="system_tray",
            loader=self._load_system_tray,
            priority=21,
            delay=350,
            dependencies=["basic_ui_framework"]
        )
        
        # === 可选阶段（1500ms+）：非关键功能组件 ===
        
        # 动画系统
        self.lazy_loader.register_task(
            name="animation_system",
            loader=self._load_animation_system,
            priority=30,
            delay=500,
            dependencies=["basic_ui_framework"]
        )
        
        # 性能监控
        self.lazy_loader.register_task(
            name="performance_monitor",
            loader=self._load_performance_monitor,
            priority=31,
            delay=600
        )
        
        # 帮助文档
        self.lazy_loader.register_task(
            name="help_documentation",
            loader=self._load_help_documentation,
            priority=32,
            delay=700
        )
        
        logger.info("延迟加载任务注册完成")
    
    # === 加载函数 ===
    
    def _load_theme_system(self):
        """加载主题系统"""
        logger.debug("加载主题系统")
        # 主题系统在主窗口初始化时已加载
        return True
    
    def _load_basic_ui_framework(self):
        """加载基础UI框架"""
        logger.debug("加载基础UI框架")
        # 基础UI框架在主窗口初始化时已加载
        return True
    
    def _load_download_manager(self):
        """加载下载管理器"""
        logger.debug("加载下载管理器")
        # 下载管理器在用户开始下载时才真正初始化
        return True
    
    def _load_image_preview(self):
        """加载图片预览组件"""
        logger.debug("加载图片预览组件")
        # 图片预览组件在主窗口初始化时已加载
        return True
    
    def _load_settings_panel(self):
        """加载设置面板"""
        logger.debug("加载设置面板")
        # 设置面板在用户打开设置时才真正初始化
        return True
    
    def _load_system_tray(self):
        """加载系统托盘"""
        logger.debug("加载系统托盘")
        # 系统托盘在主窗口初始化时已加载
        return True
    
    def _load_animation_system(self):
        """加载动画系统"""
        logger.debug("加载动画系统")
        # 动画系统在主窗口初始化时已加载
        return True
    
    def _load_performance_monitor(self):
        """加载性能监控"""
        logger.debug("加载性能监控")
        # 性能监控可以延迟加载
        return True
    
    def _load_help_documentation(self):
        """加载帮助文档"""
        logger.debug("加载帮助文档")
        # 帮助文档可以延迟加载
        return True
    
    def _on_startup_completed(self):
        """启动完成"""
        elapsed = (time.time() - self.start_time) * 1000
        logger.info(f"启动优化完成，总耗时: {elapsed:.2f}ms")
        
        # 发送完成信号
        self.startup_completed.emit(elapsed)
    
    def get_stage_time(self, stage: str) -> float:
        """获取阶段耗时"""
        return self.stage_times.get(stage, 0.0)
    
    def get_total_time(self) -> float:
        """获取总耗时"""
        if self.start_time == 0:
            return 0.0
        return (time.time() - self.start_time) * 1000


# 全局启动优化器实例
_startup_optimizer_instance = None


def get_startup_optimizer() -> StartupOptimizer:
    """获取全局启动优化器实例"""
    global _startup_optimizer_instance
    if _startup_optimizer_instance is None:
        _startup_optimizer_instance = StartupOptimizer()
    return _startup_optimizer_instance
