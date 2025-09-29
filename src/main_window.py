# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import requests
import urllib.parse
import threading
import queue
import concurrent.futures
from datetime import datetime
from PIL import Image
from io import BytesIO

# 用于处理资源路径的函数
def resource_path(relative_path):
    """获取资源文件的绝对路径，无论程序是直接运行还是被打包"""
    try:
        # PyInstaller 创建临时文件夹，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        # 未打包时，使用当前工作目录
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    return os.path.join(base_path, relative_path)

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint, QRect, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont, QImage, QLinearGradient, QRadialGradient, QPainterPath
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QListWidget, QListWidgetItem, QComboBox,
                            QSpinBox, QSlider, QProgressBar, QMessageBox, QGroupBox, QCheckBox,
                            QRadioButton, QButtonGroup, QTabWidget, QScrollArea, QSplitter,
                            QFrame, QStyle, QStyleOption, QDesktopWidget, QSizePolicy, QGridLayout,
                            QLineEdit, QTextEdit, QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox,
                            QGraphicsDropShadowEffect, QAbstractItemView, QScrollBar)

class WallpaperDownloadThread(QThread):
    """壁纸下载线程"""
    progress_updated = pyqtSignal(int, str)  # 进度更新信号 (进度百分比, 当前下载的文件名)
    download_completed = pyqtSignal()  # 下载完成信号
    download_failed = pyqtSignal(str)  # 下载失败信号
    image_downloaded = pyqtSignal(str, QPixmap)  # 图片下载完成信号 (文件路径, 图片)
    duplicate_detected = pyqtSignal(int, int)  # 检测到重复文件信号 (重复数量, 总数量)
    
    def __init__(self, base_url, page_count, download_dir, parent=None, resume_state=None, concurrent_downloads=3):
        super().__init__(parent)
        self.base_url = base_url
        self.page_count = page_count
        self.download_dir = download_dir
        self.is_running = True
        self.cookies = dict()
        self.total_images = 0
        self.downloaded_images = 0
        self.duplicate_images = 0
        self.unique_images_to_download = 0  # 需要实际下载的图片数量（不包括重复文件）
        self._last_progress_update = 0  # 上次更新进度的时间
        self._progress_update_threshold = 100  # 进度更新阈值（毫秒）
        self.concurrent_downloads = concurrent_downloads  # 并发下载数
        
        # 恢复下载状态
        self.resume_state = resume_state or {}
        self.current_page = self.resume_state.get('current_page', 1)
        self.processed_urls = self.resume_state.get('processed_urls', set())
        self.downloaded_files = self.resume_state.get('downloaded_files', set())
        self.is_resuming = bool(resume_state)  # 是否是恢复下载
        
    def download_single_image(self, img_url, img_filename):
        """下载单个图片"""
        try:
            if not self.is_running:
                return None
                
            print(f"[日志] 下载图片: {img_filename}")
            file_path = os.path.join(self.download_dir, img_filename)
            
            # 下载图片
            imgreq = requests.get(img_url, cookies=self.cookies, timeout=30)
            
            if imgreq.status_code == 200:
                # 保存图片
                with open(file_path, 'wb') as image_file:
                    for chunk in imgreq.iter_content(1024):
                        image_file.write(chunk)
                
                # 记录已下载的文件
                self.downloaded_files.add(img_filename)
                
                # 加载图片用于预览
                try:
                    img_data = imgreq.content
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    return (file_path, pixmap, True)
                except Exception as e:
                    print(f"[日志] 加载预览图片失败: {e}")
                    return (file_path, None, True)
            else:
                print(f"[日志] 下载图片失败: {img_filename}, 状态码: {imgreq.status_code}")
                return (img_filename, None, False)
                
        except Exception as e:
            print(f"[日志] 下载图片异常: {img_filename}, 错误: {e}")
            return (img_filename, None, False)
    
    def run(self):
        try:
            # 创建下载目录
            os.makedirs(self.download_dir, exist_ok=True)
            
            start_time = datetime.now()
            
            # 先获取所有图片URL，计算总数量
            all_image_urls = []
            print(f"[日志] 开始获取图片列表...")
            
            # 如果是恢复下载，从上次中断的页面开始
            start_page = self.current_page if self.is_resuming else 1
            
            for page_id in range(start_page, self.page_count + 1):
                if not self.is_running:
                    break
                
                # 获取页面数据
                url = self.base_url + str(page_id)
                print(f"[日志] 获取页面 {page_id}: {url}")
                urlreq = requests.get(url, cookies=self.cookies)
                
                if urlreq.status_code != 200:
                    self.download_failed.emit(f"获取页面数据失败: {urlreq.status_code}")
                    return
                
                pages_images = json.loads(urlreq.content)
                page_data = pages_images["data"]
                
                # 收集图片URL
                for i in range(len(page_data)):
                    img_url = page_data[i]["path"]
                    # 如果不是恢复下载或者URL不在已处理列表中，则添加
                    if not self.is_resuming or img_url not in self.processed_urls:
                        all_image_urls.append(img_url)
                        # 记录已处理的URL
                        self.processed_urls.add(img_url)
                
                # 更新当前页面，用于恢复下载
                self.current_page = page_id
            
            # 设置总图片数
            self.total_images = len(all_image_urls)
            print(f"[日志] 总共需要下载 {self.total_images} 张图片")
            
            # 检查已存在的文件
            existing_files = set()
            for filename in os.listdir(self.download_dir):
                if filename.startswith("wallhaven-") and (filename.endswith(".jpg") or filename.endswith(".png")):
                    existing_files.add(filename)
            
            print(f"[日志] 下载目录中已存在 {len(existing_files)} 个文件")
            
            # 计算需要实际下载的图片数量（不包括重复文件）
            self.unique_images_to_download = 0
            unique_image_urls = []
            
            for img_url in all_image_urls:
                filename = os.path.basename(img_url)
                if filename not in existing_files and filename not in self.downloaded_files:
                    self.unique_images_to_download += 1
                    unique_image_urls.append(img_url)
                else:
                    self.duplicate_images += 1
            
            print(f"[日志] 需要实际下载 {self.unique_images_to_download} 张新图片（不包括重复文件）")
            
            # 发送重复文件检测信号
            if self.duplicate_images > 0:
                self.duplicate_detected.emit(self.duplicate_images, self.total_images)
            
            # 如果没有需要下载的图片，检查是否需要继续下载以达到指定页数
            if self.unique_images_to_download == 0:
                print(f"[日志] 所有图片都已存在，无需下载")
                
                # 检查是否需要继续下载以达到指定页数
                images_per_page = 64
                target_total_images = images_per_page * self.page_count
                
                if self.total_images < target_total_images and self.is_running:
                    print(f"[日志] 当前图片总数({self.total_images})少于目标数量({target_total_images})，继续获取更多页面...")
                    
                    # 计算需要额外获取的页面数
                    additional_pages_needed = (target_total_images - self.total_images + images_per_page - 1) // images_per_page
                    
                    for page_id in range(self.page_count + 1, self.page_count + additional_pages_needed + 1):
                        if not self.is_running:
                            break
                        
                        # 获取页面数据
                        url = self.base_url + str(page_id)
                        print(f"[日志] 获取额外页面 {page_id}: {url}")
                        urlreq = requests.get(url, cookies=self.cookies)
                        
                        if urlreq.status_code != 200:
                            print(f"[日志] 获取额外页面数据失败: {urlreq.status_code}")
                            continue
                        
                        pages_images = json.loads(urlreq.content)
                        page_data = pages_images["data"]
                        
                        # 处理额外页面的图片
                        for i in range(len(page_data)):
                            img_url = page_data[i]["path"]
                            filename = os.path.basename(img_url)
                            
                            # 检查是否已存在
                            if filename not in existing_files and filename not in self.downloaded_files:
                                print(f"[日志] 下载额外图片: {filename}")
                                file_path = os.path.join(self.download_dir, filename)
                                
                                # 下载图片
                                imgreq = requests.get(img_url, cookies=self.cookies)
                                
                                if imgreq.status_code == 200:
                                    # 保存图片
                                    with open(file_path, 'wb') as image_file:
                                        for chunk in imgreq.iter_content(1024):
                                            image_file.write(chunk)
                                    
                                    # 记录已下载的文件
                                    self.downloaded_files.add(filename)
                                    
                                    # 加载图片用于预览
                                    try:
                                        img_data = imgreq.content
                                        pixmap = QPixmap()
                                        pixmap.loadFromData(img_data)
                                        self.image_downloaded.emit(file_path, pixmap)
                                    except Exception as e:
                                        print(f"[日志] 加载预览图片失败: {e}")
                                    
                                    self.downloaded_images += 1
                                    self.unique_images_to_download += 1
                                    
                                    # 更新进度
                                    progress = min(100, int((self.downloaded_images / self.unique_images_to_download) * 100))
                                    self.progress_updated.emit(progress, filename)
                                elif imgreq.status_code not in (403, 404):
                                    print(f"[日志] 下载额外图片失败: {imgreq.status_code}")
                                    continue
                            else:
                                self.duplicate_images += 1
                                print(f"[日志] 检测到额外页面中的重复文件: {filename}")
                else:
                    print(f"[日志] 当前图片总数({self.total_images})已达到或超过目标数量({target_total_images})，无需继续下载")
                
                # 下载完成
                if self.duplicate_images > 0:
                    print(f"[日志] 下载完成，共检测到 {self.duplicate_images} 个重复文件")
                else:
                    print(f"[日志] 下载完成，未检测到重复文件")
                
                self.download_completed.emit()
                return
            
            # 使用线程池并发下载图片
            print(f"[日志] 开始并发下载 {self.unique_images_to_download} 张图片，并发数: {self.concurrent_downloads}")
            
            # 创建线程池
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_downloads) as executor:
                # 提交所有下载任务
                future_to_url = {
                    executor.submit(self.download_single_image, img_url, os.path.basename(img_url)): img_url
                    for img_url in unique_image_urls
                }
                
                # 处理完成的任务
                for future in concurrent.futures.as_completed(future_to_url):
                    if not self.is_running:
                        # 取消所有未完成的任务
                        for f in future_to_url:
                            f.cancel()
                        break
                    
                    img_url = future_to_url[future]
                    filename = os.path.basename(img_url)
                    
                    try:
                        result = future.result()
                        if result is None:
                            continue  # 下载被取消
                            
                        file_path, pixmap, success = result
                        
                        if success:
                            # 发送图片下载完成信号
                            if pixmap:
                                self.image_downloaded.emit(file_path, pixmap)
                            
                            self.downloaded_images += 1
                        else:
                            # 下载失败，但不是403或404错误
                            if isinstance(file_path, str) and file_path != filename:
                                self.download_failed.emit(f"下载图片失败: {file_path}")
                                continue
                    except Exception as e:
                        print(f"[日志] 处理下载结果异常: {e}")
                        continue
                    
                    # 更新进度，确保不超过100%
                    if self.unique_images_to_download > 0:
                        progress = min(100, int((self.downloaded_images / self.unique_images_to_download) * 100))
                        self.progress_updated.emit(progress, filename)
            
            # 下载完成
            if self.duplicate_images > 0:
                print(f"[日志] 下载完成，共检测到 {self.duplicate_images} 个重复文件")
            else:
                print(f"[日志] 下载完成，未检测到重复文件")
            
            self.download_completed.emit()
        except Exception as e:
            self.download_failed.emit(str(e))
    
    def stop(self):
        """停止下载并保存当前状态"""
        print(f"[日志] 停止下载线程")
        self.is_running = False
        
        # 保存当前下载状态，以便恢复
        resume_state = {
            'current_page': self.current_page,
            'processed_urls': self.processed_urls,
            'downloaded_files': self.downloaded_files,
            'base_url': self.base_url,
            'page_count': self.page_count,
            'download_dir': self.download_dir,
            'total_images': self.total_images,
            'downloaded_images': self.downloaded_images,
            'duplicate_images': self.duplicate_images,
            'unique_images_to_download': self.unique_images_to_download,
            'concurrent_downloads': self.concurrent_downloads
        }
        
        # 将状态保存到文件
        try:
            state_file = os.path.join(self.download_dir, '.download_state.json')
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(resume_state, f, ensure_ascii=False, indent=2)
            print(f"[日志] 下载状态已保存到: {state_file}")
        except Exception as e:
            print(f"[日志] 保存下载状态失败: {e}")
        
        # 发送状态保存信号
        if hasattr(self, 'state_saved'):
            self.state_saved.emit(resume_state)

