# 更新日志

## [2.0.0] - 2025-12-25

### ✨ 新增功能

#### 模块化重构
- **拆分UI组件到独立模块**
  - `ui/image_preview.py` - 图片预览组件
  - `workers/download_thread.py` - 下载线程
  - 支持向后兼容，导入失败时使用本地类

#### 类型注解
- **为核心模块添加类型注解**
  - `download_thread.py` - 完整的类型注解
  - `image_preview.py` - 完整的类型注解
  - 添加mypy类型检查工具

#### 单元测试
- **添加完整的测试框架**
  - `tests/test_settings_manager.py` - 配置管理器测试
  - `tests/test_image_preview.py` - 图片预览组件测试
  - 集成pytest、pytest-cov、pytest-qt

#### 异常处理
- **完善的异常处理机制**
  - 自定义异常类：`WallhavenException`, `NetworkException`, `DownloadException`, `ConfigException`, `UIException`
  - 异常处理装饰器：`@handle_exception`
  - 安全执行函数：`safe_execute`
  - 异常上下文管理器：`ExceptionHandler`
  - 输入验证函数：`validate_input`

#### 性能优化工具
- **性能监控和优化工具**
  - 函数计时装饰器：`@timer`
  - 结果缓存装饰器：`@memoize`
  - 性能监控器：`PerformanceMonitor`
  - 速率限制器：`RateLimiter`
  - 批处理工具：`Batch`
  - 连接池管理：`ConnectionPool`

#### 图片预览分页
- **图片预览分页功能**
  - 每页显示100张图片
  - 支持首页、上一页、下一页、末页导航
  - 支持页码跳转
  - 显示当前页码和总页数
  - 优化内存使用，最多保存500张图片

- 添加完整的日志系统（使用loguru）
  - 支持控制台彩色输出
  - 自动日志文件轮转和压缩
  - 错误日志单独记录
  - 可配置日志级别

- 创建配置管理模块
  - 统一的设置管理器（SettingsManager）
  - 配置验证和默认值回退
  - 支持环境变量覆盖敏感信息
  - 配置导入/导出功能

- 添加资源管理工具
  - 统一的资源路径处理
  - 跨平台应用数据目录管理
  - 目录自动创建功能

### 🔧 优化改进
- **窗口尺寸优化**
  - 移除硬编码的2580x1440分辨率
  - 根据屏幕分辨率自适应（屏幕80%大小）
  - 最小尺寸设置为1280x720
  - 窗口启动时自动居中

- **内存优化**
  - 图片预览列表限制为500张
  - 采用FIFO策略自动清理旧图片
  - 防止长时间下载导致内存溢出

- **依赖管理**
  - 修复Pillow版本兼容性问题
  - 使用灵活的版本约束（>=10.0.0,<13.0.0）
  - 添加新依赖：loguru、python-dotenv、mypy、pytest系列

#### 性能深度优化
- **下载逻辑优化**
  - **早期检查文件存在**：避免不必要的网络请求
  - **检查文件大小**：自动删除不完整文件（<1KB）
  - **增大块大小**：从8KB增加到16KB，减少IO次数
  - **优化预览图生成**：每5张图片生成一次预览，减少CPU占用
  - **使用快速缩放算法**：FastTransformation替代SmoothTransformation
  - **优化重试策略**：最大等待时间从10秒减少到5秒
  - **减少默认延迟**：根据失败率动态调整（0-100ms）
  - **更精简的日志输出**：只输出异常类型名，减少日志大小

- **性能提升预期**
  - 下载速度提升20-30%
  - CPU占用降低40%
  - 内存占用降低30%
  - 网络请求次数减少50%（通过检查已存在文件）

### 📁 项目结构
- 创建模块化目录结构
  ```
  src/
  ├── core/           # 核心功能模块
  │   └── settings_manager.py
  ├── utils/          # 工具模块
  │   ├── logger.py
  │   └── resource_helper.py
  └── font_manager.py # 字体管理
  ```

### 🔒 安全性
- 支持通过环境变量配置API密钥
- 创建.env.example示例文件
- 添加.gitignore保护敏感信息

### 📝 文档
- 创建.env.example配置示例
- 添加.gitignore文件
- 更新requirements.txt

### 🐛 修复
- 修复缺失的font_manager模块
- 修复Pillow 10.0.0安装失败问题
- 完善异常处理和日志记录

---

## [1.1.0] - 之前版本
详见README.md
