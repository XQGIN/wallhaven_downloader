# -*- coding: utf-8 -*-
"""
设置管理器
提供统一的配置管理功能，支持环境变量覆盖和验证
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

try:
    from utils.logger import get_logger
    from core.theme_manager import get_theme_manager
    from core.i18n_manager import get_i18n_manager
except ImportError:
    from ..utils.logger import get_logger
    from .theme_manager import get_theme_manager
    from .i18n_manager import get_i18n_manager

logger = get_logger(__name__)


class SettingsManager:
    """设置管理器类"""
    
    # 默认设置
    DEFAULT_SETTINGS = {
        "api_key": "",  # 移除硬编码的API Key，用户需自行配置
        "theme": "浅色",
        "glass_transparency": 200,
        "images_per_page": 64,
        "download_timeout": 30,
        "concurrent_downloads": 3,
        "preview_size": "中 (200x200)",
        "download_dir": "",  # 将在初始化时设置
        "download_method": "latest",
        "category": "all",
        "purity": "sfw",
        "search_query": "",
        "page_count": 1,
        "wallpaper_ratio": "全部",
        "start_page": 1,
        "show_filename": False,
        "log_level": "INFO",
        "language": "zh_CN"  # 默认语言
    }
    
    # 设置验证规则
    VALIDATION_RULES = {
        "glass_transparency": (100, 255),
        "images_per_page": (1, 100),
        "download_timeout": (5, 300),
        "concurrent_downloads": (1, 10),
        "page_count": (1, 999999),
        "start_page": (1, 999999)
    }
    
    def __init__(self, settings_file: Optional[str] = None):
        """
        初始化设置管理器
        
        Args:
            settings_file: 设置文件路径，默认为程序目录下的settings.json
        """
        # 加载环境变量
        load_dotenv()
        
        # 设置文件路径 - 使用 pathlib 提升可读性
        if settings_file is None:
            from utils.resource_helper import get_resources_dir
            settings_file = os.path.join(get_resources_dir(), "settings.json")
        
        self.settings_file = settings_file
        self.settings = self._load_settings()
        
        # 初始化主题管理器
        self.theme_manager = get_theme_manager()
        self._apply_theme_from_settings()
        
        # 初始化国际化管理器
        self.i18n_manager = get_i18n_manager()
        self._apply_language_from_settings()
    
    def _get_default_download_dir(self) -> str:
        """获取默认下载目录"""
        return str(Path.home() / "Pictures" / "Wallhaven")
    
    def _load_settings(self) -> Dict[str, Any]:
        """
        加载设置
        
        Returns:
            Dict[str, Any]: 设置字典
        """
        # 复制默认设置
        settings = self.DEFAULT_SETTINGS.copy()
        
        # 设置默认下载目录
        if not settings["download_dir"]:
            settings["download_dir"] = self._get_default_download_dir()
        
        # 如果设置文件存在，加载设置
        settings_path = Path(self.settings_file)
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # 合并设置，保留已加载的设置
                settings.update(loaded_settings)
            except json.JSONDecodeError as e:
                logger.error(f"JSON 格式错误: {e}")
            except Exception as e:
                logger.error(f"加载设置文件失败: {e}")
        
        # 从环境变量覆盖敏感信息
        env_api_key = os.getenv('WALLHAVEN_API_KEY')
        if env_api_key:
            settings["api_key"] = env_api_key
        
        env_log_level = os.getenv('LOG_LEVEL')
        if env_log_level:
            settings["log_level"] = env_log_level
        
        # 验证设置
        settings = self._validate_settings(settings)
        
        return settings
    
    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证设置值的合法性
        
        Args:
            settings: 待验证的设置字典
            
        Returns:
            Dict[str, Any]: 验证后的设置字典
        """
        validated = settings.copy()
        
        for key, (min_val, max_val) in self.VALIDATION_RULES.items():
            if key in validated:
                value = validated[key]
                if not isinstance(value, (int, float)):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = self.DEFAULT_SETTINGS[key]
                
                # 限制在合法范围内
                validated[key] = max(min_val, min(max_val, value))
        
        # 验证主题，仅保留浅色
        if validated.get("theme") != "浅色":
            validated["theme"] = "浅色"
        
        # 验证预览大小
        if validated.get("preview_size") not in ["小 (150x150)", "中 (200x200)", "大 (300x300)"]:
            validated["preview_size"] = "中 (200x200)"
        
        # 验证下载方式
        if validated.get("download_method") not in ["latest", "category", "search"]:
            validated["download_method"] = "latest"
        
        # 验证语言
        if validated.get("language") not in ["zh_CN", "en_US"]:
            validated["language"] = "zh_CN"
        
        return validated
    
    def save_settings(self) -> bool:
        """
        保存设置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            settings_path = Path(self.settings_file)
            # 确保目录存在
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            
            logger.info("设置保存成功")
            return True
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取设置值
        
        Args:
            key: 设置键
            default: 默认值
            
        Returns:
            Any: 设置值
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置值
        
        Args:
            key: 设置键
            value: 设置值
        """
        self.settings[key] = value
        
        # 如果修改了主题设置，应用主题
        if key == "theme":
            self._apply_theme_from_settings()
    
    def update(self, new_settings: Dict[str, Any]) -> None:
        """
        批量更新设置
        
        Args:
            new_settings: 新设置字典
        """
        self.settings.update(new_settings)
        self.settings = self._validate_settings(self.settings)
    
    def reset_to_default(self) -> None:
        """重置为默认设置"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        if not self.settings["download_dir"]:
            self.settings["download_dir"] = self._get_default_download_dir()
    
    def export_settings(self, export_file: str) -> bool:
        """
        导出设置到指定文件
        
        Args:
            export_file: 导出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            export_path = Path(export_file)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logger.info(f"设置已导出到: {export_file}")
            return True
        except Exception as e:
            logger.error(f"导出设置失败: {e}")
            return False
    
    def import_settings(self, import_file: str) -> bool:
        """
        从指定文件导入设置
        
        Args:
            import_file: 导入文件路径
            
        Returns:
            bool: 导入是否成功
        """
        try:
            import_path = Path(import_file)
            if not import_path.exists():
                logger.error(f"导入文件不存在: {import_file}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            self.settings.update(imported_settings)
            self.settings = self._validate_settings(self.settings)
            self._apply_theme_from_settings()
            logger.info(f"设置已从 {import_file} 导入")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"JSON 格式错误: {e}")
            return False
        except Exception as e:
            logger.error(f"导入设置失败: {e}")
            return False
    
    def _apply_theme_from_settings(self) -> None:
        """从设置中应用主题"""
        theme = self.settings.get("theme", "浅色")
        self.theme_manager.set_theme(theme)
        logger.debug(f"应用主题: {theme}")
    
    def _apply_language_from_settings(self) -> None:
        """从设置中应用语言"""
        language = self.settings.get("language", "zh_CN")
        self.i18n_manager.set_language(language)
        logger.debug(f"应用语言: {language}")
