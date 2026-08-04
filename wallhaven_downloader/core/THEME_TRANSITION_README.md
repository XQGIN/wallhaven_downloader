# 主题过渡管理器使用指南

## 概述

`ThemeTransitionManager` 提供平滑的主题切换动画和颜色插值功能，是苹果液态玻璃效果重设计的核心组件之一。

## 主要特性

- ✅ **平滑过渡动画**：支持 300-500ms 的主题切换动画
- ✅ **颜色插值**：自动在起始颜色和目标颜色之间进行线性插值
- ✅ **缓动函数**：支持多种缓动曲线（默认 OutCubic）
- ✅ **回调机制**：支持注册回调函数，实时获取过渡进度
- ✅ **性能优化**：60 FPS 刷新率，自动资源管理
- ✅ **单例模式**：全局统一管理主题过渡

## 快速开始

### 基本使用

```python
from PyQt5.QtGui import QColor
from wallhaven_downloader.core.theme_transition_manager import (
    ThemeTransitionManager,
    get_transition_manager
)

# 创建管理器实例（或使用单例）
manager = get_transition_manager()

# 定义起始和目标颜色
start_colors = {
    "background": QColor(245, 245, 247),  # 浅色背景
    "text": QColor(29, 29, 31),           # 深色文本
    "accent": QColor(0, 122, 255)         # 蓝色强调
}

end_colors = {
    "background": QColor(28, 28, 30),     # 深色背景
    "text": QColor(245, 245, 247),        # 浅色文本
    "accent": QColor(10, 132, 255)        # 深色模式蓝色
}

# 开始过渡动画（400ms）
manager.start_transition(start_colors, end_colors, duration=400)
```

### 监听过渡进度

```python
# 连接信号
manager.transition_started.connect(lambda: print("过渡开始"))
manager.transition_progress.connect(lambda p: print(f"进度: {p:.2%}"))
manager.transition_completed.connect(lambda: print("过渡完成"))
```

### 注册回调函数

```python
def on_colors_update(colors):
    """颜色更新回调"""
    bg = colors.get("background")
    if bg:
        # 更新组件背景色
        my_widget.setStyleSheet(f"background-color: {bg.name()};")

# 注册回调
manager.register_callback(on_colors_update)
```

## 高级用法

### 自定义缓动函数

```python
from PyQt5.QtCore import QEasingCurve

# 设置为线性过渡
manager.set_easing_curve(QEasingCurve.Linear)

# 设置为三次缓入缓出
manager.set_easing_curve(QEasingCurve.InOutCubic)

# 设置为弹性效果
manager.set_easing_curve(QEasingCurve.OutElastic)
```

### 自定义过渡时长

```python
# 设置默认时长为 500ms
manager.set_default_duration(500)

# 或在开始过渡时指定
manager.start_transition(start_colors, end_colors, duration=300)
```

### 颜色插值工具

```python
# 静态方法：在两个颜色之间插值
start = QColor(255, 255, 255)
end = QColor(0, 0, 0)

# 50% 进度
mid_color = ThemeTransitionManager.interpolate_color(start, end, 0.5)
print(mid_color.name())  # #7F7F7F (灰色)
```

### 停止和清理

```python
# 停止当前过渡
manager.stop_transition()

# 清理所有注册
manager.clear()
```

## 与主题管理器集成

### 完整示例

```python
from wallhaven_downloader.core.theme_manager import get_theme_manager
from wallhaven_downloader.core.apple_color_palette import get_apple_palette
from wallhaven_downloader.core.theme_transition_manager import get_transition_manager

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.theme_manager = get_theme_manager()
        self.palette = get_apple_palette()
        self.transition_manager = get_transition_manager()
        
        # 注册颜色更新回调
        self.transition_manager.register_callback(self.on_theme_transition)
        
        # 监听主题变更
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
    
    def on_theme_changed(self, theme_name: str):
        """主题变更处理"""
        # 获取当前和目标颜色
        is_dark = self.theme_manager.is_dark_mode()
        
        start_colors = self.palette.get_all_colors(not is_dark)
        end_colors = self.palette.get_all_colors(is_dark)
        
        # 开始过渡动画
        self.transition_manager.start_transition(
            start_colors,
            end_colors,
            duration=400
        )
    
    def on_theme_transition(self, colors):
        """过渡期间的颜色更新"""
        # 更新窗口背景
        bg = colors.get("background")
        if bg:
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {bg.name()};
                }}
            """)
        
        # 更新其他组件...
        self.update()
```

