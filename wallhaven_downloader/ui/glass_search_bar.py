# -*- coding: utf-8 -*-
"""
玻璃搜索栏组件
提供苹果风格的液态玻璃搜索栏，支持搜索图标、清除按钮和焦点状态动画
"""

from typing import Optional, List, Callable
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QPen, QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QCompleter

try:
    from ui.liquid_glass.glass_panel_factory import GlassPanelFactory
    from ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from ui.icon_manager import get_icon_manager
    from ui.animation.micro_animation_controller import get_micro_animation_controller
    from core.enhanced_theme_manager import get_enhanced_theme_manager
    from core.apple_color_palette import get_apple_palette
    from utils.logger import get_logger
    from utils.accessibility_manager import get_accessibility_manager
except ImportError:
    from .liquid_glass.glass_panel_factory import GlassPanelFactory
    from .liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from .icon_manager import get_icon_manager
    from .animation.micro_animation_controller import get_micro_animation_controller
    from ..core.enhanced_theme_manager import get_enhanced_theme_manager
    from ..core.apple_color_palette import get_apple_palette
    from ..utils.logger import get_logger
    from ..utils.accessibility_manager import get_accessibility_manager

logger = get_logger(__name__)


class GlassSearchBar(QWidget):
    """
    玻璃搜索栏组件
    
    提供苹果风格的液态玻璃搜索栏，支持：
    - 玻璃面板背景
    - 搜索图标
    - 清除按钮（有内容时显示）
    - 焦点状态（发光边框）
    - 占位符动画
    - 实时搜索建议
    
    需求：5.1-5.8
    """
    
    # 信号
    textChanged = pyqtSignal(str)  # 文本改变信号
    returnPressed = pyqtSignal()   # 回车按下信号
    searchTriggered = pyqtSignal(str)  # 搜索触发信号
    
    def __init__(self, parent: Optional[QWidget] = None, placeholder: str = "搜索..."):
        """
        初始化玻璃搜索栏
        
        Args:
            parent: 父组件
            placeholder: 占位符文本
        """
        super().__init__(parent)
        
        # 管理器
        self.glass_factory = GlassPanelFactory()
        self.icon_manager = get_icon_manager()
        self.animation_controller = get_micro_animation_controller()
        self.theme_manager = get_enhanced_theme_manager()
        self.palette = get_apple_palette()
        self.accessibility_manager = get_accessibility_manager()
        
        # 占位符文本
        self.placeholder_text = placeholder
        
        # 焦点状态
        self._is_focused = False
        self._border_glow_opacity = 0.0  # 边框发光透明度
        
        # 占位符动画状态
        self._placeholder_opacity = 1.0
        
        # 初始化 UI
        self._init_ui()
        
        # 设置辅助功能
        self._setup_accessibility()
        
        # 连接主题变化信号
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        
        logger.info("玻璃搜索栏初始化完成")
    
    def _init_ui(self):
        """
        初始化 UI
        
        需求：5.1 - 使用玻璃效果
        需求：5.2 - 圆角设计，圆角半径为 10-12 像素
        需求：5.3 - 包含搜索图标、输入框、清除按钮
        """
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建玻璃面板作为背景
        self.glass_panel = self.glass_factory.create_panel(
            self,
            panel_type="normal",
            custom_config={
                "blur_radius": 15,
                "transparency": 0.7,
                "border_radius": 12,  # 10-12 像素圆角
                "shadow_blur": 10
            }
        )
        
        # 创建搜索栏容器
        self.search_container = QWidget(self.glass_panel)
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(8)
        
        # 搜索图标
        self.search_icon = self._create_search_icon()
        search_layout.addWidget(self.search_icon)
        
        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.placeholder_text)
        self.input_field.setFrame(False)  # 无边框
        self.input_field.setMinimumHeight(32)
        self.input_field.setAttribute(Qt.WA_TranslucentBackground)
        search_layout.addWidget(self.input_field, 1)  # 拉伸填充
        
        # 清除按钮
        self.clear_button = self._create_clear_button()
        self.clear_button.setVisible(False)  # 初始隐藏
        search_layout.addWidget(self.clear_button)
        
        # 设置容器布局
        panel_layout = QHBoxLayout(self.glass_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(self.search_container)
        
        main_layout.addWidget(self.glass_panel)
        
        # 连接信号
        self.input_field.textChanged.connect(self._on_text_changed)
        self.input_field.returnPressed.connect(self._on_return_pressed)
        self.clear_button.clicked.connect(self.clear)
        
        # 重写焦点事件
        self.input_field.focusInEvent = self._on_focus_in
        self.input_field.focusOutEvent = self._on_focus_out
        
        # 创建动画
        self._create_animations()
        
        # 应用主题颜色
        self._apply_theme_colors()
        
        # 设置固定高度
        self.setFixedHeight(48)
    
    def _create_search_icon(self) -> QPushButton:
        """
        创建搜索图标
        
        Returns:
            QPushButton: 搜索图标按钮
        """
        icon_button = QPushButton()
        icon_button.setFixedSize(24, 24)
        icon_button.setFlat(True)
        icon_button.setCursor(Qt.ArrowCursor)  # 不可点击
        icon_button.setEnabled(False)  # 禁用点击
        
        # 设置图标
        icon = self.icon_manager.get_themed_icon("search", size=20)
        icon_button.setIcon(icon)
        icon_button.setIconSize(QSize(20, 20))
        
        return icon_button
    
    def _create_clear_button(self) -> QPushButton:
        """
        创建清除按钮
        
        Returns:
            QPushButton: 清除按钮
        """
        clear_btn = QPushButton("×")
        clear_btn.setFixedSize(24, 24)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setObjectName("clearButton")
        
        return clear_btn
    
    def _create_animations(self):
        """
        创建动画
        
        需求：5.4 - 焦点状态（发光边框）
        需求：5.6 - 占位符文本淡入淡出动画
        """
        # 边框发光动画
        self.border_glow_animation = QPropertyAnimation(self, b"border_glow_opacity")
        self.border_glow_animation.setDuration(200)
        self.border_glow_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 占位符淡入淡出动画
        self.placeholder_animation = QPropertyAnimation(self, b"placeholder_opacity")
        self.placeholder_animation.setDuration(150)
        self.placeholder_animation.setEasingCurve(QEasingCurve.InOutCubic)
    
    def _on_focus_in(self, event):
        """
        输入框获得焦点
        
        需求：5.4 - 获得焦点时显示发光边框效果（2 像素强调色边框）
        """
        QLineEdit.focusInEvent(self.input_field, event)
        self._is_focused = True
        
        # 启动边框发光动画
        self.border_glow_animation.setStartValue(self._border_glow_opacity)
        self.border_glow_animation.setEndValue(1.0)
        self.border_glow_animation.start()
        
        # 如果有文本，淡出占位符
        if self.input_field.text():
            self._fade_out_placeholder()
        
        logger.debug("搜索栏获得焦点")
    
    def _on_focus_out(self, event):
        """
        输入框失去焦点
        
        需求：5.5 - 失去焦点时恢复默认边框（1 像素半透明边框）
        """
        QLineEdit.focusOutEvent(self.input_field, event)
        self._is_focused = False
        
        # 反向播放边框发光动画
        self.border_glow_animation.setStartValue(self._border_glow_opacity)
        self.border_glow_animation.setEndValue(0.0)
        self.border_glow_animation.start()
        
        # 如果没有文本，淡入占位符
        if not self.input_field.text():
            self._fade_in_placeholder()
        
        logger.debug("搜索栏失去焦点")
    
    def _on_text_changed(self, text: str):
        """
        文本改变处理
        
        需求：5.8 - 用户输入文本时显示清除按钮，带有淡入动画
        """
        # 显示/隐藏清除按钮（带淡入淡出动画）
        if text and not self.clear_button.isVisible():
            self._show_clear_button()
        elif not text and self.clear_button.isVisible():
            self._hide_clear_button()
        
        # 占位符动画
        if text and self._placeholder_opacity > 0:
            self._fade_out_placeholder()
        elif not text and self._placeholder_opacity < 1:
            self._fade_in_placeholder()
        
        # 发射信号
        self.textChanged.emit(text)
        
        logger.debug(f"搜索文本改变: {text}")
    
    def _on_return_pressed(self):
        """回车按下处理"""
        text = self.input_field.text().strip()
        if text:
            self.searchTriggered.emit(text)
            self.returnPressed.emit()
            logger.debug(f"搜索触发: {text}")
    
    def _show_clear_button(self):
        """
        显示清除按钮（带淡入动画）
        
        需求：5.8 - 清除按钮带有淡入动画
        """
        self.clear_button.show()
        self.animation_controller.create_fade_animation(
            self.clear_button,
            start_opacity=0.0,
            end_opacity=1.0,
            duration=150
        )
    
    def _hide_clear_button(self):
        """隐藏清除按钮（带淡出动画）"""
        self.animation_controller.create_fade_animation(
            self.clear_button,
            start_opacity=1.0,
            end_opacity=0.0,
            duration=150,
            callback=lambda: self.clear_button.hide()
        )
    
    def _fade_out_placeholder(self):
        """
        淡出占位符
        
        需求：5.6 - 占位符文本淡入淡出动画
        """
        self.placeholder_animation.setStartValue(self._placeholder_opacity)
        self.placeholder_animation.setEndValue(0.0)
        self.placeholder_animation.start()
    
    def _fade_in_placeholder(self):
        """
        淡入占位符
        
        需求：5.6 - 占位符文本淡入淡出动画
        """
        self.placeholder_animation.setStartValue(self._placeholder_opacity)
        self.placeholder_animation.setEndValue(1.0)
        self.placeholder_animation.start()
    
    def paintEvent(self, event):
        """
        绘制搜索栏
        
        需求：5.4 - 焦点状态显示发光边框（2 像素强调色边框）
        需求：5.5 - 默认边框（1 像素半透明边框）
        """
        super().paintEvent(event)
        
        # 绘制边框
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取主题颜色
        is_dark = self.theme_manager.is_dark_mode()
        colors = self.palette.get_all_colors(is_dark)
        
        # 计算边框颜色和宽度
        if self._is_focused and self._border_glow_opacity > 0:
            # 焦点状态：发光边框（2 像素强调色）
            border_color = colors["accent"]
            border_width = 2
            alpha = int(255 * self._border_glow_opacity)
            border_color.setAlpha(alpha)
        else:
            # 默认状态：半透明边框（1 像素）
            border_color = colors["border"]
            border_width = 1
        
        # 绘制边框
        pen = QPen(border_color, border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # 绘制圆角矩形边框
        rect = self.glass_panel.rect().adjusted(
            border_width // 2,
            border_width // 2,
            -border_width // 2,
            -border_width // 2
        )
        painter.drawRoundedRect(rect, 12, 12)
    
    def _apply_theme_colors(self):
        """应用主题颜色"""
        # 获取主题颜色
        is_dark = self.theme_manager.is_dark_mode()
        colors = self.palette.get_all_colors(is_dark)
        
        # 更新玻璃面板颜色
        if self.glass_panel:
            self.glass_panel.update_theme_colors(colors, is_dark)
        
        # 输入框样式
        input_style = f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {colors["text_primary"].name()};
                font-size: 14px;
                padding: 0px;
            }}
            QLineEdit::placeholder {{
                color: {colors["text_secondary"].name()};
            }}
        """
        self.input_field.setStyleSheet(input_style)
        
        # 搜索图标样式
        search_icon_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
            }}
        """
        self.search_icon.setStyleSheet(search_icon_style)
        
        # 清除按钮样式
        clear_button_style = f"""
            QPushButton#clearButton {{
                background-color: transparent;
                border: none;
                color: {colors["text_secondary"].name()};
                font-size: 20px;
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton#clearButton:hover {{
                background-color: rgba({colors["surface"].red()}, {colors["surface"].green()}, {colors["surface"].blue()}, 100);
                color: {colors["text_primary"].name()};
            }}
            QPushButton#clearButton:pressed {{
                background-color: rgba({colors["surface"].red()}, {colors["surface"].green()}, {colors["surface"].blue()}, 150);
            }}
        """
        self.clear_button.setStyleSheet(clear_button_style)
    
    def _on_theme_changed(self):
        """主题变化处理"""
        logger.debug("主题已变化，更新搜索栏颜色")
        self._apply_theme_colors()
        self.update()
    
    def text(self) -> str:
        """获取搜索文本"""
        return self.input_field.text()
    
    def setText(self, text: str):
        """设置搜索文本"""
        self.input_field.setText(text)
    
    def clear(self):
        """清除搜索文本"""
        self.input_field.clear()
        logger.debug("搜索栏已清除")
    
    def setPlaceholderText(self, text: str):
        """设置占位符文本"""
        self.placeholder_text = text
        self.input_field.setPlaceholderText(text)
    
    def setFocus(self):
        """设置焦点到输入框"""
        self.input_field.setFocus()
    
    def set_suggestions(self, suggestions: List[str]):
        """
        设置搜索建议
        
        Args:
            suggestions: 建议列表
            
        需求：5.7 - 支持实时搜索建议下拉列表（使用 Glass_Panel）
        """
        # 创建或更新自动完成器
        if suggestions:
            completer = QCompleter(suggestions)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            completer.setMaxVisibleItems(10)
            
            # 设置自动完成器样式（使用玻璃效果）
            is_dark = self.theme_manager.is_dark_mode()
            colors = self.palette.get_all_colors(is_dark)
            
            popup_style = f"""
                QListView {{
                    background-color: rgba({colors["surface"].red()}, {colors["surface"].green()}, {colors["surface"].blue()}, 230);
                    border: 1px solid {colors["border"].name()};
                    border-radius: 8px;
                    padding: 4px;
                    color: {colors["text_primary"].name()};
                    font-size: 14px;
                    outline: none;
                }}
                QListView::item {{
                    padding: 8px 12px;
                    border-radius: 4px;
                }}
                QListView::item:hover {{
                    background-color: rgba({colors["accent"].red()}, {colors["accent"].green()}, {colors["accent"].blue()}, 50);
                }}
                QListView::item:selected {{
                    background-color: {colors["accent"].name()};
                    color: white;
                }}
            """
            
            completer.popup().setStyleSheet(popup_style)
            self.input_field.setCompleter(completer)
            
            logger.debug(f"设置搜索建议: {len(suggestions)} 项")
        else:
            self.input_field.setCompleter(None)
    
    def get_border_glow_opacity(self) -> float:
        """获取边框发光透明度"""
        return self._border_glow_opacity
    
    def set_border_glow_opacity(self, opacity: float):
        """设置边框发光透明度"""
        self._border_glow_opacity = opacity
        self.update()
    
    def get_placeholder_opacity(self) -> float:
        """获取占位符透明度"""
        return self._placeholder_opacity
    
    def set_placeholder_opacity(self, opacity: float):
        """设置占位符透明度"""
        self._placeholder_opacity = opacity
    
    def _setup_accessibility(self):
        """设置辅助功能支持"""
        # 为搜索栏设置 ARIA 标签
        self.accessibility_manager.setup_input_accessibility(
            self.input_field,
            label="搜索",
            placeholder=self.placeholder_text,
            required=False
        )
        
        # 设置搜索栏角色
        self.accessibility_manager.set_aria_role(self, 'searchbox')
        
        # 为清除按钮设置辅助功能
        self.accessibility_manager.setup_button_accessibility(
            self.clear_button,
            label="清除搜索",
            description="清除当前搜索文本"
        )
        
        # 设置焦点策略
        self.input_field.setFocusPolicy(Qt.StrongFocus)
        
        logger.debug("搜索栏辅助功能已设置")
    
    # 定义 Qt 属性以便 QPropertyAnimation 使用
    border_glow_opacity = pyqtProperty(float, get_border_glow_opacity, set_border_glow_opacity)
    placeholder_opacity = pyqtProperty(float, get_placeholder_opacity, set_placeholder_opacity)


def create_default_search_bar(parent: Optional[QWidget] = None) -> GlassSearchBar:
    """
    创建默认的搜索栏
    
    Args:
        parent: 父组件
        
    Returns:
        GlassSearchBar: 搜索栏组件
    """
    search_bar = GlassSearchBar(parent, placeholder="搜索壁纸...")
    logger.info("默认搜索栏创建完成")
    return search_bar
