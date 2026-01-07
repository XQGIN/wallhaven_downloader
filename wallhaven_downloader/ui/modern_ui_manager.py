# -*- coding: utf-8 -*-
"""
现代化 UI 管理器
统一管理所有现代化 UI 组件和子系统
"""

from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMainWindow

try:
    from utils.logger import get_logger
    from core.enhanced_theme_manager import get_enhanced_theme_manager, EnhancedThemeManager
    from ui.animation.enhanced_animation_manager import get_enhanced_animation_manager, EnhancedAnimationManager
    from ui.layout_manager import LayoutManager
    from ui.icon_manager import get_icon_manager, IconManager
    from ui.toast_notification import ToastManager
    from ui.typography_system import TypographySystem
    from ui.liquid_glass.liquid_glass_manager import LiquidGlassManager
    from utils.performance_optimizer import PerformanceOptimizer
except ImportError:
    from ..utils.logger import get_logger
    from ..core.enhanced_theme_manager import get_enhanced_theme_manager, EnhancedThemeManager
    from .animation.enhanced_animation_manager import get_enhanced_animation_manager, EnhancedAnimationManager
    from .layout_manager import LayoutManager
    from .icon_manager import get_icon_manager, IconManager
    from .toast_notification import ToastManager
    from .typography_system import TypographySystem
    from .liquid_glass.liquid_glass_manager import LiquidGlassManager
    from ..utils.performance_optimizer import PerformanceOptimizer

logger = get_logger(__name__)


