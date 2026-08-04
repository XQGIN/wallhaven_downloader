# -*- coding: utf-8 -*-
"""
动画管理器
提供统一的动画系统，管理所有 UI 动画效果
"""

from typing import List, Optional, Callable
from PyQt5.QtCore import QObject, QPropertyAnimation, QEasingCurve, QPoint, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtGui import QPainter, QColor, QPainterPath
from PyQt5.QtCore import Qt, QRect

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class AnimationManager(QObject):
    """
    动画管理器
    
    统一管理所有动画效果，确保性能和一致性
    提供标准的缓动函数和动画时长
    """
    
    # 标准缓动函数
    EASING_CURVE = QEasingCurve.InOutCubic
    
    # 标准动画时长（毫秒）
    DURATION_FAST = 150      # 快速动画
    DURATION_NORMAL = 200    # 正常动画
    DURATION_SLOW = 300      # 慢速动画
    
    # 性能管理
    MAX_CONCURRENT_ANIMATIONS = 5  # 最大并发动画数
    
    def __init__(self):
        """初始化动画管理器"""
        super().__init__()
        self.active_animations: List[QPropertyAnimation] = []  # 活动动画列表
        self.animation_queue: List[tuple] = []  # 动画队列
        self.animations_enabled = True  # 动画启用标志
        self.performance_mode = False  # 性能模式标志
        
        logger.debug("AnimationManager 初始化完成")
    
    def create_fade_animation(
        self,
        widget: QWidget,
        start_opacity: float = 0.0,
        end_opacity: float = 1.0,
        duration: int = None,
        easing: QEasingCurve.Type = None,
        callback: Optional[Callable] = None
    ) -> Optional[QPropertyAnimation]:
        """
        创建淡入淡出动画
        
        Args:
            widget: 目标组件
            start_opacity: 起始透明度 (0.0-1.0)
            end_opacity: 结束透明度 (0.0-1.0)
            duration: 动画时长（毫秒），默认使用 DURATION_NORMAL
            easing: 缓动函数，默认使用 EASING_CURVE
            callback: 动画完成后的回调函数
            
        Returns:
            QPropertyAnimation 对象，如果动画被禁用则返回 None
        """
        if not self.animations_enabled:
            # 动画禁用时直接设置最终状态
            if callback:
                callback()
            return None
        
        # 检查并发限制
        if not self._can_start_animation():
            self._queue_animation('fade', widget, start_opacity, end_opacity, duration, easing, callback)
            return None
        
        # 创建透明度效果
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(start_opacity)
        
        # 创建动画
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration or self.DURATION_NORMAL)
        animation.setEasingCurve(easing or self.EASING_CURVE)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        
        # 连接完成信号
        def on_finished():
            self._on_animation_finished(animation)
            if callback:
                callback()
            # 清理图形效果
            widget.setGraphicsEffect(None)
        
        animation.finished.connect(on_finished)
        
        # 添加到活动列表并启动
        self._start_animation(animation)
        
        logger.debug(f"创建淡入淡出动画: {widget.__class__.__name__}, {start_opacity} -> {end_opacity}")
        return animation
    
    def create_slide_animation(
        self,
        widget: QWidget,
        direction: str,
        distance: int = 100,
        duration: int = None,
        easing: QEasingCurve.Type = None,
        callback: Optional[Callable] = None
    ) -> Optional[QPropertyAnimation]:
        """
        创建滑动动画
        
        Args:
            widget: 目标组件
            direction: 滑动方向 ('left', 'right', 'up', 'down')
            distance: 滑动距离（像素）
            duration: 动画时长（毫秒），默认使用 DURATION_NORMAL
            easing: 缓动函数，默认使用 EASING_CURVE
            callback: 动画完成后的回调函数
            
        Returns:
            QPropertyAnimation 对象，如果动画被禁用则返回 None
        """
        if not self.animations_enabled:
            if callback:
                callback()
            return None
        
        # 检查并发限制
        if not self._can_start_animation():
            self._queue_animation('slide', widget, direction, distance, duration, easing, callback)
            return None
        
        # 获取当前位置
        current_pos = widget.pos()
        
        # 计算起始和结束位置
        if direction == 'left':
            start_pos = QPoint(current_pos.x() + distance, current_pos.y())
            end_pos = current_pos
        elif direction == 'right':
            start_pos = QPoint(current_pos.x() - distance, current_pos.y())
            end_pos = current_pos
        elif direction == 'up':
            start_pos = QPoint(current_pos.x(), current_pos.y() + distance)
            end_pos = current_pos
        elif direction == 'down':
            start_pos = QPoint(current_pos.x(), current_pos.y() - distance)
            end_pos = current_pos
        else:
            logger.warning(f"未知的滑动方向: {direction}")
            return None
        
        # 设置起始位置
        widget.move(start_pos)
        
        # 创建动画
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration or self.DURATION_NORMAL)
        animation.setEasingCurve(easing or self.EASING_CURVE)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        
        # 连接完成信号
        def on_finished():
            self._on_animation_finished(animation)
            if callback:
                callback()
        
        animation.finished.connect(on_finished)
        
        # 添加到活动列表并启动
        self._start_animation(animation)
        
        logger.debug(f"创建滑动动画: {widget.__class__.__name__}, 方向={direction}, 距离={distance}")
        return animation
    
    def create_ripple_effect(
        self,
        widget: QWidget,
        pos: QPoint,
        color: QColor = None,
        duration: int = None
    ):
        """
        创建波纹效果
        
        Args:
            widget: 目标组件
            pos: 波纹起始位置
            color: 波纹颜色，默认使用主题主色
            duration: 动画时长（毫秒），默认使用 DURATION_NORMAL
        """
        if not self.animations_enabled:
            return
        
        # 检查并发限制
        if not self._can_start_animation():
            logger.debug("波纹效果因并发限制被跳过")
            return
        
        # 创建波纹效果组件
        ripple = RippleEffect(widget, pos, color, duration or self.DURATION_NORMAL)
        
        # 连接完成信号
        def on_finished():
            self._on_animation_finished(ripple.animation)
            ripple.deleteLater()
        
        ripple.animation.finished.connect(on_finished)
        
        # 添加到活动列表并启动
        self._start_animation(ripple.animation)
        ripple.start()
        
        logger.debug(f"创建波纹效果: {widget.__class__.__name__}, 位置={pos}")
    
    def create_staggered_animation(
        self,
        widgets: List[QWidget],
        animation_type: str = 'fade',
        delay: int = 50,
        duration: int = None,
        callback: Optional[Callable] = None
    ):
        """
        创建交错动画（列表项依次出现）
        
        Args:
            widgets: 组件列表
            animation_type: 动画类型 ('fade' 或 'slide')
            delay: 每项之间的延迟（毫秒）
            duration: 每个动画的时长（毫秒），默认使用 DURATION_NORMAL
            callback: 所有动画完成后的回调函数
        """
        if not self.animations_enabled or not widgets:
            if callback:
                callback()
            return
        
        total_animations = len(widgets)
        completed_count = [0]  # 使用列表以便在闭包中修改
        
        def on_single_animation_finished():
            completed_count[0] += 1
            if completed_count[0] >= total_animations and callback:
                callback()
        
        for i, widget in enumerate(widgets):
            # 使用 QTimer 延迟启动每个动画
            QTimer.singleShot(i * delay, lambda w=widget: self._start_staggered_item(
                w, animation_type, duration, on_single_animation_finished
            ))
        
        logger.debug(f"创建交错动画: {len(widgets)} 个组件, 延迟={delay}ms")
    
    def _start_staggered_item(
        self,
        widget: QWidget,
        animation_type: str,
        duration: int,
        callback: Callable
    ):
        """启动单个交错动画项"""
        if animation_type == 'fade':
            self.create_fade_animation(
                widget,
                start_opacity=0.0,
                end_opacity=1.0,
                duration=duration,
                callback=callback
            )
        elif animation_type == 'slide':
            self.create_slide_animation(
                widget,
                direction='up',
                distance=20,
                duration=duration,
                callback=callback
            )
    
    def _can_start_animation(self) -> bool:
        """检查是否可以启动新动画"""
        # 清理已完成的动画
        self.active_animations = [anim for anim in self.active_animations if anim.state() == QPropertyAnimation.Running]
        
        return len(self.active_animations) < self.MAX_CONCURRENT_ANIMATIONS
    
    def _start_animation(self, animation: QPropertyAnimation):
        """启动动画并添加到活动列表"""
        self.active_animations.append(animation)
        animation.start()
    
    def _on_animation_finished(self, animation: QPropertyAnimation):
        """动画完成处理"""
        if animation in self.active_animations:
            self.active_animations.remove(animation)
        
        # 处理队列中的动画
        self._process_queue()
    
    def _queue_animation(self, anim_type: str, *args, **kwargs):
        """将动画添加到队列"""
        self.animation_queue.append((anim_type, args, kwargs))
        logger.debug(f"动画已加入队列: {anim_type}, 队列长度={len(self.animation_queue)}")
    
    def _process_queue(self):
        """处理队列中的动画"""
        if not self.animation_queue or not self._can_start_animation():
            return
        
        # 取出队列中的第一个动画
        anim_type, args, kwargs = self.animation_queue.pop(0)
        
        # 根据类型创建动画
        if anim_type == 'fade':
            self.create_fade_animation(*args, **kwargs)
        elif anim_type == 'slide':
            self.create_slide_animation(*args, **kwargs)
    
    def enable_animations(self):
        """启用动画"""
        self.animations_enabled = True
        logger.info("动画已启用")
    
    def disable_animations(self):
        """禁用动画"""
        self.animations_enabled = False
        # 停止所有活动动画
        for animation in self.active_animations:
            animation.stop()
        self.active_animations.clear()
        self.animation_queue.clear()
        logger.info("动画已禁用")
    
    def enable_performance_mode(self):
        """启用性能模式（降低动画复杂度）"""
        self.performance_mode = True
        # 减少并发动画数量
        self.MAX_CONCURRENT_ANIMATIONS = 2
        logger.info("性能模式已启用")
    
    def disable_performance_mode(self):
        """禁用性能模式"""
        self.performance_mode = False
        self.MAX_CONCURRENT_ANIMATIONS = 5
        logger.info("性能模式已禁用")
    
    def get_active_animation_count(self) -> int:
        """获取当前活动动画数量"""
        # 清理已完成的动画
        self.active_animations = [anim for anim in self.active_animations if anim.state() == QPropertyAnimation.Running]
        return len(self.active_animations)
    
    def stop_all_animations(self):
        """停止所有动画"""
        for animation in self.active_animations:
            animation.stop()
        self.active_animations.clear()
        self.animation_queue.clear()
        logger.debug("所有动画已停止")


