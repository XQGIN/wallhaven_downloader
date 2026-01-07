# -*- coding: utf-8 -*-
"""
高级视觉效果模块
提供更丰富的视觉效果，如粒子系统、光晕效果等
"""

import math
import random
from typing import List, Tuple
from PyQt5.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QPainterPath

try:
    from core.theme_manager import get_theme_manager
    from utils.logger import get_logger
except ImportError:
    from ..core.theme_manager import get_theme_manager
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class Particle:
    """粒子类"""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, life: float, color: QColor):
        self.x = x
        self.y = y
        self.vx = vx  # x方向速度
        self.vy = vy  # y方向速度
        self.life = life  # 生命周期
        self.max_life = life
        self.color = color
        self.size = random.uniform(2, 6)
    
    def update(self, dt: float):
        """更新粒子状态"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        
        # 重力效果
        self.vy += 50 * dt
        
        # 空气阻力
        self.vx *= 0.99
        self.vy *= 0.99
    
    def is_alive(self) -> bool:
        """检查粒子是否存活"""
        return self.life > 0
    
    def get_alpha(self) -> float:
        """获取透明度（基于生命周期）"""
        return self.life / self.max_life


class ParticleSystem(QWidget):
    """
    粒子系统
    用于创建动态的视觉效果，如下载完成时的庆祝效果
    """
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.theme_manager = get_theme_manager()
        
        # 粒子列表
        self.particles: List[Particle] = []
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_particles)
        self.update_timer.setInterval(16)  # 60 FPS
        
        # 发射器参数
        self.emitter_x = 0
        self.emitter_y = 0
        self.emission_rate = 50  # 每秒发射粒子数
        self.last_emission = 0
        
        logger.debug("ParticleSystem 初始化完成")
    
    def start_celebration(self, center_x: int, center_y: int, duration: int = 3000):
        """
        开始庆祝效果
        
        Args:
            center_x: 发射中心X坐标
            center_y: 发射中心Y坐标
            duration: 持续时间（毫秒）
        """
        self.emitter_x = center_x
        self.emitter_y = center_y
        
        # 立即发射一批粒子
        self._emit_burst(30)
        
        # 开始更新
        self.update_timer.start()
        
        # 设置停止定时器
        QTimer.singleShot(duration, self.stop)
        
        self.show()
        self.raise_()
        
        logger.info(f"开始庆祝粒子效果: 中心({center_x}, {center_y}), 持续{duration}ms")
    
    def stop(self):
        """停止粒子系统"""
        self.update_timer.stop()
        self.particles.clear()
        self.hide()
        
        logger.debug("粒子系统已停止")
    
    def _emit_burst(self, count: int):
        """发射一批粒子"""
        colors = [
            self.theme_manager.get_color("success"),
            self.theme_manager.get_color("primary"),
            self.theme_manager.get_color("warning"),
            QColor(255, 215, 0),  # 金色
            QColor(255, 105, 180),  # 粉色
        ]
        
        for _ in range(count):
            # 随机方向和速度
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 300)
            
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(50, 150)  # 向上偏移
            
            # 随机生命周期和颜色
            life = random.uniform(1.0, 3.0)
            color = random.choice(colors)
            
            particle = Particle(
                self.emitter_x, self.emitter_y,
                vx, vy, life, color
            )
            
            self.particles.append(particle)
    
    def _update_particles(self):
        """更新所有粒子"""
        dt = 0.016  # 假设60FPS
        
        # 更新现有粒子
        alive_particles = []
        for particle in self.particles:
            particle.update(dt)
            if particle.is_alive() and self._is_particle_in_bounds(particle):
                alive_particles.append(particle)
        
        self.particles = alive_particles
        
        # 如果没有粒子了，停止更新
        if not self.particles:
            self.stop()
        
        self.update()
    
    def _is_particle_in_bounds(self, particle: Particle) -> bool:
        """检查粒子是否在边界内"""
        margin = 50
        return (-margin <= particle.x <= self.width() + margin and
                -margin <= particle.y <= self.height() + margin)
    
    def paintEvent(self, event):
        """绘制粒子"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for particle in self.particles:
            # 设置颜色和透明度
            color = QColor(particle.color)
            color.setAlphaF(particle.get_alpha())
            
            # 创建径向渐变
            gradient = QRadialGradient(particle.x, particle.y, particle.size)
            gradient.setColorAt(0, color)
            gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            
            # 绘制粒子
            painter.drawEllipse(
                QPointF(particle.x, particle.y),
                particle.size, particle.size
            )


