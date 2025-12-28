# 国际化功能说明

## 功能概述

Wallhaven壁纸下载器现已支持中英文双语切换功能。

## 使用方法

### 切换语言

1. 启动程序后,默认使用简体中文界面
2. 点击左侧面板的"设置"按钮
3. 在设置对话框的"界面设置"部分,找到"语言"选项
4. 从下拉列表中选择:
   - **简体中文** (zh_CN)
   - **English** (en_US)
5. 点击"确定"按钮保存设置
6. 界面将立即刷新为新语言,无需重启程序

## 技术实现

### 核心模块

1. **i18n_manager.py** - 国际化管理器
   - 提供翻译文本加载和管理
   - 支持语言切换
   - 支持嵌套键访问和参数格式化

2. **翻译文件**
   - `locales/zh_CN.json` - 简体中文翻译
   - `locales/en_US.json` - 英文翻译

3. **集成位置**
   - SettingsManager - 管理语言配置
   - MainWindow - 主窗口多语言支持
   - SettingsDialog - 设置对话框多语言支持

### 项目结构

```
wallhaven_downloader/
├── locales/               # 翻译文件目录
│   ├── zh_CN.json        # 简体中文
│   └── en_US.json        # 英文
├── src/
│   ├── core/
│   │   ├── i18n_manager.py      # 国际化管理器
│   │   └── settings_manager.py  # 配置管理(已更新)
│   └── main_window.py    # 主窗口(已更新)
└── settings.json          # 用户设置(包含language字段)
```

### 翻译文件格式

翻译文件使用JSON格式,支持嵌套结构:

```json
{
  "app": {
    "name": "应用名称",
    "version": "版本号"
  },
  "settings": {
    "title": "设置"
  }
}
```

访问翻译时使用点号分隔: `i18n.t("app.name")`

## 扩展说明

### 添加新语言

1. 在`locales/`目录下创建新的JSON文件,如`ja_JP.json`
2. 复制`zh_CN.json`或`en_US.json`的结构
3. 翻译所有文本为目标语言
4. 在`i18n_manager.py`中添加语言到`SUPPORTED_LANGUAGES`字典
5. 在设置对话框中添加新语言选项

### 添加新翻译文本

1. 在`zh_CN.json`和`en_US.json`中添加相同的键
2. 在代码中使用`self.i18n.t("your.key")`访问翻译

## 注意事项

- 语言切换后界面会立即刷新,无需重启程序
- 所有界面文本都应通过翻译系统访问,避免硬编码
- 保持所有语言文件的键结构一致
- 使用描述性的键名,便于理解和维护

## 开发规范

1. 所有用户可见文本必须通过i18n系统
2. 翻译键应使用小写字母和下划线
3. 使用点号分隔命名空间
4. 保持翻译文件同步更新
