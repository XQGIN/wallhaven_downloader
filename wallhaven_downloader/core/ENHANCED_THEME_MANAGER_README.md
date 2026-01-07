# 增强主题管理器 (EnhancedThemeManager)

## 概述

`EnhancedThemeManager` 是对现有 `ThemeManager` 的增强版本，提供了更强大的主题管理功能，包括：

- 🎨 **苹果风格颜色调色板**：完整的苹果设计规范颜色方案
- 🌈 **主题过渡动画**：流畅的主题切换动画效果
- 🔄 **自动主题跟随**：自动检测并跟随系统主题
- 💾 **配置持久化**：自动保存和加载主题配置

## 快速开始

### 基本使用

```python
from wallhaven_downloader.core.enhanced_theme_manager import get_enhanced_theme_manager

# 获取增强主题管理器实例（单例模式）
theme_manager = get_enhanced_theme_manager()

# 切换主题（带过渡动画）
theme_manager.set_theme_with_transition("深色", duration=300)

# 获取苹果风格颜色
accent_color = theme_manager.get_apple_color("accent")
background_color = theme_manager.get_apple_color("background")
```

### 启用自动主题

```python
# 启用自动主题（跟随系统）
theme_manager.enable_auto_theme()

# 禁用自动主题
theme_manager.disable_auto_theme()
```

### 配置管理

```python
# 获取当前主题配置
config = theme_manager.get_theme_config()
print(config)
# {
#     "mode": "深色",
#     "auto_enabled": True,
#     "transition_duration": 300,
#     "follow_system": True
# }

# 设置主题配置
theme_manager.set_theme_config({
    "mode": "浅色",
    "auto_enabled": False,
    "transition_duration": 400,
    "follow_system": False
})
```

## 主要功能

### 1. 主题切换与过渡

`EnhancedThemeManager` 提供了带过渡动画的主题切换功能：

```python
# 切换到深色主题，过渡时间 300ms
theme_manager.set_theme_with_transition("深色", duration=300)

# 监听过渡完成信号
theme_manager.transition_completed.connect(on_transition_completed)

def on_transition_completed():
    print("主题过渡完成！")
```

**特点：**
- 平滑的颜色过渡动画
- 可自定义过渡时长（推荐 300-500ms）
- 过渡完成后发射信号通知

### 2. 苹果风格颜色调色板

集成了完整的苹果设计规范颜色方案：

```python
# 获取颜色
background = theme_manager.get_apple_color("background")
surface = theme_manager.get_apple_color("surface")
text_primary = theme_manager.get_apple_color("text_primary")
accent = theme_manager.get_apple_color("accent")
success = theme_manager.get_apple_color("success")
error = theme_manager.get_apple_color("error")

# 颜色会根据当前主题（浅色/深色）自动调整
```

**可用颜色：**

| 颜色名称 | 说明 | 浅色主题 | 深色主题 |
|---------|------|---------|---------|
| `background` | 背景色 | #F5F5F7 | #1C1C1E |
| `surface` | 表面色 | #FFFFFF | #2C2C2E |
| `text_primary` | 主要文本 | #1D1D1F | #F5F5F7 |
| `text_secondary` | 次要文本 | #86868B | #98989D |
| `accent` | 强调色 | #007AFF | #0A84FF |
| `success` | 成功色 | #34C759 | #30D158 |
| `warning` | 警告色 | #FFCC00 | #FFD60A |
| `error` | 错误色 | #FF3B30 | #FF453A |
| `glass_normal` | 玻璃效果 | rgba(255,255,255,0.78) | rgba(44,44,46,0.78) |

### 3. 自动主题跟随系统

自动检测并跟随系统主题变化：

```python
# 启用自动主题
theme_manager.enable_auto_theme()

# 程序会每 5 秒检查一次系统主题
# 如果系统主题发生变化，会自动切换应用主题
```

**支持的平台：**
- ✅ Windows 10/11（通过注册表检测）
- ✅ macOS 10.14+（通过 defaults 命令检测）
- ✅ Linux（通过 Qt 调色板检测）

### 4. 配置持久化

主题配置会自动保存到文件：

```python
# 配置文件位置
# ~/.wallhaven_downloader/theme_config.json

# 配置会在以下情况自动保存：
# 1. 启用/禁用自动主题时
# 2. 切换主题时

# 配置会在程序启动时自动加载
```

**配置文件格式：**

```json
{
  "mode": "深色",
  "auto_enabled": true,
  "transition_duration": 300,
  "follow_system": true
}
```

