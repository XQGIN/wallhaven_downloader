"""
Linux 平台模糊提供者

使用 PyQt5 QGraphicsBlurEffect
"""

import platform
from PyQt5.QtWidgets import QWidget, QGraphicsBlurEffect
from PyQt5.QtCore import Qt
from .platform_adapter import BlurProvider


class LinuxBlurProvider(BlurProvider):
    """
    Linux 模糊提供者
    
    使用 PyQt5 QGraphicsBlurEffect 实现模糊效果
    Linux 平台没有统一的原生模糊 API，因此直接使用 PyQt5 实现
    
    需求：1.8, 15.3
    """
    
    def __init__(self):
        """初始化 Linux 模糊提供者"""
        self.linux_distribution = self._get_linux_distribution()
        self.desktop_environment = self._get_desktop_environment()
    
    def _get_linux_distribution(self) -> str:
        """
        获取 Linux 发行版信息
        
        Returns:
            发行版名称
        """
        try:
            # 尝试获取发行版信息
            import distro
            return distro.name()
        except ImportError:
            try:
                # 降级方案：使用 platform 模块
                return platform.linux_distribution()[0]
            except Exception:
                return "Unknown"
    
    def _get_desktop_environment(self) -> str:
        """
        获取桌面环境信息
        
        Returns:
            桌面环境名称 (GNOME, KDE, XFCE, etc.)
        """
        try:
            import os
            
            # 检查常见的桌面环境变量
            desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
            if desktop:
                return desktop
            
            # 检查其他环境变量
            desktop = os.environ.get('DESKTOP_SESSION', '').lower()
            if desktop:
                return desktop
            
            return "Unknown"
            
        except Exception:
            return "Unknown"
    
    
    def apply_blur(self, widget: QWidget, blur_radius: int) -> bool:
        """
        应用模糊效果
        
        使用 PyQt5 QGraphicsBlurEffect 实现
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径 (5-40px)
            
        Returns:
            是否成功应用
        """
        # 限制模糊半径范围
        blur_radius = max(5, min(40, blur_radius))
        
        try:
            # 创建模糊效果
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(blur_radius)
            
            # 设置模糊提示（优化性能）
            # PerformanceHint: 优先性能，可能牺牲一些质量
            # QualityHint: 优先质量，可能影响性能
            blur_effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint)
            
            # 应用到组件
            widget.setGraphicsEffect(blur_effect)
            
            return True
            
        except Exception as e:
            print(f"Linux 模糊应用失败: {e}")
            return False
    
    def remove_blur(self, widget: QWidget) -> bool:
        """
        移除模糊效果
        
        Args:
            widget: 目标组件
            
        Returns:
            是否成功移除
        """
        try:
            # 移除图形效果
            widget.setGraphicsEffect(None)
            return True
            
        except Exception as e:
            print(f"移除模糊失败: {e}")
            return False
    
    def is_supported(self) -> bool:
        """
        检查是否支持此模糊实现
        
        Returns:
            是否支持（Linux 平台始终支持 PyQt5 模糊）
        """
        return True
    
    def get_system_info(self) -> dict:
        """
        获取系统信息
        
        Returns:
            包含发行版和桌面环境信息的字典
        """
        return {
            "distribution": self.linux_distribution,
            "desktop_environment": self.desktop_environment,
            "platform": "linux"
        }
    
    def set_blur_quality(self, widget: QWidget, high_quality: bool = False) -> bool:
        """
        设置模糊质量
        
        Args:
            widget: 目标组件
            high_quality: 是否使用高质量模糊
            
        Returns:
            是否成功设置
        """
        try:
            effect = widget.graphicsEffect()
            if effect and isinstance(effect, QGraphicsBlurEffect):
                hint = QGraphicsBlurEffect.QualityHint if high_quality else QGraphicsBlurEffect.PerformanceHint
                effect.setBlurHints(hint)
                return True
            return False
            
        except Exception as e:
            print(f"设置模糊质量失败: {e}")
            return False
