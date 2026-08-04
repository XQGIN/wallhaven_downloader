# -*- coding: utf-8 -*-
"""
性能降级策略

定义各种降级策略，用于在性能不足时降低视觉效果质量
需求：14.6
"""

from typing import Optional, Dict, Any

try:
    from utils.logger import get_logger
except ImportError:
    from .logger import get_logger

logger = get_logger(__name__)


class DegradationStrategy:
    """
    降级策略基类
    
    定义降级策略的通用接口
    """
    
    def __init__(self, name: str):
        """
        初始化降级策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        self.applied = False
    
    def apply(self, context: Dict[str, Any]):
        """
        应用降级策略
        
        Args:
            context: 上下文信息（包含需要降级的组件引用）
        """
        raise NotImplementedError
    
    def revert(self, context: Dict[str, Any]):
        """
        恢复降级策略
        
        Args:
            context: 上下文信息
        """
        raise NotImplementedError
    
    def is_applied(self) -> bool:
        """
        检查策略是否已应用
        
        Returns:
            是否已应用
        """
        return self.applied


class ReduceBlurQualityStrategy(DegradationStrategy):
    """
    降低模糊质量策略
    
    降低液态玻璃的模糊半径和质量
    需求：14.6
    """
    
    def __init__(self):
        super().__init__("reduce_blur_quality")
        self._original_config = {}
    
    def apply(self, context: Dict[str, Any]):
        """
        应用策略：降低模糊质量
        
        Args:
            context: 包含 'liquid_glass_manager' 的上下文
        """
        liquid_glass_manager = context.get('liquid_glass_manager')
        if not liquid_glass_manager:
            logger.warning("未找到液态玻璃管理器，无法应用模糊降级")
            return
        
        try:
            # 保存原始配置
            self._original_config = {
                'blur_radius': liquid_glass_manager.blur_radius,
                'transparency': liquid_glass_manager.transparency,
                'blur_quality': liquid_glass_manager.blur_quality
            }
            
            # 应用低质量配置
            liquid_glass_manager.set_blur_quality("low")
            liquid_glass_manager.set_blur_radius(10)
            liquid_glass_manager.set_transparency(0.6)
            
            self.applied = True
            logger.info("已应用模糊质量降级策略")
        
        except Exception as e:
            logger.error(f"应用模糊质量降级失败: {e}")
    
    def revert(self, context: Dict[str, Any]):
        """
        恢复策略：恢复模糊质量
        
        Args:
            context: 包含 'liquid_glass_manager' 的上下文
        """
        liquid_glass_manager = context.get('liquid_glass_manager')
        if not liquid_glass_manager or not self._original_config:
            return
        
        try:
            # 恢复原始配置
            liquid_glass_manager.set_blur_quality(self._original_config['blur_quality'])
            liquid_glass_manager.set_blur_radius(self._original_config['blur_radius'])
            liquid_glass_manager.set_transparency(self._original_config['transparency'])
            
            self.applied = False
            logger.info("已恢复模糊质量")
        
        except Exception as e:
            logger.error(f"恢复模糊质量失败: {e}")


class ReduceAnimationComplexityStrategy(DegradationStrategy):
    """
    减少动画复杂度策略
    
    缩短动画时长，减少并发动画数量
    需求：14.5, 14.6
    """
    
    def __init__(self):
        super().__init__("reduce_animation_complexity")
        self._original_config = {}
    
    def apply(self, context: Dict[str, Any]):
        """
        应用策略：减少动画复杂度
        
        Args:
            context: 包含 'animation_manager' 的上下文
        """
        animation_manager = context.get('animation_manager')
        if not animation_manager:
            logger.warning("未找到动画管理器，无法应用动画降级")
            return
        
        try:
            # 保存原始配置
            self._original_config = {
                'complexity_level': animation_manager.get_complexity_level() if hasattr(animation_manager, 'get_complexity_level') else 'high',
                'max_concurrent': animation_manager.max_concurrent_animations if hasattr(animation_manager, 'max_concurrent_animations') else 5
            }
            
            # 应用低复杂度配置
            if hasattr(animation_manager, 'set_complexity_level'):
                animation_manager.set_complexity_level("low")
            
            if hasattr(animation_manager, 'set_max_concurrent_animations'):
                animation_manager.set_max_concurrent_animations(2)
            
            # 优化动画性能
            if hasattr(animation_manager, 'optimize_animation_for_performance'):
                animation_manager.optimize_animation_for_performance()
            
            self.applied = True
            logger.info("已应用动画复杂度降级策略")
        
        except Exception as e:
            logger.error(f"应用动画复杂度降级失败: {e}")
    
    def revert(self, context: Dict[str, Any]):
        """
        恢复策略：恢复动画复杂度
        
        Args:
            context: 包含 'animation_manager' 的上下文
        """
        animation_manager = context.get('animation_manager')
        if not animation_manager or not self._original_config:
            return
        
        try:
            # 恢复原始配置
            if hasattr(animation_manager, 'set_complexity_level'):
                animation_manager.set_complexity_level(self._original_config['complexity_level'])
            
            if hasattr(animation_manager, 'set_max_concurrent_animations'):
                animation_manager.set_max_concurrent_animations(self._original_config['max_concurrent'])
            
            # 恢复动画质量
            if hasattr(animation_manager, 'restore_animation_quality'):
                animation_manager.restore_animation_quality()
            
            self.applied = False
            logger.info("已恢复动画复杂度")
        
        except Exception as e:
            logger.error(f"恢复动画复杂度失败: {e}")


class DisableNonCriticalEffectsStrategy(DegradationStrategy):
    """
    禁用非关键视觉效果策略
    
    禁用阴影、高光等非关键视觉效果
    需求：14.6
    """
    
    def __init__(self):
        super().__init__("disable_non_critical_effects")
        self._disabled_effects = []
    
    def apply(self, context: Dict[str, Any]):
        """
        应用策略：禁用非关键视觉效果
        
        Args:
            context: 包含各种管理器的上下文
        """
        try:
            liquid_glass_manager = context.get('liquid_glass_manager')
            
            # 禁用液态玻璃的阴影和高光
            if liquid_glass_manager:
                quality_config = liquid_glass_manager.get_quality_config("low")
                quality_config['enable_shadows'] = False
                quality_config['enable_highlights'] = False
                self._disabled_effects.append('glass_shadows')
                self._disabled_effects.append('glass_highlights')
            
            # 禁用其他非关键效果
            # 可以根据需要添加更多效果的禁用逻辑
            
            self.applied = True
            logger.info(f"已禁用非关键视觉效果: {', '.join(self._disabled_effects)}")
        
        except Exception as e:
            logger.error(f"禁用非关键效果失败: {e}")
    
    def revert(self, context: Dict[str, Any]):
        """
        恢复策略：启用非关键视觉效果
        
        Args:
            context: 包含各种管理器的上下文
        """
        try:
            liquid_glass_manager = context.get('liquid_glass_manager')
            
            # 恢复液态玻璃的阴影和高光
            if liquid_glass_manager and 'glass_shadows' in self._disabled_effects:
                quality_config = liquid_glass_manager.get_quality_config()
                quality_config['enable_shadows'] = True
                quality_config['enable_highlights'] = True
            
            self._disabled_effects.clear()
            self.applied = False
            logger.info("已恢复非关键视觉效果")
        
        except Exception as e:
            logger.error(f"恢复非关键效果失败: {e}")


class DisableAnimationsStrategy(DegradationStrategy):
    """
    禁用动画策略
    
    完全禁用所有动画效果（最激进的降级）
    需求：11.7, 14.6
    """
    
    def __init__(self):
        super().__init__("disable_animations")
        self._was_enabled = True
    
    def apply(self, context: Dict[str, Any]):
        """
        应用策略：禁用所有动画
        
        Args:
            context: 包含 'animation_manager' 的上下文
        """
        animation_manager = context.get('animation_manager')
        if not animation_manager:
            logger.warning("未找到动画管理器，无法禁用动画")
            return
        
        try:
            # 保存当前状态
            self._was_enabled = animation_manager.animations_enabled
            
            # 禁用动画
            if hasattr(animation_manager, 'disable_animations'):
                animation_manager.disable_animations()
            
            self.applied = True
            logger.info("已禁用所有动画")
        
        except Exception as e:
            logger.error(f"禁用动画失败: {e}")
    
    def revert(self, context: Dict[str, Any]):
        """
        恢复策略：启用动画
        
        Args:
            context: 包含 'animation_manager' 的上下文
        """
        animation_manager = context.get('animation_manager')
        if not animation_manager:
            return
        
        try:
            # 恢复原始状态
            if self._was_enabled and hasattr(animation_manager, 'enable_animations'):
                animation_manager.enable_animations()
            
            self.applied = False
            logger.info("已恢复动画")
        
        except Exception as e:
            logger.error(f"恢复动画失败: {e}")


class ReduceRepaintFrequencyStrategy(DegradationStrategy):
    """
    降低重绘频率策略
    
    减少不必要的重绘以节省性能
    需求：14.4, 14.6
    """
    
    def __init__(self):
        super().__init__("reduce_repaint_frequency")
        self._original_config = {}
    
    def apply(self, context: Dict[str, Any]):
        """
        应用策略：降低重绘频率
        
        Args:
            context: 包含 'repaint_optimizer' 的上下文
        """
        repaint_optimizer = context.get('repaint_optimizer')
        if not repaint_optimizer:
            logger.warning("未找到重绘优化器")
            return
        
        try:
            # 启用更激进的重绘优化
            if hasattr(repaint_optimizer, 'set_optimization_level'):
                self._original_config['optimization_level'] = repaint_optimizer.get_optimization_level()
                repaint_optimizer.set_optimization_level('aggressive')
            
            self.applied = True
            logger.info("已应用重绘频率降级策略")
        
        except Exception as e:
            logger.error(f"应用重绘频率降级失败: {e}")
    
    def revert(self, context: Dict[str, Any]):
        """
        恢复策略：恢复重绘频率
        
        Args:
            context: 包含 'repaint_optimizer' 的上下文
        """
        repaint_optimizer = context.get('repaint_optimizer')
        if not repaint_optimizer or not self._original_config:
            return
        
        try:
            # 恢复原始配置
            if hasattr(repaint_optimizer, 'set_optimization_level'):
                repaint_optimizer.set_optimization_level(
                    self._original_config.get('optimization_level', 'normal')
                )
            
            self.applied = False
            logger.info("已恢复重绘频率")
        
        except Exception as e:
            logger.error(f"恢复重绘频率失败: {e}")


class DegradationStrategyManager:
    """
    降级策略管理器
    
    管理和协调各种降级策略的应用
    需求：14.6
    """
    
    # 降级级别对应的策略组合
    LEVEL_STRATEGIES = {
        "low": [
            ReduceAnimationComplexityStrategy,
        ],
        "medium": [
            ReduceAnimationComplexityStrategy,
            ReduceBlurQualityStrategy,
            ReduceRepaintFrequencyStrategy,
        ],
        "high": [
            DisableAnimationsStrategy,
            ReduceBlurQualityStrategy,
            DisableNonCriticalEffectsStrategy,
            ReduceRepaintFrequencyStrategy,
        ]
    }
    
    def __init__(self):
        """初始化降级策略管理器"""
        self._strategies: Dict[str, DegradationStrategy] = {}
        self._current_level = "none"
        self._context: Dict[str, Any] = {}
        
        logger.info("降级策略管理器已初始化")
    
    def set_context(self, context: Dict[str, Any]):
        """
        设置上下文
        
        Args:
            context: 包含各种管理器引用的上下文字典
        """
        self._context = context
        logger.debug(f"设置降级策略上下文: {list(context.keys())}")
    
    def apply_degradation(self, level: str):
        """
        应用指定级别的降级策略
        
        Args:
            level: 降级级别 (low, medium, high)
            
        需求：14.6
        """
        if level not in self.LEVEL_STRATEGIES:
            logger.warning(f"无效的降级级别: {level}")
            return
        
        # 先恢复当前策略
        self.revert_all()
        
        # 应用新策略
        strategy_classes = self.LEVEL_STRATEGIES[level]
        for strategy_class in strategy_classes:
            strategy_name = strategy_class.__name__
            
            # 创建或获取策略实例
            if strategy_name not in self._strategies:
                self._strategies[strategy_name] = strategy_class()
            
            strategy = self._strategies[strategy_name]
            
            # 应用策略
            if not strategy.is_applied():
                strategy.apply(self._context)
        
        self._current_level = level
        logger.info(f"已应用 {level} 级别降级策略")
    
    def revert_all(self):
        """
        恢复所有降级策略
        
        需求：14.6
        """
        for strategy in self._strategies.values():
            if strategy.is_applied():
                strategy.revert(self._context)
        
        self._current_level = "none"
        logger.info("已恢复所有降级策略")
    
    def get_current_level(self) -> str:
        """
        获取当前降级级别
        
        Returns:
            当前级别
        """
        return self._current_level
    
    def get_applied_strategies(self) -> list:
        """
        获取已应用的策略列表
        
        Returns:
            策略名称列表
        """
        return [
            strategy.name
            for strategy in self._strategies.values()
            if strategy.is_applied()
        ]


# 全局单例
_degradation_strategy_manager_instance: Optional[DegradationStrategyManager] = None


def get_degradation_strategy_manager() -> DegradationStrategyManager:
    """
    获取降级策略管理器单例
    
    Returns:
        DegradationStrategyManager 实例
    """
    global _degradation_strategy_manager_instance
    if _degradation_strategy_manager_instance is None:
        _degradation_strategy_manager_instance = DegradationStrategyManager()
    return _degradation_strategy_manager_instance
