# -*- coding: utf-8 -*-
"""
增强的输入框组件
提供浮动标签、清除按钮、底部边框动画和验证反馈功能
"""

from typing import Optional, Callable, List
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, QTimer, pyqtProperty
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QListWidget, QListWidgetItem, QCompleter
)
from PyQt5.QtGui import QPainter, QColor, QPen, QIcon

try:
    from core.theme_manager import get_theme_manager
    from ui.animation_manager import get_animation_manager
    from utils.logger import get_logger
except ImportError:
    from ..core.theme_manager import get_theme_manager
    from .animation_manager import get_animation_manager
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedInputField(QWidget):
    """
    增强的输入框组件
    
    特性：
    - 浮动标签效果（聚焦时标签上移）
    - 清除按钮（有内容时显示）
    - 底部边框动画（从中心向两侧扩展）
    - 验证视觉反馈（成功/错误状态）
    """
    
    # 信号
    textChanged = pyqtSignal(str)  # 文本改变信号
    returnPressed = pyqtSignal()   # 回车按下信号
    validationChanged = pyqtSignal(bool)  # 验证状态改变信号
    
    def __init__(
        self,
        label: str,
        placeholder: str = "",
        parent: Optional[QWidget] = None
    ):
        """
        初始化增强输入框
        
        Args:
            label: 标签文本
            placeholder: 占位符文本
            parent: 父组件
        """
        super().__init__(parent)
        
        self.label_text = label
        self.placeholder_text = placeholder
        
        # 获取管理器
        self.theme_manager = get_theme_manager()
        self.animation_manager = get_animation_manager()
        
        # 验证状态
        self._validation_state = None  # None, 'success', 'error'
        self._validation_message = ""
        
        # 底部边框动画进度
        self._border_progress = 0.0
        
        # 初始化 UI
        self._setup_ui()
        self._setup_animations()
        self._apply_theme()
        
        # 连接主题变更信号
        self.theme_manager.theme_changed.connect(self._apply_theme)
        
        logger.debug(f"EnhancedInputField 创建: {label}")
    
    def _setup_ui(self):
        """设置 UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 标签
        self.label = QLabel(self.label_text)
        self.label.setObjectName("floatingLabel")
        layout.addWidget(self.label)
        
        # 输入框容器
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)
        
        # 输入框
        self.input = QLineEdit()
        self.input.setPlaceholderText(self.placeholder_text)
        self.input.setMinimumHeight(36)
        input_layout.addWidget(self.input)
        
        # 清除按钮
        self.clear_button = QPushButton("×")
        self.clear_button.setFixedSize(24, 24)
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.setVisible(False)
        self.clear_button.setObjectName("clearButton")
        input_layout.addWidget(self.clear_button)
        
        layout.addWidget(input_container)
        
        # 验证消息标签
        self.validation_label = QLabel()
        self.validation_label.setObjectName("validationLabel")
        self.validation_label.setVisible(False)
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)
        
        # 连接信号
        self.input.textChanged.connect(self._on_text_changed)
        self.input.returnPressed.connect(self.returnPressed.emit)
        self.input.focusInEvent = self._on_focus_in
        self.input.focusOutEvent = self._on_focus_out
        self.clear_button.clicked.connect(self.clear)
    
    def _setup_animations(self):
        """设置动画"""
        # 标签位置动画
        self.label_animation = QPropertyAnimation(self.label, b"pos")
        self.label_animation.setDuration(200)
        self.label_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        # 底部边框动画
        self.border_animation = QPropertyAnimation(self, b"border_progress")
        self.border_animation.setDuration(200)
        self.border_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.border_animation.valueChanged.connect(self.update)
    
    def _on_focus_in(self, event):
        """输入框获得焦点"""
        QLineEdit.focusInEvent(self.input, event)
        
        # 启动底部边框动画
        self.border_animation.setStartValue(0.0)
        self.border_animation.setEndValue(1.0)
        self.border_animation.start()
        
        logger.debug(f"输入框获得焦点: {self.label_text}")
    
    def _on_focus_out(self, event):
        """输入框失去焦点"""
        QLineEdit.focusOutEvent(self.input, event)
        
        # 反向播放底部边框动画
        self.border_animation.setStartValue(1.0)
        self.border_animation.setEndValue(0.0)
        self.border_animation.start()
        
        logger.debug(f"输入框失去焦点: {self.label_text}")
    
    def _on_text_changed(self, text: str):
        """文本改变处理"""
        # 显示/隐藏清除按钮
        self.clear_button.setVisible(bool(text))
        
        # 发射信号
        self.textChanged.emit(text)
    
    def _apply_theme(self):
        """应用主题"""
        colors = self.theme_manager.get_all_colors()
        
        # 输入框样式
        input_style = f"""
            QLineEdit {{
                background-color: {self._rgba(colors["glass_normal"])};
                border: 1px solid {colors["border"].name()};
                border-radius: 5px;
                padding: 8px 12px;
                color: {colors["text_primary"].name()};
                font-size: 14px;
            }}
            QLineEdit:hover {{
                background-color: {self._rgba(colors["glass_hover"])};
                border-color: {colors["border_hover"].name()};
            }}
            QLineEdit:focus {{
                background-color: {self._rgba(colors["glass_hover"])};
            }}
        """
        
        # 根据验证状态调整边框颜色
        if self._validation_state == 'success':
            input_style += f"""
                QLineEdit {{
                    border-color: {colors["success"].name()};
                }}
            """
        elif self._validation_state == 'error':
            input_style += f"""
                QLineEdit {{
                    border-color: {colors["error"].name()};
                }}
            """
        
        self.input.setStyleSheet(input_style)
        
        # 标签样式
        label_style = f"""
            QLabel#floatingLabel {{
                color: {colors["text_secondary"].name()};
                font-size: 12px;
                font-weight: 500;
            }}
        """
        self.label.setStyleSheet(label_style)
        
        # 清除按钮样式
        clear_button_style = f"""
            QPushButton#clearButton {{
                background-color: transparent;
                border: none;
                color: {colors["text_secondary"].name()};
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton#clearButton:hover {{
                background-color: {self._rgba(colors["surface_hover"])};
                color: {colors["text_primary"].name()};
            }}
        """
        self.clear_button.setStyleSheet(clear_button_style)
        
        # 验证消息样式
        validation_color = colors["text_secondary"]
        if self._validation_state == 'success':
            validation_color = colors["success"]
        elif self._validation_state == 'error':
            validation_color = colors["error"]
        
        validation_style = f"""
            QLabel#validationLabel {{
                color: {validation_color.name()};
                font-size: 12px;
            }}
        """
        self.validation_label.setStyleSheet(validation_style)
    
    def paintEvent(self, event):
        """绘制底部边框动画"""
        super().paintEvent(event)
        
        if self._border_progress > 0 and self.input.hasFocus():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 获取主题颜色
            colors = self.theme_manager.get_all_colors()
            border_color = colors["border_focus"]
            
            # 根据验证状态调整颜色
            if self._validation_state == 'success':
                border_color = colors["success"]
            elif self._validation_state == 'error':
                border_color = colors["error"]
            
            # 设置画笔
            pen = QPen(border_color, 2)
            painter.setPen(pen)
            
            # 计算边框位置（输入框底部）
            input_rect = self.input.geometry()
            y = input_rect.bottom() + 1
            center_x = input_rect.center().x()
            
            # 从中心向两侧扩展
            half_width = int(input_rect.width() * self._border_progress / 2)
            start_x = center_x - half_width
            end_x = center_x + half_width
            
            # 绘制线条
            painter.drawLine(start_x, y, end_x, y)
    
    def set_validation_state(self, is_valid: bool, message: str = ""):
        """
        设置验证状态
        
        Args:
            is_valid: 是否有效
            message: 验证消息
        """
        # 更新验证状态
        old_state = self._validation_state
        self._validation_state = 'success' if is_valid else 'error'
        self._validation_message = message
        
        # 显示验证消息
        if message:
            self.validation_label.setText(message)
            self.validation_label.setVisible(True)
        else:
            self.validation_label.setVisible(False)
        
        # 重新应用主题（更新边框颜色）
        self._apply_theme()
        
        # 发射验证状态改变信号
        if old_state != self._validation_state:
            self.validationChanged.emit(is_valid)
        
        logger.debug(f"验证状态更新: {self.label_text}, valid={is_valid}, message={message}")
    
    def clear_validation(self):
        """清除验证状态"""
        self._validation_state = None
        self._validation_message = ""
        self.validation_label.setVisible(False)
        self._apply_theme()
    
    def text(self) -> str:
        """获取输入文本"""
        return self.input.text()
    
    def setText(self, text: str):
        """设置输入文本"""
        self.input.setText(text)
    
    def clear(self):
        """清除输入"""
        self.input.clear()
        self.clear_validation()
    
    def setPlaceholderText(self, text: str):
        """设置占位符文本"""
        self.input.setPlaceholderText(text)
    
    def setReadOnly(self, read_only: bool):
        """设置只读"""
        self.input.setReadOnly(read_only)
    
    def get_border_progress(self) -> float:
        """获取边框动画进度"""
        return self._border_progress
    
    def set_border_progress(self, progress: float):
        """设置边框动画进度"""
        self._border_progress = progress
    
    # 定义属性以便 QPropertyAnimation 使用
    border_progress = pyqtProperty(float, get_border_progress, set_border_progress)
    
    def _rgba(self, color: QColor) -> str:
        """将 QColor 转换为 rgba 字符串"""
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"


class EnhancedComboBox(QWidget):
    """
    增强的下拉框组件
    
    特性：
    - 浮动标签效果
    - 搜索过滤功能（选项超过 10 个时）
    - 底部边框动画
    """
    
    # 信号
    currentTextChanged = pyqtSignal(str)  # 当前文本改变信号
    currentIndexChanged = pyqtSignal(int)  # 当前索引改变信号
    
    def __init__(
        self,
        label: str,
        items: List[str] = None,
        parent: Optional[QWidget] = None
    ):
        """
        初始化增强下拉框
        
        Args:
            label: 标签文本
            items: 选项列表
            parent: 父组件
        """
        super().__init__(parent)
        
        self.label_text = label
        self.all_items = items or []
        
        # 获取管理器
        self.theme_manager = get_theme_manager()
        self.animation_manager = get_animation_manager()
        
        # 底部边框动画进度
        self._border_progress = 0.0
        
        # 初始化 UI
        self._setup_ui()
        self._setup_animations()
        self._apply_theme()
        
        # 连接主题变更信号
        self.theme_manager.theme_changed.connect(self._apply_theme)
        
        logger.debug(f"EnhancedComboBox 创建: {label}")
    
    def _setup_ui(self):
        """设置 UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 标签
        self.label = QLabel(self.label_text)
        self.label.setObjectName("floatingLabel")
        layout.addWidget(self.label)
        
        # 下拉框
        self.combobox = QComboBox()
        self.combobox.setMinimumHeight(36)
        self.combobox.addItems(self.all_items)
        layout.addWidget(self.combobox)
        
        # 如果选项超过 10 个，添加搜索功能
        if len(self.all_items) > 10:
            self.combobox.setEditable(True)
            self.combobox.setInsertPolicy(QComboBox.NoInsert)
            
            # 创建自动完成器
            completer = QCompleter(self.all_items)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.combobox.setCompleter(completer)
            
            # 连接文本改变信号以实现过滤
            self.combobox.lineEdit().textChanged.connect(self._filter_items)
        
        # 连接信号
        self.combobox.currentTextChanged.connect(self.currentTextChanged.emit)
        self.combobox.currentIndexChanged.connect(self.currentIndexChanged.emit)
        
        # 重写焦点事件
        self.combobox.focusInEvent = self._on_focus_in
        self.combobox.focusOutEvent = self._on_focus_out
    
    def _setup_animations(self):
        """设置动画"""
        # 底部边框动画
        self.border_animation = QPropertyAnimation(self, b"border_progress")
        self.border_animation.setDuration(200)
        self.border_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.border_animation.valueChanged.connect(self.update)
    
    def _on_focus_in(self, event):
        """下拉框获得焦点"""
        QComboBox.focusInEvent(self.combobox, event)
        
        # 启动底部边框动画
        self.border_animation.setStartValue(0.0)
        self.border_animation.setEndValue(1.0)
        self.border_animation.start()
    
    def _on_focus_out(self, event):
        """下拉框失去焦点"""
        QComboBox.focusOutEvent(self.combobox, event)
        
        # 反向播放底部边框动画
        self.border_animation.setStartValue(1.0)
        self.border_animation.setEndValue(0.0)
        self.border_animation.start()
    
    def _filter_items(self, text: str):
        """
        过滤选项
        
        Args:
            text: 搜索文本
        """
        if not text:
            # 如果搜索文本为空，显示所有选项
            self.combobox.clear()
            self.combobox.addItems(self.all_items)
            return
        
        # 过滤匹配的选项
        filtered_items = [item for item in self.all_items if text.lower() in item.lower()]
        
        # 更新下拉框
        self.combobox.clear()
        self.combobox.addItems(filtered_items)
        
        # 如果有匹配项，显示下拉列表
        if filtered_items:
            self.combobox.showPopup()
    
    def _apply_theme(self):
        """应用主题"""
        colors = self.theme_manager.get_all_colors()
        
        # 下拉框样式
        combobox_style = f"""
            QComboBox {{
                background-color: {self._rgba(colors["glass_normal"])};
                border: 1px solid {colors["border"].name()};
                border-radius: 5px;
                padding: 8px 12px;
                color: {colors["text_primary"].name()};
                font-size: 14px;
            }}
            QComboBox:hover {{
                background-color: {self._rgba(colors["glass_hover"])};
                border-color: {colors["border_hover"].name()};
            }}
            QComboBox:focus {{
                background-color: {self._rgba(colors["glass_hover"])};
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
                border-top: 5px solid {colors["text_primary"].name()};
                width: 0px;
                height: 0px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors["surface"].name()};
                border: 1px solid {colors["border"].name()};
                selection-background-color: {colors["primary"].name()};
                selection-color: white;
                color: {colors["text_primary"].name()};
                outline: none;
            }}
        """
        self.combobox.setStyleSheet(combobox_style)
        
        # 标签样式
        label_style = f"""
            QLabel#floatingLabel {{
                color: {colors["text_secondary"].name()};
                font-size: 12px;
                font-weight: 500;
            }}
        """
        self.label.setStyleSheet(label_style)
    
    def paintEvent(self, event):
        """绘制底部边框动画"""
        super().paintEvent(event)
        
        if self._border_progress > 0 and self.combobox.hasFocus():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 获取主题颜色
            colors = self.theme_manager.get_all_colors()
            border_color = colors["border_focus"]
            
            # 设置画笔
            pen = QPen(border_color, 2)
            painter.setPen(pen)
            
            # 计算边框位置（下拉框底部）
            combobox_rect = self.combobox.geometry()
            y = combobox_rect.bottom() + 1
            center_x = combobox_rect.center().x()
            
            # 从中心向两侧扩展
            half_width = int(combobox_rect.width() * self._border_progress / 2)
            start_x = center_x - half_width
            end_x = center_x + half_width
            
            # 绘制线条
            painter.drawLine(start_x, y, end_x, y)
    
    def addItem(self, text: str):
        """添加选项"""
        self.all_items.append(text)
        self.combobox.addItem(text)
    
    def addItems(self, texts: List[str]):
        """添加多个选项"""
        self.all_items.extend(texts)
        self.combobox.addItems(texts)
    
    def clear(self):
        """清除所有选项"""
        self.all_items.clear()
        self.combobox.clear()
    
    def currentText(self) -> str:
        """获取当前文本"""
        return self.combobox.currentText()
    
    def setCurrentText(self, text: str):
        """设置当前文本"""
        self.combobox.setCurrentText(text)
    
    def currentIndex(self) -> int:
        """获取当前索引"""
        return self.combobox.currentIndex()
    
    def setCurrentIndex(self, index: int):
        """设置当前索引"""
        self.combobox.setCurrentIndex(index)
    
    def get_border_progress(self) -> float:
        """获取边框动画进度"""
        return self._border_progress
    
    def set_border_progress(self, progress: float):
        """设置边框动画进度"""
        self._border_progress = progress
    
    # 定义属性以便 QPropertyAnimation 使用
    border_progress = pyqtProperty(float, get_border_progress, set_border_progress)
    
    def _rgba(self, color: QColor) -> str:
        """将 QColor 转换为 rgba 字符串"""
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
