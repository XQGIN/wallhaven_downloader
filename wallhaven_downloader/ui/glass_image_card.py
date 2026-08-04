# -*- coding: utf-8 -*-
"""
玻璃图片卡片组件

用于预览画廊的图片卡片，采用液态玻璃效果设计
需求：7.1-7.3
"""

from typing import Optional
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QLinearGradient, 
    QBrush, QPen, QFont
)
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout

try:
    from ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from ui.liquid_glass.glass_panel_factory import GlassPanelFactory
    from core.enhanced_theme_manager import EnhancedThemeManager
except ImportError:
    from .liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from .liquid_glass.glass_panel_factory import GlassPanelFactory
    from ..core.enhanced_theme_manager import EnhancedThemeManager

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class GlassImageCard(QWidget):
    """
    玻璃图片卡片组件
    
    用于预览画廊的图片卡片，具有：
    - 玻璃面板效果
    - 圆角设计（12-16px）
    - 悬停上浮效果
    - 半透明信息栏
    - 骨架屏加载动画
    
    需求：7.1-7.6
    """
    
    # 信号
    clicked = pyqtSignal(str)  # 点击卡片时发出，携带文件路径
    double_clicked = pyqtSignal(str)  # 双击卡片时发出，携带文件路径
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 file_path: str = "",
                 pixmap: Optional[QPixmap] = None,
                 image_info: Optional[dict] = None):
        """
        初始化玻璃图片卡片
        
        Args:
            parent: 父组件
            file_path: 图片文件路径
            pixmap: 图片对象
            image_info: 图片信息（分辨率、大小等）
        """
        super().__init__(parent)
        
        self.file_path = file_path
        self.pixmap = pixmap
        self.image_info = image_info or {}
        
        # 状态
        self.is_hovered = False
        self.is_loading = True  # 初始为加载状态
        self.load_failed = False
        
        # 动画
        self.hover_animation = None
        self.shadow_animation = None
        
        # 玻璃面板工厂
        self.glass_factory = GlassPanelFactory()
        
        # 主题管理器
        try:
            self.theme_manager = EnhancedThemeManager()
        except:
            self.theme_manager = None
        
        # 导入 i18n 管理器
        try:
            from core.i18n_manager import get_i18n_manager
        except ImportError:
            from ..core.i18n_manager import get_i18n_manager
        self.i18n = get_i18n_manager()
        
        # 设置固定大小（需求 7.3：圆角设计）
        self.setFixedSize(220, 280)  # 卡片大小：200x200 图片 + 边距和信息栏
        
        # 启用鼠标追踪
        self.setMouseTracking(True)
        
        # 初始化UI
        self._init_ui()
        
        # 如果有图片，设置图片
        if pixmap and not pixmap.isNull():
            self.set_image(pixmap)
    
    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)
        
        # 创建图片容器（玻璃面板）
        self.image_container = QLabel(self)
        self.image_container.setFixedSize(200, 200)
        self.image_container.setAlignment(Qt.AlignCenter)
        self.image_container.setStyleSheet("""
            QLabel {
                background-color: rgba(240, 240, 240, 100);
                border-radius: 12px;
            }
        """)
        
        # 创建信息栏（半透明）- 需求 7.5
        self.info_bar = QWidget(self)
        self.info_bar.setFixedHeight(60)
        info_layout = QVBoxLayout(self.info_bar)
        info_layout.setContentsMargins(8, 5, 8, 5)
        info_layout.setSpacing(2)
        
        # 文件名标签
        self.filename_label = QLabel(self.i18n.t("image_card.loading"))
        self.filename_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.filename_label.setWordWrap(True)
        self.filename_label.setStyleSheet("""
            QLabel {
                color: rgba(29, 29, 31, 255);
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 信息标签（分辨率、大小）
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: rgba(134, 134, 139, 255);
                font-size: 10px;
                background: transparent;
            }
        """)
        
        info_layout.addWidget(self.filename_label)
        info_layout.addWidget(self.info_label)
        
        # 设置信息栏样式（半透明玻璃效果）
        self.info_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 180);
                border-radius: 0px 0px 12px 12px;
            }
        """)
        
        # 添加到主布局
        self.main_layout.addWidget(self.image_container)
        self.main_layout.addWidget(self.info_bar)
        
        # 显示骨架屏加载动画（需求 7.6）
        if self.is_loading:
            self._show_skeleton_loading()
    
    def _show_skeleton_loading(self):
        """显示骨架屏加载动画（需求 7.6）"""
        # 创建骨架屏图片
        skeleton_pixmap = QPixmap(200, 200)
        skeleton_pixmap.fill(Qt.transparent)
        
        painter = QPainter(skeleton_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制骨架屏背景
        path = QPainterPath()
        path.addRoundedRect(0, 0, 200, 200, 12, 12)
        
        # 创建渐变效果（模拟加载动画）
        gradient = QLinearGradient(0, 0, 200, 0)
        gradient.setColorAt(0.0, QColor(240, 240, 240))
        gradient.setColorAt(0.5, QColor(250, 250, 250))
        gradient.setColorAt(1.0, QColor(240, 240, 240))
        
        painter.fillPath(path, QBrush(gradient))
        
        # 绘制加载图标
        painter.setPen(QColor(180, 180, 180))
        font = QFont()
        font.setPointSize(24)
        painter.setFont(font)
        painter.drawText(QRect(0, 0, 200, 200), Qt.AlignCenter, "⏳")
        
        painter.end()
        
        self.image_container.setPixmap(skeleton_pixmap)
    
    def set_image(self, pixmap: QPixmap):
        """
        设置图片
        
        Args:
            pixmap: 图片对象
        """
        if pixmap and not pixmap.isNull():
            # 缩放图片以适应容器（保持宽高比）
            scaled_pixmap = pixmap.scaled(
                200, 200,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # 创建圆角图片（需求 7.3：12-16px 圆角）
            rounded_pixmap = self._create_rounded_pixmap(scaled_pixmap, 12)
            
            self.image_container.setPixmap(rounded_pixmap)
            self.pixmap = pixmap
            self.is_loading = False
            self.load_failed = False
            
            # 更新信息栏
            self._update_info_bar()
        else:
            self._show_error_state()
    
    def _create_rounded_pixmap(self, pixmap: QPixmap, radius: int) -> QPixmap:
        """
        创建圆角图片
        
        Args:
            pixmap: 原始图片
            radius: 圆角半径
            
        Returns:
            圆角图片
        """
        # 创建透明背景
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.transparent)
        
        # 绘制圆角图片
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
        
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        return rounded
    
    def _show_error_state(self):
        """显示错误状态"""
        error_pixmap = QPixmap(200, 200)
        error_pixmap.fill(Qt.transparent)
        
        painter = QPainter(error_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制错误背景
        path = QPainterPath()
        path.addRoundedRect(0, 0, 200, 200, 12, 12)
        painter.fillPath(path, QBrush(QColor(255, 240, 240)))
        
        # 绘制错误图标
        painter.setPen(QColor(220, 53, 69))
        font = QFont()
        font.setPointSize(24)
        painter.setFont(font)
        painter.drawText(QRect(0, 0, 200, 200), Qt.AlignCenter, "❌\n加载失败")
        
        painter.end()
        
        self.image_container.setPixmap(error_pixmap)
        self.is_loading = False
        self.load_failed = True
        
        self.filename_label.setText(self.i18n.t("image_card.load_failed"))
        self.info_label.setText(self.i18n.t("image_card.click_retry"))
    
    def _update_info_bar(self):
        """更新信息栏"""
        import os
        
        # 更新文件名
        if self.file_path:
            filename = os.path.basename(self.file_path)
            # 限制文件名长度
            if len(filename) > 25:
                filename = filename[:22] + "..."
            self.filename_label.setText(filename)
        
        # 更新图片信息
        info_parts = []
        
        # 分辨率
        if self.pixmap and not self.pixmap.isNull():
            resolution = f"{self.pixmap.width()}x{self.pixmap.height()}"
            info_parts.append(resolution)
        elif "resolution" in self.image_info:
            info_parts.append(self.image_info["resolution"])
        
        # 文件大小
        if "size" in self.image_info:
            info_parts.append(self.image_info["size"])
        elif self.file_path:
            try:
                import os
                size_bytes = os.path.getsize(self.file_path)
                if size_bytes < 1024:
                    size_str = f"{size_bytes}B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f}KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f}MB"
                info_parts.append(size_str)
            except:
                pass
        
        self.info_label.setText(" · ".join(info_parts))
    
    def paintEvent(self, event):
        """绘制卡片（玻璃效果和阴影）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取卡片矩形
        rect = self.rect().adjusted(5, 5, -5, -5)
        
        # 绘制阴影（需求 7.4：悬停时阴影加深）
        shadow_blur = 15 if not self.is_hovered else 25
        shadow_offset = 3 if not self.is_hovered else 5
        
        for i in range(shadow_blur):
            alpha = int(30 * (1 - i / shadow_blur))
            if self.is_hovered:
                alpha = int(50 * (1 - i / shadow_blur))
            
            color = QColor(0, 0, 0, alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            
            shadow_rect = rect.adjusted(
                shadow_offset + i, shadow_offset + i,
                shadow_offset + i, shadow_offset + i
            )
            painter.drawRoundedRect(shadow_rect, 14, 14)
        
        # 绘制玻璃背景（需求 7.1-7.2）
        from PyQt5.QtCore import QRectF
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 12, 12)
        
        # 半透明白色背景
        if self.theme_manager and self.theme_manager.is_dark_mode():
            bg_color = QColor(44, 44, 46, 180)
        else:
            bg_color = QColor(255, 255, 255, 200)
        
        painter.fillPath(path, QBrush(bg_color))
        
        # 绘制边框
        border_color = QColor(216, 216, 220, 150)
        if self.is_hovered:
            border_color = QColor(0, 122, 255, 200)
        
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, 12, 12)
        
        painter.end()
        
        super().paintEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件 - 悬停上浮效果（需求 7.4）"""
        self.is_hovered = True
        self.update()
        
        # 创建悬停动画（轻微上移）
        if not self.hover_animation:
            self.hover_animation = QPropertyAnimation(self, b"pos")
            self.hover_animation.setDuration(200)
            self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 向上移动 5 像素
        current_pos = self.pos()
        self.hover_animation.setStartValue(current_pos)
        self.hover_animation.setEndValue(QPoint(current_pos.x(), current_pos.y() - 5))
        self.hover_animation.start()
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 恢复正常"""
        self.is_hovered = False
        self.update()
        
        # 恢复原位置
        if self.hover_animation:
            current_pos = self.pos()
            self.hover_animation.setStartValue(current_pos)
            self.hover_animation.setEndValue(QPoint(current_pos.x(), current_pos.y() + 5))
            self.hover_animation.start()
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 发出点击信号
            self.clicked.emit(self.file_path)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.LeftButton:
            # 发出双击信号
            self.double_clicked.emit(self.file_path)
        super().mouseDoubleClickEvent(event)
    
    def set_loading(self, loading: bool):
        """
        设置加载状态
        
        Args:
            loading: 是否加载中
        """
        self.is_loading = loading
        if loading:
            self._show_skeleton_loading()
    
    def set_error(self):
        """设置错误状态"""
        self._show_error_state()
    
    def get_file_path(self) -> str:
        """获取文件路径"""
        return self.file_path
    
    def get_pixmap(self) -> Optional[QPixmap]:
        """获取图片对象"""
        return self.pixmap
