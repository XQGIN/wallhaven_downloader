# -*- coding: utf-8 -*-
"""
美化增强管理器
集成所有新的美化功能，提供统一的美化接口
"""

from typing import Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QProgressBar
from PyQt5.QtGui import QColor

try:
    from utils.logger import get_logger
    from core.theme_manager import get_theme_manager
    from ui.micro_interactions import RippleEffect, EnhancedButton, LoadingSpinner
    from ui.advanced_effects import ParticleSystem, GlowEffect
    from ui.modern_progress import ModernProgressBar, CircularProgressBar
    from ui.smart_layout import ResponsiveGridLayout, FlexLayout
except ImportError:
    from ..utils.logger import get_logger
    from ..core.theme_manager import get_theme_manager
    from .micro_interactions import RippleEffect, EnhancedButton, LoadingSpinner
    from .advanced_effects import ParticleSystem, GlowEffect
    from .modern_progress import ModernProgressBar, CircularProgressBar
    from .smart_layout import ResponsiveGridLayout, FlexLayout

logger = get_logger(__name__)


class BeautyEnhancementManager(QObject):
    """
    美化增强管理器
    
    统一管理所有美化功能：
    - 微交互效果（波纹、悬停动画）
    - 高级视觉效果（粒子系统、光晕）
    - 现代化进度指示器
    - 智能布局系统
    """
    
    # 信号
    enhancement_applied = pyqtSignal(str)  # 美化应用完成信号
    celebration_triggered = pyqtSignal()   # 庆祝效果触发信号
    
    def __init__(self, main_window: QMainWindow):
        """
        初始化美化增强管理器
        
        Args:
            main_window: 主窗口实例
        """
        super().__init__()
        self.main_window = main_window
        self.theme_manager = get_theme_manager()
        
        # 效果组件实例
        self.particle_system: Optional[ParticleSystem] = None
        self.glow_effects: Dict[QWidget, GlowEffect] = {}
        self.loading_spinners: Dict[str, LoadingSpinner] = {}
        
        # 增强的组件映射
        self.enhanced_buttons: Dict[QPushButton, EnhancedButton] = {}
        self.enhanced_progress_bars: Dict[QProgressBar, ModernProgressBar] = {}
        
        # 初始化状态
        self._is_initialized = False
        
        logger.info("BeautyEnhancementManager 创建完成")
    
    def initialize(self) -> bool:
        """
        初始化所有美化功能
        
        Returns:
            bool: 初始化是否成功
        """
        if self._is_initialized:
            logger.warning("BeautyEnhancementManager 已经初始化")
            return True
        
        try:
            logger.info("开始初始化美化增强功能...")
            
            # 1. 初始化粒子系统
            self._init_particle_system()
            
            # 2. 扫描并增强现有组件
            self._enhance_existing_components()
            
            # 3. 连接主题变更信号
            self.theme_manager.theme_changed.connect(self._on_theme_changed)
            
            self._is_initialized = True
            self.enhancement_applied.emit("all")
            
            logger.info("美化增强功能初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"美化增强功能初始化失败: {e}")
            return False
    
    def _init_particle_system(self):
        """初始化粒子系统"""
        self.particle_system = ParticleSystem(self.main_window)
        self.particle_system.hide()
        logger.debug("粒子系统初始化完成")
    
    def _enhance_existing_components(self):
        """扫描并增强现有组件"""
        # 增强所有按钮
        self._enhance_buttons()
        
        # 增强所有进度条
        self._enhance_progress_bars()
        
        logger.debug("现有组件增强完成")
    
    def _enhance_buttons(self):
        """增强所有按钮组件"""
        buttons = self.main_window.findChildren(QPushButton)
        
        for button in buttons:
            if button not in self.enhanced_buttons:
                # 为按钮添加波纹效果
                ripple = RippleEffect(button)
                
                # 保存原始的鼠标按下事件
                original_press = button.mousePressEvent
                
                def create_enhanced_press(btn, ripple_effect):
                    def enhanced_press(event):
                        # 触发波纹效果
                        ripple_effect.resize(btn.size())
                        ripple_effect.start_ripple(event.pos())
                        # 调用原始事件
                        original_press(event)
                    return enhanced_press
                
                # 替换鼠标按下事件
                button.mousePressEvent = create_enhanced_press(button, ripple)
                
                logger.debug(f"按钮增强完成: {button.text() or button.objectName()}")
    
    def _enhance_progress_bars(self):
        """增强所有进度条组件"""
        progress_bars = self.main_window.findChildren(QProgressBar)
        
        for progress_bar in progress_bars:
            if progress_bar not in self.enhanced_progress_bars:
                # 创建现代化进度条替代
                modern_progress = ModernProgressBar(progress_bar.parent())
                modern_progress.setGeometry(progress_bar.geometry())
                modern_progress.setRange(progress_bar.minimum(), progress_bar.maximum())
                modern_progress.value = progress_bar.value()
                
                # 连接值变更信号
                def create_value_sync(original, modern):
                    def sync_value():
                        modern.value = original.value()
                    return sync_value
                
                progress_bar.valueChanged.connect(create_value_sync(progress_bar, modern_progress))
                
                # 隐藏原始进度条，显示现代化版本
                progress_bar.hide()
                modern_progress.show()
                
                self.enhanced_progress_bars[progress_bar] = modern_progress
                
                logger.debug(f"进度条增强完成: {progress_bar.objectName()}")
    
    def add_glow_effect(self, widget: QWidget, color: QColor = None, pulse: bool = False) -> GlowEffect:
        """
        为组件添加光晕效果
        
        Args:
            widget: 目标组件
            color: 光晕颜色，默认使用主题主色
            pulse: 是否启用脉冲效果
            
        Returns:
            GlowEffect: 光晕效果实例
        """
        if widget in self.glow_effects:
            # 如果已存在，更新参数
            glow = self.glow_effects[widget]
            if color:
                glow.set_glow_color(color)
            glow.set_pulse_enabled(pulse)
            return glow
        
        # 创建新的光晕效果
        glow_color = color or self.theme_manager.get_color("primary")
        glow = GlowEffect(widget, glow_color)
        glow.set_pulse_enabled(pulse)
        
        self.glow_effects[widget] = glow
        glow.show()
        
        logger.debug(f"光晕效果已添加: {widget.__class__.__name__}, 脉冲={pulse}")
        return glow
    
    def remove_glow_effect(self, widget: QWidget):
        """移除组件的光晕效果"""
        if widget in self.glow_effects:
            glow = self.glow_effects.pop(widget)
            glow.hide()
            glow.deleteLater()
            logger.debug(f"光晕效果已移除: {widget.__class__.__name__}")
    
    def create_loading_spinner(self, name: str, size: int = 32, parent: QWidget = None) -> LoadingSpinner:
        """
        创建加载动画
        
        Args:
            name: 加载动画名称（用于管理）
            size: 动画大小
            parent: 父组件
            
        Returns:
            LoadingSpinner: 加载动画实例
        """
        if name in self.loading_spinners:
            return self.loading_spinners[name]
        
        spinner = LoadingSpinner(size, parent or self.main_window)
        self.loading_spinners[name] = spinner
        
        logger.debug(f"加载动画已创建: {name}, 大小={size}")
        return spinner
    
    def show_loading(self, name: str):
        """显示指定的加载动画"""
        if name in self.loading_spinners:
            self.loading_spinners[name].start()
            logger.debug(f"加载动画已启动: {name}")
    
    def hide_loading(self, name: str):
        """隐藏指定的加载动画"""
        if name in self.loading_spinners:
            self.loading_spinners[name].stop()
            logger.debug(f"加载动画已停止: {name}")
    
    def trigger_celebration(self, center_x: int = None, center_y: int = None, duration: int = 3000):
        """
        触发庆祝粒子效果
        
        Args:
            center_x: 发射中心X坐标，默认为窗口中心
            center_y: 发射中心Y坐标，默认为窗口中心
            duration: 持续时间（毫秒）
        """
        if not self.particle_system:
            logger.warning("粒子系统未初始化，无法触发庆祝效果")
            return
        
        # 使用窗口中心作为默认位置
        if center_x is None:
            center_x = self.main_window.width() // 2
        if center_y is None:
            center_y = self.main_window.height() // 2
        
        # 调整粒子系统大小和位置
        self.particle_system.resize(self.main_window.size())
        self.particle_system.move(0, 0)
        
        # 开始庆祝效果
        self.particle_system.start_celebration(center_x, center_y, duration)
        self.celebration_triggered.emit()
        
        logger.info(f"庆祝粒子效果已触发: 中心({center_x}, {center_y}), 持续{duration}ms")
    
    def create_enhanced_button(self, text: str, parent: QWidget = None) -> EnhancedButton:
        """
        创建增强按钮
        
        Args:
            text: 按钮文本
            parent: 父组件
            
        Returns:
            EnhancedButton: 增强按钮实例
        """
        button = EnhancedButton(text, parent)
        logger.debug(f"增强按钮已创建: {text}")
        return button
    
    def create_modern_progress_bar(self, parent: QWidget = None) -> ModernProgressBar:
        """
        创建现代化进度条
        
        Args:
            parent: 父组件
            
        Returns:
            ModernProgressBar: 现代化进度条实例
        """
        progress_bar = ModernProgressBar(parent)
        logger.debug("现代化进度条已创建")
        return progress_bar
    
    def create_circular_progress_bar(self, size: int = 120, parent: QWidget = None) -> CircularProgressBar:
        """
        创建圆形进度条
        
        Args:
            size: 进度条大小
            parent: 父组件
            
        Returns:
            CircularProgressBar: 圆形进度条实例
        """
        progress_bar = CircularProgressBar(size, parent)
        logger.debug(f"圆形进度条已创建: 大小={size}")
        return progress_bar
    
    def create_responsive_grid_layout(self, parent: QWidget = None) -> ResponsiveGridLayout:
        """
        创建响应式网格布局
        
        Args:
            parent: 父组件
            
        Returns:
            ResponsiveGridLayout: 响应式网格布局实例
        """
        layout = ResponsiveGridLayout(parent)
        logger.debug("响应式网格布局已创建")
        return layout
    
    def create_flex_layout(self, direction=None, parent: QWidget = None) -> FlexLayout:
        """
        创建弹性布局
        
        Args:
            direction: 布局方向
            parent: 父组件
            
        Returns:
            FlexLayout: 弹性布局实例
        """
        from PyQt5.QtCore import Qt
        direction = direction or Qt.Horizontal
        layout = FlexLayout(direction, parent)
        logger.debug(f"弹性布局已创建: 方向={'水平' if direction == Qt.Horizontal else '垂直'}")
        return layout
    
    def _on_theme_changed(self, theme_name: str):
        """主题变更处理"""
        logger.debug(f"主题已变更为: {theme_name}，更新美化效果")
        
        # 更新光晕效果颜色
        primary_color = self.theme_manager.get_color("primary")
        for widget, glow in self.glow_effects.items():
            glow.set_glow_color(primary_color)
        
        # 触发组件重绘
        for spinner in self.loading_spinners.values():
            spinner.update()
        
        for progress_bar in self.enhanced_progress_bars.values():
            progress_bar.update()
    
    def cleanup(self):
        """清理资源"""
        logger.info("开始清理美化增强资源...")
        
        # 停止粒子系统
        if self.particle_system:
            self.particle_system.stop()
            self.particle_system.deleteLater()
        
        # 清理光晕效果
        for glow in self.glow_effects.values():
            glow.hide()
            glow.deleteLater()
        self.glow_effects.clear()
        
        # 清理加载动画
        for spinner in self.loading_spinners.values():
            spinner.stop()
            spinner.deleteLater()
        self.loading_spinners.clear()
        
        # 清理增强组件
        self.enhanced_buttons.clear()
        self.enhanced_progress_bars.clear()
        
        logger.info("美化增强资源清理完成")


# 全局单例实例
_beauty_manager_instance = None


def get_beauty_enhancement_manager(main_window: QMainWindow = None) -> BeautyEnhancementManager:
    """
    获取美化增强管理器单例实例
    
    Args:
        main_window: 主窗口实例（仅在首次调用时需要）
        
    Returns:
        BeautyEnhancementManager: 美化增强管理器实例
    """
    global _beauty_manager_instance
    
    if _beauty_manager_instance is None:
        if main_window is None:
            raise ValueError("首次调用时必须提供 main_window 参数")
        _beauty_manager_instance = BeautyEnhancementManager(main_window)
    
    return _beauty_manager_instance