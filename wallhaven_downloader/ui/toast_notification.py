# -*- coding: utf-8 -*-
"""
Toast 通知系统
提供非阻塞式通知反馈，支持多种通知类型和自动消失功能
"""

from typing import Optional, List, Callable
from PyQt5.QtCore import QObject, QTimer, Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout
from PyQt5.QtGui import QColor

try:
    from utils.logger import get_logger
    from core.theme_manager import get_theme_manager
    from ui.animation_manager import get_animation_manager
    from ui.icon_manager import get_icon_manager
except ImportError:
    from ..utils.logger import get_logger
    from ..core.theme_manager import get_theme_manager
    from .animation_manager import get_animation_manager
    from .icon_manager import get_icon_manager

logger = get_logger(__name__)


class ToastNotification(QWidget):
    """
    Toast 通知组件
    
    提供非阻塞式通知反馈，支持：
    - 4 种通知类型（成功、警告、错误、信息）
    - 自动消失（3-5 秒）
    - 手动关闭
    - 滑入滑出动画
    """
    
    # 通知类型
    TYPE_SUCCESS = "success"
    TYPE_WARNING = "warning"
    TYPE_ERROR = "error"
    TYPE_INFO = "info"
    
    # 信号
    closed = pyqtSignal()  # 通知关闭信号
    
    def __init__(
        self,
        message: str,
        toast_type: str = TYPE_INFO,
        duration: int = 3000,
        parent: Optional[QWidget] = None
    ):
        """
        初始化 Toast 通知
        
        Args:
            message: 通知消息
            toast_type: 通知类型 (success, warning, error, info)
            duration: 显示时长（毫秒），0 表示不自动消失
            parent: 父组件
        """
        super().__init__(parent)
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        
        self._theme_manager = get_theme_manager()
        self._animation_manager = get_animation_manager()
        self._icon_manager = get_icon_manager()
        
        # 自动消失定时器
        self._auto_dismiss_timer: Optional[QTimer] = None
        
        # 设置组件属性
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        
        # 初始化 UI
        self._setup_ui()
        
        logger.debug(f"创建 Toast 通知: 类型={toast_type}, 消息={message}, 时长={duration}ms")
    
    def _setup_ui(self):
        """设置 UI"""
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        
        # 图标
        icon_label = QLabel()
        icon = self._get_icon_for_type()
        icon_label.setPixmap(icon.pixmap(32, 32))
        icon_label.setFixedSize(32, 32)
        main_layout.addWidget(icon_label)
        
        # 消息文本
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {self._theme_manager.get_color('text_primary').name()};
                font-size: 16px;
                line-height: 1.5;
            }}
        """)
        main_layout.addWidget(message_label, 1)
        
        # 关闭按钮
        close_button = self._icon_manager.create_icon_button(
            'close',
            tooltip='关闭',
            size=20,
            parent=self,
            enable_hover_animation=False
        )
        close_button.setFixedSize(32, 32)
        close_button.clicked.connect(self.hide_toast)
        main_layout.addWidget(close_button)
        
        # 应用样式
        self._apply_style()
        
        # 调整大小
        self.adjustSize()
        self.setMinimumWidth(400)
        self.setMinimumHeight(70)
        self.setMaximumWidth(600)
    
    def _get_icon_for_type(self):
        """
        根据类型获取图标
        
        Returns:
            QIcon 对象
        """
        icon_map = {
            self.TYPE_SUCCESS: ('check', 'success'),
            self.TYPE_WARNING: ('warning', 'warning'),
            self.TYPE_ERROR: ('error', 'error'),
            self.TYPE_INFO: ('info', 'info'),
        }
        
        icon_name, color_name = icon_map.get(self.toast_type, ('info', 'info'))
        color = self._theme_manager.get_color(color_name)
        return self._icon_manager.get_colored_icon(icon_name, color, 32)
    
    def _apply_style(self):
        """应用样式"""
        # 获取类型对应的颜色
        color_map = {
            self.TYPE_SUCCESS: self._theme_manager.get_color('success'),
            self.TYPE_WARNING: self._theme_manager.get_color('warning'),
            self.TYPE_ERROR: self._theme_manager.get_color('error'),
            self.TYPE_INFO: self._theme_manager.get_color('info'),
        }
        
        accent_color = color_map.get(self.toast_type, self._theme_manager.get_color('info'))
        bg_color = self._theme_manager.get_color('surface')
        border_color = accent_color
        
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {self._rgba(bg_color)};
                border: 2px solid {border_color.name()};
                border-radius: 8px;
            }}
        """)
    
    def _rgba(self, color: QColor) -> str:
        """
        将 QColor 转换为 rgba 字符串
        
        Args:
            color: QColor 对象
            
        Returns:
            rgba 字符串
        """
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
    
    def show_toast(self):
        """显示通知（带滑入动画）"""
        # 显示组件
        self.show()
        
        # 创建滑入动画（从右侧滑入）
        self._animation_manager.create_slide_animation(
            self,
            direction='left',
            distance=100,
            duration=200,
            callback=self._on_show_complete
        )
        
        logger.debug(f"显示 Toast 通知: {self.message}")
    
    def _on_show_complete(self):
        """显示完成回调"""
        # 如果设置了自动消失时长，启动定时器
        if self.duration > 0:
            self._auto_dismiss_timer = QTimer(self)
            self._auto_dismiss_timer.setSingleShot(True)
            self._auto_dismiss_timer.timeout.connect(self.hide_toast)
            self._auto_dismiss_timer.start(self.duration)
    
    def hide_toast(self):
        """隐藏通知（带滑出动画）"""
        # 停止自动消失定时器
        if self._auto_dismiss_timer:
            self._auto_dismiss_timer.stop()
            self._auto_dismiss_timer = None
        
        # 创建滑出动画（向右滑出）
        self._animation_manager.create_slide_animation(
            self,
            direction='right',
            distance=100,
            duration=200,
            callback=self._on_hide_complete
        )
        
        logger.debug(f"隐藏 Toast 通知: {self.message}")
    
    def _on_hide_complete(self):
        """隐藏完成回调"""
        self.close()
        self.closed.emit()
        self.deleteLater()


