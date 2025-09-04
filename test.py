import os
import sys
import json
import urllib.parse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QTextEdit,
    QGroupBox, QGridLayout, QProgressBar, QFileDialog, QMessageBox,
    QTabWidget, QFrame
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSettings, QEvent, QSize
from PyQt5.QtGui import QFont, QIcon, QMouseEvent, QPixmap
import threading
import time

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持PyInstaller打包后的路径"""
    try:
        # PyInstaller创建临时文件夹并将路径存储在_MEIPASS中
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path is None:
            raise AttributeError
    except (AttributeError, Exception):
        base_path = os.path.abspath(".")
    
    full_path = os.path.join(base_path, relative_path)
    return full_path


class ConfigManager:
    def __init__(self):
        self.settings = QSettings('WallhavenDownloader', 'Config')
        
    def get_api_key(self):
        return self.settings.value('api_key', 'dws2O4u6Agr4v1CC92mH90H1T49QSuTM')
        
    def set_api_key(self, api_key):
        self.settings.setValue('api_key', api_key)
        
    def get_download_path(self):
        return self.settings.value('download_path', os.path.join(os.getcwd(), 'Wallhaven'))
        
    def set_download_path(self, path):
        self.settings.setValue('download_path', path)

class DownloadWorker(QThread):
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    download_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    statistics_updated = pyqtSignal(int, int, int)  # success, failed, skipped
    
    def __init__(self, base_url, download_path, pages):
        super().__init__()
        self.base_url = base_url
        self.download_path = download_path
        self.pages = pages
        self.cookies = dict()
        self.is_running = True
        self.session = self.create_session()
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.max_retries = 3  # 添加这个属性
        
    def create_session(self):
        """创建带有重试机制的会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 总重试次数
            status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的HTTP状态码
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # 修正参数名
            backoff_factor=1,  # 重试间隔倍数
            raise_on_status=False
        )
        
        # 配置HTTP适配器
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # 连接池大小
            pool_maxsize=20
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置请求头，模拟浏览器
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def stop(self):
        """安全停止下载线程"""
        self.is_running = False
        if hasattr(self, 'session'):
            try:
                self.session.close()
            except:
                pass
        
    def run(self):
        """下载主线程"""
        try:
            os.makedirs(self.download_path, exist_ok=True)
            total_images = 64 * self.pages  # 每页64张图片
            
            for page in range(1, self.pages + 1):
                if not self.is_running:
                    self.progress_updated.emit(0, total_images, "下载已被用户停止")
                    break
                    
                self.download_page(page, total_images)
                
            if self.is_running:
                self.download_finished.emit()
        except Exception as e:
            if self.is_running:  # 只有在未被停止的情况下才报告错误
                self.error_occurred.emit(f"下载出错: {str(e)}")
            
    def download_image_with_retry(self, image_url, file_path, filename, max_retries=None):
        """带重试机制的图片下载"""
        if max_retries is None:
            max_retries = getattr(self, 'max_retries', 3)
            
        for attempt in range(max_retries):
            try:
                # 设置超时时间
                img_response = self.session.get(
                    image_url, 
                    cookies=self.cookies, 
                    timeout=(10, 30),  # 连接超时10秒，读取超时30秒
                    stream=True  # 流式下载，避免内存占用过大
                )
                
                if img_response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            if not self.is_running:
                                return False, "下载被中断"
                            if chunk:
                                f.write(chunk)
                    return True, "下载成功"
                elif img_response.status_code in [403, 404]:
                    return False, "无权限/不存在"
                else:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # 指数退避
                        continue
                    return False, f"HTTP {img_response.status_code}"
                    
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                return False, f"连接错误 (重试{max_retries}次后失败): {str(e)}"
            except Exception as e:
                return False, f"未知错误: {str(e)}"
                
        return False, "重试次数用尽"
    
    def download_page(self, page_id, total_images):
        try:
            url = self.base_url + str(page_id)
            # 使用会话获取页面数据，也添加重试机制
            response = None
            for attempt in range(3):
                try:
                    response = self.session.get(url, cookies=self.cookies, timeout=(10, 30))
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    raise e
            
            if response is None:
                self.error_occurred.emit(f"无法获取页面 {page_id} 的数据")
                return
            
            if response.status_code != 200:
                self.error_occurred.emit(f"API请求失败，状态码: {response.status_code}")
                return
                
            pages_images = json.loads(response.content)
            page_data = pages_images.get("data", [])
            
            for i, image_data in enumerate(page_data):
                if not self.is_running:
                    break
                    
                current_image = ((page_id - 1) * 64) + (i + 1)  # 每页64张图片
                image_url = image_data["path"]
                filename = os.path.basename(image_url)
                file_path = os.path.join(self.download_path, filename)
                
                if not os.path.exists(file_path):
                    if not self.is_running:  # 再次检查是否停止
                        break
                        
                    success, message = self.download_image_with_retry(image_url, file_path, filename)
                    if not self.is_running:  # 下载后检查是否停止
                        break
                        
                    if success:
                        self.success_count += 1
                        self.progress_updated.emit(current_image, total_images, f"已下载: {filename}")
                    else:
                        # 如果下载失败，删除可能存在的不完整文件
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except:
                                pass
                        if "无权限/不存在" in message:
                            self.skipped_count += 1
                            self.progress_updated.emit(current_image, total_images, f"跳过: {filename} ({message})")
                        else:
                            self.failed_count += 1
                            self.progress_updated.emit(current_image, total_images, f"下载失败: {filename} - {message}")
                else:
                    self.skipped_count += 1
                    self.progress_updated.emit(current_image, total_images, f"已存在: {filename}")
                
                # 发送统计信息
                if self.is_running:  # 只有在运行时才发送
                    self.statistics_updated.emit(self.success_count, self.failed_count, self.skipped_count)
                
                # 添加小延迟，避免请求过于频繁
                if not self.is_running:
                    break
                    
                # 动态调整延迟时间，失败率较高时增加延迟
                total_processed = self.success_count + self.failed_count
                if total_processed > 10:  # 在处理了一定数量后才计算失败率
                    failure_rate = self.failed_count / total_processed
                    if failure_rate > 0.3:  # 失败率超过30%
                        time.sleep(0.5)  # 增加延迟到500毫秒
                    elif failure_rate > 0.1:  # 失败率超过10%
                        time.sleep(0.3)  # 增加延迟到300毫秒
                    else:
                        time.sleep(0.1)  # 默认100毫秒延迟
                else:
                    time.sleep(0.1)  # 默认100毫秒延迟
                    
        except Exception as e:
            self.error_occurred.emit(f"处理页面 {page_id} 时出错: {str(e)}")

class WallhavenDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.download_worker = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Wallhaven 壁纸下载器')
        self.setGeometry(100, 50, 1920, 1080)
        
        # 设置窗口图标（使用logo.ico作为任务栏图标）
        logo_icon_path = get_resource_path(os.path.join('icon', 'logo.ico'))
        if os.path.exists(logo_icon_path):
            window_icon = QIcon(logo_icon_path)
            if not window_icon.isNull():
                self.setWindowIcon(window_icon)
            else:
                # 如果logo.ico加载失败，回退到atom.ico
                fallback_icon_path = get_resource_path(os.path.join('icon', 'atom.ico'))
                if os.path.exists(fallback_icon_path):
                    fallback_icon = QIcon(fallback_icon_path)
                    if not fallback_icon.isNull():
                        self.setWindowIcon(fallback_icon)
        else:
            # 如果logo.ico不存在，使用atom.ico作为备用
            fallback_icon_path = get_resource_path(os.path.join('icon', 'atom.ico'))
            if os.path.exists(fallback_icon_path):
                fallback_icon = QIcon(fallback_icon_path)
                if not fallback_icon.isNull():
                    self.setWindowIcon(fallback_icon)
        
        # 设置窗口透明效果
        # 使用具体的枚举值来避免类型检查器错误
        self.setWindowFlags(getattr(Qt, 'Window', 0x00000001) | getattr(Qt, 'FramelessWindowHint', 0x00000800))  # type: ignore
        self.setAttribute(getattr(Qt, 'WA_TranslucentBackground', 120), True)  # type: ignore
        
        # 初始化界面布局
        self.setup_styles_and_layout()
    def create_title_bar(self):
        """创建自定义渐变标题栏"""
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border: none;
                border-bottom: 1px solid rgba(74, 144, 226, 0.5);
            }
        """)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        # 窗口图标
        icon_label = QLabel()
        icon_path = get_resource_path(os.path.join('icon', 'atom.ico'))
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                icon_pixmap = icon.pixmap(16, 16)
                icon_label.setPixmap(icon_pixmap)
                icon_label.setFixedSize(16, 16)
            else:
                # 如果图标加载失败，显示默认文本
                icon_label.setText('W')
                icon_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
                icon_label.setFixedSize(16, 16)
        else:
            # 如果图标文件不存在，显示默认文本
            icon_label.setText('W')
            icon_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
            icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet(icon_label.styleSheet() + "background: transparent;")
        title_layout.addWidget(icon_label)
        
        # 窗口标题
        self.title_label = QLabel('Wallhaven')
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                margin-left: 8px;
            }
        """)
        title_layout.addWidget(self.title_label)
        
        # 添加弹性空间
        title_layout.addStretch()
        
        # 窗口控制按钮
        self.create_window_buttons(title_layout)
        
        # 使标题栏可拖动
        self.title_bar.installEventFilter(self)
        self.drag_position = None
        
    def create_window_buttons(self, layout):
        """创建窗口控制按钮"""
        button_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 5px 10px;
                min-width: 30px;
                max-width: 30px;
                min-height: 25px;
                max-height: 25px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """
        
        # 获取图标路径
        icon_dir = get_resource_path('icon')
        # 固定图标尺寸
        icon_size = 16
        
        # 最小化按钮
        self.minimize_button = QPushButton()
        minimize_icon_path = os.path.join(icon_dir, 'minimize.ico')  # 修正文件名
        if os.path.exists(minimize_icon_path):
            icon = QIcon(minimize_icon_path)
            if not icon.isNull():
                self.minimize_button.setIcon(icon)
                # 设置固定图标尺寸
                self.minimize_button.setIconSize(QSize(icon_size, icon_size))
            else:
                self.minimize_button.setText('−')
        else:
            self.minimize_button.setText('−')
        self.minimize_button.setStyleSheet(button_style)
        self.minimize_button.clicked.connect(self.showMinimized)
        layout.addWidget(self.minimize_button)
        
        # 最大化/还原按钮
        self.maximize_button = QPushButton()
        maximize_icon_path = os.path.join(icon_dir, 'maxmize.ico')
        if os.path.exists(maximize_icon_path):
            icon = QIcon(maximize_icon_path)
            if not icon.isNull():
                self.maximize_button.setIcon(icon)
                # 设置固定图标尺寸
                self.maximize_button.setIconSize(QSize(icon_size, icon_size))
            else:
                self.maximize_button.setText('□')
        else:
            self.maximize_button.setText('□')
        self.maximize_button.setStyleSheet(button_style)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.maximize_button)
        
        # 关闭按钮
        close_button_style = button_style.replace(
            "background: rgba(255, 255, 255, 0.1);",
            "background: rgba(255, 0, 0, 0.2);"
        ).replace(
            "background: rgba(255, 255, 255, 0.2);",
            "background: rgba(255, 0, 0, 0.4);"
        )
        self.close_button = QPushButton()
        close_icon_path = os.path.join(icon_dir, 'close.ico')
        if os.path.exists(close_icon_path):
            icon = QIcon(close_icon_path)
            if not icon.isNull():
                self.close_button.setIcon(icon)
                # 设置固定图标尺寸
                self.close_button.setIconSize(QSize(icon_size, icon_size))
            else:
                self.close_button.setText('×')
        else:
            self.close_button.setText('×')
        self.close_button.setStyleSheet(close_button_style)
        self.close_button.clicked.connect(self.close_application)
        layout.addWidget(self.close_button)
        
    def close_application(self):
        """关闭应用程序"""
        # 如果有下载任务在进行，先停止它
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.download_worker.wait(1000)  # 等待最多1秒
        self.close()
        
    def toggle_maximize(self):
        """切换最大化/还原状态"""
        if self.isMaximized():
            self.showNormal()
            if hasattr(self, 'maximize_button'):
                self.maximize_button.setText('□')
        else:
            self.showMaximized()
            if hasattr(self, 'maximize_button'):
                self.maximize_button.setText('▢')
            
    def eventFilter(self, a0, a1):
        """事件过滤器处理标题栏拖拽"""
        if a0 == self.title_bar:
            if a1.type() == getattr(QEvent, 'MouseButtonPress', 2):
                # 检查是否为鼠标事件并安全访问属性
                if isinstance(a1, QMouseEvent):
                    if a1.button() == getattr(Qt, 'LeftButton', 1):
                        self.drag_position = a1.globalPos() - self.frameGeometry().topLeft()
                        return True
            elif a1.type() == getattr(QEvent, 'MouseMove', 5):
                # 检查是否为鼠标事件并安全访问属性
                if isinstance(a1, QMouseEvent):
                    if (a1.buttons() == getattr(Qt, 'LeftButton', 1) and self.drag_position is not None):
                        self.move(a1.globalPos() - self.drag_position)
                        return True
            elif a1.type() == getattr(QEvent, 'MouseButtonDblClick', 4):
                # 检查是否为鼠标事件并安全访问属性
                if isinstance(a1, QMouseEvent):
                    if a1.button() == getattr(Qt, 'LeftButton', 1):
                        self.toggle_maximize()
                        return True
        return super().eventFilter(a0, a1)
        
    def setup_styles_and_layout(self):
        """设置样式和布局"""
        # 创建自定义标题栏
        self.create_title_bar()
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a90e2;
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2d3748, stop:1 #1a202c);
                font-size: 19px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 12px 0 12px;
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4a90e2, stop:1 #667eea);
                border-radius: 6px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:0.5 #45a049, stop:1 #3e8e41);
                border: none;
                color: white;
                padding: 18px 30px;
                text-align: center;
                font-size: 20px;
                border-radius: 8px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                min-height: 35px;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5cbf60, stop:0.5 #4db151, stop:1 #459e49);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3e8e41, stop:0.5 #367d3a, stop:1 #2e6c33);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #666666, stop:1 #444444);
                color: #ffffff;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 12px;
                border: 2px solid #4a90e2;
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2d3748, stop:1 #1a202c);
                color: #ffffff;
                font-size: 18px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                min-height: 28px;
            }
            QComboBox::drop-down {
                color: #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: #ffffff;
                selection-background-color: #4a90e2;
                border: 1px solid #4a90e2;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #667eea;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3d4852, stop:1 #2a303c);
                color: #ffffff;
            }
            QTextEdit {
                border: 2px solid #4a90e2;
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2d3748, stop:1 #1a202c);
                color: #ffffff;
                font-family: 'Consolas', 'Microsoft YaHei', 'SimHei', monospace;
                font-size: 17px;
                line-height: 1.5;
                padding: 8px;
            }
            QProgressBar {
                border: 2px solid #4a90e2;
                border-radius: 10px;
                text-align: center;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2d3748, stop:1 #1a202c);
                font-size: 18px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                font-weight: bold;
                min-height: 30px;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4CAF50, stop:0.5 #5cbf60, stop:1 #4CAF50);
                border-radius: 8px;
                margin: 2px;
            }
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
            }
            QTabWidget::pane {
                border: 2px solid #4a90e2;
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2d3748, stop:1 #1a202c);
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1a1a2e, stop:1 #16213e);
                color: #ffffff;
                padding: 18px 30px;
                margin-right: 3px;
                border-radius: 8px 8px 0 0;
                font-size: 18px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                font-weight: bold;
                border: 2px solid #4a90e2;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:1 #45a049);
                color: #ffffff;
                border-color: #4CAF50;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #667eea, stop:1 #4a90e2);
                color: #ffffff;
            }
        """)
        
        # 初始化布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主容器布局
        main_container_layout = QVBoxLayout(central_widget)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)
        
        # 添加自定义标题栏
        main_container_layout.addWidget(self.title_bar)
        
        # 创建主内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border-radius: 0 0 10px 10px;
            }
        """)
        main_container_layout.addWidget(content_widget)
        
        # 主布局
        main_layout = QVBoxLayout(content_widget)
        
        # 标题
        title_label = QLabel('Wallhaven 壁纸下载器')
        title_label.setAlignment(getattr(Qt, 'AlignCenter', 0x0004))  # type: ignore
        title_label.setFont(QFont('Microsoft YaHei', 32, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                margin: 20px 0;
                background: transparent;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 下载标签页
        download_tab = QWidget()
        tab_widget.addTab(download_tab, "下载")
        
        # 配置标签页
        config_tab = QWidget()
        tab_widget.addTab(config_tab, "配置")
        
        self.setup_download_tab(download_tab)
        self.setup_config_tab(config_tab)
        
        # 日志区域
        log_group = QGroupBox("下载日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setMinimumHeight(150)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
        # 进度条
        progress_group = QGroupBox("下载进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(35)
        self.progress_label = QLabel("就绪")
        self.progress_label.setFont(QFont('Microsoft YaHei', 18))
        
        # 统计信息
        self.statistics_label = QLabel("成功: 0 | 失败: 0 | 跳过: 0")
        self.statistics_label.setFont(QFont('Microsoft YaHei', 16))
        self.statistics_label.setStyleSheet("color: #ffffff; margin: 5px 0;")
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.statistics_label)
        
        main_layout.addWidget(progress_group)
        
    def setup_download_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # 下载模式选择
        mode_group = QGroupBox("下载模式")
        mode_layout = QGridLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["分类下载", "最新壁纸", "搜索下载"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(QLabel("选择模式:"), 0, 0)
        mode_layout.addWidget(self.mode_combo, 0, 1)
        
        layout.addWidget(mode_group)
        
        # 分类下载选项
        self.category_group = QGroupBox("分类设置")
        category_layout = QGridLayout(self.category_group)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "all - 每一张墙纸", "general - 一般壁纸", "anime - 动漫壁纸", 
            "people - 人物壁纸", "ga - 一般和动漫", "gp - 一般和人物"
        ])
        category_layout.addWidget(QLabel("类别:"), 0, 0)
        category_layout.addWidget(self.category_combo, 0, 1)
        
        self.purity_combo = QComboBox()
        self.purity_combo.addItems([
            "sfw - 工作安全", "sketchy - 可疑内容", "nsfw - 工作不安全",
            "ws - 工作安全+可疑", "wn - 工作安全+不安全", "sn - 可疑+不安全", "all - 全部"
        ])
        category_layout.addWidget(QLabel("纯度:"), 1, 0)
        category_layout.addWidget(self.purity_combo, 1, 1)
        
        layout.addWidget(self.category_group)
        
        # 搜索下载选项
        self.search_group = QGroupBox("搜索设置")
        search_layout = QGridLayout(self.search_group)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词...")
        search_layout.addWidget(QLabel("搜索词:"), 0, 0)
        search_layout.addWidget(self.search_input, 0, 1)
        
        layout.addWidget(self.search_group)
        self.search_group.hide()
        
        # 下载设置
        download_group = QGroupBox("下载设置")
        download_layout = QGridLayout(download_group)
        
        self.pages_spinbox = QSpinBox()
        self.pages_spinbox.setMinimum(1)
        self.pages_spinbox.setMaximum(999999)  # 设置为无限制
        self.pages_spinbox.setValue(1)
        download_layout.addWidget(QLabel("下载页数:"), 0, 0)
        download_layout.addWidget(self.pages_spinbox, 0, 1)
        
        # 添加页数说明
        pages_info = QLabel("(每页约64张图片)")
        pages_info.setStyleSheet("color: #ffffff; font-size: 14px;")
        download_layout.addWidget(pages_info, 0, 2)
        
        # 下载线程数设置
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setMinimum(1)
        self.thread_spinbox.setMaximum(5)  # 限制最大线程数
        self.thread_spinbox.setValue(2)
        download_layout.addWidget(QLabel("并发下载数:"), 1, 0)
        download_layout.addWidget(self.thread_spinbox, 1, 1)
        
        thread_info = QLabel("(建议1-3个，过多可能被限制)")
        thread_info.setStyleSheet("color: #ffffff; font-size: 14px;")
        download_layout.addWidget(thread_info, 1, 2)
        
        # 重试次数设置
        self.retry_spinbox = QSpinBox()
        self.retry_spinbox.setMinimum(1)
        self.retry_spinbox.setMaximum(10)
        self.retry_spinbox.setValue(3)
        download_layout.addWidget(QLabel("失败重试次数:"), 2, 0)
        download_layout.addWidget(self.retry_spinbox, 2, 1)
        
        retry_info = QLabel("(网络不稳定时可增加)")
        retry_info.setStyleSheet("color: #ffffff; font-size: 14px;")
        download_layout.addWidget(retry_info, 2, 2)
        
        layout.addWidget(download_group)
        
        # 下载按钮
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("开始下载")
        self.start_button.clicked.connect(self.start_download)
        self.stop_button = QPushButton("停止下载")
        self.stop_button.clicked.connect(self.stop_download)
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)
        
    def setup_config_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # API配置
        api_group = QGroupBox("API 配置")
        api_layout = QGridLayout(api_group)
        
        self.api_input = QLineEdit()
        self.api_input.setText(self.config.get_api_key())
        self.api_input.setPlaceholderText("输入您的 Wallhaven API 密钥...")
        api_layout.addWidget(QLabel("API 密钥:"), 0, 0)
        api_layout.addWidget(self.api_input, 0, 1)
        
        api_help_label = QLabel('获取API密钥: <a href="https://wallhaven.cc/settings/account" style="color: #ffffff;">点击获取</a>')
        api_help_label.setOpenExternalLinks(True)
        api_layout.addWidget(api_help_label, 1, 0, 1, 2)
        
        layout.addWidget(api_group)
        
        # 路径配置
        path_group = QGroupBox("下载路径配置")
        path_layout = QGridLayout(path_group)
        
        self.path_input = QLineEdit()
        self.path_input.setText(self.config.get_download_path())
        path_layout.addWidget(QLabel("下载路径:"), 0, 0)
        path_layout.addWidget(self.path_input, 0, 1)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_button, 0, 2)
        
        layout.addWidget(path_group)
        
        # 保存按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)
        
        layout.addStretch()
        
    def on_mode_changed(self, mode):
        if mode == "分类下载":
            self.category_group.show()
            self.search_group.hide()
        elif mode == "搜索下载":
            self.category_group.hide()
            self.search_group.show()
        else:  # 最新壁纸
            self.category_group.hide()
            self.search_group.hide()
            
    def browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择下载文件夹")
        if folder:
            self.path_input.setText(folder)
            
    def save_config(self):
        # 验证API密钥
        api_key = self.api_input.text().strip()
        if not api_key:
            self.show_message("输入错误", "API密钥不能为空", QMessageBox.Warning)
            return
            
        # 验证下载路径
        download_path = self.path_input.text().strip()
        if not download_path:
            self.show_message("输入错误", "下载路径不能为空", QMessageBox.Warning)
            return
            
        self.config.set_api_key(api_key)
        self.config.set_download_path(download_path)
        self.show_message("保存成功", "配置已保存", QMessageBox.Information)
        
    def get_base_url(self):
        api_key = self.config.get_api_key()
        mode = self.mode_combo.currentText()
        
        if mode == "分类下载":
            category_text = self.category_combo.currentText()
            purity_text = self.purity_combo.currentText()
            
            ctags = {'all':'111', 'general':'100', 'anime':'010', 'people':'001', 'ga':'110', 'gp':'101'}
            ptags = {'sfw':'100', 'sketchy':'010', 'nsfw':'001', 'ws':'110', 'wn':'101', 'sn':'011', 'all':'111'}
            
            category_key = category_text.split(' - ')[0]
            purity_key = purity_text.split(' - ')[0]
            
            ctag = ctags.get(category_key, '111')
            ptag = ptags.get(purity_key, '100')
            
            return f'https://wallhaven.cc/api/v1/search?apikey={api_key}&categories={ctag}&purity={ptag}&page='
            
        elif mode == "搜索下载":
            query = self.search_input.text().strip()
            if not query:
                raise ValueError("搜索关键词不能为空")
            encoded_query = urllib.parse.quote_plus(query)
            return f'https://wallhaven.cc/api/v1/search?apikey={api_key}&q={encoded_query}&page='
            
        else:  # 最新壁纸
            return f'https://wallhaven.cc/api/v1/search?apikey={api_key}&topRange=1M&sorting=toplist&page='
            
    def show_message(self, title, text, icon_type):
        """显示美化的消息框"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setIcon(icon_type)
        msg_box.setText(text)
        
        # 设置消息框窗口属性，与主窗口保持一致
        msg_box.setWindowFlags(getattr(Qt, 'Dialog', 0x00000002) | getattr(Qt, 'FramelessWindowHint', 0x00000800))  # type: ignore
        msg_box.setAttribute(getattr(Qt, 'WA_TranslucentBackground', 120), True)  # type: ignore
        
        # 设置消息框样式，使用与主窗口相同的渐变背景
        msg_box.setStyleSheet("""
            QMessageBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(26, 26, 46, 0.9), stop:0.5 rgba(22, 33, 62, 0.9), stop:1 rgba(15, 52, 96, 0.9));
                color: #ffffff;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                font-size: 16px;
                border-radius: 12px;
                border: 2px solid rgba(74, 144, 226, 0.6);
                padding: 0px;
            }
            QMessageBox QLabel {
                color: #ffffff;
                font-size: 18px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                background: transparent;
                padding: 20px;
                min-width: 400px;
                min-height: 60px;
                border: none;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:0.5 #45a049, stop:1 #3e8e41);
                border: none;
                color: #ffffff;
                padding: 12px 24px;
                font-size: 18px;
                border-radius: 8px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                min-width: 100px;
                min-height: 40px;
                margin: 10px 5px;
            }
            QMessageBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5cbf60, stop:1 #4db151);
            }
            QMessageBox QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3e8e41, stop:1 #367d3a);
            }
        """)
        
        # 设置按钮
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.button(QMessageBox.Ok).setText("确定")
        
        # 使消息框在主窗口中央显示
        if self.isVisible():
            # 计算主窗口中心位置
            main_rect = self.geometry()
            main_center = main_rect.center()
            
            # 设置消息框尺寸和位置
            msg_box.resize(500, 200)
            msg_rect = msg_box.geometry()
            msg_rect.moveCenter(main_center)
            msg_box.setGeometry(msg_rect)
        
        return msg_box.exec_()
        
    def start_download(self):
        try:
            # 检查是否有正在运行的下载任务
            if self.download_worker and self.download_worker.isRunning():
                self.show_message("提示", "已有下载任务在进行中，请先停止当前任务", QMessageBox.Warning)
                return
                
            # 验证输入
            if self.mode_combo.currentText() == "搜索下载" and not self.search_input.text().strip():
                self.show_message("输入错误", "请输入搜索关键词", QMessageBox.Warning)
                return
                
            base_url = self.get_base_url()
            download_path = self.config.get_download_path()
            pages = self.pages_spinbox.value()
            max_retries = self.retry_spinbox.value()
            
            # 创建新的下载线程，传入重试次数参数
            self.download_worker = DownloadWorker(base_url, download_path, pages)
            self.download_worker.max_retries = max_retries
            self.download_worker.progress_updated.connect(self.update_progress)
            self.download_worker.download_finished.connect(self.download_finished)
            self.download_worker.error_occurred.connect(self.download_error)
            self.download_worker.statistics_updated.connect(self.update_statistics)
            
            # 更新UI状态
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setValue(0)
            self.log_text.clear()
            self.statistics_label.setText("成功: 0 | 失败: 0 | 跳过: 0")
            self.log_text.append(f"开始下载... (重试次数: {max_retries})")
            
            # 启动下载
            self.download_worker.start()
            
        except ValueError as e:
            self.show_message("输入错误", str(e), QMessageBox.Warning)
        except Exception as e:
            self.show_message("错误", f"启动下载时出错: {str(e)}", QMessageBox.Critical)
            
    def stop_download(self):
        """停止下载"""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.log_text.append("正在停止下载...")
            # 等待下载线程结束
            self.download_worker.wait(3000)  # 等待最多3秒
            
            # 重置UI状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_label.setText("下载已停止")
            self.log_text.append("下载已停止")
            
            # 清理下载worker
            self.download_worker = None
            
    def update_statistics(self, success, failed, skipped):
        """更新统计信息"""
        self.statistics_label.setText(f"成功: {success} | 失败: {failed} | 跳过: {skipped}")
        
    def update_progress(self, current, total, message):
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"进度: {current}/{total} ({progress}%)")
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
    def download_finished(self):
        """下载完成处理"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_label.setText("下载完成")
        
        # 获取最终统计数据
        if self.download_worker:
            success = self.download_worker.success_count
            failed = self.download_worker.failed_count
            skipped = self.download_worker.skipped_count
            total = success + failed + skipped
            
            summary_message = f"""
