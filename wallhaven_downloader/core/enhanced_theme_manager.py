# -*- coding: utf-8 -*-
"""
增强主题管理器
扩展现有 ThemeManager，添加苹果风格颜色方案和主题过渡
"""

import json
import os
from typing import Optional, Dict
from PyQt5.QtCore import QTimer, pyqtSignal

try:
    from core.theme_manager import ThemeManager, ThemeMode
    from core.apple_color_palette import AppleColorPalette
    from core.theme_transition_manager import ThemeTransitionManager
    from utils.logger import get_logger
except ImportError:
    from .theme_manager import ThemeManager, ThemeMode
    from .apple_color_palette import AppleColorPalette
    from .theme_transition_manager import ThemeTransitionManager
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedThemeManager(ThemeManager):
    """
    增强主题管理器
    
    扩展现有 ThemeManager，添加：
    - 苹果风格颜色方案
    - 主题过渡动画
    - 自动主题跟随系统
    - 主题配置持久化
    """
    
    # 主题过渡完成信号
    transition_completed = pyqtSignal()
    
    def __init__(self):
        """初始化增强主题管理器"""
        super().__init__()
        
        # 集成苹果颜色调色板
        self.apple_palette = AppleColorPalette()
        
        # 集成主题过渡管理器
        self.transition_manager = ThemeTransitionManager()
        
        # 自动主题相关
        self.auto_theme_enabled = False
        self.system_theme_timer: Optional[QTimer] = None
        
        # 配置文件路径
        self.config_file = self._get_config_file_path()
        
        # 加载保存的主题配置
        self._load_theme_config()
        
        logger.info("增强主题管理器初始化完成")
    
    def _get_config_file_path(self) -> str:
        """
        获取配置文件路径
        
        Returns:
            str: 配置文件完整路径
        """
        # 使用用户主目录下的配置目录
        config_dir = os.path.expanduser("~/.wallhaven_downloader")
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        return os.path.join(config_dir, "theme_config.json")
    
    def set_theme_with_transition(self, theme: str, duration: int = 300):
        """
        设置主题并应用过渡动画（仅浅色，占位保持接口）
        """
        old_theme = self.get_current_theme()
        self.set_theme(ThemeMode.LIGHT.value)
        new_theme = self.get_current_theme()
        
        if old_theme == new_theme:
            self.transition_completed.emit()
            return
        
        logger.info(f"开始主题过渡: {old_theme} -> {new_theme}, 时长: {duration}ms")
        
        old_colors = self._get_theme_colors(old_theme)
        new_colors = self._get_theme_colors(new_theme)
        
        self.transition_manager.start_transition(
            old_colors,
            new_colors,
            duration
        )
        
        self.transition_manager.transition_completed.connect(
            self._on_transition_completed
        )
    
    def _get_theme_colors(self, theme: str) -> Dict:
        """
        获取指定主题的颜色方案
        
        Args:
            theme: 主题名称
            
        Returns:
            Dict: 颜色字典
        """
        return self.apple_palette.get_all_colors(is_dark_mode=False)
    
    def _on_transition_completed(self):
        """主题过渡完成回调"""
        logger.info("主题过渡完成")
        
        # 断开信号连接
        try:
            self.transition_manager.transition_completed.disconnect(
                self._on_transition_completed
            )
        except Exception:
            pass
        
        # 发射过渡完成信号
        self.transition_completed.emit()
    
    def enable_auto_theme(self):
        """启用自动主题（跟随系统）"""
        self.auto_theme_enabled = False
        logger.info("自动主题已禁用，仅保留浅色模式")
        self.set_theme_with_transition(ThemeMode.LIGHT.value)
        self._save_theme_config()
    
    def disable_auto_theme(self):
        """禁用自动主题"""
        self.auto_theme_enabled = False
        if self.system_theme_timer is not None:
            self.system_theme_timer.stop()
        logger.info("禁用自动主题模式，已固定浅色主题")
        self.set_theme_with_transition(ThemeMode.LIGHT.value)
        self._save_theme_config()
    
    def get_apple_color(self, color_name: str) -> 'QColor':
        """
        获取苹果风格颜色
        
        Args:
            color_name: 颜色名称
            
        Returns:
            QColor: 颜色对象
        """
        return self.apple_palette.get_color(
            color_name,
            is_dark_mode=self.is_dark_mode()
        )
    
    def check_system_theme_change(self):
        """检查系统主题是否变化"""
        self.auto_theme_enabled = False
        self.set_theme_with_transition(ThemeMode.LIGHT.value)
    
    def _save_theme_config(self):
        """保存主题配置到文件"""
        try:
            config = {
                "mode": self.get_current_theme(),
                "auto_enabled": False,
                "transition_duration": 300,
                "follow_system": False
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"主题配置已保存: {config}")
        
        except Exception as e:
            logger.error(f"保存主题配置失败: {e}")
    
    def _load_theme_config(self):
        """从文件加载主题配置"""
        try:
            if not os.path.exists(self.config_file):
                logger.debug("主题配置文件不存在，使用默认配置")
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.debug(f"加载主题配置: {config}")
            
            # 应用配置
            mode = ThemeMode.LIGHT.value
            self.set_theme(mode)
        
        except Exception as e:
            logger.error(f"加载主题配置失败: {e}，使用默认配置")
    
    def get_theme_config(self) -> Dict:
        """
        获取当前主题配置
        
        Returns:
            Dict: 主题配置字典
        """
        return {
            "mode": self.get_current_theme(),
            "auto_enabled": self.auto_theme_enabled,
            "transition_duration": 300,
            "follow_system": self.auto_theme_enabled
        }
    
    def set_theme_config(self, config: Dict):
        """
        设置主题配置
        
        Args:
            config: 主题配置字典
        """
        mode = config.get("mode", ThemeMode.LIGHT.value)
        auto_enabled = config.get("auto_enabled", False)
        
        if auto_enabled:
            self.enable_auto_theme()
        else:
            self.disable_auto_theme()
            self.set_theme_with_transition(mode)


# 全局增强主题管理器实例
_enhanced_theme_manager_instance: Optional[EnhancedThemeManager] = None


def get_enhanced_theme_manager() -> EnhancedThemeManager:
    """
    获取全局增强主题管理器实例（单例模式）
    
    Returns:
        EnhancedThemeManager: 增强主题管理器实例
    """
    global _enhanced_theme_manager_instance
    if _enhanced_theme_manager_instance is None:
        _enhanced_theme_manager_instance = EnhancedThemeManager()
    return _enhanced_theme_manager_instance
