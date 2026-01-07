# -*- coding: utf-8 -*-
"""
性能降级管理器

自动检测性能问题并降级视觉效果以保持流畅性
需求：14.6
"""

from typing import Optional, Dict, List, Callable
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
import psutil
import time

try:
    from utils.logger import get_logger
except ImportError:
    from .logger import get_logger

logger = get_logger(__name__)


class PerformanceDegradationManager(QObject):
    """
    性能降级管理器
    
    负责：
    1. 监控系统性能指标（FPS、CPU、内存）
    2. 自动检测性能问题
    3. 触发降级策略
    4. 管理降级级别
    
    需求：14.6
    """
    
    # 信号
    degradation_level_changed = pyqtSignal(str)  # 降级级别变化 (none, low, medium, high)
    performance_warning = pyqtSignal(str, dict)  # 性能警告 (原因, 指标)
    degradation_triggered = pyqtSignal(str)  # 降级触发 (原因)
    degradation_recovered = pyqtSignal()  # 性能恢复
    
    # 降级级别
    LEVEL_NONE = "none"  # 无降级
    LEVEL_LOW = "low"  # 轻度降级
    LEVEL_MEDIUM = "medium"  # 中度降级
    LEVEL_HIGH = "high"  # 重度降级
    
    # 性能阈值
    FPS_THRESHOLD_CRITICAL = 20  # 严重性能问题
    FPS_THRESHOLD_LOW = 30  # 低性能
    FPS_THRESHOLD_NORMAL = 50  # 正常性能
    FPS_THRESHOLD_GOOD = 55  # 良好性能
    
    CPU_THRESHOLD_HIGH = 80  # CPU 使用率高阈值（%）
    CPU_THRESHOLD_CRITICAL = 90  # CPU 使用率严重阈值（%）
    
    MEMORY_THRESHOLD_HIGH = 80  # 内存使用率高阈值（%）
    MEMORY_THRESHOLD_CRITICAL = 90  # 内存使用率严重阈值（%）
    
    # 监控配置
    MONITOR_INTERVAL = 1000  # 监控间隔（毫秒）
    SAMPLE_SIZE = 10  # 样本数量
    RECOVERY_THRESHOLD = 5  # 恢复阈值（连续良好样本数）
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        初始化性能降级管理器
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        
        # 当前降级级别
        self._degradation_level = self.LEVEL_NONE
        
        # 性能监控数据
        self._fps_samples: List[float] = []
        self._cpu_samples: List[float] = []
        self._memory_samples: List[float] = []
        self._response_time_samples: List[float] = []
        
        # 性能问题计数器
        self._poor_performance_count = 0
        self._good_performance_count = 0
        
        # 监控定时器
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._monitor_performance)
        
        # 自动降级开关
        self._auto_degradation_enabled = True
        
        # 降级策略回调
        self._degradation_callbacks: Dict[str, List[Callable]] = {
            self.LEVEL_LOW: [],
            self.LEVEL_MEDIUM: [],
            self.LEVEL_HIGH: []
        }
        
        # 恢复策略回调
        self._recovery_callbacks: List[Callable] = []
        
        # 系统信息
        self._cpu_count = psutil.cpu_count()
        self._total_memory = psutil.virtual_memory().total / (1024 ** 3)  # GB
        
        # 性能基线（用于判断设备性能等级）
        self._device_performance_tier = self._detect_device_tier()
        
        logger.info(f"性能降级管理器已初始化 - 设备等级: {self._device_performance_tier}, "
                   f"CPU核心: {self._cpu_count}, 内存: {self._total_memory:.1f}GB")
    
    def _detect_device_tier(self) -> str:
        """
        检测设备性能等级
        
        Returns:
            设备等级 (high, medium, low)
        """
        try:
            cpu_count = self._cpu_count
            total_memory = self._total_memory
            
            # 高性能设备：4核以上 + 8GB以上内存
            if cpu_count >= 4 and total_memory >= 8:
                return "high"
            # 中等性能设备：2核以上 + 4GB以上内存
            elif cpu_count >= 2 and total_memory >= 4:
                return "medium"
            # 低性能设备
            else:
                return "low"
        except Exception as e:
            logger.error(f"检测设备性能等级失败: {e}")
            return "medium"
    
    def start_monitoring(self):
        """
        启动性能监控
        
        需求：14.6
        """
        if not self._monitor_timer.isActive():
            self._monitor_timer.start(self.MONITOR_INTERVAL)
            logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        if self._monitor_timer.isActive():
            self._monitor_timer.stop()
            logger.info("性能监控已停止")
    
    def _monitor_performance(self):
        """
        监控性能指标
        
        定期采集 CPU、内存使用率，并根据样本判断是否需要降级
        """
        try:
            # 采集 CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self._cpu_samples.append(cpu_percent)
            
            # 采集内存使用率
            memory_percent = psutil.virtual_memory().percent
            self._memory_samples.append(memory_percent)
            
            # 限制样本数量
            if len(self._cpu_samples) > self.SAMPLE_SIZE:
                self._cpu_samples.pop(0)
            if len(self._memory_samples) > self.SAMPLE_SIZE:
                self._memory_samples.pop(0)
            if len(self._fps_samples) > self.SAMPLE_SIZE:
                self._fps_samples.pop(0)
            if len(self._response_time_samples) > self.SAMPLE_SIZE:
                self._response_time_samples.pop(0)
            
            # 检查是否需要降级或恢复
            if self._auto_degradation_enabled:
                self._check_degradation_needed()
        
        except Exception as e:
            logger.error(f"性能监控失败: {e}")
    
    def record_fps(self, fps: float):
        """
        记录 FPS 样本
        
        Args:
            fps: 当前 FPS 值
        """
        self._fps_samples.append(fps)
        if len(self._fps_samples) > self.SAMPLE_SIZE:
            self._fps_samples.pop(0)
    
    def record_response_time(self, response_time: float):
        """
        记录响应时间样本
        
        Args:
            response_time: 响应时间（毫秒）
        """
        self._response_time_samples.append(response_time)
        if len(self._response_time_samples) > self.SAMPLE_SIZE:
            self._response_time_samples.pop(0)
    
    def _check_degradation_needed(self):
        """
        检查是否需要降级或恢复
        
        需求：14.6
        """
        # 计算平均值
        avg_fps = self._get_average(self._fps_samples)
        avg_cpu = self._get_average(self._cpu_samples)
        avg_memory = self._get_average(self._memory_samples)
        avg_response_time = self._get_average(self._response_time_samples)
        
        # 判断性能状态
        is_poor_performance = False
        performance_issues = []
        
        # 检查 FPS
        if avg_fps > 0 and avg_fps < self.FPS_THRESHOLD_LOW:
            is_poor_performance = True
            performance_issues.append(f"FPS过低 ({avg_fps:.1f})")
        
        # 检查 CPU
        if avg_cpu > self.CPU_THRESHOLD_HIGH:
            is_poor_performance = True
            performance_issues.append(f"CPU使用率过高 ({avg_cpu:.1f}%)")
        
        # 检查内存
        if avg_memory > self.MEMORY_THRESHOLD_HIGH:
            is_poor_performance = True
            performance_issues.append(f"内存使用率过高 ({avg_memory:.1f}%)")
        
        # 检查响应时间
        if avg_response_time > 100:
            is_poor_performance = True
            performance_issues.append(f"响应时间过长 ({avg_response_time:.1f}ms)")
        
        # 更新性能计数器
        if is_poor_performance:
            self._poor_performance_count += 1
            self._good_performance_count = 0
            
            # 连续多次性能不佳，触发降级
            if self._poor_performance_count >= 3:
                self._trigger_degradation(performance_issues, avg_fps, avg_cpu, avg_memory)
        else:
            self._good_performance_count += 1
            self._poor_performance_count = 0
            
            # 连续多次性能良好，尝试恢复
            if self._good_performance_count >= self.RECOVERY_THRESHOLD:
                self._try_recovery()
    
    def _trigger_degradation(self, issues: List[str], fps: float, cpu: float, memory: float):
        """
        触发性能降级
        
        Args:
            issues: 性能问题列表
            fps: 平均 FPS
            cpu: 平均 CPU 使用率
            memory: 平均内存使用率
        """
        # 确定降级级别
        new_level = self._calculate_degradation_level(fps, cpu, memory)
        
        # 如果级别变化，应用降级
        if new_level != self._degradation_level:
            old_level = self._degradation_level
            self._degradation_level = new_level
            
            # 发出信号
            self.degradation_level_changed.emit(new_level)
            self.degradation_triggered.emit(", ".join(issues))
            
            # 执行降级回调
            self._execute_degradation_callbacks(new_level)
            
            logger.warning(f"性能降级触发: {old_level} -> {new_level}, 原因: {', '.join(issues)}")
            logger.info(f"性能指标 - FPS: {fps:.1f}, CPU: {cpu:.1f}%, 内存: {memory:.1f}%")
    
    def _calculate_degradation_level(self, fps: float, cpu: float, memory: float) -> str:
        """
        计算应该应用的降级级别
        
        Args:
            fps: 平均 FPS
            cpu: 平均 CPU 使用率
            memory: 平均内存使用率
            
        Returns:
            降级级别
        """
        # 严重性能问题 - 重度降级
        if (fps > 0 and fps < self.FPS_THRESHOLD_CRITICAL) or \
           cpu > self.CPU_THRESHOLD_CRITICAL or \
           memory > self.MEMORY_THRESHOLD_CRITICAL:
            return self.LEVEL_HIGH
        
        # 中等性能问题 - 中度降级
        if (fps > 0 and fps < self.FPS_THRESHOLD_LOW) or \
           cpu > self.CPU_THRESHOLD_HIGH or \
           memory > self.MEMORY_THRESHOLD_HIGH:
            # 如果当前已经是重度降级，保持
            if self._degradation_level == self.LEVEL_HIGH:
                return self.LEVEL_HIGH
            return self.LEVEL_MEDIUM
        
        # 轻微性能问题 - 轻度降级
        if (fps > 0 and fps < self.FPS_THRESHOLD_NORMAL):
            # 如果当前已经是中度或重度降级，保持
            if self._degradation_level in [self.LEVEL_MEDIUM, self.LEVEL_HIGH]:
                return self._degradation_level
            return self.LEVEL_LOW
        
        return self._degradation_level
    
    def _try_recovery(self):
        """
        尝试恢复性能级别
        
        当性能持续良好时，逐步恢复到正常状态
        """
        if self._degradation_level == self.LEVEL_NONE:
            return
        
        # 逐级恢复
        old_level = self._degradation_level
        
        if self._degradation_level == self.LEVEL_HIGH:
            self._degradation_level = self.LEVEL_MEDIUM
        elif self._degradation_level == self.LEVEL_MEDIUM:
            self._degradation_level = self.LEVEL_LOW
        elif self._degradation_level == self.LEVEL_LOW:
            self._degradation_level = self.LEVEL_NONE
            self.degradation_recovered.emit()
        
        # 发出信号
        self.degradation_level_changed.emit(self._degradation_level)
        
        # 执行恢复回调
        if self._degradation_level == self.LEVEL_NONE:
            self._execute_recovery_callbacks()
        else:
            self._execute_degradation_callbacks(self._degradation_level)
        
        logger.info(f"性能恢复: {old_level} -> {self._degradation_level}")
        
        # 重置计数器
        self._good_performance_count = 0
    
    def _execute_degradation_callbacks(self, level: str):
        """
        执行降级回调
        
        Args:
            level: 降级级别
        """
        callbacks = self._degradation_callbacks.get(level, [])
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"执行降级回调失败: {e}")
    
    def _execute_recovery_callbacks(self):
        """执行恢复回调"""
        for callback in self._recovery_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"执行恢复回调失败: {e}")
    
    def register_degradation_callback(self, level: str, callback: Callable):
        """
        注册降级回调
        
        Args:
            level: 降级级别
            callback: 回调函数
        """
        if level in self._degradation_callbacks:
            self._degradation_callbacks[level].append(callback)
            logger.debug(f"注册降级回调: {level}")
    
    def register_recovery_callback(self, callback: Callable):
        """
        注册恢复回调
        
        Args:
            callback: 回调函数
        """
        self._recovery_callbacks.append(callback)
        logger.debug("注册恢复回调")
    
    def _get_average(self, samples: List[float]) -> float:
        """
        计算样本平均值
        
        Args:
            samples: 样本列表
            
        Returns:
            平均值
        """
        if not samples:
            return 0.0
        return sum(samples) / len(samples)
    
    def get_degradation_level(self) -> str:
        """
        获取当前降级级别
        
        Returns:
            降级级别
        """
        return self._degradation_level
    
    def set_degradation_level(self, level: str):
        """
        手动设置降级级别
        
        Args:
            level: 降级级别
        """
        if level not in [self.LEVEL_NONE, self.LEVEL_LOW, self.LEVEL_MEDIUM, self.LEVEL_HIGH]:
            logger.warning(f"无效的降级级别: {level}")
            return
        
        old_level = self._degradation_level
        self._degradation_level = level
        
        if old_level != level:
            self.degradation_level_changed.emit(level)
            self._execute_degradation_callbacks(level)
            logger.info(f"手动设置降级级别: {old_level} -> {level}")
    
    def enable_auto_degradation(self):
        """
        启用自动降级
        
        需求：14.6
        """
        self._auto_degradation_enabled = True
        logger.info("自动降级已启用")
    
    def disable_auto_degradation(self):
        """禁用自动降级"""
        self._auto_degradation_enabled = False
        logger.info("自动降级已禁用")
    
    def is_auto_degradation_enabled(self) -> bool:
        """
        检查是否启用自动降级
        
        Returns:
            是否启用
        """
        return self._auto_degradation_enabled
    
    def get_performance_stats(self) -> Dict:
        """
        获取性能统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "degradation_level": self._degradation_level,
            "device_tier": self._device_performance_tier,
            "auto_degradation_enabled": self._auto_degradation_enabled,
            "average_fps": self._get_average(self._fps_samples),
            "average_cpu": self._get_average(self._cpu_samples),
            "average_memory": self._get_average(self._memory_samples),
            "average_response_time": self._get_average(self._response_time_samples),
            "poor_performance_count": self._poor_performance_count,
            "good_performance_count": self._good_performance_count,
            "cpu_count": self._cpu_count,
            "total_memory_gb": self._total_memory
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self._fps_samples.clear()
        self._cpu_samples.clear()
        self._memory_samples.clear()
        self._response_time_samples.clear()
        self._poor_performance_count = 0
        self._good_performance_count = 0
        logger.debug("性能统计已重置")
    
    def get_device_tier(self) -> str:
        """
        获取设备性能等级
        
        Returns:
            设备等级 (high, medium, low)
        """
        return self._device_performance_tier


# 全局单例
_performance_degradation_manager_instance: Optional[PerformanceDegradationManager] = None


def get_performance_degradation_manager() -> PerformanceDegradationManager:
    """
    获取性能降级管理器单例
    
    Returns:
        PerformanceDegradationManager 实例
    """
    global _performance_degradation_manager_instance
    if _performance_degradation_manager_instance is None:
        _performance_degradation_manager_instance = PerformanceDegradationManager()
    return _performance_degradation_manager_instance
