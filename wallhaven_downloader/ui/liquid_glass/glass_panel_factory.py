"""
玻璃面板工厂

负责创建各种类型的玻璃面板组件
"""

from PyQt5.QtWidgets import QWidget
from typing import Dict, Optional


class GlassPanelFactory:
    """
    玻璃面板工厂
    
    负责创建各种类型的玻璃面板组件
    
    需求：1.1-1.5
    """
    
    # 面板类型配置
    PANEL_TYPES = {
        "normal": {
            "blur_radius": 20,
            "transparency": 0.7,
            "border_radius": 12,
            "shadow_blur": 20
        },
        "elevated": {
            "blur_radius": 25,
            "transparency": 0.75,
            "border_radius": 16,
            "shadow_blur": 30
        },
        "floating": {
            "blur_radius": 30,
            "transparency": 0.8,
            "border_radius": 20,
            "shadow_blur": 40
        }
    }
    
    def __init__(self):
        """初始化玻璃面板工厂"""
        pass
    
    def create_panel(self,
                    parent: QWidget,
                    panel_type: str = "normal",
                    custom_config: Optional[Dict] = None) -> 'EnhancedGlassPanel':
        """
        创建玻璃面板
        
        Args:
            parent: 父组件
            panel_type: 面板类型 (normal, elevated, floating)
            custom_config: 自定义配置，会覆盖默认配置
            
        Returns:
            玻璃面板组件
        """
        # 延迟导入以避免循环依赖
        from .enhanced_glass_panel import EnhancedGlassPanel
        
        # 获取基础配置
        if panel_type not in self.PANEL_TYPES:
            panel_type = "normal"
        
        config = self.PANEL_TYPES[panel_type].copy()
        
        # 应用自定义配置
        if custom_config:
            config.update(custom_config)
        
        # 创建面板
        panel = EnhancedGlassPanel(parent, config)
        return panel
    
    def create_card(self,
                   parent: QWidget,
                   title: str = "",
                   content: QWidget = None) -> 'GlassCard':
        """
        创建玻璃卡片
        
        Args:
            parent: 父组件
            title: 卡片标题
            content: 卡片内容组件
            
        Returns:
            玻璃卡片组件
        """
        # TODO: 在后续任务中实现 GlassCard
        # 目前返回基础面板
        from .enhanced_glass_panel import EnhancedGlassPanel
        return EnhancedGlassPanel(parent, self.PANEL_TYPES["normal"])
    
    def create_modal(self,
                    parent: QWidget,
                    content: QWidget = None) -> 'GlassModal':
        """
        创建玻璃模态框
        
        Args:
            parent: 父组件
            content: 模态框内容组件
            
        Returns:
            玻璃模态框组件
        """
        # TODO: 在后续任务中实现 GlassModal
        # 目前返回浮动面板
        from .enhanced_glass_panel import EnhancedGlassPanel
        return EnhancedGlassPanel(parent, self.PANEL_TYPES["floating"])
    
    def get_panel_config(self, panel_type: str) -> Dict:
        """
        获取面板类型的配置
        
        Args:
            panel_type: 面板类型
            
        Returns:
            配置字典
        """
        return self.PANEL_TYPES.get(panel_type, self.PANEL_TYPES["normal"]).copy()
    
    def register_panel_type(self, type_name: str, config: Dict):
        """
        注册新的面板类型
        
        Args:
            type_name: 类型名称
            config: 配置字典
        """
        self.PANEL_TYPES[type_name] = config
