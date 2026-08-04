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


class EnhancedColorPalette:
    """
    增强的颜色调色板
    提供完整的语义化颜色系统、渐变色支持和交互状态颜色
    """
    
    # 浅色主题
    LIGHT = {
        # 主色系
        "primary": QColor(0, 122, 204),
        "primary_hover": QColor(0, 102, 184),
        "primary_active": QColor(0, 82, 164),
        "primary_disabled": QColor(153, 204, 230),
        
        # 次要色系
        "secondary": QColor(108, 117, 125),
        "secondary_hover": QColor(88, 97, 105),
        "secondary_active": QColor(68, 77, 85),
        "secondary_disabled": QColor(181, 186, 190),
        
        # 语义色系 - 成功
        "success": QColor(40, 167, 69),
        "success_hover": QColor(33, 136, 56),
        "success_active": QColor(26, 105, 43),
        "success_disabled": QColor(147, 211, 166),
        
        # 语义色系 - 警告
        "warning": QColor(255, 193, 7),
        "warning_hover": QColor(224, 168, 0),
        "warning_active": QColor(193, 145, 0),
        "warning_disabled": QColor(255, 224, 130),
        
        # 语义色系 - 错误
        "error": QColor(220, 53, 69),
        "error_hover": QColor(200, 35, 51),
        "error_active": QColor(180, 17, 33),
        "error_disabled": QColor(237, 154, 164),
        
        # 语义色系 - 信息
        "info": QColor(23, 162, 184),
        "info_hover": QColor(17, 138, 158),
        "info_active": QColor(11, 114, 132),
        "info_disabled": QColor(139, 208, 218),
        
        # 中性色系
        "background": QColor(240, 240, 240),
        "surface": QColor(255, 255, 255),
        "surface_hover": QColor(250, 250, 250),
        "surface_active": QColor(245, 245, 245),
        "text_primary": QColor(33, 33, 33),
        "text_secondary": QColor(95, 95, 95),  # 调整为更深的灰色以满足 WCAG AA 标准
        "text_disabled": QColor(189, 189, 189),
        
        # 玻璃效果
        "glass_normal": QColor(255, 255, 255, 200),
        "glass_hover": QColor(255, 255, 255, 230),
        "glass_active": QColor(245, 245, 245, 210),
        "glass_disabled": QColor(250, 250, 250, 150),
        
        # 渐变色 - 主色渐变
        "gradient_primary_start": QColor(0, 122, 204),
        "gradient_primary_end": QColor(0, 153, 255),
        
        # 渐变色 - 成功渐变
        "gradient_success_start": QColor(40, 167, 69),
        "gradient_success_end": QColor(72, 199, 101),
        
        # 渐变色 - 警告渐变
        "gradient_warning_start": QColor(255, 193, 7),
        "gradient_warning_end": QColor(255, 213, 79),
        
        # 渐变色 - 错误渐变
        "gradient_error_start": QColor(220, 53, 69),
        "gradient_error_end": QColor(239, 83, 80),
        
        # 边框和阴影
        "border": QColor(204, 204, 204),
        "border_hover": QColor(153, 153, 153),
        "border_focus": QColor(0, 122, 204),
        "shadow": QColor(0, 0, 0, 30),
        "highlight": QColor(255, 255, 255, 100),
    }
    
    # 深色主题
    DARK = {
        # 主色系
        "primary": QColor(66, 153, 225),
        "primary_hover": QColor(86, 173, 245),
        "primary_active": QColor(46, 133, 205),
        "primary_disabled": QColor(66, 99, 125),
        
        # 次要色系
        "secondary": QColor(160, 174, 192),
        "secondary_hover": QColor(180, 194, 212),
        "secondary_active": QColor(140, 154, 172),
        "secondary_disabled": QColor(100, 114, 132),
        
        # 语义色系 - 成功
        "success": QColor(72, 187, 120),
        "success_hover": QColor(92, 207, 140),
        "success_active": QColor(52, 167, 100),
        "success_disabled": QColor(52, 107, 80),
        
        # 语义色系 - 警告
        "warning": QColor(255, 213, 79),
        "warning_hover": QColor(255, 233, 99),
        "warning_active": QColor(255, 193, 59),
        "warning_disabled": QColor(155, 133, 79),
        
        # 语义色系 - 错误
        "error": QColor(239, 83, 80),
        "error_hover": QColor(255, 103, 100),
        "error_active": QColor(219, 63, 60),
        "error_disabled": QColor(139, 63, 60),
        
        # 语义色系 - 信息
        "info": QColor(66, 184, 221),
        "info_hover": QColor(86, 204, 241),
        "info_active": QColor(46, 164, 201),
        "info_disabled": QColor(46, 104, 131),
        
        # 中性色系
        "background": QColor(26, 32, 44),
        "surface": QColor(45, 55, 72),
        "surface_hover": QColor(55, 65, 82),
        "surface_active": QColor(35, 45, 62),
        "text_primary": QColor(237, 242, 247),
        "text_secondary": QColor(160, 174, 192),
        "text_disabled": QColor(113, 128, 150),
        
        # 玻璃效果
        "glass_normal": QColor(45, 55, 72, 200),
        "glass_hover": QColor(55, 65, 82, 230),
        "glass_active": QColor(35, 45, 62, 210),
        "glass_disabled": QColor(40, 50, 67, 150),
        
        # 渐变色 - 主色渐变
        "gradient_primary_start": QColor(66, 153, 225),
        "gradient_primary_end": QColor(86, 173, 245),
        
        # 渐变色 - 成功渐变
        "gradient_success_start": QColor(72, 187, 120),
        "gradient_success_end": QColor(92, 207, 140),
        
        # 渐变色 - 警告渐变
        "gradient_warning_start": QColor(255, 213, 79),
        "gradient_warning_end": QColor(255, 233, 99),
        
        # 渐变色 - 错误渐变
        "gradient_error_start": QColor(239, 83, 80),
        "gradient_error_end": QColor(255, 103, 100),
        
        # 边框和阴影
        "border": QColor(63, 63, 70),
        "border_hover": QColor(90, 90, 90),
        "border_focus": QColor(66, 153, 225),
        "shadow": QColor(0, 0, 0, 60),
        "highlight": QColor(255, 255, 255, 30),
    }
    
    @staticmethod
    def check_contrast_ratio(fg: QColor, bg: QColor) -> float:
        """
        检查两个颜色之间的对比度比率（WCAG 2.1 标准）
        
        Args:
            fg: 前景色（通常是文字颜色）
            bg: 背景色
            
        Returns:
            float: 对比度比率（1.0 到 21.0 之间）
        """
        # 计算相对亮度（Relative Luminance）
        def get_relative_luminance(color: QColor) -> float:
            """计算颜色的相对亮度"""
            # 将 RGB 值归一化到 0-1 范围
            r = color.red() / 255.0
            g = color.green() / 255.0
            b = color.blue() / 255.0
            
            # 应用 sRGB 伽马校正
            def adjust_channel(channel: float) -> float:
                if channel <= 0.03928:
                    return channel / 12.92
                else:
                    return ((channel + 0.055) / 1.055) ** 2.4
            
            r = adjust_channel(r)
            g = adjust_channel(g)
            b = adjust_channel(b)
            
            # 计算相对亮度（使用 ITU-R BT.709 系数）
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        # 获取两个颜色的相对亮度
        l1 = get_relative_luminance(fg)
        l2 = get_relative_luminance(bg)
        
        # 确保 l1 是较亮的颜色
        if l1 < l2:
            l1, l2 = l2, l1
        
        # 计算对比度比率
        contrast_ratio = (l1 + 0.05) / (l2 + 0.05)
        
        return contrast_ratio
    
    @staticmethod
    def meets_wcag_aa(fg: QColor, bg: QColor, is_large_text: bool = False) -> bool:
        """
        检查颜色组合是否符合 WCAG 2.1 AA 标准
        
        Args:
            fg: 前景色（文字颜色）
            bg: 背景色
            is_large_text: 是否为大文本（18pt+ 或 14pt+ 粗体）
            
        Returns:
            bool: 是否符合 WCAG AA 标准
        """
        ratio = EnhancedColorPalette.check_contrast_ratio(fg, bg)
        
        # WCAG AA 标准：
        # 普通文本需要至少 4.5:1
        # 大文本需要至少 3:1
        required_ratio = 3.0 if is_large_text else 4.5
        
        return ratio >= required_ratio
    
    @staticmethod
    def meets_wcag_aaa(fg: QColor, bg: QColor, is_large_text: bool = False) -> bool:
        """
        检查颜色组合是否符合 WCAG 2.1 AAA 标准
        
        Args:
            fg: 前景色（文字颜色）
            bg: 背景色
            is_large_text: 是否为大文本（18pt+ 或 14pt+ 粗体）
            
        Returns:
            bool: 是否符合 WCAG AAA 标准
        """
        ratio = EnhancedColorPalette.check_contrast_ratio(fg, bg)
        
        # WCAG AAA 标准：
        # 普通文本需要至少 7:1
        # 大文本需要至少 4.5:1
        required_ratio = 4.5 if is_large_text else 7.0
        
        return ratio >= required_ratio


