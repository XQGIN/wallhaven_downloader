# -*- coding: utf-8 -*-
"""
图标管理器
提供统一的图标系统，支持图标加载、缓存和主题适配
"""

from typing import Dict, Optional
from PyQt5.QtCore import QObject, Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QTransform
from PyQt5.QtWidgets import QPushButton, QWidget
from PyQt5.QtSvg import QSvgRenderer

try:
    from utils.logger import get_logger
    from ui.animation_manager import get_animation_manager
except ImportError:
    from ..utils.logger import get_logger
    from .animation_manager import get_animation_manager

logger = get_logger(__name__)


class IconManager(QObject):
    """
    图标管理器
    
    提供统一的图标访问接口，支持：
    - 多种图标尺寸（小、中、大）
    - 图标颜色自定义
    - 图标缓存机制
    - 主题颜色适配
    """
    
    # 图标尺寸定义
    SIZE_SMALL = 16
    SIZE_MEDIUM = 24
    SIZE_LARGE = 32
    
    # 内置图标名称映射（使用 Unicode 字符作为简单图标）
    ICON_UNICODE_MAP = {
        # 功能图标
        'download': '⬇',
        'upload': '⬆',
        'settings': '⚙',
        'search': '🔍',
        'refresh': '🔄',
        'delete': '🗑',
        'edit': '✏',
        'save': '💾',
        'open': '📂',
        'close': '✖',
        'add': '➕',
        'remove': '➖',
        'check': '✓',
        'error': '✖',
        'warning': '⚠',
        'info': 'ℹ',
        'help': '❓',
        'clear': '🗑',  # 清除
        'folder_open': '📂',  # 打开文件夹
        
        # 导航图标
        'home': '🏠',
        'back': '◀',
        'forward': '▶',
        'up': '▲',
        'down': '▼',
        'left': '◀',
        'right': '▶',
        
        # 媒体图标
        'play': '▶',
        'pause': '⏸',
        'stop': '⏹',
        'image': '🖼',
        'folder': '📁',
        
        # 状态图标
        'success': '✓',
        'loading': '⟳',
        'star': '★',
        'heart': '♥',
        'lock': '🔒',
        'unlock': '🔓',
        
        # 主题和设置图标
        'sun': '☀',  # 日间模式
        'moon': '🌙',  # 夜间模式
        'droplet': '💧',  # 水滴/透明度
        'globe': '🌐',  # 全球/语言
        'key': '🔑',  # API密钥
        'clock': '⏰',  # 时间/超时
        'layers': '📚',  # 层级/并发
        'check-circle': '✅',  # 检查圆圈
        
        # 性能和系统图标
        'cpu': '💻',  # CPU/处理器
        'zap': '⚡',  # 闪电/性能
        'sliders': '🎚',  # 滑块/调节
        'bug': '🐛',  # 调试
        'refresh-cw': '🔄',  # 刷新
    }
    
    def __init__(self):
        """初始化图标管理器"""
        super().__init__()
        self._icon_cache: Dict[str, QIcon] = {}  # 图标缓存
        self._animation_manager = get_animation_manager()
        
        logger.debug("IconManager 初始化完成")
    
    def get_icon(
        self,
        name: str,
        size: int = SIZE_MEDIUM,
        color: Optional[QColor] = None
    ) -> QIcon:
        """
        获取图标
        
        Args:
            name: 图标名称
            size: 图标尺寸（像素）
            color: 图标颜色，None 则使用主题文本颜色
            
        Returns:
            QIcon 对象
        """
        # 生成缓存键
        color_key = color.name() if color else "theme"
        cache_key = f"{name}_{size}_{color_key}"
        
        # 检查缓存
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        # 如果没有指定颜色，使用固定的浅色主题颜色
        if color is None:
            color = QColor(60, 60, 60)  # 深灰色文本
        
        # 创建图标
        icon = self._create_icon(name, size, color)
        
        # 缓存图标
        self._icon_cache[cache_key] = icon
        
        logger.debug(f"创建图标: {name}, 尺寸={size}, 颜色={color.name()}")
        return icon
    
    def _create_icon(self, name: str, size: int, color: QColor) -> QIcon:
        """
        创建图标
        
        Args:
            name: 图标名称
            size: 图标尺寸
            color: 图标颜色
            
        Returns:
            QIcon 对象
        """
        # 尝试从 Unicode 映射获取
        if name in self.ICON_UNICODE_MAP:
            return self._create_text_icon(self.ICON_UNICODE_MAP[name], size, color)
        
        # 如果找不到，返回默认图标
        logger.warning(f"未找到图标: {name}，使用默认图标")
        return self._create_default_icon(size, color)
    
    def _create_text_icon(self, text: str, size: int, color: QColor) -> QIcon:
        """
        从文本创建图标
        
        Args:
            text: 文本内容（通常是 Unicode 字符）
            size: 图标尺寸
            color: 文本颜色
            
        Returns:
            QIcon 对象
        """
        # 创建 pixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        # 绘制文本
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # 设置字体
        font = painter.font()
        font.setPixelSize(int(size * 0.8))  # 字体大小为图标尺寸的 80%
        painter.setFont(font)
        
        # 设置颜色
        painter.setPen(color)
        
        # 绘制文本（居中）
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        
        return QIcon(pixmap)
    
    def _create_default_icon(self, size: int, color: QColor) -> QIcon:
        """
        创建默认图标（一个简单的方块）
        
        Args:
            size: 图标尺寸
            color: 图标颜色
            
        Returns:
            QIcon 对象
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制一个圆角矩形作为默认图标
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        margin = size // 4
        painter.drawRoundedRect(margin, margin, size - 2 * margin, size - 2 * margin, 2, 2)
        painter.end()
        
        return QIcon(pixmap)
    
    def create_icon_button(
        self,
        icon_name: str,
        tooltip: str = "",
        size: int = SIZE_MEDIUM,
        color: Optional[QColor] = None,
        parent: Optional[QWidget] = None,
        enable_hover_animation: bool = True
    ) -> QPushButton:
        """
        创建图标按钮
        
        Args:
            icon_name: 图标名称
            tooltip: 工具提示文本
            size: 图标尺寸
            color: 图标颜色
            parent: 父组件
            enable_hover_animation: 是否启用悬停动画
            
        Returns:
            QPushButton 对象（如果启用动画则返回 AnimatedIconButton）
        """
        if enable_hover_animation:
            button = AnimatedIconButton(parent)
        else:
            button = QPushButton(parent)
        
        # 设置图标
        icon = self.get_icon(icon_name, size, color)
        button.setIcon(icon)
        button.setIconSize(QSize(size, size))
        
        # 设置工具提示
        if tooltip:
            button.setToolTip(tooltip)
        
        # 设置按钮尺寸（确保符合最小点击区域 44x44px）
        button_size = max(44, size + 16)  # 图标尺寸 + 内边距
        button.setFixedSize(button_size, button_size)
        
        # 设置样式
        button.setStyleSheet(self._get_icon_button_stylesheet())
        
        logger.debug(f"创建图标按钮: {icon_name}, 工具提示={tooltip}, 动画={enable_hover_animation}")
        return button
    
    def _get_icon_button_stylesheet(self) -> str:
        """
        获取图标按钮样式表
        
        Returns:
            样式表字符串
        """
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 20);
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 40);
            }}
            QPushButton:disabled {{
                opacity: 0.5;
            }}
        """
    
    def _rgba(self, color: QColor) -> str:
        """
        将 QColor 转换为 rgba 字符串
        
        Args:
            color: QColor 对象
            
        Returns:
            rgba 字符串
        """
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
    
    def clear_cache(self):
        """清除图标缓存"""
        self._icon_cache.clear()
        logger.debug("图标缓存已清除")
    
    def get_cache_size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            缓存中的图标数量
        """
        return len(self._icon_cache)
    
    def preload_icons(self, icon_names: list, size: int = SIZE_MEDIUM):
        """
        预加载图标
        
        Args:
            icon_names: 图标名称列表
            size: 图标尺寸
        """
        for name in icon_names:
            self.get_icon(name, size)
        
        logger.debug(f"预加载了 {len(icon_names)} 个图标")
    
    def get_themed_icon(self, name: str, size: int = SIZE_MEDIUM) -> QIcon:
        """
        获取主题适配的图标（自动使用主题颜色）
        
        Args:
            name: 图标名称
            size: 图标尺寸
            
        Returns:
            QIcon 对象
        """
        return self.get_icon(name, size, None)
    
    def get_colored_icon(
        self,
        name: str,
        color: QColor,
        size: int = SIZE_MEDIUM
    ) -> QIcon:
        """
        获取指定颜色的图标
        
        Args:
            name: 图标名称
            color: 图标颜色
            size: 图标尺寸
            
        Returns:
            QIcon 对象
        """
        return self.get_icon(name, size, color)


# 全局单例
_icon_manager_instance: Optional[IconManager] = None


def get_icon_manager() -> IconManager:
    """
    获取图标管理器单例
    
    Returns:
        IconManager 实例
    """
    global _icon_manager_instance
    if _icon_manager_instance is None:
        _icon_manager_instance = IconManager()
    return _icon_manager_instance


class AnimatedIconButton(QPushButton):
    """
    支持悬停动画的图标按钮
    
    提供两种动画效果：
    1. 缩放动画：悬停时图标轻微放大
    2. 旋转动画：悬停时图标旋转
    """
    
    def __init__(self, parent: Optional[QWidget] = None, animation_type: str = 'scale'):
        """
        初始化动画图标按钮
        
        Args:
            parent: 父组件
            animation_type: 动画类型 ('scale' 或 'rotate')
        """
        super().__init__(parent)
        self.animation_type = animation_type
        self._scale = 1.0
        self._rotation = 0.0
        
        # 创建动画
        self._scale_animation = QPropertyAnimation(self, b"scale")
        self._scale_animation.setDuration(150)
        self._scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self._rotation_animation = QPropertyAnimation(self, b"rotation")
        self._rotation_animation.setDuration(200)
        self._rotation_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        
        if self.animation_type == 'scale':
            # 缩放动画：放大到 1.15 倍
            self._scale_animation.setStartValue(self._scale)
            self._scale_animation.setEndValue(1.15)
            self._scale_animation.start()
        elif self.animation_type == 'rotate':
            # 旋转动画：旋转 15 度
            self._rotation_animation.setStartValue(self._rotation)
            self._rotation_animation.setEndValue(15.0)
            self._rotation_animation.start()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        
        if self.animation_type == 'scale':
            # 恢复原始大小
            self._scale_animation.setStartValue(self._scale)
            self._scale_animation.setEndValue(1.0)
            self._scale_animation.start()
        elif self.animation_type == 'rotate':
            # 恢复原始角度
            self._rotation_animation.setStartValue(self._rotation)
            self._rotation_animation.setEndValue(0.0)
            self._rotation_animation.start()
    
    def paintEvent(self, event):
        """重写绘制事件以应用变换"""
        if self._scale != 1.0 or self._rotation != 0.0:
            # 保存当前图标
            icon = self.icon()
            if not icon.isNull():
                # 创建变换后的图标
                icon_size = self.iconSize()
                pixmap = icon.pixmap(icon_size)
                
                # 应用变换
                transform = QTransform()
                transform.translate(icon_size.width() / 2, icon_size.height() / 2)
                if self._scale != 1.0:
                    transform.scale(self._scale, self._scale)
                if self._rotation != 0.0:
                    transform.rotate(self._rotation)
                transform.translate(-icon_size.width() / 2, -icon_size.height() / 2)
                
                transformed_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                
                # 临时设置变换后的图标
                self.setIcon(QIcon(transformed_pixmap))
        
        super().paintEvent(event)
    
    def get_scale(self) -> float:
        """获取缩放比例"""
        return self._scale
    
    def set_scale(self, scale: float):
        """设置缩放比例"""
        self._scale = scale
        self.update()
    
    def get_rotation(self) -> float:
        """获取旋转角度"""
        return self._rotation
    
    def set_rotation(self, rotation: float):
        """设置旋转角度"""
        self._rotation = rotation
        self.update()
    
    # 定义属性以便 QPropertyAnimation 使用
    scale = pyqtProperty(float, get_scale, set_scale)
    rotation = pyqtProperty(float, get_rotation, set_rotation)