## API 参考

### 主要方法

#### `start_transition(start_colors, end_colors, duration=None)`
开始主题过渡动画

**参数：**
- `start_colors` (Dict[str, QColor]): 起始颜色字典
- `end_colors` (Dict[str, QColor]): 目标颜色字典
- `duration` (int, optional): 过渡时长（毫秒），默认 400ms

#### `stop_transition()`
停止当前的过渡动画

#### `register_callback(callback)`
注册颜色更新回调函数

**参数：**
- `callback` (Callable): 回调函数，接收 `Dict[str, QColor]` 参数

#### `set_easing_curve(curve_type)`
设置缓动函数类型

**参数：**
- `curve_type` (QEasingCurve.Type): 缓动曲线类型

#### `set_default_duration(duration)`
设置默认过渡时长

**参数：**
- `duration` (int): 时长（毫秒），建议 300-500ms

### 静态方法

#### `interpolate_color(start, end, progress)`
在两个颜色之间进行线性插值

**参数：**
- `start` (QColor): 起始颜色
- `end` (QColor): 目标颜色
- `progress` (float): 进度（0.0-1.0）

**返回：**
- `QColor`: 插值后的颜色

### 信号

#### `transition_started`
过渡开始时发射

#### `transition_progress(float)`
过渡进度更新时发射，参数为进度值（0.0-1.0）

#### `transition_completed`
过渡完成时发射

## 性能考虑

### 帧率优化

- 默认帧间隔：16ms（约 60 FPS）
- 使用缓动函数减少计算量
- 自动停止完成的过渡

### 内存管理

- 自动清理完成的过渡
- 支持手动清理资源
- 使用颜色缓存减少重复计算

### 最佳实践

1. **合理设置时长**：建议 300-500ms，过短会显得生硬，过长会影响体验
2. **选择合适的缓动函数**：OutCubic 适合大多数场景
3. **及时清理回调**：不再使用的回调应及时取消注册
4. **避免频繁切换**：等待当前过渡完成再开始新的过渡

## 常见问题

### Q: 如何确保过渡完成后再执行操作？

A: 连接 `transition_completed` 信号：

```python
manager.transition_completed.connect(self.on_transition_done)

def on_transition_done(self):
    print("过渡完成，可以执行后续操作")
```

### Q: 如何实现多个组件同步过渡？

A: 在回调函数中更新所有组件：

```python
def on_colors_update(colors):
    # 更新多个组件
    self.header.update_colors(colors)
    self.sidebar.update_colors(colors)
    self.content.update_colors(colors)

manager.register_callback(on_colors_update)
```

### Q: 过渡动画卡顿怎么办？

A: 检查以下几点：
1. 减少回调函数中的计算量
2. 使用更简单的缓动函数（如 Linear）
3. 适当增加帧间隔（降低帧率）
4. 减少同时过渡的颜色数量

## 测试

运行单元测试：

```bash
python -m pytest tests/test_theme_transition.py -v
```

## 相关文档

- [主题管理器](./theme_manager.py)
- [苹果颜色调色板](./apple_color_palette.py)
- [液态玻璃管理器](../ui/liquid_glass/liquid_glass_manager.py)

## 版本历史

- **v1.0.0** (2026-01-04): 初始版本
  - 实现基本的主题过渡功能
  - 支持颜色插值和缓动函数
  - 提供回调机制和信号系统