## 信号与事件

`EnhancedThemeManager` 提供了以下信号：

### theme_changed

主题变化时发射：

```python
theme_manager.theme_changed.connect(on_theme_changed)

def on_theme_changed(theme: str):
    print(f"主题已变化为: {theme}")
    # 更新 UI...
```

### transition_completed

主题过渡动画完成时发射：

```python
theme_manager.transition_completed.connect(on_transition_completed)

def on_transition_completed():
    print("主题过渡动画完成")
    # 执行后续操作...
```

## 与现有 ThemeManager 的兼容性

`EnhancedThemeManager` 继承自 `ThemeManager`，完全兼容现有代码：

```python
# 所有 ThemeManager 的方法都可以使用
theme_manager.set_theme("深色")
theme_manager.get_current_theme()
theme_manager.is_dark_mode()
theme_manager.get_color("primary")
theme_manager.get_all_colors()

# 同时还有增强功能
theme_manager.set_theme_with_transition("浅色", duration=300)
theme_manager.get_apple_color("accent")
theme_manager.enable_auto_theme()
```

## 最佳实践

### 1. 使用单例模式

始终通过 `get_enhanced_theme_manager()` 获取实例：

```python
from wallhaven_downloader.core.enhanced_theme_manager import get_enhanced_theme_manager

theme_manager = get_enhanced_theme_manager()
```

### 2. 连接信号处理主题变化

```python
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_manager = get_enhanced_theme_manager()
        self.theme_manager.theme_changed.connect(self.apply_theme)
    
    def apply_theme(self):
        # 更新 UI 样式
        bg_color = self.theme_manager.get_apple_color("background")
        text_color = self.theme_manager.get_apple_color("text_primary")
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg_color.name()};
                color: {text_color.name()};
            }}
        """)
```

### 3. 使用过渡动画提升用户体验

```python
# 推荐使用带过渡的主题切换
theme_manager.set_theme_with_transition("深色", duration=300)

# 而不是直接切换
# theme_manager.set_theme("深色")  # 不推荐
```

### 4. 启用自动主题提升用户体验

```python
# 在应用启动时启用自动主题
if user_preferences.get("auto_theme", True):
    theme_manager.enable_auto_theme()
```

## 演示程序

运行演示程序查看所有功能：

```bash
python tests/demo_enhanced_theme_manager.py
```

演示程序展示了：
- 主题切换按钮
- 自动主题开关
- 苹果风格颜色显示
- 配置信息显示
- 实时主题过渡效果

## 测试

运行单元测试：

```bash
pytest tests/test_enhanced_theme_manager.py -v
```

测试覆盖：
- ✅ 初始化测试
- ✅ 颜色获取测试
- ✅ 主题切换测试
- ✅ 自动主题测试
- ✅ 配置持久化测试
- ✅ 单例模式测试

## 技术细节

### 继承关系

```
QObject
  └── ThemeManager
        └── EnhancedThemeManager
```

### 依赖关系

```
EnhancedThemeManager
  ├── ThemeManager (父类)
  ├── AppleColorPalette (颜色调色板)
  └── ThemeTransitionManager (过渡管理器)
```

### 配置文件位置

- **Windows**: `C:\Users\<用户名>\.wallhaven_downloader\theme_config.json`
- **macOS**: `/Users/<用户名>/.wallhaven_downloader/theme_config.json`
- **Linux**: `/home/<用户名>/.wallhaven_downloader/theme_config.json`

## 常见问题

### Q: 如何禁用主题过渡动画？

A: 将过渡时长设置为 0：

```python
theme_manager.set_theme_with_transition("深色", duration=0)
```

### Q: 自动主题检测的频率是多少？

A: 默认每 5 秒检查一次系统主题。可以通过修改 `enable_auto_theme()` 中的定时器间隔来调整。

### Q: 配置文件损坏怎么办？

A: 如果配置文件损坏，程序会自动使用默认配置（浅色主题，自动主题禁用）。

### Q: 如何自定义颜色？

A: 可以通过修改 `AppleColorPalette` 类中的颜色定义来自定义颜色方案。

## 更新日志

### v1.0.0 (2026-01-04)

- ✨ 初始版本发布
- ✅ 集成苹果风格颜色调色板
- ✅ 实现主题过渡动画
- ✅ 实现自动主题跟随系统
- ✅ 实现配置持久化
- ✅ 完整的单元测试覆盖
- ✅ 演示程序和文档

## 许可证

本项目采用与 Wallhaven Downloader 相同的许可证。
