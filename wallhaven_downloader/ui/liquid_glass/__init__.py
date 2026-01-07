"""
液态玻璃效果系统

提供苹果风格的液态玻璃视觉效果，包括：
- 毛玻璃模糊效果
- 半透明层
- 动态光影效果
- 多层深度效果
- 跨平台兼容性
- 性能优化（缓存、重绘优化）

主要组件：
- LiquidGlassManager: 液态玻璃系统管理器
- BlurLayerManager: 模糊层管理器
- GlassPanelFactory: 玻璃面板工厂
- PlatformBlurAdapter: 平台模糊适配器
- EnhancedGlassPanel: 增强玻璃面板组件
- RepaintOptimizer: 重绘优化器
"""

from .liquid_glass_manager import LiquidGlassManager
from .blur_layer_manager import BlurLayerManager
from .glass_panel_factory import GlassPanelFactory
from .platform_adapter import PlatformBlurAdapter
from .enhanced_glass_panel import EnhancedGlassPanel
from .repaint_optimizer import RepaintOptimizer, get_repaint_optimizer

__all__ = [
    'LiquidGlassManager',
    'BlurLayerManager',
    'GlassPanelFactory',
    'PlatformBlurAdapter',
    'EnhancedGlassPanel',
    'RepaintOptimizer',
    'get_repaint_optimizer',
]

__version__ = '1.0.0'
