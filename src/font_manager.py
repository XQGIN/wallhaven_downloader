# -*- coding: utf-8 -*-
"""
字体管理器模块
用于加载和管理应用程序中使用的字体
"""

import os
import sys
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtCore import QObject


class FontManager(QObject):
    """字体管理器类"""
    
    def __init__(self):
        super().__init__()
        self._loaded_fonts = {}
        self._font_dir = self._get_font_directory()
    
    def _get_font_directory(self):
        """获取字体目录路径"""
        try:
            # PyInstaller打包后的路径
            base_path = sys._MEIPASS
        except Exception:
            # 开发环境路径
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        return os.path.join(base_path, 'font')
    
    def load_font(self, font_filename):
        """
        加载指定的字体文件
        
        Args:
            font_filename: 字体文件名
            
        Returns:
            str: 字体家族名称，如果加载失败返回None
        """
        if font_filename in self._loaded_fonts:
            return self._loaded_fonts[font_filename]
        
        font_path = os.path.join(self._font_dir, font_filename)
        
        if not os.path.exists(font_path):
            print(f"字体文件不存在: {font_path}")
            return None
        
        font_id = QFontDatabase.addApplicationFont(font_path)
        
        if font_id == -1:
            print(f"加载字体失败: {font_path}")
            return None
        
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        
        if not font_families:
            print(f"无法获取字体家族: {font_path}")
            return None
        
        font_family = font_families[0]
        self._loaded_fonts[font_filename] = font_family
        
        return font_family
    
    def get_font(self, font_filename, size=12, bold=False, italic=False):
        """
        获取指定的字体对象
        
        Args:
            font_filename: 字体文件名
            size: 字体大小
            bold: 是否加粗
            italic: 是否斜体
            
        Returns:
            QFont: 字体对象
        """
        font_family = self.load_font(font_filename)
        
        if font_family is None:
            # 如果加载失败，返回默认字体
            return QFont("Arial", size)
        
        font = QFont(font_family, size)
        
        if bold:
            font.setBold(True)
        
        if italic:
            font.setItalic(True)
        
        return font
    
    @staticmethod
    def get_default_font(size=12, bold=False):
        """
        获取默认字体
        
        Args:
            size: 字体大小
            bold: 是否加粗
            
        Returns:
            QFont: 字体对象
        """
        font = QFont("Microsoft YaHei", size)
        
        if bold:
            font.setBold(True)
        
        return font
