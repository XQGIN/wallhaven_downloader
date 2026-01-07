# -*- coding: utf-8 -*-
"""
配置管理器
提供完整的配置持久化功能，包括保存、加载、验证、错误处理和重置
"""

import os
import json
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from utils.logger import get_logger
    from ui.glass_toast import show_toast
except ImportError:
    from ..utils.logger import get_logger
    try:
        from ..ui.glass_toast import show_toast
    except ImportError:
        # 如果 glass_toast 不可用，定义一个空函数
        def show_toast(message, toast_type="info", parent=None):
            pass

logger = get_logger(__name__)


@dataclass
class ThemeConfig:
    """主题配置数据模型"""
    mode: str = "浅色"  # "浅色", "深色", "自动"
    auto_enabled: bool = False  # 是否启用自动主题
    transition_duration: int = 300  # 主题切换动画时长（毫秒）
    follow_system: bool = True  # 是否跟随系统主题
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ThemeConfig':
        """从字典创建"""
        return cls(
            mode=data.get("mode", "浅色"),
            auto_enabled=data.get("auto_enabled", False),
            transition_duration=data.get("transition_duration", 300),
            follow_system=data.get("follow_system", True)
        )


@dataclass
class GlassEffectConfig:
    """玻璃效果配置数据模型"""
    blur_radius: int = 20  # 模糊半径 (5-40px)
    transparency: float = 0.7  # 透明度 (0.6-0.95)
    border_radius: int = 12  # 圆角半径 (8-20px)
    shadow_blur: int = 20  # 阴影模糊度 (10-40px)
    edge_highlight_width: int = 2  # 边缘高光宽度 (1-2px)
    use_native_blur: bool = True  # 是否使用原生模糊
    performance_mode: bool = False  # 是否启用性能模式
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GlassEffectConfig':
        """从字典创建"""
        return cls(
            blur_radius=data.get("blur_radius", 20),
            transparency=data.get("transparency", 0.7),
            border_radius=data.get("border_radius", 12),
            shadow_blur=data.get("shadow_blur", 20),
            edge_highlight_width=data.get("edge_highlight_width", 2),
            use_native_blur=data.get("use_native_blur", True),
            performance_mode=data.get("performance_mode", False)
        )


@dataclass
class AnimationConfig:
    """动画配置数据模型"""
    enabled: bool = True  # 是否启用动画
    performance_mode: bool = False  # 是否启用性能模式
    hover_duration: int = 200  # 悬停动画时长（毫秒）
    press_duration: int = 150  # 按下动画时长（毫秒）
    transition_duration: int = 300  # 过渡动画时长（毫秒）
    reduce_motion: bool = False  # 是否减少动画（辅助功能）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnimationConfig':
        """从字典创建"""
        return cls(
            enabled=data.get("enabled", True),
            performance_mode=data.get("performance_mode", False),
            hover_duration=data.get("hover_duration", 200),
            press_duration=data.get("press_duration", 150),
            transition_duration=data.get("transition_duration", 300),
            reduce_motion=data.get("reduce_motion", False)
        )


@dataclass
class WindowConfig:
    """窗口配置数据模型"""
    x: int = 100
    y: int = 100
    width: int = 1280
    height: int = 800
    maximized: bool = False
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WindowConfig':
        """从字典创建"""
        return cls(
            x=data.get("x", 100),
            y=data.get("y", 100),
            width=data.get("width", 1280),
            height=data.get("height", 800),
            maximized=data.get("maximized", False)
        )


