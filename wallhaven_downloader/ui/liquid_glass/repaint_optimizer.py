"""
重绘优化器

实现脏区域检测和静止时停止重绘，优化界面性能

需求：14.4
"""

from PyQt5.QtCore import QObject, QTimer, QRect, pyqtSignal
from PyQt5.QtWidgets import QWidget
from typing import Dict, Set, Optional, List
import time


class RepaintOptimizer(QObject):
    """
    重绘优化器
    
    功能：
    1. 脏区域检测：只重绘变化的区域
    2. 静止检测：窗口静止时停止不必要的重绘
    3. 重绘节流：限制重绘频率
    
    需求：14.4
    """
    
    # 信号
    idle_state_changed = pyqtSignal(bool)  # 静止状态变化
    repaint_throttled = pyqtSignal(QWidget)  # 重绘被节流
    
    # 配置常量
    IDLE_TIMEOUT = 1000  # 静止超时时间（毫秒）
    MIN_REPAINT_INTERVAL = 16  # 最小重绘间隔（毫秒，约 60 FPS）
    DIRTY_REGION_MERGE_THRESHOLD = 50  # 脏区域合并阈值（像素）
    
    def __init__(self):
        """初始化重绘优化器"""
        super().__init__()
        
        # 静止检测定时器
        self.idle_timer = QTimer()
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self._on_idle_timeout)
        
        # 状态跟踪
        self.is_idle = False  # 是否处于静止状态
        self.last_activity_time = time.time()  # 最后活动时间
        
        # 组件重绘跟踪
        self.widget_last_repaint: Dict[int, float] = {}  # widget_id -> last_repaint_time
        self.widget_repaint_count: Dict[int, int] = {}  # widget_id -> repaint_count
        
        # 脏区域跟踪
        self.dirty_regions: Dict[int, List[QRect]] = {}  # widget_id -> [dirty_rects]
        
        # 优化统计
        self.total_repaints = 0
        self.throttled_repaints = 0
        self.merged_regions = 0
        
        # 启用标志
        self.optimization_enabled = True
        self.idle_detection_enabled = True
        self.dirty_region_tracking_enabled = True
    
    def record_activity(self):
        """
        记录用户活动
        
        重置静止定时器，标记为活动状态
        """
        if not self.idle_detection_enabled:
            return
        
        self.last_activity_time = time.time()
        
        # 如果之前是静止状态，现在变为活动状态
        if self.is_idle:
            self.is_idle = False
            self.idle_state_changed.emit(False)
            print("窗口状态: 活动")
        
        # 重启静止定时器
        self.idle_timer.start(self.IDLE_TIMEOUT)
    
    def _on_idle_timeout(self):
        """
        静止超时回调
        
        当用户一段时间没有活动时触发
        """
        if not self.is_idle:
            self.is_idle = True
            self.idle_state_changed.emit(True)
            print("窗口状态: 静止（停止不必要的重绘）")
    
    def should_repaint(self, widget: QWidget) -> bool:
        """
        判断组件是否应该重绘
        
        考虑因素：
        1. 是否处于静止状态
        2. 距离上次重绘的时间间隔
        3. 是否有脏区域
        
        Args:
            widget: 目标组件
            
        Returns:
            是否应该重绘
        """
        if not self.optimization_enabled:
            return True
        
        widget_id = id(widget)
        current_time = time.time()
        
        # 如果处于静止状态且没有脏区域，不重绘
        if self.is_idle and not self.has_dirty_regions(widget):
            return False
        
        # 检查重绘间隔（节流）
        last_repaint = self.widget_last_repaint.get(widget_id, 0)
        time_since_last = (current_time - last_repaint) * 1000  # 转换为毫秒
        
        if time_since_last < self.MIN_REPAINT_INTERVAL:
            # 重绘太频繁，节流
            self.throttled_repaints += 1
            self.repaint_throttled.emit(widget)
            return False
        
        return True
    
    def mark_repaint(self, widget: QWidget):
        """
        标记组件已重绘
        
        Args:
            widget: 已重绘的组件
        """
        widget_id = id(widget)
        current_time = time.time()
        
        # 更新重绘时间
        self.widget_last_repaint[widget_id] = current_time
        
        # 更新重绘计数
        self.widget_repaint_count[widget_id] = self.widget_repaint_count.get(widget_id, 0) + 1
        self.total_repaints += 1
        
        # 清除脏区域
        if widget_id in self.dirty_regions:
            del self.dirty_regions[widget_id]
        
        # 记录活动
        self.record_activity()
    
    def add_dirty_region(self, widget: QWidget, rect: QRect):
        """
        添加脏区域
        
        Args:
            widget: 目标组件
            rect: 脏区域矩形
        """
        if not self.dirty_region_tracking_enabled:
            return
        
        widget_id = id(widget)
        
        if widget_id not in self.dirty_regions:
            self.dirty_regions[widget_id] = []
        
        # 尝试与现有脏区域合并
        merged = False
        for i, existing_rect in enumerate(self.dirty_regions[widget_id]):
            if self._should_merge_regions(existing_rect, rect):
                # 合并区域
                self.dirty_regions[widget_id][i] = existing_rect.united(rect)
                self.merged_regions += 1
                merged = True
                break
        
        if not merged:
            # 添加新的脏区域
            self.dirty_regions[widget_id].append(rect)
        
        # 记录活动
        self.record_activity()
    
    def _should_merge_regions(self, rect1: QRect, rect2: QRect) -> bool:
        """
        判断两个区域是否应该合并
        
        如果两个区域距离很近，合并它们可以减少重绘次数
        
        Args:
            rect1: 第一个矩形
            rect2: 第二个矩形
            
        Returns:
            是否应该合并
        """
        # 计算两个矩形之间的距离
        dx = 0
        dy = 0
        
        if rect1.right() < rect2.left():
            dx = rect2.left() - rect1.right()
        elif rect2.right() < rect1.left():
            dx = rect1.left() - rect2.right()
        
        if rect1.bottom() < rect2.top():
            dy = rect2.top() - rect1.bottom()
        elif rect2.bottom() < rect1.top():
            dy = rect1.top() - rect2.bottom()
        
        distance = (dx * dx + dy * dy) ** 0.5
        
        return distance < self.DIRTY_REGION_MERGE_THRESHOLD
    
    def get_dirty_regions(self, widget: QWidget) -> List[QRect]:
        """
        获取组件的脏区域列表
        
        Args:
            widget: 目标组件
            
        Returns:
            脏区域矩形列表
        """
        widget_id = id(widget)
        return self.dirty_regions.get(widget_id, []).copy()
    
    def has_dirty_regions(self, widget: QWidget) -> bool:
        """
        检查组件是否有脏区域
        
        Args:
            widget: 目标组件
            
        Returns:
            是否有脏区域
        """
        widget_id = id(widget)
        return widget_id in self.dirty_regions and len(self.dirty_regions[widget_id]) > 0
    
    def clear_dirty_regions(self, widget: QWidget):
        """
        清除组件的脏区域
        
        Args:
            widget: 目标组件
        """
        widget_id = id(widget)
        if widget_id in self.dirty_regions:
            del self.dirty_regions[widget_id]
    
    def get_repaint_count(self, widget: QWidget) -> int:
        """
        获取组件的重绘次数
        
        Args:
            widget: 目标组件
            
        Returns:
            重绘次数
        """
        widget_id = id(widget)
        return self.widget_repaint_count.get(widget_id, 0)
    
    def get_repaint_rate(self, widget: QWidget) -> float:
        """
        获取组件的重绘频率（每秒）
        
        Args:
            widget: 目标组件
            
        Returns:
            重绘频率（次/秒）
        """
        widget_id = id(widget)
        
        if widget_id not in self.widget_last_repaint:
            return 0.0
        
        current_time = time.time()
        last_repaint = self.widget_last_repaint[widget_id]
        time_elapsed = current_time - last_repaint
        
        if time_elapsed < 0.001:  # 避免除零
            return 0.0
        
        repaint_count = self.widget_repaint_count.get(widget_id, 0)
        return repaint_count / time_elapsed
    
    def enable_optimization(self):
        """启用重绘优化"""
        self.optimization_enabled = True
        print("重绘优化已启用")
    
    def disable_optimization(self):
        """禁用重绘优化"""
        self.optimization_enabled = False
        print("重绘优化已禁用")
    
    def enable_idle_detection(self):
        """启用静止检测"""
        self.idle_detection_enabled = True
        self.idle_timer.start(self.IDLE_TIMEOUT)
        print("静止检测已启用")
    
    def disable_idle_detection(self):
        """禁用静止检测"""
        self.idle_detection_enabled = False
        self.idle_timer.stop()
        if self.is_idle:
            self.is_idle = False
            self.idle_state_changed.emit(False)
        print("静止检测已禁用")
    
    def enable_dirty_region_tracking(self):
        """启用脏区域跟踪"""
        self.dirty_region_tracking_enabled = True
        print("脏区域跟踪已启用")
    
    def disable_dirty_region_tracking(self):
        """禁用脏区域跟踪"""
        self.dirty_region_tracking_enabled = False
        self.dirty_regions.clear()
        print("脏区域跟踪已禁用")
    
    def get_optimization_stats(self) -> Dict:
        """
        获取优化统计信息
        
        Returns:
            统计信息字典
        """
        throttle_rate = 0.0
        if self.total_repaints > 0:
            throttle_rate = (self.throttled_repaints / self.total_repaints) * 100
        
        return {
            "is_idle": self.is_idle,
            "optimization_enabled": self.optimization_enabled,
            "idle_detection_enabled": self.idle_detection_enabled,
            "dirty_region_tracking_enabled": self.dirty_region_tracking_enabled,
            "total_repaints": self.total_repaints,
            "throttled_repaints": self.throttled_repaints,
            "throttle_rate": round(throttle_rate, 2),
            "merged_regions": self.merged_regions,
            "tracked_widgets": len(self.widget_last_repaint),
            "dirty_widgets": len(self.dirty_regions)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.total_repaints = 0
        self.throttled_repaints = 0
        self.merged_regions = 0
        self.widget_repaint_count.clear()
        print("重绘统计已重置")
    
    def cleanup(self):
        """清理资源"""
        self.idle_timer.stop()
        self.widget_last_repaint.clear()
        self.widget_repaint_count.clear()
        self.dirty_regions.clear()
        print("重绘优化器已清理")


# 全局单例
_repaint_optimizer_instance: Optional[RepaintOptimizer] = None


def get_repaint_optimizer() -> RepaintOptimizer:
    """
    获取重绘优化器单例
    
    Returns:
        RepaintOptimizer 实例
    """
    global _repaint_optimizer_instance
    if _repaint_optimizer_instance is None:
        _repaint_optimizer_instance = RepaintOptimizer()
    return _repaint_optimizer_instance
