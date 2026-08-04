# -*- coding: utf-8 -*-
""" 
动画混入类
提供通用的悬浮和过渡动画功能
"""

from typing import Optional
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

try:
    from core.theme_manager import get_theme_manager
except ImportError:
    from ..core.theme_manager import get_theme_manager


class HoverAnimationMixin:
    """悬浮动画混入类
    
    提供通用的悬浮、焦点动画逻辑，支持主题切换
    使用方法：继承此类并调用初始化方法
    
    Example:
        class MyWidget(QWidget, HoverAnimationMixin):
            def __init__(self):
                super().__init__()
                self.init_hover_animation()  # 自动使用主题颜色
                # 连接主题变更信号
                get_theme_manager().theme_changed.connect(self._on_theme_changed)
    """
    
    def init_hover_animation(
        self,
        normal_bg: Optional[QColor] = None,
        hover_bg: Optional[QColor] = None,
        focus_bg: Optional[QColor] = None,
        animation_duration: int = 150,
        update_threshold: int = 100,
        use_theme_colors: bool = True
    ):
        """
        初始化悬浮动画
        
        Args:
            normal_bg: 正常状态背景色（如果为 None 且 use_theme_colors=True，则使用主题颜色）
            hover_bg: 悬浮状态背景色
            focus_bg: 焦点状态背景色（可选）
            animation_duration: 动画持续时间（毫秒）
            update_threshold: 更新阈值（毫秒），防止频繁触发
            use_theme_colors: 是否使用主题管理器的颜色
        """
        self._use_theme_colors = use_theme_colors
        
        if use_theme_colors and normal_bg is None:
            theme_manager = get_theme_manager()
            self._normal_background = QColor(theme_manager.get_color("glass_normal"))
            self._hover_background = QColor(theme_manager.get_color("glass_hover"))
            self._focus_background = QColor(theme_manager.get_color("glass_hover"))
        else:
            self._normal_background = QColor(normal_bg) if normal_bg else QColor(255, 255, 255, 180)
            if hover_bg:
                self._hover_background = QColor(hover_bg)
            else:
                self._hover_background = QColor(self._normal_background.red(), self._normal_background.green(), self._normal_background.blue(), min(255, self._normal_background.alpha() + 40))
            if focus_bg:
                self._focus_background = QColor(focus_bg)
            else:
                self._focus_background = QColor(self._normal_background.red(), self._normal_background.green(), self._normal_background.blue(), min(255, self._normal_background.alpha() + 60))
        
        self._current_background = QColor(self._normal_background)
        
        self._is_hovered = False
        self._is_focused = False
        self._hover_animation_progress = 0.0
        self._hover_animation_timer: Optional[int] = None
        self._hover_animation_duration = animation_duration
        self._hover_start_time = 0
        self._last_hover_time = 0
        self._update_threshold = update_threshold
    
    def _on_theme_changed(self, theme_name: str):
        """主题变更事件处理"""
        if self._use_theme_colors:
            theme_manager = get_theme_manager()
            self._normal_background = QColor(theme_manager.get_color("glass_normal"))
            self._hover_background = QColor(theme_manager.get_color("glass_hover"))
            self._focus_background = QColor(theme_manager.get_color("glass_hover"))
            self._current_background = QColor(self._normal_background)
            
            # 触发重绘
            if hasattr(self, 'update'):
                self.update()
            if hasattr(self, '_update_stylesheet'):
                self._update_stylesheet()
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        current_time = self._get_current_time()
        if not self._is_hovered and current_time - self._last_hover_time > self._update_threshold:
            self._is_hovered = True
            self._last_hover_time = current_time
            self._start_hover_animation()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        current_time = self._get_current_time()
        if self._is_hovered and current_time - self._last_hover_time > self._update_threshold:
            self._is_hovered = False
            self._last_hover_time = current_time
            self._start_hover_animation()
        super().leaveEvent(event)
    
    def focusInEvent(self, event):
        """焦点进入事件"""
        current_time = self._get_current_time()
        if not self._is_focused and current_time - self._last_hover_time > self._update_threshold:
            self._is_focused = True
            self._last_hover_time = current_time
            self._start_hover_animation()
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        """焦点离开事件"""
        current_time = self._get_current_time()
        if self._is_focused and current_time - self._last_hover_time > self._update_threshold:
            self._is_focused = False
            self._last_hover_time = current_time
            self._start_hover_animation()
        super().focusOutEvent(event)
    
    def _get_current_time(self) -> int:
        """获取当前时间"""
        return self._hover_animation_timer if self._hover_animation_timer else 0
    
    def _start_hover_animation(self):
        """开始悬浮动画"""
        self._hover_animation_progress = 0.0
        self._hover_start_time = 0
        
        # 停止已有定时器
        if self._hover_animation_timer:
            self.killTimer(self._hover_animation_timer)
        
        # 启动新定时器（约60fps）
        self._hover_animation_timer = self.startTimer(16)
    
    def _update_hover_animation(self):
        """更新悬浮动画进度"""
        if self._hover_start_time == 0:
            self._hover_start_time = self._hover_animation_timer
        
        elapsed = self._hover_animation_timer - self._hover_start_time
        self._hover_animation_progress = min(1.0, elapsed / self._hover_animation_duration)
        
        # 使用缓动函数
        eased_progress = self._ease_in_out_cubic(self._hover_animation_progress)
        
        # 确定目标颜色
        if self._is_focused:
            target_color = self._focus_background
        elif self._is_hovered:
            target_color = self._hover_background
        else:
            target_color = self._normal_background
        
        # 保存之前的颜色
        prev_color = self._current_background
        
        # 颜色插值
        self._current_background = self._interpolate_color(
            self._current_background,
            target_color,
            eased_progress
        )
        
        # 检查颜色变化是否显著
        color_changed = self._is_color_changed(prev_color, self._current_background, threshold=5)
        
        if color_changed or self._hover_animation_progress >= 1.0:
            self._update_stylesheet()
        
        # 动画完成
        if self._hover_animation_progress >= 1.0:
            self._current_background = QColor(target_color)
            self.killTimer(self._hover_animation_timer)
            self._hover_animation_timer = None
    
    @staticmethod
    def _ease_in_out_cubic(t: float) -> float:
        """三次贝塞尔缓动函数"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def _interpolate_color(start: QColor, end: QColor, progress: float) -> QColor:
        """颜色插值"""
        r = int(start.red() + (end.red() - start.red()) * progress)
        g = int(start.green() + (end.green() - start.green()) * progress)
        b = int(start.blue() + (end.blue() - start.blue()) * progress)
        a = int(start.alpha() + (end.alpha() - start.alpha()) * progress)
        return QColor(r, g, b, a)
    
    @staticmethod
    def _is_color_changed(color1: QColor, color2: QColor, threshold: int = 5) -> bool:
        """检查颜色变化是否显著"""
        return (
            abs(color1.red() - color2.red()) > threshold or
            abs(color1.green() - color2.green()) > threshold or
            abs(color1.blue() - color2.blue()) > threshold or
            abs(color1.alpha() - color2.alpha()) > threshold
        )
    
    def timerEvent(self, event):
        """定时器事件"""
        if event.timerId() == self._hover_animation_timer:
            self._update_hover_animation()
        super().timerEvent(event)
    
    def _update_stylesheet(self):
        """
        更新样式表 - 子类需要实现此方法
        
        使用 self._current_background 来更新组件样式
        """
        raise NotImplementedError("子类必须实现 _update_stylesheet 方法")
    
    def set_transparency(self, transparency: int):
        """
        设置透明度
        
        Args:
            transparency: 透明度值 (0-255)
        """
        self._normal_background.setAlpha(transparency)
        self._hover_background.setAlpha(min(255, transparency + 40))
        self._focus_background.setAlpha(min(255, transparency + 60))
        self._update_stylesheet()
