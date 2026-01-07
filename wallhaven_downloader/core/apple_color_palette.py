# -*- coding: utf-8 -*-
"""
苹果颜色调色板
提供符合苹果设计规范的颜色方案，支持日间和夜间主题
"""

from typing import Dict
from PyQt5.QtGui import QColor

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class AppleColorPalette:
    """
    苹果风格颜色调色板
    
    提供符合苹果设计规范的颜色方案，包括：
    - 完整的日间主题颜色（Light Mode）
    - 完整的夜间主题颜色（Dark Mode）
    - 语义化的颜色命名
    - 玻璃效果颜色
    - 渐变色支持
    
    颜色值参考：
    - Apple Human Interface Guidelines
    - iOS/macOS 系统颜色
    - SF Symbols 颜色规范
    """
    
    # 日间主题颜色 (Light Mode)
    LIGHT = {
        # 背景色系 - 苹果浅色主题
        "background": QColor(245, 245, 247),  # #F5F5F7 - 主背景色
        "surface": QColor(255, 255, 255),  # #FFFFFF - 表面色（卡片、面板）
        "surface_secondary": QColor(250, 250, 250),  # #FAFAFA - 次要表面色
        
        # 文本色系
        "text_primary": QColor(29, 29, 31),  # #1D1D1F - 主要文本
        "text_secondary": QColor(134, 134, 139),  # #86868B - 次要文本
        "text_tertiary": QColor(174, 174, 178),  # #AEAEB2 - 三级文本
        
        # 玻璃效果 - 半透明层
        "glass_normal": QColor(255, 255, 255, 200),  # rgba(255,255,255,0.78) - 正常状态
        "glass_hover": QColor(255, 255, 255, 230),  # rgba(255,255,255,0.90) - 悬停状态
        "glass_active": QColor(250, 250, 250, 210),  # rgba(250,250,250,0.82) - 激活状态
        
        # 强调色 - 苹果蓝 (Apple Blue)
        "accent": QColor(0, 122, 255),  # #007AFF - 主强调色
        "accent_hover": QColor(0, 102, 235),  # #0066EB - 悬停状态
        "accent_active": QColor(0, 82, 215),  # #0052D7 - 激活状态
        
        # 语义色 - 成功 (Success)
        "success": QColor(52, 199, 89),  # #34C759 - 成功/完成
        "success_hover": QColor(42, 179, 79),  # 悬停状态
        "success_active": QColor(32, 159, 69),  # 激活状态
        
        # 语义色 - 警告 (Warning)
        "warning": QColor(255, 204, 0),  # #FFCC00 - 警告/注意
        "warning_hover": QColor(235, 184, 0),  # 悬停状态
        "warning_active": QColor(215, 164, 0),  # 激活状态
        
        # 语义色 - 错误 (Error)
        "error": QColor(255, 59, 48),  # #FF3B30 - 错误/危险
        "error_hover": QColor(235, 39, 28),  # 悬停状态
        "error_active": QColor(215, 19, 8),  # 激活状态
        
        # 语义色 - 信息 (Info)
        "info": QColor(90, 200, 250),  # #5AC8FA - 信息提示
        "info_hover": QColor(70, 180, 230),  # 悬停状态
        "info_active": QColor(50, 160, 210),  # 激活状态
        
        # 边框和分隔线
        "border": QColor(216, 216, 220),  # #D8D8DC - 边框色
        "separator": QColor(229, 229, 234),  # #E5E5EA - 分隔线
        
        # 阴影
        "shadow": QColor(0, 0, 0, 30),  # rgba(0,0,0,0.12) - 普通阴影
        "shadow_elevated": QColor(0, 0, 0, 50),  # rgba(0,0,0,0.20) - 提升阴影
        
        # 高光
        "highlight": QColor(255, 255, 255, 100),  # rgba(255,255,255,0.39) - 边缘高光
    }
    
    # 夜间主题颜色 (Dark Mode)
    DARK = {
        # 背景色系 - 苹果深色主题
        "background": QColor(28, 28, 30),  # #1C1C1E - 主背景色
        "surface": QColor(44, 44, 46),  # #2C2C2E - 表面色（卡片、面板）
        "surface_secondary": QColor(58, 58, 60),  # #3A3A3C - 次要表面色
        
        # 文本色系
        "text_primary": QColor(245, 245, 247),  # #F5F5F7 - 主要文本
        "text_secondary": QColor(152, 152, 157),  # #98989D - 次要文本
        "text_tertiary": QColor(99, 99, 102),  # #636366 - 三级文本
        
        # 玻璃效果 - 半透明层
        "glass_normal": QColor(44, 44, 46, 200),  # rgba(44,44,46,0.78) - 正常状态
        "glass_hover": QColor(58, 58, 60, 230),  # rgba(58,58,60,0.90) - 悬停状态
        "glass_active": QColor(38, 38, 40, 210),  # rgba(38,38,40,0.82) - 激活状态
        
        # 强调色 - 苹果蓝 (深色模式)
        "accent": QColor(10, 132, 255),  # #0A84FF - 主强调色
        "accent_hover": QColor(30, 152, 255),  # #1E98FF - 悬停状态
        "accent_active": QColor(0, 112, 235),  # #0070EB - 激活状态
        
        # 语义色 - 成功 (深色模式)
        "success": QColor(48, 209, 88),  # #30D158 - 成功/完成
        "success_hover": QColor(68, 229, 108),  # 悬停状态
        "success_active": QColor(28, 189, 68),  # 激活状态
        
        # 语义色 - 警告 (深色模式)
        "warning": QColor(255, 214, 10),  # #FFD60A - 警告/注意
        "warning_hover": QColor(255, 234, 30),  # 悬停状态
        "warning_active": QColor(235, 194, 0),  # 激活状态
        
        # 语义色 - 错误 (深色模式)
        "error": QColor(255, 69, 58),  # #FF453A - 错误/危险
        "error_hover": QColor(255, 89, 78),  # 悬停状态
        "error_active": QColor(235, 49, 38),  # 激活状态
        
        # 语义色 - 信息 (深色模式)
        "info": QColor(100, 210, 255),  # #64D2FF - 信息提示
        "info_hover": QColor(120, 230, 255),  # 悬停状态
        "info_active": QColor(80, 190, 235),  # 激活状态
        
        # 边框和分隔线
        "border": QColor(56, 56, 58),  # #38383A - 边框色
        "separator": QColor(72, 72, 74),  # #48484A - 分隔线
        
        # 阴影
        "shadow": QColor(0, 0, 0, 60),  # rgba(0,0,0,0.24) - 普通阴影
        "shadow_elevated": QColor(0, 0, 0, 80),  # rgba(0,0,0,0.32) - 提升阴影
        
        # 高光
        "highlight": QColor(255, 255, 255, 30),  # rgba(255,255,255,0.12) - 边缘高光
    }
    
    def __init__(self):
        """初始化苹果颜色调色板"""
        logger.debug("苹果颜色调色板初始化完成")
    
    def get_color(self, color_name: str, is_dark_mode: bool = False) -> QColor:
        """
        获取指定颜色
        
        Args:
            color_name: 颜色名称（如 "background", "text_primary", "accent" 等）
            is_dark_mode: 是否为深色模式，默认为 False（浅色模式）
            
        Returns:
            QColor: 颜色对象，如果颜色名称不存在则返回黑色
            
        Example:
            >>> palette = AppleColorPalette()
            >>> bg_color = palette.get_color("background", is_dark_mode=False)
            >>> accent_color = palette.get_color("accent", is_dark_mode=True)
        """
        palette = self.DARK if is_dark_mode else self.LIGHT
        color = palette.get(color_name)
        
        if color is None:
            logger.warning(f"颜色名称 '{color_name}' 不存在，返回默认黑色")
            return QColor(0, 0, 0)
        
        return color
    
    def get_all_colors(self, is_dark_mode: bool = False) -> Dict[str, QColor]:
        """
        获取所有颜色
        
        Args:
            is_dark_mode: 是否为深色模式，默认为 False（浅色模式）
            
        Returns:
            Dict[str, QColor]: 包含所有颜色的字典
            
        Example:
            >>> palette = AppleColorPalette()
            >>> light_colors = palette.get_all_colors(is_dark_mode=False)
            >>> dark_colors = palette.get_all_colors(is_dark_mode=True)
        """
        return self.DARK.copy() if is_dark_mode else self.LIGHT.copy()
    
    def get_color_hex(self, color_name: str, is_dark_mode: bool = False) -> str:
        """
        获取指定颜色的十六进制表示
        
        Args:
            color_name: 颜色名称
            is_dark_mode: 是否为深色模式
            
        Returns:
            str: 颜色的十六进制字符串（如 "#F5F5F7"）
            
        Example:
            >>> palette = AppleColorPalette()
            >>> hex_color = palette.get_color_hex("accent")
            >>> print(hex_color)  # "#007AFF"
        """
        color = self.get_color(color_name, is_dark_mode)
        return color.name()
    
    def get_color_rgba(self, color_name: str, is_dark_mode: bool = False) -> str:
        """
        获取指定颜色的 RGBA 表示
        
        Args:
            color_name: 颜色名称
            is_dark_mode: 是否为深色模式
            
        Returns:
            str: 颜色的 RGBA 字符串（如 "rgba(255,255,255,200)"）
            
        Example:
            >>> palette = AppleColorPalette()
            >>> rgba_color = palette.get_color_rgba("glass_normal")
            >>> print(rgba_color)  # "rgba(255,255,255,200)"
        """
        color = self.get_color(color_name, is_dark_mode)
        return f"rgba({color.red()},{color.green()},{color.blue()},{color.alpha()})"
    
    @staticmethod
    def check_contrast_ratio(fg: QColor, bg: QColor) -> float:
        """
        检查两个颜色之间的对比度比率（WCAG 2.1 标准）
        
        Args:
            fg: 前景色（通常是文字颜色）
            bg: 背景色
            
        Returns:
            float: 对比度比率（1.0 到 21.0 之间）
            
        Example:
            >>> fg = QColor(29, 29, 31)  # 深色文本
            >>> bg = QColor(245, 245, 247)  # 浅色背景
            >>> ratio = AppleColorPalette.check_contrast_ratio(fg, bg)
            >>> print(f"对比度: {ratio:.2f}:1")
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
            is_large_text: 是否为大文本（18pt+ 或 14pt+ 粗体），默认为 False
            
        Returns:
            bool: 是否符合 WCAG AA 标准
            
        Note:
            WCAG AA 标准要求：
            - 普通文本：对比度至少 4.5:1
            - 大文本：对比度至少 3:1
            
        Example:
            >>> fg = QColor(29, 29, 31)
            >>> bg = QColor(245, 245, 247)
            >>> is_compliant = AppleColorPalette.meets_wcag_aa(fg, bg)
            >>> print(f"符合 WCAG AA: {is_compliant}")
        """
        ratio = AppleColorPalette.check_contrast_ratio(fg, bg)
        
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
            is_large_text: 是否为大文本（18pt+ 或 14pt+ 粗体），默认为 False
            
        Returns:
            bool: 是否符合 WCAG AAA 标准
            
        Note:
            WCAG AAA 标准要求：
            - 普通文本：对比度至少 7:1
            - 大文本：对比度至少 4.5:1
            
        Example:
            >>> fg = QColor(29, 29, 31)
            >>> bg = QColor(245, 245, 247)
            >>> is_compliant = AppleColorPalette.meets_wcag_aaa(fg, bg)
            >>> print(f"符合 WCAG AAA: {is_compliant}")
        """
        ratio = AppleColorPalette.check_contrast_ratio(fg, bg)
        
        # WCAG AAA 标准：
        # 普通文本需要至少 7:1
        # 大文本需要至少 4.5:1
        required_ratio = 4.5 if is_large_text else 7.0
        
        return ratio >= required_ratio
    
    def validate_color_scheme(self, is_dark_mode: bool = False) -> Dict[str, bool]:
        """
        验证颜色方案的可访问性
        
        检查主要文本和背景颜色组合是否符合 WCAG AA 标准
        
        Args:
            is_dark_mode: 是否为深色模式
            
        Returns:
            Dict[str, bool]: 验证结果字典，键为颜色组合名称，值为是否符合标准
            
        Example:
            >>> palette = AppleColorPalette()
            >>> results = palette.validate_color_scheme(is_dark_mode=False)
            >>> for combo, is_valid in results.items():
            ...     print(f"{combo}: {'✓' if is_valid else '✗'}")
        """
        results = {}
        
        # 获取颜色
        text_primary = self.get_color("text_primary", is_dark_mode)
        text_secondary = self.get_color("text_secondary", is_dark_mode)
        background = self.get_color("background", is_dark_mode)
        surface = self.get_color("surface", is_dark_mode)
        
        # 检查主要文本和背景的对比度
        results["text_primary_on_background"] = self.meets_wcag_aa(text_primary, background)
        results["text_primary_on_surface"] = self.meets_wcag_aa(text_primary, surface)
        results["text_secondary_on_background"] = self.meets_wcag_aa(text_secondary, background)
        results["text_secondary_on_surface"] = self.meets_wcag_aa(text_secondary, surface)
        
        # 记录验证结果
        mode_name = "深色" if is_dark_mode else "浅色"
        logger.info(f"{mode_name}模式颜色方案验证结果:")
        for combo, is_valid in results.items():
            status = "✓ 通过" if is_valid else "✗ 未通过"
            logger.info(f"  {combo}: {status}")
        
        return results


# 全局实例（可选）
_apple_palette_instance = None


def get_apple_palette() -> AppleColorPalette:
    """
    获取全局苹果颜色调色板实例（单例模式）
    
    Returns:
        AppleColorPalette: 苹果颜色调色板实例
        
    Example:
        >>> palette = get_apple_palette()
        >>> accent_color = palette.get_color("accent")
    """
    global _apple_palette_instance
    if _apple_palette_instance is None:
        _apple_palette_instance = AppleColorPalette()
    return _apple_palette_instance
