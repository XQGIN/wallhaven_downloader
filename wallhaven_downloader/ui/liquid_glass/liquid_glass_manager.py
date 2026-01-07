"""
液态玻璃管理器

负责管理全局的液态玻璃效果，包括模糊层、透明度、光影效果
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QWidget
from typing import Dict, List, Optional


class LiquidGlassManager(QObject):
    """
    液态玻璃系统管理器
    
    负责管理全局的液态玻璃效果，包括模糊层、透明度、光影效果
    
    需求：1.1-1.8, 14.6
    """
    
    # 信号
    blur_quality_changed = pyqtSignal(str)  # 模糊质量变化
    transparency_changed = pyqtSignal(float)  # 透明度变化
    performance_mode_changed = pyqtSignal(bool)  # 性能模式变化
    
    # 质量级别配置
    QUALITY_CONFIGS = {
        "low": {
            "blur_radius": 10,
            "transparency": 0.6,
            "use_native": False,
            "enable_shadows": False,
            "enable_highlights": False
        },
        "medium": {
            "blur_radius": 15,
            "transparency": 0.7,
            "use_native": True,
            "enable_shadows": True,
            "enable_highlights": False
        },
        "high": {
            "blur_radius": 20,
            "transparency": 0.75,
            "use_native": True,
            "enable_shadows": True,
            "enable_highlights": True
        }
    }
    
    def __init__(self, main_window: QMainWindow = None):
        """
        初始化液态玻璃管理器
        
        Args:
            main_window: 主窗口实例
        """
        super().__init__()
        self.main_window = main_window
        
        # 延迟导入以避免循环依赖
        from .blur_layer_manager import BlurLayerManager
        from .glass_panel_factory import GlassPanelFactory
        from .platform_adapter import PlatformBlurAdapter
        from .repaint_optimizer import get_repaint_optimizer
        
        self.blur_layer_manager = BlurLayerManager()
        self.glass_panel_factory = GlassPanelFactory()
        self.platform_adapter = PlatformBlurAdapter()
        self.repaint_optimizer = get_repaint_optimizer()
        
        # 配置参数
        self.blur_radius = 20  # 模糊半径 (5-40px)
        self.transparency = 0.7  # 透明度 (0.6-0.95)
        self.blur_quality = "high"  # 模糊质量 (low, medium, high)
        
        # 初始化状态
        self._initialized = False
        self._performance_mode = False
        
        # 保存原始配置（用于性能模式切换）
        self._original_blur_radius = self.blur_radius
        self._original_transparency = self.transparency
        self._original_quality = self.blur_quality
        
        # 管理的玻璃面板列表
        self._managed_panels: List[QWidget] = []
        
        # 主题管理器引用（延迟初始化）
        self._theme_manager = None
        self._theme_connected = False
    
    def initialize(self) -> bool:
        """
        初始化液态玻璃系统
        
        Returns:
            是否成功初始化
        """
        if self._initialized:
            return True
        
        try:
            # 初始化平台适配器
            if not self.platform_adapter.initialize():
                print("警告: 平台适配器初始化失败，将使用降级方案")
            
            self._initialized = True
            return True
        except Exception as e:
            print(f"液态玻璃系统初始化失败: {e}")
            return False
    
    def apply_global_blur(self, widget: QWidget) -> bool:
        """
        为窗口应用全局模糊效果
        
        Args:
            widget: 目标窗口组件
            
        Returns:
            是否成功应用模糊
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        # 根据性能模式决定是否使用原生模糊
        use_native = not self._performance_mode
        
        success = self.blur_layer_manager.apply_blur(
            widget,
            blur_radius=self.blur_radius,
            use_native=use_native
        )
        
        return success
    
    def create_glass_panel(self, 
                          parent: QWidget,
                          panel_type: str = "normal",
                          blur_radius: int = None,
                          transparency: float = None) -> QWidget:
        """
        创建玻璃面板组件
        
        Args:
            parent: 父组件
            panel_type: 面板类型 (normal, elevated, floating)
            blur_radius: 自定义模糊半径
            transparency: 自定义透明度
            
        Returns:
            玻璃面板组件
        """
        custom_config = {}
        
        # 应用自定义配置
        if blur_radius is not None:
            custom_config['blur_radius'] = blur_radius
        if transparency is not None:
            custom_config['transparency'] = transparency
        
        # 在性能模式下，应用性能优化配置
        if self._performance_mode:
            quality_config = self.QUALITY_CONFIGS[self.blur_quality]
            custom_config['blur_radius'] = quality_config['blur_radius']
            custom_config['transparency'] = quality_config['transparency']
            custom_config['enable_shadows'] = quality_config['enable_shadows']
            custom_config['enable_highlights'] = quality_config['enable_highlights']
        
        panel = self.glass_panel_factory.create_panel(
            parent,
            panel_type=panel_type,
            custom_config=custom_config if custom_config else None
        )
        
        # 添加到管理列表
        self._managed_panels.append(panel)
        
        return panel
    
    def set_blur_radius(self, radius: int):
        """
        设置模糊半径 (5-40px)
        
        Args:
            radius: 模糊半径
        """
        # 限制在有效范围内
        self.blur_radius = max(5, min(40, radius))
        
        # 如果不在性能模式，保存为原始配置
        if not self._performance_mode:
            self._original_blur_radius = self.blur_radius
    
    def set_transparency(self, transparency: float):
        """
        设置透明度 (0.6-0.95)
        
        Args:
            transparency: 透明度值
        """
        # 限制在有效范围内
        self.transparency = max(0.6, min(0.95, transparency))
        self.transparency_changed.emit(self.transparency)
        
        # 如果不在性能模式，保存为原始配置
        if not self._performance_mode:
            self._original_transparency = self.transparency
    
    def set_blur_quality(self, quality: str):
        """
        设置模糊质量 (low, medium, high)
        
        Args:
            quality: 质量级别
        """
        if quality in ["low", "medium", "high"]:
            self.blur_quality = quality
            self.blur_quality_changed.emit(quality)
            
            # 如果不在性能模式，保存为原始配置
            if not self._performance_mode:
                self._original_quality = quality
    
    def enable_performance_mode(self):
        """
        启用性能模式（降低视觉效果质量）
        
        需求：14.6
        """
        if self._performance_mode:
            return
        
        # 保存当前配置
        self._original_blur_radius = self.blur_radius
        self._original_transparency = self.transparency
        self._original_quality = self.blur_quality
        
        # 应用性能模式配置
        self._performance_mode = True
        self.set_blur_quality("low")
        
        # 应用低质量配置
        quality_config = self.QUALITY_CONFIGS["low"]
        self.blur_radius = quality_config['blur_radius']
        self.transparency = quality_config['transparency']
        
        # 更新所有已管理的面板
        self._update_managed_panels()
        
        # 发出信号
        self.performance_mode_changed.emit(True)
        
        print("性能模式已启用：降低视觉效果质量以提升性能")
    
    def disable_performance_mode(self):
        """
        禁用性能模式（恢复完整视觉效果）
        
        需求：14.6
        """
        if not self._performance_mode:
            return
        
        # 恢复原始配置
        self._performance_mode = False
        self.blur_radius = self._original_blur_radius
        self.transparency = self._original_transparency
        self.set_blur_quality(self._original_quality)
        
        # 更新所有已管理的面板
        self._update_managed_panels()
        
        # 发出信号
        self.performance_mode_changed.emit(False)
        
        print("性能模式已禁用：恢复完整视觉效果")
    
    def _update_managed_panels(self):
        """
        更新所有已管理的玻璃面板
        
        应用当前的质量配置到所有面板
        """
        quality_config = self.QUALITY_CONFIGS[self.blur_quality]
        
        for panel in self._managed_panels[:]:  # 使用副本遍历
            try:
                # 检查面板是否仍然有效
                if panel is None or not panel.isVisible():
                    self._managed_panels.remove(panel)
                    continue
                
                # 更新面板配置
                if hasattr(panel, 'blur_radius'):
                    panel.blur_radius = quality_config['blur_radius']
                if hasattr(panel, 'transparency'):
                    panel.transparency = quality_config['transparency']
                
                # 触发重绘
                panel.update()
            except Exception as e:
                print(f"更新面板失败: {e}")
                # 移除无效面板
                if panel in self._managed_panels:
                    self._managed_panels.remove(panel)
    
    def is_performance_mode(self) -> bool:
        """
        检查是否处于性能模式
        
        Returns:
            是否启用性能模式
        """
        return self._performance_mode
    
    def get_quality_config(self, quality: str = None) -> Dict:
        """
        获取质量配置
        
        Args:
            quality: 质量级别，如果为 None 则返回当前质量配置
            
        Returns:
            质量配置字典
        """
        if quality is None:
            quality = self.blur_quality
        
        return self.QUALITY_CONFIGS.get(quality, self.QUALITY_CONFIGS["high"]).copy()
    
    def get_managed_panel_count(self) -> int:
        """
        获取当前管理的面板数量
        
        Returns:
            面板数量
        """
        return len(self._managed_panels)
    
    def clear_managed_panels(self):
        """清除所有管理的面板引用"""
        self._managed_panels.clear()
    
    def get_platform_info(self) -> Dict[str, any]:
        """
        获取平台信息
        
        Returns:
            包含平台信息的字典
        """
        return {
            "platform": self.platform_adapter.get_platform_name(),
            "native_blur_supported": self.platform_adapter.is_native_blur_supported(),
            "initialized": self._initialized,
            "performance_mode": self._performance_mode,
            "blur_quality": self.blur_quality,
            "blur_radius": self.blur_radius,
            "transparency": self.transparency
        }
    
    def get_blur_stats(self) -> Dict:
        """
        获取模糊效果统计信息
        
        Returns:
            统计信息字典
        """
        blur_stats = self.blur_layer_manager.get_cache_stats()
        repaint_stats = self.repaint_optimizer.get_optimization_stats()
        
        return {
            **blur_stats,
            "repaint_optimization": repaint_stats
        }
    
    def cleanup(self):
        """
        清理资源
        
        在应用关闭时调用
        """
        # 断开主题管理器信号
        if self._theme_manager and self._theme_connected:
            try:
                self._theme_manager.theme_changed.disconnect(self._on_theme_changed)
            except Exception:
                pass
        
        # 清除所有模糊缓存
        self.blur_layer_manager.clear_blur_cache()
        
        # 清除面板引用
        self.clear_managed_panels()
        
        # 清理重绘优化器
        self.repaint_optimizer.cleanup()
        
        print("液态玻璃管理器已清理")
    
    def connect_theme_manager(self, theme_manager):
        """
        连接主题管理器
        
        Args:
            theme_manager: 增强主题管理器实例
            
        需求：2.7
        """
        if self._theme_connected:
            return
        
        self._theme_manager = theme_manager
        
        # 连接主题切换信号
        try:
            theme_manager.theme_changed.connect(self._on_theme_changed)
            self._theme_connected = True
            print("液态玻璃管理器已连接到主题管理器")
            
            # 立即应用当前主题
            self._on_theme_changed()
        except Exception as e:
            print(f"连接主题管理器失败: {e}")
    
    def _on_theme_changed(self):
        """
        主题切换回调
        
        在主题切换时调整玻璃效果参数并更新所有玻璃组件
        
        需求：2.7
        """
        if not self._theme_manager:
            return
        
        try:
            # 获取当前主题
            is_dark_mode = self._theme_manager.is_dark_mode()
            
            print(f"主题切换检测: {'深色' if is_dark_mode else '浅色'}模式")
            
            # 根据主题调整玻璃效果参数
            if is_dark_mode:
                # 深色模式：增加模糊强度，提高透明度
                self._adjust_for_dark_theme()
            else:
                # 浅色模式：适中的模糊和透明度
                self._adjust_for_light_theme()
            
            # 更新所有管理的玻璃面板
            self._update_panels_for_theme(is_dark_mode)
            
            print(f"玻璃效果已调整: 模糊半径={self.blur_radius}, 透明度={self.transparency}")
        
        except Exception as e:
            print(f"主题切换处理失败: {e}")
    
    def _adjust_for_dark_theme(self):
        """
        调整为深色主题的玻璃效果参数
        
        深色模式下：
        - 增加模糊强度（更强的模糊效果）
        - 提高透明度（更透明）
        - 增强对比度
        """
        if not self._performance_mode:
            # 深色模式使用更强的模糊
            self.blur_radius = 25
            self.transparency = 0.78
            self._original_blur_radius = self.blur_radius
            self._original_transparency = self.transparency
        else:
            # 性能模式下也要调整
            quality_config = self.QUALITY_CONFIGS[self.blur_quality].copy()
            quality_config['blur_radius'] = int(quality_config['blur_radius'] * 1.2)
            quality_config['transparency'] = min(0.95, quality_config['transparency'] + 0.08)
            self.blur_radius = quality_config['blur_radius']
            self.transparency = quality_config['transparency']
    
    def _adjust_for_light_theme(self):
        """
        调整为浅色主题的玻璃效果参数
        
        浅色模式下：
        - 适中的模糊强度
        - 适中的透明度
        - 柔和的视觉效果
        """
        if not self._performance_mode:
            # 浅色模式使用标准模糊
            self.blur_radius = 20
            self.transparency = 0.7
            self._original_blur_radius = self.blur_radius
            self._original_transparency = self.transparency
        else:
            # 性能模式下使用配置值
            quality_config = self.QUALITY_CONFIGS[self.blur_quality]
            self.blur_radius = quality_config['blur_radius']
            self.transparency = quality_config['transparency']
    
    def _update_panels_for_theme(self, is_dark_mode: bool):
        """
        更新所有玻璃面板以适应新主题
        
        Args:
            is_dark_mode: 是否为深色模式
        """
        # 获取主题颜色
        theme_colors = self._get_theme_colors(is_dark_mode)
        
        for panel in self._managed_panels[:]:  # 使用副本遍历
            try:
                # 检查面板是否仍然有效
                if panel is None or not hasattr(panel, 'update'):
                    self._managed_panels.remove(panel)
                    continue
                
                # 更新面板的模糊和透明度
                if hasattr(panel, 'set_blur_radius'):
                    panel.set_blur_radius(self.blur_radius)
                if hasattr(panel, 'set_transparency'):
                    panel.set_transparency(self.transparency)
                
                # 更新面板的主题颜色
                if hasattr(panel, 'update_theme_colors'):
                    panel.update_theme_colors(theme_colors, is_dark_mode)
                
                # 触发重绘
                panel.update()
            
            except Exception as e:
                print(f"更新面板主题失败: {e}")
                # 移除无效面板
                if panel in self._managed_panels:
                    self._managed_panels.remove(panel)
    
    def _get_theme_colors(self, is_dark_mode: bool) -> Dict:
        """
        获取主题颜色方案
        
        Args:
            is_dark_mode: 是否为深色模式
            
        Returns:
            颜色字典
        """
        if not self._theme_manager:
            # 如果没有主题管理器，返回默认颜色
            return self._get_default_colors(is_dark_mode)
        
        try:
            # 尝试从主题管理器获取苹果颜色
            if hasattr(self._theme_manager, 'apple_palette'):
                return self._theme_manager.apple_palette.get_all_colors(is_dark_mode)
        except Exception as e:
            print(f"获取主题颜色失败: {e}")
        
        return self._get_default_colors(is_dark_mode)
    
    def _get_default_colors(self, is_dark_mode: bool) -> Dict:
        """
        获取默认颜色方案（当主题管理器不可用时）
        
        Args:
            is_dark_mode: 是否为深色模式
            
        Returns:
            颜色字典
        """
        from PyQt5.QtGui import QColor
        
        if is_dark_mode:
            return {
                "background": QColor(28, 28, 30),
                "surface": QColor(44, 44, 46),
                "glass_normal": QColor(44, 44, 46, 200),
                "glass_hover": QColor(58, 58, 60, 230),
                "text_primary": QColor(245, 245, 247),
                "accent": QColor(10, 132, 255),
                "border": QColor(56, 56, 58),
            }
        else:
            return {
                "background": QColor(245, 245, 247),
                "surface": QColor(255, 255, 255),
                "glass_normal": QColor(255, 255, 255, 200),
                "glass_hover": QColor(255, 255, 255, 230),
                "text_primary": QColor(29, 29, 31),
                "accent": QColor(0, 122, 255),
                "border": QColor(216, 216, 220),
            }
