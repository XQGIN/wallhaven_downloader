"""
模糊层管理器

负责管理和应用模糊效果，支持多平台实现
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QGraphicsBlurEffect
from typing import Dict, List, Optional, Tuple
import time


class BlurLayerManager(QObject):
    """
    模糊层管理器
    
    负责管理和应用模糊效果，支持多平台实现
    
    需求：1.1, 1.4, 14.3
    """
    
    # 信号
    blur_applied = pyqtSignal(QWidget, int)  # 模糊应用成功信号
    blur_removed = pyqtSignal(QWidget)  # 模糊移除信号
    cache_cleared = pyqtSignal()  # 缓存清除信号
    
    # 缓存配置
    MAX_CACHE_SIZE = 50  # 最大缓存数量
    CACHE_CLEANUP_THRESHOLD = 40  # 缓存清理阈值
    CACHE_TTL = 300  # 缓存生存时间（秒）- 5分钟
    MIN_CACHE_SIZE = 10  # 最小保留缓存数量
    
    def __init__(self):
        """初始化模糊层管理器"""
        super().__init__()
        
        # 延迟导入以避免循环依赖
        from .platform_adapter import PlatformBlurAdapter
        
        self.platform_adapter = PlatformBlurAdapter()
        
        # 模糊效果缓存：widget_id -> (blur_effect, blur_radius, last_access_time)
        self.blur_cache: Dict[int, Tuple[QGraphicsBlurEffect, int, float]] = {}
        
        # 活动的模糊组件列表
        self.active_blur_widgets: List[QWidget] = []
        
        # 缓存统计
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_evictions = 0  # 缓存驱逐次数
        
        # 智能缓存策略
        self.cache_strategy = "lru"  # lru, lfu, ttl
        self.access_frequency: Dict[int, int] = {}  # 访问频率统计（用于 LFU）
    
    def apply_blur(self, 
                   widget: QWidget,
                   blur_radius: int = 20,
                   use_native: bool = True) -> bool:
        """
        为组件应用模糊效果
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径 (5-40px)
            use_native: 是否使用原生模糊效果
            
        Returns:
            是否成功应用模糊
        """
        if widget is None:
            return False
        
        # 限制模糊半径在有效范围内
        blur_radius = max(5, min(40, blur_radius))
        
        try:
            # 尝试使用原生模糊效果
            if use_native:
                if self.platform_adapter.apply_native_blur(widget, blur_radius):
                    if widget not in self.active_blur_widgets:
                        self.active_blur_widgets.append(widget)
                    self.blur_applied.emit(widget, blur_radius)
                    return True
            
            # 降级到 PyQt5 模糊效果
            success = self._apply_qt_blur(widget, blur_radius)
            if success:
                self.blur_applied.emit(widget, blur_radius)
            return success
        
        except Exception as e:
            print(f"应用模糊效果失败: {e}")
            # 尝试降级方案
            success = self._apply_qt_blur(widget, blur_radius)
            if success:
                self.blur_applied.emit(widget, blur_radius)
            return success
    
    def _apply_qt_blur(self, widget: QWidget, blur_radius: int) -> bool:
        """
        使用 PyQt5 QGraphicsBlurEffect 应用模糊
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径
            
        Returns:
            是否成功应用
        """
        try:
            widget_id = id(widget)
            current_time = time.time()
            
            # 检查缓存
            if widget_id in self.blur_cache:
                blur_effect, cached_radius, _ = self.blur_cache[widget_id]
                
                # 更新访问频率（用于 LFU）
                self.access_frequency[widget_id] = self.access_frequency.get(widget_id, 0) + 1
                
                # 如果半径相同，直接重用（缓存命中）
                if cached_radius == blur_radius:
                    self.cache_hits += 1
                    # 更新访问时间
                    self.blur_cache[widget_id] = (blur_effect, blur_radius, current_time)
                    return True
                
                # 半径不同，更新半径
                blur_effect.setBlurRadius(blur_radius)
                self.blur_cache[widget_id] = (blur_effect, blur_radius, current_time)
                self.cache_misses += 1
            else:
                # 缓存未命中，创建新的模糊效果
                self.cache_misses += 1
                
                # 检查缓存大小，必要时清理
                if len(self.blur_cache) >= self.MAX_CACHE_SIZE:
                    self._cleanup_cache()
                
                # 创建新的模糊效果
                blur_effect = QGraphicsBlurEffect()
                blur_effect.setBlurRadius(blur_radius)
                widget.setGraphicsEffect(blur_effect)
                
                # 缓存模糊效果
                self.blur_cache[widget_id] = (blur_effect, blur_radius, current_time)
                
                # 初始化访问频率
                self.access_frequency[widget_id] = 1
            
            if widget not in self.active_blur_widgets:
                self.active_blur_widgets.append(widget)
            
            return True
        
        except Exception as e:
            print(f"PyQt5 模糊效果应用失败: {e}")
            return False
    
    def _cleanup_cache(self):
        """
        清理缓存，移除最久未使用的条目
        
        支持多种缓存策略：
        - LRU (Least Recently Used): 移除最久未访问的条目
        - LFU (Least Frequently Used): 移除访问频率最低的条目
        - TTL (Time To Live): 移除过期的条目
        
        需求：14.3
        """
        if len(self.blur_cache) < self.CACHE_CLEANUP_THRESHOLD:
            return
        
        current_time = time.time()
        items_to_remove = []
        
        if self.cache_strategy == "lru":
            # LRU 策略：按访问时间排序，移除最旧的
            sorted_cache = sorted(
                self.blur_cache.items(),
                key=lambda x: x[1][2]  # 按 last_access_time 排序
            )
            
            # 移除最旧的 20% 条目，但保留最小缓存数量
            remove_count = max(
                len(sorted_cache) // 5,
                len(sorted_cache) - self.MIN_CACHE_SIZE
            )
            items_to_remove = [widget_id for widget_id, _ in sorted_cache[:remove_count]]
        
        elif self.cache_strategy == "lfu":
            # LFU 策略：按访问频率排序，移除频率最低的
            sorted_cache = sorted(
                self.blur_cache.items(),
                key=lambda x: self.access_frequency.get(x[0], 0)
            )
            
            remove_count = max(
                len(sorted_cache) // 5,
                len(sorted_cache) - self.MIN_CACHE_SIZE
            )
            items_to_remove = [widget_id for widget_id, _ in sorted_cache[:remove_count]]
        
        elif self.cache_strategy == "ttl":
            # TTL 策略：移除过期的条目
            for widget_id, (_, _, last_access_time) in self.blur_cache.items():
                if current_time - last_access_time > self.CACHE_TTL:
                    items_to_remove.append(widget_id)
            
            # 如果过期的不够，再用 LRU 补充
            if len(items_to_remove) < len(self.blur_cache) // 5:
                sorted_cache = sorted(
                    [(wid, data) for wid, data in self.blur_cache.items() 
                     if wid not in items_to_remove],
                    key=lambda x: x[1][2]
                )
                additional_remove = (len(self.blur_cache) // 5) - len(items_to_remove)
                items_to_remove.extend([wid for wid, _ in sorted_cache[:additional_remove]])
        
        # 执行清理
        for widget_id in items_to_remove:
            if widget_id in self.blur_cache:
                del self.blur_cache[widget_id]
                self.cache_evictions += 1
                # 清理访问频率统计
                if widget_id in self.access_frequency:
                    del self.access_frequency[widget_id]
        
        if items_to_remove:
            print(f"缓存清理: 移除 {len(items_to_remove)} 个条目，当前缓存大小: {len(self.blur_cache)}")
    
    def set_cache_strategy(self, strategy: str):
        """
        设置缓存策略
        
        Args:
            strategy: 缓存策略 ('lru', 'lfu', 'ttl')
        """
        if strategy in ["lru", "lfu", "ttl"]:
            self.cache_strategy = strategy
            print(f"缓存策略已设置为: {strategy}")
        else:
            print(f"无效的缓存策略: {strategy}")
    
    def set_cache_size_limit(self, max_size: int, cleanup_threshold: int = None):
        """
        设置缓存大小限制
        
        Args:
            max_size: 最大缓存数量
            cleanup_threshold: 清理阈值（可选，默认为 max_size * 0.8）
        """
        self.MAX_CACHE_SIZE = max(10, max_size)
        self.CACHE_CLEANUP_THRESHOLD = cleanup_threshold or int(max_size * 0.8)
        print(f"缓存大小限制已设置: 最大={self.MAX_CACHE_SIZE}, 清理阈值={self.CACHE_CLEANUP_THRESHOLD}")
        
        # 如果当前缓存超过新限制，立即清理
        if len(self.blur_cache) > self.MAX_CACHE_SIZE:
            self._cleanup_cache()
    
    def optimize_cache(self):
        """
        优化缓存
        
        执行以下优化：
        1. 清理过期条目（TTL）
        2. 清理无效的组件引用
        3. 重置访问频率统计（如果使用 LFU）
        
        需求：14.3
        """
        current_time = time.time()
        invalid_widgets = []
        expired_widgets = []
        
        # 检查所有缓存条目
        for widget_id, (blur_effect, blur_radius, last_access_time) in list(self.blur_cache.items()):
            # 检查是否过期
            if current_time - last_access_time > self.CACHE_TTL:
                expired_widgets.append(widget_id)
            
            # 检查模糊效果是否仍然有效
            if blur_effect is None or not hasattr(blur_effect, 'blurRadius'):
                invalid_widgets.append(widget_id)
        
        # 清理过期和无效的条目
        for widget_id in set(expired_widgets + invalid_widgets):
            if widget_id in self.blur_cache:
                del self.blur_cache[widget_id]
                self.cache_evictions += 1
            if widget_id in self.access_frequency:
                del self.access_frequency[widget_id]
        
        # 清理活动组件列表中的无效引用
        self.active_blur_widgets = [
            widget for widget in self.active_blur_widgets
            if widget is not None and hasattr(widget, 'isVisible')
        ]
        
        if expired_widgets or invalid_widgets:
            print(f"缓存优化: 清理 {len(expired_widgets)} 个过期条目, {len(invalid_widgets)} 个无效条目")
    
    def get_cache_efficiency(self) -> float:
        """
        计算缓存效率
        
        Returns:
            缓存命中率（0-100）
        """
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return (self.cache_hits / total_requests) * 100
    
    def remove_blur(self, widget: QWidget):
        """
        移除组件的模糊效果
        
        Args:
            widget: 目标组件
        """
        if widget is None:
            return
        
        try:
            # 移除图形效果
            widget.setGraphicsEffect(None)
            
            # 从缓存中移除
            widget_id = id(widget)
            if widget_id in self.blur_cache:
                del self.blur_cache[widget_id]
            
            # 清理访问频率统计
            if widget_id in self.access_frequency:
                del self.access_frequency[widget_id]
            
            # 从活动列表中移除
            if widget in self.active_blur_widgets:
                self.active_blur_widgets.remove(widget)
            
            self.blur_removed.emit(widget)
        
        except Exception as e:
            print(f"移除模糊效果失败: {e}")
    
    def update_blur_radius(self, widget: QWidget, radius: int):
        """
        更新组件的模糊半径
        
        Args:
            widget: 目标组件
            radius: 新的模糊半径 (5-40px)
        """
        if widget is None:
            return
        
        # 限制在有效范围内
        radius = max(5, min(40, radius))
        
        widget_id = id(widget)
        if widget_id in self.blur_cache:
            blur_effect, _, _ = self.blur_cache[widget_id]
            blur_effect.setBlurRadius(radius)
            # 更新缓存
            self.blur_cache[widget_id] = (blur_effect, radius, time.time())
        else:
            # 如果不在缓存中，重新应用模糊
            self.apply_blur(widget, radius)
    
    def clear_blur_cache(self):
        """清除模糊效果缓存"""
        # 移除所有模糊效果
        for widget in self.active_blur_widgets[:]:
            self.remove_blur(widget)
        
        # 清空缓存
        self.blur_cache.clear()
        self.active_blur_widgets.clear()
        self.access_frequency.clear()
        
        # 重置统计
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_evictions = 0
        
        self.cache_cleared.emit()
    
    def get_active_blur_count(self) -> int:
        """
        获取当前活动的模糊组件数量
        
        Returns:
            活动模糊组件数量
        """
        return len(self.active_blur_widgets)
    
    def get_cache_size(self) -> int:
        """
        获取当前缓存大小
        
        Returns:
            缓存中的条目数量
        """
        return len(self.blur_cache)
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存命中率等统计信息的字典
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.blur_cache),
            "active_widgets": len(self.active_blur_widgets),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_evictions": self.cache_evictions,
            "hit_rate": round(hit_rate, 2),
            "cache_strategy": self.cache_strategy,
            "cache_efficiency": round(self.get_cache_efficiency(), 2)
        }
    
    def is_blur_cached(self, widget: QWidget, blur_radius: int) -> bool:
        """
        检查指定组件和模糊半径是否已缓存
        
        Args:
            widget: 目标组件
            blur_radius: 模糊半径
            
        Returns:
            是否已缓存
        """
        widget_id = id(widget)
        if widget_id in self.blur_cache:
            _, cached_radius, _ = self.blur_cache[widget_id]
            return cached_radius == blur_radius
        return False
