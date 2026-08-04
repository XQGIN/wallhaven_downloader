"""
文本缩放管理器

支持文本缩放（100%-200%），确保布局不破坏
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QApplication
from PyQt5.QtGui import QFont
from typing import List, Dict, Optional

try:
    from utils.logger import get_logger
except ImportError:
    from .logger import get_logger

logger = get_logger(__name__)


class TextScaleManager(QObject):
    """
    文本缩放管理器
    
    支持文本缩放（100%-200%），确保布局不破坏
    
    需求：16.7 - 支持文本缩放，不破坏布局
    """
    
    # 信号
    scale_changed = pyqtSignal(float)  # 缩放比例变化
    
    # 单例实例
    _instance = None
    
    # 缩放范围
    MIN_SCALE = 1.0  # 100%
    MAX_SCALE = 2.0  # 200%
    DEFAULT_SCALE = 1.0  # 默认 100%
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        super().__init__()
        self._initialized = True
        
        # 当前缩放比例
        self._scale = self.DEFAULT_SCALE
        
        # 注册的组件列表
        self._registered_widgets: List[QWidget] = []
        
        # 原始字体大小缓存
        self._original_font_sizes: Dict[QWidget, int] = {}
        
        # 原始最小尺寸缓存
        self._original_min_sizes: Dict[QWidget, tuple] = {}
        
        logger.info("文本缩放管理器初始化完成")
    
    def register_widget(self, widget: QWidget):
        """
        注册组件以支持文本缩放
        
        Args:
            widget: 要注册的组件
        """
        if widget in self._registered_widgets:
            return
        
        self._registered_widgets.append(widget)
        
        # 缓存原始字体大小
        font = widget.font()
        self._original_font_sizes[widget] = font.pointSize() if font.pointSize() > 0 else 10
        
        # 缓存原始最小尺寸
        self._original_min_sizes[widget] = (widget.minimumWidth(), widget.minimumHeight())
        
        # 应用当前缩放
        if self._scale != self.DEFAULT_SCALE:
            self._apply_scale_to_widget(widget, self._scale)
        
        logger.debug(f"注册组件用于文本缩放: {widget.__class__.__name__}")
    
    def unregister_widget(self, widget: QWidget):
        """
        取消注册组件
        
        Args:
            widget: 要取消注册的组件
        """
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)
            
            # 清除缓存
            if widget in self._original_font_sizes:
                del self._original_font_sizes[widget]
            if widget in self._original_min_sizes:
                del self._original_min_sizes[widget]
            
            logger.debug(f"取消注册组件: {widget.__class__.__name__}")
    
    def register_widget_tree(self, root_widget: QWidget):
        """
        递归注册组件树中的所有文本组件
        
        Args:
            root_widget: 根组件
        """
        # 注册根组件
        if self._is_text_widget(root_widget):
            self.register_widget(root_widget)
        
        # 递归注册子组件
        for child in root_widget.findChildren(QWidget):
            if self._is_text_widget(child):
                self.register_widget(child)
        
        logger.debug(f"注册组件树: {root_widget.__class__.__name__}")
    
    def _is_text_widget(self, widget: QWidget) -> bool:
        """
        判断组件是否包含文本
        
        Args:
            widget: 组件
            
        Returns:
            bool: 是否包含文本
        """
        return isinstance(widget, (QLabel, QPushButton, QLineEdit, QTextEdit))
    
    def set_scale(self, scale: float):
        """
        设置文本缩放比例
        
        Args:
            scale: 缩放比例（1.0 = 100%, 2.0 = 200%）
        """
        # 限制范围
        scale = max(self.MIN_SCALE, min(self.MAX_SCALE, scale))
        
        if scale == self._scale:
            return
        
        old_scale = self._scale
        self._scale = scale
        
        # 应用到所有注册的组件
        for widget in self._registered_widgets:
            self._apply_scale_to_widget(widget, scale)
        
        # 发射信号
        self.scale_changed.emit(scale)
        
        logger.info(f"文本缩放比例已更改: {old_scale:.0%} -> {scale:.0%}")
    
    def _apply_scale_to_widget(self, widget: QWidget, scale: float):
        """
        应用缩放到组件
        
        Args:
            widget: 目标组件
            scale: 缩放比例
        """
        try:
            # 获取原始字体大小
            original_size = self._original_font_sizes.get(widget, 10)
            
            # 计算新的字体大小
            new_size = int(original_size * scale)
            
            # 应用新字体大小
            font = widget.font()
            font.setPointSize(new_size)
            widget.setFont(font)
            
            # 调整最小尺寸以适应缩放后的文本
            if widget in self._original_min_sizes:
                original_min_width, original_min_height = self._original_min_sizes[widget]
                
                # 根据缩放比例调整最小尺寸
                new_min_width = int(original_min_width * scale) if original_min_width > 0 else 0
                new_min_height = int(original_min_height * scale) if original_min_height > 0 else 0
                
                if new_min_width > 0 or new_min_height > 0:
                    widget.setMinimumSize(new_min_width, new_min_height)
            
            # 调整组件大小以适应新的文本
            widget.adjustSize()
            
            # 更新布局
            if widget.layout():
                widget.layout().update()
            
            logger.debug(f"应用文本缩放到 {widget.__class__.__name__}: {scale:.0%}")
            
        except Exception as e:
            logger.error(f"应用文本缩放失败: {e}")
    
    def get_scale(self) -> float:
        """
        获取当前缩放比例
        
        Returns:
            float: 当前缩放比例
        """
        return self._scale
    
    def get_scale_percentage(self) -> int:
        """
        获取当前缩放百分比
        
        Returns:
            int: 缩放百分比（100-200）
        """
        return int(self._scale * 100)
    
    def set_scale_percentage(self, percentage: int):
        """
        设置缩放百分比
        
        Args:
            percentage: 缩放百分比（100-200）
        """
        scale = percentage / 100.0
        self.set_scale(scale)
    
    def reset_scale(self):
        """重置缩放到默认值（100%）"""
        self.set_scale(self.DEFAULT_SCALE)
        logger.info("文本缩放已重置到默认值")
    
    def increase_scale(self, step: float = 0.1):
        """
        增加缩放比例
        
        Args:
            step: 增加步长（默认 0.1 = 10%）
        """
        new_scale = self._scale + step
        self.set_scale(new_scale)
    
    def decrease_scale(self, step: float = 0.1):
        """
        减少缩放比例
        
        Args:
            step: 减少步长（默认 0.1 = 10%）
        """
        new_scale = self._scale - step
        self.set_scale(new_scale)
    
    def apply_to_application(self, app: QApplication):
        """
        应用文本缩放到整个应用程序
        
        Args:
            app: QApplication 实例
        """
        # 获取所有顶层窗口
        for window in app.topLevelWidgets():
            self.register_widget_tree(window)
        
        logger.info("文本缩放已应用到整个应用程序")
    
    def get_recommended_scale_for_dpi(self, dpi: int) -> float:
        """
        根据 DPI 获取推荐的缩放比例
        
        Args:
            dpi: 屏幕 DPI
            
        Returns:
            float: 推荐的缩放比例
        """
        # 标准 DPI 为 96
        standard_dpi = 96
        
        # 计算推荐缩放
        recommended_scale = dpi / standard_dpi
        
        # 限制在有效范围内
        recommended_scale = max(self.MIN_SCALE, min(self.MAX_SCALE, recommended_scale))
        
        return recommended_scale
    
    def auto_scale_for_screen(self):
        """根据屏幕 DPI 自动调整缩放"""
        try:
            from PyQt5.QtWidgets import QApplication
            
            # 获取主屏幕
            screen = QApplication.primaryScreen()
            if screen:
                dpi = screen.logicalDotsPerInch()
                recommended_scale = self.get_recommended_scale_for_dpi(int(dpi))
                
                # 只在推荐缩放大于当前缩放时应用
                if recommended_scale > self._scale:
                    self.set_scale(recommended_scale)
                    logger.info(f"根据屏幕 DPI ({dpi}) 自动调整缩放到 {recommended_scale:.0%}")
        except Exception as e:
            logger.error(f"自动缩放失败: {e}")
    
    def clear_all(self):
        """清除所有注册的组件"""
        self._registered_widgets.clear()
        self._original_font_sizes.clear()
        self._original_min_sizes.clear()
        logger.info("已清除所有注册的组件")


# 全局访问函数
_text_scale_manager = None

def get_text_scale_manager() -> TextScaleManager:
    """获取文本缩放管理器单例"""
    global _text_scale_manager
    if _text_scale_manager is None:
        _text_scale_manager = TextScaleManager()
    return _text_scale_manager
