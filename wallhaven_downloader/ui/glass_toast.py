# -*- coding: utf-8 -*-
"""
玻璃 Toast 通知系统

扩展现有 ToastNotification，集成液态玻璃效果
提供四种类型的通知：成功、信息、警告、错误
"""

from typing import Optional, List
from PyQt5.QtCore import QObject, QTimer, Qt, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QPen

try:
    from utils.logger import get_logger
    from ui.animation_manager import get_animation_manager
    from ui.icon_manager import get_icon_manager
    from ui.liquid_glass.liquid_glass_manager import LiquidGlassManager
    from ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from utils.accessibility_manager import get_accessibility_manager
except ImportError:
    from ..utils.logger import get_logger
    from .animation_manager import get_animation_manager
    from .icon_manager import get_icon_manager
    from .liquid_glass.liquid_glass_manager import LiquidGlassManager
    from .liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from ..utils.accessibility_manager import get_accessibility_manager

logger = get_logger(__name__)


class GlassToast(QWidget):
    """
    玻璃 Toast 通知组件
    
    扩展现有 ToastNotification，集成液态玻璃效果
    
    特性：
    - 使用玻璃面板作为背景
    - 四种通知类型（成功、信息、警告、错误）
    - 滑入滑出动画
    - 自动消失（3-5 秒）
    - 支持堆叠显示
    
    需求：10.1-10.4, 10.7
    """
    
    # 通知类型
    TYPE_SUCCESS = "success"
    TYPE_INFO = "info"
    TYPE_WARNING = "warning"
    TYPE_ERROR = "error"
    
    # 信号
    closed = pyqtSignal()  # 通知关闭信号
    
    def __init__(
        self,
        message: str,
        toast_type: str = TYPE_INFO,
        duration: int = 3000,
        parent: Optional[QWidget] = None,
        glass_manager: Optional[LiquidGlassManager] = None
    ):
        """
        初始化玻璃 Toast 通知
        
        Args:
            message: 通知消息
            toast_type: 通知类型 (success, info, warning, error)
            duration: 显示时长（毫秒），0 表示不自动消失
            parent: 父组件
            glass_manager: 液态玻璃管理器实例
        """
        super().__init__(parent)
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        
        # 管理器
        self._animation_manager = get_animation_manager()
        self._icon_manager = get_icon_manager()
        self._glass_manager = glass_manager
        self._accessibility_manager = get_accessibility_manager()
        
        # 自动消失定时器
        self._auto_dismiss_timer: Optional[QTimer] = None
        
        # 动画
        self._slide_in_animation: Optional[QPropertyAnimation] = None
        self._slide_out_animation: Optional[QPropertyAnimation] = None
        self._fade_out_animation: Optional[QPropertyAnimation] = None
        
        # 设置组件属性
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        
        # 玻璃面板（背景）
        self._glass_panel: Optional[EnhancedGlassPanel] = None
        
        # 初始化 UI
        self._setup_ui()
        
        # 设置辅助功能
        self._setup_accessibility()
        
        logger.debug(f"创建玻璃 Toast 通知: 类型={toast_type}, 消息={message}, 时长={duration}ms")
    
    def _setup_ui(self):
        """设置 UI"""
        # 创建玻璃面板作为背景
        self._create_glass_background()
        
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)
        
        # 图标
        icon_label = QLabel()
        icon = self._get_icon_for_type()
        icon_label.setPixmap(icon.pixmap(24, 24))
        icon_label.setFixedSize(24, 24)
        main_layout.addWidget(icon_label)
        
        # 消息文本
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: rgb(60, 60, 60);
                font-size: 14px;
                background: transparent;
            }}
        """)
        main_layout.addWidget(message_label, 1)
        
        # 关闭按钮
        close_button = self._icon_manager.create_icon_button(
            'close',
            tooltip='关闭',
            size=16,
            parent=self,
            enable_hover_animation=False
        )
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.hide_toast)
        main_layout.addWidget(close_button)
        
        # 调整大小
        self.adjustSize()
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
    
    def _create_glass_background(self):
        """创建玻璃面板背景"""
        if self._glass_manager:
            # 使用液态玻璃管理器创建面板
            self._glass_panel = self._glass_manager.create_glass_panel(
                parent=self,
                panel_type="elevated",  # 使用 elevated 类型以获得更好的视觉效果
                blur_radius=25,
                transparency=0.85
            )
        else:
            # 如果没有玻璃管理器，创建基础玻璃面板
            config = {
                "blur_radius": 25,
                "transparency": 0.85,
                "border_radius": 10,
                "shadow_blur": 30
            }
            self._glass_panel = EnhancedGlassPanel(self, config)
        
        # 设置玻璃面板大小与父组件相同
        if self._glass_panel:
            self._glass_panel.setGeometry(self.rect())
            self._glass_panel.lower()  # 确保在最底层
    
    def resizeEvent(self, event):
        """
        调整大小事件
        
        Args:
            event: 事件对象
        """
        super().resizeEvent(event)
        # 同步调整玻璃面板大小
        if self._glass_panel:
            self._glass_panel.setGeometry(self.rect())
    
    def paintEvent(self, event):
        """
        绘制事件 - 添加类型特定的强调色边框
        
        Args:
            event: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取类型对应的强调色
        accent_color = self._get_accent_color_for_type()
        
        # 绘制强调色边框（左侧）
        border_width = 4
        path = QPainterPath()
        path.addRoundedRect(
            0, 0,
            border_width, self.height(),
            2, 2
        )
        painter.fillPath(path, QBrush(accent_color))
        
        super().paintEvent(event)
    
    def _get_icon_for_type(self):
        """
        根据类型获取图标
        
        Returns:
            QIcon 对象
        """
        icon_map = {
            self.TYPE_SUCCESS: ('check', QColor(34, 197, 94)),  # 绿色
            self.TYPE_WARNING: ('warning', QColor(245, 158, 11)),  # 橙色
            self.TYPE_ERROR: ('error', QColor(239, 68, 68)),  # 红色
            self.TYPE_INFO: ('info', QColor(59, 130, 246)),  # 蓝色
        }
        
        icon_name, color = icon_map.get(self.toast_type, ('info', QColor(59, 130, 246)))
        return self._icon_manager.get_colored_icon(icon_name, color, 24)
    
    def _get_accent_color_for_type(self) -> QColor:
        """
        根据类型获取强调色
        
        Returns:
            QColor 对象
        """
        color_map = {
            self.TYPE_SUCCESS: QColor(34, 197, 94),  # 绿色
            self.TYPE_WARNING: QColor(245, 158, 11),  # 橙色
            self.TYPE_ERROR: QColor(239, 68, 68),  # 红色
            self.TYPE_INFO: QColor(59, 130, 246),  # 蓝色
        }
        
        return color_map.get(self.toast_type, QColor(59, 130, 246))
    
    def show_toast(self):
        """
        显示通知（带滑入动画）
        
        需求：10.4
        """
        # 显示组件
        self.show()
        
        # 创建滑入动画（从右侧滑入）
        start_pos = self.pos() + QPoint(100, 0)  # 从右侧 100px 外开始
        end_pos = self.pos()
        
        self._slide_in_animation = QPropertyAnimation(self, b"pos")
        self._slide_in_animation.setDuration(300)  # 300ms 滑入
        self._slide_in_animation.setStartValue(start_pos)
        self._slide_in_animation.setEndValue(end_pos)
        self._slide_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._slide_in_animation.finished.connect(self._on_show_complete)
        
        # 同时创建淡入动画
        self.setWindowOpacity(0.0)
        fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        fade_in_animation.setDuration(300)
        fade_in_animation.setStartValue(0.0)
        fade_in_animation.setEndValue(1.0)
        fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 启动动画
        self._slide_in_animation.start()
        fade_in_animation.start()
        
        logger.debug(f"显示玻璃 Toast 通知: {self.message}")
    
    def _on_show_complete(self):
        """显示完成回调"""
        # 如果设置了自动消失时长，启动定时器
        if self.duration > 0:
            self._auto_dismiss_timer = QTimer(self)
            self._auto_dismiss_timer.setSingleShot(True)
            self._auto_dismiss_timer.timeout.connect(self.hide_toast)
            self._auto_dismiss_timer.start(self.duration)
    
    def hide_toast(self):
        """
        隐藏通知（带滑出和淡出动画）
        
        需求：10.4
        """
        # 停止自动消失定时器
        if self._auto_dismiss_timer:
            self._auto_dismiss_timer.stop()
            self._auto_dismiss_timer = None
        
        # 创建滑出动画（向右滑出）
        start_pos = self.pos()
        end_pos = self.pos() + QPoint(100, 0)  # 向右滑出 100px
        
        self._slide_out_animation = QPropertyAnimation(self, b"pos")
        self._slide_out_animation.setDuration(200)  # 200ms 滑出
        self._slide_out_animation.setStartValue(start_pos)
        self._slide_out_animation.setEndValue(end_pos)
        self._slide_out_animation.setEasingCurve(QEasingCurve.InCubic)
        self._slide_out_animation.finished.connect(self._on_hide_complete)
        
        # 同时创建淡出动画
        self._fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out_animation.setDuration(200)
        self._fade_out_animation.setStartValue(1.0)
        self._fade_out_animation.setEndValue(0.0)
        self._fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
        
        # 启动动画
        self._slide_out_animation.start()
        self._fade_out_animation.start()
        
        logger.debug(f"隐藏玻璃 Toast 通知: {self.message}")
    
    def _on_hide_complete(self):
        """隐藏完成回调"""
        self.close()
        self.closed.emit()
        self.deleteLater()
    
    def _setup_accessibility(self):
        """设置辅助功能支持"""
        # 为 Toast 设置 ARIA 标签和角色
        self._accessibility_manager.setup_alert_accessibility(
            self,
            message=self.message,
            alert_type=self.toast_type
        )
        
        # 向屏幕阅读器宣布消息
        self._accessibility_manager.announce(self, self.message)
        
        logger.debug(f"Toast 辅助功能已设置: {self.toast_type}")


