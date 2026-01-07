# -*- coding: utf-8 -*-
"""
卡片组件模块
提供现代化的卡片设计组件，支持不同层级和交互效果
"""

from typing import Optional
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPainterPath
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect

try:
    from core.theme_manager import get_theme_manager
    from utils.logger import get_logger
except ImportError:
    from ..core.theme_manager import get_theme_manager
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class CardComponent(QWidget):
    """
    现代化卡片组件
    
    提供统一的卡片样式和交互效果，支持：
    - 5 个层级（elevation 1-5）
    - 可配置的圆角半径（12-16px）
    - 可配置的内边距（16-24px）
    - 可配置的外边距（8-12px）
    - 悬停动画效果
    """
    
    # 默认配置
    DEFAULT_ELEVATION = 1
    DEFAULT_BORDER_RADIUS = 14  # 12-16px 范围内的中间值
    DEFAULT_PADDING = 20  # 16-24px 范围内的中间值
    DEFAULT_MARGIN = 10  # 8-12px 范围内的中间值
    
    # 层级对应的阴影模糊半径
    ELEVATION_SHADOW_MAP = {
        1: 4,   # elevation 1: 4px 模糊
        2: 8,   # elevation 2: 8px 模糊
        3: 12,  # elevation 3: 12px 模糊
        4: 16,  # elevation 4: 16px 模糊
        5: 20,  # elevation 5: 20px 模糊
    }
    
    # 悬停动画配置
    HOVER_LIFT_DISTANCE = 3  # 悬停时上移的像素数（2-4px）
    HOVER_ANIMATION_DURATION = 175  # 动画时长（150-200ms）
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        elevation: int = DEFAULT_ELEVATION,
        border_radius: int = DEFAULT_BORDER_RADIUS,
        padding: int = DEFAULT_PADDING,
        margin: int = DEFAULT_MARGIN,
        interactive: bool = False
    ):
        """
        初始化卡片组件
        
        Args:
            parent: 父组件
            elevation: 卡片层级（1-5），影响阴影深度
            border_radius: 圆角半径（12-16px）
            padding: 内边距（16-24px）
            margin: 外边距（8-12px）
            interactive: 是否可交互（启用悬停效果）
        """
        super().__init__(parent)
        
        # 验证并设置参数
        self._elevation = self._validate_elevation(elevation)
        self._border_radius = self._validate_border_radius(border_radius)
        self._padding = self._validate_padding(padding)
        self._margin = self._validate_margin(margin)
        self._interactive = interactive
        
        # 主题管理器
        self._theme_manager = get_theme_manager()
        
        # 悬停状态
        self._is_hovered = False
        self._hover_offset = 0  # 用于动画的垂直偏移量
        self._original_y = 0  # 记录原始 Y 坐标
        
        # 设置组件属性
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMouseTracking(True)
        
        # 初始化样式
        self._setup_style()
        self._setup_shadow()
        
        # 如果可交互，设置悬停动画
        if self._interactive:
            self._setup_hover_animation()
        
        logger.debug(
            f"卡片组件初始化: elevation={self._elevation}, "
            f"border_radius={self._border_radius}, padding={self._padding}, "
            f"margin={self._margin}, interactive={self._interactive}"
        )
    
    def _validate_elevation(self, elevation: int) -> int:
        """验证并调整 elevation 值到 1-5 范围"""
        if elevation < 1:
            logger.warning(f"elevation {elevation} 小于 1，调整为 1")
            return 1
        elif elevation > 5:
            logger.warning(f"elevation {elevation} 大于 5，调整为 5")
            return 5
        return elevation
    
    def _validate_border_radius(self, radius: int) -> int:
        """验证并调整 border_radius 到 12-16px 范围"""
        if radius < 12:
            logger.warning(f"border_radius {radius} 小于 12，调整为 12")
            return 12
        elif radius > 16:
            logger.warning(f"border_radius {radius} 大于 16，调整为 16")
            return 16
        return radius
    
    def _validate_padding(self, padding: int) -> int:
        """验证并调整 padding 到 16-24px 范围"""
        if padding < 16:
            logger.warning(f"padding {padding} 小于 16，调整为 16")
            return 16
        elif padding > 24:
            logger.warning(f"padding {padding} 大于 24，调整为 24")
            return 24
        return padding
    
    def _validate_margin(self, margin: int) -> int:
        """验证并调整 margin 到 8-12px 范围"""
        if margin < 8:
            logger.warning(f"margin {margin} 小于 8，调整为 8")
            return 8
        elif margin > 12:
            logger.warning(f"margin {margin} 大于 12，调整为 12")
            return 12
        return margin
    
    def _setup_style(self):
        """设置卡片样式"""
        # 获取当前主题颜色
        colors = self._theme_manager.get_enhanced_colors()
        surface_color = colors.get("surface", QColor(255, 255, 255))
        
        # 设置样式表
        self.setStyleSheet(f"""
            CardComponent {{
                background-color: {surface_color.name()};
                border-radius: {self._border_radius}px;
                padding: {self._padding}px;
                margin: {self._margin}px;
            }}
        """)
    
    def _setup_shadow(self):
        """设置阴影效果"""
        # 根据 elevation 获取阴影模糊半径
        blur_radius = self.ELEVATION_SHADOW_MAP.get(self._elevation, 4)
        
        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur_radius)
        shadow.setXOffset(0)
        shadow.setYOffset(2)  # 轻微的向下偏移
        
        # 获取阴影颜色
        colors = self._theme_manager.get_enhanced_colors()
        shadow_color = colors.get("shadow", QColor(0, 0, 0, 30))
        shadow.setColor(shadow_color)
        
        self.setGraphicsEffect(shadow)
        
        # 保存阴影引用以便后续修改
        self._shadow_effect = shadow
    
    def _setup_hover_animation(self):
        """设置悬停动画"""
        # 创建垂直偏移动画
        self._hover_animation = QPropertyAnimation(self, b"hoverOffset")
        self._hover_animation.setDuration(self.HOVER_ANIMATION_DURATION)
        self._hover_animation.setEasingCurve(QEasingCurve.InOutCubic)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        if self._interactive:
            self._is_hovered = True
            # 记录原始位置
            if self._original_y == 0:
                self._original_y = self.y()
            self._animate_hover(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self._interactive:
            self._is_hovered = False
            self._animate_hover(False)
        super().leaveEvent(event)
    
    def _animate_hover(self, is_entering: bool):
        """
        执行悬停动画
        
        Args:
            is_entering: True 表示鼠标进入，False 表示鼠标离开
        """
        if not hasattr(self, '_hover_animation'):
            return
        
        # 停止当前动画
        self._hover_animation.stop()
        
        if is_entering:
            # 鼠标进入：上移并加深阴影
            self._hover_animation.setStartValue(self._hover_offset)
            self._hover_animation.setEndValue(-self.HOVER_LIFT_DISTANCE)
            
            # 增加阴影模糊半径（加深阴影）
            current_blur = self.ELEVATION_SHADOW_MAP.get(self._elevation, 4)
            new_blur = current_blur + 4  # 增加 4px
            self._shadow_effect.setBlurRadius(new_blur)
            self._shadow_effect.setYOffset(4)  # 增加 Y 偏移
        else:
            # 鼠标离开：恢复原位和原始阴影
            self._hover_animation.setStartValue(self._hover_offset)
            self._hover_animation.setEndValue(0)
            
            # 恢复原始阴影
            original_blur = self.ELEVATION_SHADOW_MAP.get(self._elevation, 4)
            self._shadow_effect.setBlurRadius(original_blur)
            self._shadow_effect.setYOffset(2)
        
        self._hover_animation.start()
    
    @pyqtProperty(int)
    def hoverOffset(self):
        """获取悬停偏移量（用于动画）"""
        return self._hover_offset
    
    @hoverOffset.setter
    def hoverOffset(self, value: int):
        """设置悬停偏移量（用于动画）"""
        self._hover_offset = value
        # 通过移动组件位置来实现上移效果
        # 计算新的 Y 坐标：原始位置 + 偏移量（负值表示上移）
        if self._original_y != 0:
            new_y = self._original_y + value
            self.move(self.x(), new_y)
    
    # 属性访问器
    @property
    def elevation(self) -> int:
        """获取卡片层级"""
        return self._elevation
    
    @elevation.setter
    def elevation(self, value: int):
        """设置卡片层级"""
        self._elevation = self._validate_elevation(value)
        self._setup_shadow()
    
    @property
    def border_radius(self) -> int:
        """获取圆角半径"""
        return self._border_radius
    
    @border_radius.setter
    def border_radius(self, value: int):
        """设置圆角半径"""
        self._border_radius = self._validate_border_radius(value)
        self._setup_style()
    
    @property
    def padding(self) -> int:
        """获取内边距"""
        return self._padding
    
    @padding.setter
    def padding(self, value: int):
        """设置内边距"""
        self._padding = self._validate_padding(value)
        self._setup_style()
    
    @property
    def margin(self) -> int:
        """获取外边距"""
        return self._margin
    
    @margin.setter
    def margin(self, value: int):
        """设置外边距"""
        self._margin = self._validate_margin(value)
        self._setup_style()
    
    @property
    def interactive(self) -> bool:
        """获取是否可交互"""
        return self._interactive
    
    @interactive.setter
    def interactive(self, value: bool):
        """设置是否可交互"""
        self._interactive = value
        if value and not hasattr(self, '_hover_animation'):
            self._setup_hover_animation()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取当前主题颜色
        colors = self._theme_manager.get_enhanced_colors()
        surface_color = colors.get("surface", QColor(255, 255, 255))
        
        # 创建圆角矩形路径
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(
            rect.x(), rect.y(), rect.width(), rect.height(),
            self._border_radius, self._border_radius
        )
        
        # 填充背景
        painter.fillPath(path, surface_color)
        
        super().paintEvent(event)


class CardManager:
    """
    卡片管理器
    
    管理多个卡片实例，提供统一的样式管理和 z-index 层级系统
    """
    
    # Z-index 层级定义
    Z_INDEX_BACKGROUND = 0      # 背景层 (0-9)
    Z_INDEX_CONTENT = 10        # 内容层 (10-99)
    Z_INDEX_FLOATING = 100      # 浮动层 (100-999)
    Z_INDEX_MODAL = 1000        # 模态层 (1000+)
    
    def __init__(self):
        """初始化卡片管理器"""
        self._cards = []  # 存储所有卡片实例
        self._theme_manager = get_theme_manager()
        
        # 监听主题变化
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        
        logger.info("卡片管理器初始化完成")
    
    def create_card(
        self,
        parent: Optional[QWidget] = None,
        elevation: int = CardComponent.DEFAULT_ELEVATION,
        border_radius: int = CardComponent.DEFAULT_BORDER_RADIUS,
        padding: int = CardComponent.DEFAULT_PADDING,
        margin: int = CardComponent.DEFAULT_MARGIN,
        interactive: bool = False,
        z_index_layer: str = "content"
    ) -> CardComponent:
        """
        创建卡片组件
        
        Args:
            parent: 父组件
            elevation: 卡片层级（1-5）
            border_radius: 圆角半径（12-16px）
            padding: 内边距（16-24px）
            margin: 外边距（8-12px）
            interactive: 是否可交互
            z_index_layer: Z-index 层级 ("background", "content", "floating", "modal")
            
        Returns:
            CardComponent: 创建的卡片实例
        """
        card = CardComponent(
            parent=parent,
            elevation=elevation,
            border_radius=border_radius,
            padding=padding,
            margin=margin,
            interactive=interactive
        )
        
        # 设置 z-index
        z_index = self._get_z_index(z_index_layer)
        if parent:
            card.raise_()  # 提升到父组件的顶层
            # 注意：Qt 没有直接的 z-index 属性，需要通过 raise_() 和 lower_() 管理
        
        # 添加到管理列表
        self._cards.append(card)
        
        logger.debug(f"创建卡片: elevation={elevation}, z_index_layer={z_index_layer}")
        
        return card
    
    def _get_z_index(self, layer: str) -> int:
        """
        获取指定层级的 z-index 值
        
        Args:
            layer: 层级名称
            
        Returns:
            int: z-index 值
        """
        layer_map = {
            "background": self.Z_INDEX_BACKGROUND,
            "content": self.Z_INDEX_CONTENT,
            "floating": self.Z_INDEX_FLOATING,
            "modal": self.Z_INDEX_MODAL,
        }
        return layer_map.get(layer, self.Z_INDEX_CONTENT)
    
    def apply_consistent_style(
        self,
        elevation: Optional[int] = None,
        border_radius: Optional[int] = None,
        padding: Optional[int] = None,
        margin: Optional[int] = None
    ):
        """
        对所有卡片应用一致的样式
        
        Args:
            elevation: 卡片层级（None 表示不修改）
            border_radius: 圆角半径（None 表示不修改）
            padding: 内边距（None 表示不修改）
            margin: 外边距（None 表示不修改）
        """
        for card in self._cards:
            if elevation is not None:
                card.elevation = elevation
            if border_radius is not None:
                card.border_radius = border_radius
            if padding is not None:
                card.padding = padding
            if margin is not None:
                card.margin = margin
        
        logger.info(f"应用一致样式到 {len(self._cards)} 个卡片")
    
    def _on_theme_changed(self, theme_name: str):
        """
        主题变化回调
        
        Args:
            theme_name: 新主题名称
        """
        # 刷新所有卡片的样式
        for card in self._cards:
            card._setup_style()
            card._setup_shadow()
        
        logger.info(f"主题切换到 {theme_name}，已更新 {len(self._cards)} 个卡片")
    
    def get_cards(self) -> list:
        """获取所有卡片实例"""
        return self._cards.copy()
    
    def clear(self):
        """清除所有卡片引用"""
        self._cards.clear()
        logger.info("清除所有卡片引用")
