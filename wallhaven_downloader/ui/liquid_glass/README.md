# 液态玻璃系统使用指南

## 概述

液态玻璃系统提供了苹果风格的毛玻璃效果，支持跨平台（Windows、macOS、Linux）并具有性能优化功能。

## 核心组件

### LiquidGlassManager（液态玻璃管理器）

主要的管理类，负责协调所有液态玻璃效果。

#### 基本使用

```python
from wallhaven_downloader.ui.liquid_glass import LiquidGlassManager

# 创建管理器
glass_manager = LiquidGlassManager(main_window)

# 初始化
if glass_manager.initialize():
    print("初始化成功")

# 为窗口应用全局模糊
glass_manager.apply_global_blur(window)

# 创建玻璃面板
panel = glass_manager.create_glass_panel(
    parent=parent_widget,
    panel_type="normal",  # normal, elevated, floating
    blur_radius=20,
    transparency=0.7
)
```

#### 性能模式

```python
# 启用性能模式（降低视觉效果质量）
glass_manager.enable_performance_mode()

# 禁用性能模式（恢复完整视觉效果）
glass_manager.disable_performance_mode()

# 检查性能模式状态
if glass_manager.is_performance_mode():
    print("当前处于性能模式")
```

#### 配置调整

```python
# 设置模糊半径 (5-40px)
glass_manager.set_blur_radius(25)

# 设置透明度 (0.6-0.95)
glass_manager.set_transparency(0.8)

# 设置模糊质量 (low, medium, high)
glass_manager.set_blur_quality("high")
```

#### 信号监听

```python
# 监听性能模式变化
glass_manager.performance_mode_changed.connect(on_performance_mode_changed)

# 监听模糊质量变化
glass_manager.blur_quality_changed.connect(on_blur_quality_changed)

# 监听透明度变化
glass_manager.transparency_changed.connect(on_transparency_changed)
```

#### 获取信息

```python
# 获取平台信息
info = glass_manager.get_platform_info()
print(f"平台: {info['platform']}")
print(f"原生模糊支持: {info['native_blur_supported']}")

# 获取模糊统计
stats = glass_manager.get_blur_stats()
print(f"缓存命中率: {stats['hit_rate']}%")

# 获取质量配置
config = glass_manager.get_quality_config("high")
print(f"高质量配置: {config}")
```

## 质量级别配置

### Low（低质量）
- 模糊半径: 10px
- 透明度: 0.6
- 不使用原生模糊
- 禁用阴影和高光

### Medium（中等质量）
- 模糊半径: 15px
- 透明度: 0.7
- 使用原生模糊
- 启用阴影，禁用高光

### High（高质量）
- 模糊半径: 20px
- 透明度: 0.75
- 使用原生模糊
- 启用阴影和高光

## 面板类型

### Normal（普通面板）
- 模糊半径: 20px
- 透明度: 0.7
- 圆角半径: 12px
- 阴影模糊: 20px

### Elevated（提升面板）
- 模糊半径: 25px
- 透明度: 0.75
- 圆角半径: 16px
- 阴影模糊: 30px

### Floating（浮动面板）
- 模糊半径: 30px
- 透明度: 0.8
- 圆角半径: 20px
- 阴影模糊: 40px

## 性能优化建议

1. **启用性能模式**：在低性能设备上自动降低视觉效果质量
2. **模糊缓存**：相同参数的模糊效果会被缓存，避免重复计算
3. **面板管理**：管理器会自动跟踪和更新所有创建的面板
4. **平台适配**：自动选择最优的平台特定实现

## 清理资源

```python
# 在应用关闭时清理资源
glass_manager.cleanup()
```

## 完整示例

```python
from PyQt5.QtWidgets import QApplication, QMainWindow
from wallhaven_downloader.ui.liquid_glass import LiquidGlassManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建液态玻璃管理器
        self.glass_manager = LiquidGlassManager(self)
        self.glass_manager.initialize()
        
        # 监听性能模式变化
        self.glass_manager.performance_mode_changed.connect(
            self.on_performance_mode_changed
        )
        
        # 应用全局模糊
        self.glass_manager.apply_global_blur(self)
        
        # 创建玻璃面板
        panel = self.glass_manager.create_glass_panel(
            self,
            panel_type="elevated"
        )
    
    def on_performance_mode_changed(self, enabled):
        if enabled:
            print("性能模式已启用")
        else:
            print("性能模式已禁用")
    
    def closeEvent(self, event):
        # 清理资源
        self.glass_manager.cleanup()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
```

## 需求映射

- **需求 1.1-1.8**: 液态玻璃视觉系统核心功能
- **需求 14.6**: 性能模式切换和视觉效果质量调整
