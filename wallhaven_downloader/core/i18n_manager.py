# -*- coding: utf-8 -*-
"""
国际化管理器
提供多语言支持，支持中英文切换
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal

try:
    from utils.logger import get_logger
except ImportError:
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class I18nManager(QObject):
    """国际化管理器"""
    
    # 语言变更信号
    language_changed = pyqtSignal(str)
    
    # 支持的语言
    SUPPORTED_LANGUAGES = {
        "zh_CN": "简体中文",
        "en_US": "English"
    }
    
    def __init__(self, locale_dir: Optional[str] = None, default_language: str = "zh_CN"):
        """
        初始化国际化管理器
        
        Args:
            locale_dir: 翻译文件目录路径
            default_language: 默认语言，zh_CN或en_US
        """
        super().__init__()
        
        # 设置翻译文件目录
        if locale_dir is None:
            base_path = Path(__file__).parent.parent.parent
            locale_dir = str(base_path / "locales")
        
        self.locale_dir = locale_dir
        self.current_language = default_language
        self.translations: Dict[str, Any] = {}
        
        # 加载翻译
        self._load_translations()
    
    def _load_translations(self) -> None:
        """加载当前语言的翻译文件"""
        try:
            locale_file = Path(self.locale_dir) / f"{self.current_language}.json"
            
            if not locale_file.exists():
                logger.warning(f"翻译文件不存在: {locale_file}，使用默认语言")
                # 尝试加载默认语言
                if self.current_language != "zh_CN":
                    self.current_language = "zh_CN"
                    locale_file = Path(self.locale_dir) / f"{self.current_language}.json"
            
            if locale_file.exists():
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                logger.info(f"成功加载翻译文件: {self.current_language}")
            else:
                logger.error(f"无法加载任何翻译文件")
                self.translations = {}
                
        except json.JSONDecodeError as e:
            logger.error(f"翻译文件JSON格式错误: {e}")
            self.translations = {}
        except Exception as e:
            logger.error(f"加载翻译文件失败: {e}")
            self.translations = {}
    
    def set_language(self, language: str) -> bool:
        """
        设置当前语言
        
        Args:
            language: 语言代码，zh_CN或en_US
            
        Returns:
            bool: 设置是否成功
        """
        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"不支持的语言: {language}")
            return False
        
        if language == self.current_language:
            return True
        
        self.current_language = language
        self._load_translations()
        
        # 发射语言变更信号
        self.language_changed.emit(language)
        logger.info(f"语言已切换到: {self.SUPPORTED_LANGUAGES[language]}")
        
        return True
    
    def get_current_language(self) -> str:
        """获取当前语言代码"""
        return self.current_language
    
    def get_current_language_name(self) -> str:
        """获取当前语言显示名称"""
        return self.SUPPORTED_LANGUAGES.get(self.current_language, "未知")
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def t(self, key: str, **kwargs) -> str:
        """
        翻译指定键的文本
        
        Args:
            key: 翻译键，支持嵌套键，如 "menu.file.open"
            **kwargs: 用于字符串格式化的参数
            
        Returns:
            str: 翻译后的文本，如果找不到则返回键本身
        """
        try:
            # 支持嵌套键
            keys = key.split('.')
            value = self.translations
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break
            
            if value is None:
                logger.debug(f"翻译键未找到: {key}")
                return key
            
            # 如果是字符串，进行格式化
            if isinstance(value, str) and kwargs:
                try:
                    return value.format(**kwargs)
                except KeyError as e:
                    logger.warning(f"翻译格式化参数缺失: {key}, {e}")
                    return value
            
            return str(value) if value is not None else key
            
        except Exception as e:
            logger.error(f"翻译失败: {key}, {e}")
            return key
    
    def has_translation(self, key: str) -> bool:
        """
        检查是否存在指定键的翻译
        
        Args:
            key: 翻译键
            
        Returns:
            bool: 是否存在翻译
        """
        try:
            keys = key.split('.')
            value = self.translations
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return False
            
            return value is not None
        except Exception:
            return False


# 全局单例
_i18n_manager = None


def get_i18n_manager(locale_dir: Optional[str] = None, default_language: str = "zh_CN") -> I18nManager:
    """
    获取国际化管理器单例
    
    Args:
        locale_dir: 翻译文件目录路径（仅首次调用时有效）
        default_language: 默认语言（仅首次调用时有效）
        
    Returns:
        I18nManager: 国际化管理器实例
    """
    global _i18n_manager
    
    if _i18n_manager is None:
        _i18n_manager = I18nManager(locale_dir, default_language)
    
    return _i18n_manager