class ToastManager(QObject):
    """
    Toast 管理器
    
    管理 Toast 通知的显示和队列：
    - 限制同时显示的通知数量（最多 3 个）
    - 队列管理（超过限制的通知进入队列）
    - 自动定位（屏幕右上角）
    """
    
    MAX_TOASTS = 3  # 最大同时显示数量
    TOAST_SPACING = 10  # 通知之间的间距
    MARGIN_TOP = 20  # 顶部边距
    MARGIN_RIGHT = 20  # 右侧边距
    
    def __init__(self, parent: QWidget):
        """
        初始化 Toast 管理器
        
        Args:
            parent: 父组件（通常是主窗口）
        """
        super().__init__(parent)
        self.parent_widget = parent
        self.active_toasts: List[ToastNotification] = []  # 活动通知列表
        self.toast_queue: List[tuple] = []  # 通知队列
        
        logger.debug("ToastManager 初始化完成")
    
    def show(
        self,
        message: str,
        toast_type: str = ToastNotification.TYPE_INFO,
        duration: int = 3000
    ):
        """
        显示 Toast 通知
        
        Args:
            message: 通知消息
            toast_type: 通知类型 (success, warning, error, info)
            duration: 显示时长（毫秒），0 表示不自动消失
        """
        # 检查是否达到最大显示数量
        if len(self.active_toasts) >= self.MAX_TOASTS:
            # 加入队列
            self.toast_queue.append((message, toast_type, duration))
            logger.debug(f"Toast 加入队列: {message}, 队列长度={len(self.toast_queue)}")
            return
        
        # 创建并显示通知
        self._create_and_show_toast(message, toast_type, duration)
    
    def _create_and_show_toast(self, message: str, toast_type: str, duration: int):
        """
        创建并显示 Toast 通知
        
        Args:
            message: 通知消息
            toast_type: 通知类型
            duration: 显示时长
        """
        # 创建通知
        toast = ToastNotification(message, toast_type, duration, self.parent_widget)
        
        # 连接关闭信号
        toast.closed.connect(lambda: self._on_toast_closed(toast))
        
        # 添加到活动列表
        self.active_toasts.append(toast)
        
        # 计算位置
        self._position_toast(toast)
        
        # 显示通知
        toast.show_toast()
        
        logger.info(f"显示 Toast: 类型={toast_type}, 消息={message}")
    
    def _position_toast(self, toast: ToastNotification):
        """
        定位 Toast 通知（与图片预览标题平行）
        
        Args:
            toast: Toast 通知组件
        """
        # 获取主窗口的全局位置和大小
        if hasattr(self.parent_widget, 'frameGeometry'):
            # 使用 frameGeometry 获取包含标题栏的完整窗口区域
            parent_frame = self.parent_widget.frameGeometry()
            parent_global_pos = QPoint(parent_frame.x(), parent_frame.y())
            parent_width = parent_frame.width()
            parent_height = parent_frame.height()
        else:
            # 回退方案：使用 geometry 和 mapToGlobal
            parent_rect = self.parent_widget.geometry()
            parent_global_pos = self.parent_widget.mapToGlobal(QPoint(0, 0))
            parent_width = parent_rect.width()
            parent_height = parent_rect.height()
        
        # 计算 x 位置（相对于主窗口右边缘）
        x = parent_global_pos.x() + parent_width - toast.width() - self.MARGIN_RIGHT
        
        # 尝试获取图片预览标题的位置
        preview_title_y = None
        if hasattr(self.parent_widget, 'preview_title'):
            try:
                preview_title = self.parent_widget.preview_title
                # 获取预览标题相对于主窗口的全局位置
                preview_global_pos = preview_title.mapToGlobal(QPoint(0, 0))
                preview_title_y = preview_global_pos.y()
                logger.debug(f"找到图片预览标题位置: y={preview_title_y}")
            except Exception as e:
                logger.debug(f"获取图片预览标题位置失败: {e}")
        
        # 计算 y 位置
        if preview_title_y is not None:
            # 与图片预览标题平行
            y = preview_title_y
        else:
            # 回退方案：使用固定偏移
            title_bar_height = 0
            if hasattr(self.parent_widget, 'frameGeometry') and hasattr(self.parent_widget, 'geometry'):
                title_bar_height = self.parent_widget.frameGeometry().height() - self.parent_widget.geometry().height()
            
            # 估算图片预览标题的位置（标题栏 + 工具栏 + 内容区域顶部边距）
            y = parent_global_pos.y() + title_bar_height + 120
        
        # 如果有其他活动通知，需要向下偏移
        toast_index = self.active_toasts.index(toast)
        for i in range(toast_index):
            if i < len(self.active_toasts):
                y += self.active_toasts[i].height() + self.TOAST_SPACING
        
        # 确保通知不会超出屏幕边界
        from PyQt5.QtWidgets import QDesktopWidget
        desktop = QDesktopWidget()
        screen_rect = desktop.screenGeometry()
        
        # 调整 x 位置，确保不超出屏幕右边界
        if x + toast.width() > screen_rect.right():
            x = screen_rect.right() - toast.width() - 10
        
        # 调整 y 位置，确保不超出屏幕下边界
        if y + toast.height() > screen_rect.bottom():
            y = screen_rect.bottom() - toast.height() - 10
        
        # 设置位置
        toast.move(x, y)
        
        logger.debug(f"Toast 定位: x={x}, y={y}, 主窗口位置=({parent_global_pos.x()}, {parent_global_pos.y()})")
    
    def _on_toast_closed(self, toast: ToastNotification):
        """
        Toast 关闭回调
        
        Args:
            toast: 关闭的 Toast 通知
        """
        # 从活动列表移除
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
        
        # 重新定位剩余的通知
        self._reposition_toasts()
        
        # 处理队列中的通知
        self._process_queue()
        
        logger.debug(f"Toast 已关闭，剩余活动通知: {len(self.active_toasts)}")
    
    def _reposition_toasts(self):
        """重新定位所有活动通知"""
        for toast in self.active_toasts:
            self._position_toast(toast)
    
    def _process_queue(self):
        """处理队列中的通知"""
        if not self.toast_queue or len(self.active_toasts) >= self.MAX_TOASTS:
            return
        
        # 取出队列中的第一个通知
        message, toast_type, duration = self.toast_queue.pop(0)
        
        # 显示通知
        self._create_and_show_toast(message, toast_type, duration)
        
        logger.debug(f"从队列显示 Toast，剩余队列: {len(self.toast_queue)}")
    
    def show_success(self, message: str, duration: int = 3000):
        """
        显示成功通知
        
        Args:
            message: 通知消息
            duration: 显示时长（毫秒）
        """
        self.show(message, ToastNotification.TYPE_SUCCESS, duration)
    
    def show_warning(self, message: str, duration: int = 4000):
        """
        显示警告通知
        
        Args:
            message: 通知消息
            duration: 显示时长（毫秒）
        """
        self.show(message, ToastNotification.TYPE_WARNING, duration)
    
    def show_error(self, message: str, duration: int = 5000):
        """
        显示错误通知
        
        Args:
            message: 通知消息
            duration: 显示时长（毫秒）
        """
        self.show(message, ToastNotification.TYPE_ERROR, duration)
    
    def show_info(self, message: str, duration: int = 3000):
        """
        显示信息通知
        
        Args:
            message: 通知消息
            duration: 显示时长（毫秒）
        """
        self.show(message, ToastNotification.TYPE_INFO, duration)
    
    def clear_all(self):
        """清除所有通知"""
        # 关闭所有活动通知
        for toast in self.active_toasts[:]:  # 使用副本避免迭代时修改列表
            toast.hide_toast()
        
        # 清空队列
        self.toast_queue.clear()
        
        logger.info("已清除所有 Toast 通知")
    
    def get_active_count(self) -> int:
        """
        获取活动通知数量
        
        Returns:
            活动通知数量
        """
        return len(self.active_toasts)
    
    def get_queue_size(self) -> int:
        """
        获取队列大小
        
        Returns:
            队列中的通知数量
        """
        return len(self.toast_queue)


# 全局单例（可选）
_toast_manager_instance: Optional[ToastManager] = None


def get_toast_manager(parent: Optional[QWidget] = None) -> ToastManager:
    """
    获取 Toast 管理器单例
    
    Args:
        parent: 父组件（首次调用时必须提供）
        
    Returns:
        ToastManager 实例
    """
    global _toast_manager_instance
    if _toast_manager_instance is None:
        if parent is None:
            raise ValueError("首次调用 get_toast_manager 必须提供 parent 参数")
        _toast_manager_instance = ToastManager(parent)
    return _toast_manager_instance