class ConfigurationManager:
    """
    配置管理器
    
    负责管理应用程序的所有配置，包括：
    - 主题配置
    - 玻璃效果配置
    - 动画配置
    - 窗口状态配置
    - 用户设置
    """
    
    # 默认配置
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "theme": ThemeConfig().to_dict(),
        "glass_effect": GlassEffectConfig().to_dict(),
        "animation": AnimationConfig().to_dict(),
        "window": WindowConfig().to_dict(),
        "user_settings": {
            "language": "zh_CN",
            "api_key": "",
            "download_dir": "",
            "concurrent_downloads": 10,
            "images_per_page": 64
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为程序目录下的 config.json
        """
        # 配置文件路径
        if config_file is None:
            base_path = Path(__file__).parent.parent.parent
            config_file = str(base_path / "config.json")
        
        self.config_file = Path(config_file)
        self.backup_dir = self.config_file.parent / "config_backups"
        
        # 错误状态
        self.last_error = None
        self.config_corrupted = False
        
        # 加载配置
        self.config = self._load_config()
        
        # 配置对象
        self.theme_config = ThemeConfig.from_dict(self.config.get("theme", {}))
        self.glass_effect_config = GlassEffectConfig.from_dict(self.config.get("glass_effect", {}))
        self.animation_config = AnimationConfig.from_dict(self.config.get("animation", {}))
        self.window_config = WindowConfig.from_dict(self.config.get("window", {}))
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        # 如果配置文件不存在，返回默认配置
        if not self.config_file.exists():
            logger.info("配置文件不存在，使用默认配置")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # 验证配置
            validated_config = self._validate_config(loaded_config)
            logger.info("配置加载成功")
            self.last_error = None
            self.config_corrupted = False
            return validated_config
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 JSON 格式错误: {e}")
            self.last_error = f"配置文件格式错误: {str(e)}"
            self.config_corrupted = True
            
            # 备份损坏的配置文件
            self._backup_corrupted_config()
            
            # 显示错误通知
            self._show_config_error_notification(
                "配置文件损坏",
                "配置文件格式错误，已使用默认配置。损坏的文件已备份。"
            )
            
            # 返回默认配置
            return self._get_default_config()
            
        except PermissionError as e:
            logger.error(f"配置文件权限不足: {e}")
            self.last_error = f"配置文件权限不足: {str(e)}"
            
            # 显示错误通知
            self._show_config_error_notification(
                "权限错误",
                "无法读取配置文件，权限不足。已使用默认配置。"
            )
            
            return self._get_default_config()
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.last_error = f"加载配置失败: {str(e)}"
            
            # 显示错误通知
            self._show_config_error_notification(
                "加载失败",
                f"无法加载配置文件: {str(e)}。已使用默认配置。"
            )
            
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置字典
        """
        # 深拷贝默认配置，避免修改类变量
        import copy
        config = copy.deepcopy(self.DEFAULT_CONFIG)
        
        # 设置默认下载目录
        if not config["user_settings"]["download_dir"]:
            config["user_settings"]["download_dir"] = str(Path.home() / "Pictures" / "Wallhaven")
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置的合法性
        
        Args:
            config: 待验证的配置字典
            
        Returns:
            Dict[str, Any]: 验证后的配置字典
        """
        # 从默认配置开始
        validated = self._get_default_config()
        
        # 合并加载的配置
        if isinstance(config, dict):
            # 深度合并配置
            for key in validated.keys():
                if key in config:
                    if isinstance(validated[key], dict) and isinstance(config[key], dict):
                        validated[key].update(config[key])
                    else:
                        validated[key] = config[key]
        
        # 验证主题配置
        if "theme" in validated:
            theme_data = validated["theme"]
            if theme_data.get("mode") not in ["浅色", "深色", "自动"]:
                theme_data["mode"] = "浅色"
            if not isinstance(theme_data.get("transition_duration"), int):
                theme_data["transition_duration"] = 300
            validated["theme"] = theme_data
        
        # 验证玻璃效果配置
        if "glass_effect" in validated:
            glass_data = validated["glass_effect"]
            glass_data["blur_radius"] = max(5, min(40, glass_data.get("blur_radius", 20)))
            glass_data["transparency"] = max(0.6, min(0.95, glass_data.get("transparency", 0.7)))
            glass_data["border_radius"] = max(8, min(20, glass_data.get("border_radius", 12)))
            validated["glass_effect"] = glass_data
        
        # 验证动画配置
        if "animation" in validated:
            anim_data = validated["animation"]
            anim_data["hover_duration"] = max(100, min(500, anim_data.get("hover_duration", 200)))
            anim_data["press_duration"] = max(100, min(500, anim_data.get("press_duration", 150)))
            anim_data["transition_duration"] = max(100, min(1000, anim_data.get("transition_duration", 300)))
            validated["animation"] = anim_data
        
        # 验证窗口配置
        if "window" in validated:
            window_data = validated["window"]
            window_data["width"] = max(1024, min(3840, window_data.get("width", 1280)))
            window_data["height"] = max(768, min(2160, window_data.get("height", 800)))
            validated["window"] = window_data
        
        return validated
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 更新配置字典
            self.config["theme"] = self.theme_config.to_dict()
            self.config["glass_effect"] = self.glass_effect_config.to_dict()
            self.config["animation"] = self.animation_config.to_dict()
            self.config["window"] = self.window_config.to_dict()
            
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info("配置保存成功")
            self.last_error = None
            return True
            
        except PermissionError as e:
            logger.error(f"保存配置失败，权限不足: {e}")
            self.last_error = f"权限不足: {str(e)}"
            
            # 显示错误通知
            self._show_config_error_notification(
                "保存失败",
                "无法保存配置文件，权限不足。请检查文件权限。"
            )
            
            return False
            
        except OSError as e:
            logger.error(f"保存配置失败，磁盘错误: {e}")
            self.last_error = f"磁盘错误: {str(e)}"
            
            # 显示错误通知
            self._show_config_error_notification(
                "保存失败",
                "无法保存配置文件，可能是磁盘空间不足或磁盘错误。"
            )
            
            return False
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            self.last_error = f"保存失败: {str(e)}"
            
            # 显示错误通知
            self._show_config_error_notification(
                "保存失败",
                f"无法保存配置文件: {str(e)}"
            )
            
            return False
    
    def _backup_corrupted_config(self):
        """备份损坏的配置文件"""
        try:
            if not self.config_file.exists():
                return
            
            # 创建备份目录
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_corrupted_{timestamp}.json"
            
            # 复制文件
            shutil.copy2(self.config_file, backup_file)
            logger.info(f"损坏的配置文件已备份到: {backup_file}")
            
        except Exception as e:
            logger.error(f"备份损坏的配置文件失败: {e}")
    
    def _show_config_error_notification(self, title: str, message: str):
        """
        显示配置错误通知
        
        Args:
            title: 通知标题
            message: 通知消息
        """
        try:
            # 尝试显示 Toast 通知
            show_toast(f"{title}: {message}", toast_type="error")
        except Exception as e:
            logger.warning(f"无法显示错误通知: {e}")
    
    def get_last_error(self) -> Optional[str]:
        """
        获取最后一次错误信息
        
        Returns:
            Optional[str]: 错误信息，如果没有错误则返回 None
        """
        return self.last_error
    
    def is_config_corrupted(self) -> bool:
        """
        检查配置是否损坏
        
        Returns:
            bool: 配置是否损坏
        """
        return self.config_corrupted
    
    def reset_to_default(self, backup: bool = True, notify: bool = True) -> bool:
        """
        重置为默认配置
        
        Args:
            backup: 是否备份当前配置
            notify: 是否显示通知
            
        Returns:
            bool: 重置是否成功
        """
        try:
            # 备份当前配置
            if backup and self.config_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"config_before_reset_{timestamp}.json"
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.config_file, backup_file)
                logger.info(f"当前配置已备份到: {backup_file}")
            
            # 重置配置
            self.config = self._get_default_config()
            self.theme_config = ThemeConfig.from_dict(self.config["theme"])
            self.glass_effect_config = GlassEffectConfig.from_dict(self.config["glass_effect"])
            self.animation_config = AnimationConfig.from_dict(self.config["animation"])
            self.window_config = WindowConfig.from_dict(self.config["window"])
            
            # 清除错误状态
            self.last_error = None
            self.config_corrupted = False
            
            # 保存默认配置
            success = self.save_config()
            
            if success:
                logger.info("配置已重置为默认值")
                
                # 显示成功通知
                if notify:
                    try:
                        show_toast("配置已重置为默认值", toast_type="success")
                    except Exception:
                        pass
            else:
                logger.error("重置配置后保存失败")
            
            return success
            
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            self.last_error = f"重置失败: {str(e)}"
            
            # 显示错误通知
            if notify:
                self._show_config_error_notification(
                    "重置失败",
                    f"无法重置配置: {str(e)}"
                )
            
            return False
    
    def reset_theme_to_default(self) -> bool:
        """
        仅重置主题配置为默认值
        
        Returns:
            bool: 重置是否成功
        """
        try:
            self.theme_config = ThemeConfig()
            success = self.save_config()
            
            if success:
                logger.info("主题配置已重置为默认值")
            
            return success
            
        except Exception as e:
            logger.error(f"重置主题配置失败: {e}")
            return False
    
    def reset_glass_effect_to_default(self) -> bool:
        """
        仅重置玻璃效果配置为默认值
        
        Returns:
            bool: 重置是否成功
        """
        try:
            self.glass_effect_config = GlassEffectConfig()
            success = self.save_config()
            
            if success:
                logger.info("玻璃效果配置已重置为默认值")
            
            return success
            
        except Exception as e:
            logger.error(f"重置玻璃效果配置失败: {e}")
            return False
    
    def reset_animation_to_default(self) -> bool:
        """
        仅重置动画配置为默认值
        
        Returns:
            bool: 重置是否成功
        """
        try:
            self.animation_config = AnimationConfig()
            success = self.save_config()
            
            if success:
                logger.info("动画配置已重置为默认值")
            
            return success
            
        except Exception as e:
            logger.error(f"重置动画配置失败: {e}")
            return False
    
    def reset_window_to_default(self) -> bool:
        """
        仅重置窗口配置为默认值
        
        Returns:
            bool: 重置是否成功
        """
        try:
            self.window_config = WindowConfig()
            success = self.save_config()
            
            if success:
                logger.info("窗口配置已重置为默认值")
            
            return success
            
        except Exception as e:
            logger.error(f"重置窗口配置失败: {e}")
            return False
    
    def get_theme_config(self) -> ThemeConfig:
        """获取主题配置"""
        return self.theme_config
    
    def save_theme_config(self, theme_config: ThemeConfig) -> bool:
        """
        保存主题配置
        
        Args:
            theme_config: 主题配置对象
            
        Returns:
            bool: 保存是否成功
        """
        self.theme_config = theme_config
        return self.save_config()
    
    def get_glass_effect_config(self) -> GlassEffectConfig:
        """获取玻璃效果配置"""
        return self.glass_effect_config
    
    def save_glass_effect_config(self, glass_config: GlassEffectConfig) -> bool:
        """
        保存玻璃效果配置
        
        Args:
            glass_config: 玻璃效果配置对象
            
        Returns:
            bool: 保存是否成功
        """
        self.glass_effect_config = glass_config
        return self.save_config()
    
    def get_animation_config(self) -> AnimationConfig:
        """获取动画配置"""
        return self.animation_config
    
    def save_animation_config(self, animation_config: AnimationConfig) -> bool:
        """
        保存动画配置
        
        Args:
            animation_config: 动画配置对象
            
        Returns:
            bool: 保存是否成功
        """
        self.animation_config = animation_config
        return self.save_config()
    
    def get_window_config(self) -> WindowConfig:
        """获取窗口配置"""
        return self.window_config
    
    def save_window_config(self, window_config: WindowConfig) -> bool:
        """
        保存窗口配置
        
        Args:
            window_config: 窗口配置对象
            
        Returns:
            bool: 保存是否成功
        """
        self.window_config = window_config
        return self.save_config()
    
    def get_user_setting(self, key: str, default: Any = None) -> Any:
        """
        获取用户设置
        
        Args:
            key: 设置键
            default: 默认值
            
        Returns:
            Any: 设置值
        """
        return self.config.get("user_settings", {}).get(key, default)
    
    def set_user_setting(self, key: str, value: Any) -> bool:
        """
        设置用户设置
        
        Args:
            key: 设置键
            value: 设置值
            
        Returns:
            bool: 保存是否成功
        """
        if "user_settings" not in self.config:
            self.config["user_settings"] = {}
        
        self.config["user_settings"][key] = value
        return self.save_config()


# 全局配置管理器实例
_config_manager_instance = None


def get_configuration_manager(config_file: Optional[str] = None) -> ConfigurationManager:
    """
    获取配置管理器单例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        ConfigurationManager: 配置管理器实例
    """
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigurationManager(config_file)
    return _config_manager_instance
