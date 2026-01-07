# -*- coding: utf-8 -*-
"""
自定义标题栏组件

实现需求 3.2：自定义标题栏
- 窗口控制按钮（最小化、最大化、关闭）
- 应用玻璃效果
- 支持窗口拖动
"""

import sys
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QPen
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                            QSizePolicy, QGraphicsDropShadowEffect)

try:
    from ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
except ImportError:
    from wallhaven_downloader.ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel


class CustomTitleBar(EnhancedGlassPanel):
    """
    自定义标题栏组件
    
    需求 3.2：实现自定义标题栏
    - 窗口控制按钮（最小化、最大化、关闭）
    - 应用玻璃效果
    - 支持窗口拖动
    """
    
    # 信号
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    
    def __init__(self, parent=None, title=""):
        """初始化自定义标题栏
        
        Args:
            parent: 父窗口
            title: 窗口标题
        """
        # 使用玻璃面板配置
        config = {
            "blur_radius": 15,
            "transparency": 0.9,
            "border_radius": 0,  # 标题栏不需要圆角
            "shadow_blur": 10
        }
        super().__init__(parent, config)
        self.setStyleSheet("""
            CustomTitleBar {
                border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            }
        """)
        
        self.parent_window = parent
        self.title_text = title
        
        # 拖动状态
        self._is_dragging = False
        self._drag_position = QPoint()
        
        # 设置固定高度 - 增大以容纳更大的按钮
        self.setFixedHeight(56)
        
        # 初始化 UI
        self._init_ui()
        
        # 关闭阴影以避免在透明无边框窗口上扩展脏区域导致 UpdateLayeredWindowIndirect 失败
        self._disable_shadow_effect()
    
    def _init_ui(self):
        """初始化 UI 组件"""
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        # 应用图标（可选）
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setScaledContents(True)
        layout.addWidget(self.icon_label)
        
        # 窗口标题
        self.title_label = QLabel(self.title_text)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #1D1D1F;
                font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC";
                font-size: 18px;
                font-weight: 700;
                background: transparent;
                letter-spacing: 0.3px;
            }
        """)
        layout.addStretch()
        layout.addWidget(self.title_label)
        
        # 弹性空间
        layout.addStretch()
        
        # 窗口控制按钮
        self._create_control_buttons(layout)
    
    def _create_control_buttons(self, layout):
        """创建窗口控制按钮
        
        Args:
            layout: 布局对象
        """
        # 按钮样式 - 参考主界面玻璃按钮效果
        button_style = """
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 220),
                    stop:1 rgba(255, 255, 255, 180)
                );
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 10px;
                color: rgb(50, 50, 50);
                font-size: 18px;
                font-weight: 700;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 250),
                    stop:1 rgba(255, 255, 255, 220)
                );
                border: 1px solid rgba(59, 130, 246, 200);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(240, 240, 240, 220),
                    stop:1 rgba(230, 230, 230, 200)
                );
                border: 1px solid rgba(59, 130, 246, 250);
            }
        """
        
        # 最小化按钮
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(52, 40)
        self.minimize_btn.setStyleSheet(button_style)
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        self.minimize_btn.setToolTip("最小化")
        self.minimize_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.minimize_btn)
        
        # 最大化/还原按钮
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(52, 40)
        self.maximize_btn.setStyleSheet(button_style)
        self.maximize_btn.clicked.connect(self._on_maximize_clicked)
        self.maximize_btn.setToolTip("最大化")
        self.maximize_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.maximize_btn)
        
        # 关闭按钮（特殊样式 - 悬停时红色）
        close_button_style = """
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 220),
                    stop:1 rgba(255, 255, 255, 180)
                );
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 10px;
                color: rgb(50, 50, 50);
                font-size: 20px;
                font-weight: 700;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(239, 68, 68, 240),
                    stop:1 rgba(220, 38, 38, 220)
                );
                color: white;
                border: 1px solid rgba(239, 68, 68, 250);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(185, 28, 28, 240),
                    stop:1 rgba(153, 27, 27, 220)
                );
                color: white;
                border: 1px solid rgba(185, 28, 28, 250);
            }
        """
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(52, 40)
        self.close_btn.setStyleSheet(close_button_style)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        self.close_btn.setToolTip("关闭")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.close_btn)
    
    def _on_maximize_clicked(self):
        """处理最大化按钮点击"""
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.maximize_btn.setText("□")
                self.maximize_clicked.emit()
            else:
                self.maximize_btn.setText("❐")
                self.maximize_clicked.emit()
    
    def _disable_shadow_effect(self):
        """禁用默认阴影，避免在透明无边框窗口产生超界脏区域"""
        effect = self.graphicsEffect()
        if effect:
            self.setGraphicsEffect(None)
    
    def set_title(self, title):
        """设置窗口标题
        
        Args:
            title: 窗口标题文本
        """
        self.title_text = title
        self.title_label.setText(title)
    
    def set_icon(self, icon_path):
        """设置窗口图标
        
        Args:
            icon_path: 图标文件路径
        """
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            self.icon_label.setPixmap(pixmap.scaled(
                24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
    
    def update_maximize_button(self, is_maximized):
        """更新最大化按钮状态
        
        Args:
            is_maximized: 是否已最大化
        """
        if is_maximized:
            self.maximize_btn.setText("❐")
            self.maximize_btn.setToolTip("还原")
        else:
            self.maximize_btn.setText("□")
            self.maximize_btn.setToolTip("最大化")
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖动窗口"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在按钮上
            if not self._is_click_on_button(event.pos()):
                self._is_dragging = True
                if self.parent_window:
                    self._drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖动窗口"""
        if event.buttons() == Qt.LeftButton and self._is_dragging:
            if self.parent_window and not self.parent_window.isMaximized():
                self.parent_window.move(event.globalPos() - self._drag_position)
                event.accept()
                return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖动"""
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件 - 最大化/还原窗口"""
        if event.button() == Qt.LeftButton:
            if not self._is_click_on_button(event.pos()):
                self._on_maximize_clicked()
                event.accept()
                return
        
        super().mouseDoubleClickEvent(event)
    
    def _is_click_on_button(self, pos):
        """检查点击位置是否在按钮上
        
        Args:
            pos: 点击位置
            
        Returns:
            是否在按钮上
        """
        # 检查是否点击在控制按钮上
        for btn in [self.minimize_btn, self.maximize_btn, self.close_btn]:
            if btn.geometry().contains(pos):
                return True
        return False
    
    def apply_theme(self, is_dark_mode=False):
        """应用主题
        
        Args:
            is_dark_mode: 是否为深色模式
        """
        if is_dark_mode:
            # 深色主题
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #F5F5F7;
                    font-size: 18px;
                    font-weight: 700;
                    background: transparent;
                    letter-spacing: 0.3px;
                }
            """)
            
            button_style = """
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(60, 60, 60, 220),
                        stop:1 rgba(40, 40, 40, 180)
                    );
                    border: 1px solid rgba(100, 100, 100, 150);
                    border-radius: 10px;
                    color: #F5F5F7;
                    font-size: 18px;
                    font-weight: 700;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(80, 80, 80, 240),
                        stop:1 rgba(60, 60, 60, 200)
                    );
                    border: 1px solid rgba(59, 130, 246, 200);
                }
                QPushButton:pressed {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(40, 40, 40, 220),
                        stop:1 rgba(30, 30, 30, 200)
                    );
                    border: 1px solid rgba(59, 130, 246, 250);
                }
            """
            
            self.minimize_btn.setStyleSheet(button_style)
            self.maximize_btn.setStyleSheet(button_style)
            
            close_button_style = """
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(60, 60, 60, 220),
                        stop:1 rgba(40, 40, 40, 180)
                    );
                    border: 1px solid rgba(100, 100, 100, 150);
                    border-radius: 10px;
                    color: #F5F5F7;
                    font-size: 20px;
                    font-weight: 700;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 69, 58, 240),
                        stop:1 rgba(211, 47, 47, 220)
                    );
                    color: white;
                    border: 1px solid rgba(255, 69, 58, 250);
                }
                QPushButton:pressed {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(211, 47, 47, 240),
                        stop:1 rgba(183, 28, 28, 220)
                    );
                    color: white;
                    border: 1px solid rgba(211, 47, 47, 250);
                }
            """
            self.close_btn.setStyleSheet(close_button_style)
        else:
            # 浅色主题（默认）
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #1D1D1F;
                    font-size: 18px;
                    font-weight: 700;
                    background: transparent;
                    letter-spacing: 0.3px;
                }
            """)
            
            button_style = """
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 220),
                        stop:1 rgba(255, 255, 255, 180)
                    );
                    border: 1px solid rgba(200, 200, 200, 150);
                    border-radius: 10px;
                    color: rgb(50, 50, 50);
                    font-size: 18px;
                    font-weight: 700;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 250),
                        stop:1 rgba(255, 255, 255, 220)
                    );
                    border: 1px solid rgba(59, 130, 246, 200);
                }
                QPushButton:pressed {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(240, 240, 240, 220),
                        stop:1 rgba(230, 230, 230, 200)
                    );
                    border: 1px solid rgba(59, 130, 246, 250);
                }
            """
            
            self.minimize_btn.setStyleSheet(button_style)
            self.maximize_btn.setStyleSheet(button_style)
            
            close_button_style = """
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 220),
                        stop:1 rgba(255, 255, 255, 180)
                    );
                    border: 1px solid rgba(200, 200, 200, 150);
                    border-radius: 10px;
                    color: rgb(50, 50, 50);
                    font-size: 20px;
                    font-weight: 700;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 59, 48, 240),
                        stop:1 rgba(220, 38, 38, 220)
                    );
                    color: white;
                    border: 1px solid rgba(255, 59, 48, 250);
                }
                QPushButton:pressed {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(211, 47, 47, 240),
                        stop:1 rgba(183, 28, 28, 220)
                    );
                    color: white;
                    border: 1px solid rgba(211, 47, 47, 250);
                }
            """
            self.close_btn.setStyleSheet(close_button_style)
