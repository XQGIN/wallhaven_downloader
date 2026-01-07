# -*- coding: utf-8 -*-
"""
排版系统
提供统一的字体管理、文字层级和排版规则
"""

import sys
import platform
from typing import Dict, Optional
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QWidget, QLabel

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class TypographyLevel:
    """文字层级常量"""
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BODY = "body"
    SMALL = "small"


class TypographySystem:
    """
    排版系统
    提供统一的字体管理和排版规则
    """
    
    # 字体栈定义（根据操作系统）
    FONT_FAMILY = {
        "windows": ["Segoe UI", "Microsoft YaHei", "sans-serif"],
        "macos": ["SF Pro Display", "PingFang SC", "sans-serif"],
        "linux": ["Ubuntu", "Noto Sans CJK SC", "sans-serif"]
    }
    
    # 文字层级定义
    TEXT_LEVELS = {
        TypographyLevel.HEADING_1: {
            "size": 32,
            "weight": QFont.Bold,  # 700
            "line_height": 1.2
        },
        TypographyLevel.HEADING_2: {
            "size": 24,
            "weight": QFont.DemiBold,  # 600
            "line_height": 1.3
        },
        TypographyLevel.HEADING_3: {
            "size": 20,
            "weight": QFont.DemiBold,  # 600
            "line_height": 1.3
        },
        TypographyLevel.BODY: {
            "size": 14,
            "weight": QFont.Normal,  # 400
            "line_height": 1.5
        },
        TypographyLevel.SMALL: {
            "size": 12,
            "weight": QFont.Normal,  # 400
            "line_height": 1.6
        }
    }
    
    # 文本行宽限制（字符数）
    LINE_WIDTH_MIN = 50
    LINE_WIDTH_MAX = 75
    
    # 平均字符宽度系数（用于估算）
    AVG_CHAR_WIDTH_RATIO = 0.6  # 相对于字体大小
    
    def __init__(self):
        """初始化排版系统"""
        self._system = self._detect_system()
        self._font_family = self._get_font_family()
        self._font_cache: Dict[str, QFont] = {}
        
        logger.info(f"排版系统初始化完成，系统: {self._system}, 字体: {self._font_family[0]}")
    
    def _detect_system(self) -> str:
        """
        检测操作系统
        
        Returns:
            str: 系统类型 ("windows", "macos", "linux")
        """
        system = platform.system().lower()
        
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            logger.warning(f"未知系统类型: {system}，使用 Linux 字体栈")
            return "linux"
    
    def _get_font_family(self) -> list:
        """
        获取当前系统的字体栈
        
        Returns:
            list: 字体列表
        """
        return self.FONT_FAMILY.get(self._system, self.FONT_FAMILY["linux"])
    
    def get_font(self, level: str) -> QFont:
        """
        获取指定层级的字体
        
        Args:
            level: 文字层级 (heading_1, heading_2, heading_3, body, small)
            
        Returns:
            QFont: 字体对象
        """
        # 检查缓存
        if level in self._font_cache:
            return QFont(self._font_cache[level])
        
        # 获取层级配置
        if level not in self.TEXT_LEVELS:
            logger.warning(f"未知的文字层级: {level}，使用 body 层级")
            level = TypographyLevel.BODY
        
        config = self.TEXT_LEVELS[level]
        
        # 创建字体
        font = QFont()
        
        # 设置字体族（尝试列表中的字体）
        for family in self._font_family:
            font.setFamily(family)
            # 检查字体是否可用
            if font.family() == family or font.family().lower() == family.lower():
                break
        
        # 设置字体大小
        font.setPointSize(config["size"])
        
        # 设置字重
        font.setWeight(config["weight"])
        
        # 缓存字体
        self._font_cache[level] = font
        
        return QFont(font)
    
    def apply_typography(self, widget: QWidget, level: str) -> None:
        """
        应用排版样式到组件
        
        Args:
            widget: Qt 组件
            level: 文字层级
        """
        # 获取字体
        font = self.get_font(level)
        widget.setFont(font)
        
        # 如果是 QLabel，设置行高
        if isinstance(widget, QLabel):
            config = self.TEXT_LEVELS.get(level, self.TEXT_LEVELS[TypographyLevel.BODY])
            line_height = config["line_height"]
            
            # 计算行高（像素）
            font_metrics = QFontMetrics(font)
            line_spacing = int(font_metrics.height() * line_height)
            
            # 设置样式表以控制行高
            current_style = widget.styleSheet()
            line_height_style = f"line-height: {line_spacing}px;"
            
            if current_style:
                widget.setStyleSheet(f"{current_style} {line_height_style}")
            else:
                widget.setStyleSheet(line_height_style)
            
            # 启用自动换行
            widget.setWordWrap(True)
    
    def get_line_height(self, level: str) -> float:
        """
        获取指定层级的行高比率
        
        Args:
            level: 文字层级
            
        Returns:
            float: 行高比率
        """
        config = self.TEXT_LEVELS.get(level, self.TEXT_LEVELS[TypographyLevel.BODY])
        return config["line_height"]
    
    def calculate_max_width(self, level: str, char_count: int = LINE_WIDTH_MAX) -> int:
        """
        计算指定字符数的最大宽度（像素）
        
        Args:
            level: 文字层级
            char_count: 字符数（默认 75）
            
        Returns:
            int: 最大宽度（像素）
        """
        font = self.get_font(level)
        font_metrics = QFontMetrics(font)
        
        # 使用平均字符宽度估算
        avg_char_width = font_metrics.averageCharWidth()
        max_width = int(avg_char_width * char_count)
        
        return max_width
    
    def truncate_text(self, text: str, widget: QWidget, max_width: Optional[int] = None) -> str:
        """
        截断文本并添加省略号
        
        Args:
            text: 原始文本
            widget: Qt 组件（用于获取字体）
            max_width: 最大宽度（像素），如果为 None 则使用组件宽度
            
        Returns:
            str: 截断后的文本
        """
        if not text:
            return text
        
        # 获取字体度量
        font = widget.font()
        font_metrics = QFontMetrics(font)
        
        # 确定最大宽度
        if max_width is None:
            max_width = widget.width()
        
        # 如果文本宽度小于最大宽度，直接返回
        text_width = font_metrics.horizontalAdvance(text)
        if text_width <= max_width:
            return text
        
        # 截断文本并添加省略号
        elided_text = font_metrics.elidedText(text, Qt.ElideRight, max_width)
        
        return elided_text
    
    def set_text_with_truncation(self, label: QLabel, text: str, max_width: Optional[int] = None) -> None:
        """
        设置 QLabel 文本并自动截断
        
        Args:
            label: QLabel 组件
            text: 文本内容
            max_width: 最大宽度（像素），如果为 None 则使用标签宽度
        """
        # 保存原始文本作为工具提示
        label.setToolTip(text)
        
        # 截断文本
        truncated_text = self.truncate_text(text, label, max_width)
        
        # 设置文本
        label.setText(truncated_text)
    
    def apply_line_width_limit(self, widget: QWidget, level: str, char_count: Optional[int] = None) -> None:
        """
        应用文本行宽限制
        
        Args:
            widget: Qt 组件
            level: 文字层级
            char_count: 字符数限制（默认使用 LINE_WIDTH_MAX）
        """
        if char_count is None:
            char_count = self.LINE_WIDTH_MAX
        
        # 计算最大宽度
        max_width = self.calculate_max_width(level, char_count)
        
        # 设置最大宽度
        widget.setMaximumWidth(max_width)
    
    def get_font_info(self, level: str) -> Dict:
        """
        获取指定层级的字体信息
        
        Args:
            level: 文字层级
            
        Returns:
            Dict: 字体信息字典
        """
        config = self.TEXT_LEVELS.get(level, self.TEXT_LEVELS[TypographyLevel.BODY])
        font = self.get_font(level)
        
        return {
            "level": level,
            "family": font.family(),
            "size": config["size"],
            "weight": config["weight"],
            "line_height": config["line_height"],
            "font": font
        }
    
    def clear_cache(self) -> None:
        """清除字体缓存"""
        self._font_cache.clear()
        logger.debug("字体缓存已清除")


# 全局排版系统实例
_typography_system_instance: Optional[TypographySystem] = None


def get_typography_system() -> TypographySystem:
    """
    获取全局排版系统实例（单例模式）
    
    Returns:
        TypographySystem: 排版系统实例
    """
    global _typography_system_instance
    if _typography_system_instance is None:
        _typography_system_instance = TypographySystem()
    return _typography_system_instance
