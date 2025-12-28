# -*- coding: utf-8 -*-
"""
主题切换动画效果
提供平滑的主题过渡动画
"""

from typing import Optional
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class ThemeTransition(QObject):
    """主题切换动画管理器"""
    
    # 动画完成信号
    animation_finished = pyqtSignal()
    
    def __init__(self, widget: QWidget, duration: int = 300):
        """
        初始化主题切换动画
        
        Args:
            widget: 需要应用动画的窗口部件
            duration: 动画持续时间（毫秒）
        """
        super().__init__(widget)
        self.widget = widget
        self.duration = duration
        self.opacity_effect: Optional[QGraphicsOpacityEffect] = None
        self.fade_animation: Optional[QPropertyAnimation] = None
        
    def apply_fade_transition(self, callback=None):
        """
        应用淡入淡出过渡效果
        
        Args:
            callback: 动画完成后的回调函数
        """
        # 创建透明度效果
        if self.opacity_effect is None:
            self.opacity_effect = QGraphicsOpacityEffect(self.widget)
            self.widget.setGraphicsEffect(self.opacity_effect)
        
        # 创建动画
        if self.fade_animation is None:
            self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_animation.setDuration(self.duration)
            self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 先淡出
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        
        def on_fade_out_finished():
            # 执行回调（通常是更新主题样式）
            if callback:
                callback()
            
            # 再淡入
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.finished.disconnect()
            self.fade_animation.finished.connect(self._on_animation_complete)
            self.fade_animation.start()
        
        self.fade_animation.finished.connect(on_fade_out_finished)
        self.fade_animation.start()
    
    def apply_quick_fade(self, callback=None):
        """
        应用快速淡入效果（适用于组件更新）
        
        Args:
            callback: 动画完成后的回调函数
        """
        # 创建透明度效果
        if self.opacity_effect is None:
            self.opacity_effect = QGraphicsOpacityEffect(self.widget)
            self.widget.setGraphicsEffect(self.opacity_effect)
        
        # 创建动画
        if self.fade_animation is None:
            self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_animation.setDuration(self.duration // 2)
            self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 执行回调
        if callback:
            callback()
        
        # 淡入
        self.fade_animation.setStartValue(0.7)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.finished.disconnect()
        self.fade_animation.finished.connect(self._on_animation_complete)
        self.fade_animation.start()
    
    def _on_animation_complete(self):
        """动画完成处理"""
        # 移除图形效果以提升性能
        if self.opacity_effect:
            self.widget.setGraphicsEffect(None)
            self.opacity_effect = None
        
        self.animation_finished.emit()
        logger.debug("主题切换动画完成")
    
    def stop(self):
        """停止动画"""
        if self.fade_animation and self.fade_animation.state() == QPropertyAnimation.Running:
            self.fade_animation.stop()
        
        # 清理效果
        if self.opacity_effect:
            self.widget.setGraphicsEffect(None)
            self.opacity_effect = None


class ThemeAwareWidget:
    """
    主题感知窗口部件混入类
    
    为组件提供主题切换支持和动画效果
    """
    
    def __init__(self, *args, **kwargs):
        """初始化主题感知组件"""
        super().__init__(*args, **kwargs)
        self._theme_transition: Optional[ThemeTransition] = None
        self._theme_animation_enabled = True
    
    def enable_theme_transition(self, duration: int = 300):
        """
        启用主题切换动画
        
        Args:
            duration: 动画持续时间（毫秒）
        """
        if isinstance(self, QWidget):
            self._theme_transition = ThemeTransition(self, duration)
            self._theme_animation_enabled = True
    
    def disable_theme_transition(self):
        """禁用主题切换动画"""
        self._theme_animation_enabled = False
        if self._theme_transition:
            self._theme_transition.stop()
    
    def apply_theme_with_animation(self, apply_func):
        """
        带动画地应用主题
        
        Args:
            apply_func: 应用主题的函数
        """
        if self._theme_animation_enabled and self._theme_transition:
            self._theme_transition.apply_fade_transition(apply_func)
        else:
            apply_func()
    
    def update_theme_quickly(self, apply_func):
        """
        快速更新主题（适用于小组件）
        
        Args:
            apply_func: 应用主题的函数
        """
        if self._theme_animation_enabled and self._theme_transition:
            self._theme_transition.apply_quick_fade(apply_func)
        else:
            apply_func()
