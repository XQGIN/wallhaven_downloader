# -*- coding: utf-8 -*-
"""
异常处理模块
提供统一的异常处理和错误报告机制
"""

from typing import Optional, Callable, Any
from functools import wraps
from utils.logger import get_logger

logger = get_logger(__name__)


class WallhavenException(Exception):
    """Wallhaven下载器基础异常类"""
    pass


class NetworkException(WallhavenException):
    """网络相关异常"""
    pass


class DownloadException(WallhavenException):
    """下载相关异常"""
    pass


class ConfigException(WallhavenException):
    """配置相关异常"""
    pass


class UIException(WallhavenException):
    """UI相关异常"""
    pass


def handle_exception(
    error_message: str = "操作失败",
    default_return: Any = None,
    raise_exception: bool = False,
    log_level: str = "error"
):
    """
    异常处理装饰器
    
    Args:
        error_message: 错误消息
        default_return: 异常时的默认返回值
        raise_exception: 是否重新抛出异常
        log_level: 日志级别 (debug, info, warning, error, critical)
    
    Example:
        @handle_exception("配置保存失败", default_return=False)
        def save_config(self, config):
            # 保存配置的代码
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 记录日志
                log_func = getattr(logger, log_level, logger.error)
                log_func(f"{error_message}: {str(e)}", exc_info=True)
                
                # 是否重新抛出异常
                if raise_exception:
                    raise
                
                return default_return
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    error_message: str = "执行失败",
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    安全执行函数，捕获所有异常
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        error_message: 错误消息
        default_return: 异常时的默认返回值
        **kwargs: 关键字参数
    
    Returns:
        函数执行结果或默认返回值
    
    Example:
        result = safe_execute(
            risky_function,
            arg1, arg2,
            error_message="风险操作失败",
            default_return=[]
        )
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}", exc_info=True)
        return default_return


class ExceptionHandler:
    """异常处理上下文管理器"""
    
    def __init__(
        self,
        error_message: str = "操作失败",
        suppress: bool = True,
        callback: Optional[Callable] = None
    ):
        """
        初始化异常处理器
        
        Args:
            error_message: 错误消息
            suppress: 是否抑制异常
            callback: 异常发生时的回调函数
        """
        self.error_message = error_message
        self.suppress = suppress
        self.callback = callback
        self.exception: Optional[Exception] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.exception = exc_val
            logger.error(f"{self.error_message}: {str(exc_val)}", exc_info=True)
            
            # 调用回调函数
            if self.callback:
                try:
                    self.callback(exc_val)
                except Exception as e:
                    logger.error(f"异常回调函数执行失败: {str(e)}")
            
            # 返回True抑制异常，False重新抛出
            return self.suppress
        
        return False


def validate_input(
    value: Any,
    value_type: type,
    min_value: Optional[Any] = None,
    max_value: Optional[Any] = None,
    allowed_values: Optional[list] = None,
    error_message: str = "输入验证失败"
) -> Any:
    """
    输入验证
    
    Args:
        value: 要验证的值
        value_type: 期望的类型
        min_value: 最小值
        max_value: 最大值
        allowed_values: 允许的值列表
        error_message: 错误消息
    
    Returns:
        验证后的值
    
    Raises:
        ValueError: 验证失败时抛出
    
    Example:
        page_count = validate_input(
            user_input,
            int,
            min_value=1,
            max_value=100,
            error_message="页数必须在1-100之间"
        )
    """
    # 类型检查
    if not isinstance(value, value_type):
        try:
            value = value_type(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"{error_message}: 类型错误，期望{value_type.__name__}") from e
    
    # 范围检查
    if min_value is not None and value < min_value:
        raise ValueError(f"{error_message}: 值不能小于{min_value}")
    
    if max_value is not None and value > max_value:
        raise ValueError(f"{error_message}: 值不能大于{max_value}")
    
    # 允许值检查
    if allowed_values is not None and value not in allowed_values:
        raise ValueError(f"{error_message}: 值必须在{allowed_values}中")
    
    return value
