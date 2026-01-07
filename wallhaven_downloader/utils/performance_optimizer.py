# -*- coding: utf-8 -*-
"""
性能优化器
提供虚拟滚动、组件缓存、性能降级和性能监控功能
"""

from typing import Dict, List, Optional, Any, Callable
from PyQt5.QtCore import QObject, QTimer, QElapsedTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget
import time
import psutil
import platform

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class VirtualScrollManager(QObject):
    """
    虚拟滚动管理器（需求 14.1）
    高效处理超过100个图片的列表
    """
    
    # 可见区域缓冲数量（上下各缓冲的项目数）
    BUFFER_SIZE = 10
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化虚拟滚动管理器
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 所有数据项
        self._all_items: List[Any] = []
        
        # 当前可见范围
        self._visible_start = 0
        self._visible_end = 0
        
        # 项目高度（用于计算可见范围）
        self._item_height = 100
        
        # 容器高度
        self._container_height = 0
        
        # 渲染回调函数
        self._render_callback: Optional[Callable] = None
        
        logger.info("虚拟滚动管理器已初始化")
    
    def set_items(self, items: List[Any]):
        """
        设置所有数据项
        
        Args:
            items: 数据项列表
        """
        self._all_items = items
        self._update_visible_range(0)
        logger.debug(f"虚拟滚动：设置 {len(items)} 个数据项")
    
    def set_item_height(self, height: int):
        """
        设置项目高度
        
        Args:
            height: 项目高度（像素）
        """
        self._item_height = height
    
    def set_container_height(self, height: int):
        """
        设置容器高度
        
        Args:
            height: 容器高度（像素）
        """
        self._container_height = height
    
    def set_render_callback(self, callback: Callable):
        """
        设置渲染回调函数
        
        Args:
            callback: 渲染函数，接收 (start_index, end_index, items) 参数
        """
        self._render_callback = callback
    
    def on_scroll(self, scroll_position: int):
        """
        处理滚动事件
        
        Args:
            scroll_position: 滚动位置（像素）
        """
        self._update_visible_range(scroll_position)
    
    def _update_visible_range(self, scroll_position: int):
        """
        更新可见范围并触发渲染
        
        Args:
            scroll_position: 滚动位置（像素）
        """
        if not self._all_items or self._item_height == 0:
            return
        
        # 计算可见范围（带缓冲）
        visible_count = max(1, self._container_height // self._item_height)
        start_index = max(0, (scroll_position // self._item_height) - self.BUFFER_SIZE)
        end_index = min(len(self._all_items), start_index + visible_count + self.BUFFER_SIZE * 2)
        
        # 如果范围变化，触发渲染
        if start_index != self._visible_start or end_index != self._visible_end:
            self._visible_start = start_index
            self._visible_end = end_index
            
            if self._render_callback:
                visible_items = self._all_items[start_index:end_index]
                self._render_callback(start_index, end_index, visible_items)
            
            logger.debug(f"虚拟滚动：可见范围 [{start_index}, {end_index})")
    
    def get_visible_range(self) -> tuple:
        """
        获取当前可见范围
        
        Returns:
            (start_index, end_index) 元组
        """
        return (self._visible_start, self._visible_end)
    
    def get_total_height(self) -> int:
        """
        获取总高度（用于设置滚动条范围）
        
        Returns:
            总高度（像素）
        """
        return len(self._all_items) * self._item_height


class ComponentCache(QObject):
    """
    组件缓存管理器（需求 14.4）
    缓存已渲染的组件，避免重复渲染
    """
    
    # 最大缓存数量
    MAX_CACHE_SIZE = 200
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化组件缓存管理器
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 缓存字典 {key: (component, last_access_time)}
        self._cache: Dict[str, tuple] = {}
        
        # 缓存命中统计
        self._hit_count = 0
        self._miss_count = 0
        
        logger.info("组件缓存管理器已初始化")
    
    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取组件
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的组件，如果不存在返回 None
        """
        if key in self._cache:
            component, _ = self._cache[key]
            # 更新访问时间
            self._cache[key] = (component, time.time())
            self._hit_count += 1
            logger.debug(f"缓存命中: {key}")
            return component
        else:
            self._miss_count += 1
            logger.debug(f"缓存未命中: {key}")
            return None
    
    def put(self, key: str, component: Any):
        """
        将组件放入缓存
        
        Args:
            key: 缓存键
            component: 要缓存的组件
        """
        # 如果缓存已满，移除最久未使用的项
        if len(self._cache) >= self.MAX_CACHE_SIZE:
            self._evict_lru()
        
        self._cache[key] = (component, time.time())
        logger.debug(f"缓存组件: {key}")
    
    def remove(self, key: str):
        """
        从缓存移除组件
        
        Args:
            key: 缓存键
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"移除缓存: {key}")
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        logger.info("清空组件缓存")
    
    def _evict_lru(self):
        """移除最久未使用的缓存项（LRU策略）"""
        if not self._cache:
            return
        
        # 找到最久未使用的项
        lru_key = min(self._cache.items(), key=lambda x: x[1][1])[0]
        del self._cache[lru_key]
        logger.debug(f"LRU淘汰: {lru_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.MAX_CACHE_SIZE,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate
        }


class PerformanceDegradation(QObject):
    """
    性能降级管理器（需求 14.5, 14.6）
    自动检测低性能设备并降低动画复杂度
    """
    
    # 性能阈值
    RESPONSE_TIME_THRESHOLD = 100  # 响应时间阈值（毫秒）
    
    # 性能模式
    MODE_HIGH = "high"  # 高性能模式
    MODE_MEDIUM = "medium"  # 中等性能模式
    MODE_LOW = "low"  # 低性能模式
    
    # 信号
    performance_mode_changed = pyqtSignal(str)  # 性能模式变化信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化性能降级管理器
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 当前性能模式
        self._current_mode = self.MODE_HIGH
        
        # 性能监控数据
        self._response_times: List[float] = []
        
        # 系统信息
        self._cpu_count = psutil.cpu_count()
        self._total_memory = psutil.virtual_memory().total / (1024 ** 3)  # GB
        
        # 自动检测设备性能
        self._detect_device_performance()
        
        logger.info(f"性能降级管理器已初始化，当前模式: {self._current_mode}")
    
    def _detect_device_performance(self):
        """自动检测设备性能（需求 14.5）"""
        try:
            # 获取系统信息
            system = platform.system()
            cpu_count = self._cpu_count
            total_memory = self._total_memory
            
            logger.info(f"系统信息: {system}, CPU核心数: {cpu_count}, 内存: {total_memory:.2f}GB")
            
            # 根据硬件配置判断性能等级
            if cpu_count >= 4 and total_memory >= 8:
                self._set_mode(self.MODE_HIGH)
            elif cpu_count >= 2 and total_memory >= 4:
                self._set_mode(self.MODE_MEDIUM)
            else:
                self._set_mode(self.MODE_LOW)
                logger.warning("检测到低性能设备，已启用性能降级模式")
        
        except Exception as e:
            logger.error(f"检测设备性能失败: {str(e)}")
            self._set_mode(self.MODE_MEDIUM)
    
    def record_response_time(self, response_time: float):
        """
        记录响应时间（需求 14.6）
        
        Args:
            response_time: 响应时间（毫秒）
        """
        self._response_times.append(response_time)
        
        # 只保留最近50次
        if len(self._response_times) > 50:
            self._response_times.pop(0)
        
        # 检查是否需要降级
        self._check_performance()
    
    def _check_performance(self):
        """检查性能并自动调整模式"""
        if len(self._response_times) < 10:
            return
        
        # 计算平均响应时间
        avg_response_time = 0
        if self._response_times:
            avg_response_time = sum(self._response_times) / len(self._response_times)
        
        # 根据性能指标调整模式
        if avg_response_time > self.RESPONSE_TIME_THRESHOLD:
            if self._current_mode == self.MODE_HIGH:
                self._set_mode(self.MODE_MEDIUM)
                logger.warning(f"性能下降，切换到中等性能模式 (响应时间: {avg_response_time:.1f}ms)")
            elif self._current_mode == self.MODE_MEDIUM:
                self._set_mode(self.MODE_LOW)
                logger.warning(f"性能持续下降，切换到低性能模式 (响应时间: {avg_response_time:.1f}ms)")
        elif avg_response_time < 50:
            # 性能恢复，可以升级模式
            if self._current_mode == self.MODE_LOW:
                self._set_mode(self.MODE_MEDIUM)
                logger.info(f"性能恢复，切换到中等性能模式 (响应时间: {avg_response_time:.1f}ms)")
            elif self._current_mode == self.MODE_MEDIUM:
                self._set_mode(self.MODE_HIGH)
                logger.info(f"性能良好，切换到高性能模式 (响应时间: {avg_response_time:.1f}ms)")
    
    def _set_mode(self, mode: str):
        """
        设置性能模式
        
        Args:
            mode: 性能模式
        """
        if mode != self._current_mode:
            self._current_mode = mode
            self.performance_mode_changed.emit(mode)
            logger.info(f"性能模式已切换: {mode}")
    
    def get_mode(self) -> str:
        """
        获取当前性能模式
        
        Returns:
            当前性能模式
        """
        return self._current_mode
    
    def should_reduce_animations(self) -> bool:
        """
        是否应该降低动画复杂度（需求 14.5）
        
        Returns:
            True 如果应该降低动画复杂度
        """
        return self._current_mode in [self.MODE_MEDIUM, self.MODE_LOW]
    
    def should_disable_animations(self) -> bool:
        """
        是否应该禁用动画
        
        Returns:
            True 如果应该禁用动画
        """
        return self._current_mode == self.MODE_LOW
    
    def get_animation_duration_multiplier(self) -> float:
        """
        获取动画时长倍数
        
        Returns:
            动画时长倍数（0.5 = 减半，1.0 = 正常）
        """
        if self._current_mode == self.MODE_HIGH:
            return 1.0
        elif self._current_mode == self.MODE_MEDIUM:
            return 0.7
        else:  # LOW
            return 0.5
    
    def get_max_concurrent_animations(self) -> int:
        """
        获取最大并发动画数量
        
        Returns:
            最大并发动画数量
        """
        if self._current_mode == self.MODE_HIGH:
            return 5
        elif self._current_mode == self.MODE_MEDIUM:
            return 3
        else:  # LOW
            return 1


class PerformanceMonitor(QObject):
    """
    性能监控器（需求 14.6）
    跟踪响应时间
    """
    
    # 信号
    stats_updated = pyqtSignal(dict)  # 统计信息更新信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化性能监控器
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 响应时间监控
        self._operation_timers: Dict[str, QElapsedTimer] = {}
        self._response_times: Dict[str, List[float]] = {}
        
        # 定时更新统计信息
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start(1000)  # 每秒更新一次
        
        logger.info("性能监控器已初始化")
    
    def start_operation(self, operation_name: str):
        """
        开始记录操作时间
        
        Args:
            operation_name: 操作名称
        """
        timer = QElapsedTimer()
        timer.start()
        self._operation_timers[operation_name] = timer
    
    def end_operation(self, operation_name: str):
        """
        结束记录操作时间
        
        Args:
            operation_name: 操作名称
        """
        if operation_name in self._operation_timers:
            timer = self._operation_timers[operation_name]
            elapsed = timer.elapsed()
            
            # 记录响应时间
            if operation_name not in self._response_times:
                self._response_times[operation_name] = []
            
            self._response_times[operation_name].append(elapsed)
            
            # 只保留最近50次
            if len(self._response_times[operation_name]) > 50:
                self._response_times[operation_name].pop(0)
            
            del self._operation_timers[operation_name]
            
            # 如果响应时间超过阈值，记录警告
            if elapsed > 100:
                logger.warning(f"操作 '{operation_name}' 响应时间过长: {elapsed}ms")
    
    def _update_stats(self):
        """更新统计信息"""
        # 计算平均响应时间
        avg_response_times = {}
        for operation, times in self._response_times.items():
            if times:
                avg_response_times[operation] = sum(times) / len(times)
        
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        
        # 发送统计信息
        stats = {
            "avg_response_times": avg_response_times,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent
        }
        
        self.stats_updated.emit(stats)
    
    def get_current_fps(self) -> float:
        """
        获取当前帧率（已移除帧率监控功能）
        
        Returns:
            固定返回 60.0，保持接口兼容性
        """
        return 60.0
    
    def get_avg_response_time(self, operation_name: str) -> float:
        """
        获取指定操作的平均响应时间
        
        Args:
            operation_name: 操作名称
            
        Returns:
            平均响应时间（毫秒），如果没有记录返回 0
        """
        if operation_name in self._response_times and self._response_times[operation_name]:
            return sum(self._response_times[operation_name]) / len(self._response_times[operation_name])
        return 0


class PerformanceOptimizer(QObject):
    """
    性能优化器总管理器
    整合虚拟滚动、组件缓存、性能降级和性能监控
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化性能优化器
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 创建子管理器
        self.virtual_scroll = VirtualScrollManager(parent)
        self.component_cache = ComponentCache(parent)
        self.degradation = PerformanceDegradation(parent)
        self.monitor = PerformanceMonitor(parent)
        
        # 连接性能降级信号
        self.degradation.performance_mode_changed.connect(self._on_performance_mode_changed)
        
        # 连接性能监控信号
        self.monitor.stats_updated.connect(self._on_stats_updated)
        
        logger.info("性能优化器已初始化")
    
    def _on_performance_mode_changed(self, mode: str):
        """
        性能模式变化处理
        
        Args:
            mode: 新的性能模式
        """
        logger.info(f"性能模式已变化: {mode}")
        
        # 根据性能模式调整缓存大小
        if mode == PerformanceDegradation.MODE_LOW:
            self.component_cache.MAX_CACHE_SIZE = 100
        elif mode == PerformanceDegradation.MODE_MEDIUM:
            self.component_cache.MAX_CACHE_SIZE = 150
        else:
            self.component_cache.MAX_CACHE_SIZE = 200
    
    def _on_stats_updated(self, stats: Dict[str, Any]):
        """
        统计信息更新处理
        
        Args:
            stats: 统计信息
        """
        # 记录响应时间
        avg_response_times = stats.get("avg_response_times", {})
        for operation, time in avg_response_times.items():
            self.degradation.record_response_time(time)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "performance_mode": self.degradation.get_mode(),
            "cache_stats": self.component_cache.get_stats(),
            "should_reduce_animations": self.degradation.should_reduce_animations(),
            "animation_duration_multiplier": self.degradation.get_animation_duration_multiplier(),
            "max_concurrent_animations": self.degradation.get_max_concurrent_animations()
        }
