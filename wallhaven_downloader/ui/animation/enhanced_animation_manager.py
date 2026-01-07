# -*- coding: utf-8 -*-
"""
增强动画管理器
扩展现有 AnimationManager，集成 MicroAnimationController
"""

from typing import Optional, Callable, List
from PyQt5.QtCore import QObject, QPropertyAnimation, QEasingCurve, QPoint, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor

try:
    from ui.animation_manager import AnimationManager
    from ui.animation.micro_animation_controller import MicroAnimationController
    from utils.logger import get_logger
    from utils.system_accessibility_detector import get_system_accessibility_detector
except ImportError:
    from ..animation_manager import AnimationManager
    from .micro_animation_controller import MicroAnimationController
    from ...utils.logger import get_logger
    from ...utils.system_accessibility_detector import get_system_accessibility_detector

logger = get_logger(__name__)


class EnhancedAnimationManager(AnimationManager):
    """
    增强动画管理器
    
    扩展现有 AnimationManager，添加：
    - 微动画控制器集成
    - 性能监控
    - 动画复杂度降级
    - 更精细的动画控制
    """
    
    # 信号
    performance_mode_changed = pyqtSignal(bool)  # 性能模式变化
    animation_state_changed = pyqtSignal(bool)  # 动画启用状态变化
    
    # 性能阈值
    FPS_THRESHOLD_LOW = 30  # 低性能阈值
    FPS_THRESHOLD_NORMAL = 50  # 正常性能阈值
    MAX_CONCURRENT_ANIMATIONS = 5  # 最大并发动画数量（默认）
    
    # GPU 加速属性列表
    GPU_ACCELERATED_PROPERTIES = [
        b'opacity',  # 透明度
        b'pos',  # 位置
        b'geometry',  # 几何形状
        b'windowOpacity',  # 窗口透明度
    ]
    
    def __init__(self):
        """初始化增强动画管理器"""
        super().__init__()
        
        # 集成微动画控制器
        self.micro_controller = MicroAnimationController()
        
        # 系统辅助功能检测器
        self.accessibility_detector = get_system_accessibility_detector()
        
        # 性能监控
        self.fps_samples: List[float] = []  # FPS 样本
        self.max_fps_samples = 30  # 最大样本数
        self.performance_check_timer = QTimer()
        self.performance_check_timer.timeout.connect(self._check_performance)
        self.performance_check_interval = 1000  # 性能检查间隔（毫秒）
        
        # 动画复杂度级别
        self.complexity_level = "high"  # high, medium, low
        
        # 自动降级标志
        self.auto_degradation_enabled = True
        
        # 并发动画控制
        self.max_concurrent_animations = self.MAX_CONCURRENT_ANIMATIONS
        self.active_animations_count = 0
        self.queued_animations = []  # 队列中的动画
        
        # GPU 加速优化
        self.gpu_acceleration_enabled = True
        self.prefer_gpu_properties = True
        
        # 是否遵循系统辅助功能设置（默认不遵循，由应用设置控制）
        self.respect_system_settings = False
        
        # 连接系统辅助功能变化信号
        self.accessibility_detector.reduce_motion_changed.connect(self._on_reduce_motion_changed)
        
        # 开始监控系统辅助功能设置（但不立即应用）
        self.accessibility_detector.start_monitoring()
        
        logger.info("EnhancedAnimationManager 初始化完成")
    
    # ==================== 微动画方法 ====================
    
    def create_hover_animation(
        self,
        widget: QWidget,
        property_name: str = "scale",
        start_value: float = 1.0,
        end_value: float = 1.05,
        duration: int = None
    ) -> Optional[QPropertyAnimation]:
        """
        创建悬停动画
        
        Args:
            widget: 目标组件
            property_name: 属性名称
            start_value: 起始值
            end_value: 结束值
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation 对象
        """
        if not self.animations_enabled:
            return None
        
        return self.micro_controller.create_hover_animation(
            widget, property_name, start_value, end_value, duration
        )
    
    def create_press_animation(
        self,
        widget: QWidget,
        scale_factor: float = 0.95,
        duration: int = None
    ) -> Optional[QPropertyAnimation]:
        """
        创建按下动画
        
        Args:
            widget: 目标组件
            scale_factor: 缩放因子
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation 对象
        """
        if not self.animations_enabled:
            return None
        
        return self.micro_controller.create_press_animation(
            widget, scale_factor, duration
        )
    
    def create_micro_fade_animation(
        self,
        widget: QWidget,
        start_opacity: float = 0.0,
        end_opacity: float = 1.0,
        duration: int = None
    ) -> Optional[QPropertyAnimation]:
        """
        创建微动画淡入淡出
        
        Args:
            widget: 目标组件
            start_opacity: 起始透明度
            end_opacity: 结束透明度
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation 对象
        """
        if not self.animations_enabled:
            return None
        
        return self.micro_controller.create_fade_animation(
            widget, start_opacity, end_opacity, duration
        )
    
    def create_micro_slide_animation(
        self,
        widget: QWidget,
        start_pos: QPoint,
        end_pos: QPoint,
        duration: int = None
    ) -> Optional[QPropertyAnimation]:
        """
        创建微动画滑动
        
        Args:
            widget: 目标组件
            start_pos: 起始位置
            end_pos: 结束位置
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation 对象
        """
        if not self.animations_enabled:
            return None
        
        return self.micro_controller.create_slide_animation(
            widget, start_pos, end_pos, duration
        )
    
    def create_micro_ripple_effect(
        self,
        widget: QWidget,
        center: QPoint,
        max_radius: int = None,
        color: QColor = None,
        duration: int = None
    ):
        """
        创建微动画涟漪效果
        
        Args:
            widget: 目标组件
            center: 涟漪中心点
            max_radius: 最大半径
            color: 涟漪颜色
            duration: 动画时长（毫秒）
        """
        if not self.animations_enabled:
            return
        
        self.micro_controller.create_ripple_effect(
            widget, center, max_radius, color, duration
        )
    
    # ==================== 性能监控方法 ====================
    
    def start_performance_monitoring(self):
        """启动性能监控"""
        if not self.performance_check_timer.isActive():
            self.performance_check_timer.start(self.performance_check_interval)
            logger.info("性能监控已启动")
    
    def stop_performance_monitoring(self):
        """停止性能监控"""
        if self.performance_check_timer.isActive():
            self.performance_check_timer.stop()
            logger.info("性能监控已停止")
    
    def record_fps(self, fps: float):
        """
        记录 FPS 样本
        
        Args:
            fps: 当前 FPS 值
        """
        self.fps_samples.append(fps)
        
        # 限制样本数量
        if len(self.fps_samples) > self.max_fps_samples:
            self.fps_samples.pop(0)
    
    def get_average_fps(self) -> float:
        """
        获取平均 FPS
        
        Returns:
            平均 FPS 值
        """
        if not self.fps_samples:
            return 60.0  # 默认值
        
        return sum(self.fps_samples) / len(self.fps_samples)
    
    def _check_performance(self):
        """检查性能并自动调整"""
        if not self.auto_degradation_enabled:
            return
        
        avg_fps = self.get_average_fps()
        
        # 根据 FPS 自动调整复杂度
        if avg_fps < self.FPS_THRESHOLD_LOW:
            # 性能很低，降级到最低复杂度
            if self.complexity_level != "low":
                self.set_complexity_level("low")
                logger.warning(f"性能较低 (FPS: {avg_fps:.1f})，降级到低复杂度模式")
        elif avg_fps < self.FPS_THRESHOLD_NORMAL:
            # 性能一般，使用中等复杂度
            if self.complexity_level != "medium":
                self.set_complexity_level("medium")
                logger.info(f"性能一般 (FPS: {avg_fps:.1f})，切换到中等复杂度模式")
        else:
            # 性能良好，使用高复杂度
            if self.complexity_level != "high":
                self.set_complexity_level("high")
                logger.info(f"性能良好 (FPS: {avg_fps:.1f})，切换到高复杂度模式")
    
    # ==================== 复杂度控制方法 ====================
    
    def set_complexity_level(self, level: str):
        """
        设置动画复杂度级别
        
        Args:
            level: 复杂度级别 ('high', 'medium', 'low')
        """
        if level not in ["high", "medium", "low"]:
            logger.warning(f"无效的复杂度级别: {level}")
            return
        
        old_level = self.complexity_level
        self.complexity_level = level
        
        # 根据复杂度调整参数
        if level == "low":
            # 低复杂度：减少并发动画，缩短时长
            self.DURATION_FAST = 100
            self.DURATION_NORMAL = 150
            self.DURATION_SLOW = 200
            self.enable_performance_mode()
            self.set_max_concurrent_animations(2)
        elif level == "medium":
            # 中等复杂度：适中的并发和时长
            self.DURATION_FAST = 120
            self.DURATION_NORMAL = 180
            self.DURATION_SLOW = 250
            self.disable_performance_mode()
            self.set_max_concurrent_animations(3)
        else:  # high
            # 高复杂度：完整的动画效果
            self.DURATION_FAST = 150
            self.DURATION_NORMAL = 200
            self.DURATION_SLOW = 300
            self.disable_performance_mode()
            self.set_max_concurrent_animations(5)
        
        logger.info(f"动画复杂度从 {old_level} 切换到 {level}")
    
    def get_complexity_level(self) -> str:
        """
        获取当前复杂度级别
        
        Returns:
            复杂度级别字符串
        """
        return self.complexity_level
    
    def enable_auto_degradation(self):
        """启用自动降级"""
        self.auto_degradation_enabled = True
        self.start_performance_monitoring()
        logger.info("自动降级已启用")
    
    def disable_auto_degradation(self):
        """禁用自动降级"""
        self.auto_degradation_enabled = False
        self.stop_performance_monitoring()
        logger.info("自动降级已禁用")
    
    # ==================== 重写父类方法 ====================
    
    def enable_animations(self):
        """启用动画"""
        super().enable_animations()
        self.animation_state_changed.emit(True)
    
    def disable_animations(self):
        """禁用动画"""
        super().disable_animations()
        self.animation_state_changed.emit(False)
    
    def enable_performance_mode(self):
        """启用性能模式"""
        super().enable_performance_mode()
        self.performance_mode_changed.emit(True)
    
    def disable_performance_mode(self):
        """禁用性能模式"""
        super().disable_performance_mode()
        self.performance_mode_changed.emit(False)
    
    # ==================== 批量动画方法 ====================
    
    def create_sequential_animations(
        self,
        widgets: List[QWidget],
        animation_type: str = 'fade',
        delay: int = 50,
        duration: int = None,
        callback: Optional[Callable] = None
    ):
        """
        创建顺序动画（一个接一个）
        
        Args:
            widgets: 组件列表
            animation_type: 动画类型
            delay: 每项之间的延迟（毫秒）
            duration: 每个动画的时长（毫秒）
            callback: 所有动画完成后的回调函数
        """
        # 使用父类的交错动画方法
        self.create_staggered_animation(
            widgets, animation_type, delay, duration, callback
        )
    
    def create_parallel_animations(
        self,
        widgets: List[QWidget],
        animation_type: str = 'fade',
        duration: int = None,
        callback: Optional[Callable] = None
    ):
        """
        创建并行动画（同时执行）
        
        Args:
            widgets: 组件列表
            animation_type: 动画类型
            duration: 每个动画的时长（毫秒）
            callback: 所有动画完成后的回调函数
        """
        if not self.animations_enabled or not widgets:
            if callback:
                callback()
            return
        
        total_animations = len(widgets)
        completed_count = [0]
        
        def on_single_animation_finished():
            completed_count[0] += 1
            if completed_count[0] >= total_animations and callback:
                callback()
        
        # 同时启动所有动画
        for widget in widgets:
            if animation_type == 'fade':
                self.create_fade_animation(
                    widget,
                    start_opacity=0.0,
                    end_opacity=1.0,
                    duration=duration,
                    callback=on_single_animation_finished
                )
            elif animation_type == 'slide':
                self.create_slide_animation(
                    widget,
                    direction='up',
                    distance=20,
                    duration=duration,
                    callback=on_single_animation_finished
                )
        
        logger.debug(f"创建并行动画: {len(widgets)} 个组件")
    
    # ==================== 工具方法 ====================
    
    def get_performance_stats(self) -> dict:
        """
        获取性能统计信息
        
        Returns:
            包含性能统计的字典
        """
        return {
            "average_fps": self.get_average_fps(),
            "active_animations": self.get_active_animation_count(),
            "queued_animations": len(self.animation_queue),
            "complexity_level": self.complexity_level,
            "performance_mode": self.performance_mode,
            "animations_enabled": self.animations_enabled,
            "auto_degradation": self.auto_degradation_enabled,
            "max_concurrent_animations": self.max_concurrent_animations,
            "gpu_acceleration_enabled": self.gpu_acceleration_enabled
        }
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self.fps_samples.clear()
        logger.debug("性能统计已重置")
    
    # ==================== 并发动画控制方法 ====================
    
    def set_max_concurrent_animations(self, max_count: int):
        """
        设置最大并发动画数量
        
        Args:
            max_count: 最大并发动画数量
            
        需求：14.5
        """
        self.max_concurrent_animations = max(1, max_count)
        logger.info(f"最大并发动画数量设置为: {self.max_concurrent_animations}")
    
    def can_start_animation(self) -> bool:
        """
        检查是否可以启动新动画
        
        Returns:
            是否可以启动新动画
        """
        return self.active_animations_count < self.max_concurrent_animations
    
    def register_animation_start(self):
        """注册动画启动"""
        self.active_animations_count += 1
    
    def register_animation_end(self):
        """注册动画结束"""
        self.active_animations_count = max(0, self.active_animations_count - 1)
        
        # 如果有队列中的动画，启动下一个
        if self.queued_animations and self.can_start_animation():
            self._start_queued_animation()
    
    def _start_queued_animation(self):
        """启动队列中的下一个动画"""
        if not self.queued_animations:
            return
        
        animation_func, args, kwargs = self.queued_animations.pop(0)
        try:
            animation_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"启动队列动画失败: {e}")
    
    def queue_animation(self, animation_func, *args, **kwargs):
        """
        将动画加入队列
        
        Args:
            animation_func: 动画创建函数
            *args: 位置参数
            **kwargs: 关键字参数
        """
        self.queued_animations.append((animation_func, args, kwargs))
        logger.debug(f"动画已加入队列，当前队列长度: {len(self.queued_animations)}")
    
    def clear_animation_queue(self):
        """清空动画队列"""
        self.queued_animations.clear()
        logger.debug("动画队列已清空")
    
    # ==================== GPU 加速优化方法 ====================
    
    def is_gpu_accelerated_property(self, property_name: bytes) -> bool:
        """
        检查属性是否支持 GPU 加速
        
        Args:
            property_name: 属性名称（字节串）
            
        Returns:
            是否支持 GPU 加速
        """
        return property_name in self.GPU_ACCELERATED_PROPERTIES
    
    def create_optimized_animation(
        self,
        widget: QWidget,
        property_name: str,
        start_value,
        end_value,
        duration: int = None,
        easing: QEasingCurve.Type = None,
        callback: Optional[Callable] = None
    ) -> Optional[QPropertyAnimation]:
        """
        创建优化的动画
        
        优先使用 GPU 加速属性，并控制并发数量
        
        Args:
            widget: 目标组件
            property_name: 属性名称
            start_value: 起始值
            end_value: 结束值
            duration: 动画时长（毫秒）
            easing: 缓动曲线
            callback: 完成回调
            
        Returns:
            QPropertyAnimation 对象
            
        需求：14.5
        """
        if not self.animations_enabled:
            if callback:
                callback()
            return None
        
        # 检查是否可以启动新动画
        if not self.can_start_animation():
            # 如果达到并发限制，加入队列
            self.queue_animation(
                self.create_optimized_animation,
                widget, property_name, start_value, end_value,
                duration, easing, callback
            )
            logger.debug(f"动画已加入队列（达到并发限制 {self.max_concurrent_animations}）")
            return None
        
        # 转换属性名为字节串
        property_bytes = property_name.encode('utf-8')
        
        # 检查是否为 GPU 加速属性
        is_gpu_property = self.is_gpu_accelerated_property(property_bytes)
        
        if not is_gpu_property and self.prefer_gpu_properties:
            logger.debug(f"属性 {property_name} 不支持 GPU 加速，建议使用 opacity 或 pos")
        
        # 创建动画
        animation = QPropertyAnimation(widget, property_bytes)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        
        # 设置时长
        if duration is None:
            duration = self.DURATION_NORMAL
        animation.setDuration(duration)
        
        # 设置缓动曲线
        if easing is None:
            easing = QEasingCurve.OutCubic
        animation.setEasingCurve(easing)
        
        # 注册动画启动
        self.register_animation_start()
        
        # 设置完成回调
        def on_finished():
            self.register_animation_end()
            if callback:
                callback()
        
        animation.finished.connect(on_finished)
        
        # 启动动画
        animation.start(QPropertyAnimation.DeleteWhenStopped)
        
        logger.debug(f"创建优化动画: {property_name}, GPU加速={is_gpu_property}, 并发={self.active_animations_count}/{self.max_concurrent_animations}")
        
        return animation
    
    def enable_gpu_acceleration(self):
        """
        启用 GPU 加速优化
        
        需求：14.5
        """
        self.gpu_acceleration_enabled = True
        self.prefer_gpu_properties = True
        logger.info("GPU 加速优化已启用")
    
    def disable_gpu_acceleration(self):
        """禁用 GPU 加速优化"""
        self.gpu_acceleration_enabled = False
        self.prefer_gpu_properties = False
        logger.info("GPU 加速优化已禁用")
    
    def optimize_animation_for_performance(self):
        """
        为性能优化动画设置
        
        执行以下优化：
        1. 限制并发动画数量
        2. 优先使用 GPU 加速属性
        3. 缩短动画时长
        4. 简化缓动曲线
        
        需求：14.5
        """
        # 限制并发动画
        self.set_max_concurrent_animations(3)
        
        # 启用 GPU 加速
        self.enable_gpu_acceleration()
        
        # 缩短动画时长
        self.DURATION_FAST = 100
        self.DURATION_NORMAL = 150
        self.DURATION_SLOW = 200
        
        # 清空队列中的动画
        self.clear_animation_queue()
        
        logger.info("动画性能优化已应用")
    
    def restore_animation_quality(self):
        """
        恢复动画质量设置
        
        恢复到高质量动画配置
        """
        # 恢复并发限制
        self.set_max_concurrent_animations(self.MAX_CONCURRENT_ANIMATIONS)
        
        # 恢复动画时长
        self.DURATION_FAST = 150
        self.DURATION_NORMAL = 200
        self.DURATION_SLOW = 300
        
        logger.info("动画质量设置已恢复")
    
    def set_respect_system_settings(self, respect: bool):
        """
        设置是否遵循系统辅助功能设置
        
        Args:
            respect: True=遵循系统设置，False=使用应用设置
        """
        self.respect_system_settings = respect
        logger.info(f"{'遵循' if respect else '不遵循'}系统辅助功能设置")
        
        # 如果启用遵循且系统启用了减少动画，则禁用动画
        if respect and self.accessibility_detector.is_reduce_motion_enabled():
            self.disable_animations()
            logger.info("系统启用了减少动画，已禁用动画")
    
    def get_respect_system_settings(self) -> bool:
        """
        获取是否遵循系统辅助功能设置
        
        Returns:
            bool: 是否遵循系统设置
        """
        return self.respect_system_settings
    
    def _on_reduce_motion_changed(self, enabled: bool):
        """
        系统减少动画设置变化处理
        
        需求：16.5 - 遵循系统辅助功能设置中的减少动画选项
        
        Args:
            enabled: 是否启用减少动画
        """
        # 仅在遵循系统设置时才应用
        if not self.respect_system_settings:
            logger.debug(f"系统减少动画设置变化 (enabled={enabled})，但应用设置优先，不自动应用")
            return
        
        if enabled:
            # 启用减少动画 - 禁用所有动画
            self.disable_animations()
            logger.info("系统启用了减少动画，已禁用所有动画")
        else:
            # 禁用减少动画 - 恢复动画
            self.enable_animations()
            logger.info("系统禁用了减少动画，已恢复动画")
        
        # 发射信号
        self.animation_state_changed.emit(not enabled)
    
    def should_animate(self) -> bool:
        """
        判断是否应该播放动画
        
        考虑因素：
        - 动画是否启用
        - 系统减少动画设置（仅在遵循系统设置时）
        - 性能模式
        
        Returns:
            bool: 是否应该播放动画
        """
        # 检查动画是否启用
        if not self.animations_enabled:
            return False
        
        # 仅在遵循系统设置时才检查系统减少动画设置
        if self.respect_system_settings and self.accessibility_detector.is_reduce_motion_enabled():
            return False
        
        # 检查性能模式
        if self.performance_mode and self.complexity_level == "low":
            return False
        
        return True
    
    def create_animation_safe(
        self,
        widget: QWidget,
        property_name: bytes,
        start_value,
        end_value,
        duration: int = 300,
        easing: QEasingCurve.Type = QEasingCurve.OutCubic
    ) -> Optional[QPropertyAnimation]:
        """
        安全创建动画（考虑减少动画设置）
        
        如果系统启用了减少动画，则立即应用最终状态而不播放动画
        
        Args:
            widget: 目标组件
            property_name: 属性名称
            start_value: 起始值
            end_value: 结束值
            duration: 动画时长
            easing: 缓动函数
            
        Returns:
            QPropertyAnimation: 动画对象（如果创建）或 None
        """
        if not self.should_animate():
            # 不播放动画，直接应用最终状态
            widget.setProperty(property_name, end_value)
            logger.debug(f"减少动画模式：直接应用最终状态 {property_name}")
            return None
        
        # 创建并返回动画
        animation = QPropertyAnimation(widget, property_name)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setDuration(duration)
        animation.setEasingCurve(easing)
        
        return animation


# 全局单例
_enhanced_animation_manager_instance: Optional[EnhancedAnimationManager] = None


def get_enhanced_animation_manager() -> EnhancedAnimationManager:
    """
    获取增强动画管理器单例
    
    Returns:
        EnhancedAnimationManager 实例
    """
    global _enhanced_animation_manager_instance
    if _enhanced_animation_manager_instance is None:
        _enhanced_animation_manager_instance = EnhancedAnimationManager()
    return _enhanced_animation_manager_instance
