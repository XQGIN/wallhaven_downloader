# -*- coding: utf-8 -*-
"""
增强玻璃按钮组件
扩展现有 GlassButton，实现三种样式和完整的玻璃效果
"""

from typing import Optional
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt5.QtWidgets import QPushButton, QWidget, QGraphicsDropShadowEffect
from PyQt5.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, 
    QRadialGradient, QPixmap, QFont
)

try:
    from utils.logger import get_logger
    from core.enhanced_theme_manager import get_enhanced_theme_manager
    from utils.accessibility_manager import get_accessibility_manager
except ImportError:
    from ..utils.logger import get_logger
    from ..core.enhanced_theme_manager import get_enhanced_theme_manager
    from ..utils.accessibility_manager import get_accessibility_manager

logger = get_logger(__name__)


class EnhancedGlassButton(QPushButton):
    """
    增强玻璃按钮组件
    
    提供三种样式：
    - primary: 主要按钮（强调色背景 + 白色文本）
    - secondary: 次要按钮（半透明背景 + 主题色文本）
    - text: 文本按钮（无背景 + 主题色文本）
    
    特性：
    - 完整的玻璃效果（模糊、透明、光影）
    - 悬停和按下动画
    - 涟漪效果
    - 主题自适应
    - 禁用状态支持
    """
    
    # 按钮样式
    STYLE_PRIMARY = "primary"
    STYLE_SECONDARY = "secondary"
    STYLE_TEXT = "text"
    
    # 信号
    ripple_started = pyqtSignal(QPoint)  # 涟漪开始
    
    def __init__(
        self,
        text: str = "",
        style: str = STYLE_PRIMARY,
        parent: Optional[QWidget] = None
    ):
        """
        初始化增强玻璃按钮
        
        Args:
            text: 按钮文本
            style: 按钮样式 (primary, secondary, text)
            parent: 父组件
        """
        super().__init__(text, parent)
        
        # 样式
        self.button_style = style
        
        # 主题管理器
        self.theme_manager = get_enhanced_theme_manager()
        
        # 辅助功能管理器
        self.accessibility_manager = get_accessibility_manager()
        
        # 状态
        self._is_hovered = False
        self._is_pressed = False
        
        # 颜色（将在 _update_colors 中设置）
        self._normal_bg_color = QColor()
        self._hover_bg_color = QColor()
        self._pressed_bg_color = QColor()
        self._text_color = QColor()
        self._border_color = QColor()
        
        # 当前颜色和目标颜色
        self._current_bg_color = QColor()
        self._target_bg_color = QColor()
        
        # 视觉参数
        self._blur_radius = 20  # 模糊半径
        self._transparency = 0.7  # 透明度
        self._border_radius = 10  # 圆角半径
        self._shadow_blur = 20  # 阴影模糊度
        self._edge_highlight_width = 2  # 边缘高光宽度
        
        # 动画参数
        self._animation_progress = 0.0  # 动画进度 (0.0 到 1.0)
        self._animation_timer = None  # 动画定时器
        self._animation_duration = 200  # 动画持续时间（毫秒）
        self._animation_start_time = 0  # 动画开始时间
        
        # 涟漪效果参数
        self._ripple_animation = False  # 是否有涟漪动画
        self._ripple_progress = 0.0  # 涟漪动画进度
        self._ripple_timer = None  # 涟漪动画定时器
        self._ripple_duration = 400  # 涟漪动画持续时间（毫秒）
        self._ripple_start_time = 0  # 涟漪动画开始时间
        self._ripple_center = QPoint()  # 涟漪中心点
        self._ripple_max_radius = 0  # 涟漪最大半径
        
        # 缩放动画参数
        self._scale_animation = False  # 是否有缩放动画
        self._scale_progress = 0.0  # 缩放动画进度
        self._scale_timer = None  # 缩放动画定时器
        self._scale_duration = 150  # 缩放动画持续时间（毫秒）
        self._scale_start_time = 0  # 缩放动画开始时间
        self._scale_factor = 1.0  # 当前缩放因子
        self._target_scale = 1.0  # 目标缩放因子
        self._normal_scale = 1.0  # 正常缩放
        self._pressed_scale = 0.97  # 按下时的缩放（0.95-0.98）
        
        # 缓存
        self._cached_pixmap = None  # 缓存按钮图像
        self._needs_update = True  # 是否需要更新缓存
        
        # 初始化
        self._update_colors()
        self._setup_ui()
        self._setup_accessibility()
        
        # 连接主题变化信号
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        
        logger.debug(f"EnhancedGlassButton 创建: style={style}, text={text}")
    
    def _setup_ui(self):
        """设置 UI"""
        # 设置光标
        self.setCursor(Qt.PointingHandCursor)
        
        # 设置最小高度
        if self.button_style == self.STYLE_TEXT:
            self.setMinimumHeight(36)
        else:
            self.setMinimumHeight(44)  # 符合可访问性要求（至少 44x44 像素）
        
        # 设置最小宽度
        self.setMinimumWidth(88)
    
    def _setup_accessibility(self):
        """设置辅助功能支持"""
        # 设置 ARIA 标签和角色
        style_desc = {
            self.STYLE_PRIMARY: "主要按钮",
            self.STYLE_SECONDARY: "次要按钮",
            self.STYLE_TEXT: "文本按钮"
        }
        
        description = f"{style_desc.get(self.button_style, '按钮')}"
        if self.text():
            self.accessibility_manager.setup_button_accessibility(
                self,
                label=self.text(),
                description=description
            )
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.StrongFocus)
        
        # 设置可访问的点击区域（已在 _setup_ui 中设置最小尺寸）
    
    def _update_colors(self):
        """更新颜色方案（根据主题和样式）"""
        is_dark = self.theme_manager.is_dark_mode()
        
        if self.button_style == self.STYLE_PRIMARY:
            # 主要按钮：强调色背景 + 白色文本
            accent_color = self.theme_manager.get_apple_color("accent")
            accent_hover = self.theme_manager.get_apple_color("accent_hover")
            accent_active = self.theme_manager.get_apple_color("accent_active")
            
            self._normal_bg_color = QColor(accent_color)
            self._normal_bg_color.setAlpha(int(255 * 0.9))
            
            self._hover_bg_color = QColor(accent_hover)
            self._hover_bg_color.setAlpha(int(255 * 0.95))
            
            self._pressed_bg_color = QColor(accent_active)
            self._pressed_bg_color.setAlpha(int(255 * 0.85))
            
            self._text_color = QColor(255, 255, 255)  # 白色文本
            self._border_color = QColor(accent_color)
            self._border_color.setAlpha(100)
            
        elif self.button_style == self.STYLE_SECONDARY:
            # 次要按钮：半透明背景 + 主题色文本
            glass_normal = self.theme_manager.get_apple_color("glass_normal")
            glass_hover = self.theme_manager.get_apple_color("glass_hover")
            glass_active = self.theme_manager.get_apple_color("glass_active")
            
            self._normal_bg_color = QColor(glass_normal)
            self._hover_bg_color = QColor(glass_hover)
            self._pressed_bg_color = QColor(glass_active)
            
            self._text_color = self.theme_manager.get_apple_color("text_primary")
            self._border_color = self.theme_manager.get_apple_color("border")
            
        else:  # STYLE_TEXT
            # 文本按钮：无背景 + 主题色文本
            self._normal_bg_color = QColor(0, 0, 0, 0)  # 完全透明
            self._hover_bg_color = self.theme_manager.get_apple_color("glass_normal")
            self._hover_bg_color.setAlpha(50)  # 非常淡的背景
            self._pressed_bg_color = self.theme_manager.get_apple_color("glass_active")
            self._pressed_bg_color.setAlpha(80)
            
            accent_color = self.theme_manager.get_apple_color("accent")
            self._text_color = QColor(accent_color)
            self._border_color = QColor(0, 0, 0, 0)  # 无边框
        
        # 设置当前颜色
        if not self._animation_timer:
            if self._is_pressed:
                self._current_bg_color = QColor(self._pressed_bg_color)
            elif self._is_hovered:
                self._current_bg_color = QColor(self._hover_bg_color)
            else:
                self._current_bg_color = QColor(self._normal_bg_color)
        
        # 标记需要更新
        self._needs_update = True
        self.update()
    
    def _on_theme_changed(self, theme: str):
        """主题变化处理"""
        self._update_colors()
        logger.debug(f"按钮主题已更新: {theme}")
    
    def paintEvent(self, event):
        """绘制按钮"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 应用缩放变换
        if self._scale_factor != 1.0:
            # 计算缩放中心点（按钮中心）
            center_x = self.width() / 2
            center_y = self.height() / 2
            
            # 应用缩放变换
            painter.translate(center_x, center_y)
            painter.scale(self._scale_factor, self._scale_factor)
            painter.translate(-center_x, -center_y)
        
        # 如果需要更新缓存或大小改变
        if self._needs_update or self._cached_pixmap is None or self._cached_pixmap.size() != self.size():
            self._update_cache()
            self._needs_update = False
        
        # 绘制缓存的按钮
        if self._cached_pixmap:
            painter.drawPixmap(0, 0, self._cached_pixmap)
        
        # 绘制涟漪效果
        if self._ripple_animation and self._ripple_progress > 0:
            self._draw_ripple(painter)
        
        # 绘制文本
        self._draw_text(painter)
    
    def _update_cache(self):
        """更新按钮缓存"""
        # 创建与按钮大小相同的缓存图像
        self._cached_pixmap = QPixmap(self.size())
        self._cached_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self._cached_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 使用动画进度进行颜色插值
        current_bg_color = self._interpolate_color(
            self._current_bg_color, 
            self._target_bg_color, 
            self._animation_progress
        )
        
        # 如果不是文本按钮，绘制阴影
        if self.button_style != self.STYLE_TEXT:
            self._draw_shadow(painter, current_bg_color)
        
        # 绘制玻璃背景
        self._draw_glass_background(painter, current_bg_color)
        
        # 如果不是文本按钮，绘制高光效果
        if self.button_style != self.STYLE_TEXT:
            self._draw_highlights(painter)
            self._draw_edge_highlight(painter)
        
        painter.end()
    
    def _draw_shadow(self, painter: QPainter, bg_color: QColor):
        """绘制阴影"""
        # 根据悬停状态调整阴影
        shadow_blur = self._shadow_blur
        shadow_alpha = 100
        
        if self._is_hovered:
            progress = self._ease_in_out_cubic(self._animation_progress)
            shadow_blur = int(self._shadow_blur + 10 * progress)
            shadow_alpha = int(100 + 50 * progress)
        
        # 绘制多层阴影
        shadow_rect = self.rect().adjusted(3, 3, -3, -3)
        painter.setPen(Qt.NoPen)
        
        for i in range(shadow_blur // 2):
            alpha = int(shadow_alpha * (1 - i / (shadow_blur // 2)) * 0.5)
            color = QColor(0, 0, 0, alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(
                shadow_rect.adjusted(i, i, -i, -i),
                self._border_radius,
                self._border_radius
            )
    
    def _draw_glass_background(self, painter: QPainter, bg_color: QColor):
        """绘制玻璃背景"""
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
        
        # 绘制边框（如果有）
        if self._border_color.alpha() > 0:
            painter.setPen(QPen(self._border_color, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                self.rect().adjusted(1, 1, -1, -1),
                self._border_radius,
                self._border_radius
            )
    
    def _draw_highlights(self, painter: QPainter):
        """绘制高光效果"""
        # 主高光 - 从上到下的线性渐变
        highlight_rect = QRect(
            self.rect().left() + 5,
            self.rect().top() + 5,
            self.rect().width() - 10,
            self.rect().height() // 3
        )
        
        main_gradient = QLinearGradient(highlight_rect.topLeft(), highlight_rect.bottomLeft())
        main_gradient.setColorAt(0, QColor(255, 255, 255, 80))
        main_gradient.setColorAt(0.7, QColor(255, 255, 255, 40))
        main_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(main_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(highlight_rect, self._border_radius, self._border_radius)
        
        # 次级高光 - 径向渐变
        highlight_radius = min(self.rect().width(), self.rect().height()) // 4
        highlight_center = QPoint(
            self.rect().left() + int(self.rect().width() * 0.3),
            self.rect().top() + int(self.rect().height() * 0.3)
        )
        
        radial_highlight = QRadialGradient(highlight_center, highlight_radius)
        radial_highlight.setColorAt(0, QColor(255, 255, 255, 60))
        radial_highlight.setColorAt(0.5, QColor(255, 255, 255, 30))
        radial_highlight.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(radial_highlight))
        painter.drawEllipse(
            highlight_center.x() - highlight_radius,
            highlight_center.y() - highlight_radius,
            highlight_radius * 2,
            highlight_radius * 2
        )
    
    def _draw_edge_highlight(self, painter: QPainter):
        """绘制边缘高光"""
        edge_rect = self.rect().adjusted(2, 2, -2, -2)
        
        # 创建边缘高光的渐变
        edge_gradient = QLinearGradient(edge_rect.topLeft(), edge_rect.topRight())
        edge_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        edge_gradient.setColorAt(0.2, QColor(255, 255, 255, 60))
        edge_gradient.setColorAt(0.5, QColor(255, 255, 255, 100))
        edge_gradient.setColorAt(0.8, QColor(255, 255, 255, 60))
        edge_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(QPen(edge_gradient, self._edge_highlight_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(edge_rect, self._border_radius, self._border_radius)
    
    def _draw_ripple(self, painter: QPainter):
        """绘制涟漪效果"""
        # 计算当前波纹半径
        current_radius = int(self._ripple_max_radius * self._ripple_progress)
        
        # 计算波纹透明度（随着扩散逐渐消失）
        ripple_alpha = int(150 * (1 - self._ripple_progress))
        
        # 绘制多层波纹
        for i in range(3):
            layer_radius = current_radius - i * 5
            layer_alpha = ripple_alpha // (i + 1)
            
            if layer_radius > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 255, 255, layer_alpha))
                painter.drawEllipse(
                    self._ripple_center.x() - layer_radius,
                    self._ripple_center.y() - layer_radius,
                    layer_radius * 2,
                    layer_radius * 2
                )
    
    def _draw_text(self, painter: QPainter):
        """绘制文本"""
        painter.setPen(QPen(self._text_color))
        
        # 设置字体
        font = QFont()
        if self.button_style == self.STYLE_PRIMARY:
            font.setBold(True)
        painter.setFont(font)
        
        # 如果不是文本按钮，添加文本阴影
        if self.button_style != self.STYLE_TEXT:
            shadow_offset = 1
            painter.setPen(QPen(QColor(0, 0, 0, 50)))
            painter.drawText(
                self.rect().adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset),
                Qt.AlignCenter,
                self.text()
            )
        
        # 绘制主文本
        painter.setPen(QPen(self._text_color))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
    
    # ==================== 动画方法 ====================
    
    def _start_animation(self, target_color: QColor):
        """开始颜色过渡动画"""
        self._target_bg_color = QColor(target_color)
        self._animation_progress = 0.0
        self._animation_start_time = 0
        
        # 如果已有定时器，先停止
        if self._animation_timer:
            self.killTimer(self._animation_timer)
        
        # 启动新的定时器
        self._animation_timer = self.startTimer(16)  # 约60fps
    
    def _update_animation(self):
        """更新动画进度"""
        if self._animation_start_time == 0:
            import time
            self._animation_start_time = time.time() * 1000
        
        import time
        elapsed = time.time() * 1000 - self._animation_start_time
        self._animation_progress = min(1.0, elapsed / self._animation_duration)
        
        # 更新缓存并重绘
        self._needs_update = True
        self.update()
        
        # 动画完成
        if self._animation_progress >= 1.0:
            self._current_bg_color = QColor(self._target_bg_color)
            self.killTimer(self._animation_timer)
            self._animation_timer = None
    
    def _start_ripple_animation(self, pos: QPoint):
        """开始波纹动画"""
        self._ripple_animation = True
        self._ripple_progress = 0.0
        self._ripple_start_time = 0
        self._ripple_center = pos
        
        # 计算最大波纹半径（从点击点到按钮最远角的距离）
        dx = max(pos.x(), self.width() - pos.x())
        dy = max(pos.y(), self.height() - pos.y())
        self._ripple_max_radius = int((dx * dx + dy * dy) ** 0.5)
        
        # 如果已有定时器，先停止
        if self._ripple_timer:
            self.killTimer(self._ripple_timer)
        
        # 启动新的定时器
        self._ripple_timer = self.startTimer(16)  # 约60fps
        
        # 发射信号
        self.ripple_started.emit(pos)
    
    def _update_ripple_animation(self):
        """更新波纹动画进度"""
        if self._ripple_start_time == 0:
            import time
            self._ripple_start_time = time.time() * 1000
        
        import time
        elapsed = time.time() * 1000 - self._ripple_start_time
        raw_progress = min(1.0, elapsed / self._ripple_duration)
        
        # 使用缓出函数使波纹扩散更自然
        self._ripple_progress = self._ease_out_quad(raw_progress)
        
        # 重绘
        self.update()
        
        # 动画完成
        if raw_progress >= 1.0:
            self._ripple_animation = False
            self.killTimer(self._ripple_timer)
            self._ripple_timer = None
    
    def _start_scale_animation(self, target_scale: float):
        """开始缩放动画"""
        self._scale_animation = True
        self._target_scale = target_scale
        self._scale_progress = 0.0
        self._scale_start_time = 0
        
        # 如果已有定时器，先停止
        if self._scale_timer:
            self.killTimer(self._scale_timer)
        
        # 启动新的定时器
        self._scale_timer = self.startTimer(16)  # 约60fps
    
    def _update_scale_animation(self):
        """更新缩放动画进度"""
        if self._scale_start_time == 0:
            import time
            self._scale_start_time = time.time() * 1000
        
        import time
        elapsed = time.time() * 1000 - self._scale_start_time
        raw_progress = min(1.0, elapsed / self._scale_duration)
        
        # 使用缓动函数
        eased_progress = self._ease_in_out_cubic(raw_progress)
        
        # 计算当前缩放因子
        start_scale = self._scale_factor
        self._scale_factor = start_scale + (self._target_scale - start_scale) * eased_progress
        
        # 重绘
        self.update()
        
        # 动画完成
        if raw_progress >= 1.0:
            self._scale_factor = self._target_scale
            self._scale_animation = False
            self.killTimer(self._scale_timer)
            self._scale_timer = None
    
    # ==================== 缓动函数 ====================
    
    def _interpolate_color(self, start_color: QColor, end_color: QColor, progress: float) -> QColor:
        """在两种颜色之间进行插值"""
        eased_progress = self._ease_in_out_cubic(progress)
        
        r = int(start_color.red() + (end_color.red() - start_color.red()) * eased_progress)
        g = int(start_color.green() + (end_color.green() - start_color.green()) * eased_progress)
        b = int(start_color.blue() + (end_color.blue() - start_color.blue()) * eased_progress)
        a = int(start_color.alpha() + (end_color.alpha() - start_color.alpha()) * eased_progress)
        return QColor(r, g, b, a)
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """三次贝塞尔缓动函数"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def _ease_out_quad(self, t: float) -> float:
        """二次缓出函数"""
        return 1 - (1 - t) * (1 - t)
    
    # ==================== 事件处理 ====================
    
    def timerEvent(self, event):
        """定时器事件"""
        if event.timerId() == self._animation_timer:
            self._update_animation()
        elif event.timerId() == self._ripple_timer:
            self._update_ripple_animation()
        elif event.timerId() == self._scale_timer:
            self._update_scale_animation()
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        if not self._is_hovered:
            self._is_hovered = True
            if not self._is_pressed:
                self._start_animation(self._hover_bg_color)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self._is_hovered:
            self._is_hovered = False
            if not self._is_pressed:
                self._start_animation(self._normal_bg_color)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if not self._is_pressed:
            self._is_pressed = True
            self._start_animation(self._pressed_bg_color)
            
            # 开始缩放动画（缩小）
            self._start_scale_animation(self._pressed_scale)
            
            # 开始波纹动画
            self._start_ripple_animation(event.pos())
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if self._is_pressed:
            self._is_pressed = False
            
            # 恢复缩放
            self._start_scale_animation(self._normal_scale)
            
            if self._is_hovered:
                self._start_animation(self._hover_bg_color)
            else:
                self._start_animation(self._normal_bg_color)
        super().mouseReleaseEvent(event)
    
    def resizeEvent(self, event):
        """按钮大小改变时需要更新缓存"""
        self._needs_update = True
        super().resizeEvent(event)
    
    def changeEvent(self, event):
        """状态改变事件"""
        if event.type() == event.EnabledChange:
            # 禁用状态改变
            self._needs_update = True
            self.update()
        super().changeEvent(event)
    
    # ==================== 公共方法 ====================
    
    def set_style(self, style: str):
        """
        设置按钮样式
        
        Args:
            style: 按钮样式 (primary, secondary, text)
        """
        if style not in [self.STYLE_PRIMARY, self.STYLE_SECONDARY, self.STYLE_TEXT]:
            logger.warning(f"无效的按钮样式: {style}")
            return
        
        self.button_style = style
        self._update_colors()
        self._setup_ui()
        logger.debug(f"按钮样式已更新: {style}")
    
    def get_style(self) -> str:
        """获取当前按钮样式"""
        return self.button_style
    
    def set_blur_radius(self, radius: int):
        """设置模糊半径"""
        self._blur_radius = max(5, min(40, radius))
        self._needs_update = True
        self.update()
    
    def set_transparency(self, transparency: float):
        """设置透明度"""
        self._transparency = max(0.6, min(0.95, transparency))
        self._needs_update = True
        self.update()
    
    def set_border_radius(self, radius: int):
        """设置圆角半径"""
        self._border_radius = max(8, min(20, radius))
        self._needs_update = True
        self.update()
