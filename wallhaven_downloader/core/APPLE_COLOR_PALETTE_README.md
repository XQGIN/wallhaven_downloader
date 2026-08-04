# Apple Color Palette (苹果颜色调色板)

## 概述

`AppleColorPalette` 类提供了符合苹果设计规范的完整颜色方案，支持日间和夜间两种主题模式。

## 功能特性

### 1. 完整的颜色方案
- **日间主题 (Light Mode)**: 29 种颜色
- **夜间主题 (Dark Mode)**: 29 种颜色
- 包含背景色、文本色、玻璃效果、语义色等

### 2. 颜色类别

#### 背景色系
- `background`: 主背景色
- `surface`: 表面色（卡片、面板）
- `surface_secondary`: 次要表面色

#### 文本色系
- `text_primary`: 主要文本
- `text_secondary`: 次要文本
- `text_tertiary`: 三级文本

#### 玻璃效果
- `glass_normal`: 正常状态
- `glass_hover`: 悬停状态
- `glass_active`: 激活状态

#### 强调色
- `accent`: 主强调色（苹果蓝）
- `accent_hover`: 悬停状态
- `accent_active`: 激活状态

#### 语义色
- `success`: 成功/完成（绿色）
- `warning`: 警告/注意（黄色）
- `error`: 错误/危险（红色）
- `info`: 信息提示（蓝色）

每种语义色都包含 `_hover` 和 `_active` 状态

#### 边框和阴影
- `border`: 边框色
- `separator`: 分隔线
- `shadow`: 普通阴影
- `shadow_elevated`: 提升阴影
- `highlight`: 边缘高光

### 3. 可访问性支持

#### WCAG 标准检查
- `check_contrast_ratio()`: 计算对比度比率
- `meets_wcag_aa()`: 检查是否符合 WCAG AA 标准（4.5:1）
- `meets_wcag_aaa()`: 检查是否符合 WCAG AAA 标准（7:1）
- `validate_color_scheme()`: 验证整个颜色方案的可访问性

#### 验证结果
- **浅色模式**: 主要文本符合 WCAG AAA 标准（15.46:1）
- **深色模式**: 主要文本符合 WCAG AAA 标准（15.63:1）

### 4. 多种颜色格式
- `get_color()`: 返回 QColor 对象
- `get_color_hex()`: 返回十六进制字符串（如 "#007AFF"）
- `get_color_rgba()`: 返回 RGBA 字符串（如 "rgba(255,255,255,200)"）

## 使用示例

### 基本用法

```python
from wallhaven_downloader.core.apple_color_palette import AppleColorPalette

# 创建调色板实例
palette = AppleColorPalette()

# 获取浅色模式的颜色
bg_light = palette.get_color("background", is_dark_mode=False)
text_light = palette.get_color("text_primary", is_dark_mode=False)
accent_light = palette.get_color("accent", is_dark_mode=False)

# 获取深色模式的颜色
bg_dark = palette.get_color("background", is_dark_mode=True)
text_dark = palette.get_color("text_primary", is_dark_mode=True)
accent_dark = palette.get_color("accent", is_dark_mode=True)
```

### 使用单例模式

```python
from wallhaven_downloader.core.apple_color_palette import get_apple_palette

# 获取全局单例实例
palette = get_apple_palette()
accent_color = palette.get_color("accent")
```

### 获取所有颜色

```python
# 获取浅色模式的所有颜色
light_colors = palette.get_all_colors(is_dark_mode=False)

# 获取深色模式的所有颜色
dark_colors = palette.get_all_colors(is_dark_mode=True)
```

### 颜色格式转换

```python
# 十六进制格式
hex_color = palette.get_color_hex("accent")  # "#007aff"

# RGBA 格式
rgba_color = palette.get_color_rgba("glass_normal")  # "rgba(255,255,255,200)"
```

### 对比度检查

```python
from PyQt5.QtGui import QColor

# 检查对比度
text = palette.get_color("text_primary", is_dark_mode=False)
bg = palette.get_color("background", is_dark_mode=False)

ratio = AppleColorPalette.check_contrast_ratio(text, bg)
print(f"对比度: {ratio:.2f}:1")  # 15.46:1

# 检查 WCAG 标准
meets_aa = AppleColorPalette.meets_wcag_aa(text, bg)
meets_aaa = AppleColorPalette.meets_wcag_aaa(text, bg)

print(f"符合 WCAG AA: {meets_aa}")  # True
print(f"符合 WCAG AAA: {meets_aaa}")  # True
```

### 验证颜色方案

```python
# 验证整个颜色方案的可访问性
results = palette.validate_color_scheme(is_dark_mode=False)

for combo, is_valid in results.items():
    print(f"{combo}: {'✓' if is_valid else '✗'}")
```

## 颜色参考

### 浅色模式 (Light Mode)

| 颜色名称 | RGB | HEX | 说明 |
|---------|-----|-----|------|
| background | (245, 245, 247) | #F5F5F7 | 主背景色 |
| surface | (255, 255, 255) | #FFFFFF | 表面色 |
| text_primary | (29, 29, 31) | #1D1D1F | 主要文本 |
| text_secondary | (134, 134, 139) | #86868B | 次要文本 |
| accent | (0, 122, 255) | #007AFF | 苹果蓝 |
| success | (52, 199, 89) | #34C759 | 成功色 |
| warning | (255, 204, 0) | #FFCC00 | 警告色 |
| error | (255, 59, 48) | #FF3B30 | 错误色 |
| info | (90, 200, 250) | #5AC8FA | 信息色 |

### 深色模式 (Dark Mode)

| 颜色名称 | RGB | HEX | 说明 |
|---------|-----|-----|------|
| background | (28, 28, 30) | #1C1C1E | 主背景色 |
| surface | (44, 44, 46) | #2C2C2E | 表面色 |
| text_primary | (245, 245, 247) | #F5F5F7 | 主要文本 |
| text_secondary | (152, 152, 157) | #98989D | 次要文本 |
| accent | (10, 132, 255) | #0A84FF | 苹果蓝 |
| success | (48, 209, 88) | #30D158 | 成功色 |
| warning | (255, 214, 10) | #FFD60A | 警告色 |
| error | (255, 69, 58) | #FF453A | 错误色 |
| info | (100, 210, 255) | #64D2FF | 信息色 |

## 设计原则

1. **符合苹果设计规范**: 颜色值参考 Apple Human Interface Guidelines
2. **可访问性优先**: 所有主要文本颜色符合 WCAG AAA 标准
3. **语义化命名**: 使用清晰、直观的颜色名称
4. **状态支持**: 为交互元素提供 hover 和 active 状态
5. **玻璃效果**: 支持半透明的液态玻璃效果

## 测试

运行测试套件：

```bash
# 运行单元测试
python tests/test_apple_color_palette.py

# 运行演示脚本
python tests/demo_apple_colors.py
```

## 需求验证

本实现满足以下需求：
- **需求 2.4**: 日间主题使用浅色背景和深色文本 ✓
- **需求 2.5**: 夜间主题使用深色背景和浅色文本 ✓
- **需求 2.6**: 为每个主题定义完整的颜色方案 ✓
- **需求 16.3**: 文本和背景对比度符合 WCAG AA 标准 ✓

## 相关文件

- `wallhaven_downloader/core/apple_color_palette.py`: 主实现文件
- `tests/test_apple_color_palette.py`: 单元测试
- `tests/demo_apple_colors.py`: 演示脚本
