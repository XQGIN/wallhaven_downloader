# -*- coding: utf-8 -*-
"""
空状态组件
提供空状态、加载状态和错误状态的显示
"""

from typing import Optional, Callable
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGraphicsOpacityEffect
)

try:
    from core.theme_manager import get_theme_manager
    from ui.animation_manager import get_animation_manager
    from ui.typography_system import get_typography_system, TypographyLevel
    from utils.logger import get_logger
except ImportError:
    from ..core.theme_manager import get_theme_manager
    from .animation_manager import get_animation_manager
    from .typography_system import get_typography_system, TypographyLevel
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmptyStateType:
    """空状态类型常量"""
    EMPTY = "empty"          # 空状态
    LOADING = "loading"      # 加载中
    ERROR = "error"          # 错误状态


class SkeletonItem(QWidget):
    """骨架屏单项"""
    
    def __init__(self, width: int = 200, height: int = 20, parent=None):
        """
        初始化骨架屏单项
        
        Args:
            width: 宽度
            height: 高度
            parent: 父组件
        """
        super().__init__(parent)
        self.setFixedSize(width, height)
        
        # 脉冲动画
        self.opacity = 1.0
        self._setup_pulse_animation()
    
    def _setup_pulse_animation(self):
        """设置脉冲动画"""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.InOutSine)
        self.animation.setStartValue(0.3)
        self.animation.setEndValue(1.0)
        self.animation.setLoopCount(-1)  # 无限循环
        self.animation.start()
    
    def paintEvent(self, event):
        """绘制骨架屏"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取主题颜色
        theme_manager = get_theme_manager()
        bg_color = theme_manager.get_color("surface_hover")
        
        # 绘制圆角矩形
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 4, 4)
    
    def stop_animation(self):
        """停止动画"""
        if hasattr(self, 'animation'):
            self.animation.stop()


class SkeletonScreen(QWidget):
    """骨架屏组件"""
    
    def __init__(self, parent=None):
        """
        初始化骨架屏
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)
        
        # 创建多个骨架项
        self.skeleton_items = []
        
        # 标题骨架
        title_skeleton = SkeletonItem(300, 32, self)
        layout.addWidget(title_skeleton, 0, Qt.AlignCenter)
        self.skeleton_items.append(title_skeleton)
        
        layout.addSpacing(20)
        
        # 内容骨架（3行）
        for i in range(3):
            width = 400 if i == 1 else 350
            content_skeleton = SkeletonItem(width, 20, self)
            layout.addWidget(content_skeleton, 0, Qt.AlignCenter)
            self.skeleton_items.append(content_skeleton)
            
            if i < 2:
                layout.addSpacing(12)
        
        layout.addSpacing(30)
        
        # 按钮骨架
        button_skeleton = SkeletonItem(120, 36, self)
        layout.addWidget(button_skeleton, 0, Qt.AlignCenter)
        self.skeleton_items.append(button_skeleton)
        
        layout.addStretch()
    
    def stop_animations(self):
        """停止所有动画"""
        for item in self.skeleton_items:
            item.stop_animation()