class ModernUIManager(QObject):
    """
    现代化 UI 管理器
    
    作为所有现代化 UI 组件的核心协调器，负责：
    - 初始化所有子管理器（LiquidGlass, EnhancedTheme, EnhancedAnimation, Card, Layout, Icon, Toast, Typography）
    - 协调主题切换
    - 管理组件生命周期
    - 提供统一的访问接口
    
    需求：所有
    """
    
    # 信号
    initialized = pyqtSignal()  # 初始化完成信号
    theme_applied = pyqtSignal(str)  # 主题应用完成信号
    
    def __init__(self, main_window: QMainWindow):
        """
        初始化现代化 UI 管理器
        
        Args:
            main_window: 主窗口实例
        """
        super().__init__()
        self.main_window = main_window
        
        # 子管理器实例
        self.liquid_glass_manager: Optional[LiquidGlassManager] = None
        self.theme_manager: Optional[EnhancedThemeManager] = None
        self.animation_manager: Optional[EnhancedAnimationManager] = None
        self.layout_manager: Optional[LayoutManager] = None
        self.icon_manager: Optional[IconManager] = None
        self.toast_manager: Optional[ToastManager] = None
        self.typography_system: Optional[TypographySystem] = None
        self.performance_optimizer: Optional[PerformanceOptimizer] = None
        
        # 初始化状态
        self._is_initialized = False
        
        logger.info("ModernUIManager 创建完成")
    
    def initialize(self) -> bool:
        """
        初始化所有现代化 UI 组件
        
        按照依赖顺序初始化各个子系统：
        1. EnhancedThemeManager - 增强主题管理（最基础）
        2. LiquidGlassManager - 液态玻璃管理（依赖主题）
        3. EnhancedAnimationManager - 增强动画管理
        4. IconManager - 图标管理
        5. TypographySystem - 排版系统
        6. LayoutManager - 布局管理
        7. ToastManager - 通知管理
        8. PerformanceOptimizer - 性能优化器
        
        Returns:
            bool: 初始化是否成功
        """
        if self._is_initialized:
            logger.warning("ModernUIManager 已经初始化，跳过重复初始化")
            return True
        
        try:
            logger.info("开始初始化 ModernUIManager...")
            
            # 1. 初始化增强主题管理器（单例）
            logger.debug("初始化 EnhancedThemeManager...")
            self.theme_manager = get_enhanced_theme_manager()
            
            # 2. 初始化液态玻璃管理器（如果主窗口已有，则使用现有的）
            logger.debug("初始化 LiquidGlassManager...")
            if hasattr(self.main_window, 'liquid_glass_manager') and self.main_window.liquid_glass_manager:
                self.liquid_glass_manager = self.main_window.liquid_glass_manager
                logger.debug("使用主窗口已有的 LiquidGlassManager")
            else:
                self.liquid_glass_manager = LiquidGlassManager(self.main_window)
                if not self.liquid_glass_manager.initialize():
                    logger.warning("LiquidGlassManager 初始化失败")
            
            # 连接液态玻璃管理器到主题管理器（需求 2.7）
            if self.liquid_glass_manager and self.theme_manager:
                self.liquid_glass_manager.connect_theme_manager(self.theme_manager)
                logger.debug("LiquidGlassManager 已连接到 EnhancedThemeManager")
            
            # 3. 初始化增强动画管理器（单例）
            logger.debug("初始化 EnhancedAnimationManager...")
            self.animation_manager = get_enhanced_animation_manager()
            
            # 从主窗口设置中应用动画配置
            if hasattr(self.main_window, 'settings'):
                enable_animations = self.main_window.settings.get('enable_animations', True)
                performance_mode = self.main_window.settings.get('performance_mode', False)
                gpu_acceleration = self.main_window.settings.get('gpu_acceleration', True)
                
                logger.debug(f"应用动画设置: enable_animations={enable_animations}, "
                           f"performance_mode={performance_mode}, gpu_acceleration={gpu_acceleration}")
                
                # 应用动画启用状态
                if enable_animations:
                    self.animation_manager.enable_animations()
                else:
                    self.animation_manager.disable_animations()
                
                # 应用性能模式
                if performance_mode:
                    self.animation_manager.enable_performance_mode()
                else:
                    self.animation_manager.disable_performance_mode()
                
                # 应用 GPU 加速
                if gpu_acceleration:
                    self.animation_manager.enable_gpu_acceleration()
                else:
                    self.animation_manager.disable_gpu_acceleration()
            
            # 4. 初始化图标管理器（单例）
            logger.debug("初始化 IconManager...")
            self.icon_manager = get_icon_manager()
            
            # 5. 初始化排版系统
            logger.debug("初始化 TypographySystem...")
            self.typography_system = TypographySystem()
            
            # 6. 初始化布局管理器
            logger.debug("初始化 LayoutManager...")
            self.layout_manager = LayoutManager(self.main_window)
            
            # 7. 初始化 Toast 管理器
            logger.debug("初始化 ToastManager...")
            self.toast_manager = ToastManager(self.main_window)
            
            # 8. 初始化性能优化器（需求 14.1-14.6）
            logger.debug("初始化 PerformanceOptimizer...")
            self.performance_optimizer = PerformanceOptimizer(self.main_window)
            
            # 连接性能降级信号到动画管理器和液态玻璃管理器
            self.performance_optimizer.degradation.performance_mode_changed.connect(
                self._on_performance_mode_changed
            )
            
            # 连接主题变化信号
            self.theme_manager.theme_changed.connect(self._on_theme_changed)
            
            # 标记为已初始化
            self._is_initialized = True
            
            logger.info("ModernUIManager 初始化完成")
            self.initialized.emit()
            
            return True
            
        except Exception as e:
            logger.error(f"ModernUIManager 初始化失败: {e}", exc_info=True)
            return False
    
    def apply_modern_theme(self, theme_name: str) -> bool:
        """
        应用现代化主题
        
        协调所有子系统应用新主题：
        1. 更新主题管理器
        2. 刷新卡片样式
        3. 清除图标缓存（以便使用新主题颜色）
        4. 更新排版系统
        5. 发送主题应用完成信号
        
        Args:
            theme_name: 主题名称 ("浅色", "深色", "自动")
            
        Returns:
            bool: 主题应用是否成功
        """
        if not self._is_initialized:
            logger.error("ModernUIManager 未初始化，无法应用主题")
            return False
        
        try:
            logger.info(f"应用现代化主题: {theme_name}")
            
            # 1. 设置主题管理器
            self.theme_manager.set_theme(theme_name)
            
            # 2. 清除图标缓存，以便重新生成使用新主题颜色的图标
            self.icon_manager.clear_cache()
            logger.debug("图标缓存已清除")
            
            # 3. Toast 通知会在下次创建时自动使用新主题
            
            logger.info(f"主题 '{theme_name}' 应用完成")
            self.theme_applied.emit(theme_name)
            
            return True
            
        except Exception as e:
            logger.error(f"应用主题失败: {e}", exc_info=True)
            return False
    
    def _on_theme_changed(self, theme_name: str):
        """
        主题变化回调
        
        当主题管理器的主题发生变化时（包括系统主题自动切换），
        协调所有子系统更新。
        
        Args:
            theme_name: 新主题名称
        """
        logger.debug(f"主题已变化: {theme_name}")
        
        # 清除图标缓存
        if self.icon_manager:
            self.icon_manager.clear_cache()
        
        # 卡片管理器会自动响应 theme_changed 信号
        # 其他组件在下次使用时会自动使用新主题
    
    def _on_performance_mode_changed(self, mode: str):
        """
        性能模式变化回调（需求 14.5, 14.6）
        
        当性能降级管理器检测到性能变化时，自动调整动画复杂度和液态玻璃效果
        
        Args:
            mode: 新的性能模式 ('high', 'medium', 'low')
        """
        logger.info(f"性能模式已变化: {mode}")
        
        # 调整动画管理器
        if self.animation_manager:
            if mode == "low":
                # 低性能模式：禁用动画
                self.animation_manager.disable_animations()
                logger.info("低性能模式：已禁用动画")
            elif mode == "medium":
                # 中等性能模式：启用动画但降低复杂度
                self.animation_manager.enable_animations()
                self.animation_manager.enable_performance_mode()
                logger.info("中等性能模式：已启用性能模式")
            else:  # high
                # 高性能模式：启用所有动画
                self.animation_manager.enable_animations()
                self.animation_manager.disable_performance_mode()
                logger.info("高性能模式：已启用所有动画")
        
        # 调整液态玻璃管理器
        if self.liquid_glass_manager:
            if mode == "low":
                # 低性能模式：启用性能模式
                self.liquid_glass_manager.enable_performance_mode()
                logger.info("低性能模式：液态玻璃已启用性能模式")
            else:
                # 中高性能模式：禁用性能模式
                self.liquid_glass_manager.disable_performance_mode()
                logger.info(f"{mode}性能模式：液态玻璃已禁用性能模式")
    
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._is_initialized
    
    def get_theme_manager(self) -> Optional[EnhancedThemeManager]:
        """
        获取增强主题管理器
        
        Returns:
            EnhancedThemeManager 实例，如果未初始化则返回 None
        """
        return self.theme_manager
    
    def get_liquid_glass_manager(self) -> Optional[LiquidGlassManager]:
        """
        获取液态玻璃管理器
        
        Returns:
            LiquidGlassManager 实例，如果未初始化则返回 None
        """
        return self.liquid_glass_manager
    
    def get_animation_manager(self) -> Optional[EnhancedAnimationManager]:
        """
        获取增强动画管理器
        
        Returns:
            EnhancedAnimationManager 实例，如果未初始化则返回 None
        """
        return self.animation_manager
    
    def get_layout_manager(self) -> Optional[LayoutManager]:
        """
        获取布局管理器
        
        Returns:
            LayoutManager 实例，如果未初始化则返回 None
        """
        return self.layout_manager
    
    def get_icon_manager(self) -> Optional[IconManager]:
        """
        获取图标管理器
        
        Returns:
            IconManager 实例，如果未初始化则返回 None
        """
        return self.icon_manager
    
    def get_toast_manager(self) -> Optional[ToastManager]:
        """
        获取 Toast 管理器
        
        Returns:
            ToastManager 实例，如果未初始化则返回 None
        """
        return self.toast_manager
    
    def get_typography_system(self) -> Optional[TypographySystem]:
        """
        获取排版系统
        
        Returns:
            TypographySystem 实例，如果未初始化则返回 None
        """
        return self.typography_system
    
    def get_performance_optimizer(self) -> Optional[PerformanceOptimizer]:
        """
        获取性能优化器
        
        Returns:
            PerformanceOptimizer 实例，如果未初始化则返回 None
        """
        return self.performance_optimizer
    
    def enable_animations(self):
        """启用动画"""
        if self.animation_manager:
            self.animation_manager.enable_animations()
            logger.info("动画已启用")
    
    def disable_animations(self):
        """禁用动画"""
        if self.animation_manager:
            self.animation_manager.disable_animations()
            logger.info("动画已禁用")
    
    def enable_performance_mode(self):
        """
        启用性能模式
        
        降低动画复杂度以提高性能
        """
        if self.animation_manager:
            self.animation_manager.enable_performance_mode()
            logger.info("性能模式已启用")
    
    def disable_performance_mode(self):
        """禁用性能模式"""
        if self.animation_manager:
            self.animation_manager.disable_performance_mode()
            logger.info("性能模式已禁用")
    
    def show_toast(self, message: str, toast_type: str = "info", duration: int = 3000):
        """
        显示 Toast 通知（便捷方法）
        
        Args:
            message: 通知消息
            toast_type: 通知类型 (success, warning, error, info)
            duration: 显示时长（毫秒）
        """
        if self.toast_manager:
            self.toast_manager.show(message, toast_type, duration)
    
    def show_success(self, message: str, duration: int = 3000):
        """显示成功通知"""
        if self.toast_manager:
            self.toast_manager.show_success(message, duration)
    
    def show_warning(self, message: str, duration: int = 4000):
        """显示警告通知"""
        if self.toast_manager:
            self.toast_manager.show_warning(message, duration)
    
    def show_error(self, message: str, duration: int = 5000):
        """显示错误通知"""
        if self.toast_manager:
            self.toast_manager.show_error(message, duration)
    
    def show_info(self, message: str, duration: int = 3000):
        """显示信息通知"""
        if self.toast_manager:
            self.toast_manager.show_info(message, duration)
    
    def get_current_breakpoint(self) -> Optional[str]:
        """
        获取当前布局断点
        
        Returns:
            当前断点名称 ('small', 'medium', 'large')，如果未初始化则返回 None
        """
        if self.layout_manager:
            return self.layout_manager.get_current_breakpoint()
        return None
    
    def get_status_info(self) -> dict:
        """
        获取管理器状态信息
        
        Returns:
            包含各子系统状态的字典
        """
        info = {
            'initialized': self._is_initialized,
            'theme': self.theme_manager.get_current_theme() if self.theme_manager else None,
            'animations_enabled': self.animation_manager.animations_enabled if self.animation_manager else None,
            'performance_mode': self.animation_manager.performance_mode if self.animation_manager else None,
            'active_animations': self.animation_manager.get_active_animation_count() if self.animation_manager else 0,
            'active_toasts': self.toast_manager.get_active_count() if self.toast_manager else 0,
            'current_breakpoint': self.get_current_breakpoint(),
            'icon_cache_size': self.icon_manager.get_cache_size() if self.icon_manager else 0,
        }
        
        # 添加液态玻璃管理器信息
        if self.liquid_glass_manager:
            glass_info = self.liquid_glass_manager.get_platform_info()
            blur_stats = self.liquid_glass_manager.get_blur_stats()
            info.update({
                'liquid_glass_platform': glass_info.get('platform', 'unknown'),
                'liquid_glass_native_blur': glass_info.get('native_blur_supported', False),
                'liquid_glass_performance_mode': glass_info.get('performance_mode', False),
                'liquid_glass_blur_quality': glass_info.get('blur_quality', 'unknown'),
                'liquid_glass_managed_panels': self.liquid_glass_manager.get_managed_panel_count(),
                'liquid_glass_blur_cache': blur_stats.get('cache_size', 0),
            })
        
        # 添加性能优化器信息
        if self.performance_optimizer:
            perf_stats = self.performance_optimizer.get_stats()
            info.update({
                'fps': perf_stats.get('fps', 0),
                'performance_degradation_mode': perf_stats.get('performance_mode', 'unknown'),
                'cache_stats': perf_stats.get('cache_stats', {}),
                'should_reduce_animations': perf_stats.get('should_reduce_animations', False),
                'animation_duration_multiplier': perf_stats.get('animation_duration_multiplier', 1.0),
                'max_concurrent_animations': perf_stats.get('max_concurrent_animations', 5),
            })
        
        return info
    
    def cleanup(self):
        """
        清理资源
        
        在应用关闭时调用，清理所有子系统
        """
        logger.info("开始清理 ModernUIManager...")
        
        try:
            # 停止所有动画
            if self.animation_manager:
                self.animation_manager.stop_all_animations()
            
            # 清除所有 Toast 通知
            if self.toast_manager:
                self.toast_manager.clear_all()
            
            # 清除图标缓存
            if self.icon_manager:
                self.icon_manager.clear_cache()
            
            # 清理液态玻璃管理器
            if self.liquid_glass_manager:
                self.liquid_glass_manager.cleanup()
                logger.debug("液态玻璃管理器已清理")
            
            # 清理性能优化器
            if self.performance_optimizer:
                self.performance_optimizer.component_cache.clear()
                logger.debug("性能优化器已清理")
            
            logger.info("ModernUIManager 清理完成")
            
        except Exception as e:
            logger.error(f"ModernUIManager 清理失败: {e}", exc_info=True)


# 全局单例（可选）
_modern_ui_manager_instance: Optional[ModernUIManager] = None


def get_modern_ui_manager(main_window: Optional[QMainWindow] = None) -> ModernUIManager:
    """
    获取现代化 UI 管理器单例
    
    Args:
        main_window: 主窗口实例（首次调用时必须提供）
        
    Returns:
        ModernUIManager 实例
    """
    global _modern_ui_manager_instance
    if _modern_ui_manager_instance is None:
        if main_window is None:
            raise ValueError("首次调用 get_modern_ui_manager 必须提供 main_window 参数")
        _modern_ui_manager_instance = ModernUIManager(main_window)
    return _modern_ui_manager_instance
