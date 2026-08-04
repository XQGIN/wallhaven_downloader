# -*- coding: utf-8 -*-
"""
玻璃导航栏组件
提供苹果风格的液态玻璃导航栏，支持图标+文字或纯图标显示模式
"""

from typing import Optional, List, Dict, Callable
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QColor, QPainter, QPen, QLinearGradient
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy

try:
    from ui.liquid_glass.glass_panel_factory import GlassPanelFactory
    from ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from ui.icon_manager import get_icon_manager
    from ui.animation.micro_animation_controller import get_micro_animation_controller
    from core.enhanced_theme_manager import get_enhanced_theme_manager
    from core.apple_color_palette import get_apple_palette
    from utils.logger import get_logger
except ImportError:
    from .liquid_glass.glass_panel_factory import GlassPanelFactory
    from .liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from .icon_manager import get_icon_manager
    from .animation.micro_animation_controller import get_micro_animation_controller
    from ..core.enhanced_theme_manager import get_enhanced_theme_manager
    from ..core.apple_color_palette import get_apple_palette
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class NavigationItem:
    """
    导航项数据类
    
    封装导航项的所有信息
    """
    
    def __init__(
        self,
        id: str,
        label: str,
        icon_name: str,
        tooltip: str = "",
        callback: Optional[Callable] = None
    ):
        """
        初始化导航项
        
        Args:
            id: 导航项唯一标识
            label: 显示文本
            icon_name: 图标名称
            tooltip: 工具提示文本
            callback: 点击回调函数
        """
        self.id = id
        self.label = label
        self.icon_name = icon_name
        self.tooltip = tooltip or label
        self.callback = callback