class EmptyStateWidget(QWidget):
    """
    空状态组件
    
    支持三种状态：
    1. 空状态：显示插图和引导文字
    2. 加载状态：显示骨架屏
    3. 错误状态：显示错误信息和重试按钮
    """
    
    # 信号
    action_clicked = pyqtSignal()  # 快速操作按钮点击
    retry_clicked = pyqtSignal()   # 重试按钮点击
    
    def __init__(self, parent=None):
        """
        初始化空状态组件
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        self.animation_manager = get_animation_manager()
        self.typography_system = get_typography_system()
        
        # 导入 i18n 管理器
        try:
            from core.i18n_manager import get_i18n_manager
        except ImportError:
            from ..core.i18n_manager import get_i18n_manager
        self.i18n = get_i18n_manager()
        
        self.current_state = EmptyStateType.EMPTY
        
        self._setup_ui()
        self._apply_theme()
        
        logger.debug("EmptyStateWidget 初始化完成")
    
    def _setup_ui(self):
        """设置 UI"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignCenter)
        
        # 创建三种状态的容器
        self._create_empty_state()
        self._create_loading_state()
        self._create_error_state()
        
        # 默认显示空状态
        self.show_empty_state()
    
    def _create_empty_state(self):
        """创建空状态 UI"""
        self.empty_container = QWidget(self)
        empty_layout = QVBoxLayout(self.empty_container)
        empty_layout.setSpacing(20)
        empty_layout.setContentsMargins(40, 40, 40, 40)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        # 插图（使用文字图标代替）
        self.empty_icon = QLabel("📭", self.empty_container)
        self.empty_icon.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(64)
        self.empty_icon.setFont(icon_font)
        empty_layout.addWidget(self.empty_icon)
        
        empty_layout.addSpacing(10)
        
        # 标题
        self.empty_title = QLabel(self.i18n.t("empty_state.empty_title"), self.empty_container)
        self.empty_title.setAlignment(Qt.AlignCenter)
        self.typography_system.apply_typography(self.empty_title, TypographyLevel.HEADING_2)
        empty_layout.addWidget(self.empty_title)
        
        empty_layout.addSpacing(10)
        
        # 描述文字
        self.empty_description = QLabel(
            self.i18n.t("empty_state.empty_description"),
            self.empty_container
        )
        self.empty_description.setAlignment(Qt.AlignCenter)
        self.typography_system.apply_typography(self.empty_description, TypographyLevel.BODY)
        empty_layout.addWidget(self.empty_description)
        
        empty_layout.addSpacing(20)
        
        # 快速操作按钮
        self.action_button = QPushButton(self.i18n.t("empty_state.action_button"), self.empty_container)
        self.action_button.setMinimumSize(120, 40)
        self.action_button.setCursor(Qt.PointingHandCursor)
        self.action_button.clicked.connect(self.action_clicked.emit)
        empty_layout.addWidget(self.action_button, 0, Qt.AlignCenter)
        
        empty_layout.addStretch()
        
        self.main_layout.addWidget(self.empty_container)
    
    def _create_loading_state(self):
        """创建加载状态 UI"""
        self.loading_container = QWidget(self)
        loading_layout = QVBoxLayout(self.loading_container)
        loading_layout.setSpacing(0)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setAlignment(Qt.AlignCenter)
        
        # 骨架屏
        self.skeleton_screen = SkeletonScreen(self.loading_container)
        loading_layout.addWidget(self.skeleton_screen)
        
        self.main_layout.addWidget(self.loading_container)
        self.loading_container.hide()
    
    def _create_error_state(self):
        """创建错误状态 UI"""
        self.error_container = QWidget(self)
        error_layout = QVBoxLayout(self.error_container)
        error_layout.setSpacing(20)
        error_layout.setContentsMargins(40, 40, 40, 40)
        error_layout.setAlignment(Qt.AlignCenter)
        
        # 错误图标
        self.error_icon = QLabel("⚠️", self.error_container)
        self.error_icon.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(64)
        self.error_icon.setFont(icon_font)
        error_layout.addWidget(self.error_icon)
        
        error_layout.addSpacing(10)
        
        # 错误标题
        self.error_title = QLabel(self.i18n.t("empty_state.error_title"), self.error_container)
        self.error_title.setAlignment(Qt.AlignCenter)
        self.typography_system.apply_typography(self.error_title, TypographyLevel.HEADING_2)
        error_layout.addWidget(self.error_title)
        
        error_layout.addSpacing(10)
        
        # 错误描述
        self.error_description = QLabel(
            self.i18n.t("empty_state.error_description"),
            self.error_container
        )
        self.error_description.setAlignment(Qt.AlignCenter)
        self.typography_system.apply_typography(self.error_description, TypographyLevel.BODY)
        error_layout.addWidget(self.error_description)
        
        error_layout.addSpacing(20)
        
        # 重试按钮
        self.retry_button = QPushButton(self.i18n.t("empty_state.retry_button"), self.error_container)
        self.retry_button.setMinimumSize(120, 40)
        self.retry_button.setCursor(Qt.PointingHandCursor)
        self.retry_button.clicked.connect(self.retry_clicked.emit)
        error_layout.addWidget(self.retry_button, 0, Qt.AlignCenter)
        
        error_layout.addStretch()
        
        self.main_layout.addWidget(self.error_container)
        self.error_container.hide()
    
    def _apply_theme(self):
        """应用主题样式"""
        colors = self.theme_manager.get_all_colors()
        
        # 空状态样式
        self.empty_title.setStyleSheet(f"color: {colors['text_primary'].name()};")
        self.empty_description.setStyleSheet(f"color: {colors['text_secondary'].name()};")
        
        # 快速操作按钮样式
        self.action_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary'].name()};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover'].name()};
            }}
            QPushButton:pressed {{
                background-color: {colors['primary_active'].name()};
            }}
        """)
        
        # 错误状态样式
        self.error_title.setStyleSheet(f"color: {colors['error'].name()};")
        self.error_description.setStyleSheet(f"color: {colors['text_secondary'].name()};")
        
        # 重试按钮样式
        self.retry_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['error'].name()};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors['error_hover'].name()};
            }}
            QPushButton:pressed {{
                background-color: {colors['error_active'].name()};
            }}
        """)
    
    def show_empty_state(
        self,
        title: str = "暂无内容",
        description: str = "这里还没有任何内容\n点击下方按钮开始操作",
        action_text: str = "开始操作",
        icon: str = "📭"
    ):
        """
        显示空状态
        
        Args:
            title: 标题文字
            description: 描述文字
            action_text: 操作按钮文字
            icon: 图标（emoji 或文字）
        """
        # 更新文字
        self.empty_title.setText(title)
        self.empty_description.setText(description)
        self.action_button.setText(action_text)
        self.empty_icon.setText(icon)
        
        # 切换显示
        self._switch_state(EmptyStateType.EMPTY)
        
        logger.debug(f"显示空状态: {title}")
    
    def show_loading_state(self):
        """显示加载状态（骨架屏）"""
        self._switch_state(EmptyStateType.LOADING)
        logger.debug("显示加载状态")
    
    def show_error_state(
        self,
        title: str = "出错了",
        description: str = "加载内容时遇到了问题\n请检查网络连接后重试",
        icon: str = "⚠️"
    ):
        """
        显示错误状态
        
        Args:
            title: 错误标题
            description: 错误描述
            icon: 错误图标（emoji 或文字）
        """
        # 更新文字
        self.error_title.setText(title)
        self.error_description.setText(description)
        self.error_icon.setText(icon)
        
        # 切换显示
        self._switch_state(EmptyStateType.ERROR)
        
        logger.debug(f"显示错误状态: {title}")
    
    def _switch_state(self, new_state: str):
        """
        切换状态
        
        Args:
            new_state: 新状态
        """
        if self.current_state == new_state:
            return
        
        # 隐藏当前状态
        if self.current_state == EmptyStateType.EMPTY:
            self.animation_manager.create_fade_animation(
                self.empty_container,
                start_opacity=1.0,
                end_opacity=0.0,
                duration=150,
                callback=self.empty_container.hide
            )
        elif self.current_state == EmptyStateType.LOADING:
            self.skeleton_screen.stop_animations()
            self.animation_manager.create_fade_animation(
                self.loading_container,
                start_opacity=1.0,
                end_opacity=0.0,
                duration=150,
                callback=self.loading_container.hide
            )
        elif self.current_state == EmptyStateType.ERROR:
            self.animation_manager.create_fade_animation(
                self.error_container,
                start_opacity=1.0,
                end_opacity=0.0,
                duration=150,
                callback=self.error_container.hide
            )
        
        # 显示新状态
        def show_new_state():
            if new_state == EmptyStateType.EMPTY:
                self.empty_container.show()
                self.animation_manager.create_fade_animation(
                    self.empty_container,
                    start_opacity=0.0,
                    end_opacity=1.0,
                    duration=200
                )
            elif new_state == EmptyStateType.LOADING:
                self.loading_container.show()
                self.animation_manager.create_fade_animation(
                    self.loading_container,
                    start_opacity=0.0,
                    end_opacity=1.0,
                    duration=200
                )
            elif new_state == EmptyStateType.ERROR:
                self.error_container.show()
                self.animation_manager.create_fade_animation(
                    self.error_container,
                    start_opacity=0.0,
                    end_opacity=1.0,
                    duration=200
                )
        
        # 延迟显示新状态
        QTimer.singleShot(150, show_new_state)
        
        self.current_state = new_state
    
    def set_action_callback(self, callback: Callable):
        """
        设置快速操作按钮回调
        
        Args:
            callback: 回调函数
        """
        try:
            self.action_clicked.disconnect()
        except TypeError:
            pass  # 没有连接时忽略错误
        self.action_clicked.connect(callback)
    
    def set_retry_callback(self, callback: Callable):
        """
        设置重试按钮回调
        
        Args:
            callback: 回调函数
        """
        try:
            self.retry_clicked.disconnect()
        except TypeError:
            pass  # 没有连接时忽略错误
        self.retry_clicked.connect(callback)
    
    def cleanup(self):
        """清理资源"""
        # 停止骨架屏动画
        if hasattr(self, 'skeleton_screen'):
            self.skeleton_screen.stop_animations()
        
        logger.debug("EmptyStateWidget 资源已清理")


# 便捷函数
def create_empty_state(
    parent=None,
    title: str = "暂无内容",
    description: str = "这里还没有任何内容",
    action_text: str = "开始操作"
) -> EmptyStateWidget:
    """
    创建空状态组件的便捷函数
    
    Args:
        parent: 父组件
        title: 标题
        description: 描述
        action_text: 操作按钮文字
        
    Returns:
        EmptyStateWidget: 空状态组件实例
    """
    widget = EmptyStateWidget(parent)
    widget.show_empty_state(title, description, action_text)
    return widget
