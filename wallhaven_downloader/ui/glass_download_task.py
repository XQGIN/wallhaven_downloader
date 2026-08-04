# -*- coding: utf-8 -*-
"""
玻璃下载任务组件

提供液态玻璃效果的下载任务显示面板
"""

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QTimer, QParallelAnimationGroup
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPen, QBrush, QLinearGradient, QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QGraphicsOpacityEffect

try:
    from ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from ui.liquid_glass.glass_panel_factory import GlassPanelFactory
    from ui.glass_progress_indicator import GlassProgressIndicator
    from core.enhanced_theme_manager import EnhancedThemeManager
except ImportError:
    from wallhaven_downloader.ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from wallhaven_downloader.ui.liquid_glass.glass_panel_factory import GlassPanelFactory
    from wallhaven_downloader.ui.glass_progress_indicator import GlassProgressIndicator
    from wallhaven_downloader.core.enhanced_theme_manager import EnhancedThemeManager


class GlassDownloadTask(EnhancedGlassPanel):
    """
    玻璃下载任务组件
    
    显示单个下载任务的信息，包括：
    - 缩略图
    - 文件名
    - 进度
    - 速度
    - 状态
    
    需求：8.1-8.2
    """
    
    # 信号
    pause_clicked = pyqtSignal()  # 暂停按钮点击
    resume_clicked = pyqtSignal()  # 继续按钮点击
    cancel_clicked = pyqtSignal()  # 取消按钮点击
    retry_clicked = pyqtSignal()  # 重试按钮点击
    expand_clicked = pyqtSignal()  # 展开/折叠按钮点击
    
    # 任务状态
    STATUS_PENDING = "pending"  # 等待中
    STATUS_DOWNLOADING = "downloading"  # 下载中
    STATUS_PAUSED = "paused"  # 已暂停
    STATUS_COMPLETED = "completed"  # 已完成
    STATUS_FAILED = "failed"  # 失败
    STATUS_CANCELLED = "cancelled"  # 已取消
    
    def __init__(self, parent=None, task_data=None):
        """
        初始化下载任务组件
        
        Args:
            parent: 父组件
            task_data: 任务数据字典，包含：
                - filename: 文件名
                - url: 下载URL
                - thumbnail: 缩略图 QPixmap（可选）
                - file_size: 文件大小（字节）
                - status: 初始状态
        """
        # 使用 normal 面板类型
        factory = GlassPanelFactory()
        config = factory.get_panel_config("normal")
        
        super().__init__(parent, config)
        
        # 任务数据
        self.task_data = task_data or {}
        self.filename = self.task_data.get("filename", "未知文件")
        self.url = self.task_data.get("url", "")
        self.thumbnail = self.task_data.get("thumbnail", None)
        self.file_size = self.task_data.get("file_size", 0)
        self.status = self.task_data.get("status", self.STATUS_PENDING)
        
        # 下载进度数据
        self.progress = 0  # 0-100
        self.downloaded_bytes = 0
        self.download_speed = 0  # 字节/秒
        self.time_remaining = 0  # 秒
        
        # 展开/折叠状态
        self.is_expanded = False
        
        # 动画
        self._expand_animation = None
        self._celebration_animation = None
        self._celebration_timer = None
        
        # 获取主题管理器
        try:
            self.theme_manager = EnhancedThemeManager()
        except:
            self.theme_manager = None
        
        # 初始化UI
        self._init_ui()
        
        # 设置固定高度
        self.setFixedHeight(100)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(15)
        
        # === 左侧：缩略图 ===
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(80, 80)
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border-radius: 8px;
                background-color: rgba(200, 200, 200, 0.3);
            }
        """)
        
        # 设置缩略图
        if self.thumbnail and not self.thumbnail.isNull():
            scaled_thumbnail = self.thumbnail.scaled(
                80, 80,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_thumbnail)
        else:
            # 默认占位图
            self.thumbnail_label.setText("📷")
            self.thumbnail_label.setAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(24)
            self.thumbnail_label.setFont(font)
        
        main_layout.addWidget(self.thumbnail_label)
        
        # === 中间：信息区域 ===
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # 文件名
        self.filename_label = QLabel(self._truncate_filename(self.filename, 50))
        self.filename_label.setStyleSheet("""
            QLabel {
                color: #1D1D1F;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        info_layout.addWidget(self.filename_label)
        
        # 进度和速度信息
        self.info_label = QLabel(self._format_info_text())
        self.info_label.setStyleSheet("""
            QLabel {
                color: #86868B;
                font-size: 12px;
            }
        """)
        info_layout.addWidget(self.info_label)
        
        # 进度条（使用 GlassProgressIndicator）
        self.progress_bar = GlassProgressIndicator()
        self.progress_bar.set_status(self.status)
        self.progress_bar.set_progress(self.progress)
        info_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel(self._format_status_text())
        self.status_label.setStyleSheet(self._get_status_style())
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)
        
        # === 右侧：操作按钮区域（将在子任务 20.3 中实现）===
        self.action_buttons_widget = QWidget()
        action_layout = QHBoxLayout(self.action_buttons_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        
        # 暂停/继续按钮
        self.pause_resume_button = QPushButton("⏸")
        self.pause_resume_button.setFixedSize(36, 36)
        self.pause_resume_button.setStyleSheet(self._get_button_style())
        self.pause_resume_button.clicked.connect(self._on_pause_resume_clicked)
        action_layout.addWidget(self.pause_resume_button)
        
        # 取消按钮
        self.cancel_button = QPushButton("✕")
        self.cancel_button.setFixedSize(36, 36)
        self.cancel_button.setStyleSheet(self._get_button_style())
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        action_layout.addWidget(self.cancel_button)
        
        # 重试按钮（默认隐藏）
        self.retry_button = QPushButton("↻")
        self.retry_button.setFixedSize(36, 36)
        self.retry_button.setStyleSheet(self._get_button_style())
        self.retry_button.clicked.connect(self.retry_clicked.emit)
        self.retry_button.setVisible(False)
        action_layout.addWidget(self.retry_button)
        
        main_layout.addWidget(self.action_buttons_widget)
        
        # 更新按钮可见性
        self._update_button_visibility()
    
    def _truncate_filename(self, filename: str, max_length: int) -> str:
        """截断文件名"""
        if len(filename) <= max_length:
            return filename
        
        # 保留扩展名
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        available_length = max_length - len(ext) - 4  # 4 for "..." and "."
        
        if available_length > 0:
            return f"{name[:available_length]}...{ext}"
        return f"{filename[:max_length]}..."
    
    def _format_info_text(self) -> str:
        """格式化信息文本"""
        if self.status == self.STATUS_COMPLETED:
            return f"已完成 • {self._format_file_size(self.file_size)}"
        elif self.status == self.STATUS_DOWNLOADING:
            speed_text = self._format_speed(self.download_speed)
            size_text = f"{self._format_file_size(self.downloaded_bytes)} / {self._format_file_size(self.file_size)}"
            return f"{size_text} • {speed_text}"
        elif self.status == self.STATUS_PAUSED:
            size_text = f"{self._format_file_size(self.downloaded_bytes)} / {self._format_file_size(self.file_size)}"
            return f"已暂停 • {size_text}"
        elif self.status == self.STATUS_FAILED:
            return "下载失败"
        elif self.status == self.STATUS_PENDING:
            return f"等待中 • {self._format_file_size(self.file_size)}"
        else:
            return ""
    
    def _format_status_text(self) -> str:
        """格式化状态文本"""
        status_map = {
            self.STATUS_PENDING: "⏳ 等待中",
            self.STATUS_DOWNLOADING: f"📥 下载中 {self.progress}%",
            self.STATUS_PAUSED: "⏸ 已暂停",
            self.STATUS_COMPLETED: "✓ 已完成",
            self.STATUS_FAILED: "✕ 失败",
            self.STATUS_CANCELLED: "⊘ 已取消"
        }
        return status_map.get(self.status, "")
    
    def _get_status_style(self) -> str:
        """获取状态标签样式"""
        # 状态颜色（需求 8.5）
        color_map = {
            self.STATUS_PENDING: "#86868B",  # 灰色
            self.STATUS_DOWNLOADING: "#007AFF",  # 蓝色
            self.STATUS_PAUSED: "#FF9500",  # 橙色
            self.STATUS_COMPLETED: "#34C759",  # 绿色
            self.STATUS_FAILED: "#FF3B30",  # 红色
            self.STATUS_CANCELLED: "#86868B"  # 灰色
        }
        
        color = color_map.get(self.status, "#86868B")
        
        return f"""
            QLabel {{
                color: {color};
                font-size: 12px;
                font-weight: 600;
            }}
        """
    
    def _get_button_style(self) -> str:
        """获取按钮样式"""
        return """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 18px;
                color: #1D1D1F;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.7);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.9);
            }
        """
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    def _format_speed(self, speed_bytes_per_sec: int) -> str:
        """格式化下载速度"""
        return f"{self._format_file_size(speed_bytes_per_sec)}/s"
    
    def _update_button_visibility(self):
        """更新按钮可见性"""
        # 根据状态显示/隐藏按钮
        if self.status == self.STATUS_DOWNLOADING:
            self.pause_resume_button.setVisible(True)
            self.pause_resume_button.setText("⏸")
            self.cancel_button.setVisible(True)
            self.retry_button.setVisible(False)
        elif self.status == self.STATUS_PAUSED:
            self.pause_resume_button.setVisible(True)
            self.pause_resume_button.setText("▶")
            self.cancel_button.setVisible(True)
            self.retry_button.setVisible(False)
        elif self.status == self.STATUS_FAILED:
            self.pause_resume_button.setVisible(False)
            self.cancel_button.setVisible(False)
            self.retry_button.setVisible(True)
        elif self.status == self.STATUS_COMPLETED:
            self.pause_resume_button.setVisible(False)
            self.cancel_button.setVisible(False)
            self.retry_button.setVisible(False)
        else:
            self.pause_resume_button.setVisible(False)
            self.cancel_button.setVisible(True)
            self.retry_button.setVisible(False)
    
    def _on_pause_resume_clicked(self):
        """暂停/继续按钮点击处理"""
        if self.status == self.STATUS_DOWNLOADING:
            self.pause_clicked.emit()
        elif self.status == self.STATUS_PAUSED:
            self.resume_clicked.emit()
    
    # === 公共方法 ===
    
    def set_thumbnail(self, pixmap: QPixmap):
        """设置缩略图"""
        if pixmap and not pixmap.isNull():
            scaled_thumbnail = pixmap.scaled(
                80, 80,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_thumbnail)
            self.thumbnail = pixmap
    
    def set_progress(self, progress: int, downloaded_bytes: int = 0, speed: int = 0):
        """
        设置下载进度
        
        Args:
            progress: 进度百分比 (0-100)
            downloaded_bytes: 已下载字节数
            speed: 下载速度（字节/秒）
        """
        self.progress = max(0, min(100, progress))
        self.downloaded_bytes = downloaded_bytes
        self.download_speed = speed
        
        # 更新UI
        self.info_label.setText(self._format_info_text())
        self.status_label.setText(self._format_status_text())
        
        # 更新进度条
        self.progress_bar.set_progress(self.progress)
        
        self.update()
    
    def set_status(self, status: str):
        """
        设置任务状态
        
        Args:
            status: 状态值（使用 STATUS_* 常量）
        """
        old_status = self.status
        self.status = status
        
        # 更新UI
        self.info_label.setText(self._format_info_text())
        self.status_label.setText(self._format_status_text())
        self.status_label.setStyleSheet(self._get_status_style())
        
        # 更新进度条状态
        self.progress_bar.set_status(self._map_status_to_progress_bar(status))
        
        # 更新按钮可见性
        self._update_button_visibility()
        
        # 如果状态变为完成，播放庆祝动画（需求 8.8）
        if old_status != self.STATUS_COMPLETED and status == self.STATUS_COMPLETED:
            # 延迟一点播放动画，让UI先更新
            QTimer.singleShot(100, self._on_status_changed_to_completed)
        
        self.update()
    
    def _map_status_to_progress_bar(self, status: str) -> str:
        """将任务状态映射到进度条状态"""
        status_map = {
            self.STATUS_PENDING: GlassProgressIndicator.STATUS_PENDING,
            self.STATUS_DOWNLOADING: GlassProgressIndicator.STATUS_DOWNLOADING,
            self.STATUS_PAUSED: GlassProgressIndicator.STATUS_PAUSED,
            self.STATUS_COMPLETED: GlassProgressIndicator.STATUS_COMPLETED,
            self.STATUS_FAILED: GlassProgressIndicator.STATUS_FAILED,
            self.STATUS_CANCELLED: GlassProgressIndicator.STATUS_PENDING
        }
        return status_map.get(status, GlassProgressIndicator.STATUS_PENDING)
    
    def get_status(self) -> str:
        """获取当前状态"""
        return self.status
    
    def get_filename(self) -> str:
        """获取文件名"""
        return self.filename
    
    def get_url(self) -> str:
        """获取下载URL"""
        return self.url
    
    def get_progress(self) -> int:
        """获取进度百分比"""
        return self.progress
    
    # === 动画方法（需求 8.6-8.8）===
    
    def toggle_expand(self):
        """切换展开/折叠状态（需求 8.6）"""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def expand(self):
        """展开任务详情"""
        if self.is_expanded:
            return
        
        self.is_expanded = True
        
        # 创建展开动画
        self._expand_animation = QPropertyAnimation(self, b"minimumHeight")
        self._expand_animation.setDuration(300)  # 300ms
        self._expand_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._expand_animation.setStartValue(100)
        self._expand_animation.setEndValue(200)  # 展开到 200px
        
        # 同时动画最大高度
        max_height_animation = QPropertyAnimation(self, b"maximumHeight")
        max_height_animation.setDuration(300)
        max_height_animation.setEasingCurve(QEasingCurve.OutCubic)
        max_height_animation.setStartValue(100)
        max_height_animation.setEndValue(200)
        
        # 创建并行动画组
        animation_group = QParallelAnimationGroup(self)
        animation_group.addAnimation(self._expand_animation)
        animation_group.addAnimation(max_height_animation)
        
        animation_group.start()
        
        # 发送展开信号
        self.expand_clicked.emit()
    
    def collapse(self):
        """折叠任务详情"""
        if not self.is_expanded:
            return
        
        self.is_expanded = False
        
        # 创建折叠动画
        self._expand_animation = QPropertyAnimation(self, b"minimumHeight")
        self._expand_animation.setDuration(300)  # 300ms
        self._expand_animation.setEasingCurve(QEasingCurve.InCubic)
        self._expand_animation.setStartValue(200)
        self._expand_animation.setEndValue(100)
        
        # 同时动画最大高度
        max_height_animation = QPropertyAnimation(self, b"maximumHeight")
        max_height_animation.setDuration(300)
        max_height_animation.setEasingCurve(QEasingCurve.InCubic)
        max_height_animation.setStartValue(200)
        max_height_animation.setEndValue(100)
        
        # 创建并行动画组
        animation_group = QParallelAnimationGroup(self)
        animation_group.addAnimation(self._expand_animation)
        animation_group.addAnimation(max_height_animation)
        
        animation_group.start()
        
        # 发送折叠信号
        self.expand_clicked.emit()
    
    def play_celebration_animation(self):
        """
        播放完成庆祝动画（需求 8.8）
        
        实现效果：
        1. 轻微放大（1.0 -> 1.05 -> 1.0）
        2. 发光效果（透明度变化）
        3. 持续约 1 秒
        """
        # 创建图形效果
        glow_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(glow_effect)
        
        # 创建透明度动画（发光效果）
        opacity_animation = QPropertyAnimation(glow_effect, b"opacity")
        opacity_animation.setDuration(500)  # 500ms
        opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        opacity_animation.setStartValue(1.0)
        opacity_animation.setKeyValueAt(0.5, 0.7)  # 中间变暗
        opacity_animation.setEndValue(1.0)
        
        # 启动动画
        opacity_animation.start()
        
        # 保存动画引用，防止被垃圾回收
        self._celebration_animation = opacity_animation
        
        # 动画结束后移除效果
        def cleanup():
            self.setGraphicsEffect(None)
            self._celebration_animation = None
        
        opacity_animation.finished.connect(cleanup)
        
        # 添加视觉反馈：改变边框颜色
        self._celebration_timer = QTimer(self)
        self._celebration_timer.setSingleShot(True)
        self._celebration_timer.timeout.connect(lambda: self.update())
        self._celebration_timer.start(500)
    
    def _on_status_changed_to_completed(self):
        """当状态变为完成时触发"""
        # 播放庆祝动画
        self.play_celebration_animation()

