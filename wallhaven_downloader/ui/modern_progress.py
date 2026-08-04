# -*- coding: utf-8 -*-
"""
现代化进度指示器
提供多种样式的进度条和加载动画
"""

import math
from typing import Optional
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QConicalGradient, QFont

try:
    from core.theme_manager import get_theme_manager
    from ui.typography_system import TypographySystem
    from utils.logger import get_logger
except ImportError:
    from ..core.theme_manager import get_theme_manager
    from .typography_system import TypographySystem
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class ModernProgressBar(QWidget):
    """
    现代化线性进度条
    支持渐变色、动画效果和自定义样式
    """
    
    # 信号
    valueChanged = pyqtSignal(int)  # 值改变信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        
        # 进度参数
        self._value = 0
        self._minimum = 0
        self._maximum = 100
        
        # 样式参数
        self.bar_height = 8
        self.border_radius = 4
        self.show_text = True
        self.text_position = "center"  # "center", "right", "none"
        
        # 动画参数
        self._animated_value = 0
        self.animation_duration = 300
        self.use_animation = True
        
        # 渐变效果
        self.use_gradient = True
        self.gradient_colors = None  # 将使用主题色
        
        # 动画对象
        self._value_animation = None
        
        # 设置最小高度
        self.setMinimumHeight(self.bar_height + 20)  # 为文本留空间
        
        # 连接主题变更
        self.theme_manager.theme_changed.connect(self.update)
        
        logger.debug("ModernProgressBar 初始化完成")
    
    @pyqtProperty(int)
    def value(self):
        """获取当前值"""
        return self._value
    
    @value.setter
    def value(self, val: int):
        """设置当前值"""
        val = max(self._minimum, min(self._maximum, val))
        if val != self._value:
            self._value = val
            self.valueChanged.emit(val)
            
            if self.use_animation:
                self._animate_to_value(val)
            else:
                self._animated_value = val
                self.update()
    
    @pyqtProperty(float)
    def animated_value(self):
        """获取动画值（用于动画）"""
        return self._animated_value
    
    @animated_value.setter
    def animated_value(self, val: float):
        """设置动画值"""
        self._animated_value = val
        self.update()
    
    def _animate_to_value(self, target_value: int):
        """动画到目标值"""
        if self._value_animation:
            self._value_animation.stop()
        
        self._value_animation = QPropertyAnimation(self, b"animated_value")
        self._value_animation.setDuration(self.animation_duration)
        self._value_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._value_animation.setStartValue(self._animated_value)
        self._value_animation.setEndValue(target_value)
        self._value_animation.start()
    
    def setRange(self, minimum: int, maximum: int):
        """设置范围"""
        self._minimum = minimum
        self._maximum = maximum
        self.update()
    
    def paintEvent(self, event):
        """绘制进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算进度条区域
        bar_rect = self.rect()
        if self.show_text:
            bar_rect.setHeight(self.bar_height)
            bar_rect.moveTop((self.height() - self.bar_height) // 2)
        
        # 绘制背景
        self._draw_background(painter, bar_rect)
        
        # 绘制进度
        if self._animated_value > self._minimum:
            self._draw_progress(painter, bar_rect)
        
        # 绘制文本
        if self.show_text:
            self._draw_text(painter)
    
    def _draw_background(self, painter: QPainter, rect):
        """绘制背景"""
        bg_color = self.theme_manager.get_color("border")
        bg_color.setAlpha(100)
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.border_radius, self.border_radius)
    
    def _draw_progress(self, painter: QPainter, rect):
        """绘制进度"""
        # 计算进度宽度
        progress_ratio = (self._animated_value - self._minimum) / (self._maximum - self._minimum)
        progress_width = rect.width() * progress_ratio
        
        progress_rect = rect
        progress_rect.setWidth(int(progress_width))
        
        if self.use_gradient:
            # 创建渐变
            gradient = QLinearGradient(progress_rect.topLeft(), progress_rect.topRight())
            
            if self.gradient_colors:
                for i, color in enumerate(self.gradient_colors):
                    gradient.setColorAt(i / (len(self.gradient_colors) - 1), color)
            else:
                # 使用主题色渐变
                primary = self.theme_manager.get_color("primary")
                success = self.theme_manager.get_color("success")
                
                if progress_ratio < 0.5:
                    # 前半段：主色到成功色
                    gradient.setColorAt(0, primary)
                    gradient.setColorAt(1, success)
                else:
                    # 后半段：成功色
                    gradient.setColorAt(0, success)
                    gradient.setColorAt(1, success)
            
            painter.setBrush(QBrush(gradient))
        else:
            # 纯色
            color = self.theme_manager.get_color("primary")
            painter.setBrush(QBrush(color))
        
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(progress_rect, self.border_radius, self.border_radius)
    
    def _draw_text(self, painter: QPainter):
        """绘制文本"""
        if self.text_position == "none":
            return
        
        # 计算百分比
        percentage = int((self._animated_value - self._minimum) / (self._maximum - self._minimum) * 100)
        text = f"{percentage}%"
        
        # 设置字体
        font = painter.font()
        font.setPointSize(10)
        font.setWeight(QFont.Medium)
        painter.setFont(font)
        
        # 设置颜色
        text_color = self.theme_manager.get_color("text_primary")
        painter.setPen(text_color)
        
        # 绘制文本
        if self.text_position == "center":
            painter.drawText(self.rect(), Qt.AlignCenter, text)
        elif self.text_position == "right":
            painter.drawText(self.rect(), Qt.AlignRight | Qt.AlignVCenter, text)


class CircularProgressBar(QWidget):
    """
    圆形进度条
    现代化的环形进度指示器
    """
    
    def __init__(self, size: int = 120, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        
        # 设置大小
        self.setFixedSize(size, size)
        
        # 进度参数
        self._value = 0
        self._minimum = 0
        self._maximum = 100
        
        # 样式参数
        self.line_width = 8
        self.start_angle = 90  # 从顶部开始
        self.show_text = True
        self.show_percentage = True
        
        # 动画参数
        self._animated_value = 0
        self.animation_duration = 500
        
        # 渐变效果
        self.use_gradient = True
        
        # 动画对象
        self._value_animation = None
        
        # 连接主题变更
        self.theme_manager.theme_changed.connect(self.update)
        
        logger.debug(f"CircularProgressBar 初始化完成: 大小={size}")
    
    @pyqtProperty(int)
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val: int):
        val = max(self._minimum, min(self._maximum, val))
        if val != self._value:
            self._value = val
            self._animate_to_value(val)
    
    @pyqtProperty(float)
    def animated_value(self):
        return self._animated_value
    
    @animated_value.setter
    def animated_value(self, val: float):
        self._animated_value = val
        self.update()
    
    def _animate_to_value(self, target_value: int):
        """动画到目标值"""
        if self._value_animation:
            self._value_animation.stop()
        
        self._value_animation = QPropertyAnimation(self, b"animated_value")
        self._value_animation.setDuration(self.animation_duration)
        self._value_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._value_animation.setStartValue(self._animated_value)
        self._value_animation.setEndValue(target_value)
        self._value_animation.start()
    
    def paintEvent(self, event):
        """绘制圆形进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算绘制区域
        rect = self.rect()
        margin = self.line_width // 2
        draw_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # 绘制背景圆环
        self._draw_background_ring(painter, draw_rect)
        
        # 绘制进度圆环
        if self._animated_value > self._minimum:
            self._draw_progress_ring(painter, draw_rect)
        
        # 绘制中心文本
        if self.show_text:
            self._draw_center_text(painter, rect)
    
    def _draw_background_ring(self, painter: QPainter, rect):
        """绘制背景圆环"""
        bg_color = self.theme_manager.get_color("border")
        bg_color.setAlpha(100)
        
        pen = QPen(bg_color)
        pen.setWidth(self.line_width)
        pen.setCapStyle(Qt.RoundCap)
        
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)
    
    def _draw_progress_ring(self, painter: QPainter, rect):
        """绘制进度圆环"""
        # 计算进度角度
        progress_ratio = (self._animated_value - self._minimum) / (self._maximum - self._minimum)
        span_angle = int(360 * progress_ratio)
        
        if self.use_gradient:
            # 创建圆锥渐变
            gradient = QConicalGradient(rect.center(), self.start_angle)
            
            primary = self.theme_manager.get_color("primary")
            success = self.theme_manager.get_color("success")
            
            gradient.setColorAt(0, primary)
            gradient.setColorAt(0.5, success)
            gradient.setColorAt(1, primary)
            
            pen = QPen(QBrush(gradient), self.line_width)
        else:
            color = self.theme_manager.get_color("primary")
            pen = QPen(color, self.line_width)
        
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # 绘制进度弧
        painter.drawArc(rect, self.start_angle * 16, -span_angle * 16)
    
    def _draw_center_text(self, painter: QPainter, rect):
        """绘制中心文本"""
        # 计算百分比
        percentage = int((self._animated_value - self._minimum) / (self._maximum - self._minimum) * 100)
        
        # 设置字体
        font = painter.font()
        font.setPointSize(max(12, self.width() // 8))
        font.setWeight(QFont.Bold)
        painter.setFont(font)
        
        # 设置颜色
        text_color = self.theme_manager.get_color("text_primary")
        painter.setPen(text_color)
        
        # 绘制文本
        if self.show_percentage:
            text = f"{percentage}%"
        else:
            text = str(int(self._animated_value))
        
        painter.drawText(rect, Qt.AlignCenter, text)