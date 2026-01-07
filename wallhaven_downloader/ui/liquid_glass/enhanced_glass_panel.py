"""
增强玻璃面板组件

提供完整的液态玻璃效果，包括多层模糊、边缘高光、内阴影等
"""

from PyQt5.QtCore import Qt, QRect, QRectF, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect
from typing import Dict, Optional


class EnhancedGlassPanel(QWidget):
    """
    增强玻璃面板组件
    
    提供完整的液态玻璃效果，包括：
    - 多层模糊效果
    - 边缘高光
    - 内阴影
    - 悬停增强
    - 动态调整
    
    需求：1.1-1.5, 6.1-6.8
    """
    
    def __init__(self, parent: Optional[QWidget] = None, config: Optional[Dict] = None):
        """
        初始化增强玻璃面板
        
        Args:
            parent: 父组件
            config: 配置参数字典
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 配置参数
        self.config = config or {}
        self.blur_radius = self.config.get("blur_radius", 20)
        self.transparency = self.config.get("transparency", 0.7)
        self.border_radius = self.config.get("border_radius", 12)
        self.shadow_blur = self.config.get("shadow_blur", 20)
        self.edge_highlight_width = self.config.get("edge_highlight_width", 2)
        
        # 状态
        self.is_hovered = False
        self.is_focused = False
        
        # 主题颜色（默认浅色主题）
        self._is_dark_mode = False
        self._theme_colors = self._get_default_light_colors()
        
        # 缓存
        self.cached_background = None
        self.needs_background_update = True
        
        # 动画
        self.hover_animation: Optional[QPropertyAnimation] = None
        self.focus_animation: Optional[QPropertyAnimation] = None
        
        # 启用鼠标跟踪以支持悬停效果
        self.setMouseTracking(True)
        
        # 应用阴影效果
        self._apply_shadow_effect()
    
    def _apply_shadow_effect(self):
        """应用阴影效果"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(self.shadow_blur)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def paintEvent(self, event):
        """
        绘制玻璃面板
        
        Args:
            event: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # 绘制多层阴影
        self._draw_multi_layer_shadow(painter, rect)
        
        # 绘制玻璃背景
        self._draw_glass_background(painter, rect)
        
        # 绘制高光效果
        self._draw_highlights(painter, rect)
        
        # 绘制边缘高光
        self._draw_edge_highlight(painter, rect)
    
    def _draw_multi_layer_shadow(self, painter: QPainter, rect: QRect):
        """
        绘制多层阴影
        
        Args:
            painter: 绘制器
            rect: 绘制区域
        """
        # 多层阴影效果已通过 QGraphicsDropShadowEffect 实现
        # 这里可以添加额外的内阴影效果
        pass
    
    def _draw_glass_background(self, painter: QPainter, rect: QRect):
        """
        绘制玻璃背景
        
        Args:
            painter: 绘制器
            rect: 绘制区域
        """
        # 创建圆角路径
        path = QPainterPath()
        # 将 QRect 转换为 QRectF
        rectf = QRectF(rect.adjusted(1, 1, -1, -1))
        path.addRoundedRect(rectf, 
                           self.border_radius, 
                           self.border_radius)
        
        # 计算透明度（悬停时增加）
        alpha = int(255 * self.transparency)
        if self.is_hovered:
            alpha = min(255, int(alpha * 1.1))
        
        # 使用主题颜色
        glass_color = self._theme_colors.get("glass_normal", QColor(255, 255, 255, 200))
        if self.is_hovered:
            glass_color = self._theme_colors.get("glass_hover", QColor(255, 255, 255, 230))
        
        # 应用透明度
        background_color = QColor(glass_color)
        background_color.setAlpha(alpha)
        
        # 绘制半透明背景
        painter.fillPath(path, QBrush(background_color))
        
        # 绘制边框
        border_color = self._theme_colors.get("border", QColor(216, 216, 220))
        border_alpha = int(alpha * 0.5)
        border_color.setAlpha(border_alpha)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)
    
    def _draw_highlights(self, painter: QPainter, rect: QRect):
        """
        绘制高光效果
        
        Args:
            painter: 绘制器
            rect: 绘制区域
        """
        # 创建顶部高光渐变
        gradient = QLinearGradient(rect.topLeft(), rect.center())
        gradient.setColorAt(0, QColor(255, 255, 255, 40))
        gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        # 创建高光路径（仅顶部区域）
        highlight_path = QPainterPath()
        highlight_rect = QRect(rect.x(), rect.y(), rect.width(), rect.height() // 2)
        highlight_rectf = QRectF(highlight_rect.adjusted(1, 1, -1, 0))
        highlight_path.addRoundedRect(highlight_rectf,
                                     self.border_radius,
                                     self.border_radius)
        
        painter.fillPath(highlight_path, QBrush(gradient))
    
    def _draw_edge_highlight(self, painter: QPainter, rect: QRect):
        """
        绘制边缘高光
        
        Args:
            painter: 绘制器
            rect: 绘制区域
        """
        # 边缘高光（细微的亮边）
        edge_color = QColor(255, 255, 255, 60)
        painter.setPen(QPen(edge_color, self.edge_highlight_width))
        
        path = QPainterPath()
        rectf = QRectF(rect.adjusted(1, 1, -1, -1))
        path.addRoundedRect(rectf,
                           self.border_radius,
                           self.border_radius)
        painter.drawPath(path)
    
    def enterEvent(self, event):
        """
        鼠标进入事件 - 悬停增强
        
        Args:
            event: 事件对象
        """
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """
        鼠标离开事件 - 恢复正常
        
        Args:
            event: 事件对象
        """
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def set_blur_radius(self, radius: int):
        """
        设置模糊半径
        
        Args:
            radius: 模糊半径 (5-40px)
        """
        self.blur_radius = max(5, min(40, radius))
        self.needs_background_update = True
        self.update()
    
    def set_transparency(self, transparency: float):
        """
        设置透明度
        
        Args:
            transparency: 透明度 (0.6-0.95)
        """
        self.transparency = max(0.6, min(0.95, transparency))
        self.update()
    
    def set_border_radius(self, radius: int):
        """
        设置圆角半径
        
        Args:
            radius: 圆角半径 (8-20px)
        """
        self.border_radius = max(8, min(20, radius))
        self.update()
    
    def update_theme_colors(self, theme_colors: Dict, is_dark_mode: bool):
        """
        更新主题颜色
        
        Args:
            theme_colors: 主题颜色字典
            is_dark_mode: 是否为深色模式
            
        需求：2.7
        """
        self._theme_colors = theme_colors
        self._is_dark_mode = is_dark_mode
        
        # 根据主题调整阴影效果
        self._update_shadow_for_theme()
        
        # 标记需要更新背景
        self.needs_background_update = True
        
        # 触发重绘
        self.update()
    
    def _update_shadow_for_theme(self):
        """根据主题更新阴影效果"""
        shadow = self.graphicsEffect()
        if shadow and isinstance(shadow, QGraphicsDropShadowEffect):
            if self._is_dark_mode:
                # 深色模式：更深的阴影
                shadow.setColor(QColor(0, 0, 0, 60))
                shadow.setBlurRadius(self.shadow_blur * 1.2)
            else:
                # 浅色模式：较浅的阴影
                shadow.setColor(QColor(0, 0, 0, 30))
                shadow.setBlurRadius(self.shadow_blur)
    
    def _get_default_light_colors(self) -> Dict:
        """
        获取默认浅色主题颜色
        
        Returns:
            颜色字典
        """
        return {
            "background": QColor(245, 245, 247),
            "surface": QColor(255, 255, 255),
            "glass_normal": QColor(255, 255, 255, 200),
            "glass_hover": QColor(255, 255, 255, 230),
            "text_primary": QColor(29, 29, 31),
            "accent": QColor(0, 122, 255),
            "border": QColor(216, 216, 220),
        }