class ThemeManager(QObject):
    """主题管理器"""
    
    # 主题变更信号
    theme_changed = pyqtSignal(str)  # 发射新主题名称
    
    def __init__(self):
        """初始化主题管理器"""
        super().__init__()
        self._current_mode = ThemeMode.LIGHT
        self._auto_mode_enabled = False
        self._system_theme = ThemeMode.LIGHT
        
        logger.info("主题管理器初始化完成，当前仅支持浅色模式")
    
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
            theme: 主题名称，仅支持 "浅色"
        """
        previous = self._current_mode
        self._auto_mode_enabled = False
        if theme != ThemeMode.LIGHT.value:
            logger.info(f"仅支持浅色主题，收到 '{theme}' 已回退为浅色")
        self._current_mode = ThemeMode.LIGHT
        
        if previous != self._current_mode:
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
        return False
    
    def get_color(self, color_name: str) -> QColor:
        """
        获取指定颜色
        
        Args:
            color_name: 颜色名称
            
        Returns:
            QColor: 颜色对象
        """
        enhanced_colors = EnhancedColorPalette.LIGHT
        if color_name in enhanced_colors:
            return enhanced_colors[color_name]
        
        colors = ThemeColors.LIGHT
        return colors.get(color_name, QColor(0, 0, 0))
    
    def get_all_colors(self) -> Dict[str, QColor]:
        """
        获取当前主题的所有颜色
        
        Returns:
            Dict[str, QColor]: 颜色字典
        """
        enhanced_colors = EnhancedColorPalette.LIGHT
        theme_colors = ThemeColors.LIGHT
        
        all_colors = {}
        all_colors.update(theme_colors)
        all_colors.update(enhanced_colors)
        
        return all_colors
    
    def get_enhanced_colors(self) -> Dict[str, QColor]:
        """
        获取增强的颜色调色板
        
        Returns:
            Dict[str, QColor]: 增强的颜色字典
        """
        return EnhancedColorPalette.LIGHT
    
    def check_color_contrast(self, fg_color_name: str, bg_color_name: str) -> float:
        """
        检查两个颜色之间的对比度
        
        Args:
            fg_color_name: 前景色名称
            bg_color_name: 背景色名称
            
        Returns:
            float: 对比度比率
        """
        fg = self.get_color(fg_color_name)
        bg = self.get_color(bg_color_name)
        return EnhancedColorPalette.check_contrast_ratio(fg, bg)
    
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
        if not self._auto_mode_enabled:
            return
        
        self._auto_mode_enabled = False
        self._current_mode = ThemeMode.LIGHT
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