class GlassEffectWidget(QWidget):
    """液态玻璃效果的基础部件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._glass_color = QColor(255, 255, 255, 180)  # 半透明白色
        self._border_color = QColor(255, 255, 255, 100)
        self._border_radius = 20
        self._shadow_blur = 20
        self._shadow_color = QColor(0, 0, 0, 50)
        self._highlight_color = QColor(255, 255, 255, 150)
        self._cached_background = None  # 缓存背景
        self._needs_background_update = True  # 是否需要更新背景
        
    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 如果需要更新背景或窗口大小改变
        if self._needs_background_update or self._cached_background is None or self._cached_background.size() != self.size():
            self._updateBackgroundCache()
            self._needs_background_update = False
        
        # 绘制缓存的背景
        if self._cached_background:
            painter.drawPixmap(0, 0, self._cached_background)
    
    def _updateBackgroundCache(self):
        """更新背景缓存"""
        # 创建与窗口大小相同的缓存图像
        self._cached_background = QPixmap(self.size())
        self._cached_background.fill(Qt.transparent)
        
        painter = QPainter(self._cached_background)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 绘制多层阴影，增加深度感
        shadow_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(Qt.NoPen)
        
        # 外层阴影 - 更模糊，更扩散
        for i in range(self._shadow_blur):
            alpha = int(self._shadow_color.alpha() * (1 - i / self._shadow_blur) * 0.6)
            color = QColor(self._shadow_color.red(), self._shadow_color.green(), 
                          self._shadow_color.blue(), alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(shadow_rect.adjusted(i, i, -i, -i), self._border_radius, self._border_radius)
        
        # 内层阴影 - 更锐利，更集中
        inner_shadow_rect = self.rect().adjusted(5, 5, -5, -5)
        for i in range(self._shadow_blur // 2):
            alpha = int(self._shadow_color.alpha() * (1 - i / (self._shadow_blur // 2)) * 0.4)
            color = QColor(self._shadow_color.red(), self._shadow_color.green(), 
                          self._shadow_color.blue(), alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(inner_shadow_rect.adjusted(i, i, -i, -i), self._border_radius, self._border_radius)
        
        # 绘制玻璃背景
        painter.setBrush(QBrush(self._glass_color))
        painter.setPen(QPen(self._border_color, 1))
        painter.drawRoundedRect(self.rect().adjusted(5, 5, -5, -5), self._border_radius, self._border_radius)
        
        # 绘制多层次高光效果，增加玻璃质感
        # 主高光 - 从左上到右下的线性渐变
        highlight_rect = QRect(self.rect().left() + 10, self.rect().top() + 10, 
                              self.rect().width() - 20, self.rect().height() // 3)
        main_gradient = QLinearGradient(highlight_rect.topLeft(), highlight_rect.bottomLeft())
        main_gradient.setColorAt(0, QColor(255, 255, 255, self._highlight_color.alpha()))
        main_gradient.setColorAt(0.7, QColor(255, 255, 255, self._highlight_color.alpha() // 2))
        main_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(main_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(highlight_rect, self._border_radius, self._border_radius)
        
        # 绘制边缘高光，增强玻璃边缘的立体感
        edge_highlight_width = 3
        edge_rect = self.rect().adjusted(5, 5, -5, -5)
        
        # 创建边缘高光的渐变
        edge_gradient = QLinearGradient(edge_rect.topLeft(), edge_rect.topRight())
        edge_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        edge_gradient.setColorAt(0.2, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(0.5, QColor(255, 255, 255, 120))
        edge_gradient.setColorAt(0.8, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(QPen(edge_gradient, edge_highlight_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(edge_rect, self._border_radius, self._border_radius)
        
        painter.end()
    
    def resizeEvent(self, event):
        """窗口大小改变时需要更新缓存"""
        self._needs_background_update = True
        super().resizeEvent(event)
    
    def setGlassColor(self, color):
        self._glass_color = color
        self._needs_background_update = True
        self.update()
    
    def setBorderColor(self, color):
        self._border_color = color
        self._needs_background_update = True
        self.update()
    
    def setBorderRadius(self, radius):
        self._border_radius = radius
        self._needs_background_update = True
        self.update()
    
    def setTransparency(self, transparency):
        """设置玻璃效果透明度"""
        # 更新颜色的透明度
        self._glass_color.setAlpha(transparency)
        self._border_color.setAlpha(max(50, transparency // 2))
        self._shadow_color.setAlpha(max(30, transparency // 3))
        self._highlight_color.setAlpha(min(255, transparency - 30))
        
        # 标记需要更新背景
        self._needs_background_update = True
        self.update()

class ImagePreviewWidget(QListWidget):
    """图片预览部件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setMovement(QListWidget.Static)
        self.setResizeMode(QListWidget.Adjust)
        self.setUniformItemSizes(True)
        self.setWrapping(True)
        self.setSpacing(10)
        self.setIconSize(QSize(200, 200))
        self.setTextElideMode(Qt.ElideRight)
        self.setWordWrap(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 设置样式
        self.setStyleSheet("""
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
        self.itemDoubleClicked.connect(self.showFullImage)
        
    def showFullImage(self, item):
        """显示完整图片"""
        if item and item.data(Qt.UserRole):
            file_path = item.data(Qt.UserRole)
            try:
                # 创建一个对话框显示完整图片
                dialog = QDialog(self)
                dialog.setWindowTitle("图片预览")
                
                layout = QVBoxLayout(dialog)
                
                # 创建图片标签
                label = QLabel()
                pixmap = QPixmap(file_path)
                
                # 根据图片分辨率实际调整缩放75%
                scaled_width = int(pixmap.width() * 0.75)
                scaled_height = int(pixmap.height() * 0.75)
                
                # 获取屏幕尺寸，确保对话框不会超出屏幕
                screen = QApplication.desktop().screenGeometry()
                max_width = int(screen.width() * 0.9)
                max_height = int(screen.height() * 0.9)
                
                # 限制对话框最大尺寸
                dialog_width = min(scaled_width, max_width)
                dialog_height = min(scaled_height, max_height)
                
                # 设置对话框大小
                dialog.setMinimumSize(400, 300)  # 设置最小尺寸
                dialog.resize(dialog_width, dialog_height)
                
                # 缩放图片以适应对话框大小
                if pixmap.width() > dialog.width() or pixmap.height() > dialog.height():
                    pixmap = pixmap.scaled(dialog.width() - 20, dialog.height() - 20, 
                                          Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                
                layout.addWidget(label)
                
                # 添加关闭按钮
                close_button = QPushButton("关闭")
                close_button.clicked.connect(dialog.accept)
                layout.addWidget(close_button)
                
                dialog.exec_()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法显示图片: {str(e)}")
    
    def addImage(self, file_path, pixmap):
        """添加图片到预览列表"""
        # 获取当前设置的预览图片大小
        preview_size = "中 (200x200)"  # 默认大小
        if hasattr(self.parent(), 'settings'):
            preview_size = self.parent().settings.get("preview_size", "中 (200x200)")
        
        # 根据设置确定图标大小
        if preview_size == "小 (150x150)":
            icon_size = QSize(150, 150)
        elif preview_size == "中 (200x200)":
            icon_size = QSize(200, 200)
        elif preview_size == "大 (300x300)":
            icon_size = QSize(300, 300)
        else:
            icon_size = QSize(200, 200)  # 默认大小
        
        # 统一缩放图片到指定大小，保持宽高比
        scaled_pixmap = pixmap.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 创建列表项
        item = QListWidgetItem()
        
        # 为图片添加圆角效果
        rounded_pixmap = QPixmap(scaled_pixmap.size())
        rounded_pixmap.fill(Qt.transparent)
        
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, scaled_pixmap.width(), scaled_pixmap.height(), 15, 15)
        
        # 使用路径裁剪
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()
        
        # 设置图标
        icon = QIcon(rounded_pixmap)
        item.setIcon(icon)
        
        # 设置文本为文件名
        filename = os.path.basename(file_path)
        item.setText(filename)
        
        # 存储文件路径
        item.setData(Qt.UserRole, file_path)
        
        # 添加到列表
        self.addItem(item)
        
        # 滚动到底部
        self.scrollToBottom()

class HoverableComboBox(QComboBox):
    """下拉框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._normal_background = QColor(255, 255, 255, 180)
        self._current_background = QColor(self._normal_background)
        self._updateStylesheet()
        
    def _updateStylesheet(self):
        """更新样式表"""
        # 获取当前主题
        theme = "light"  # 默认浅色主题
        if hasattr(self.parent(), 'settings'):
            theme_setting = self.parent().settings.get("theme", "浅色")
            if theme_setting == "深色":
                theme = "dark"
        
        # 根据主题设置基础样式
        if theme == "dark":
            text_color = "#FFFFFF"
            border_color = "#3F3F46"
            dropdown_arrow_color = "#FFFFFF"
            current_bg = "rgba(45, 45, 48, 180)"
        else:
            text_color = "#333333"
            border_color = "#CCCCCC"
            dropdown_arrow_color = "#333333"
            current_bg = "rgba(255, 255, 255, 180)"
        
        # 构建样式表
        stylesheet = f"""
            QComboBox {{
                background-color: {current_bg};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
                color: {text_color};
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {dropdown_arrow_color};
            }}
            QComboBox QAbstractItemView {{
                background-color: {current_bg};
                border: 1px solid {border_color};
                border-radius: 5px;
                color: {text_color};
                selection-background-color: #007ACC;
                selection-color: white;
            }}
        """
        
        self.setStyleSheet(stylesheet)
    
    def setTransparency(self, transparency):
        """设置透明度"""
        self._normal_background.setAlpha(transparency)
        self._updateStylesheet()

class HoverableLineEdit(QLineEdit):
    """带有悬浮效果的输入框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._normal_background = QColor(255, 255, 255, 180)
        self._hover_background = QColor(255, 255, 255, 220)
        self._focus_background = QColor(255, 255, 255, 240)
        self._current_background = QColor(self._normal_background)
        self._is_hovered = False
        self._is_focused = False
        self._hover_animation_progress = 0.0
        self._hover_animation_timer = None
        self._hover_animation_duration = 150  # 减少动画持续时间，提高响应速度
        self._hover_start_time = 0
        self._last_hover_time = 0  # 上次悬浮时间，用于防止频繁触发动画
        self._updateStylesheet()
        
    def enterEvent(self, event):
        """鼠标进入事件 - 优化动画触发"""
        current_time = self._hover_animation_timer if self._hover_animation_timer else 0
        if not self._is_hovered and current_time - self._last_hover_time > 100:  # 增加阈值到100ms
            self._is_hovered = True
            self._last_hover_time = current_time
            self._startHoverAnimation()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 优化动画触发"""
        current_time = self._hover_animation_timer if self._hover_animation_timer else 0
        if self._is_hovered and current_time - self._last_hover_time > 100:  # 增加阈值到100ms
            self._is_hovered = False
            self._last_hover_time = current_time
            self._startHoverAnimation()
        super().leaveEvent(event)
    
    def focusInEvent(self, event):
        """焦点进入事件 - 优化动画触发"""
        current_time = self._hover_animation_timer if self._hover_animation_timer else 0
        if not self._is_focused and current_time - self._last_hover_time > 100:  # 增加阈值到100ms
            self._is_focused = True
            self._last_hover_time = current_time
            self._startHoverAnimation()
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        """焦点离开事件 - 优化动画触发"""
        current_time = self._hover_animation_timer if self._hover_animation_timer else 0
        if self._is_focused and current_time - self._last_hover_time > 100:  # 增加阈值到100ms
            self._is_focused = False
            self._last_hover_time = current_time
            self._startHoverAnimation()
        super().focusOutEvent(event)
    
    def _startHoverAnimation(self):
        """开始悬浮动画"""
        self._hover_animation_progress = 0.0
        self._hover_start_time = 0
        
        # 如果已有定时器，先停止
        if self._hover_animation_timer:
            self.killTimer(self._hover_animation_timer)
        
        # 启动新的定时器
        self._hover_animation_timer = self.startTimer(16)  # 约60fps
    
    def _updateHoverAnimation(self):
        """更新悬浮动画进度"""
        if self._hover_start_time == 0:
            self._hover_start_time = self._hover_animation_timer
        
        elapsed = self._hover_animation_timer - self._hover_start_time
        self._hover_animation_progress = min(1.0, elapsed / self._hover_animation_duration)
        
        # 使用三次贝塞尔缓动函数使动画更自然
        eased_progress = self._easeInOutCubic(self._hover_animation_progress)
        
        # 确定目标颜色
        if self._is_focused:
            target_color = self._focus_background
        elif self._is_hovered:
            target_color = self._hover_background
        else:
            target_color = self._normal_background
        
        # 保存之前的颜色值用于比较
        prev_color = self._current_background
        
        # 更新背景颜色
        r = int(self._current_background.red() + 
               (target_color.red() - self._current_background.red()) * 
               eased_progress)
        g = int(self._current_background.green() + 
               (target_color.green() - self._current_background.green()) * 
               eased_progress)
        b = int(self._current_background.blue() + 
               (target_color.blue() - self._current_background.blue()) * 
               eased_progress)
        a = int(self._current_background.alpha() + 
               (target_color.alpha() - self._current_background.alpha()) * 
               eased_progress)
        self._current_background = QColor(r, g, b, a)
        
        # 只有当颜色变化超过阈值时才更新样式，减少不必要的重绘
        color_changed = (abs(prev_color.red() - self._current_background.red()) > 5 or
                        abs(prev_color.green() - self._current_background.green()) > 5 or
                        abs(prev_color.blue() - self._current_background.blue()) > 5 or
                        abs(prev_color.alpha() - self._current_background.alpha()) > 5)
        
        if color_changed or self._hover_animation_progress >= 1.0:
            # 更新样式
            self._updateStylesheet()
        
        # 动画完成
        if self._hover_animation_progress >= 1.0:
            self._current_background = QColor(target_color)
            self.killTimer(self._hover_animation_timer)
            self._hover_animation_timer = None
    
    def _easeInOutCubic(self, t):
        """三次贝塞尔缓动函数，使动画更加自然"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def _updateStylesheet(self):
        """更新样式表"""
        # 获取当前主题
        theme = "light"  # 默认浅色主题
        if hasattr(self.parent(), 'settings'):
            theme_setting = self.parent().settings.get("theme", "浅色")
            if theme_setting == "深色":
                theme = "dark"
        
        # 根据主题设置基础样式
        if theme == "dark":
            text_color = "#FFFFFF"
            border_color = "#3F3F46"
            focus_border_color = "#007ACC"
        else:
            text_color = "#333333"
            border_color = "#CCCCCC"
            focus_border_color = "#007ACC"
        
        # 设置当前背景颜色
        current_bg = f"rgba({self._current_background.red()}, {self._current_background.green()}, {self._current_background.blue()}, {self._current_background.alpha()})"
        
        # 构建样式表
        stylesheet = f"""
            QLineEdit {{
                background-color: {current_bg};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
                color: {text_color};
            }}
            QLineEdit:focus {{
                border: 1px solid {focus_border_color};
            }}
        """
        
        self.setStyleSheet(stylesheet)
    
    def timerEvent(self, event):
        """定时器事件"""
        if event.timerId() == self._hover_animation_timer:
            self._updateHoverAnimation()
    
    def setTransparency(self, transparency):
        """设置透明度"""
        self._normal_background.setAlpha(transparency)
        self._hover_background.setAlpha(min(255, transparency + 40))
        self._focus_background.setAlpha(min(255, transparency + 60))
        self._updateStylesheet()

class GlassButton(QPushButton):
    """液态玻璃效果的按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._glass_color = QColor(255, 255, 255, 180)
        self._hover_color = QColor(255, 255, 255, 220)
        self._pressed_color = QColor(255, 255, 255, 150)
        self._text_color = QColor(50, 50, 50)
        self._border_radius = 15
        self._is_hovered = False
        self._is_pressed = False
        self._current_color = self._glass_color  # 当前颜色
        self._target_color = self._glass_color  # 目标颜色
        self._cached_pixmap = None  # 缓存按钮图像
        self._needs_update = True  # 是否需要更新缓存
        self._animation_progress = 0.0  # 动画进度 (0.0 到 1.0)
        self._animation_timer = None  # 动画定时器
        self._animation_duration = 200  # 增加动画持续时间，使效果更流畅
        self._animation_start_time = 0  # 动画开始时间
        self._last_hover_time = 0  # 上次悬浮时间，用于防止频繁触发动画
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        
        # 波纹效果相关
        self._ripple_animation = False  # 是否有波纹动画
        self._ripple_progress = 0.0  # 波纹动画进度
        self._ripple_timer = None  # 波纹动画定时器
        self._ripple_duration = 400  # 增加波纹动画持续时间，使效果更自然
        self._ripple_start_time = 0  # 波纹动画开始时间
        self._ripple_center = QPoint()  # 波纹中心点
        self._ripple_radius = 0  # 波纹半径
        self._ripple_max_radius = 0  # 波纹最大半径
        
        # 光效属性
        self._light_source_pos = QPoint(int(0.3 * 100), int(0.3 * 100))  # 光源位置（相对位置，存储为整数）
        self._ambient_light = 0.6  # 环境光强度
        self._specular_strength = 0.8  # 镜面反射强度
        self._normal_shadow_blur = 15  # 正常状态阴影模糊度
        self._hover_shadow_blur = 20  # 悬浮状态阴影模糊度
        self._normal_shadow_color = QColor(0, 0, 0, 100)  # 正常状态阴影颜色
        self._hover_shadow_color = QColor(0, 0, 0, 150)  # 悬浮状态阴影颜色
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 如果需要更新缓存或大小改变
        if self._needs_update or self._cached_pixmap is None or self._cached_pixmap.size() != self.size():
            self._updateCache()
            self._needs_update = False
        
        # 绘制缓存的按钮
        if self._cached_pixmap:
            painter.drawPixmap(0, 0, self._cached_pixmap)
        
        # 绘制波纹效果
        if self._ripple_animation and self._ripple_progress > 0:
            # 计算当前波纹半径
            current_radius = int(self._ripple_max_radius * self._ripple_progress)
            
            # 计算波纹透明度（随着扩散逐渐消失）
            ripple_alpha = int(150 * (1 - self._ripple_progress))
            
            # 绘制多层波纹，增强视觉效果
            for i in range(3):
                # 每层波纹的半径和透明度略有不同
                layer_radius = current_radius - i * 5
                layer_alpha = ripple_alpha // (i + 1)
                
                if layer_radius > 0:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(255, 255, 255, layer_alpha))
                    painter.drawEllipse(
                        self._ripple_center.x() - layer_radius,
                        self._ripple_center.y() - layer_radius,
                        layer_radius * 2,
                        layer_radius * 2
                    )
        
        # 绘制文本（在波纹效果之后，确保文本在最上层）
        painter.setPen(QPen(self._text_color))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        
        # 添加文本阴影效果，增强可读性
        shadow_offset = 1
        painter.setPen(QPen(QColor(0, 0, 0, 50)))
        painter.drawText(
            self.rect().adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset), 
            Qt.AlignCenter, 
            self.text()
        )
        
        # 绘制主文本
        painter.setPen(QPen(self._text_color))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        
        # 如果有动画在进行，继续更新
        if self._animation_timer and self._animation_progress < 1.0:
            self._updateAnimation()
        
        # 如果有波纹动画在进行，继续更新
        if self._ripple_timer and self._ripple_progress < 1.0:
            self._updateRippleAnimation()
    
    def _updateCache(self):
        """更新按钮缓存"""
        # 创建与按钮大小相同的缓存图像
        self._cached_pixmap = QPixmap(self.size())
        self._cached_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self._cached_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 使用动画进度进行颜色插值
        current_color = self._interpolateColor(self._current_color, self._target_color, self._animation_progress)
        
        # 根据悬浮状态选择阴影参数
        current_shadow_blur = self._normal_shadow_blur
        current_shadow_color = self._normal_shadow_color
        
        if self._is_hovered:
            # 在悬浮状态下，根据动画进度插值阴影参数
            progress = self._easeInOutCubic(self._animation_progress)
            current_shadow_blur = int(
                self._normal_shadow_blur + 
                (self._hover_shadow_blur - self._normal_shadow_blur) * 
                progress
            )
            
            # 插值阴影颜色
            r = int(self._normal_shadow_color.red() + 
                   (self._hover_shadow_color.red() - self._normal_shadow_color.red()) * 
                   progress)
            g = int(self._normal_shadow_color.green() + 
                   (self._hover_shadow_color.green() - self._normal_shadow_color.green()) * 
                   progress)
            b = int(self._normal_shadow_color.blue() + 
                   (self._hover_shadow_color.blue() - self._normal_shadow_color.blue()) * 
                   progress)
            a = int(self._normal_shadow_color.alpha() + 
                   (self._hover_shadow_color.alpha() - self._normal_shadow_color.alpha()) * 
                   progress)
            current_shadow_color = QColor(r, g, b, a)
        
        # 绘制多层阴影，增加深度感
        shadow_rect = self.rect().adjusted(5, 5, -5, -5)
        painter.setPen(Qt.NoPen)
        
        # 外层阴影 - 更模糊，更扩散
        for i in range(current_shadow_blur):
            alpha = int(current_shadow_color.alpha() * (1 - i / current_shadow_blur) * 0.6)
            color = QColor(current_shadow_color.red(), current_shadow_color.green(), 
                          current_shadow_color.blue(), alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(shadow_rect.adjusted(i, i, -i, -i), self._border_radius, self._border_radius)
        
        # 内层阴影 - 更锐利，更集中
        inner_shadow_rect = self.rect().adjusted(3, 3, -3, -3)
        for i in range(current_shadow_blur // 2):
            alpha = int(current_shadow_color.alpha() * (1 - i / (current_shadow_blur // 2)) * 0.4)
            color = QColor(current_shadow_color.red(), current_shadow_color.green(), 
                          current_shadow_color.blue(), alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(inner_shadow_rect.adjusted(i, i, -i, -i), self._border_radius, self._border_radius)
        
        # 绘制玻璃背景
        painter.setBrush(QBrush(current_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
        
        # 绘制多层次高光效果，增加玻璃质感
        # 主高光 - 从左上到右下的线性渐变
        highlight_rect = QRect(self.rect().left() + 5, self.rect().top() + 5, 
                              self.rect().width() - 10, self.rect().height() // 3)
        main_gradient = QLinearGradient(highlight_rect.topLeft(), highlight_rect.bottomLeft())
        main_gradient.setColorAt(0, QColor(255, 255, 255, 100))
        main_gradient.setColorAt(0.7, QColor(255, 255, 255, 50))
        main_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(main_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(highlight_rect, self._border_radius, self._border_radius)
        
        # 次级高光 - 径向渐变，模拟点光源反射
        highlight_radius = min(self.rect().width(), self.rect().height()) // 4
        highlight_center = QPoint(
            self.rect().left() + int(self.rect().width() * self._light_source_pos.x() / 100),
            self.rect().top() + int(self.rect().height() * self._light_source_pos.y() / 100)
        )
        
        radial_highlight = QRadialGradient(highlight_center, highlight_radius)
        radial_highlight.setColorAt(0, QColor(255, 255, 255, int(100 * self._specular_strength)))
        radial_highlight.setColorAt(0.5, QColor(255, 255, 255, int(50 * self._specular_strength)))
        radial_highlight.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(radial_highlight))
        painter.drawEllipse(highlight_center.x() - highlight_radius, 
                           highlight_center.y() - highlight_radius,
                           highlight_radius * 2, highlight_radius * 2)
        
        # 绘制边缘高光，增强玻璃边缘的立体感
        edge_highlight_width = 2
        edge_rect = self.rect().adjusted(2, 2, -2, -2)
        
        # 创建边缘高光的渐变
        edge_gradient = QLinearGradient(edge_rect.topLeft(), edge_rect.topRight())
        edge_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        edge_gradient.setColorAt(0.2, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(0.5, QColor(255, 255, 255, 120))
        edge_gradient.setColorAt(0.8, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(QPen(edge_gradient, edge_highlight_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(edge_rect, self._border_radius, self._border_radius)
        
        painter.end()
    
    def _interpolateColor(self, start_color, end_color, progress):
        """在两种颜色之间进行插值，使用改进的缓动函数"""
        # 使用三次贝塞尔缓动函数，使动画更加自然
        eased_progress = self._easeInOutCubic(progress)
        
        r = int(start_color.red() + (end_color.red() - start_color.red()) * eased_progress)
        g = int(start_color.green() + (end_color.green() - start_color.green()) * eased_progress)
        b = int(start_color.blue() + (end_color.blue() - start_color.blue()) * eased_progress)
        a = int(start_color.alpha() + (end_color.alpha() - start_color.alpha()) * eased_progress)
        return QColor(r, g, b, a)
    
    def _easeInOutCubic(self, t):
        """三次贝塞尔缓动函数，使动画更加自然"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def _startAnimation(self, target_color):
        """开始颜色过渡动画"""
        self._target_color = target_color
        self._animation_progress = 0.0
        self._animation_start_time = 0
        
        # 如果已有定时器，先停止
        if self._animation_timer:
            self.killTimer(self._animation_timer)
        
        # 启动新的定时器
        self._animation_timer = self.startTimer(16)  # 约60fps
    
    def _updateAnimation(self):
        """更新动画进度"""
        if self._animation_start_time == 0:
            self._animation_start_time = self._animation_timer
        
        elapsed = self._animation_timer - self._animation_start_time
        self._animation_progress = min(1.0, elapsed / self._animation_duration)
        
        # 计算当前颜色
        current_color = self._interpolateColor(self._current_color, self._target_color, self._animation_progress)
        
        # 只有当颜色变化超过阈值时才更新缓存并重绘，减少不必要的重绘
        color_changed = (abs(self._current_color.red() - current_color.red()) > 5 or
                        abs(self._current_color.green() - current_color.green()) > 5 or
                        abs(self._current_color.blue() - current_color.blue()) > 5 or
                        abs(self._current_color.alpha() - current_color.alpha()) > 5)
        
        if color_changed or self._animation_progress >= 1.0:
            # 更新缓存并重绘
            self._needs_update = True
            self.update()
        
        # 动画完成
        if self._animation_progress >= 1.0:
            self._current_color = QColor(self._target_color)
            self.killTimer(self._animation_timer)
            self._animation_timer = None
    
    def timerEvent(self, event):
        """定时器事件"""
        if event.timerId() == self._animation_timer:
            self._updateAnimation()
        elif event.timerId() == self._ripple_timer:
            self._updateRippleAnimation()
    
    def _startRippleAnimation(self, pos):
        """开始波纹动画"""
        self._ripple_animation = True
        self._ripple_progress = 0.0
        self._ripple_start_time = 0
        self._ripple_center = pos
        
        # 计算最大波纹半径（从点击点到按钮最远角的距离）
        dx = max(pos.x(), self.width() - pos.x())
        dy = max(pos.y(), self.height() - pos.y())
        self._ripple_max_radius = int((dx * dx + dy * dy) ** 0.5)
        
        # 如果已有定时器，先停止
        if self._ripple_timer:
            self.killTimer(self._ripple_timer)
        
        # 启动新的定时器
        self._ripple_timer = self.startTimer(16)  # 约60fps
    
    def _updateRippleAnimation(self):
        """更新波纹动画进度"""
        if self._ripple_start_time == 0:
            self._ripple_start_time = self._ripple_timer
        
        elapsed = self._ripple_timer - self._ripple_start_time
        self._ripple_progress = min(1.0, elapsed / self._ripple_duration)
        
        # 使用缓出函数使波纹扩散更自然
        eased_progress = self._easeOutQuad(self._ripple_progress)
        self._ripple_progress = eased_progress
        
        # 重绘
        self.update()
        
        # 动画完成
        if self._ripple_progress >= 1.0:
            self._ripple_animation = False
            self.killTimer(self._ripple_timer)
            self._ripple_timer = None
    
    def _easeOutQuad(self, t):
        """二次缓出函数"""
        return 1 - (1 - t) * (1 - t)
    
    def enterEvent(self, event):
        """鼠标进入事件 - 优化动画触发"""
        current_time = self._animation_timer if self._animation_timer else 0
        if not self._is_hovered and current_time - getattr(self, '_last_hover_time', 0) > 100:  # 增加阈值到100ms
            self._is_hovered = True
            self._last_hover_time = current_time
            if not self._is_pressed:
                self._startAnimation(self._hover_color)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 优化动画触发"""
        current_time = self._animation_timer if self._animation_timer else 0
        if self._is_hovered and current_time - getattr(self, '_last_hover_time', 0) > 100:  # 增加阈值到100ms
            self._is_hovered = False
            self._last_hover_time = current_time
            if not self._is_pressed:
                self._startAnimation(self._glass_color)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 优化动画触发"""
        current_time = self._animation_timer if self._animation_timer else 0
        if not self._is_pressed and current_time - getattr(self, '_last_hover_time', 0) > 100:  # 增加阈值到100ms
            self._is_pressed = True
            self._last_hover_time = current_time
            self._startAnimation(self._pressed_color)
            
            # 开始波纹动画
            self._startRippleAnimation(event.pos())
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 优化动画触发"""
        current_time = self._animation_timer if self._animation_timer else 0
        if self._is_pressed and current_time - getattr(self, '_last_hover_time', 0) > 100:  # 增加阈值到100ms
            self._is_pressed = False
            self._last_hover_time = current_time
            if self._is_hovered:
                self._startAnimation(self._hover_color)
            else:
                self._startAnimation(self._glass_color)
        super().mouseReleaseEvent(event)
    
    def resizeEvent(self, event):
        """按钮大小改变时需要更新缓存"""
        self._needs_update = True
        super().resizeEvent(event)
    
    def setTransparency(self, transparency):
        """设置按钮透明度"""
        # 更新所有颜色的透明度
        self._glass_color.setAlpha(transparency)
        self._hover_color.setAlpha(min(255, transparency + 40))  # 悬停时稍微增加透明度
        self._pressed_color.setAlpha(max(100, transparency - 30))  # 按下时稍微降低透明度
        
        # 如果当前没有动画，更新当前颜色
        if not self._animation_timer:
            if self._is_pressed:
                self._current_color = QColor(self._pressed_color)
            elif self._is_hovered:
                self._current_color = QColor(self._hover_color)
            else:
                self._current_color = QColor(self._glass_color)
        
        # 标记需要更新缓存
        self._needs_update = True
        self.update()

class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self.initUI()
        self.loadSettings()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 创建玻璃效果容器
        glass_container = GlassEffectWidget(self)
        glass_layout = QVBoxLayout(glass_container)
        glass_layout.setContentsMargins(20, 20, 20, 20)
        glass_layout.setSpacing(15)
        
        # 下载设置组
        download_group = QGroupBox("下载设置")
        download_layout = QFormLayout()
        
        # API密钥
        self.api_key_edit = HoverableLineEdit()
        download_layout.addRow("API密钥:", self.api_key_edit)
        
        # 每页图片数
        self.images_per_page_spin = QSpinBox()
        self.images_per_page_spin.setRange(1, 100)
        self.images_per_page_spin.setValue(24)
        download_layout.addRow("每页图片数:", self.images_per_page_spin)
        
        # 下载超时时间
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" 秒")
        download_layout.addRow("下载超时:", self.timeout_spin)
        
        # 并发下载数
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        download_layout.addRow("并发下载数:", self.concurrent_spin)
        
        download_group.setLayout(download_layout)
        glass_layout.addWidget(download_group)
        
        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout()
        
        self.theme_combo = HoverableComboBox()
        self.theme_combo.addItems(["浅色", "深色", "自动"])
        ui_layout.addRow("主题:", self.theme_combo)
        
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(100, 255)
        self.transparency_slider.setValue(200)
        self.transparency_label = QLabel("200")
        
        transparency_layout = QHBoxLayout()
        transparency_layout.addWidget(self.transparency_slider)
        transparency_layout.addWidget(self.transparency_label)
        
        self.transparency_slider.valueChanged.connect(lambda v: self.transparency_label.setText(str(v)))
        ui_layout.addRow("玻璃透明度:", transparency_layout)
        
        # 预览图片大小
        self.preview_size_combo = HoverableComboBox()
        self.preview_size_combo.addItems(["小 (150x150)", "中 (200x200)", "大 (300x300)"])
        ui_layout.addRow("预览图片大小:", self.preview_size_combo)
        
        ui_group.setLayout(ui_layout)
        glass_layout.addWidget(ui_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        ok_btn = GlassButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = GlassButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        glass_layout.addLayout(button_layout)
        layout.addWidget(glass_container)
        self.setLayout(layout)
    
    def loadSettings(self):
        # 加载设置
        self.api_key_edit.setText(self.settings.get("api_key", "dws2O4u6Agr4v1CC92mH90H1T49QSuTM"))
        self.theme_combo.setCurrentText(self.settings.get("theme", "浅色"))
        self.transparency_slider.setValue(self.settings.get("glass_transparency", 200))
        self.images_per_page_spin.setValue(self.settings.get("images_per_page", 24))
        self.timeout_spin.setValue(self.settings.get("download_timeout", 30))
        self.concurrent_spin.setValue(self.settings.get("concurrent_downloads", 3))
        
        # 加载预览图片大小设置
        preview_size = self.settings.get("preview_size", "中 (200x200)")
        self.preview_size_combo.setCurrentText(preview_size)
    
    def getSettings(self):
        # 返回设置
        settings = {
            "api_key": self.api_key_edit.text(),
            "theme": self.theme_combo.currentText(),
            "glass_transparency": self.transparency_slider.value(),
            "images_per_page": self.images_per_page_spin.value(),
            "download_timeout": self.timeout_spin.value(),
            "concurrent_downloads": self.concurrent_spin.value(),
            "preview_size": self.preview_size_combo.currentText()
        }
            
        return settings

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        print("正在初始化主窗口...")
        super().__init__()
        print("设置窗口标题和大小...")
        self.setWindowTitle("Wallhaven壁纸下载器")
        
        # 设置窗口尺寸为2580×1440分辨率
        self.setMinimumSize(2580, 1440)
        self.resize(2580, 1440)
        
        # 设置窗口图标
        print("设置窗口图标...")
        # self.setWindowIcon(QIcon(resource_path("resources/icon.png")))
        
        # 初始化设置
        print("加载设置...")
        self.settings = self.loadSettings()
        
        # 初始化UI
        print("初始化UI...")
        self.initUI()
        
        # 初始化变量
        print("初始化变量...")
        self.download_thread = None
        self.base_url = ""
        
        # 应用主题
        print("应用主题...")
        self.applyTheme()
        
        print("主窗口初始化完成")
    
    def loadSettings(self):
        """加载设置"""
        settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")
        print(f"[日志] 开始加载设置，文件路径: {settings_file}")
        
        # 默认设置
        default_settings = {
            "api_key": "dws2O4u6Agr4v1CC92mH90H1T49QSuTM",
            "theme": "浅色",
            "glass_transparency": 200,
            "images_per_page": 24,
            "download_timeout": 30,
            "concurrent_downloads": 3,
            "preview_size": "中 (200x200)",
            "download_dir": os.path.join(os.path.expanduser("~"), "Pictures", "Wallhaven"),
            # 下载设置相关
            "download_method": "latest",  # latest, category, search
            "category": "all",
            "purity": "sfw",
            "search_query": "",
            "page_count": 1
        }
        
        # 如果设置文件存在，加载设置
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    print(f"[日志] 成功从文件加载设置: {settings}")
                
                # 合并默认设置和加载的设置
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                        print(f"[日志] 添加缺失的默认设置: {key} = {value}")
                
                print(f"[日志] 最终设置: {settings}")
                return settings
            except Exception as e:
                print(f"[日志] 加载设置失败: {e}")
                return default_settings
        else:
            # 如果设置文件不存在，创建默认设置文件
            print(f"[日志] 设置文件不存在，创建默认设置文件")
            try:
                os.makedirs(os.path.dirname(settings_file), exist_ok=True)
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4, ensure_ascii=False)
                print(f"[日志] 成功创建默认设置文件")
            except Exception as e:
                print(f"[日志] 创建设置文件失败: {e}")
            
            return default_settings
    
    def saveSettings(self):
        """保存设置"""
        settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")
        print(f"[日志] 开始保存设置，文件路径: {settings_file}")
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            print(f"[日志] 成功保存设置: {self.settings}")
        except Exception as e:
            print(f"[日志] 保存设置失败: {e}")
    
    def applyTheme(self):
        """应用主题"""
        print(f"[日志] 开始应用主题")
        theme = self.settings.get("theme", "浅色")
        print(f"[日志] 当前主题: {theme}")
        
        if theme == "深色":
            # 设置深色主题
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                }
            """)
            print(f"[日志] 已应用深色主题")
        else:
            # 设置浅色主题
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #F0F0F0;
                    color: #333333;
                }
            """)
            print(f"[日志] 已应用浅色主题")
        
        # 应用透明度设置
        transparency = self.settings.get("glass_transparency", 200)
        print(f"[日志] 玻璃透明度: {transparency}")
        
        # 更新所有玻璃效果部件的透明度
        glass_widgets = self.findChildren(GlassEffectWidget)
        print(f"[日志] 找到 {len(glass_widgets)} 个玻璃效果部件")
        for widget in glass_widgets:
            widget.setTransparency(transparency)
        
        # 更新所有按钮的透明度
        buttons = self.findChildren(GlassButton)
        print(f"[日志] 找到 {len(buttons)} 个按钮")
        for widget in buttons:
            widget.setTransparency(transparency)
        
        # 更新所有输入框的透明度
        line_edits = self.findChildren(HoverableLineEdit)
        print(f"[日志] 找到 {len(line_edits)} 个输入框")
        for widget in line_edits:
            widget.setTransparency(transparency)
        
        # 更新所有下拉框的透明度
        combo_boxes = self.findChildren(HoverableComboBox)
        print(f"[日志] 找到 {len(combo_boxes)} 个下拉框")
        for widget in combo_boxes:
            widget.setTransparency(transparency)
        
        print(f"[日志] 主题应用完成")
    
    def initUI(self):
        print("[日志] 开始初始化UI...")
        # 创建中央部件
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 创建主内容区域
        print("[日志] 创建主内容区域...")
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # 左侧面板 - 下载设置
        print("[日志] 创建左侧面板...")
        left_panel = GlassEffectWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)
        
        # 下载设置标题
        settings_title = QLabel("下载设置")
        settings_title.setFont(QFont("", 12, QFont.Bold))
        left_layout.addWidget(settings_title)
        
        # 下载方式选择
        download_method_group = QGroupBox("下载方式")
        download_method_layout = QVBoxLayout()
        
        # 类别下载
        self.category_radio = QRadioButton("从指定类别下载")
        download_method_layout.addWidget(self.category_radio)
        
        # 最新下载
        self.latest_radio = QRadioButton("下载最新壁纸")
        self.latest_radio.setChecked(True)
        download_method_layout.addWidget(self.latest_radio)
        
        # 搜索下载
        self.search_radio = QRadioButton("从搜索下载")
        download_method_layout.addWidget(self.search_radio)
        
        download_method_group.setLayout(download_method_layout)
        left_layout.addWidget(download_method_group)
        
        # 类别设置
        self.category_group = QGroupBox("类别设置")
        category_layout = QFormLayout()
        
        # 类别选择
        self.category_combo = HoverableComboBox()
        self.category_combo.addItems(["all", "general", "anime", "people", "ga", "gp"])
        category_layout.addRow("类别:", self.category_combo)
        
        # 纯度选择
        self.purity_combo = HoverableComboBox()
        self.purity_combo.addItems(["sfw", "sketchy", "nsfw", "ws", "wn", "sn", "all"])
        category_layout.addRow("纯度:", self.purity_combo)
        
        self.category_group.setLayout(category_layout)
        self.category_group.setEnabled(False)
        left_layout.addWidget(self.category_group)
        
        # 搜索设置
        self.search_group = QGroupBox("搜索设置")
        search_layout = QFormLayout()
        
        # 搜索关键词
        self.search_edit = HoverableLineEdit()
        search_layout.addRow("搜索关键词:", self.search_edit)
        
        self.search_group.setLayout(search_layout)
        self.search_group.setEnabled(False)
        left_layout.addWidget(self.search_group)
        
        # 下载设置
        download_settings_group = QGroupBox("下载设置")
        download_settings_layout = QFormLayout()
        
        # 下载页数
        self.page_count_spin = QSpinBox()
        self.page_count_spin.setRange(1, 999999)  # 设置为很大的数，表示不限页数
        self.page_count_spin.setValue(1)
        download_settings_layout.addRow("下载页数:", self.page_count_spin)
        
        # 下载目录
        download_dir_layout = QHBoxLayout()
        self.download_dir_edit = HoverableLineEdit()
        self.download_dir_edit.setText(self.settings.get("download_dir", os.path.join(os.path.expanduser("~"), "Pictures", "Wallhaven")))
        download_dir_layout.addWidget(self.download_dir_edit)
        
        browse_btn = GlassButton("浏览")
        browse_btn.clicked.connect(self.browseDownloadDir)
        download_dir_layout.addWidget(browse_btn)
        
        download_settings_layout.addRow("下载目录:", download_dir_layout)
        
        download_settings_group.setLayout(download_settings_layout)
        left_layout.addWidget(download_settings_group)
        
        # 下载按钮
        print("[日志] 创建下载按钮...")
        self.download_btn = GlassButton("开始下载")
        self.download_btn.setMinimumHeight(50)
        self.download_btn.clicked.connect(self.startDownload)
        left_layout.addWidget(self.download_btn)
        
        # 停止按钮
        self.stop_btn = GlassButton("停止下载")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.clicked.connect(self.stopDownload)
        self.stop_btn.setEnabled(False)
        left_layout.addWidget(self.stop_btn)
        
        # 进度条
        print("[日志] 创建进度条...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        left_layout.addWidget(self.status_label)
        
        # 设置按钮
        settings_btn = GlassButton("设置")
        settings_btn.clicked.connect(self.showSettings)
        left_layout.addWidget(settings_btn)
        
        # 连接单选按钮信号
        self.category_radio.toggled.connect(self.updateDownloadOptions)
        self.latest_radio.toggled.connect(self.updateDownloadOptions)
        self.search_radio.toggled.connect(self.updateDownloadOptions)
        
        # 右侧面板 - 图片预览
        print("[日志] 创建右侧面板...")
        right_panel = GlassEffectWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)
        
        # 预览标题
        preview_title = QLabel("图片预览")
        preview_title.setFont(QFont("", 12, QFont.Bold))
        right_layout.addWidget(preview_title)
        
        # 图片预览区域
        print("[日志] 创建图片预览区域...")
        self.image_preview = ImagePreviewWidget()
        right_layout.addWidget(self.image_preview)
        
        # 预览控制按钮
        preview_controls_layout = QHBoxLayout()
        
        self.clear_preview_btn = GlassButton("清除预览")
        self.clear_preview_btn.clicked.connect(self.clearPreview)
        preview_controls_layout.addWidget(self.clear_preview_btn)
        
        self.open_dir_btn = GlassButton("打开下载目录")
        self.open_dir_btn.clicked.connect(self.openDownloadDir)
        preview_controls_layout.addWidget(self.open_dir_btn)
        
        right_layout.addLayout(preview_controls_layout)
        
        # 添加左右面板到主布局
        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(right_panel, 2)
        
        main_layout.addWidget(content_widget)
        
        # 添加底部布局，用于放置退出按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()  # 添加弹性空间，使按钮靠右
        
        # 创建退出按钮
        self.exit_btn = GlassButton("退出")
        self.exit_btn.clicked.connect(self.close)  # 连接到窗口关闭事件
        bottom_layout.addWidget(self.exit_btn)
        
        main_layout.addLayout(bottom_layout)
        
        # 设置中央部件
        self.setCentralWidget(central_widget)
        
        print("[日志] UI初始化完成")
        
        # 加载下载设置
        print("[日志] 加载下载设置...")
        self.loadDownloadSettings()
    
    def updateDownloadOptions(self):
        """更新下载选项的可用状态"""
        print(f"[日志] 更新下载选项状态")
        category_enabled = self.category_radio.isChecked()
        search_enabled = self.search_radio.isChecked()
        print(f"[日志] 类别设置启用: {category_enabled}, 搜索设置启用: {search_enabled}")
        
        self.category_group.setEnabled(category_enabled)
        self.search_group.setEnabled(search_enabled)
        
        # 保存下载方式设置
        if category_enabled:
            self.settings["download_method"] = "category"
            print(f"[日志] 保存下载方式: category")
        elif search_enabled:
            self.settings["download_method"] = "search"
            print(f"[日志] 保存下载方式: search")
        else:
            self.settings["download_method"] = "latest"
            print(f"[日志] 保存下载方式: latest")
        
        # 保存设置
        self.saveSettings()
    
    def browseDownloadDir(self):
        """浏览下载目录"""
        print(f"[日志] 浏览下载目录，当前目录: {self.download_dir_edit.text()}")
        dir_path = QFileDialog.getExistingDirectory(self, "选择下载目录", self.download_dir_edit.text())
        if dir_path:
            print(f"[日志] 选择新目录: {dir_path}")
            self.download_dir_edit.setText(dir_path)
            # 保存下载目录设置
            self.settings["download_dir"] = dir_path
            print(f"[日志] 保存下载目录设置: {dir_path}")
            self.saveSettings()
        else:
            print(f"[日志] 取消选择目录")
    
    def buildBaseUrl(self):
        """构建基础URL"""
        print(f"[日志] 构建基础URL")
        api_key = self.settings.get("api_key", "dws2O4u6Agr4v1CC92mH90H1T49QSuTM")
        print(f"[日志] 使用API密钥: {api_key[:10]}...")
        
        if self.category_radio.isChecked():
            # 类别下载
            category = self.category_combo.currentText()
            purity = self.purity_combo.currentText()
            print(f"[日志] 类别下载: 类别={category}, 纯度={purity}")
            
            # 类别代码映射
            category_codes = {
                "all": "111",
                "general": "100",
                "anime": "010",
                "people": "001",
                "ga": "110",
                "gp": "101"
            }
            
            # 纯度代码映射
            purity_codes = {
                "sfw": "100",
                "sketchy": "010",
                "nsfw": "001",
                "ws": "110",
                "wn": "101",
                "sn": "011",
                "all": "111"
            }
            
            ctag = category_codes.get(category, "111")
            ptag = purity_codes.get(purity, "100")
            
            self.base_url = f"https://wallhaven.cc/api/v1/search?apikey={api_key}&categories={ctag}&purity={ptag}&page="
            print(f"[日志] 构建类别下载URL: {self.base_url}")
        
        elif self.latest_radio.isChecked():
            # 最新下载
            top_list_range = "1M"
            self.base_url = f"https://wallhaven.cc/api/v1/search?apikey={api_key}&topRange={top_list_range}&sorting=toplist&page="
            print(f"[日志] 构建最新下载URL: {self.base_url}")
        
        elif self.search_radio.isChecked():
            # 搜索下载
            query = self.search_edit.text().strip()
            print(f"[日志] 搜索下载，关键词: {query}")
            if query:
                encoded_query = urllib.parse.quote_plus(query)
                self.base_url = f"https://wallhaven.cc/api/v1/search?apikey={api_key}&q={encoded_query}&page="
                print(f"[日志] 构建搜索下载URL: {self.base_url}")
            else:
                print(f"[日志] 搜索关键词为空")
                QMessageBox.warning(self, "警告", "请输入搜索关键词")
                return False
        
        return True
    
    def startDownload(self):
        """开始下载"""
        print(f"[日志] 开始下载")
        
        if self.download_thread and self.download_thread.isRunning():
            print(f"[日志] 下载正在进行中，先停止当前下载")
            QMessageBox.warning(self, "警告", "下载正在进行中，请先停止当前下载")
            return
        
        # 保存当前下载设置
        print(f"[日志] 保存当前下载设置")
        self.saveCurrentDownloadSettings()
        
        # 构建基础URL
        if not self.buildBaseUrl():
            print(f"[日志] 构建基础URL失败")
            return
        
        # 获取下载设置
        page_count = self.page_count_spin.value()
        download_dir = self.download_dir_edit.text()
        print(f"[日志] 下载设置: 页数={page_count}, 目录={download_dir}")
        
        # 检查下载目录
        if not download_dir:
            print(f"[日志] 下载目录为空")
            QMessageBox.warning(self, "警告", "请选择下载目录")
            return
        
        # 创建下载目录
        try:
            os.makedirs(download_dir, exist_ok=True)
            print(f"[日志] 创建/确认下载目录: {download_dir}")
        except Exception as e:
            print(f"[日志] 创建下载目录失败: {e}")
            QMessageBox.critical(self, "错误", f"创建下载目录失败: {e}")
            return
        
        # 检查是否有保存的下载状态
        state_file = os.path.join(download_dir, '.download_state.json')
        resume_state = None
        
        if os.path.exists(state_file):
            print(f"[日志] 发现保存的下载状态文件: {state_file}")
            reply = QMessageBox.question(self, "恢复下载", 
                                       "发现未完成的下载任务，是否要恢复下载？",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                try:
                    with open(state_file, 'r', encoding='utf-8') as f:
                        resume_state = json.load(f)
                    print(f"[日志] 加载下载状态成功: 当前页面={resume_state.get('current_page', 1)}")
                except Exception as e:
                    print(f"[日志] 加载下载状态失败: {e}")
                    QMessageBox.warning(self, "警告", f"加载下载状态失败: {e}")
            else:
                # 删除状态文件
                try:
                    os.remove(state_file)
                    print(f"[日志] 删除下载状态文件")
                except Exception as e:
                    print(f"[日志] 删除下载状态文件失败: {e}")
        
        # 更新UI状态
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)  # 确保进度条范围是0-100
        
        if resume_state:
            self.status_label.setText("正在恢复下载...")
            print(f"[日志] 更新UI状态为恢复下载")
        else:
            self.status_label.setText("正在获取图片列表...")
            print(f"[日志] 更新UI状态为下载中")
        
        # 创建并启动下载线程
        print(f"[日志] 创建下载线程")
        # 获取并发下载数设置，优先使用恢复状态中的设置
        if resume_state and 'concurrent_downloads' in resume_state:
            concurrent_downloads = resume_state['concurrent_downloads']
            print(f"[日志] 使用恢复状态中的并发下载数: {concurrent_downloads}")
        else:
            concurrent_downloads = self.settings.get("concurrent_downloads", 3)
            print(f"[日志] 使用设置中的并发下载数: {concurrent_downloads}")
        
        self.download_thread = WallpaperDownloadThread(self.base_url, page_count, download_dir, None, resume_state, concurrent_downloads)
        self.download_thread.progress_updated.connect(self.updateProgress)
        self.download_thread.download_completed.connect(self.downloadCompleted)
        self.download_thread.download_failed.connect(self.downloadFailed)
        self.download_thread.image_downloaded.connect(self.imageDownloaded)
        self.download_thread.duplicate_detected.connect(self.onDuplicateDetected)
        self.download_thread.start()
        print(f"[日志] 下载线程已启动")
    
    def onDuplicateDetected(self, duplicate_count, total_count):
        """处理重复文件检测信号"""
        print(f"[日志] 检测到重复文件: {duplicate_count}/{total_count}")
        # 更新状态标签，显示重复文件信息
        self.status_label.setText(f"正在获取图片列表... (检测到 {duplicate_count} 个重复文件)")
    
    def stopDownload(self):
        """停止下载"""
        print(f"[日志] 停止下载")
        if self.download_thread and self.download_thread.isRunning():
            print(f"[日志] 下载线程正在运行，停止下载")
            self.download_thread.stop()
            self.download_thread.wait()
            print(f"[日志] 下载线程已停止")
            
            # 更新UI状态
            self.download_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.status_label.setText("下载已停止")
            print(f"[日志] 更新UI状态为已停止")
            
            # 显示停止后的提示信息
            QMessageBox.information(self, "下载已停止", 
                                  "下载已停止。\n您可以稍后点击'开始下载'按钮继续下载未完成的图片。")
        else:
            print(f"[日志] 没有正在运行的下载线程")
    
    def updateProgress(self, progress, filename):
        """更新下载进度"""
        print(f"[日志] 更新下载进度: {progress}%, 文件: {filename}")
        # 确保进度不超过100%
        progress = min(100, max(0, progress))
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"正在下载: {filename}")
    
    def downloadCompleted(self):
        """下载完成"""
        print(f"[日志] 下载完成")
        
        # 删除下载状态文件（如果存在）
        download_dir = self.download_dir_edit.text()
        state_file = os.path.join(download_dir, '.download_state.json')
        if os.path.exists(state_file):
            try:
                os.remove(state_file)
                print(f"[日志] 删除下载状态文件: {state_file}")
            except Exception as e:
                print(f"[日志] 删除下载状态文件失败: {e}")
        
        # 更新UI状态
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("下载完成")
        
        # 显示下载完成信息，包括重复文件数量
        if hasattr(self.download_thread, 'duplicate_images') and self.download_thread.duplicate_images > 0:
            QMessageBox.information(self, "完成", 
                                  f"壁纸下载完成！\n共检测到 {self.download_thread.duplicate_images} 个重复文件已跳过。")
        else:
            QMessageBox.information(self, "完成", "壁纸下载完成")
    
    def downloadFailed(self, error_msg):
        """下载失败"""
        print(f"[日志] 下载失败: {error_msg}")
        # 更新UI状态
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("下载失败")
        
        QMessageBox.critical(self, "错误", f"下载失败: {error_msg}")
    
    def imageDownloaded(self, file_path, pixmap):
        """图片下载完成"""
        print(f"[日志] 图片下载完成: {file_path}")
        # 添加到预览列表
        self.image_preview.addImage(file_path, pixmap)
    
    def clearPreview(self):
        """清除预览"""
        print(f"[日志] 清除预览")
        self.image_preview.clear()
    
    def openDownloadDir(self):
        """打开下载目录"""
        download_dir = self.download_dir_edit.text()
        print(f"[日志] 打开下载目录: {download_dir}")
        if download_dir and os.path.exists(download_dir):
            import subprocess
            if sys.platform == 'win32':
                subprocess.Popen(['explorer', os.path.normpath(download_dir)])
                print(f"[日志] 在Windows系统中打开目录")
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', download_dir])
                print(f"[日志] 在macOS系统中打开目录")
            else:
                subprocess.Popen(['xdg-open', download_dir])
                print(f"[日志] 在Linux系统中打开目录")
        else:
            print(f"[日志] 下载目录不存在: {download_dir}")
            QMessageBox.warning(self, "警告", f"下载目录不存在: {download_dir}")
    
    def showSettings(self):
        """显示设置对话框"""
        print(f"[日志] 显示设置对话框")
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            print(f"[日志] 用户确认设置")
            # 获取新设置
            new_settings = dialog.getSettings()
            print(f"[日志] 新设置: {new_settings}")
            
            # 更新设置
            self.settings.update(new_settings)
            
            # 保存设置
            self.saveSettings()
            
            # 应用主题
            self.applyTheme()
            
            # 更新预览图片大小
            preview_size = self.settings.get("preview_size", "中 (200x200)")
            if preview_size == "小 (150x150)":
                self.image_preview.setIconSize(QSize(150, 150))
            elif preview_size == "中 (200x200)":
                self.image_preview.setIconSize(QSize(200, 200))
            elif preview_size == "大 (300x300)":
                self.image_preview.setIconSize(QSize(300, 300))
            print(f"[日志] 更新预览图片大小: {preview_size}")
        else:
            print(f"[日志] 用户取消设置")
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        print(f"[日志] 关闭窗口事件")
        # 如果有下载正在进行，询问是否停止
        if self.download_thread and self.download_thread.isRunning():
            print(f"[日志] 下载正在进行中，询问用户")
            reply = QMessageBox.question(self, "确认", "下载正在进行中，是否停止并退出？",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                print(f"[日志] 用户选择停止下载并退出")
                # 停止下载线程
                self.download_thread.stop()
                self.download_thread.wait(5000)  # 等待最多5秒
                
                # 如果线程仍在运行，强制终止
                if self.download_thread.isRunning():
                    print(f"[日志] 下载线程未正常停止，强制终止")
                    self.download_thread.terminate()
                    self.download_thread.wait(2000)  # 再等待2秒
                
                # 清理资源
                self.download_thread = None
                
                # 确保所有子进程都被终止
                try:
                    import psutil
                    current_process = psutil.Process()
                    children = current_process.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                            child.wait(timeout=3)
                        except:
                            try:
                                child.kill()
                            except:
                                pass
                except ImportError:
                    # 如果没有psutil，使用其他方法
                    if sys.platform == 'win32':
                        import subprocess
                        try:
                            # 获取当前进程ID
                            pid = os.getpid()
                            # 使用taskkill终止所有子进程
                            subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], 
                                          shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except:
                            pass
                
                event.accept()
            else:
                print(f"[日志] 用户选择取消退出")
                event.ignore()
        else:
            print(f"[日志] 没有正在进行的下载，直接退出")
            # 确保所有子进程都被终止
            try:
                import psutil
                current_process = psutil.Process()
                children = current_process.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                        child.wait(timeout=3)
                    except:
                        try:
                            child.kill()
                        except:
                            pass
            except ImportError:
                # 如果没有psutil，使用其他方法
                if sys.platform == 'win32':
                    import subprocess
                    try:
                        # 获取当前进程ID
                        pid = os.getpid()
                        # 使用taskkill终止所有子进程
                        subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], 
                                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except:
                        pass
            
            event.accept()
    
    def loadDownloadSettings(self):
        """加载下载设置"""
        print(f"[日志] 加载下载设置")
        
        # 加载下载方式
        download_method = self.settings.get("download_method", "latest")
        print(f"[日志] 下载方式: {download_method}")
        
        if download_method == "category":
            self.category_radio.setChecked(True)
            print(f"[日志] 设置类别下载为选中状态")
        elif download_method == "search":
            self.search_radio.setChecked(True)
            print(f"[日志] 设置搜索下载为选中状态")
        else:
            self.latest_radio.setChecked(True)
            print(f"[日志] 设置最新下载为选中状态")
        
        # 加载类别设置
        category = self.settings.get("category", "all")
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
            print(f"[日志] 设置类别: {category}")
        
        # 加载纯度设置
        purity = self.settings.get("purity", "sfw")
        index = self.purity_combo.findText(purity)
        if index >= 0:
            self.purity_combo.setCurrentIndex(index)
            print(f"[日志] 设置纯度: {purity}")
        
        # 加载搜索关键词
        search_query = self.settings.get("search_query", "")
        self.search_edit.setText(search_query)
        print(f"[日志] 设置搜索关键词: {search_query}")
        
        # 加载下载页数
        page_count = self.settings.get("page_count", 1)
        self.page_count_spin.setValue(page_count)
        print(f"[日志] 设置下载页数: {page_count}")
        
        # 连接信号以保存设置变化
        self.category_combo.currentTextChanged.connect(self.onCategoryChanged)
        self.purity_combo.currentTextChanged.connect(self.onPurityChanged)
        self.search_edit.textChanged.connect(self.onSearchQueryChanged)
        self.page_count_spin.valueChanged.connect(self.onPageCountChanged)
        
        print(f"[日志] 下载设置加载完成")
    
    def saveCurrentDownloadSettings(self):
        """保存当前下载设置"""
        print(f"[日志] 保存当前下载设置")
        
        # 保存类别设置
        if self.category_radio.isChecked():
            self.settings["category"] = self.category_combo.currentText()
            print(f"[日志] 保存类别: {self.settings['category']}")
        
        # 保存纯度设置
        if self.category_radio.isChecked():
            self.settings["purity"] = self.purity_combo.currentText()
            print(f"[日志] 保存纯度: {self.settings['purity']}")
        
        # 保存搜索关键词
        if self.search_radio.isChecked():
            self.settings["search_query"] = self.search_edit.text()
            print(f"[日志] 保存搜索关键词: {self.settings['search_query']}")
        
        # 保存下载页数
        self.settings["page_count"] = self.page_count_spin.value()
        print(f"[日志] 保存下载页数: {self.settings['page_count']}")
        
        # 保存设置到文件
        self.saveSettings()
    
    def onCategoryChanged(self, value):
        """类别变化事件"""
        print(f"[日志] 类别变化: {value}")
        if self.category_radio.isChecked():
            self.settings["category"] = value
            self.saveSettings()
    
    def onPurityChanged(self, value):
        """纯度变化事件"""
        print(f"[日志] 纯度变化: {value}")
        if self.category_radio.isChecked():
            self.settings["purity"] = value
            self.saveSettings()
    
    def onSearchQueryChanged(self, value):
        """搜索关键词变化事件"""
        print(f"[日志] 搜索关键词变化: {value}")
        if self.search_radio.isChecked():
            self.settings["search_query"] = value
            self.saveSettings()
    
    def onPageCountChanged(self, value):
        """下载页数变化事件"""
        print(f"[日志] 下载页数变化: {value}")
        self.settings["page_count"] = value
        self.saveSettings()