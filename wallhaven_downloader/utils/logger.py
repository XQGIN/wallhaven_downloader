# -*- coding: utf-8 -*-
"""
日志管理模块
提供统一的日志记录功能
"""

import os
import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days"
) -> None:
    """
    设置日志系统
    
    Args:
        log_dir: 日志目录路径，默认为程序目录下的logs文件夹
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    # 移除默认的控制台输出
    logger.remove()
    
    # 确定日志目录
    if log_dir is None:
        try:
            # PyInstaller打包后的路径
            base_path = sys._MEIPASS
        except Exception:
            # 开发环境路径
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        log_dir = os.path.join(base_path, "..", "logs")
    
    # 创建日志目录
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    console_target = sys.stdout or getattr(sys, "__stdout__", None)
    if console_target:
        logger.add(
            console_target,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # 文件输出 - 详细格式
    log_file = os.path.join(log_dir, "wallhaven_{time:YYYY-MM-DD}.log")
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    # 错误日志单独记录
    error_log_file = os.path.join(log_dir, "error_{time:YYYY-MM-DD}.log")
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=rotation,
        retention=retention,
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    
    logger.info("日志系统初始化成功")
    logger.info(f"日志目录: {log_dir}")
    logger.info(f"日志级别: {log_level}")


def get_logger(name: Optional[str] = None):
    """
    获取logger实例
    
    Args:
        name: logger名称（可选）
        
    Returns:
        logger实例
    """
    if name:
        return logger.bind(name=name)
    return logger


# 默认导出
__all__ = ['setup_logger', 'get_logger', 'logger']
