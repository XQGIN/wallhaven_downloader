# -*- coding: utf-8 -*-
"""
自定义箭头图标组件

提供美观的SVG箭头图标用于下拉框和数字输入框
"""

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainterPath
from PyQt5.QtSvg import QSvgRenderer
from io import BytesIO


class CustomArrows:
    """自定义箭头图标生成器"""
    
    @staticmethod
    def get_down_arrow_svg(color: str = "#646464", size: int = 16) -> str:
        """获取向下箭头的SVG代码
        
        Args:
            color: 箭头颜色
            size: 图标大小
            
        Returns:
            SVG代码字符串
        """
        return f'''
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M7 10L12 15L17 10" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        '''
    
    @staticmethod
    def get_up_arrow_svg(color: str = "#646464", size: int = 16) -> str:
        """获取向上箭头的SVG代码
        
        Args:
            color: 箭头颜色
            size: 图标大小
            
        Returns:
            SVG代码字符串
        """
        return f'''
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 14L12 9L7 14" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        '''
    
    @staticmethod
    def svg_to_pixmap(svg_code: str, size: QSize = QSize(16, 16)) -> QPixmap:
        """将SVG代码转换为QPixmap
        
        Args:
            svg_code: SVG代码字符串
            size: 目标大小
            
        Returns:
            QPixmap对象
        """
        # 创建SVG渲染器
        svg_bytes = svg_code.encode('utf-8')
        renderer = QSvgRenderer(svg_bytes)
        
        # 创建透明背景的Pixmap
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        # 渲染SVG到Pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        return pixmap
    
    @staticmethod
    def create_arrow_icon(direction: str = "down", color: str = "#646464", size: int = 16) -> QPixmap:
        """创建箭头图标
        
        Args:
            direction: 箭头方向 ("up" 或 "down")
            color: 箭头颜色
            size: 图标大小
            
        Returns:
            QPixmap对象
        """
        if direction == "up":
            svg_code = CustomArrows.get_up_arrow_svg(color, size)
        else:
            svg_code = CustomArrows.get_down_arrow_svg(color, size)
        
        return CustomArrows.svg_to_pixmap(svg_code, QSize(size, size))
