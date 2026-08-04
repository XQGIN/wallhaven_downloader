# -*- coding: utf-8 -*-
"""
布局管理器 - 处理响应式布局和断点切换

该模块提供了响应式布局管理功能，支持根据窗口大小自动调整布局。
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QSize
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLayout
from typing import Optional, Callable, Dict, Any
from wallhaven_downloader.utils.logger import get_logger

logger = get_logger(__name__)


class LayoutManager(QObject):
    """
    布局管理器
    
    负责处理响应式布局和断点切换，支持：
    - 3 个断点定义（small, medium, large）
    - 窗口大小调整处理（带防抖）
    - 布局过渡动画
    - 响应式网格布局
    """
    
    # 断点定义（像素）
    BREAKPOINT_SMALL = 800      # 小窗口：< 800px
    BREAKPOINT_MEDIUM = 1200    # 中等窗口：800-1200px
    # 大窗口：> 1200px
    
    # 最小触摸目标尺寸（像素）
    MIN_TOUCH_TARGET_SIZE = 44
    
    # 布局过渡动画时长（毫秒）
    LAYOUT_TRANSITION_DURATION = 200
    
    # 防抖延迟（毫秒）
    DEBOUNCE_DELAY = 150
    
    # 断点改变信号
    breakpoint_changed = pyqtSignal(str)  # 新断点名称
    
    # 网格列数配置
    GRID_COLUMNS = {
        'small': (1, 2),    # 小窗口：1-2 列
        'medium': (3, 4),   # 中等窗口：3-4 列
        'large': (5, 6)     # 大窗口：5-6 列
    }
    
    def __init__(self, main_window: QMainWindow):
        """
        初始化布局管理器
        
        Args:
            main_window: 主窗口实例
        """
        super().__init__()
        self.main_window = main_window
        self.current_breakpoint = self._get_current_breakpoint()
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._on_resize_timeout)
        self._layout_callbacks: Dict[str, list] = {
            'small': [],
            'medium': [],
            'large': []
        }
        self._setup_resize_handler()
        
        logger.info(f"布局管理器初始化完成，当前断点: {self.current_breakpoint}")
    
    def _get_current_breakpoint(self) -> str:
        """
        获取当前断点
        
        根据主窗口的宽度判断当前应该使用哪个断点。
        
        Returns:
            str: 断点名称 ('small', 'medium', 'large')
        """
        width = self.main_window.width()
        
        if width < self.BREAKPOINT_SMALL:
            return 'small'
        elif width < self.BREAKPOINT_MEDIUM:
            return 'medium'
        else:
            return 'large'
    
    def _setup_resize_handler(self):
        """
        设置窗口大小调整处理器（带防抖）
        
        使用 QTimer 实现防抖，避免在窗口调整过程中频繁触发布局更新。
        """
        # 重写主窗口的 resizeEvent
        original_resize_event = self.main_window.resizeEvent
        
        def debounced_resize_event(event):
            # 调用原始的 resizeEvent
            original_resize_event(event)
            # 启动防抖定时器
            self._resize_timer.start(self.DEBOUNCE_DELAY)
        
        self.main_window.resizeEvent = debounced_resize_event
        logger.debug("窗口大小调整处理器已设置（带防抖）")
    
    def _on_resize_timeout(self):
        """
        防抖定时器超时处理
        
        当窗口大小调整停止后，检查断点是否改变，如果改变则应用新布局。
        """
        new_breakpoint = self._get_current_breakpoint()
        
        if new_breakpoint != self.current_breakpoint:
            logger.info(f"断点改变: {self.current_breakpoint} -> {new_breakpoint}")
            old_breakpoint = self.current_breakpoint
            self.current_breakpoint = new_breakpoint
            
            # 应用新断点的布局
            self.apply_layout_for_breakpoint(new_breakpoint)
            
            # 发送断点改变信号
            self.breakpoint_changed.emit(new_breakpoint)
    
    def apply_layout_for_breakpoint(self, breakpoint: str):
        """
        应用指定断点的布局
        
        执行所有注册到该断点的布局回调函数。
        
        Args:
            breakpoint: 断点名称 ('small', 'medium', 'large')
        """
        if breakpoint not in self._layout_callbacks:
            logger.warning(f"未知的断点: {breakpoint}")
            return
        
        logger.info(f"应用断点布局: {breakpoint}")
        
        # 执行所有注册的回调
        for callback in self._layout_callbacks[breakpoint]:
            try:
                callback()
            except Exception as e:
                logger.error(f"执行布局回调失败: {e}")
    
    def register_layout_callback(self, breakpoint: str, callback: Callable):
        """
        注册布局回调函数
        
        当切换到指定断点时，会调用注册的回调函数。
        
        Args:
            breakpoint: 断点名称 ('small', 'medium', 'large')
            callback: 回调函数
        """
        if breakpoint not in self._layout_callbacks:
            logger.warning(f"未知的断点: {breakpoint}")
            return
        
        self._layout_callbacks[breakpoint].append(callback)
        logger.debug(f"注册布局回调到断点: {breakpoint}")
    
    def get_grid_columns(self, breakpoint: Optional[str] = None) -> tuple:
        """
        获取指定断点的网格列数范围
        
        Args:
            breakpoint: 断点名称，如果为 None 则使用当前断点
        
        Returns:
            tuple: (最小列数, 最大列数)
        """
        if breakpoint is None:
            breakpoint = self.current_breakpoint
        
        return self.GRID_COLUMNS.get(breakpoint, (3, 4))
    
    def calculate_optimal_columns(self, 
                                  container_width: int, 
                                  item_width: int,
                                  breakpoint: Optional[str] = None) -> int:
        """
        计算最优列数
        
        根据容器宽度和项目宽度，在断点允许的范围内计算最优列数。
        
        Args:
            container_width: 容器宽度（像素）
            item_width: 单个项目宽度（像素）
            breakpoint: 断点名称，如果为 None 则使用当前断点
        
        Returns:
            int: 最优列数
        """
        min_cols, max_cols = self.get_grid_columns(breakpoint)
        
        # 根据容器宽度计算可以容纳的列数
        calculated_cols = max(1, container_width // item_width)
        
        # 限制在断点允许的范围内
        optimal_cols = max(min_cols, min(calculated_cols, max_cols))
        
        return optimal_cols
    
    def apply_responsive_grid(self, 
                             grid_layout: QGridLayout,
                             items: list,
                             item_width: int = 200,
                             item_height: int = 150):
        """
        应用响应式网格布局
        
        根据当前断点自动调整网格的列数。
        
        Args:
            grid_layout: 网格布局对象
            items: 要布局的项目列表（QWidget）
            item_width: 单个项目的宽度（像素）
            item_height: 单个项目的高度（像素）
        """
        if not items:
            return
        
        # 获取容器宽度
        container = grid_layout.parentWidget()
        if container:
            container_width = container.width()
        else:
            container_width = self.main_window.width()
        
        # 计算最优列数
        columns = self.calculate_optimal_columns(container_width, item_width)
        
        logger.debug(f"应用响应式网格: {len(items)} 项, {columns} 列")
        
        # 清空现有布局
        while grid_layout.count():
            item = grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # 重新布局
        for index, item in enumerate(items):
            row = index // columns
            col = index % columns
            grid_layout.addWidget(item, row, col)
    
    def ensure_minimum_size(self, widget: QWidget, 
                           min_width: Optional[int] = None,
                           min_height: Optional[int] = None):
        """
        确保组件满足最小尺寸要求
        
        特别是确保交互元素满足最小触摸目标尺寸（44x44px）。
        
        Args:
            widget: 要检查的组件
            min_width: 最小宽度，默认为 MIN_TOUCH_TARGET_SIZE
            min_height: 最小高度，默认为 MIN_TOUCH_TARGET_SIZE
        """
        if min_width is None:
            min_width = self.MIN_TOUCH_TARGET_SIZE
        if min_height is None:
            min_height = self.MIN_TOUCH_TARGET_SIZE
        
        current_min_size = widget.minimumSize()
        
        # 只在需要时更新最小尺寸
        if current_min_size.width() < min_width or current_min_size.height() < min_height:
            new_width = max(current_min_size.width(), min_width)
            new_height = max(current_min_size.height(), min_height)
            widget.setMinimumSize(QSize(new_width, new_height))
            logger.debug(f"更新组件最小尺寸: {widget.__class__.__name__} -> {new_width}x{new_height}")
    
    def get_current_breakpoint(self) -> str:
        """
        获取当前断点（公共方法）
        
        Returns:
            str: 当前断点名称
        """
        return self.current_breakpoint
    
    def get_breakpoint_info(self) -> Dict[str, Any]:
        """
        获取当前断点的详细信息
        
        Returns:
            dict: 包含断点名称、窗口宽度、列数范围等信息
        """
        width = self.main_window.width()
        min_cols, max_cols = self.get_grid_columns()
        
        return {
            'breakpoint': self.current_breakpoint,
            'window_width': width,
            'min_columns': min_cols,
            'max_columns': max_cols,
            'is_small': self.current_breakpoint == 'small',
            'is_medium': self.current_breakpoint == 'medium',
            'is_large': self.current_breakpoint == 'large'
        }