class GlassNavigationBar(QWidget):
    """
    玻璃导航栏组件
    
    提供苹果风格的液态玻璃导航栏，支持：
    - 玻璃面板背景
    - 图标 + 文字或纯图标显示模式
    - 悬停效果
    - 选中状态
    - 选中指示器动画
    
    需求：4.1-4.6
    """
    
    # 信号
    item_clicked = pyqtSignal(str)  # 导航项被点击，参数为导航项 ID
    
    # 显示模式
    MODE_ICON_TEXT = "icon_text"  # 图标 + 文字
    MODE_ICON_ONLY = "icon_only"  # 仅图标
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化玻璃导航栏
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 管理器
        self.glass_factory = GlassPanelFactory()
        self.icon_manager = get_icon_manager()
        self.animation_controller = get_micro_animation_controller()
        self.theme_manager = get_enhanced_theme_manager()
        self.palette = get_apple_palette()
        
        # 导航项
        self.navigation_items: List[NavigationItem] = []
        self.navigation_buttons: Dict[str, QPushButton] = {}
        
        # 当前选中的导航项
        self.selected_item_id: Optional[str] = None
        
        # 显示模式
        self.display_mode = self.MODE_ICON_TEXT
        
        # 选中指示器
        self.indicator_widget: Optional[QWidget] = None
        self.indicator_animation: Optional[QPropertyAnimation] = None
        
        # 初始化 UI
        self._init_ui()
        
        # 连接主题变化信号
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        
        logger.info("玻璃导航栏初始化完成")
    
    def _init_ui(self):
        """初始化 UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建玻璃面板作为背景
        self.glass_panel = self.glass_factory.create_panel(
            self,
            panel_type="normal",
            custom_config={
                "blur_radius": 20,
                "transparency": 0.7,
                "border_radius": 12,
                "shadow_blur": 15
            }
        )
        
        # 创建导航项容器
        self.nav_container = QWidget(self.glass_panel)
        self.nav_layout = QHBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(8, 8, 8, 8)
        self.nav_layout.setSpacing(4)
        
        # 创建选中指示器
        self._create_indicator()
        
        # 设置布局
        panel_layout = QVBoxLayout(self.glass_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(self.nav_container)
        
        main_layout.addWidget(self.glass_panel)
        
        # 应用主题颜色
        self._apply_theme_colors()
    
    def _create_indicator(self):
        """创建选中指示器"""
        self.indicator_widget = QWidget(self.nav_container)
        self.indicator_widget.setFixedHeight(3)
        self.indicator_widget.hide()
        
        # 设置指示器样式
        self._update_indicator_style()
    
    def _update_indicator_style(self):
        """更新指示器样式"""
        if not self.indicator_widget:
            return
        
        # 获取强调色
        is_dark = self.theme_manager.is_dark_mode()
        accent_color = self.palette.get_color("accent", is_dark)
        
        self.indicator_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {accent_color.name()};
                border-radius: 1px;
            }}
        """)
    
    def add_navigation_item(
        self,
        id: str,
        label: str,
        icon_name: str,
        tooltip: str = "",
        callback: Optional[Callable] = None
    ):
        """
        添加导航项
        
        Args:
            id: 导航项唯一标识
            label: 显示文本
            icon_name: 图标名称
            tooltip: 工具提示文本
            callback: 点击回调函数
        """
        # 创建导航项数据
        nav_item = NavigationItem(id, label, icon_name, tooltip, callback)
        self.navigation_items.append(nav_item)
        
        # 创建导航按钮
        button = self._create_navigation_button(nav_item)
        self.navigation_buttons[id] = button
        
        # 添加到布局
        self.nav_layout.addWidget(button)
        
        logger.debug(f"添加导航项: {id} - {label}")
    
    def _create_navigation_button(self, nav_item: NavigationItem) -> QPushButton:
        """
        创建导航按钮
        
        Args:
            nav_item: 导航项数据
            
        Returns:
            QPushButton: 导航按钮
        """
        button = NavigationButton(nav_item.id)
        button.setObjectName(f"nav_button_{nav_item.id}")
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip(nav_item.tooltip)
        
        # 设置按钮内容
        self._update_button_content(button, nav_item)
        
        # 设置按钮样式
        self._update_button_style(button, is_selected=False)
        
        # 连接点击事件
        button.clicked.connect(lambda: self._on_item_clicked(nav_item.id))
        
        # 设置尺寸策略
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        return button
    
    def _update_button_content(self, button: QPushButton, nav_item: NavigationItem):
        """
        更新按钮内容
        
        Args:
            button: 按钮组件
            nav_item: 导航项数据
        """
        # 获取图标
        icon = self.icon_manager.get_themed_icon(nav_item.icon_name, size=24)
        button.setIcon(icon)
        button.setIconSize(QSize(24, 24))
        
        # 根据显示模式设置文本
        if self.display_mode == self.MODE_ICON_TEXT:
            button.setText(nav_item.label)
            button.setMinimumHeight(48)
        else:
            button.setText("")
            button.setFixedSize(48, 48)
    
    def _update_button_style(self, button: QPushButton, is_selected: bool):
        """
        更新按钮样式
        
        Args:
            button: 按钮组件
            is_selected: 是否为选中状态
        """
        # 获取主题颜色
        is_dark = self.theme_manager.is_dark_mode()
        colors = self.palette.get_all_colors(is_dark)
        
        # 根据选中状态设置样式
        if is_selected:
            bg_color = colors["accent"]
            text_color = QColor(255, 255, 255)
            bg_alpha = 255
        else:
            bg_color = colors["surface"]
            text_color = colors["text_primary"]
            bg_alpha = 0  # 默认透明
        
        # 悬停和激活状态的颜色
        hover_color = colors["glass_hover"]
        active_color = colors["glass_active"]
        
        # 设置样式表
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, {bg_alpha});
                color: {text_color.name()};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: rgba({hover_color.red()}, {hover_color.green()}, {hover_color.blue()}, {hover_color.alpha()});
            }}
            QPushButton:pressed {{
                background-color: rgba({active_color.red()}, {active_color.green()}, {active_color.blue()}, {active_color.alpha()});
            }}
        """)
    
    def _on_item_clicked(self, item_id: str):
        """
        导航项点击处理
        
        Args:
            item_id: 导航项 ID
        """
        logger.debug(f"导航项被点击: {item_id}")
        
        # 设置选中状态
        self.set_selected_item(item_id)
        
        # 发射信号
        self.item_clicked.emit(item_id)
        
        # 执行回调
        for nav_item in self.navigation_items:
            if nav_item.id == item_id and nav_item.callback:
                nav_item.callback()
                break
    
    def set_selected_item(self, item_id: str, animate: bool = True):
        """
        设置选中的导航项
        
        Args:
            item_id: 导航项 ID
            animate: 是否显示动画
        """
        if item_id not in self.navigation_buttons:
            logger.warning(f"导航项不存在: {item_id}")
            return
        
        # 更新选中状态
        old_selected_id = self.selected_item_id
        self.selected_item_id = item_id
        
        # 更新所有按钮的样式
        for nav_id, button in self.navigation_buttons.items():
            is_selected = (nav_id == item_id)
            self._update_button_style(button, is_selected)
        
        # 移动选中指示器
        if animate:
            self._animate_indicator(item_id)
        else:
            self._move_indicator(item_id)
        
        logger.debug(f"选中导航项: {item_id}")
    
    def _move_indicator(self, item_id: str):
        """
        移动选中指示器（无动画）
        
        Args:
            item_id: 导航项 ID
        """
        if item_id not in self.navigation_buttons:
            return
        
        button = self.navigation_buttons[item_id]
        
        # 计算指示器位置
        button_geometry = button.geometry()
        indicator_x = button_geometry.x()
        indicator_y = button_geometry.bottom() - 3
        indicator_width = button_geometry.width()
        
        # 移动指示器
        self.indicator_widget.setGeometry(
            indicator_x,
            indicator_y,
            indicator_width,
            3
        )
        self.indicator_widget.show()
    
    def _animate_indicator(self, item_id: str):
        """
        移动选中指示器（带动画）
        
        Args:
            item_id: 导航项 ID
            
        需求：4.6 - 选中指示器动画，过渡时间 200-300 毫秒
        """
        if item_id not in self.navigation_buttons:
            return
        
        button = self.navigation_buttons[item_id]
        
        # 计算目标位置
        button_geometry = button.geometry()
        target_x = button_geometry.x()
        target_y = button_geometry.bottom() - 3
        target_width = button_geometry.width()
        
        # 如果指示器未显示，直接移动
        if not self.indicator_widget.isVisible():
            self._move_indicator(item_id)
            return
        
        # 停止之前的动画
        if self.indicator_animation and self.indicator_animation.state() == QPropertyAnimation.Running:
            self.indicator_animation.stop()
        
        # 创建动画
        self.indicator_animation = QPropertyAnimation(self.indicator_widget, b"geometry")
        self.indicator_animation.setDuration(250)  # 250ms，符合 200-300ms 要求
        self.indicator_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 设置起始和结束值
        current_geometry = self.indicator_widget.geometry()
        target_geometry = QRect(target_x, target_y, target_width, 3)
        
        self.indicator_animation.setStartValue(current_geometry)
        self.indicator_animation.setEndValue(target_geometry)
        
        # 启动动画
        self.indicator_animation.start()
        
        logger.debug(f"指示器动画: {current_geometry} -> {target_geometry}")
    
    def set_display_mode(self, mode: str):
        """
        设置显示模式
        
        Args:
            mode: 显示模式 (MODE_ICON_TEXT 或 MODE_ICON_ONLY)
            
        需求：4.3 - 支持图标 + 文字或纯图标两种显示模式
        """
        if mode not in [self.MODE_ICON_TEXT, self.MODE_ICON_ONLY]:
            logger.warning(f"无效的显示模式: {mode}")
            return
        
        self.display_mode = mode
        
        # 更新所有按钮的内容
        for nav_item in self.navigation_items:
            if nav_item.id in self.navigation_buttons:
                button = self.navigation_buttons[nav_item.id]
                self._update_button_content(button, nav_item)
        
        logger.debug(f"显示模式已更改: {mode}")
    
    def get_selected_item_id(self) -> Optional[str]:
        """
        获取当前选中的导航项 ID
        
        Returns:
            Optional[str]: 选中的导航项 ID，如果没有选中则返回 None
        """
        return self.selected_item_id
    
    def clear_navigation_items(self):
        """清除所有导航项"""
        # 移除所有按钮
        for button in self.navigation_buttons.values():
            self.nav_layout.removeWidget(button)
            button.deleteLater()
        
        # 清空数据
        self.navigation_items.clear()
        self.navigation_buttons.clear()
        self.selected_item_id = None
        
        # 隐藏指示器
        if self.indicator_widget:
            self.indicator_widget.hide()
        
        logger.debug("所有导航项已清除")
    
    def _apply_theme_colors(self):
        """应用主题颜色"""
        # 获取主题颜色
        is_dark = self.theme_manager.is_dark_mode()
        colors = self.palette.get_all_colors(is_dark)
        
        # 更新玻璃面板颜色
        if self.glass_panel:
            self.glass_panel.update_theme_colors(colors, is_dark)
        
        # 更新指示器样式
        self._update_indicator_style()
        
        # 更新所有按钮样式
        for nav_id, button in self.navigation_buttons.items():
            is_selected = (nav_id == self.selected_item_id)
            self._update_button_style(button, is_selected)
    
    def _on_theme_changed(self):
        """主题变化处理"""
        logger.debug("主题已变化，更新导航栏颜色")
        self._apply_theme_colors()
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        
        # 更新指示器位置
        if self.selected_item_id:
            self._move_indicator(self.selected_item_id)


def create_default_navigation_bar(parent: Optional[QWidget] = None) -> GlassNavigationBar:
    """
    创建默认的导航栏（包含下载、预览、设置、关于四个导航项）
    
    Args:
        parent: 父组件
        
    Returns:
        GlassNavigationBar: 导航栏组件
        
    需求：4.2 - 包含主要功能入口：下载、预览、设置、关于
    """
    nav_bar = GlassNavigationBar(parent)
    
    # 添加导航项
    nav_bar.add_navigation_item(
        id="download",
        label="下载",
        icon_name="download",
        tooltip="下载壁纸"
    )
    
    nav_bar.add_navigation_item(
        id="preview",
        label="预览",
        icon_name="image",
        tooltip="预览图片"
    )
    
    nav_bar.add_navigation_item(
        id="settings",
        label="设置",
        icon_name="settings",
        tooltip="应用设置"
    )
    
    nav_bar.add_navigation_item(
        id="about",
        label="关于",
        icon_name="info",
        tooltip="关于应用"
    )
    
    # 默认选中第一个导航项
    nav_bar.set_selected_item("download", animate=False)
    
    logger.info("默认导航栏创建完成")
    return nav_bar



class NavigationButton(QPushButton):
    """
    导航按钮组件
    
    支持悬停动画效果：
    - 背景色变化
    - 轻微放大（scale 1.05）
    
    需求：4.4 - 悬停效果（背景色变化 + 轻微放大）
    """
    
    def __init__(self, item_id: str, parent: Optional[QWidget] = None):
        """
        初始化导航按钮
        
        Args:
            item_id: 导航项 ID
            parent: 父组件
        """
        super().__init__(parent)
        self.item_id = item_id
        self._scale = 1.0
        self._is_hovered = False
        
        # 创建缩放动画
        self._scale_animation = QPropertyAnimation(self, b"scaleValue")
        self._scale_animation.setDuration(200)  # 200ms 动画时长
        self._scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 获取动画控制器
        self.animation_controller = get_micro_animation_controller()
    
    def enterEvent(self, event):
        """
        鼠标进入事件 - 悬停效果
        
        需求：4.4 - 悬停效果（背景色变化 + 轻微放大）
        """
        super().enterEvent(event)
        self._is_hovered = True
        
        # 启动放大动画
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.05)  # 放大到 1.05 倍
        self._scale_animation.start()
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 恢复正常"""
        super().leaveEvent(event)
        self._is_hovered = False
        
        # 启动恢复动画
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.0)  # 恢复到原始大小
        self._scale_animation.start()
    
    def paintEvent(self, event):
        """重写绘制事件以应用缩放变换"""
        super().paintEvent(event)
    
    def getScaleValue(self) -> float:
        """获取缩放比例"""
        return self._scale
    
    def setScaleValue(self, scale: float):
        """设置缩放比例"""
        self._scale = scale
        
        # 通过调整最小尺寸来模拟缩放效果
        if hasattr(self, '_original_size') and self._original_size:
            new_width = int(self._original_size.width() * scale)
            new_height = int(self._original_size.height() * scale)
            self.setMinimumSize(new_width, new_height)
        
        self.update()
    
    # 定义 Qt 属性以便 QPropertyAnimation 使用
    from PyQt5.QtCore import pyqtProperty
    scaleValue = pyqtProperty(float, getScaleValue, setScaleValue)
    
    def resizeEvent(self, event):
        """记录原始尺寸"""
        super().resizeEvent(event)
        if not hasattr(self, '_original_size') or not self._original_size:
            self._original_size = event.size()
