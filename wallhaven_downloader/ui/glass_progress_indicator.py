# -*- coding: utf-8 -*-
"""
玻璃进度指示器组件

提供带有渐变色和流动光泽动画的进度条
"""

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush, QPainterPath
from PyQt5.QtWidgets import QWidget


class GlassProgressIndicator(QWidget):
    """
    玻璃进度指示器
    
    特性：
    - 渐变色进度条
    - 流动光泽动画
    - 状态颜色（进行中、完成、失败、暂停）
    
    需求：8.3-8.5
    """
    
    # 状态常量
    STATUS_DOWNLOADING = "downloading"  # 下载中 - 蓝色
    STATUS_COMPLETED = "completed"  # 完成 - 绿色
    STATUS_FAILED = "failed"  # 失败 - 红色
    STATUS_PAUSED = "paused"  # 暂停 - 橙色
    STATUS_PENDING = "pending"  # 等待 - 灰色
    
    # 状态颜色映射（需求 8.5）
    STATUS_COLORS = {
        STATUS_DOWNLOADING: {
            "start": QColor(0, 122, 255),  # #007AFF 苹果蓝
            "end": QColor(10, 132, 255)  # #0A84FF 浅蓝
        },
        STATUS_COMPLETED: {
            "start": QColor(52, 199, 89),  # #34C759 绿色
            "end": QColor(48, 209, 88)  # #30D158 浅绿
        },
        STATUS_FAILED: {
            "start": QColor(255, 59, 48),  # #FF3B30 红色
            "end": QColor(255, 69, 58)  # #FF453A 浅红
        },
        STATUS_PAUSED: {
            "start": QColor(255, 149, 0),  # #FF9500 橙色
            "end": QColor(255, 159, 10)  # #FF9F0A 浅橙
        },
        STATUS_PENDING: {
            "start": QColor(134, 134, 139),  # #86868B 灰色
            "end": QColor(152, 152, 157)  # #98989D 浅灰
        }
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 进度值 (0-100)
        self._progress = 0
        
        # 状态
        self._status = self.STATUS_PENDING
        
        # 流动光泽动画偏移量 (0-1)
        self._shine_offset = 0.0
        
        # 背景色
        self._background_color = QColor(200, 200, 200, 80)  # 半透明灰色
        
        # 边框圆角
        self._border_radius = 3
        
        # 流动光泽动画定时器（需求 8.4）
        self._shine_timer = QTimer(self)
        self._shine_timer.timeout.connect(self._update_shine)
        self._shine_timer.setInterval(30)  # 30ms 更新一次，约 33 FPS
        
        # 动画速度
        self._shine_speed = 0.02  # 每次更新移动 2%
        
        # 设置固定高度
        self.setFixedHeight(6)
        
        # 设置最小宽度
        self.setMinimumWidth(100)
    
    def set_progress(self, progress: int):
        """
        设置进度
        
        Args:
            progress: 进度百分比 (0-100)
        """
        self._progress = max(0, min(100, progress))
        self.update()
    
    def get_progress(self) -> int:
        """获取当前进度"""
        return self._progress
    
    def set_status(self, status: str):
        """
        设置状态
        
        Args:
            status: 状态值（使用 STATUS_* 常量）
        """
        self._status = status
        
        # 根据状态控制流动光泽动画
        if status == self.STATUS_DOWNLOADING:
            self.start_shine_animation()
        else:
            self.stop_shine_animation()
        
        self.update()
    
    def get_status(self) -> str:
        """获取当前状态"""
        return self._status
    
    def start_shine_animation(self):
        """启动流动光泽动画（需求 8.4）"""
        if not self._shine_timer.isActive():
            self._shine_timer.start()
    
    def stop_shine_animation(self):
        """停止流动光泽动画"""
        if self._shine_timer.isActive():
            self._shine_timer.stop()
        self._shine_offset = 0.0
        self.update()
    
    def _update_shine(self):
        """更新流动光泽偏移量"""
        self._shine_offset += self._shine_speed
        if self._shine_offset >= 1.0:
            self._shine_offset = 0.0
        self.update()
    
    def paintEvent(self, event):
        """绘制进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 获取绘制区域
        rect = self.rect()
        
        # === 第一层：背景 ===
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self._background_color))
        painter.drawRoundedRect(rect, self._border_radius, self._border_radius)
        
        # === 第二层：进度条 ===
        if self._progress > 0:
            # 计算进度条宽度
            progress_width = int(rect.width() * self._progress / 100)
            progress_rect = rect.adjusted(0, 0, -(rect.width() - progress_width), 0)
            
            # 获取状态颜色
            colors = self.STATUS_COLORS.get(
                self._status,
                self.STATUS_COLORS[self.STATUS_PENDING]
            )
            
            # 创建渐变色（需求 8.3）
            gradient = QLinearGradient(progress_rect.topLeft(), progress_rect.topRight())
            gradient.setColorAt(0, colors["start"])
            gradient.setColorAt(1, colors["end"])
            
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(progress_rect, self._border_radius, self._border_radius)
            
            # === 第三层：流动光泽效果（需求 8.4）===
            if self._status == self.STATUS_DOWNLOADING and self._progress < 100:
                self._draw_shine_effect(painter, progress_rect)
    
    def _draw_shine_effect(self, painter: QPainter, progress_rect):
        """
        绘制流动光泽效果
        
        实现原理：
        1. 创建一个从左到右移动的高光渐变
        2. 高光宽度约为进度条宽度的 30%
        3. 使用定时器不断更新偏移量，产生流动效果
        """
        # 保存画家状态
        painter.save()
        
        # 设置裁剪区域为进度条
        clip_path = QPainterPath()
        clip_path.addRoundedRect(
            progress_rect.x(), progress_rect.y(),
            progress_rect.width(), progress_rect.height(),
            self._border_radius, self._border_radius
        )
        painter.setClipPath(clip_path)
        
        # 计算光泽位置和宽度
        shine_width = progress_rect.width() * 0.3  # 光泽宽度为进度条的 30%
        shine_x = progress_rect.x() + (progress_rect.width() + shine_width) * self._shine_offset - shine_width
        
        # 创建光泽渐变
        shine_gradient = QLinearGradient(shine_x, 0, shine_x + shine_width, 0)
        shine_gradient.setColorAt(0, QColor(255, 255, 255, 0))  # 完全透明
        shine_gradient.setColorAt(0.5, QColor(255, 255, 255, 100))  # 半透明白色
        shine_gradient.setColorAt(1, QColor(255, 255, 255, 0))  # 完全透明
        
        # 绘制光泽
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shine_gradient))
        painter.drawRect(
            int(shine_x),
            progress_rect.y(),
            int(shine_width),
            progress_rect.height()
        )
        
        # 恢复画家状态
        painter.restore()
    
    def showEvent(self, event):
        """显示事件 - 如果是下载中状态，启动动画"""
        super().showEvent(event)
        if self._status == self.STATUS_DOWNLOADING:
            self.start_shine_animation()
    
    def hideEvent(self, event):
        """隐藏事件 - 停止动画"""
        super().hideEvent(event)
        self.stop_shine_animation()
    
    # === Qt 属性（用于动画）===
    
    def _get_shine_offset(self):
        """获取光泽偏移量"""
        return self._shine_offset
    
    def _set_shine_offset(self, value):
        """设置光泽偏移量"""
        self._shine_offset = value
        self.update()
    
    shine_offset = pyqtProperty(float, _get_shine_offset, _set_shine_offset)

