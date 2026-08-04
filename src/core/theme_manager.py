# -*- coding: utf-8 -*-
"""
主题管理器
提供统一的主题颜色管理和系统主题检测功能
"""

import sys
from enum import Enum
from typing import Dict, Tuple, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class ThemeMode(Enum):
    """主题模式枚举"""
    LIGHT = "浅色"
    DARK = "深色"
    AUTO = "自动"


class ThemeColors:
    """主题颜色定义"""
    
    # 浅色主题
    LIGHT = {
        # 背景色
        "background": QColor(240, 240, 240),
        "surface": QColor(255, 255, 255),
        "surface_hover": QColor(250, 250, 250),
        
        # 玻璃效果
        "glass_normal": QColor(255, 255, 255, 180),
        "glass_hover": QColor(255, 255, 255, 220),
        "glass_pressed": QColor(245, 245, 245, 200),
        
        # 文字色
        "text_primary": QColor(51, 51, 51),
        "text_secondary": QColor(102, 102, 102),
        "text_disabled": QColor(189, 189, 189),
        
        # 边框色
        "border": QColor(204, 204, 204),
        "border_focus": QColor(0, 122, 204),
        "border_hover": QColor(153, 153, 153),
        
        # 功能色
        "primary": QColor(0, 122, 204),
        "success": QColor(40, 167, 69),
        "warning": QColor(255, 193, 7),
        "error": QColor(220, 53, 69),
        "info": QColor(23, 162, 184),
        
        # 阴影色
        "shadow": QColor(0, 0, 0, 30),
        "highlight": QColor(255, 255, 255, 100),
        
        # 下拉箭头
        "dropdown_arrow": QColor(51, 51, 51)
    }
    
    # 深色主题
    DARK = {
        # 背景色
        "background": QColor(45, 45, 48),
        "surface": QColor(37, 37, 38),
        "surface_hover": QColor(51, 51, 51),
        
        # 玻璃效果
        "glass_normal": QColor(45, 45, 48, 180),
        "glass_hover": QColor(60, 60, 63, 220),
        "glass_pressed": QColor(30, 30, 32, 200),
        
        # 文字色
        "text_primary": QColor(255, 255, 255),
        "text_secondary": QColor(204, 204, 204),
        "text_disabled": QColor(128, 128, 128),
        
        # 边框色
        "border": QColor(63, 63, 70),
        "border_focus": QColor(0, 122, 204),
        "border_hover": QColor(90, 90, 90),
        
        # 功能色
        "primary": QColor(0, 122, 204),
        "success": QColor(40, 167, 69),
        "warning": QColor(255, 193, 7),
        "error": QColor(220, 53, 69),
        "info": QColor(23, 162, 184),
        
        # 阴影色
        "shadow": QColor(0, 0, 0, 60),
        "highlight": QColor(255, 255, 255, 30),
        
        # 下拉箭头
        "dropdown_arrow": QColor(255, 255, 255)
    }


