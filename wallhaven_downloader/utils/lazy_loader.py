# -*- coding: utf-8 -*-
"""
延迟加载管理器

实现延迟加载非关键组件，优化启动性能
需求：14.8 - 启动渲染性能
"""

import time
from typing import Callable, Dict, List, Optional, Any
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

try:
    from utils.logger import get_logger
except ImportError:
    from wallhaven_downloader.utils.logger import get_logger

logger = get_logger(__name__)


class LazyLoadTask:
    """延迟加载任务"""
    
    def __init__(
        self,
        name: str,
        loader: Callable,
        priority: int = 0,
        delay: int = 0,
        dependencies: Optional[List[str]] = None
    ):
        """
        初始化延迟加载任务
        
        Args:
            name: 任务名称
            loader: 加载函数
            priority: 优先级（数字越小优先级越高）
            delay: 延迟时间（毫秒）
            dependencies: 依赖的任务名称列表
        """
        self.name = name
        self.loader = loader
        self.priority = priority
        self.delay = delay
        self.dependencies = dependencies or []
        self.loaded = False
        self.loading = False
        self.result = None
        self.error = None


class LazyLoader(QObject):
    """
    延迟加载管理器
    
    负责管理和调度延迟加载任务，优化启动性能
    
    功能：
    - 延迟加载非关键组件
    - 优化资源加载顺序
    - 分阶段初始化UI组件
    - 依赖管理
    """
    
    # 信号
    task_started = pyqtSignal(str)  # 任务开始
    task_completed = pyqtSignal(str, object)  # 任务完成（任务名，结果）
    task_failed = pyqtSignal(str, str)  # 任务失败（任务名，错误信息）
    all_tasks_completed = pyqtSignal()  # 所有任务完成
    
    def __init__(self):
        super().__init__()
        self.tasks: Dict[str, LazyLoadTask] = {}
        self.task_queue: List[LazyLoadTask] = []
        self.loading_tasks: List[str] = []
        self.max_concurrent_tasks = 3  # 最大并发任务数
        self.is_loading = False
        self.start_time = 0
        
        logger.info("延迟加载管理器初始化")
    
    def register_task(
        self,
        name: str,
        loader: Callable,
        priority: int = 0,
        delay: int = 0,
        dependencies: Optional[List[str]] = None
    ):
        """
        注册延迟加载任务
        
        Args:
            name: 任务名称
            loader: 加载函数
            priority: 优先级（数字越小优先级越高）
            delay: 延迟时间（毫秒）
            dependencies: 依赖的任务名称列表
        """
        if name in self.tasks:
            logger.warning(f"任务 {name} 已存在，将被覆盖")
        
        task = LazyLoadTask(name, loader, priority, delay, dependencies)
        self.tasks[name] = task
        logger.debug(f"注册延迟加载任务: {name}, 优先级: {priority}, 延迟: {delay}ms")
    
    def start_loading(self):
        """开始加载所有任务"""
        if self.is_loading:
            logger.warning("延迟加载已在进行中")
            return
        
        self.is_loading = True
        self.start_time = time.time()
        logger.info("开始延迟加载")
        
        # 构建任务队列（按优先级排序）
        self._build_task_queue()
        
        # 开始处理任务队列
        self._process_queue()
    
    def _build_task_queue(self):
        """构建任务队列"""
        # 按优先级排序任务
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: (t.priority, t.delay)
        )
        
        self.task_queue = sorted_tasks
        logger.debug(f"任务队列已构建，共 {len(self.task_queue)} 个任务")
    
    def _process_queue(self):
        """处理任务队列"""
        if not self.task_queue and not self.loading_tasks:
            # 所有任务完成
            self._on_all_tasks_completed()
            return
        
        # 检查是否可以启动新任务
        while (len(self.loading_tasks) < self.max_concurrent_tasks and 
               self.task_queue):
            # 获取下一个可以执行的任务
            task = self._get_next_executable_task()
            
            if task is None:
                # 没有可执行的任务，等待当前任务完成
                break
            
            # 启动任务
            self._start_task(task)
    
    def _get_next_executable_task(self) -> Optional[LazyLoadTask]:
        """获取下一个可以执行的任务"""
        for task in self.task_queue:
            # 检查依赖是否已完成
            if self._check_dependencies(task):
                self.task_queue.remove(task)
                return task
        
        return None
    
    def _check_dependencies(self, task: LazyLoadTask) -> bool:
        """检查任务的依赖是否已完成"""
        for dep_name in task.dependencies:
            if dep_name not in self.tasks:
                logger.error(f"任务 {task.name} 的依赖 {dep_name} 不存在")
                return False
            
            dep_task = self.tasks[dep_name]
            if not dep_task.loaded:
                return False
        
        return True
    
    def _start_task(self, task: LazyLoadTask):
        """启动任务"""
        task.loading = True
        self.loading_tasks.append(task.name)
        
        logger.debug(f"启动任务: {task.name}")
        self.task_started.emit(task.name)
        
        # 如果有延迟，使用定时器
        if task.delay > 0:
            QTimer.singleShot(task.delay, lambda: self._execute_task(task))
        else:
            self._execute_task(task)
    
    def _execute_task(self, task: LazyLoadTask):
        """执行任务"""
        try:
            start_time = time.time()
            
            # 执行加载函数
            result = task.loader()
            
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"任务 {task.name} 完成，耗时: {elapsed:.2f}ms")
            
            # 标记任务完成
            task.loaded = True
            task.loading = False
            task.result = result
            
            # 从加载列表中移除
            if task.name in self.loading_tasks:
                self.loading_tasks.remove(task.name)
            
            # 发送完成信号
            self.task_completed.emit(task.name, result)
            
            # 继续处理队列
            self._process_queue()
            
        except Exception as e:
            logger.error(f"任务 {task.name} 执行失败: {str(e)}")
            
            # 标记任务失败
            task.loaded = False
            task.loading = False
            task.error = str(e)
            
            # 从加载列表中移除
            if task.name in self.loading_tasks:
                self.loading_tasks.remove(task.name)
            
            # 发送失败信号
            self.task_failed.emit(task.name, str(e))
            
            # 继续处理队列（即使任务失败）
            self._process_queue()
    
    def _on_all_tasks_completed(self):
        """所有任务完成"""
        self.is_loading = False
        elapsed = (time.time() - self.start_time) * 1000
        
        # 统计结果
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.loaded)
        failed_tasks = sum(1 for t in self.tasks.values() if t.error is not None)
        
        logger.info(
            f"延迟加载完成，总耗时: {elapsed:.2f}ms, "
            f"总任务: {total_tasks}, 完成: {completed_tasks}, 失败: {failed_tasks}"
        )
        
        # 发送完成信号
        self.all_tasks_completed.emit()
    
    def get_task_result(self, name: str) -> Any:
        """获取任务结果"""
        if name not in self.tasks:
            logger.warning(f"任务 {name} 不存在")
            return None
        
        task = self.tasks[name]
        if not task.loaded:
            logger.warning(f"任务 {name} 尚未完成")
            return None
        
        return task.result
    
    def is_task_loaded(self, name: str) -> bool:
        """检查任务是否已加载"""
        if name not in self.tasks:
            return False
        
        return self.tasks[name].loaded
    
    def wait_for_task(self, name: str, timeout: int = 5000):
        """
        等待任务完成
        
        Args:
            name: 任务名称
            timeout: 超时时间（毫秒）
        """
        if name not in self.tasks:
            logger.warning(f"任务 {name} 不存在")
            return
        
        task = self.tasks[name]
        if task.loaded:
            return
        
        # 使用事件循环等待
        from PyQt5.QtCore import QEventLoop, QTimer
        
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        
        def on_completed(task_name, result):
            if task_name == name:
                loop.quit()
        
        self.task_completed.connect(on_completed)
        timer.start(timeout)
        loop.exec_()
        
        self.task_completed.disconnect(on_completed)
    
    def cancel_all_tasks(self):
        """取消所有未完成的任务"""
        logger.info("取消所有延迟加载任务")
        
        self.task_queue.clear()
        self.loading_tasks.clear()
        self.is_loading = False
    
    def reset(self):
        """重置延迟加载管理器"""
        logger.info("重置延迟加载管理器")
        
        self.tasks.clear()
        self.task_queue.clear()
        self.loading_tasks.clear()
        self.is_loading = False
        self.start_time = 0


# 全局延迟加载管理器实例
_lazy_loader_instance = None


def get_lazy_loader() -> LazyLoader:
    """获取全局延迟加载管理器实例"""
    global _lazy_loader_instance
    if _lazy_loader_instance is None:
        _lazy_loader_instance = LazyLoader()
    return _lazy_loader_instance
