# -*- coding: utf-8 -*-
"""
玻璃全屏预览对话框

用于全屏预览图片，带有模糊背景和缩放动画
需求：7.7
"""

from typing import Optional
from PyQt5.QtCore import (
    Qt, QSize, QRect, QPoint, QPropertyAnimation, 
    QEasingCurve, QParallelAnimationGroup, pyqtSignal
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QColor, QBrush, QPen, QFont,
    QKeySequence, QCursor
)
from PyQt5.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, 
    QHBoxLayout, QGraphicsBlurEffect, QGraphicsOpacityEffect,
    QApplication
)
import os

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class GlassFullscreenPreview(QDialog):
    """
    玻璃全屏预览对话框
    
    用于全屏预览图片，具有：
    - 模糊背景（需求 7.7）
    - 图片缩放动画（需求 7.7）
    - 键盘快捷键支持
    - 平滑的进入/退出动画
    
    需求：7.7
    """
    
    # 信号
    closed = pyqtSignal()  # 对话框关闭时发出
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 file_path: str = "",
                 pixmap: Optional[QPixmap] = None):
        """
        初始化全屏预览对话框
        
        Args:
            parent: 父组件
            file_path: 图片文件路径
            pixmap: 图片对象
        """
        super().__init__(parent)
        
        self.file_path = file_path
        self.pixmap = pixmap
        
        # 导入 i18n 管理器
        try:
            from core.i18n_manager import get_i18n_manager
        except ImportError:
            from ..core.i18n_manager import get_i18n_manager
        self.i18n = get_i18n_manager()
        
        # 动画
        self.fade_in_animation = None
        self.zoom_animation = None
        self.animation_group = None
        
        # 设置对话框属性
        self.setWindowTitle(self.i18n.t("fullscreen_preview.title"))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置为全屏
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # 初始化UI
        self._init_ui()
        
        # 如果有图片，显示图片
        if pixmap and not pixmap.isNull():
            self._display_image(pixmap)
        
        # 启动进入动画
        self._start_enter_animation()
    
    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建模糊背景层（需求 7.7）
        self.background_widget = QWidget(self)
        self.background_widget.setGeometry(self.rect())
        self.background_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 230);
            }
        """)
        
        # 应用模糊效果
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(20)
        self.background_widget.setGraphicsEffect(blur_effect)
        
        # 创建内容容器
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background: transparent;
            }
        """)
        
        # 创建底部控制栏
        control_widget = self._create_control_bar()
        
        # 添加到内容布局
        content_layout.addWidget(self.image_label, 1)
        content_layout.addWidget(control_widget, 0)
        
        # 添加到主布局
        self.main_layout.addWidget(content_widget)
        
        # 设置初始透明度为 0（用于淡入动画）
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0)
        content_widget.setGraphicsEffect(opacity_effect)
        self.content_opacity_effect = opacity_effect
    
    def _create_control_bar(self) -> QWidget:
        """创建底部控制栏"""
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)
        
        # 文件名标签
        self.filename_label = QLabel()
        if self.file_path:
            self.filename_label.setText(os.path.basename(self.file_path))
        else:
            self.filename_label.setText(self.i18n.t("fullscreen_preview.title"))
        
        self.filename_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                padding: 10px 15px;
                background-color: rgba(0, 0, 0, 150);
                border-radius: 8px;
            }
        """)
        self.filename_label.setAlignment(Qt.AlignCenter)
        
        # 图片信息标签
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 200);
                font-size: 12px;
                padding: 10px 15px;
                background-color: rgba(0, 0, 0, 100);
                border-radius: 8px;
            }
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        
        # 关闭按钮
        self.close_button = QPushButton("✕ 关闭 (ESC)")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 53, 69, 200);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(200, 35, 51, 255);
            }
            QPushButton:pressed {
                background-color: rgba(180, 25, 41, 255);
            }
        """)
        self.close_button.clicked.connect(self._start_exit_animation)
        self.close_button.setShortcut(QKeySequence("Esc"))
        
        # 添加到布局
        control_layout.addWidget(self.filename_label)
        control_layout.addWidget(self.info_label)
        control_layout.addStretch()
        control_layout.addWidget(self.close_button)
        
        return control_widget
    
    def _display_image(self, pixmap: QPixmap):
        """
        显示图片
        
        Args:
            pixmap: 图片对象
        """
        if pixmap and not pixmap.isNull():
            # 获取屏幕尺寸
            screen = QApplication.primaryScreen().geometry()
            max_width = screen.width() - 100
            max_height = screen.height() - 200
            
            # 缩放图片以适应屏幕（保持宽高比）
            scaled_pixmap = pixmap.scaled(
                max_width,
                max_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            self.pixmap = pixmap
            
            # 更新图片信息
            self._update_image_info(pixmap)
        else:
            self.image_label.setText(self.i18n.t("fullscreen_preview.cannot_load"))
            self.image_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 24px;
                    background: transparent;
                }
            """)
    
    def _update_image_info(self, pixmap: QPixmap):
        """
        更新图片信息
        
        Args:
            pixmap: 图片对象
        """
        info_parts = []
        
        # 分辨率
        resolution = f"{pixmap.width()} × {pixmap.height()}"
        info_parts.append(resolution)
        
        # 文件大小
        if self.file_path and os.path.exists(self.file_path):
            try:
                size_bytes = os.path.getsize(self.file_path)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                info_parts.append(size_str)
            except:
                pass
        
        self.info_label.setText(" · ".join(info_parts))
    
    def _start_enter_animation(self):
        """启动进入动画（淡入 + 缩放）- 需求 7.7"""
        # 创建淡入动画
        self.fade_in_animation = QPropertyAnimation(self.content_opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 创建缩放动画（需求 7.7：图片缩放动画）
        # 注意：QLabel 不直接支持缩放属性，我们使用几何变换
        if self.image_label.pixmap():
            # 获取最终尺寸
            final_size = self.image_label.pixmap().size()
            
            # 设置初始尺寸（稍小）
            initial_width = int(final_size.width() * 0.9)
            initial_height = int(final_size.height() * 0.9)
            
            # 创建临时的缩放图片
            initial_pixmap = self.pixmap.scaled(
                initial_width,
                initial_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(initial_pixmap)
            
            # 使用定时器逐步放大
            from PyQt5.QtCore import QTimer
            self.zoom_steps = 0
            self.zoom_timer = QTimer()
            self.zoom_timer.timeout.connect(self._animate_zoom)
            self.zoom_timer.start(20)  # 每 20ms 更新一次
        
        # 启动淡入动画
        self.fade_in_animation.start()
    
    def _animate_zoom(self):
        """执行缩放动画步骤"""
        self.zoom_steps += 1
        total_steps = 15  # 总步数（300ms / 20ms）
        
        if self.zoom_steps >= total_steps:
            # 动画完成，显示最终图片
            self.zoom_timer.stop()
            screen = QApplication.primaryScreen().geometry()
            max_width = screen.width() - 100
            max_height = screen.height() - 200
            
            final_pixmap = self.pixmap.scaled(
                max_width,
                max_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(final_pixmap)
        else:
            # 计算当前缩放比例（从 0.9 到 1.0）
            progress = self.zoom_steps / total_steps
            # 使用缓动函数
            eased_progress = self._ease_out_cubic(progress)
            scale = 0.9 + (0.1 * eased_progress)
            
            # 缩放图片
            screen = QApplication.primaryScreen().geometry()
            max_width = int((screen.width() - 100) * scale)
            max_height = int((screen.height() - 200) * scale)
            
            scaled_pixmap = self.pixmap.scaled(
                max_width,
                max_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
    
    def _ease_out_cubic(self, t: float) -> float:
        """
        缓动函数：ease-out-cubic
        
        Args:
            t: 进度（0-1）
            
        Returns:
            缓动后的进度
        """
        return 1 - pow(1 - t, 3)
    
    def _start_exit_animation(self):
        """启动退出动画（淡出）"""
        # 创建淡出动画
        fade_out_animation = QPropertyAnimation(self.content_opacity_effect, b"opacity")
        fade_out_animation.setDuration(200)
        fade_out_animation.setStartValue(1.0)
        fade_out_animation.setEndValue(0.0)
        fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
        
        # 动画完成后关闭对话框
        fade_out_animation.finished.connect(self.accept)
        
        fade_out_animation.start()
        
        # 保存动画引用，防止被垃圾回收
        self.exit_animation = fade_out_animation
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 点击背景关闭"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在图片外部
            if not self.image_label.geometry().contains(event.pos()):
                self._start_exit_animation()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == Qt.Key_Escape:
            self._start_exit_animation()
        elif event.key() == Qt.Key_Space:
            self._start_exit_animation()
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.closed.emit()
        super().closeEvent(event)
    
    @staticmethod
    def show_preview(parent: Optional[QWidget], file_path: str, pixmap: Optional[QPixmap] = None):
        """
        静态方法：显示全屏预览
        
        Args:
            parent: 父组件
            file_path: 图片文件路径
            pixmap: 图片对象（可选，如果不提供则从文件加载）
        """
        # 如果没有提供 pixmap，从文件加载
        if not pixmap and file_path and os.path.exists(file_path):
            pixmap = QPixmap(file_path)
        
        if pixmap and not pixmap.isNull():
            dialog = GlassFullscreenPreview(parent, file_path, pixmap)
            dialog.exec_()
        else:
            logger.error(f"无法加载图片: {file_path}")
