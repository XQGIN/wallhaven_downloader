"""
平台模糊适配器

提供跨平台的模糊效果实现，支持 Windows、macOS、Linux
"""

import sys
import platform
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget
from typing import Optional


class PlatformBlurAdapter(QObject):
    """
    平台模糊适配器
    
    检测操作系统并提供平台特定的模糊实现
    
    需求：1.6, 1.7, 1.8, 15.1-15.4
    """
    
    def __init__(self):
        """初始化平台适配器"""
        super().__init__()
        
        self.platform = self._detect_platform()
        self.blur_provider: Optional['BlurProvider'] = None
        self._initialized = False
    
    def _detect_platform(self) -> str:
        """
        检测当前操作系统平台
        
        Returns:
            平台名称: 'windows', 'macos', 'linux'
        """
        system = platform.system().lower()
        
        if system == 'windows':
            return 'windows'
        elif system == 'darwin':
            return 'macos'
        elif system == 'linux':
            return 'linux'
        else:
            # 默认使用 Linux 方案
            return 'linux'
    
    def initialize(self) -> bool:
        """
        初始化平台特定的模糊提供者
        
        Returns:
            是否成功初始化
        """
        if self._initialized:
            return True
        
        try:
            if self.platform == 'windows':
                from .windows_blur_provider import WindowsBlurProvider
                self.blur_provider = WindowsBlurProvider()
            elif self.platform == 'macos':
                from .macos_blur_provider import MacOSBlurProvider
                self.blur_provider = MacOSBlurProvider()
            else:  # linux
                from .linux_blur_provider import LinuxBlurProvider
                self.blur_provider = LinuxBlurProvider()
            
            self._initialized = True
            return True
        
        except ImportError as e:
            print(f"平台模糊提供者导入失败: {e}")
            # 使用降级方案
            return self._initialize_fallback()
        except Exception as e:
            print(f"平台适配器初始化失败: {e}")
            return self._initialize_fallback()
    
    def _initialize_fallback(self) -> bool:
        """
        初始化降级方案（使用 PyQt5 基础模糊）
        
        Returns:
            是否成功初始化
        """
        try:
            from .linux_blur_provider import LinuxBlurProvider
            self.blur_provider = LinuxBlurProvider()
            self._initialized = True
            return True
        except Exception as e:
            print(f"降级方案初始化失败: {e}")
            return False
    
    def apply_native_blur(self, widget: QWidget, blur_radius: int = 20) -> bool:
        """
        应用原生平台模糊效果
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径
            
        Returns:
            是否成功应用
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        if self.blur_provider is None:
            return False
        
        try:
            return self.blur_provider.apply_blur(widget, blur_radius)
        except Exception as e:
            print(f"应用原生模糊失败: {e}")
            return False
    
    def remove_native_blur(self, widget: QWidget) -> bool:
        """
        移除原生平台模糊效果
        
        Args:
            widget: 目标组件
            
        Returns:
            是否成功移除
        """
        if self.blur_provider is None:
            return False
        
        try:
            return self.blur_provider.remove_blur(widget)
        except Exception as e:
            print(f"移除原生模糊失败: {e}")
            return False
    
    def is_native_blur_supported(self) -> bool:
        """
        检查当前平台是否支持原生模糊
        
        Returns:
            是否支持原生模糊
        """
        if not self._initialized:
            self.initialize()
        
        return self.blur_provider is not None and self.blur_provider.is_supported()
    
    def get_platform_name(self) -> str:
        """
        获取平台名称
        
        Returns:
            平台名称
        """
        return self.platform


class BlurProvider:
    """
    模糊提供者基类
    
    定义平台特定模糊实现的接口
    """
    
    def apply_blur(self, widget: QWidget, blur_radius: int) -> bool:
        """
        应用模糊效果
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径
            
        Returns:
            是否成功应用
        """
        raise NotImplementedError("子类必须实现 apply_blur 方法")
    
    def remove_blur(self, widget: QWidget) -> bool:
        """
        移除模糊效果
        
        Args:
            widget: 目标组件
            
        Returns:
            是否成功移除
        """
        raise NotImplementedError("子类必须实现 remove_blur 方法")
    
    def is_supported(self) -> bool:
        """
        检查是否支持此模糊实现
        
        Returns:
            是否支持
        """
        return True
