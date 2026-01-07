"""
系统辅助功能检测器

检测操作系统的辅助功能设置，如减少动画、高对比度等
"""

import sys
import platform
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

try:
    from utils.logger import get_logger
except ImportError:
    from .logger import get_logger

logger = get_logger(__name__)


class SystemAccessibilityDetector(QObject):
    """
    系统辅助功能检测器
    
    检测操作系统的辅助功能设置：
    - 减少动画（Reduce Motion）
    - 高对比度（High Contrast）
    - 屏幕阅读器（Screen Reader）
    
    需求：16.5 - 检测系统辅助功能设置，遵循减少动画选项
    """
    
    # 信号
    reduce_motion_changed = pyqtSignal(bool)  # 减少动画设置变化
    high_contrast_changed = pyqtSignal(bool)  # 高对比度设置变化
    screen_reader_changed = pyqtSignal(bool)  # 屏幕阅读器状态变化
    
    # 单例实例
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        super().__init__()
        self._initialized = True
        
        # 当前状态
        self._reduce_motion = False
        self._high_contrast = False
        self._screen_reader_active = False
        
        # 操作系统
        self._os_name = platform.system()
        
        # 定时检查器（每 5 秒检查一次）
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_settings)
        self._check_timer.setInterval(5000)
        
        # 初始检测
        self._detect_initial_settings()
        
        logger.info(f"系统辅助功能检测器初始化完成 (OS: {self._os_name})")
    
    def _detect_initial_settings(self):
        """初始检测系统辅助功能设置"""
        self._reduce_motion = self._detect_reduce_motion()
        self._high_contrast = self._detect_high_contrast()
        self._screen_reader_active = self._detect_screen_reader()
        
        logger.info(f"初始辅助功能设置: 减少动画={self._reduce_motion}, "
                   f"高对比度={self._high_contrast}, 屏幕阅读器={self._screen_reader_active}")
    
    def _detect_reduce_motion(self) -> bool:
        """
        检测系统是否启用了减少动画选项
        
        Returns:
            bool: 是否启用减少动画
        """
        try:
            if self._os_name == "Windows":
                return self._detect_reduce_motion_windows()
            elif self._os_name == "Darwin":  # macOS
                return self._detect_reduce_motion_macos()
            elif self._os_name == "Linux":
                return self._detect_reduce_motion_linux()
            else:
                logger.warning(f"不支持的操作系统: {self._os_name}")
                return False
        except Exception as e:
            logger.error(f"检测减少动画设置失败: {e}")
            return False
    
    def _detect_reduce_motion_windows(self) -> bool:
        """
        检测 Windows 系统的减少动画设置
        
        Windows 10/11: 设置 > 轻松使用 > 显示 > 在 Windows 中显示动画
        
        Returns:
            bool: 是否启用减少动画
        """
        try:
            import winreg
            
            # 读取注册表
            key_path = r"Control Panel\Desktop\WindowMetrics"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            
            try:
                # MinAnimate 值：0 = 禁用动画，1 = 启用动画
                value, value_type = winreg.QueryValueEx(key, "MinAnimate")
                winreg.CloseKey(key)
                
                logger.debug(f"Windows MinAnimate 注册表值: {value} (类型: {value_type}, 实际类型: {type(value).__name__})")
                
                # 转换为字符串进行比较，返回 True 表示减少动画（即禁用动画）
                result = str(value) == "0"
                logger.debug(f"减少动画检测结果: {result}")
                return result
            except FileNotFoundError:
                winreg.CloseKey(key)
                logger.debug("MinAnimate 注册表键不存在")
                return False
                
        except Exception as e:
            logger.debug(f"Windows 减少动画检测失败: {e}")
            return False
    
    def _detect_reduce_motion_macos(self) -> bool:
        """
        检测 macOS 系统的减少动画设置
        
        macOS: 系统偏好设置 > 辅助功能 > 显示 > 减少动态效果
        
        Returns:
            bool: 是否启用减少动画
        """
        try:
            import subprocess
            
            # 使用 defaults 命令读取设置
            result = subprocess.run(
                ["defaults", "read", "com.apple.universalaccess", "reduceMotion"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # 返回值为 1 表示启用减少动画
            return result.stdout.strip() == "1"
            
        except Exception as e:
            logger.debug(f"macOS 减少动画检测失败: {e}")
            return False
    
    def _detect_reduce_motion_linux(self) -> bool:
        """
        检测 Linux 系统的减少动画设置
        
        GNOME: gsettings get org.gnome.desktop.interface enable-animations
        KDE: kreadconfig5 --group KDE --key AnimationDurationFactor
        
        Returns:
            bool: 是否启用减少动画
        """
        try:
            import subprocess
            
            # 尝试 GNOME
            try:
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "enable-animations"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                # false 表示禁用动画
                if "false" in result.stdout.lower():
                    return True
            except:
                pass
            
            # 尝试 KDE
            try:
                result = subprocess.run(
                    ["kreadconfig5", "--group", "KDE", "--key", "AnimationDurationFactor"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                # 0 表示禁用动画
                if result.stdout.strip() == "0":
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.debug(f"Linux 减少动画检测失败: {e}")
            return False
    
    def _detect_high_contrast(self) -> bool:
        """
        检测系统是否启用了高对比度模式
        
        Returns:
            bool: 是否启用高对比度
        """
        try:
            if self._os_name == "Windows":
                return self._detect_high_contrast_windows()
            elif self._os_name == "Darwin":  # macOS
                return self._detect_high_contrast_macos()
            elif self._os_name == "Linux":
                return self._detect_high_contrast_linux()
            else:
                return False
        except Exception as e:
            logger.error(f"检测高对比度设置失败: {e}")
            return False
    
    def _detect_high_contrast_windows(self) -> bool:
        """检测 Windows 高对比度模式"""
        try:
            import winreg
            
            key_path = r"Control Panel\Accessibility\HighContrast"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            
            try:
                # Flags 值的第 0 位表示是否启用高对比度
                value, _ = winreg.QueryValueEx(key, "Flags")
                winreg.CloseKey(key)
                
                return (int(value) & 1) == 1
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
                
        except Exception as e:
            logger.debug(f"Windows 高对比度检测失败: {e}")
            return False
    
    def _detect_high_contrast_macos(self) -> bool:
        """检测 macOS 高对比度模式"""
        try:
            import subprocess
            
            result = subprocess.run(
                ["defaults", "read", "com.apple.universalaccess", "increaseContrast"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            return result.stdout.strip() == "1"
            
        except Exception as e:
            logger.debug(f"macOS 高对比度检测失败: {e}")
            return False
    
    def _detect_high_contrast_linux(self) -> bool:
        """检测 Linux 高对比度模式"""
        try:
            import subprocess
            
            # GNOME
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.a11y.interface", "high-contrast"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            return "true" in result.stdout.lower()
            
        except Exception as e:
            logger.debug(f"Linux 高对比度检测失败: {e}")
            return False
    
    def _detect_screen_reader(self) -> bool:
        """
        检测屏幕阅读器是否活动
        
        Returns:
            bool: 屏幕阅读器是否活动
        """
        try:
            if self._os_name == "Windows":
                return self._detect_screen_reader_windows()
            elif self._os_name == "Darwin":  # macOS
                return self._detect_screen_reader_macos()
            elif self._os_name == "Linux":
                return self._detect_screen_reader_linux()
            else:
                return False
        except Exception as e:
            logger.error(f"检测屏幕阅读器失败: {e}")
            return False
    
    def _detect_screen_reader_windows(self) -> bool:
        """检测 Windows 屏幕阅读器（Narrator, JAWS, NVDA）"""
        try:
            import psutil
            
            # 常见的屏幕阅读器进程名
            screen_readers = ["Narrator.exe", "nvda.exe", "jaws.exe", "JAWS.exe"]
            
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] in screen_readers:
                        return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            logger.debug(f"Windows 屏幕阅读器检测失败: {e}")
            return False
    
    def _detect_screen_reader_macos(self) -> bool:
        """检测 macOS 屏幕阅读器（VoiceOver）"""
        try:
            import subprocess
            
            result = subprocess.run(
                ["defaults", "read", "com.apple.universalaccess", "voiceOverOnOffKey"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"macOS 屏幕阅读器检测失败: {e}")
            return False
    
    def _detect_screen_reader_linux(self) -> bool:
        """检测 Linux 屏幕阅读器（Orca）"""
        try:
            import psutil
            
            for proc in psutil.process_iter(['name']):
                try:
                    if 'orca' in proc.info['name'].lower():
                        return True
                except:
                    pass
            
            return False
            
        except Exception as e:
            logger.debug(f"Linux 屏幕阅读器检测失败: {e}")
            return False
    
    def _check_settings(self):
        """定期检查设置变化"""
        # 检查减少动画
        new_reduce_motion = self._detect_reduce_motion()
        if new_reduce_motion != self._reduce_motion:
            self._reduce_motion = new_reduce_motion
            self.reduce_motion_changed.emit(new_reduce_motion)
            logger.info(f"减少动画设置已变化: {new_reduce_motion}")
        
        # 检查高对比度
        new_high_contrast = self._detect_high_contrast()
        if new_high_contrast != self._high_contrast:
            self._high_contrast = new_high_contrast
            self.high_contrast_changed.emit(new_high_contrast)
            logger.info(f"高对比度设置已变化: {new_high_contrast}")
        
        # 检查屏幕阅读器
        new_screen_reader = self._detect_screen_reader()
        if new_screen_reader != self._screen_reader_active:
            self._screen_reader_active = new_screen_reader
            self.screen_reader_changed.emit(new_screen_reader)
            logger.info(f"屏幕阅读器状态已变化: {new_screen_reader}")
    
    def start_monitoring(self):
        """开始监控系统辅助功能设置"""
        if not self._check_timer.isActive():
            self._check_timer.start()
            logger.info("开始监控系统辅助功能设置")
    
    def stop_monitoring(self):
        """停止监控系统辅助功能设置"""
        if self._check_timer.isActive():
            self._check_timer.stop()
            logger.info("停止监控系统辅助功能设置")
    
    def is_reduce_motion_enabled(self) -> bool:
        """
        是否启用减少动画
        
        Returns:
            bool: 是否启用减少动画
        """
        return self._reduce_motion
    
    def is_high_contrast_enabled(self) -> bool:
        """
        是否启用高对比度
        
        Returns:
            bool: 是否启用高对比度
        """
        return self._high_contrast
    
    def is_screen_reader_active(self) -> bool:
        """
        屏幕阅读器是否活动
        
        Returns:
            bool: 屏幕阅读器是否活动
        """
        return self._screen_reader_active
    
    def force_check(self):
        """强制检查当前设置"""
        self._check_settings()


# 全局访问函数
_detector = None

def get_system_accessibility_detector() -> SystemAccessibilityDetector:
    """获取系统辅助功能检测器单例"""
    global _detector
    if _detector is None:
        _detector = SystemAccessibilityDetector()
    return _detector
