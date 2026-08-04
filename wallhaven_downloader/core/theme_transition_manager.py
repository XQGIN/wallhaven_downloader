# -*- coding: utf-8 -*-
"""
主题过渡管理器
提供平滑的主题切换动画和颜色插值功能
"""

from typing import Dict, List, Callable, Optional
from PyQt5.QtCore import QObject, QTimer, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class ThemeTransitionManager(QObject):
    """
    主题过渡管理器
    
    负责管理主题切换时的平滑过渡动画，包括：
    - 颜色插值计算
    - 过渡动画控制
    - 组件更新协调
    - 性能优化
    
    特性：
    - 支持自定义过渡时长（300-500ms）
    - 使用缓动函数实现平滑过渡
    - 支持多组件同步更新
    - 自动清理和资源管理
    """
    
    # 信号
    transition_started = pyqtSignal()  # 过渡开始
    transition_progress = pyqtSignal(float)  # 过渡进度（0.0-1.0）
    transition_completed = pyqtSignal()  # 过渡完成
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        初始化主题过渡管理器
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        
        # 过渡配置
        self.default_duration = 400  # 默认过渡时长（毫秒）
        self.frame_interval = 16  # 帧间隔（约60 FPS）
        
        # 过渡状态
        self.is_transitioning = False
        self.current_progress = 0.0
        self.elapsed_time = 0
        self.target_duration = 0
        
        # 颜色缓存
        self.start_colors: Dict[str, QColor] = {}
        self.end_colors: Dict[str, QColor] = {}
        self.current_colors: Dict[str, QColor] = {}
        
        # 注册的组件和回调
        self.registered_widgets: List[QWidget] = []
        self.update_callbacks: List[Callable[[Dict[str, QColor]], None]] = []
        
        # 定时器
        self.transition_timer = QTimer(self)
        self.transition_timer.timeout.connect(self._on_transition_tick)
        
        # 缓动函数
        self.easing_curve = QEasingCurve(QEasingCurve.OutCubic)
        
        logger.debug("主题过渡管理器初始化完成")
    
    def start_transition(
        self,
        start_colors: Dict[str, QColor],
        end_colors: Dict[str, QColor],
        duration: int = None
    ) -> None:
        """
        开始主题过渡动画
        
        Args:
            start_colors: 起始颜色字典
            end_colors: 目标颜色字典
            duration: 过渡时长（毫秒），默认使用 default_duration
            
        Example:
            >>> manager = ThemeTransitionManager()
            >>> start = {"background": QColor(255, 255, 255)}
            >>> end = {"background": QColor(28, 28, 30)}
            >>> manager.start_transition(start, end, duration=400)
        """
        # 如果正在过渡，先停止
        if self.is_transitioning:
            self.stop_transition()
        
        # 设置过渡参数
        self.start_colors = start_colors.copy()
        self.end_colors = end_colors.copy()
        self.current_colors = start_colors.copy()
        self.target_duration = duration if duration is not None else self.default_duration
        
        # 重置状态
        self.is_transitioning = True
        self.current_progress = 0.0
        self.elapsed_time = 0
        
        # 发射开始信号
        self.transition_started.emit()
        
        # 启动定时器
        self.transition_timer.start(self.frame_interval)
        
        logger.debug(f"开始主题过渡动画，时长: {self.target_duration}ms")
    
    def stop_transition(self) -> None:
        """
        停止当前的过渡动画
        
        立即停止过渡并清理资源
        """
        if not self.is_transitioning:
            return
        
        # 停止定时器
        self.transition_timer.stop()
        
        # 重置状态
        self.is_transitioning = False
        self.current_progress = 0.0
        self.elapsed_time = 0
        
        logger.debug("主题过渡动画已停止")
    
    def _on_transition_tick(self) -> None:
        """
        过渡动画的每一帧更新
        
        计算当前进度，插值颜色，并通知所有注册的组件
        """
        # 更新经过时间
        self.elapsed_time += self.frame_interval
        
        # 计算原始进度（线性）
        raw_progress = min(1.0, self.elapsed_time / self.target_duration)
        
        # 应用缓动函数
        self.current_progress = self.easing_curve.valueForProgress(raw_progress)
        
        # 插值所有颜色
        self._interpolate_colors()
        
        # 通知所有回调
        self._notify_callbacks()
        
        # 发射进度信号
        self.transition_progress.emit(self.current_progress)
        
        # 检查是否完成
        if raw_progress >= 1.0:
            self._complete_transition()
    
    def _interpolate_colors(self) -> None:
        """
        插值所有颜色
        
        根据当前进度，在起始颜色和目标颜色之间进行线性插值
        """
        for color_name in self.start_colors.keys():
            if color_name in self.end_colors:
                start_color = self.start_colors[color_name]
                end_color = self.end_colors[color_name]
                
                # 插值颜色
                interpolated = self.interpolate_color(
                    start_color,
                    end_color,
                    self.current_progress
                )
                
                self.current_colors[color_name] = interpolated
    
    def _notify_callbacks(self) -> None:
        """
        通知所有注册的回调函数
        
        将当前插值后的颜色传递给所有回调
        """
        for callback in self.update_callbacks:
            try:
                callback(self.current_colors)
            except Exception as e:
                logger.error(f"主题过渡回调执行失败: {e}")
    
    def _complete_transition(self) -> None:
        """
        完成过渡动画
        
        停止定时器，清理资源，发射完成信号
        """
        # 停止定时器
        self.transition_timer.stop()
        
        # 确保最终颜色准确
        self.current_colors = self.end_colors.copy()
        self.current_progress = 1.0
        
        # 最后一次通知
        self._notify_callbacks()
        
        # 重置状态
        self.is_transitioning = False
        
        # 发射完成信号
        self.transition_completed.emit()
        
        logger.debug("主题过渡动画完成")
    
    @staticmethod
    def interpolate_color(
        start: QColor,
        end: QColor,
        progress: float
    ) -> QColor:
        """
        在两个颜色之间进行线性插值
        
        Args:
            start: 起始颜色
            end: 目标颜色
            progress: 进度（0.0-1.0）
            
        Returns:
            QColor: 插值后的颜色
            
        Example:
            >>> start = QColor(255, 255, 255)
            >>> end = QColor(0, 0, 0)
            >>> mid = ThemeTransitionManager.interpolate_color(start, end, 0.5)
            >>> print(mid.red(), mid.green(), mid.blue())  # 127, 127, 127
        """
        # 确保进度在有效范围内
        progress = max(0.0, min(1.0, progress))
        
        # 插值 RGBA 各分量
        r = int(start.red() + (end.red() - start.red()) * progress)
        g = int(start.green() + (end.green() - start.green()) * progress)
        b = int(start.blue() + (end.blue() - start.blue()) * progress)
        a = int(start.alpha() + (end.alpha() - start.alpha()) * progress)
        
        return QColor(r, g, b, a)
    
    def register_widget(self, widget: QWidget) -> None:
        """
        注册需要更新的组件
        
        Args:
            widget: 需要在主题过渡时更新的组件
            
        Note:
            注册的组件会在过渡时自动调用 update() 方法
        """
        if widget not in self.registered_widgets:
            self.registered_widgets.append(widget)
            logger.debug(f"注册组件: {widget.__class__.__name__}")
    
    def unregister_widget(self, widget: QWidget) -> None:
        """
        取消注册组件
        
        Args:
            widget: 要取消注册的组件
        """
        if widget in self.registered_widgets:
            self.registered_widgets.remove(widget)
            logger.debug(f"取消注册组件: {widget.__class__.__name__}")
    
    def register_callback(
        self,
        callback: Callable[[Dict[str, QColor]], None]
    ) -> None:
        """
        注册颜色更新回调函数
        
        Args:
            callback: 回调函数，接收当前颜色字典作为参数
            
        Example:
            >>> def on_colors_update(colors: Dict[str, QColor]):
            ...     print(f"背景色: {colors['background'].name()}")
            >>> manager.register_callback(on_colors_update)
        """
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
            logger.debug("注册颜色更新回调")
    
    def unregister_callback(
        self,
        callback: Callable[[Dict[str, QColor]], None]
    ) -> None:
        """
        取消注册回调函数
        
        Args:
            callback: 要取消注册的回调函数
        """
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
            logger.debug("取消注册颜色更新回调")
    
    def set_easing_curve(self, curve_type: QEasingCurve.Type) -> None:
        """
        设置缓动函数类型
        
        Args:
            curve_type: 缓动曲线类型
            
        常用类型：
            - QEasingCurve.Linear: 线性
            - QEasingCurve.InOutQuad: 二次缓入缓出
            - QEasingCurve.OutCubic: 三次缓出（默认）
            - QEasingCurve.InOutCubic: 三次缓入缓出
            
        Example:
            >>> manager.set_easing_curve(QEasingCurve.InOutCubic)
        """
        self.easing_curve = QEasingCurve(curve_type)
        logger.debug(f"设置缓动函数: {curve_type}")
    
    def set_default_duration(self, duration: int) -> None:
        """
        设置默认过渡时长
        
        Args:
            duration: 时长（毫秒），建议范围 300-500ms
            
        Example:
            >>> manager.set_default_duration(400)
        """
        if duration < 100:
            logger.warning(f"过渡时长过短: {duration}ms，建议至少 100ms")
        elif duration > 1000:
            logger.warning(f"过渡时长过长: {duration}ms，建议不超过 1000ms")
        
        self.default_duration = duration
        logger.debug(f"设置默认过渡时长: {duration}ms")
    
    def get_current_colors(self) -> Dict[str, QColor]:
        """
        获取当前插值后的颜色
        
        Returns:
            Dict[str, QColor]: 当前颜色字典
            
        Note:
            如果没有正在进行的过渡，返回空字典
        """
        return self.current_colors.copy()
    
    def get_progress(self) -> float:
        """
        获取当前过渡进度
        
        Returns:
            float: 进度值（0.0-1.0）
        """
        return self.current_progress
    
    def is_active(self) -> bool:
        """
        检查是否正在进行过渡
        
        Returns:
            bool: 是否正在过渡
        """
        return self.is_transitioning
    
    def clear(self) -> None:
        """
        清理所有注册的组件和回调
        
        停止当前过渡并清空所有注册
        """
        # 停止过渡
        if self.is_transitioning:
            self.stop_transition()
        
        # 清空注册
        self.registered_widgets.clear()
        self.update_callbacks.clear()
        
        # 清空颜色缓存
        self.start_colors.clear()
        self.end_colors.clear()
        self.current_colors.clear()
        
        logger.debug("主题过渡管理器已清理")


# 全局实例（可选）
_transition_manager_instance: Optional[ThemeTransitionManager] = None


def get_transition_manager() -> ThemeTransitionManager:
    """
    获取全局主题过渡管理器实例（单例模式）
    
    Returns:
        ThemeTransitionManager: 主题过渡管理器实例
        
    Example:
        >>> manager = get_transition_manager()
        >>> manager.set_default_duration(400)
    """
    global _transition_manager_instance
    if _transition_manager_instance is None:
        _transition_manager_instance = ThemeTransitionManager()
    return _transition_manager_instance
