# -*- coding: utf-8 -*-
"""
工具模块
"""

from .logger import setup_logger, get_logger
from .resource_helper import resource_path
from .exceptions import (
    WallhavenException,
    NetworkException,
    DownloadException,
    ConfigException,
    UIException,
    handle_exception,
    safe_execute,
    ExceptionHandler,
    validate_input
)
from .performance_optimizer import (
    VirtualScrollManager,
    ComponentCache,
    PerformanceDegradation,
    PerformanceMonitor,
    PerformanceOptimizer
)
from .lazy_loader import LazyLoader, LazyLoadTask, get_lazy_loader
from .startup_optimizer import StartupOptimizer, get_startup_optimizer
from .resource_loader import ResourceLoader, get_resource_loader

__all__ = [
    'setup_logger',
    'get_logger',
    'resource_path',
    'WallhavenException',
    'NetworkException',
    'DownloadException',
    'ConfigException',
    'UIException',
    'handle_exception',
    'safe_execute',
    'ExceptionHandler',
    'validate_input',
    'VirtualScrollManager',
    'ComponentCache',
    'PerformanceDegradation',
    'PerformanceMonitor',
    'PerformanceOptimizer',
    'LazyLoader',
    'LazyLoadTask',
    'get_lazy_loader',
    'StartupOptimizer',
    'get_startup_optimizer',
    'ResourceLoader',
    'get_resource_loader'
]
