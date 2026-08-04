"""
Windows 平台模糊提供者

使用 Windows 原生 Acrylic 或 Mica 效果
"""

import sys
import platform
from PyQt5.QtWidgets import QWidget, QGraphicsBlurEffect
from PyQt5.QtCore import Qt
from .platform_adapter import BlurProvider


class WindowsBlurProvider(BlurProvider):
    """
    Windows 模糊提供者
    
    在 Windows 11 上优先使用 Mica 效果
    在 Windows 10 上使用 Acrylic 效果
    如果原生效果不可用，降级到 PyQt5 模糊
    
    需求：1.6, 18.1-18.8
    """
    
    def __init__(self):
        """初始化 Windows 模糊提供者"""
        self.native_blur_available = False
        self.windows_version = self._get_windows_version()
        self.blur_type = self._determine_blur_type()
        self._check_native_blur_support()
    
    def _get_windows_version(self) -> tuple:
        """
        获取 Windows 版本号
        
        Returns:
            (major, minor, build) 版本元组
        """
        try:
            version = platform.version()
            # Windows 版本格式: "10.0.19041" 或 "10.0.22000"
            parts = version.split('.')
            if len(parts) >= 3:
                major = int(parts[0])
                minor = int(parts[1])
                build = int(parts[2])
                return (major, minor, build)
        except Exception:
            pass
        return (0, 0, 0)
    
    def _determine_blur_type(self) -> str:
        """
        根据 Windows 版本确定模糊类型
        
        Returns:
            'mica' (Windows 11), 'acrylic' (Windows 10), 或 'qt' (降级)
        """
        major, minor, build = self.windows_version
        
        # Windows 11 (build >= 22000)
        if major >= 10 and build >= 22000:
            return 'mica'
        # Windows 10 (build >= 17134, 支持 Acrylic)
        elif major >= 10 and build >= 17134:
            return 'acrylic'
        else:
            return 'qt'
    
    
    def _check_native_blur_support(self):
        """
        检查是否支持原生模糊效果
        
        尝试导入和初始化原生模糊库（BlurWindow 或 win32mica）
        如果失败，标记为不可用，将使用降级方案
        """
        try:
            # 尝试导入 Windows 原生模糊库
            # 注意：这些库需要单独安装，不是必需依赖
            
            if self.blur_type == 'mica':
                # 尝试导入 Mica 效果库
                # try:
                #     import win32mica
                #     self.native_blur_available = True
                #     return
                # except ImportError:
                #     pass
                pass
            
            elif self.blur_type == 'acrylic':
                # 尝试导入 Acrylic 效果库
                # try:
                #     import BlurWindow
                #     self.native_blur_available = True
                #     return
                # except ImportError:
                #     pass
                pass
            
            # 如果原生库不可用，使用 PyQt5 降级方案
            self.native_blur_available = False
            
        except Exception as e:
            print(f"检查原生模糊支持时出错: {e}")
            self.native_blur_available = False
    
    def _apply_native_blur(self, widget: QWidget, blur_radius: int) -> bool:
        """
        应用原生 Windows 模糊效果（Mica 或 Acrylic）
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径
            
        Returns:
            是否成功应用
            
        注意：此方法为未来集成原生模糊库预留
        当前版本使用降级方案
        """
        try:
            # 获取窗口句柄
            hwnd = int(widget.winId())
            
            if self.blur_type == 'mica':
                # TODO: 集成 win32mica
                # import win32mica
                # win32mica.ApplyMica(hwnd, win32mica.MICAMODE.DARK)
                # return True
                pass
            
            elif self.blur_type == 'acrylic':
                # TODO: 集成 BlurWindow
                # from BlurWindow.blurWindow import blur
                # blur(hwnd, Acrylic=True, Dark=True)
                # return True
                pass
            
            return False
            
        except Exception as e:
            print(f"应用原生 Windows 模糊失败: {e}")
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
                print(f"Windows 原生模糊失败，降级到 PyQt5: {e}")
        
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
                    hwnd = int(widget.winId())
                    # TODO: 清理原生模糊效果
                    # 具体实现取决于使用的库
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
            是否支持（Windows 平台始终支持降级方案）
        """
        return True
    
    def get_blur_type(self) -> str:
        """
        获取当前使用的模糊类型
        
        Returns:
            'mica', 'acrylic', 或 'qt'
        """
        return self.blur_type
    
    def is_native_available(self) -> bool:
        """
        检查原生模糊是否可用
        
        Returns:
            是否可用原生模糊
        """
        return self.native_blur_available
