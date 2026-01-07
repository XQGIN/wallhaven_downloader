"""
macOS 平台模糊提供者

使用 macOS 原生 NSVisualEffectView
"""

import sys
import platform
from PyQt5.QtWidgets import QWidget, QGraphicsBlurEffect
from PyQt5.QtCore import Qt
from .platform_adapter import BlurProvider


class MacOSBlurProvider(BlurProvider):
    """
    macOS 模糊提供者
    
    使用 NSVisualEffectView（如果可用）
    如果原生效果不可用，降级到 PyQt5 模糊
    
    需求：1.7, 15.2
    """
    
    def __init__(self):
        """初始化 macOS 模糊提供者"""
        self.native_blur_available = False
        self.macos_version = self._get_macos_version()
        self._check_native_blur_support()
    
    def _get_macos_version(self) -> tuple:
        """
        获取 macOS 版本号
        
        Returns:
            (major, minor, patch) 版本元组
        """
        try:
            version = platform.mac_ver()[0]
            if version:
                parts = version.split('.')
                major = int(parts[0]) if len(parts) > 0 else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                patch = int(parts[2]) if len(parts) > 2 else 0
                return (major, minor, patch)
        except Exception:
            pass
        return (0, 0, 0)
    
    def _check_native_blur_support(self):
        """
        检查是否支持原生模糊效果
        
        NSVisualEffectView 在 macOS 10.10+ 可用
        尝试导入 PyObjC 库来访问原生 API
        """
        try:
            major, minor, patch = self.macos_version
            
            # NSVisualEffectView 需要 macOS 10.10 (Yosemite) 或更高版本
            if major >= 10 and minor >= 10:
                # 尝试导入 PyObjC
                try:
                    # import objc
                    # from AppKit import NSVisualEffectView
                    # self.native_blur_available = True
                    # return
                    pass
                except ImportError:
                    pass
            
            # 如果原生库不可用，使用 PyQt5 降级方案
            self.native_blur_available = False
            
        except Exception as e:
            print(f"检查 macOS 原生模糊支持时出错: {e}")
            self.native_blur_available = False
    
    
    def _apply_native_blur(self, widget: QWidget, blur_radius: int) -> bool:
        """
        应用原生 macOS 模糊效果（NSVisualEffectView）
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径（注意：NSVisualEffectView 不直接支持半径参数）
            
        Returns:
            是否成功应用
            
        注意：此方法为未来集成 NSVisualEffectView 预留
        当前版本使用降级方案
        """
        try:
            # TODO: 集成 NSVisualEffectView
            # 
            # from AppKit import NSVisualEffectView, NSVisualEffectMaterialLight
            # from PyQt5.QtMacExtras import QMacNativeWidget
            # 
            # # 创建 NSVisualEffectView
            # effect_view = NSVisualEffectView.alloc().initWithFrame_(widget.rect())
            # effect_view.setMaterial_(NSVisualEffectMaterialLight)
            # effect_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            # effect_view.setState_(NSVisualEffectStateActive)
            # 
            # # 将效果视图添加到 Qt 组件
            # native_widget = QMacNativeWidget()
            # native_widget.setNativeView(effect_view)
            # widget.layout().addWidget(native_widget)
            # 
            # return True
            
            return False
            
        except Exception as e:
            print(f"应用原生 macOS 模糊失败: {e}")
            return False
    
    def apply_blur(self, widget: QWidget, blur_radius: int) -> bool:
        """
        应用模糊效果
        
        优先尝试使用原生模糊效果，失败则降级到 PyQt5 模糊
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径 (5-40px)
            
        Returns:
            是否成功应用
        """
        # 限制模糊半径范围
        blur_radius = max(5, min(40, blur_radius))
        
        # 尝试使用原生模糊
        if self.native_blur_available:
            try:
                if self._apply_native_blur(widget, blur_radius):
                    return True
            except Exception as e:
                print(f"macOS 原生模糊失败，降级到 PyQt5: {e}")
        
        # 降级到 PyQt5 模糊
        return self._apply_qt_blur(widget, blur_radius)
    
    
    def _apply_qt_blur(self, widget: QWidget, blur_radius: int) -> bool:
        """
        使用 PyQt5 QGraphicsBlurEffect 应用模糊（降级方案）
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径
            
        Returns:
            是否成功应用
        """
        try:
            # 创建模糊效果
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(blur_radius)
            
            # 设置模糊提示（优化性能）
            blur_effect.setBlurHints(QGraphicsBlurEffect.PerformanceHint)
            
            # 应用到组件
            widget.setGraphicsEffect(blur_effect)
            
            return True
            
        except Exception as e:
            print(f"PyQt5 模糊应用失败: {e}")
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
            
            # 如果使用了原生模糊，也需要清理
            if self.native_blur_available:
                try:
                    # TODO: 清理 NSVisualEffectView
                    # 具体实现取决于如何集成原生视图
                    pass
                except Exception:
                    pass
            
            return True
            
        except Exception as e:
            print(f"移除模糊失败: {e}")
            return False
    
    def is_supported(self) -> bool:
        """
        检查是否支持此模糊实现
        
        Returns:
            是否支持（macOS 平台始终支持降级方案）
        """
        return True
    
    def is_native_available(self) -> bool:
        """
        检查原生模糊是否可用
        
        Returns:
            是否可用原生模糊
        """
        return self.native_blur_available
    
    def get_macos_version_string(self) -> str:
        """
        获取 macOS 版本字符串
        
        Returns:
            版本字符串，如 "10.15.7"
        """
        major, minor, patch = self.macos_version
        return f"{major}.{minor}.{patch}"