class ThemeManager(QObject):
    """主题管理器"""
    
    # 主题变更信号
    theme_changed = pyqtSignal(str)  # 发射新主题名称
    
    def __init__(self):
        """初始化主题管理器"""
        super().__init__()
        self._current_mode = ThemeMode.LIGHT
        self._auto_mode_enabled = False
        self._system_theme = self._detect_system_theme()
        
        logger.info(f"主题管理器初始化完成，系统主题: {self._system_theme}")
    
    def _detect_system_theme(self) -> ThemeMode:
        """
        检测系统主题
        
        Returns:
            ThemeMode: 系统主题模式
        """
        try:
            # Windows 10/11 检测
            if sys.platform == "win32":
                try:
                    import winreg
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(
                        registry,
                        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                    )
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    
                    return ThemeMode.LIGHT if value == 1 else ThemeMode.DARK
                except Exception as e:
                    logger.debug(f"Windows 主题检测失败: {e}")
            
            # macOS 检测
            elif sys.platform == "darwin":
                try:
                    import subprocess
                    result = subprocess.run(
                        ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                        capture_output=True,
                        text=True
                    )
                    return ThemeMode.DARK if result.returncode == 0 else ThemeMode.LIGHT
                except Exception as e:
                    logger.debug(f"macOS 主题检测失败: {e}")
            
            # Linux 检测（通过 Qt 调色板）
            elif sys.platform.startswith("linux"):
                app = QApplication.instance()
                if app:
                    palette = app.palette()
                    window_color = palette.color(QPalette.Window)
                    # 如果窗口背景色较暗，则为深色主题
                    brightness = (window_color.red() + window_color.green() + window_color.blue()) / 3
                    return ThemeMode.DARK if brightness < 128 else ThemeMode.LIGHT
        
        except Exception as e:
            logger.warning(f"系统主题检测失败: {e}")
        
        # 默认返回浅色主题
        return ThemeMode.LIGHT
    
    def set_theme(self, theme: str) -> None:
        """
        设置主题
        
        Args:
            theme: 主题名称 ("浅色", "深色", "自动")
        """
        if theme == ThemeMode.AUTO.value:
            self._auto_mode_enabled = True
            self._current_mode = self._system_theme
            logger.info(f"启用自动主题模式，当前系统主题: {self._current_mode.value}")
        else:
            self._auto_mode_enabled = False
            if theme == ThemeMode.LIGHT.value:
                self._current_mode = ThemeMode.LIGHT
            elif theme == ThemeMode.DARK.value:
                self._current_mode = ThemeMode.DARK
            else:
                logger.warning(f"未知主题: {theme}，使用浅色主题")
                self._current_mode = ThemeMode.LIGHT
        
        # 发射主题变更信号
        self.theme_changed.emit(self._current_mode.value)
    
    def get_current_theme(self) -> str:
        """
        获取当前主题名称
        
        Returns:
            str: 主题名称
        """
        return self._current_mode.value
    
    def is_dark_mode(self) -> bool:
        """
        判断当前是否为深色模式
        
        Returns:
            bool: 是否为深色模式
        """
        return self._current_mode == ThemeMode.DARK
    
    def get_color(self, color_name: str) -> QColor:
        """
        获取指定颜色
        
        Args:
            color_name: 颜色名称
            
        Returns:
            QColor: 颜色对象
        """
        colors = ThemeColors.DARK if self.is_dark_mode() else ThemeColors.LIGHT
        return colors.get(color_name, QColor(0, 0, 0))
    
    def get_all_colors(self) -> Dict[str, QColor]:
        """
        获取当前主题的所有颜色
        
        Returns:
            Dict[str, QColor]: 颜色字典
        """
        return ThemeColors.DARK if self.is_dark_mode() else ThemeColors.LIGHT
    
    def get_stylesheet(self, widget_type: str = "main") -> str:
        """
        获取指定组件的样式表
        
        Args:
            widget_type: 组件类型 ("main", "button", "input", "combobox", etc.)
            
        Returns:
            str: Qt 样式表字符串
        """
        colors = self.get_all_colors()
        
        if widget_type == "main":
            return f"""
                QMainWindow {{
                    background-color: {colors["background"].name()};
                    color: {colors["text_primary"].name()};
                }}
            """
        
        elif widget_type == "button":
            return f"""
                QPushButton {{
                    background-color: {self._rgba(colors["glass_normal"])};
                    border: 1px solid {colors["border"].name()};
                    border-radius: 5px;
                    padding: 8px 15px;
                    color: {colors["text_primary"].name()};
                }}
                QPushButton:hover {{
                    background-color: {self._rgba(colors["glass_hover"])};
                    border-color: {colors["border_hover"].name()};
                }}
                QPushButton:pressed {{
                    background-color: {self._rgba(colors["glass_pressed"])};
                }}
                QPushButton:disabled {{
                    color: {colors["text_disabled"].name()};
                    background-color: {self._rgba(colors["surface"])};
                }}
            """
        
        elif widget_type == "input":
            return f"""
                QLineEdit {{
                    background-color: {self._rgba(colors["glass_normal"])};
                    border: 1px solid {colors["border"].name()};
                    border-radius: 5px;
                    padding: 5px;
                    color: {colors["text_primary"].name()};
                }}
                QLineEdit:hover {{
                    background-color: {self._rgba(colors["glass_hover"])};
                }}
                QLineEdit:focus {{
                    border-color: {colors["border_focus"].name()};
                }}
            """
        
        elif widget_type == "combobox":
            return f"""
                QComboBox {{
                    background-color: {self._rgba(colors["glass_normal"])};
                    border: 1px solid {colors["border"].name()};
                    border-radius: 5px;
                    padding: 5px;
                    color: {colors["text_primary"].name()};
                    min-height: 20px;
                }}
                QComboBox:hover {{
                    background-color: {self._rgba(colors["glass_hover"])};
                    border-color: {colors["border_hover"].name()};
                }}
                QComboBox:focus {{
                    border-color: {colors["border_focus"].name()};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 20px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid {colors["dropdown_arrow"].name()};
                    width: 0px;
                    height: 0px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {colors["surface"].name()};
                    border: 1px solid {colors["border"].name()};
                    selection-background-color: {colors["primary"].name()};
                    selection-color: white;
                    color: {colors["text_primary"].name()};
                }}
            """
        
        elif widget_type == "groupbox":
            return f"""
                QGroupBox {{
                    border: 1px solid {colors["border"].name()};
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                    color: {colors["text_primary"].name()};
                    font-weight: bold;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                    background-color: {colors["background"].name()};
                }}
            """
        
        elif widget_type == "label":
            return f"""
                QLabel {{
                    color: {colors["text_primary"].name()};
                }}
            """
        
        return ""
    
    def _rgba(self, color: QColor) -> str:
        """
        将 QColor 转换为 rgba 字符串
        
        Args:
            color: QColor 对象
            
        Returns:
            str: rgba 字符串
        """
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
    
    def refresh_system_theme(self) -> None:
        """刷新系统主题检测（当用户改变系统主题时调用）"""
        if self._auto_mode_enabled:
            old_theme = self._current_mode
            self._system_theme = self._detect_system_theme()
            self._current_mode = self._system_theme
            
            if old_theme != self._current_mode:
                logger.info(f"系统主题已更改: {old_theme.value} -> {self._current_mode.value}")
                self.theme_changed.emit(self._current_mode.value)


# 全局主题管理器实例
_theme_manager_instance: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """
    获取全局主题管理器实例（单例模式）
    
    Returns:
        ThemeManager: 主题管理器实例
    """
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager()
    return _theme_manager_instance
