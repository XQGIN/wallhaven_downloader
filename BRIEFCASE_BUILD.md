# Briefcase 打包使用说明

本项目已配置为使用 Briefcase 进行打包，替代原有的 PyInstaller 方案。

## 🚀 快速开始

### 方法一：使用自动化打包脚本（推荐）

直接运行打包脚本，自动完成所有步骤：

```bash
python build_briefcase.py
```

脚本会自动：
1. 检查并安装 Briefcase（如果未安装）
2. 创建应用程序结构
3. 构建应用程序
4. 更新资源文件
5. 打包成安装程序

### 方法二：手动执行 Briefcase 命令

#### 1. 安装 Briefcase

```bash
pip install briefcase>=0.3.18
```

或者安装所有依赖：

```bash
pip install -r requirements.txt
```

#### 2. 创建应用程序

首次使用需要创建应用程序结构：

```bash
briefcase create
```

#### 3. 构建应用程序

```bash
briefcase build
```

#### 4. 更新资源（如果修改了代码或资源）

```bash
briefcase update
```

#### 5. 打包应用程序

```bash
briefcase package
```

此命令会生成平台特定的安装包：
- **Windows**: MSI 安装包
- **macOS**: DMG 镜像文件
- **Linux**: AppImage/DEB/RPM（根据发行版）

## 🧪 开发测试

### 在开发模式下运行

直接在开发环境运行应用（无需打包）：

```bash
briefcase dev
```

这对于快速测试非常有用，会使用本地 Python 环境运行。

### 运行已打包的应用

```bash
briefcase run
```

## 📦 输出文件

打包完成后，输出文件位于 `dist` 目录：

```
dist/
├── Wallhaven壁纸下载器-1.1.0.msi  (Windows)
├── Wallhaven壁纸下载器-1.1.0.dmg  (macOS)
└── wallhaven_downloader-1.1.0.AppImage  (Linux)
```

## 🔧 配置说明

### pyproject.toml

所有 Briefcase 配置都在 `pyproject.toml` 文件中：

- **项目信息**：名称、版本、作者等
- **应用配置**：图标、启动屏幕、资源文件
- **依赖管理**：Python 包依赖、系统依赖
- **平台特定配置**：Windows、macOS、Linux 各自的配置

### 关键配置项

```toml
[tool.briefcase.app.wallhaven_downloader]
formal_name = "Wallhaven壁纸下载器"  # 应用显示名称
sources = ['src']                     # 源代码目录
icon = "icon/logo"                    # 应用图标
resources = ['locales', 'icon']       # 额外资源文件
```

## ⚙️ 常用命令

| 命令 | 说明 |
|------|------|
| `briefcase create` | 创建应用程序结构 |
| `briefcase dev` | 开发模式运行 |
| `briefcase build` | 构建应用程序 |
| `briefcase run` | 运行已构建的应用 |
| `briefcase update` | 更新代码和资源 |
| `briefcase package` | 打包成安装程序 |
| `briefcase publish` | 发布到应用商店 |

## 🔄 重新打包

如果修改了代码或资源文件，重新打包：

```bash
# 方法一：使用脚本（推荐）
python build_briefcase.py

# 方法二：手动执行
briefcase update
briefcase build
briefcase package
```

## 📝 注意事项

1. **首次打包时间较长**：Briefcase 需要下载 Python 嵌入式版本和依赖，可能需要 10-20 分钟
2. **网络要求**：首次打包需要稳定的网络连接
3. **磁盘空间**：确保有足够的磁盘空间（建议至少 500MB）
4. **资源文件**：
   - 图标文件自动从 PNG 转换为平台特定格式
   - `locales` 和 `icon` 目录会自动打包进应用
5. **依赖版本**：确保 `pyproject.toml` 中的依赖版本与 `requirements.txt` 保持一致

## 🆚 Briefcase vs PyInstaller

### Briefcase 优势

- ✅ **跨平台一致性**：统一的配置和打包流程
- ✅ **现代化**：支持最新的 Python 版本和特性
- ✅ **应用商店支持**：可直接发布到 Windows Store、Mac App Store 等
- ✅ **标准化配置**：使用 `pyproject.toml` 标准配置文件
- ✅ **更好的图标支持**：自动处理多种分辨率图标
- ✅ **代码签名集成**：内置对 macOS/Windows 代码签名的支持

### PyInstaller 优势

- ✅ **更小的包体积**：生成的安装包通常更小
- ✅ **更快的打包速度**：增量打包速度更快
- ✅ **更多配置选项**：可精细控制打包过程

## 🐛 常见问题

### Q: 打包失败怎么办？

1. 确保 Python 版本 >= 3.7
2. 检查网络连接是否稳定
3. 清理临时文件：删除 `build` 目录后重试
4. 查看详细错误日志

### Q: 如何修改应用图标？

替换 `icon/logo.png` 和 `icon/logo.ico` 文件，然后重新打包。

### Q: 如何减小安装包体积？

1. 移除不必要的依赖
2. 使用虚拟环境打包，避免包含多余的包
3. 考虑使用 Briefcase 的 `--adhoc-sign` 选项（macOS）

### Q: 开发模式运行报错？

确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

## 📚 更多信息

- [Briefcase 官方文档](https://briefcase.readthedocs.io/)
- [Briefcase GitHub](https://github.com/beeware/briefcase)
- [BeeWare 项目](https://beeware.org/)

## 🔗 相关文件

- `pyproject.toml` - Briefcase 配置文件
- `build_briefcase.py` - 自动化打包脚本
- `src/__main__.py` - 应用入口文件
- `requirements.txt` - Python 依赖列表
