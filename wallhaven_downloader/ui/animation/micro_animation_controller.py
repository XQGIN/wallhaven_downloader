# -*- coding: utf-8 -*-
"""
微动画控制器
提供细腻的微动画效果，包括悬停、按下、淡入淡出、滑动等动画
"""

from typing import Optional, Callable
from PyQt5.QtCore import QObject, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal, pyqtProperty
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt

try:
    from utils.logger import get_logger
except ImportError:
    from ...utils.logger import get_logger

logger = get_logger(__name__)


class MicroAnimationController(QObject):
    """
    微动画控制器
    
    提供细腻的微动画效果，用于增强用户交互体验
    支持悬停、按下、淡入淡出、滑动等多种动画类型
    """
    
    # 动画类型配置
    ANIMATION_TYPES = {
        "hover": {
            "duration": 200,
            "easing": QEasingCurve.OutCubic
        },
        "press": {
            "duration": 150,
            "easing": QEasingCurve.InOutQuad
        },
        "transition": {
            "duration": 300,
            "easing": QEasingCurve.InOutCubic
        },
        "fade": {
            "duration": 250,
            "easing": QEasingCurve.OutCubic
        },
        "slide": {
            "duration": 300,
            "easing": QEasingCurve.OutCubic
        },
        "loading": {
            "duration": 1000,
            "easing": QEasingCurve.Linear
        }
    }
    
    def __init__(self):
        """初始化微动画控制器"""
        super().__init__()
        self.active_animations = []  # 活动动画列表
        logger.debug("MicroAnimationController 初始化完成")
    
    def create_hover_animation(
        self,
        widget: QWidget,
        property_name: str,
        start_value,
        end_value,
        duration: int = None,
        easing: QEasingCurve.Type = None,
        callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """
        创建悬停动画
        
        Args:
            widget: 目标组件
            property_name: 要动画的属性名称（如 "geometry", "pos", "size"）
            start_value: 起始值
            end_value: 结束值
            duration: 动画时长（毫秒），默认使用 hover 配置
            easing: 缓动函数，默认使用 hover 配置
            callback: 动画完成后的回调函数
            
        Returns:
            QPropertyAnimation 对象
        """
        config = self.ANIMATION_TYPES["hover"]
        
        # 创建动画
        animation = QPropertyAnimation(widget, property_name.encode())
        animation.setDuration(duration or config["duration"])
        animation.setEasingCurve(easing or config["easing"])
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        
        # 连接完成信号
        def on_finished():
            self._on_animation_finished(animation)
            if callback:
                callback()
        
        animation.finished.connect(on_finished)
        
        # 添加到活动列表并启动
        self.active_animations.append(animation)
        animation.start()
        
        logger.debug(f"创建悬停动画: {widget.__class__.__name__}, 属性={property_name}")
        return animation
    
    def create_press_animation(
        self,
        widget: QWidget,
        scale_factor: float = 0.95,
        duration: int = None,
        easing: QEasingCurve.Type = None,
        callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """
        创建按下动画（缩放效果）
        
        Args:
            widget: 目标组件
            scale_factor: 缩放因子（0.0-1.0），默认 0.95
            duration: 动画时长（毫秒），默认使用 press 配置
            easing: 缓动函数，默认使用 press 配置
            callback: 动画完成后的回调函数
            
        Returns:
            QPropertyAnimation 对象
        """
        config = self.ANIMATION_TYPES["press"]
        
        # 获取原始尺寸
        original_size = widget.size()
        original_pos = widget.pos()
        
        # 计算缩放后的尺寸和位置（保持中心点不变）
        scaled_width = int(original_size.width() * scale_factor)
        scaled_height = int(original_size.height() * scale_factor)
        offset_x = (original_size.width() - scaled_width) // 2
        offset_y = (original_size.height() - scaled_height) // 2
        
        # 创建几何动画（同时改变位置和大小）
        from PyQt5.QtCore import QRect
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration or config["duration"])
        animation.setEasingCurve(easing or config["easing"])
        animation.setStartValue(widget.geometry())
        animation.setEndValue(QRect(
            original_pos.x() + offset_x,
            original_pos.y() + offset_y,
            scaled_width,
            scaled_height
        ))
        
        # 连接完成信号
        def on_finished():
            self._on_animation_finished(animation)
            if callback:
                callback()
        
        animation.finished.connect(on_finished)
        
        # 添加到活动列表并启动
        self.active_animations.append(animation)
        animation.start()
        
        logger.debug(f"创建按下动画: {widget.__class__.__name__}, 缩放={scale_factor}")
        return animation
    
    def create_fade_animation(
        self,
        widget: QWidget,
        start_opacity: float,
        end_opacity: float,
        duration: int = None,
        easing: QEasingCurve.Type = None,
        callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """
        创建淡入淡出动画
        
        Args:
            widget: 目标组件
            start_opacity: 起始透明度（0.0-1.0）
            end_opacity: 结束透明度（0.0-1.0）
            duration: 动画时长（毫秒），默认使用 fade 配置
            easing: 缓动函数，默认使用 fade 配置
            callback: 动画完成后的回调函数
            
        Returns:
            QPropertyAnimation 对象
        """
        config = self.ANIMATION_TYPES["fade"]
        
        # 创建或获取透明度效果
        opacity_effect = widget.graphicsEffect()
        if not isinstance(opacity_effect, QGraphicsOpacityEffect):
            opacity_effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(opacity_effect)
        
        opacity_effect.setOpacity(start_opacity)
        
        # 创建动画
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration or config["duration"])
        animation.setEasingCurve(easing or config["easing"])
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        
        # 连接完成信号
        def on_finished():
            self._on_animation_finished(animation)
            if callback:
                callback()
        
        animation.finished.connect(on_finished)
        
        # 添加到活动列表并启动
        self.active_animations.append(animation)
        animation.start()
        
        logger.debug(f"创建淡入淡出动画: {widget.__class__.__name__}, {start_opacity} -> {end_opacity}")
        return animation
    
    def create_slide_animation(
        self,
        widget: QWidget,
        start_pos: QPoint,
        end_pos: QPoint,
        duration: int = None,
        easing: QEasingCurve.Type = None,
        callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """
        创建滑动动画
        
        Args:
            widget: 目标组件
            start_pos: 起始位置
            end_pos: 结束位置
            duration: 动画时长（毫秒），默认使用 slide 配置
            easing: 缓动函数，默认使用 slide 配置
            callback: 动画完成后的回调函数
            
        Returns:
            QPropertyAnimation 对象
        """
        config = self.ANIMATION_TYPES["slide"]
        
        # 设置起始位置
        widget.move(start_pos)
        
        # 创建动画
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration or config["duration"])
        animation.setEasingCurve(easing or config["easing"])
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        
        # 连接完成信号
        def on_finished():
            self._on_animation_finished(animation)
            if callback:
                callback()
        
        animation.finished.connect(on_finished)
        
        # 添加到活动列表并启动
        self.active_animations.append(animation)
        animation.start()
        
        logger.debug(f"创建滑动动画: {widget.__class__.__name__}, {start_pos} -> {end_pos}")
        return animation
    
    def create_ripple_effect(
        self,
        widget: QWidget,
        center: QPoint,
        max_radius: int,
        color: QColor = None,
        duration: int = None,
        callback: Optional[Callable] = None
    ) -> 'RippleAnimation':
        """
        创建涟漪效果
        
        Args:
            widget: 目标组件
            center: 涟漪中心点
            max_radius: 最大半径
            color: 涟漪颜色，默认使用半透明白色
            duration: 动画时长（毫秒），默认使用 transition 配置
            callback: 动画完成后的回调函数
            
        Returns:
            RippleAnimation 对象
        """
        config = self.ANIMATION_TYPES["transition"]
        
        # 创建涟漪动画
        ripple = RippleAnimation(
            widget,
            center,
            max_radius,
            color or QColor(255, 255, 255, 100),
            duration or config["duration"]
        )
        
        # 连接完成信号
        def on_finished():
            self._on_animation_finished(ripple.animation)
            if callback:
                callback()
            ripple.deleteLater()
        
        ripple.animation.finished.connect(on_finished)
        
        # 添加到活动列表并启动
        self.active_animations.append(ripple.animation)
        ripple.start()
        
        logger.debug(f"创建涟漪效果: {widget.__class__.__name__}, 中心={center}, 半径={max_radius}")
        return ripple
    
    def _on_animation_finished(self, animation: QPropertyAnimation):
        """动画完成处理"""
        if animation in self.active_animations:
            self.active_animations.remove(animation)
    
    def stop_all_animations(self):
        """停止所有动画"""
        for animation in self.active_animations:
            if animation and animation.state() == QPropertyAnimation.Running:
                animation.stop()
        self.active_animations.clear()
        logger.debug("所有微动画已停止")
    
    def get_active_animation_count(self) -> int:
        """获取当前活动动画数量"""
        # 清理已完成的动画
        self.active_animations = [
            anim for anim in self.active_animations 
            if anim and anim.state() == QPropertyAnimation.Running
        ]
        return len(self.active_animations)


class RippleAnimation(QWidget):
    """
    涟漪动画组件
    
    实现从点击位置向外扩散的涟漪效果
    """
    
    def __init__(
        self,
        parent: QWidget,
        center: QPoint,
        max_radius: int,
        color: QColor,
        duration: int
    ):
        """
        初始化涟漪动画
        
        Args:
            parent: 父组件
            center: 涟漪中心点
            max_radius: 最大半径
            color: 涟漪颜色
            duration: 动画时长
        """
        super().__init__(parent)
        self.center = center
        self.max_radius = max_radius
        self.ripple_color = color
        self._radius = 0
        
        # 设置组件属性
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(parent.rect())
        
        # 创建动画
        self.animation = QPropertyAnimation(self, b"radius")
        self.animation.setDuration(duration)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setStartValue(0)
        self.animation.setEndValue(max_radius)
        
        # 连接动画更新信号
        self.animation.valueChanged.connect(self.update)
        
        logger.debug(f"RippleAnimation 初始化: 中心={center}, 最大半径={max_radius}")
    
    def start(self):
        """启动涟漪动画"""
        self.show()
        self.animation.start()
        logger.debug("涟漪动画已启动")
    
    def paintEvent(self, event):
        """绘制涟漪"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算透明度（随半径增大而降低）
        if self.max_radius > 0:
            alpha_ratio = 1 - (self._radius / self.max_radius)
        else:
            alpha_ratio = 1
        
        alpha = int(self.ripple_color.alpha() * alpha_ratio)
        color = QColor(
            self.ripple_color.red(),
            self.ripple_color.green(),
            self.ripple_color.blue(),
            alpha
        )
        
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        # 绘制圆形涟漪
        painter.drawEllipse(self.center, int(self._radius), int(self._radius))
    
    def get_radius(self) -> int:
        """获取涟漪半径"""
        return self._radius
    
    def set_radius(self, radius: int):
        """设置涟漪半径"""
        self._radius = radius
    
    # 定义 Qt 属性以便 QPropertyAnimation 使用
    radius = pyqtProperty(int, get_radius, set_radius)


# 全局单例
_micro_animation_controller_instance: Optional[MicroAnimationController] = None


def get_micro_animation_controller() -> MicroAnimationController:
    """
    获取微动画控制器单例
    
    Returns:
        MicroAnimationController 实例
    """
    global _micro_animation_controller_instance
    if _micro_animation_controller_instance is None:
        _micro_animation_controller_instance = MicroAnimationController()
    return _micro_animation_controller_instance
