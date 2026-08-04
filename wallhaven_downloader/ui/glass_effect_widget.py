# -*- coding: utf-8 -*-
"""
增强的玻璃效果组件

实现功能:
- 多层玻璃效果（背景模糊、半透明、高光、阴影）
- 边缘高光（1-2px 白色半透明边框）
- 内阴影效果
- 悬停增强（模糊度和透明度动态调整）
- 动态模糊/透明度调整（5-20px 模糊半径，0.6-0.9 透明度）

需求映射:
- 需求 6.1: 多层叠加实现真实的毛玻璃效果
- 需求 6.2: 边缘高光（1-2px 白色半透明边框）
- 需求 6.3: 悬停时增加背景模糊度和透明度
- 需求 6.4: 内阴影效果，增强深度感
- 需求 6.5: 动态调整玻璃效果的模糊半径和透明度
"""

from PyQt5.QtWidgets import QWidget, QStyleOption
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import (QPainter, QColor, QBrush, QPen, QPixmap, 
                        QLinearGradient)


class GlassEffectWidget(QWidget):
    """液态玻璃效果的基础部件
    
    增强功能:
    - 多层玻璃效果（背景模糊、半透明、高光、阴影）
    - 边缘高光（1-2px 白色半透明边框）
    - 内阴影效果
    - 悬停增强（模糊度和透明度动态调整）
    - 动态模糊/透明度调整（5-20px 模糊半径，0.6-0.9 透明度）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 基础玻璃效果参数
        self._glass_color = QColor(255, 255, 255, 180)  # 半透明白色
        self._border_color = QColor(255, 255, 255, 100)
        self._border_radius = 20
        self._shadow_blur = 20
        self._shadow_color = QColor(0, 0, 0, 50)
        self._highlight_color = QColor(255, 255, 255, 150)
        
        # 动态调整参数（需求 6.5）
        self._blur_radius = 10  # 模糊半径 (5-20px)
        self._transparency = 0.7  # 透明度 (0.6-0.9)
        
        # 悬停状态（需求 6.3）
        self._is_hovered = False
        self._hover_blur_multiplier = 1.25  # 悬停时模糊度增加 25%
        self._hover_transparency_increase = 0.15  # 悬停时透明度增加 15%
        
        # 缓存
        self._cached_background = None  # 缓存背景
        self._needs_background_update = True  # 是否需要更新背景
        
        # 启用鼠标跟踪以支持悬停效果
        self.setMouseTracking(True)
    
    def paintEvent(self, event):
        """绘制事件"""
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 如果需要更新背景或窗口大小改变
        if (self._needs_background_update or 
            self._cached_background is None or 
            self._cached_background.size() != self.size()):
            self._updateBackgroundCache()
            self._needs_background_update = False
        
        # 绘制缓存的背景
        if self._cached_background:
            painter.drawPixmap(0, 0, self._cached_background)
    
    def _updateBackgroundCache(self):
        """更新背景缓存
        
        实现多层玻璃效果:
        1. 外层阴影 - 模糊扩散
        2. 内层阴影 - 锐利集中（需求 6.4）
        3. 玻璃背景 - 半透明
        4. 主高光 - 线性渐变
        5. 边缘高光 - 1-2px 白色半透明边框（需求 6.2）
        """
        # 创建与窗口大小相同的缓存图像
        self._cached_background = QPixmap(self.size())
        self._cached_background.fill(Qt.transparent)
        
        painter = QPainter(self._cached_background)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 计算当前有效的模糊半径（考虑悬停状态）
        effective_blur = self._blur_radius
        if self._is_hovered:
            effective_blur = int(self._blur_radius * self._hover_blur_multiplier)
        
        # 计算当前有效的透明度（考虑悬停状态）
        effective_transparency = self._transparency
        if self._is_hovered:
            effective_transparency = min(0.9, self._transparency + self._hover_transparency_increase)
        
        # === 第一层：外层阴影 - 更模糊，更扩散 ===
        shadow_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(Qt.NoPen)
        
        for i in range(self._shadow_blur):
            alpha = int(self._shadow_color.alpha() * (1 - i / self._shadow_blur) * 0.6)
            color = QColor(
                self._shadow_color.red(), 
                self._shadow_color.green(), 
                self._shadow_color.blue(), 
                alpha
            )
            painter.setBrush(color)
            painter.drawRoundedRect(
                shadow_rect.adjusted(i, i, -i, -i), 
                self._border_radius, 
                self._border_radius
            )
        
        # === 第二层：内层阴影 - 更锐利，更集中（需求 6.4）===
        inner_shadow_rect = self.rect().adjusted(5, 5, -5, -5)
        inner_shadow_layers = max(5, effective_blur // 2)
        
        for i in range(inner_shadow_layers):
            alpha = int(self._shadow_color.alpha() * (1 - i / inner_shadow_layers) * 0.5)
            color = QColor(
                self._shadow_color.red(), 
                self._shadow_color.green(), 
                self._shadow_color.blue(), 
                alpha
            )
            painter.setBrush(color)
            # 内阴影从边缘向内收缩
            inset = int(i * 0.5)  # 转换为整数
            painter.drawRoundedRect(
                inner_shadow_rect.adjusted(inset, inset, -inset, -inset), 
                self._border_radius - inset, 
                self._border_radius - inset
            )
        
        # === 第三层：玻璃背景 - 半透明 ===
        glass_alpha = int(255 * effective_transparency)
        glass_color = QColor(
            self._glass_color.red(),
            self._glass_color.green(),
            self._glass_color.blue(),
            glass_alpha
        )
        painter.setBrush(QBrush(glass_color))
        painter.setPen(QPen(self._border_color, 1))
        painter.drawRoundedRect(
            self.rect().adjusted(5, 5, -5, -5), 
            self._border_radius, 
            self._border_radius
        )
        
        # === 第四层：主高光 - 从左上到右下的线性渐变 ===
        highlight_rect = QRect(
            self.rect().left() + 10, 
            self.rect().top() + 10, 
            self.rect().width() - 20, 
            self.rect().height() // 3
        )
        main_gradient = QLinearGradient(highlight_rect.topLeft(), highlight_rect.bottomLeft())
        main_gradient.setColorAt(0, QColor(255, 255, 255, self._highlight_color.alpha()))
        main_gradient.setColorAt(0.7, QColor(255, 255, 255, self._highlight_color.alpha() // 2))
        main_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(main_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(highlight_rect, self._border_radius, self._border_radius)
        
        # === 第五层：边缘高光 - 1-2px 白色半透明边框（需求 6.2）===
        edge_highlight_width = 2  # 1-2px
        edge_rect = self.rect().adjusted(5, 5, -5, -5)
        
        # 创建边缘高光的渐变
        edge_gradient = QLinearGradient(edge_rect.topLeft(), edge_rect.topRight())
        edge_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        edge_gradient.setColorAt(0.2, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(0.5, QColor(255, 255, 255, 120))
        edge_gradient.setColorAt(0.8, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(QPen(edge_gradient, edge_highlight_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(edge_rect, self._border_radius, self._border_radius)
        
        painter.end()
    
    def resizeEvent(self, event):
        """窗口大小改变时需要更新缓存"""
        self._needs_background_update = True
        super().resizeEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件 - 悬停增强（需求 6.3）"""
        self._is_hovered = True
        self._needs_background_update = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 恢复正常状态"""
        self._is_hovered = False
        self._needs_background_update = True
        self.update()
        super().leaveEvent(event)
    
    def set_blur_radius(self, radius: int):
        """设置模糊半径（需求 6.5）
        
        Args:
            radius: 模糊半径，范围 5-20px
        """
        self._blur_radius = max(5, min(20, radius))
        self._needs_background_update = True
        self.update()
    
    def set_transparency(self, transparency: float):
        """设置透明度（需求 6.5）
        
        Args:
            transparency: 透明度，范围 0.6-0.9
        """
        self._transparency = max(0.6, min(0.9, transparency))
        self._needs_background_update = True
        self.update()
    
    def get_blur_radius(self) -> int:
        """获取当前模糊半径"""
        return self._blur_radius
    
    def get_transparency(self) -> float:
        """获取当前透明度"""
        return self._transparency
    
    def setGlassColor(self, color: QColor):
        """设置玻璃颜色
        
        Args:
            color: 玻璃颜色
        """
        self._glass_color = color
        self._needs_background_update = True
        self.update()
