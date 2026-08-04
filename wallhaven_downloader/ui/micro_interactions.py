# -*- coding: utf-8 -*-
"""
微交互增强模块
提供细腻的交互反馈，提升用户体验
"""

from typing import Optional
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QLinearGradient

try:
    from core.theme_manager import get_theme_manager
    from ui.animation_manager import get_animation_manager
    from utils.logger import get_logger
except ImportError:
    from ..core.theme_manager import get_theme_manager
    from .animation_manager import get_animation_manager
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class RippleEffect(QWidget):
    """
    波纹点击效果
    Material Design风格的点击反馈
    """
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.theme_manager = get_theme_manager()
        self.animation_manager = get_animation_manager()
        
        # 波纹参数
        self._ripple_radius = 0
        self._ripple_opacity = 0.3
        self._ripple_center = None
        self._max_radius = 0
        
        # 动画
        self._radius_animation = None
        self._opacity_animation = None
        
    def start_ripple(self, center_point):
        """开始波纹动画"""
        self._ripple_center = center_point
        self._max_radius = max(self.width(), self.height()) * 0.8
        
        # 半径动画
        self._radius_animation = QPropertyAnimation(self, b"ripple_radius")
        self._radius_animation.setDuration(400)
        self._radius_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._radius_animation.setStartValue(0)
        self._radius_animation.setEndValue(self._max_radius)
        
        # 透明度动画
        self._opacity_animation = QPropertyAnimation(self, b"ripple_opacity")
        self._opacity_animation.setDuration(400)
        self._opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._opacity_animation.setStartValue(0.3)
        self._opacity_animation.setEndValue(0)
        
        # 启动动画
        self._radius_animation.start()
        self._opacity_animation.start()
        
        # 动画完成后隐藏
        self._opacity_animation.finished.connect(self.hide)
        
        self.show()
        self.raise_()
    
    @pyqtProperty(float)
    def ripple_radius(self):
        return self._ripple_radius
    
    @ripple_radius.setter
    def ripple_radius(self, value):
        self._ripple_radius = value
        self.update()
    
    @pyqtProperty(float)
    def ripple_opacity(self):
        return self._ripple_opacity
    
    @ripple_opacity.setter
    def ripple_opacity(self, value):
        self._ripple_opacity = value
        self.update()
    
    def paintEvent(self, event):
        if not self._ripple_center:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取主题色
        primary_color = self.theme_manager.get_color("primary")
        ripple_color = QColor(primary_color)
        ripple_color.setAlphaF(self._ripple_opacity)
        
        painter.setBrush(ripple_color)
        painter.setPen(Qt.NoPen)
        
        # 绘制圆形波纹
        painter.drawEllipse(
            self._ripple_center.x() - self._ripple_radius,
            self._ripple_center.y() - self._ripple_radius,
            self._ripple_radius * 2,
            self._ripple_radius * 2
        )


class EnhancedButton(QPushButton):
    """
    增强按钮组件
    包含波纹效果、悬停动画、按压反馈
    """
    
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        
        self.theme_manager = get_theme_manager()
        self.animation_manager = get_animation_manager()
        
        # 波纹效果
        self.ripple_effect = RippleEffect(self)
        
        # 悬停状态
        self._is_hovered = False
        self._is_pressed = False
        
        # 设置样式
        self._apply_style()
        
        # 连接主题变更
        self.theme_manager.theme_changed.connect(self._apply_style)
    
    def _apply_style(self):
        """应用按钮样式"""
        colors = self.theme_manager.get_enhanced_colors()
        
        style = f"""
        EnhancedButton {{
            background: {colors['primary'].name()};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            min-height: 20px;
        }}
        
        EnhancedButton:hover {{
            background: {colors['primary_hover'].name()};
            transform: translateY(-1px);
        }}
        
        EnhancedButton:pressed {{
            background: {colors['primary_active'].name()};
            transform: translateY(0px);
        }}
        
        EnhancedButton:disabled {{
            background: {colors['primary_disabled'].name()};
            color: rgba(255, 255, 255, 0.6);
        }}
        """
        
        self.setStyleSheet(style)
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 触发波纹效果"""
        super().mousePressEvent(event)
        
        if event.button() == Qt.LeftButton:
            self.ripple_effect.resize(self.size())
            self.ripple_effect.start_ripple(event.pos())
    
    def resizeEvent(self, event):
        """调整大小事件"""
        super().resizeEvent(event)
        self.ripple_effect.resize(self.size())


class LoadingSpinner(QWidget):
    """
    加载动画组件
    现代化的旋转加载指示器
    """
    
    def __init__(self, size: int = 32, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setFixedSize(size, size)
        self.theme_manager = get_theme_manager()
        
        # 动画参数
        self._rotation = 0
        self._animation = None
        
        # 设置动画
        self._setup_animation()
    
    def _setup_animation(self):
        """设置旋转动画"""
        self._animation = QPropertyAnimation(self, b"rotation")
        self._animation.setDuration(1000)
        self._animation.setLoopCount(-1)  # 无限循环
        self._animation.setStartValue(0)
        self._animation.setEndValue(360)
        self._animation.setEasingCurve(QEasingCurve.Linear)
    
    @pyqtProperty(int)
    def rotation(self):
        return self._rotation
    
    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        self.update()
    
    def start(self):
        """开始动画"""
        self._animation.start()
        self.show()
    
    def stop(self):
        """停止动画"""
        self._animation.stop()
        self.hide()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取主题色
        primary_color = self.theme_manager.get_color("primary")
        
        # 设置画笔
        painter.setPen(Qt.NoPen)
        
        # 绘制旋转的圆弧
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 4
        
        # 创建渐变
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 255))
        gradient.setColorAt(1, QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 50))
        
        painter.setBrush(gradient)
        
        # 旋转画布
        painter.translate(center)
        painter.rotate(self._rotation)
        
        # 绘制圆弧
        path = QPainterPath()
        path.arcMoveTo(-radius, -radius, radius * 2, radius * 2, 0)
        path.arcTo(-radius, -radius, radius * 2, radius * 2, 0, 270)
        
        painter.strokePath(path, painter.pen())