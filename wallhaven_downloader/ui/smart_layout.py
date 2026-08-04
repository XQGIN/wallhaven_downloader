# -*- coding: utf-8 -*-
"""
智能布局系统
提供响应式布局和自适应间距
"""

from typing import List, Optional, Tuple
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtWidgets import (
    QWidget, QLayout, QLayoutItem, QSizePolicy, 
    QVBoxLayout, QHBoxLayout, QGridLayout
)

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class ResponsiveGridLayout(QLayout):
    """
    响应式网格布局
    根据容器宽度自动调整列数和间距
    """
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        
        # 布局项目列表
        self.items: List[QLayoutItem] = []
        
        # 响应式参数
        self.min_item_width = 200  # 最小项目宽度
        self.max_item_width = 400  # 最大项目宽度
        self.preferred_columns = 3  # 首选列数
        self.min_columns = 1  # 最小列数
        self.max_columns = 6  # 最大列数
        
        # 间距参数
        self.base_spacing = 16  # 基础间距
        self.adaptive_spacing = True  # 自适应间距
        
        logger.debug("ResponsiveGridLayout 初始化完成")
    
    def addItem(self, item: QLayoutItem):
        """添加布局项"""
        self.items.append(item)
        self.invalidate()
    
    def count(self) -> int:
        """返回项目数量"""
        return len(self.items)
    
    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        """获取指定索引的项目"""
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        """移除并返回指定索引的项目"""
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def sizeHint(self) -> QSize:
        """返回建议大小"""
        if not self.items:
            return QSize(0, 0)
        
        # 计算最优布局
        container_width = self.geometry().width() or 800  # 默认宽度
        columns, item_width, spacing = self._calculate_layout(container_width)
        
        # 计算行数
        rows = (len(self.items) + columns - 1) // columns
        
        # 计算总高度（假设所有项目高度相同）
        item_height = 200  # 默认项目高度
        if self.items and self.items[0].widget():
            item_height = self.items[0].sizeHint().height()
        
        total_height = rows * item_height + (rows - 1) * spacing
        total_width = columns * item_width + (columns - 1) * spacing
        
        return QSize(total_width, total_height)
    
    def minimumSize(self) -> QSize:
        """返回最小大小"""
        if not self.items:
            return QSize(0, 0)
        
        # 单列布局的最小大小
        min_width = self.min_item_width
        min_height = len(self.items) * 100  # 假设最小项目高度为100
        
        return QSize(min_width, min_height)
    
    def setGeometry(self, rect: QRect):
        """设置几何形状并布局项目"""
        super().setGeometry(rect)
        self._layout_items(rect)
    
    def _calculate_layout(self, container_width: int) -> Tuple[int, int, int]:
        """
        计算最优布局参数
        
        Returns:
            Tuple[columns, item_width, spacing]: 列数、项目宽度、间距
        """
        # 计算可能的列数
        possible_columns = []
        
        for cols in range(self.min_columns, self.max_columns + 1):
            # 计算间距总宽度
            spacing_width = (cols - 1) * self.base_spacing
            available_width = container_width - spacing_width
            
            # 计算每个项目的宽度
            item_width = available_width // cols
            
            # 检查是否在合理范围内
            if self.min_item_width <= item_width <= self.max_item_width:
                possible_columns.append((cols, item_width))
        
        # 如果没有合适的列数，使用最接近的
        if not possible_columns:
            if container_width < self.min_item_width:
                # 容器太小，使用单列
                cols = 1
                item_width = container_width
            else:
                # 容器太大，使用最大列数
                cols = self.max_columns
                spacing_width = (cols - 1) * self.base_spacing
                item_width = (container_width - spacing_width) // cols
        else:
            # 选择最接近首选列数的选项
            cols, item_width = min(
                possible_columns,
                key=lambda x: abs(x[0] - self.preferred_columns)
            )
        
        # 计算自适应间距
        if self.adaptive_spacing and cols > 1:
            # 根据剩余空间调整间距
            used_width = cols * item_width
            remaining_width = container_width - used_width
            spacing = remaining_width // (cols - 1)
            spacing = max(self.base_spacing // 2, min(spacing, self.base_spacing * 2))
        else:
            spacing = self.base_spacing
        
        return cols, item_width, spacing
    
    def _layout_items(self, rect: QRect):
        """布局所有项目"""
        if not self.items:
            return
        
        # 计算布局参数
        columns, item_width, spacing = self._calculate_layout(rect.width())
        
        # 计算项目高度（使用第一个项目的建议高度）
        item_height = 200  # 默认高度
        if self.items[0].widget():
            item_height = self.items[0].sizeHint().height()
        
        # 布局项目
        x_start = rect.x()
        y_start = rect.y()
        
        for i, item in enumerate(self.items):
            if not item.widget():
                continue
            
            # 计算行列位置
            row = i // columns
            col = i % columns
            
            # 计算项目位置
            x = x_start + col * (item_width + spacing)
            y = y_start + row * (item_height + spacing)
            
            # 设置项目几何形状
            item_rect = QRect(x, y, item_width, item_height)
            item.setGeometry(item_rect)
    
    def set_responsive_params(
        self,
        min_item_width: int = None,
        max_item_width: int = None,
        preferred_columns: int = None,
        min_columns: int = None,
        max_columns: int = None
    ):
        """设置响应式参数"""
        if min_item_width is not None:
            self.min_item_width = min_item_width
        if max_item_width is not None:
            self.max_item_width = max_item_width
        if preferred_columns is not None:
            self.preferred_columns = preferred_columns
        if min_columns is not None:
            self.min_columns = min_columns
        if max_columns is not None:
            self.max_columns = max_columns
        
        self.invalidate()
        
        logger.debug(f"响应式参数已更新: 项目宽度={self.min_item_width}-{self.max_item_width}, "
                    f"列数={self.min_columns}-{self.max_columns}(首选{self.preferred_columns})")


class FlexLayout(QLayout):
    """
    弹性布局
    类似CSS Flexbox的布局系统
    """
    
    # 对齐方式
    ALIGN_START = 0
    ALIGN_CENTER = 1
    ALIGN_END = 2
    ALIGN_STRETCH = 3
    ALIGN_SPACE_BETWEEN = 4
    ALIGN_SPACE_AROUND = 5
    
    def __init__(self, direction: Qt.Orientation = Qt.Horizontal, parent: QWidget = None):
        super().__init__(parent)
        
        self.items: List[QLayoutItem] = []
        self.direction = direction
        
        # 弹性参数
        self.main_axis_alignment = self.ALIGN_START  # 主轴对齐
        self.cross_axis_alignment = self.ALIGN_STRETCH  # 交叉轴对齐
        self.wrap = False  # 是否换行
        
        # 间距
        self.spacing_value = 8
        
        logger.debug(f"FlexLayout 初始化完成: 方向={'水平' if direction == Qt.Horizontal else '垂直'}")
    
    def addItem(self, item: QLayoutItem):
        """添加布局项"""
        self.items.append(item)
        self.invalidate()
    
    def count(self) -> int:
        return len(self.items)
    
    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def sizeHint(self) -> QSize:
        """返回建议大小"""
        if not self.items:
            return QSize(0, 0)
        
        if self.direction == Qt.Horizontal:
            # 水平布局：宽度累加，高度取最大
            total_width = sum(item.sizeHint().width() for item in self.items)
            total_width += (len(self.items) - 1) * self.spacing_value
            max_height = max(item.sizeHint().height() for item in self.items)
            return QSize(total_width, max_height)
        else:
            # 垂直布局：高度累加，宽度取最大
            max_width = max(item.sizeHint().width() for item in self.items)
            total_height = sum(item.sizeHint().height() for item in self.items)
            total_height += (len(self.items) - 1) * self.spacing_value
            return QSize(max_width, total_height)
    
    def minimumSize(self) -> QSize:
        """返回最小大小"""
        if not self.items:
            return QSize(0, 0)
        
        if self.direction == Qt.Horizontal:
            total_width = sum(item.minimumSize().width() for item in self.items)
            total_width += (len(self.items) - 1) * self.spacing_value
            max_height = max(item.minimumSize().height() for item in self.items)
            return QSize(total_width, max_height)
        else:
            max_width = max(item.minimumSize().width() for item in self.items)
            total_height = sum(item.minimumSize().height() for item in self.items)
            total_height += (len(self.items) - 1) * self.spacing_value
            return QSize(max_width, total_height)
    
    def setGeometry(self, rect: QRect):
        """设置几何形状并布局项目"""
        super().setGeometry(rect)
        self._layout_items(rect)
    
    def _layout_items(self, rect: QRect):
        """布局所有项目"""
        if not self.items:
            return
        
        if self.direction == Qt.Horizontal:
            self._layout_horizontal(rect)
        else:
            self._layout_vertical(rect)
    
    def _layout_horizontal(self, rect: QRect):
        """水平布局"""
        # 计算总的首选宽度
        total_preferred_width = sum(item.sizeHint().width() for item in self.items)
        total_spacing = (len(self.items) - 1) * self.spacing_value
        available_width = rect.width() - total_spacing
        
        # 计算每个项目的实际宽度
        item_widths = []
        if total_preferred_width <= available_width:
            # 有剩余空间，根据对齐方式分配
            if self.main_axis_alignment == self.ALIGN_SPACE_BETWEEN:
                # 项目间均匀分布
                extra_spacing = (available_width - total_preferred_width) // (len(self.items) - 1) if len(self.items) > 1 else 0
                self.spacing_value += extra_spacing
                item_widths = [item.sizeHint().width() for item in self.items]
            elif self.main_axis_alignment == self.ALIGN_SPACE_AROUND:
                # 项目周围均匀分布
                extra_space = available_width - total_preferred_width
                extra_per_item = extra_space // len(self.items)
                item_widths = [item.sizeHint().width() + extra_per_item for item in self.items]
            else:
                item_widths = [item.sizeHint().width() for item in self.items]
        else:
            # 空间不足，按比例缩放
            scale_factor = available_width / total_preferred_width
            item_widths = [int(item.sizeHint().width() * scale_factor) for item in self.items]
        
        # 计算起始位置
        if self.main_axis_alignment == self.ALIGN_CENTER:
            used_width = sum(item_widths) + total_spacing
            start_x = rect.x() + (rect.width() - used_width) // 2
        elif self.main_axis_alignment == self.ALIGN_END:
            used_width = sum(item_widths) + total_spacing
            start_x = rect.x() + rect.width() - used_width
        else:
            start_x = rect.x()
        
        # 布局项目
        current_x = start_x
        for i, (item, width) in enumerate(zip(self.items, item_widths)):
            if not item.widget():
                continue
            
            # 计算高度和Y位置
            if self.cross_axis_alignment == self.ALIGN_STRETCH:
                height = rect.height()
                y = rect.y()
            elif self.cross_axis_alignment == self.ALIGN_CENTER:
                height = item.sizeHint().height()
                y = rect.y() + (rect.height() - height) // 2
            elif self.cross_axis_alignment == self.ALIGN_END:
                height = item.sizeHint().height()
                y = rect.y() + rect.height() - height
            else:  # ALIGN_START
                height = item.sizeHint().height()
                y = rect.y()
            
            # 设置项目几何形状
            item.setGeometry(QRect(current_x, y, width, height))
            current_x += width + self.spacing_value
    
    def _layout_vertical(self, rect: QRect):
        """垂直布局（类似水平布局的逻辑，但交换宽高）"""
        # 计算总的首选高度
        total_preferred_height = sum(item.sizeHint().height() for item in self.items)
        total_spacing = (len(self.items) - 1) * self.spacing_value
        available_height = rect.height() - total_spacing
        
        # 计算每个项目的实际高度
        item_heights = []
        if total_preferred_height <= available_height:
            if self.main_axis_alignment == self.ALIGN_SPACE_BETWEEN:
                extra_spacing = (available_height - total_preferred_height) // (len(self.items) - 1) if len(self.items) > 1 else 0
                self.spacing_value += extra_spacing
                item_heights = [item.sizeHint().height() for item in self.items]
            elif self.main_axis_alignment == self.ALIGN_SPACE_AROUND:
                extra_space = available_height - total_preferred_height
                extra_per_item = extra_space // len(self.items)
                item_heights = [item.sizeHint().height() + extra_per_item for item in self.items]
            else:
                item_heights = [item.sizeHint().height() for item in self.items]
        else:
            scale_factor = available_height / total_preferred_height
            item_heights = [int(item.sizeHint().height() * scale_factor) for item in self.items]
        
        # 计算起始位置
        if self.main_axis_alignment == self.ALIGN_CENTER:
            used_height = sum(item_heights) + total_spacing
            start_y = rect.y() + (rect.height() - used_height) // 2
        elif self.main_axis_alignment == self.ALIGN_END:
            used_height = sum(item_heights) + total_spacing
            start_y = rect.y() + rect.height() - used_height
        else:
            start_y = rect.y()
        
        # 布局项目
        current_y = start_y
        for i, (item, height) in enumerate(zip(self.items, item_heights)):
            if not item.widget():
                continue
            
            # 计算宽度和X位置
            if self.cross_axis_alignment == self.ALIGN_STRETCH:
                width = rect.width()
                x = rect.x()
            elif self.cross_axis_alignment == self.ALIGN_CENTER:
                width = item.sizeHint().width()
                x = rect.x() + (rect.width() - width) // 2
            elif self.cross_axis_alignment == self.ALIGN_END:
                width = item.sizeHint().width()
                x = rect.x() + rect.width() - width
            else:  # ALIGN_START
                width = item.sizeHint().width()
                x = rect.x()
            
            # 设置项目几何形状
            item.setGeometry(QRect(x, current_y, width, height))
            current_y += height + self.spacing_value