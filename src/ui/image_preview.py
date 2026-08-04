# -*- coding: utf-8 -*-
"""
图片预览组件
支持分页显示、图片缩略图预览
"""

from typing import List, Dict, Optional
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QIcon, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSpinBox, QAbstractItemView,
    QDialog, QMessageBox, QApplication, QGraphicsOpacityEffect
)

try:
    from core.theme_manager import get_theme_manager
except ImportError:
    from ..core.theme_manager import get_theme_manager

from utils.logger import get_logger

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
        
        # 存储所有图片信息
        self.all_images: List[Dict[str, any]] = []
        self.current_page: int = 1
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        
        # 创建顶部信息栏
        info_layout = QHBoxLayout()
        
        # 下载数量标签
        self.download_count_label = QLabel("已下载: 0 张")
        self.download_count_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 100);
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 5px;
                padding: 5px;
                margin: 5px;
                font-weight: bold;
            }
        """)
        self.download_count_label.setAlignment(Qt.AlignCenter)
        
        # 分页信息标签
        self.page_info_label = QLabel("第 1 页 / 共1页")
        self.page_info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 100);
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 5px;
                padding: 5px;
                margin: 5px;
                font-weight: bold;
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
        self.image_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.image_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 设置图片列表样式
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
                border-radius: 15px;
                padding: 5px;
                margin: 5px;
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
        
        # 创建分页控制按钮
        page_control_layout = self._create_page_controls()
        
        # 添加所有组件到主布局
        self.main_layout.addLayout(info_layout)
        self.main_layout.addWidget(self.image_list)
        self.main_layout.addLayout(page_control_layout)
    
    def _create_page_controls(self) -> QHBoxLayout:
        """创建分页控制按钮"""
        page_control_layout = QHBoxLayout()
        
        # 首页按钮
        self.first_page_btn = QPushButton("首页")
        self.first_page_btn.clicked.connect(self.goToFirstPage)
        self.first_page_btn.setEnabled(False)
        
        # 上一页按钮
        self.prev_page_btn = QPushButton("上一页")
        self.prev_page_btn.clicked.connect(self.goToPrevPage)
        self.prev_page_btn.setEnabled(False)
        
        # 页码跳转
        page_jump_layout = QHBoxLayout()
        page_jump_label = QLabel("跳转到:")
        self.page_jump_spin = QSpinBox()
        self.page_jump_spin.setMinimum(1)
        self.page_jump_spin.setMaximum(1)
        self.page_jump_spin.setValue(1)
        page_jump_btn = QPushButton("跳转")
        page_jump_btn.clicked.connect(self.jumpToPage)
        page_jump_layout.addWidget(page_jump_label)
        page_jump_layout.addWidget(self.page_jump_spin)
        page_jump_layout.addWidget(page_jump_btn)
        
        # 下一页按钮
        self.next_page_btn = QPushButton("下一页")
        self.next_page_btn.clicked.connect(self.goToNextPage)
        self.next_page_btn.setEnabled(False)
        
        # 末页按钮
        self.last_page_btn = QPushButton("末页")
        self.last_page_btn.clicked.connect(self.goToLastPage)
        self.last_page_btn.setEnabled(False)
        
        page_control_layout.addWidget(self.first_page_btn)
        page_control_layout.addWidget(self.prev_page_btn)
        page_control_layout.addLayout(page_jump_layout)
        page_control_layout.addWidget(self.next_page_btn)
        page_control_layout.addWidget(self.last_page_btn)
        
        return page_control_layout
    
    def showFullImage(self, item: QListWidgetItem):
        """
        显示完整图片
        
        Args:
            item: 列表项
        """
        if item and item.data(Qt.UserRole):
            file_path = item.data(Qt.UserRole)
            try:
                # 创建对话框显示完整图片
                dialog = QDialog(self)
                dialog.setWindowTitle("图片预览")
                
                layout = QVBoxLayout(dialog)
                
                # 创建图片标签
                label = QLabel()
                pixmap = QPixmap(file_path)
                
                # 根据图片分辨率调整缩放75%
                scaled_width = int(pixmap.width() * 0.75)
                scaled_height = int(pixmap.height() * 0.75)
                
                # 获取屏幕尺寸 - 修复 QDesktopWidget 弃用警告
                screen = QApplication.primaryScreen().geometry()
                max_width = int(screen.width() * 0.9)
                max_height = int(screen.height() * 0.9)
                
                # 限制对话框最大尺寸
                dialog_width = min(scaled_width, max_width)
                dialog_height = min(scaled_height, max_height)
                
                dialog.setMinimumSize(400, 300)
                dialog.resize(dialog_width, dialog_height)
                
                # 缩放图片以适应对话框大小
                if pixmap.width() > dialog.width() or pixmap.height() > dialog.height():
                    pixmap = pixmap.scaled(
                        dialog.width() - 20,
                        dialog.height() - 20,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
                
                # 添加关闭按钮
                close_button = QPushButton("关闭")
                close_button.clicked.connect(dialog.accept)
                layout.addWidget(close_button)
                
                dialog.exec_()
            except Exception as e:
                logger.error(f"显示图片失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"无法显示图片: {str(e)}")
    
    def addImage(self, file_path: str, pixmap: QPixmap):
        """
        添加图片到预览列表
        
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
        
        # 创建固定大小的透明背景图片
        fixed_pixmap = QPixmap(icon_size)
        fixed_pixmap.fill(Qt.transparent)
        
        # 缩放图片保持宽高比
        scaled_pixmap = pixmap.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 计算居中位置
        x = (icon_size.width() - scaled_pixmap.width()) // 2
        y = (icon_size.height() - scaled_pixmap.height()) // 2
        
        # 绘制圆角图片
        painter = QPainter(fixed_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, icon_size.width(), icon_size.height(), 15, 15)
        painter.setClipPath(path)
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()
        
        # 存储图片信息
        self.all_images.append({
            "file_path": file_path,
            "pixmap": fixed_pixmap
        })
        
        # 更新显示
        self.updateDisplay()
        
        # 更新下载数量
        self.download_count_label.setText(f"已下载: {len(self.all_images)} 张")
    
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
        """更新当前页面显示"""
        # 清空当前显示
        self.image_list.clear()
        
        # 计算总页数
        total_pages = max(1, (len(self.all_images) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        
        # 确保当前页码合法
        if self.current_page > total_pages:
            self.current_page = total_pages
        
        # 更新分页信息
        self.page_info_label.setText(f"第 {self.current_page} 页 / 共{total_pages}页")
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
            
            item = QListWidgetItem()
            icon = QIcon(image_data["pixmap"])
            item.setIcon(icon)
            item.setData(Qt.UserRole, image_data["file_path"])
            
            self.image_list.addItem(item)
        
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
        self.download_count_label.setText("已下载: 0 张")
        self.page_info_label.setText("第 1 页 / 共1页")
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
