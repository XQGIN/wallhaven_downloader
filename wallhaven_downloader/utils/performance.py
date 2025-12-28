# -*- coding: utf-8 -*-
"""
性能优化工具模块
提供性能分析和优化相关的工具函数
"""

import time
import functools
from typing import Callable, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def timer(func: Callable) -> Callable:
    """
    函数执行时间计时装饰器
    
    Example:
        @timer
        def slow_function():
            time.sleep(1)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.debug(f"{func.__name__} 执行时间: {duration:.3f}秒")
        return result
    return wrapper


def memoize(func: Callable) -> Callable:
    """
    函数结果缓存装饰器（适用于纯函数）
    
    Example:
        @memoize
        def expensive_calculation(n):
            return n * n
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 创建缓存键
        key = str(args) + str(kwargs)
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        
        return cache[key]
    
    return wrapper


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, name: str):
        """
        初始化性能监控器
        
        Args:
            name: 监控项名称
        """
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """进入上下文"""
        self.start_time = time.time()
        logger.debug(f"开始监控: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.debug(f"{self.name} 完成，耗时: {duration:.3f}秒")
        return False
    
    def get_duration(self) -> float:
        """获取执行时长"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0


class RateLimiter:
    """速率限制器 - 防止请求过快"""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        初始化速率限制器
        
        Args:
            max_calls: 时间窗口内的最大调用次数
            time_window: 时间窗口（秒）
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def __call__(self, func: Callable) -> Callable:
        """装饰器调用"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # 清理过期的调用记录
            self.calls = [call_time for call_time in self.calls 
                         if now - call_time < self.time_window]
            
            # 检查是否超过限制
            if len(self.calls) >= self.max_calls:
                sleep_time = self.time_window - (now - self.calls[0])
                if sleep_time > 0:
                    logger.debug(f"速率限制: 等待 {sleep_time:.2f}秒")
                    time.sleep(sleep_time)
                    self.calls.pop(0)
            
            # 记录本次调用
            self.calls.append(time.time())
            
            return func(*args, **kwargs)
        
        return wrapper


class Batch:
    """批处理工具"""
    
    @staticmethod
    def process(items: list, batch_size: int, processor: Callable) -> list:
        """
        批量处理数据
        
        Args:
            items: 要处理的数据列表
            batch_size: 批次大小
            processor: 处理函数，接受一批数据，返回处理结果
        
        Returns:
            所有批次的处理结果
        
        Example:
            def process_batch(batch):
                return [item * 2 for item in batch]
            
            results = Batch.process([1,2,3,4,5], 2, process_batch)
        """
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_result = processor(batch)
            results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
        
        return results


def optimize_image_size(width: int, height: int, max_size: int = 200) -> tuple:
    """
    优化图片尺寸，保持宽高比
    
    Args:
        width: 原始宽度
        height: 原始高度
        max_size: 最大尺寸
    
    Returns:
        (优化后的宽度, 优化后的高度)
    """
    if width <= max_size and height <= max_size:
        return (width, height)
    
    # 计算缩放比例
    ratio = min(max_size / width, max_size / height)
    
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    
    return (new_width, new_height)


class ConnectionPool:
    """连接池管理（简化版）"""
    
    def __init__(self, max_connections: int = 10):
        """
        初始化连接池
        
        Args:
            max_connections: 最大连接数
        """
        self.max_connections = max_connections
        self.active_connections = 0
        self.waiting = []
    
    def acquire(self):
        """获取连接"""
        if self.active_connections < self.max_connections:
            self.active_connections += 1
            return True
        return False
    
    def release(self):
        """释放连接"""
        if self.active_connections > 0:
            self.active_connections -= 1
    
    def get_stats(self) -> dict:
        """获取连接池状态"""
        return {
            'active': self.active_connections,
            'max': self.max_connections,
            'usage': f"{(self.active_connections / self.max_connections * 100):.1f}%"
        }
