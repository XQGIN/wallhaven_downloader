# -*- coding: utf-8 -*-
"""
图片预览组件
支持分页显示、图片缩略图预览
"""

from typing import List, Dict, Optional
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, QEvent
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QIcon, QColor, QCursor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSpinBox, QAbstractItemView,
    QDialog, QMessageBox, QApplication, QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect, QMenu, QAction
)
import os

try:
    from core.theme_manager import get_theme_manager
except ImportError:
    from ..core.theme_manager import get_theme_manager

try:
    from core.i18n_manager import get_i18n_manager
except ImportError:
    from ..core.i18n_manager import get_i18n_manager

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

try:
    from ui.enhanced_glass_button import EnhancedGlassButton
except ImportError:
    from ..ui.enhanced_glass_button import EnhancedGlassButton

logger = get_logger(__name__)


class ImagePreviewWidget(QWidget):
    """图片预览部件 - 支持分页显示"""
    
    # 每页显示图片数量
    ITEMS_PER_PAGE: int = 100
    # 最大总图片数量限制
    MAX_TOTAL_ITEMS: int = 500
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化图片预览组件
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        
        # 获取国际化管理器
        self.i18n = get_i18n_manager()
        
        # 存储所有图片信息
        self.all_images: List[Dict[str, any]] = []
        self.current_page: int = 1
        
        # 悬停预览相关（需求 13.2）
        self.hover_preview_label: Optional[QLabel] = None
        
        # 懒加载相关（需求 13.3）
        self._lazy_load_enabled = True
        self._loaded_pages = set()  # 已加载的页面
        
        # 占位图和重试（需求 13.4）
        self._placeholder_pixmap: Optional[QPixmap] = None
        self._error_pixmap: Optional[QPixmap] = None
        
        self._init_ui()
        self._create_placeholder_images()
    
    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        
        # 创建顶部信息栏
        info_layout = QHBoxLayout()
        
        # 下载数量标签
        self.download_count_label = QLabel(self.i18n.t("preview.downloaded", count=0))
        self.download_count_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 10px 16px;
                margin: 5px;
                font-weight: bold;
                font-size: 16px;
                color: rgb(60, 60, 60);
            }
        """)
        self.download_count_label.setAlignment(Qt.AlignCenter)
        
        # 分页信息标签
        self.page_info_label = QLabel(self.i18n.t("preview.page_info", current=1, total=1))
        self.page_info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 10px 16px;
                margin: 5px;
                font-weight: bold;
                font-size: 16px;
                color: rgb(60, 60, 60);
            }
        """)
        self.page_info_label.setAlignment(Qt.AlignCenter)
        
        info_layout.addWidget(self.download_count_label)
        info_layout.addWidget(self.page_info_label)
        
        # 创建图片列表控件
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setMovement(QListWidget.Static)
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setUniformItemSizes(True)
        self.image_list.setWrapping(True)
        self.image_list.setSpacing(10)
        self.image_list.setIconSize(QSize(200, 200))
        self.image_list.setTextElideMode(Qt.ElideRight)
        self.image_list.setWordWrap(True)
        self.image_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.image_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 启用拖放排序（需求 13.5）
        self.image_list.setDragEnabled(True)
        self.image_list.setAcceptDrops(True)
        self.image_list.setDropIndicatorShown(True)
        self.image_list.setDragDropMode(QAbstractItemView.InternalMove)
        
        # 启用右键菜单（需求 13.2）
        self.image_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # 设置图片列表样式 - 现代化设计（需求 13.1）
        self.image_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 50);
                border: none;
                outline: none;
                border-radius: 10px;
            }
            QListWidget::item {
                background-color: rgba(255, 255, 255, 100);
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 10px;  /* 圆角 8-12px */
                padding: 8px;
                margin: 8px;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 122, 204, 150);
                border: 1px solid rgba(0, 122, 204, 200);
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 150);
                border: 1px solid rgba(150, 150, 150, 150);
            }
        """)
        
        # 连接双击事件
        self.image_list.itemDoubleClicked.connect(self.showFullImage)
        
        # 连接鼠标进入/离开事件（需求 13.2：悬停预览）
        self.image_list.itemEntered.connect(self._on_item_entered)
        self.image_list.viewport().installEventFilter(self)
        
        # 创建分页控制按钮
        page_control_layout = self._create_page_controls()
        
        # 添加所有组件到主布局
        self.main_layout.addLayout(info_layout)
        self.main_layout.addWidget(self.image_list)
        self.main_layout.addLayout(page_control_layout)
    
    def _create_page_controls(self) -> QHBoxLayout:
        """创建分页控制按钮 - 使用液态玻璃按钮"""
        page_control_layout = QHBoxLayout()
        page_control_layout.setSpacing(8)
        
        # 首页按钮 - 使用 EnhancedGlassButton
        self.first_page_btn = EnhancedGlassButton(f"⏮ {self.i18n.t('preview.first_page')}", EnhancedGlassButton.STYLE_SECONDARY)
        self.first_page_btn.clicked.connect(self.goToFirstPage)
        self.first_page_btn.setEnabled(False)
        self.first_page_btn.setMinimumSize(100, 44)
        
        # 上一页按钮
        self.prev_page_btn = EnhancedGlassButton(f"◀ {self.i18n.t('preview.prev_page')}", EnhancedGlassButton.STYLE_SECONDARY)
        self.prev_page_btn.clicked.connect(self.goToPrevPage)
        self.prev_page_btn.setEnabled(False)
        self.prev_page_btn.setMinimumSize(100, 44)
        
        # 页码跳转
        page_jump_layout = QHBoxLayout()
        page_jump_layout.setSpacing(8)
        page_jump_label = QLabel(self.i18n.t("preview.jump_to"))
        page_jump_label.setStyleSheet("""
            QLabel {
                color: rgb(60, 60, 60);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        self.page_jump_spin = QSpinBox()
        self.page_jump_spin.setMinimum(1)
        self.page_jump_spin.setMaximum(1)
        self.page_jump_spin.setValue(1)
        self._apply_glass_spinbox_style(self.page_jump_spin)
        
        page_jump_btn = EnhancedGlassButton(self.i18n.t("preview.jump"), EnhancedGlassButton.STYLE_PRIMARY)
        page_jump_btn.clicked.connect(self.jumpToPage)
        page_jump_btn.setMinimumSize(80, 44)
        
        page_jump_layout.addWidget(page_jump_label)
        page_jump_layout.addWidget(self.page_jump_spin)
        page_jump_layout.addWidget(page_jump_btn)
        
        # 下一页按钮
        self.next_page_btn = EnhancedGlassButton(f"{self.i18n.t('preview.next_page')} ▶", EnhancedGlassButton.STYLE_SECONDARY)
        self.next_page_btn.clicked.connect(self.goToNextPage)
        self.next_page_btn.setEnabled(False)
        self.next_page_btn.setMinimumSize(100, 44)
        
        # 末页按钮
        self.last_page_btn = EnhancedGlassButton(f"{self.i18n.t('preview.last_page')} ⏭", EnhancedGlassButton.STYLE_SECONDARY)
        self.last_page_btn.clicked.connect(self.goToLastPage)
        self.last_page_btn.setEnabled(False)
        self.last_page_btn.setMinimumSize(100, 44)
        
        page_control_layout.addWidget(self.first_page_btn)
        page_control_layout.addWidget(self.prev_page_btn)
        page_control_layout.addStretch()
        page_control_layout.addLayout(page_jump_layout)
        page_control_layout.addStretch()
        page_control_layout.addWidget(self.next_page_btn)
        page_control_layout.addWidget(self.last_page_btn)
        
        return page_control_layout
    
    def showFullImage(self, item: QListWidgetItem):
        """
        显示完整图片 - 全屏灯箱效果（需求 13.6）
        
        Args:
            item: 列表项
        """
        if item and item.data(Qt.UserRole):
            file_path = item.data(Qt.UserRole)
            try:
                # 创建全屏对话框（需求 13.6：全屏灯箱效果）
                dialog = QDialog(self)
                dialog.setWindowTitle(self.i18n.t("fullscreen_preview.title"))
                dialog.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: rgba(0, 0, 0, 230);
                    }
                """)
                
                # 设置为全屏
                screen = QApplication.primaryScreen().geometry()
                dialog.setGeometry(screen)
                
                layout = QVBoxLayout(dialog)
                layout.setContentsMargins(20, 20, 20, 20)
                
                # 创建图片标签
                label = QLabel()
                pixmap = QPixmap(file_path)
                
                if not pixmap.isNull():
                    # 缩放图片以适应屏幕
                    max_width = screen.width() - 100
                    max_height = screen.height() - 150
                    
                    scaled_pixmap = pixmap.scaled(
                        max_width,
                        max_height,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    
                    label.setPixmap(scaled_pixmap)
                    label.setAlignment(Qt.AlignCenter)
                    
                    # 添加阴影效果
                    shadow = QGraphicsDropShadowEffect()
                    shadow.setBlurRadius(30)
                    shadow.setColor(QColor(0, 0, 0, 180))
                    shadow.setOffset(0, 0)
                    label.setGraphicsEffect(shadow)
                else:
                    label.setText(self.i18n.t("preview.image_load_failed"))
                    label.setStyleSheet("color: white; font-size: 24px;")
                
                layout.addWidget(label)
                
                # 创建底部控制栏
                control_layout = QHBoxLayout()
                
                # 文件名标签
                filename_label = QLabel(os.path.basename(file_path))
                filename_label.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 14px;
                        font-weight: 500;
                        padding: 12px 20px;
                        background-color: rgba(0, 0, 0, 150);
                        border-radius: 8px;
                    }
                """)
                filename_label.setAlignment(Qt.AlignCenter)
                
                # 关闭按钮
                close_button = QPushButton("✕ 关闭 (ESC)")
                close_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(220, 53, 69, 220);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-size: 14px;
                        font-weight: bold;
                        min-height: 40px;
                    }
                    QPushButton:hover {
                        background-color: rgba(200, 35, 51, 255);
                    }
                    QPushButton:pressed {
                        background-color: rgba(180, 25, 41, 255);
                    }
                """)
                close_button.setCursor(Qt.PointingHandCursor)
                close_button.clicked.connect(dialog.accept)
                
                # 添加键盘快捷键支持
                close_button.setShortcut("Esc")
                
                control_layout.addWidget(filename_label)
                control_layout.addStretch()
                control_layout.addWidget(close_button)
                
                layout.addLayout(control_layout)
                
                # 点击背景关闭
                dialog.mousePressEvent = lambda e: dialog.accept() if e.button() == Qt.LeftButton else None
                
                dialog.exec_()
            except Exception as e:
                logger.error(f"显示图片失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"无法显示图片: {str(e)}")
    
    def addImage(self, file_path: str, pixmap: QPixmap, use_lazy_load: bool = False):
        """
        添加图片到预览列表（需求 13.1：圆角和阴影效果）
        
        Args:
            file_path: 文件路径
            pixmap: 图片对象
        """
        # 内存优化：限制总图片数量
        if len(self.all_images) >= self.MAX_TOTAL_ITEMS:
            self.all_images.pop(0)
            logger.debug(f"图片总数达到上限({self.MAX_TOTAL_ITEMS})，移除最早的图片")
        
        # 获取预览图片大小设置
        icon_size = self._get_icon_size()
        
        # 创建带阴影和圆角的缩略图（需求 13.1）
        fixed_pixmap = self._create_thumbnail_with_shadow(pixmap, icon_size)
        
        # 存储图片信息
        self.all_images.append({
            "file_path": file_path,
            "pixmap": fixed_pixmap
        })
        
        # 更新显示
        self.updateDisplay()
        
        # 更新下载数量
        self.download_count_label.setText(self.i18n.t("preview.downloaded", count=len(self.all_images)))
    
    def _create_thumbnail_with_shadow(self, pixmap: QPixmap, icon_size: QSize) -> QPixmap:
        """
        创建带阴影和圆角的缩略图（需求 13.1）
        
        Args:
            pixmap: 原始图片
            icon_size: 目标尺寸
            
        Returns:
            带阴影和圆角的缩略图
        """
        # 创建固定大小的透明背景图片（留出阴影空间）
        shadow_offset = 8  # 阴影偏移
        canvas_size = QSize(icon_size.width() + shadow_offset * 2, 
                           icon_size.height() + shadow_offset * 2)
        fixed_pixmap = QPixmap(canvas_size)
        fixed_pixmap.fill(Qt.transparent)
        
        # 缩放图片保持宽高比
        scaled_pixmap = pixmap.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 计算居中位置（考虑阴影偏移）
        x = shadow_offset + (icon_size.width() - scaled_pixmap.width()) // 2
        y = shadow_offset + (icon_size.height() - scaled_pixmap.height()) // 2
        
        # 绘制阴影和圆角图片
        painter = QPainter(fixed_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 绘制阴影（需求 13.1）
        shadow_color = QColor(0, 0, 0, 40)
        shadow_blur = 6
        border_radius = 10  # 圆角 8-12px
        
        for i in range(shadow_blur):
            alpha = int(shadow_color.alpha() * (1 - i / shadow_blur))
            color = QColor(shadow_color.red(), shadow_color.green(), 
                          shadow_color.blue(), alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            shadow_rect = scaled_pixmap.rect().adjusted(
                x + i, y + i, x + i, y + i
            )
            painter.drawRoundedRect(shadow_rect, border_radius, border_radius)
        
        # 绘制圆角图片（需求 13.1：8-12px 圆角）
        path = QPainterPath()
        path.addRoundedRect(x, y, scaled_pixmap.width(), scaled_pixmap.height(), 
                           border_radius, border_radius)
        painter.setClipPath(path)
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()
        
        return fixed_pixmap
    
    def _get_icon_size(self) -> QSize:
        """获取图标大小"""
        preview_size = "中 (200x200)"
        if hasattr(self.parent(), 'settings'):
            preview_size = self.parent().settings.get("preview_size", "中 (200x200)")
        
        size_map = {
            "小 (150x150)": QSize(150, 150),
            "中 (200x200)": QSize(200, 200),
            "大 (300x300)": QSize(300, 300)
        }
        
        return size_map.get(preview_size, QSize(200, 200))
    
    def updateDisplay(self):
        """更新当前页面显示（支持懒加载 - 需求 13.3）"""
        # 清空当前显示
        self.image_list.clear()
        
        # 计算总页数
        total_pages = max(1, (len(self.all_images) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        
        # 确保当前页码合法
        if self.current_page > total_pages:
            self.current_page = total_pages
        
        # 更新分页信息
        self.page_info_label.setText(self.i18n.t("preview.page_info", current=self.current_page, total=total_pages))
        self.page_jump_spin.setMaximum(total_pages)
        self.page_jump_spin.setValue(self.current_page)
        
        # 更新按钮状态
        self.first_page_btn.setEnabled(self.current_page > 1)
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)
        self.last_page_btn.setEnabled(self.current_page < total_pages)
        
        # 计算当前页的图片索引范围
        start_idx = (self.current_page - 1) * self.ITEMS_PER_PAGE
        end_idx = min(start_idx + self.ITEMS_PER_PAGE, len(self.all_images))
        
        # 添加当前页的图片
        for i in range(start_idx, end_idx):
            image_data = self.all_images[i]
            
            # 懒加载：如果图片未加载，触发加载（需求 13.3）
            if self._lazy_load_enabled and not image_data["is_loaded"] and not image_data["load_failed"]:
                self._load_image_for_item(i)
            
            item = QListWidgetItem()
            icon = QIcon(image_data["pixmap"])
            item.setIcon(icon)
            item.setData(Qt.UserRole, image_data["file_path"])
            
            self.image_list.addItem(item)
        
        # 标记当前页已加载
        self._loaded_pages.add(self.current_page)
        
        # 滚动到顶部
        self.image_list.scrollToTop()
    
    def goToFirstPage(self):
        """跳转到首页"""
        self.current_page = 1
        self.updateDisplay()
        logger.debug("跳转到首页")
    
    def goToPrevPage(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.updateDisplay()
            logger.debug(f"跳转到第{self.current_page}页")
    
    def goToNextPage(self):
        """下一页"""
        total_pages = max(1, (len(self.all_images) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        if self.current_page < total_pages:
            self.current_page += 1
            self.updateDisplay()
            logger.debug(f"跳转到第{self.current_page}页")
    
    def goToLastPage(self):
        """跳转到末页"""
        total_pages = max(1, (len(self.all_images) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        self.current_page = total_pages
        self.updateDisplay()
        logger.debug(f"跳转到末页(第{total_pages}页)")
    
    def jumpToPage(self):
        """跳转到指定页"""
        target_page = self.page_jump_spin.value()
        total_pages = max(1, (len(self.all_images) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        
        if 1 <= target_page <= total_pages:
            self.current_page = target_page
            self.updateDisplay()
            logger.debug(f"跳转到第{target_page}页")
    
    def count(self) -> int:
        """返回图片数量"""
        return len(self.all_images)
    
    def clear(self):
        """清除所有图片"""
        self.all_images.clear()
        self.current_page = 1
        self.image_list.clear()
        self.download_count_label.setText(self.i18n.t("preview.downloaded", count=0))
        self.page_info_label.setText(self.i18n.t("preview.page_info", current=1, total=1))
        self.page_jump_spin.setMaximum(1)
        self.page_jump_spin.setValue(1)
        self.first_page_btn.setEnabled(False)
        self.prev_page_btn.setEnabled(False)
        self.next_page_btn.setEnabled(False)
        self.last_page_btn.setEnabled(False)
        logger.debug("清除所有预览图片")
    
    def scrollToBottom(self):
        """滚动到底部"""
        self.image_list.scrollToBottom()
    
    def _show_hover_preview(self, file_path: str):
        """
        显示悬停放大预览（需求 13.2）
        
        Args:
            file_path: 文件路径
        """
        try:
            # 创建悬停预览标签（如果不存在）
            if self.hover_preview_label is None:
                self.hover_preview_label = QLabel(self)
                self.hover_preview_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(0, 0, 0, 200);
                        border: 2px solid rgba(255, 255, 255, 150);
                        border-radius: 10px;
                        padding: 10px;
                    }
                """)
                self.hover_preview_label.setAlignment(Qt.AlignCenter)
                self.hover_preview_label.hide()
            
            # 加载并显示放大的图片
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # 缩放到合适大小（比缩略图大，但不超过屏幕）
                max_size = 400
                scaled_pixmap = pixmap.scaled(
                    max_size, max_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self.hover_preview_label.setPixmap(scaled_pixmap)
                self.hover_preview_label.adjustSize()
                
                # 定位到鼠标附近
                cursor_pos = self.mapFromGlobal(QCursor.pos())
                x = min(cursor_pos.x() + 20, self.width() - self.hover_preview_label.width() - 20)
                y = min(cursor_pos.y() + 20, self.height() - self.hover_preview_label.height() - 20)
                x = max(20, x)
                y = max(20, y)
                
                self.hover_preview_label.move(x, y)
                self.hover_preview_label.show()
                self.hover_preview_label.raise_()
        except Exception as e:
            logger.error(f"显示悬停预览失败: {str(e)}")
    
    def _hide_hover_preview(self):
        """隐藏悬停预览"""
        if self.hover_preview_label:
            self.hover_preview_label.hide()
    
    def _handle_delete_image(self, file_path: str):
        """
        处理删除图片请求（需求 13.2）
        
        Args:
            file_path: 文件路径
        """
        reply = QMessageBox.question(
            self,
            self.i18n.t("preview.delete_confirm"),
            f"{self.i18n.t('preview.delete_message')}\n{os.path.basename(file_path)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 从列表中移除
                self.all_images = [img for img in self.all_images if img["file_path"] != file_path]
                
                # 删除文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"已删除图片: {file_path}")
                
                # 更新显示
                self.updateDisplay()
                self.download_count_label.setText(self.i18n.t("preview.downloaded", count=len(self.all_images)))
                
                QMessageBox.information(self, self.i18n.t("preview.delete_success"), self.i18n.t("preview.delete_success_message"))
            except Exception as e:
                logger.error(f"删除图片失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"删除图片失败: {str(e)}")
    
    def _handle_open_folder(self, file_path: str):
        """
        处理打开文件夹请求（需求 13.2）
        
        Args:
            file_path: 文件路径
        """
        try:
            folder_path = os.path.dirname(file_path)
            if os.path.exists(folder_path):
                # 在不同操作系统上打开文件夹
                import platform
                system = platform.system()
                
                if system == "Windows":
                    os.startfile(folder_path)
                elif system == "Darwin":  # macOS
                    os.system(f'open "{folder_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{folder_path}"')
                
                logger.info(f"已打开文件夹: {folder_path}")
            else:
                QMessageBox.warning(self, "错误", "文件夹不存在")
        except Exception as e:
            logger.error(f"打开文件夹失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"打开文件夹失败: {str(e)}")
    
    def _show_context_menu(self, position):
        """
        显示右键菜单（需求 13.2, 13.4）
        
        Args:
            position: 鼠标位置
        """
        item = self.image_list.itemAt(position)
        if item:
            file_path = item.data(Qt.UserRole)
            
            # 查找图片数据
            image_data = None
            for img in self.all_images:
                if img["file_path"] == file_path:
                    image_data = img
                    break
            
            menu = QMenu(self)
            
            # 查看大图
            view_action = QAction("🔍 查看大图", self)
            view_action.triggered.connect(lambda: self.showFullImage(item))
            menu.addAction(view_action)
            
            # 如果加载失败，添加重试选项（需求 13.4）
            if image_data and image_data.get("load_failed", False):
                menu.addSeparator()
                retry_action = QAction("🔄 重试加载", self)
                retry_action.triggered.connect(lambda: self._retry_load_image(file_path))
                menu.addAction(retry_action)
            
            menu.addSeparator()
            
            # 打开文件夹
            open_action = QAction("📂 打开文件夹", self)
            open_action.triggered.connect(lambda: self._handle_open_folder(file_path))
            menu.addAction(open_action)
            
            # 删除
            delete_action = QAction("🗑 删除", self)
            delete_action.triggered.connect(lambda: self._handle_delete_image(file_path))
            menu.addAction(delete_action)
            
            # 显示菜单
            menu.exec_(self.image_list.mapToGlobal(position))
    
    def _on_item_entered(self, item: QListWidgetItem):
        """
        鼠标进入列表项时显示预览（需求 13.2）
        
        Args:
            item: 列表项
        """
        if item:
            file_path = item.data(Qt.UserRole)
            self._show_hover_preview(file_path)
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理鼠标离开列表"""
        if obj == self.image_list.viewport():
            if event.type() == event.Leave:
                self._hide_hover_preview()
        return super().eventFilter(obj, event)
    
    def _create_placeholder_images(self):
        """创建占位图和错误图（需求 13.4）"""
        # 创建占位图
        size = QSize(200, 200)
        self._placeholder_pixmap = QPixmap(size)
        self._placeholder_pixmap.fill(QColor(240, 240, 240))
        
        painter = QPainter(self._placeholder_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制加载图标
        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QApplication.font())
        painter.drawText(self._placeholder_pixmap.rect(), Qt.AlignCenter, "⏳\n加载中...")
        painter.end()
        
        # 创建错误图
        self._error_pixmap = QPixmap(size)
        self._error_pixmap.fill(QColor(255, 240, 240))
        
        painter = QPainter(self._error_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制错误图标
        painter.setPen(QColor(220, 53, 69))
        painter.setFont(QApplication.font())
        painter.drawText(self._error_pixmap.rect(), Qt.AlignCenter, "❌\n加载失败\n点击重试")
        painter.end()
    
    def addImage(self, file_path: str, pixmap: QPixmap, use_lazy_load: bool = False):
        """
        添加图片到预览列表（需求 13.1：圆角和阴影效果，13.3：懒加载）
        
        Args:
            file_path: 文件路径
            pixmap: 图片对象
            use_lazy_load: 是否使用懒加载
        """
        # 内存优化：限制总图片数量
        if len(self.all_images) >= self.MAX_TOTAL_ITEMS:
            self.all_images.pop(0)
            logger.debug(f"图片总数达到上限({self.MAX_TOTAL_ITEMS})，移除最早的图片")
        
        # 获取预览图片大小设置
        icon_size = self._get_icon_size()
        
        # 懒加载：如果启用，先使用占位图（需求 13.3）
        if use_lazy_load and self._lazy_load_enabled:
            fixed_pixmap = self._placeholder_pixmap
            is_loaded = False
        else:
            # 创建带阴影和圆角的缩略图（需求 13.1）
            try:
                fixed_pixmap = self._create_thumbnail_with_shadow(pixmap, icon_size)
                is_loaded = True
            except Exception as e:
                logger.error(f"创建缩略图失败: {str(e)}")
                fixed_pixmap = self._error_pixmap
                is_loaded = False
        
        # 存储图片信息
        self.all_images.append({
            "file_path": file_path,
            "pixmap": fixed_pixmap,
            "original_pixmap": pixmap if not use_lazy_load else None,
            "is_loaded": is_loaded,
            "load_failed": False
        })
        
        # 更新显示
        self.updateDisplay()
        
        # 更新下载数量
        self.download_count_label.setText(self.i18n.t("preview.downloaded", count=len(self.all_images)))
    
    def _load_image_for_item(self, index: int):
        """
        懒加载：为指定索引的图片加载实际内容（需求 13.3）
        
        Args:
            index: 图片索引
        """
        if 0 <= index < len(self.all_images):
            image_data = self.all_images[index]
            
            # 如果已加载或加载失败，跳过
            if image_data["is_loaded"] or image_data["load_failed"]:
                return
            
            try:
                # 从文件加载图片
                file_path = image_data["file_path"]
                if os.path.exists(file_path):
                    pixmap = QPixmap(file_path)
                    if not pixmap.isNull():
                        # 创建缩略图
                        icon_size = self._get_icon_size()
                        thumbnail = self._create_thumbnail_with_shadow(pixmap, icon_size)
                        
                        # 更新图片数据
                        image_data["pixmap"] = thumbnail
                        image_data["original_pixmap"] = pixmap
                        image_data["is_loaded"] = True
                        
                        # 更新显示
                        self.updateDisplay()
                    else:
                        raise Exception("图片加载失败")
                else:
                    raise Exception("文件不存在")
            except Exception as e:
                logger.error(f"懒加载图片失败: {str(e)}")
                image_data["pixmap"] = self._error_pixmap
                image_data["load_failed"] = True
                self.updateDisplay()
    
    def _retry_load_image(self, file_path: str):
        """
        重试加载失败的图片（需求 13.4）
        
        Args:
            file_path: 文件路径
        """
        for i, image_data in enumerate(self.all_images):
            if image_data["file_path"] == file_path and image_data["load_failed"]:
                # 重置加载状态
                image_data["load_failed"] = False
                image_data["is_loaded"] = False
                image_data["pixmap"] = self._placeholder_pixmap
                
                # 重新加载
                self._load_image_for_item(i)
                break


    
    def _apply_glass_spinbox_style(self, spinbox: QSpinBox):
        """应用玻璃风格数字输入框样式 - 使用SVG箭头图标"""
        try:
            from ui.custom_arrows import CustomArrows
        except ImportError:
            try:
                from wallhaven_downloader.ui.custom_arrows import CustomArrows
            except ImportError:
                # 回退到基础样式
                spinbox.setStyleSheet("""
                    QSpinBox {
                        background: qlineargradient(
                            x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(255, 255, 255, 200),
                            stop:1 rgba(255, 255, 255, 180)
                        );
                        border: 1px solid rgba(200, 200, 200, 150);
                        border-radius: 10px;
                        padding: 10px 14px;
                        color: rgb(50, 50, 50);
                        font-size: 14px;
                        font-weight: 600;
                        min-height: 40px;
                        min-width: 90px;
                    }
                    QSpinBox:hover {
                        background: qlineargradient(
                            x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(255, 255, 255, 240),
                            stop:1 rgba(255, 255, 255, 220)
                        );
                        border-color: rgba(59, 130, 246, 200);
                    }
                    QSpinBox:focus {
                        background: qlineargradient(
                            x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(255, 255, 255, 250),
                            stop:1 rgba(255, 255, 255, 240)
                        );
                        border: 2px solid rgb(59, 130, 246);
                    }
                """)
                return
        
        import tempfile
        import os
        
        # 创建向上和向下箭头图标
        up_arrow = CustomArrows.create_arrow_icon("up", "#646464", 16)
        up_arrow_hover = CustomArrows.create_arrow_icon("up", "#3b82f6", 16)
        down_arrow = CustomArrows.create_arrow_icon("down", "#646464", 16)
        down_arrow_hover = CustomArrows.create_arrow_icon("down", "#3b82f6", 16)
        
        # 保存图标到临时文件
        temp_dir = tempfile.gettempdir()
        up_arrow_path = os.path.join(temp_dir, "preview_spinbox_up_arrow.png")
        up_arrow_hover_path = os.path.join(temp_dir, "preview_spinbox_up_arrow_hover.png")
        down_arrow_path = os.path.join(temp_dir, "preview_spinbox_down_arrow.png")
        down_arrow_hover_path = os.path.join(temp_dir, "preview_spinbox_down_arrow_hover.png")
        
        up_arrow.save(up_arrow_path)
        up_arrow_hover.save(up_arrow_hover_path)
        down_arrow.save(down_arrow_path)
        down_arrow_hover.save(down_arrow_hover_path)
        
        # 转换路径为URL格式
        up_arrow_url = up_arrow_path.replace("\\", "/")
        up_arrow_hover_url = up_arrow_hover_path.replace("\\", "/")
        down_arrow_url = down_arrow_path.replace("\\", "/")
        down_arrow_hover_url = down_arrow_hover_path.replace("\\", "/")
        
        spinbox.setStyleSheet(f"""
            QSpinBox {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 200),
                    stop:1 rgba(255, 255, 255, 180)
                );
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 10px;
                padding: 10px 14px;
                color: rgb(50, 50, 50);
                font-size: 14px;
                font-weight: 600;
                min-height: 40px;
                min-width: 90px;
            }}
            QSpinBox:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 240),
                    stop:1 rgba(255, 255, 255, 220)
                );
                border-color: rgba(59, 130, 246, 200);
            }}
            QSpinBox:focus {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 250),
                    stop:1 rgba(255, 255, 255, 240)
                );
                border: 2px solid rgb(59, 130, 246);
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid rgba(200, 200, 200, 150);
                border-top-right-radius: 10px;
                background: transparent;
            }}
            QSpinBox::up-button:hover {{
                background: rgba(59, 130, 246, 100);
            }}
            QSpinBox::up-arrow {{
                image: url({up_arrow_url});
                width: 16px;
                height: 16px;
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 28px;
                border-left: 1px solid rgba(200, 200, 200, 150);
                border-bottom-right-radius: 10px;
                background: transparent;
            }}
            QSpinBox::down-button:hover {{
                background: rgba(59, 130, 246, 100);
            }}
            QSpinBox::down-arrow {{
                image: url({down_arrow_url});
                width: 16px;
                height: 16px;
            }}
        """)