class GlassToastManager(QObject):
    """
    玻璃 Toast 管理器
    
    管理玻璃 Toast 通知的显示和队列
    
    特性：
    - 限制同时显示的通知数量（最多 3 个）
    - 队列管理（超过限制的通知进入队列）
    - 自动定位（屏幕右上角）
    - 堆叠显示
    
    需求：10.7
    """
    
    MAX_TOASTS = 3  # 最大同时显示数量
    TOAST_SPACING = 10  # 通知之间的间距
    MARGIN_TOP = 20  # 顶部边距
    MARGIN_RIGHT = 20  # 右侧边距
    
    def __init__(self, parent: QWidget, glass_manager: Optional[LiquidGlassManager] = None):
        """
        初始化玻璃 Toast 管理器
        
        Args:
            parent: 父组件（通常是主窗口）
            glass_manager: 液态玻璃管理器实例
        """
        super().__init__(parent)
        self.parent_widget = parent
        self._glass_manager = glass_manager
        self.active_toasts: List[GlassToast] = []  # 活动通知列表
        self.toast_queue: List[tuple] = []  # 通知队列
        
        logger.debug("GlassToastManager 初始化完成")
    
    def show(
        self,
        message: str,
        toast_type: str = GlassToast.TYPE_INFO,
        duration: int = 3000
    ):
        """
        显示玻璃 Toast 通知
        
        Args:
            message: 通知消息
            toast_type: 通知类型 (success, info, warning, error)
            duration: 显示时长（毫秒），0 表示不自动消失
        """
        # 检查是否达到最大显示数量
        if len(self.active_toasts) >= self.MAX_TOASTS:
            # 加入队列
            self.toast_queue.append((message, toast_type, duration))
            logger.debug(f"玻璃 Toast 加入队列: {message}, 队列长度={len(self.toast_queue)}")
            return
        
        # 创建并显示通知
        self._create_and_show_toast(message, toast_type, duration)
    
    def _create_and_show_toast(self, message: str, toast_type: str, duration: int):
        """
        创建并显示玻璃 Toast 通知
        
        Args:
            message: 通知消息
            toast_type: 通知类型
            duration: 显示时长
        """
        # 创建通知
        toast = GlassToast(
            message,
            toast_type,
            duration,
            self.parent_widget,
            self._glass_manager
        )
        
        # 连接关闭信号
        toast.closed.connect(lambda: self._on_toast_closed(toast))
        
        # 添加到活动列表
        self.active_toasts.append(toast)
        
        # 计算位置
        self._position_toast(toast)
        
        # 显示通知
        toast.show_toast()
        
        logger.info(f"显示玻璃 Toast: 类型={toast_type}, 消息={message}")
    
    def _position_toast(self, toast: GlassToast):
        """
        定位玻璃 Toast 通知（屏幕右上角，堆叠显示）
        
        Args:
            toast: Toast 通知组件
            
        需求：10.7
        """
        # 获取父组件的全局位置和大小
        parent_rect = self.parent_widget.geometry()
        parent_global_pos = self.parent_widget.mapToGlobal(QPoint(0, 0))
        
        # 计算 x 位置（右对齐）
        x = parent_global_pos.x() + parent_rect.width() - toast.width() - self.MARGIN_RIGHT
        
        # 计算 y 位置（从上到下排列）
        y = parent_global_pos.y() + self.MARGIN_TOP
        
        # 如果有其他活动通知，需要向下偏移（堆叠显示）
        toast_index = self.active_toasts.index(toast)
        for i in range(toast_index):
            if i < len(self.active_toasts):
                y += self.active_toasts[i].height() + self.TOAST_SPACING
        
        # 设置位置
        toast.move(x, y)
        
        logger.debug(f"玻璃 Toast 定位: x={x}, y={y}, 索引={toast_index}")
    
    def _on_toast_closed(self, toast: GlassToast):
        """
        Toast 关闭回调
        
        Args:
            toast: 关闭的 Toast 通知
        """
        # 从活动列表移除
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
        
        # 重新定位剩余的通知（带动画）
        self._reposition_toasts_animated()
        
        # 处理队列中的通知
        self._process_queue()
        
        logger.debug(f"玻璃 Toast 已关闭，剩余活动通知: {len(self.active_toasts)}")
    
    def _reposition_toasts_animated(self):
        """重新定位所有活动通知（带动画）"""
        for i, toast in enumerate(self.active_toasts):
            # 计算新位置
            parent_rect = self.parent_widget.geometry()
            parent_global_pos = self.parent_widget.mapToGlobal(QPoint(0, 0))
            
            x = parent_global_pos.x() + parent_rect.width() - toast.width() - self.MARGIN_RIGHT
            y = parent_global_pos.y() + self.MARGIN_TOP
            
            # 累加之前通知的高度
            for j in range(i):
                if j < len(self.active_toasts):
                    y += self.active_toasts[j].height() + self.TOAST_SPACING
            
            new_pos = QPoint(x, y)
            
            # 如果位置有变化，创建移动动画
            if toast.pos() != new_pos:
                animation = QPropertyAnimation(toast, b"pos")
                animation.setDuration(200)
                animation.setStartValue(toast.pos())
                animation.setEndValue(new_pos)
                animation.setEasingCurve(QEasingCurve.OutCubic)
                animation.start()
    
    def _process_queue(self):
        """处理队列中的通知"""
        if not self.toast_queue or len(self.active_toasts) >= self.MAX_TOASTS:
            return
        
        # 取出队列中的第一个通知
        message, toast_type, duration = self.toast_queue.pop(0)
        
        # 显示通知
        self._create_and_show_toast(message, toast_type, duration)
        
        logger.debug(f"从队列显示玻璃 Toast，剩余队列: {len(self.toast_queue)}")
    
    def show_success(self, message: str, duration: int = 3000):
        """
        显示成功通知
        
        Args:
            message: 通知消息
            duration: 显示时长（毫秒）
        """
        self.show(message, GlassToast.TYPE_SUCCESS, duration)
    
    def show_info(self, message: str, duration: int = 3000):
        """
        显示信息通知
        
        Args:
            message: 通知消息
            duration: 显示时长（毫秒）
        """
        self.show(message, GlassToast.TYPE_INFO, duration)
    
    def show_warning(self, message: str, duration: int = 4000):
        """
        显示警告通知
        
        Args:
            message: 通知消息
            duration: 显示时长（毫秒）
        """
        self.show(message, GlassToast.TYPE_WARNING, duration)
    
    def show_error(self, message: str, duration: int = 5000):
        """
        显示错误通知
        
        Args:
            message: 通知消息
            duration: 显示时长（毫秒）
        """
        self.show(message, GlassToast.TYPE_ERROR, duration)
    
    def clear_all(self):
        """清除所有通知"""
        # 关闭所有活动通知
        for toast in self.active_toasts[:]:  # 使用副本避免迭代时修改列表
            toast.hide_toast()
        
        # 清空队列
        self.toast_queue.clear()
        
        logger.info("已清除所有玻璃 Toast 通知")
    
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
_glass_toast_manager_instance: Optional[GlassToastManager] = None


def get_glass_toast_manager(
    parent: Optional[QWidget] = None,
    glass_manager: Optional[LiquidGlassManager] = None
) -> GlassToastManager:
    """
    获取玻璃 Toast 管理器单例
    
    Args:
        parent: 父组件（首次调用时必须提供）
        glass_manager: 液态玻璃管理器实例
        
    Returns:
        GlassToastManager 实例
    """
    global _glass_toast_manager_instance
    if _glass_toast_manager_instance is None:
        if parent is None:
            raise ValueError("首次调用 get_glass_toast_manager 必须提供 parent 参数")
        _glass_toast_manager_instance = GlassToastManager(parent, glass_manager)
    return _glass_toast_manager_instance