class GlowEffect(QWidget):
    """
    光晕效果组件
    为重要元素添加发光效果
    """
    
    def __init__(self, target_widget: QWidget, glow_color: QColor = None):
        super().__init__(target_widget.parent())
        
        self.target_widget = target_widget
        self.theme_manager = get_theme_manager()
        
        # 光晕颜色
        self.glow_color = glow_color or self.theme_manager.get_color("primary")
        
        # 光晕参数
        self.glow_radius = 20
        self.glow_intensity = 0.8
        self.pulse_enabled = False
        
        # 脉冲动画
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_phase = 0
        
        # 设置属性
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 跟踪目标组件位置
        self._update_position()
        
        logger.debug(f"GlowEffect 创建: 目标={target_widget.__class__.__name__}")
    
    def set_glow_color(self, color: QColor):
        """设置光晕颜色"""
        self.glow_color = color
        self.update()
    
    def set_glow_radius(self, radius: int):
        """设置光晕半径"""
        self.glow_radius = radius
        self._update_position()
        self.update()
    
    def set_pulse_enabled(self, enabled: bool):
        """启用/禁用脉冲效果"""
        self.pulse_enabled = enabled
        if enabled:
            self.pulse_timer.start(50)  # 20 FPS
        else:
            self.pulse_timer.stop()
    
    def _update_position(self):
        """更新光晕位置和大小"""
        if not self.target_widget:
            return
        
        # 计算光晕区域（比目标组件大一圈）
        target_rect = self.target_widget.geometry()
        margin = self.glow_radius
        
        self.setGeometry(
            target_rect.x() - margin,
            target_rect.y() - margin,
            target_rect.width() + margin * 2,
            target_rect.height() + margin * 2
        )
    
    def _update_pulse(self):
        """更新脉冲动画"""
        self.pulse_phase += 0.1
        if self.pulse_phase >= 2 * math.pi:
            self.pulse_phase = 0
        
        self.update()
    
    def paintEvent(self, event):
        """绘制光晕效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.target_widget:
            return
        
        # 计算当前强度（考虑脉冲）
        current_intensity = self.glow_intensity
        if self.pulse_enabled:
            pulse_factor = (math.sin(self.pulse_phase) + 1) / 2  # 0-1
            current_intensity *= (0.5 + 0.5 * pulse_factor)  # 0.5-1.0
        
        # 创建光晕颜色
        glow_color = QColor(self.glow_color)
        glow_color.setAlphaF(current_intensity)
        
        # 目标区域（相对于光晕组件）
        target_rect = QRect(
            self.glow_radius,
            self.glow_radius,
            self.target_widget.width(),
            self.target_widget.height()
        )
        
        # 创建多层光晕效果
        for i in range(5):
            layer_radius = self.glow_radius * (1 - i * 0.2)
            layer_alpha = current_intensity * (0.8 - i * 0.15)
            
            if layer_radius <= 0 or layer_alpha <= 0:
                continue
            
            # 创建径向渐变
            gradient = QRadialGradient(target_rect.center(), layer_radius)
            
            inner_color = QColor(glow_color)
            inner_color.setAlphaF(layer_alpha)
            outer_color = QColor(glow_color)
            outer_color.setAlphaF(0)
            
            gradient.setColorAt(0.7, inner_color)
            gradient.setColorAt(1.0, outer_color)
            
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            
            # 绘制光晕
            painter.drawRoundedRect(
                target_rect.adjusted(-layer_radius, -layer_radius, layer_radius, layer_radius),
                layer_radius, layer_radius
            )