# -*- coding: utf-8 -*-
"""
下载线程模块
提供壁纸下载的后台线程处理
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Set, Any, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import concurrent.futures

from utils.logger import get_logger
from utils.performance import PerformanceMonitor, RateLimiter
from utils.exceptions import NetworkException, DownloadException

logger = get_logger(__name__)


class WallpaperDownloadThread(QThread):
    """壁纸下载线程"""
    
    # 定义信号
    progress_updated = pyqtSignal(int, str)  # 进度更新信号 (进度百分比, 当前下载的文件名)
    download_completed = pyqtSignal()  # 下载完成信号
    download_failed = pyqtSignal(str)  # 下载失败信号
    image_downloaded = pyqtSignal(str, QPixmap)  # 图片下载完成信号 (文件路径, 图片)
    duplicate_detected = pyqtSignal(int, int)  # 检测到重复文件信号 (重复数量, 总数量)
    
    def __init__(
        self, 
        base_url: str,
        start_page: int,
        page_count: int,
        download_dir: str,
        parent=None,
        resume_state: Optional[Dict[str, Any]] = None,
        concurrent_downloads: int = 3
    ):
        """
        初始化下载线程
        
        Args:
            base_url: API基础URL
            start_page: 起始页码
            page_count: 下载页数
            download_dir: 下载目录
            parent: 父对象
            resume_state: 恢复下载状态
            concurrent_downloads: 并发下载数
        """
        super().__init__(parent)
        self.base_url = base_url
        self.start_page = start_page
        self.page_count = page_count
        self.download_dir = download_dir
        self.is_running = True
        self.cookies: Dict[str, str] = {}
        
        # 统计信息
        self.total_images = 0
        self.downloaded_images = 0
        self.duplicate_images = 0
        self.unique_images_to_download = 0
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        # 性能优化 - 增加并发数
        self._last_progress_update = 0
        self._progress_update_threshold = 100
        # 优化: 增加默认并发数到10，提高下载速度（原5->10）
        self.concurrent_downloads = max(concurrent_downloads, 10)
        self.max_retries = 3
        
        # 优化: 文件存在性检查缓存
        self.existing_files_cache: Set[str] = set()
        
        # 创建会话
        self.session = self._create_session()
        
        # 恢复下载状态
        self.resume_state = resume_state or {}
        self.current_page = self.resume_state.get('current_page', self.start_page)
        
        # 处理已处理的URL和文件
        processed_urls = self.resume_state.get('processed_urls', set())
        downloaded_files = self.resume_state.get('downloaded_files', set())
        self.processed_urls: Set[str] = set(processed_urls) if isinstance(processed_urls, (list, set)) else set()
        self.downloaded_files: Set[str] = set(downloaded_files) if isinstance(downloaded_files, (list, set)) else set()
        self.is_resuming = bool(resume_state)
        
        # 预览图生成频率配置（优化: 5->10，减少CPU占用）
        self.preview_generation_interval = 10  # 每 N 张生成一次预览
    
    def _create_session(self) -> requests.Session:
        """创建带有重试机制的会话 - 性能优化版本"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
            raise_on_status=False
        )
        
        # 优化: 增加连接池大小，支持更高的并发（20->30, 50->100）
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=30,  # 增加到30
            pool_maxsize=100      # 增加到100
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://wallhaven.cc/'
        })
        
        return session
    
    def download_single_image(self, img_url: str, img_filename: str) -> Optional[Tuple[str, Optional[QPixmap], bool]]:
        """
        下载单个图片 - 性能优化版本
        
        优化点:
        1. 早期检查文件是否存在，避免不必要的网络请求
        2. 使用流式下载，减少内存占用
        3. 只在需要时生成预览图，减少CPU占用
        4. 使用指数退避策略，减少不必要的重试
        
        Args:
            img_url: 图片URL
            img_filename: 文件名
            
        Returns:
            (文件路径, QPixmap对象, 是否成功) 或 None
        """
        try:
            if not self.is_running:
                return None
            
            file_path = os.path.join(self.download_dir, img_filename)
            
            # 优化: 使用缓存检查文件是否已存在，避免重复的磁盘I/O
            if img_filename in self.existing_files_cache:
                self.skipped_count += 1
                logger.debug(f"图片已存在（缓存命中），跳过: {img_filename}")
                return (file_path, None, True)
            
            # 如果缓存未命中，检查文件系统
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                # 检查文件大小，过小的文件可能是不完整的
                if file_size > 1024:  # 大于1KB
                    self.skipped_count += 1
                    self.existing_files_cache.add(img_filename)  # 添加到缓存
                    logger.debug(f"图片已存在，跳过: {img_filename}")
                    # 不生成预览图，节省资源
                    return (file_path, None, True)
                else:
                    # 删除不完整文件
                    try:
                        os.remove(file_path)
                        logger.warning(f"删除不完整文件: {img_filename} ({file_size} bytes)")
                    except OSError as e:
                        logger.warning(f"删除不完整文件失败: {e}")
            
            # 添加cookies
            if self.cookies:
                self.session.cookies.update(self.cookies)
            
            # 优化: 重试逻辑，使用指数退避
            for retry_count in range(self.max_retries):
                try:
                    # 使用流式下载，减少内存占用
                    response = self.session.get(
                        img_url,
                        timeout=(10, 30),  # 连接超时10秒，读取超时30秒
                        stream=True
                    )
                    
                    if response.status_code == 200:
                        # 优化: 使用更大的块大小，减少IO次数（16KB->64KB）
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=65536):  # 64KB
                                if not self.is_running:
                                    # 删除不完整文件
                                    if os.path.exists(file_path):
                                        try:
                                            os.remove(file_path)
                                            logger.debug(f"已删除不完整文件: {img_filename}")
                                        except OSError as e:
                                            logger.warning(f"删除不完整文件失败: {e}")
                                    return None
                                if chunk:
                                    f.write(chunk)
                        
                        self.downloaded_files.add(img_filename)
                        self.existing_files_cache.add(img_filename)  # 添加到缓存
                        self.success_count += 1
                        
                        # 优化: 根据配置生成预览图
                        pixmap = None
                        if self.success_count % self.preview_generation_interval == 0:
                            try:
                                with open(file_path, 'rb') as f:
                                    img_data = f.read()
                                
                                pixmap = QPixmap()
                                pixmap.loadFromData(img_data)
                                
                                if not pixmap.isNull():
                                    # 优化: 使用快速缩放算法
                                    scaled_pixmap = pixmap.scaled(200, 200, 1, 0)  # Qt.KeepAspectRatio, Qt.FastTransformation
                                    return (file_path, scaled_pixmap, True)
                            except Exception as e:
                                logger.debug(f"预览图生成失败: {img_filename}")
                        
                        return (file_path, pixmap, True)
                    
                    elif response.status_code in [403, 404]:
                        logger.debug(f"图片不可访问 ({response.status_code}): {img_filename}")
                        self.skipped_count += 1
                        return (img_filename, None, False)
                    
                    elif response.status_code == 429:
                        # 优化: 对429限流错误使用更长的等待时间
                        wait_time = min(2 ** (retry_count + 2), 15)  # 更长的等待时间
                        logger.warning(f"遇到限流 (429), 等待 {wait_time}秒后重试 {retry_count + 1}/{self.max_retries}")
                        time.sleep(wait_time)
                    
                    else:
                        # 优化: 对其他错误使用较短的等待时间
                        wait_time = min(2 ** retry_count, 3)  # 最大3秒
                        logger.debug(f"下载失败 (状态码{response.status_code}), 重试 {retry_count + 1}/{self.max_retries}")
                        time.sleep(wait_time)
                
                except (requests.exceptions.ConnectionError, 
                        requests.exceptions.Timeout,
                        requests.exceptions.ChunkedEncodingError) as e:
                    # 优化: 网络错误立即重试，不等待
                    if retry_count == 0:
                        logger.debug(f"网络错误: {type(e).__name__}, 立即重试")
                        continue
                    wait_time = min(2 ** (retry_count - 1), 3)
                    logger.debug(f"网络错误: {type(e).__name__}, 等待{wait_time}秒后重试 {retry_count + 1}/{self.max_retries}")
                    time.sleep(wait_time)
                
                except Exception as e:
                    wait_time = min(2 ** retry_count, 5)
                    logger.warning(f"下载异常: {type(e).__name__}, 重试 {retry_count + 1}/{self.max_retries}")
                    time.sleep(wait_time)
            
            # 所有重试都失败
            self.failed_count += 1
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"已删除失败文件: {img_filename}")
                except OSError as e:
                    logger.warning(f"删除失败文件失败: {e}")
            return (img_filename, None, False)
        
        except Exception as e:
            logger.error(f"下载图片时发生严重错误: {str(e)}")
            self.failed_count += 1
            return (img_filename, None, False)
    
    def run(self):
        """线程主函数"""
        try:
            os.makedirs(self.download_dir, exist_ok=True)
            start_time = datetime.now()
            
            logger.info(f"开始下载，起始页: {self.start_page}, 页数: {self.page_count}")
            
            # 加载状态
            if self.is_resuming:
                if self._load_download_state():
                    logger.info("成功加载下载状态")
                else:
                    self.is_resuming = False
                    logger.warning("加载下载状态失败，从头开始")
            
            # 优化: 一次性扫描所有已存在的文件，建立缓存
            existing_files = set()
            for filename in os.listdir(self.download_dir):
                if filename.startswith("wallhaven-") and filename.endswith((".jpg", ".png")):
                    existing_files.add(filename)
            
            # 初始化文件缓存
            self.existing_files_cache = existing_files.copy()
            
            logger.info(f"发现 {len(existing_files)} 个已存在文件，已建立缓存")
            
            # 初始化计数器
            if not self.is_resuming:
                self.total_images = 0
                self.downloaded_images = 0
                self.duplicate_images = 0
                self.unique_images_to_download = 0
                self.success_count = 0
                self.failed_count = 0
                self.skipped_count = 0
            
            start_page = self.current_page if self.is_resuming else self.start_page
            
            # 并发下载
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_downloads) as executor:
                for page_id in range(start_page, start_page + self.page_count):
                    if not self.is_running:
                        logger.info("下载被用户中断")
                        break
                    
                    # 获取页面数据
                    page_data = self._fetch_page_data(page_id)
                    if not page_data:
                        continue
                    
                    self.current_page = page_id
                    
                    # 处理当前页面图片
                    for item in page_data:
                        if not self.is_running:
                            break
                        
                        img_url = item["path"]
                        filename = os.path.basename(img_url)
                        self.total_images += 1
                        
                        # 检查是否需要下载
                        if filename not in existing_files and filename not in self.downloaded_files:
                            future = executor.submit(self.download_single_image, img_url, filename)
                            
                            try:
                                result = future.result()
                                if result is None:
                                    continue
                                
                                file_path, pixmap, success = result
                                
                                if success:
                                    if pixmap:
                                        self.image_downloaded.emit(file_path, pixmap)
                                    
                                    self.downloaded_images += 1
                                    self.unique_images_to_download += 1
                                    
                                    # 定期保存状态
                                    if self.downloaded_images % 10 == 0:
                                        self._save_download_state()
                                else:
                                    if isinstance(file_path, str) and file_path != filename:
                                        self.download_failed.emit(f"下载失败: {file_path}")
                            
                            except Exception as e:
                                logger.error(f"处理下载结果时出错: {str(e)}")
                                continue
                        else:
                            self.duplicate_images += 1
                            self.skipped_count += 1
                        
                        # 更新进度
                        self._update_progress(page_id, start_page, filename)
                        
                        # 动态延迟
                        self._apply_dynamic_delay()
                    
                    # 每页保存一次状态
                    self._save_download_state()
                    
                    # 发送重复检测信号
                    if self.duplicate_images > 0:
                        self.duplicate_detected.emit(self.duplicate_images, self.total_images)
            
            # 完成
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"下载完成! 总数: {self.total_images}, 成功: {self.success_count}, "
                       f"失败: {self.failed_count}, 跳过: {self.skipped_count}, 用时: {duration:.1f}秒")
            
            # 删除状态文件
            try:
                state_file = os.path.join(self.download_dir, 'download_state.json')
                if os.path.exists(state_file):
                    os.remove(state_file)
                    logger.debug("已删除下载状态文件")
            except OSError as e:
                logger.warning(f"删除状态文件失败: {e}")
            
            self.download_completed.emit()
        
        except Exception as e:
            logger.error(f"下载线程异常: {str(e)}")
            self.download_failed.emit(str(e))
        finally:
            # 清理资源
            self.cleanup()
    
    def cleanup(self):
        """清理资源，关闭 Session"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
                logger.debug("Session 已关闭")
        except Exception as e:
            logger.warning(f"关闭 Session 失败: {e}")
    
    def _fetch_page_data(self, page_id: int) -> Optional[list]:
        """获取页面数据"""
        url = self.base_url + str(page_id)
        
        if self.cookies:
            self.session.cookies.update(self.cookies)
        
        for retry_count in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=(10, 30))
                
                if response.status_code == 200:
                    data = json.loads(response.content)
                    return data.get("data", [])
                else:
                    wait_time = min(2 ** (retry_count + 1), 10)
                    logger.debug(f"获取页面 {page_id} 失败，重试 {retry_count + 1}/{self.max_retries}")
                    time.sleep(wait_time)
            
            except Exception as e:
                wait_time = min(2 ** (retry_count + 1), 10)
                logger.warning(f"获取页面 {page_id} 异常: {str(e)}, 重试 {retry_count + 1}/{self.max_retries}")
                time.sleep(wait_time)
        
        self.download_failed.emit(f"获取页面 {page_id} 失败，已尝试 {self.max_retries} 次")
        return None
    
    def _update_progress(self, current_page: int, start_page: int, filename: str):
        """更新进度"""
        processed_images = self.downloaded_images + self.duplicate_images
        current_relative_page = current_page - start_page + 1
        progress = min(100, int(((current_relative_page - 1) * 64 + processed_images) / (self.page_count * 64) * 100))
        self.progress_updated.emit(progress, filename)
    
    def _apply_dynamic_delay(self):
        """动态调整延迟 - 性能优化版本
        
        优化点:
        1. 完全移除延迟，让并发控制来管理速度
        2. 只在失败率极高时才添加延迟
        3. 根据失败率动态调整
        """
        if not self.is_running:
            return
        
        total_processed = self.success_count + self.failed_count
        if total_processed > 20:  # 增加样本数量（10->20）
            failure_rate = self.failed_count / total_processed
            if failure_rate > 0.5:  # 失败率超过50%才延迟（30%->50%）
                time.sleep(0.05)  # 50毫秒
            # 否则不延迟，完全依靠并发控制
    
    def stop(self):
        """停止下载并保存状态"""
        logger.info("正在停止下载...")
        self.is_running = False
        
        # 保存状态
        resume_state = {
            'start_page': self.start_page,
            'current_page': self.current_page,
            'processed_urls': list(self.processed_urls),
            'downloaded_files': list(self.downloaded_files),
            'base_url': self.base_url,
            'page_count': self.page_count,
            'download_dir': self.download_dir,
            'total_images': self.total_images,
            'downloaded_images': self.downloaded_images,
            'duplicate_images': self.duplicate_images,
            'unique_images_to_download': self.unique_images_to_download,
            'concurrent_downloads': self.concurrent_downloads
        }
        
        try:
            state_file = os.path.join(self.download_dir, '.download_state.json')
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(resume_state, f, ensure_ascii=False, indent=2)
            logger.info("下载状态已保存")
        except Exception as e:
            logger.error(f"保存下载状态失败: {str(e)}")
    
    def _save_download_state(self):
        """保存下载状态"""
        state = {
            'start_page': self.start_page,
            'current_page': self.current_page,
            'downloaded_files': list(self.downloaded_files),
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'skipped_count': self.skipped_count,
            'total_images': self.total_images,
            'downloaded_images': self.downloaded_images,
            'duplicate_images': self.duplicate_images,
            'unique_images_to_download': self.unique_images_to_download,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(os.path.join(self.download_dir, 'download_state.json'), 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存下载状态失败: {str(e)}")
    
    def _load_download_state(self) -> bool:
        """加载下载状态"""
        state_file = os.path.join(self.download_dir, 'download_state.json')
        if not os.path.exists(state_file):
            return False
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.start_page = state.get('start_page', 1)
            self.current_page = state.get('current_page', self.start_page)
            self.downloaded_files = set(state.get('downloaded_files', []))
            self.success_count = state.get('success_count', 0)
            self.failed_count = state.get('failed_count', 0)
            self.skipped_count = state.get('skipped_count', 0)
            self.total_images = state.get('total_images', 0)
            self.downloaded_images = state.get('downloaded_images', 0)
            self.duplicate_images = state.get('duplicate_images', 0)
            self.unique_images_to_download = state.get('unique_images_to_download', 0)
            
            return True
        except Exception as e:
            logger.error(f"加载下载状态失败: {str(e)}")
            return False