=== 下载完成 ===
总计处理: {total} 个文件
成功下载: {success} 个
跳过/已存在: {skipped} 个
下载失败: {failed} 个
成功率: {(success/total*100):.1f}%""".strip() if total > 0 else """
=== 下载完成 ===
没有找到任何文件需要下载""".strip()
            
            self.log_text.append(summary_message)
            
            # 如果失败率较高，给出建议
            if total > 0 and failed / total > 0.2:
                suggestion = """
建议:
- 失败率较高，可能是网络不稳定导致
- 尝试增加重试次数（在配置页面）
- 或者稍后再试
- 检查网络连接是否稳定"""
                self.log_text.append(suggestion)
                
            self.show_message("完成", f"下载任务已完成!\n成功: {success}, 失败: {failed}, 跳过: {skipped}", QMessageBox.Information)
            
            # 清理下载worker
            self.download_worker = None
        else:
            self.log_text.append("所有下载任务已完成!")
            self.show_message("完成", "下载任务已完成!", QMessageBox.Information)
        
    def download_error(self, error_message):
        """下载错误处理"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_text.append(f"错误: {error_message}")
        self.show_message("下载错误", error_message, QMessageBox.Critical)
        
        # 清理下载worker
        if self.download_worker:
            self.download_worker = None

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Wallhaven下载器")
    
    # 设置应用程序图标（任务栏图标）
    app_icon_path = get_resource_path(os.path.join('icon', 'logo.ico'))
    if os.path.exists(app_icon_path):
        app_icon = QIcon(app_icon_path)
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
        else:
            # 如果logo.ico加载失败，回退到atom.ico
            fallback_icon_path = get_resource_path(os.path.join('icon', 'atom.ico'))
            if os.path.exists(fallback_icon_path):
                fallback_icon = QIcon(fallback_icon_path)
                if not fallback_icon.isNull():
                    app.setWindowIcon(fallback_icon)
    else:
        # 如果logo.ico不存在，使用atom.ico作为备用
        fallback_icon_path = get_resource_path(os.path.join('icon', 'atom.ico'))
        if os.path.exists(fallback_icon_path):
            fallback_icon = QIcon(fallback_icon_path)
            if not fallback_icon.isNull():
                app.setWindowIcon(fallback_icon)
        
    window = WallhavenDownloader()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()