class RippleEffect(QWidget):
    """波纹效果组件"""
    
    def __init__(self, parent: QWidget, pos: QPoint, color: QColor = None, duration: int = 200):
        """
        初始化波纹效果
        
        Args:
            parent: 父组件
            pos: 波纹起始位置
            color: 波纹颜色
            duration: 动画时长
        """
        super().__init__(parent)
        self.ripple_pos = pos
        self.ripple_color = color or QColor(255, 255, 255, 100)
        self._ripple_radius = 0  # 使用私有变量避免递归
        self.max_radius = max(parent.width(), parent.height())
        
        # 设置组件属性
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(parent.rect())
        
        # 创建动画
        self.animation = QPropertyAnimation(self, b"ripple_radius")
        self.animation.setDuration(duration)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setStartValue(0)
        self.animation.setEndValue(self.max_radius)
        
        # 连接动画更新信号
        self.animation.valueChanged.connect(self.update)
    
    def start(self):
        """启动波纹动画"""
        self.show()
        self.animation.start()
    
    def paintEvent(self, event):
        """绘制波纹"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置波纹颜色（随半径增大而透明度降低）
        alpha = int(self.ripple_color.alpha() * (1 - self._ripple_radius / self.max_radius))
        color = QColor(self.ripple_color.red(), self.ripple_color.green(), self.ripple_color.blue(), alpha)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        # 绘制圆形波纹
        painter.drawEllipse(self.ripple_pos, int(self._ripple_radius), int(self._ripple_radius))
    
    def get_ripple_radius(self) -> int:
        """获取波纹半径"""
        return self._ripple_radius
    
    def set_ripple_radius(self, radius: int):
        """设置波纹半径"""
        self._ripple_radius = radius
    
    # 定义属性以便 QPropertyAnimation 使用
    ripple_radius = property(get_ripple_radius, set_ripple_radius)


# 全局单例
_animation_manager_instance: Optional[AnimationManager] = None


def get_animation_manager() -> AnimationManager:
    """
    获取动画管理器单例
    
    Returns:
        AnimationManager 实例
    """
    global _animation_manager_instance
    if _animation_manager_instance is None:
        _animation_manager_instance = AnimationManager()
    return _animation_manager_instance
