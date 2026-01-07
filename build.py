# -*- coding: utf-8 -*-
"""
Wallhaven Downloader - PyInstaller 打包脚本

自动化打包脚本，确保所有资源和依赖项正确包含在最终可执行文件中。

Usage:
    python build.py

Features:
    - 自动打包所有必要资源（图标、语言文件、配置示例）
    - 包含所有隐藏导入和子模块（包括液态玻璃UI组件）
    - 生成Windows单目录可执行程序
    - 支持PyQt5和所有依赖库
    - 优化的资源管理和错误处理
    - 支持最新的液态玻璃效果、主题系统、动画管理器

Version: 2.2.0
Updated: 2026-01-06
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def clean_build() -> None:
    """清理之前的构建产物"""
    base_dir = Path(__file__).parent.resolve()
    clean_dirs = [base_dir / "dist", base_dir / "build"]
    
    for dir_path in clean_dirs:
        if dir_path.exists():
            print(f"清理目录: {dir_path}")
            shutil.rmtree(dir_path, ignore_errors=True)


def validate_resources(base_dir: Path) -> bool:
    """验证必要资源是否存在"""
    required_files = [
        base_dir / "main.py",
        base_dir / "icon" / "logo.ico",
        base_dir / "icon" / "logo.png",
        base_dir / ".env.example",
    ]
    
    required_dirs = [
        base_dir / "wallhaven_downloader",
        base_dir / "locales",
        base_dir / "icon",
    ]
    
    missing = []
    
    for file_path in required_files:
        if not file_path.exists():
            missing.append(str(file_path))
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing.append(str(dir_path))
    
    if missing:
        print("错误：缺少必要的资源文件：")
        for item in missing:
            print(f"  - {item}")
        return False
    
    return True


def run() -> None:
    """执行PyInstaller打包流程"""
    base_dir = Path(__file__).parent.resolve()
    dist_dir = base_dir / "dist"
    build_dir = base_dir / "build"
    icon_dir = base_dir / "icon"
    locales_dir = base_dir / "locales"
    env_example = base_dir / ".env.example"
    entry_file = base_dir / "main.py"
    icon_file = icon_dir / "logo.png"

    print("="*60)
    print("Wallhaven Downloader v2.2.0 - PyInstaller 打包脚本")
    print("包含液态玻璃效果、主题系统、动画管理器")
    print("="*60)
    
    # 验证资源
    print("\n[1/4] 验证资源文件...")
    if not validate_resources(base_dir):
        sys.exit(1)
    print("✓ 资源文件验证通过")
    
    # 清理旧构建
    print("\n[2/4] 清理旧构建...")
    clean_build()
    
    # 创建输出目录
    print("\n[3/4] 创建输出目录...")
    for path in (dist_dir, build_dir):
        path.mkdir(parents=True, exist_ok=True)
    print(f"✓ 创建目录: {dist_dir}")
    print(f"✓ 创建目录: {build_dir}")

    # 准备资源文件参数
    add_data_args = [
        f"{icon_dir}{os.pathsep}icon",
        f"{locales_dir}{os.pathsep}locales",
        f"{env_example}{os.pathsep}.",
    ]
    
    # 如果settings.json存在，也打包进去
    settings_file = base_dir / "settings.json"
    if settings_file.exists():
        add_data_args.append(f"{settings_file}{os.pathsep}.")

    src_dir = base_dir / "wallhaven_downloader"

    # 隐藏导入模块列表 - 包含所有UI组件和子模块
    hidden_imports = [
        # 核心模块
        "wallhaven_downloader",
        "wallhaven_downloader.main_window",
        "wallhaven_downloader.font_manager",
        
        # core 子包
        "wallhaven_downloader.core",
        "wallhaven_downloader.core.apple_color_palette",
        "wallhaven_downloader.core.configuration_manager",
        "wallhaven_downloader.core.enhanced_theme_manager",
        "wallhaven_downloader.core.i18n_manager",
        "wallhaven_downloader.core.settings_manager",
        "wallhaven_downloader.core.theme_manager",
        "wallhaven_downloader.core.theme_transition_manager",
        
        # ui 子包 - 主要组件
        "wallhaven_downloader.ui",
        "wallhaven_downloader.ui.advanced_effects",
        "wallhaven_downloader.ui.animation_manager",
        "wallhaven_downloader.ui.animation_mixin",
        "wallhaven_downloader.ui.beauty_enhancement_manager",
        "wallhaven_downloader.ui.card_component",
        "wallhaven_downloader.ui.custom_arrows",
        "wallhaven_downloader.ui.custom_title_bar",
        "wallhaven_downloader.ui.empty_state",
        "wallhaven_downloader.ui.enhanced_glass_button",
        "wallhaven_downloader.ui.enhanced_input",
        "wallhaven_downloader.ui.glass_download_task",
        "wallhaven_downloader.ui.glass_effect_widget",
        "wallhaven_downloader.ui.glass_fullscreen_preview",
        "wallhaven_downloader.ui.glass_image_card",
        "wallhaven_downloader.ui.glass_navigation_bar",
        "wallhaven_downloader.ui.glass_progress_indicator",
        "wallhaven_downloader.ui.glass_search_bar",
        "wallhaven_downloader.ui.glass_settings_panel",
        "wallhaven_downloader.ui.glass_settings_panel_clean",
        "wallhaven_downloader.ui.glass_toast",
        "wallhaven_downloader.ui.icon_manager",
        "wallhaven_downloader.ui.image_preview",
        "wallhaven_downloader.ui.layout_manager",
        "wallhaven_downloader.ui.micro_interactions",
        "wallhaven_downloader.ui.modern_progress",
        "wallhaven_downloader.ui.modern_ui_manager",
        "wallhaven_downloader.ui.smart_layout",
        "wallhaven_downloader.ui.theme_transition",
        "wallhaven_downloader.ui.toast_notification",
        "wallhaven_downloader.ui.typography_system",
        
        # ui.animation 子包
        "wallhaven_downloader.ui.animation",
        "wallhaven_downloader.ui.animation.enhanced_animation_manager",
        "wallhaven_downloader.ui.animation.micro_animation_controller",
        
        # ui.liquid_glass 子包
        "wallhaven_downloader.ui.liquid_glass",
        "wallhaven_downloader.ui.liquid_glass.blur_layer_manager",
        "wallhaven_downloader.ui.liquid_glass.enhanced_glass_panel",
        "wallhaven_downloader.ui.liquid_glass.glass_panel_factory",
        "wallhaven_downloader.ui.liquid_glass.linux_blur_provider",
        "wallhaven_downloader.ui.liquid_glass.liquid_glass_manager",
        "wallhaven_downloader.ui.liquid_glass.macos_blur_provider",
        "wallhaven_downloader.ui.liquid_glass.platform_adapter",
        "wallhaven_downloader.ui.liquid_glass.repaint_optimizer",
        "wallhaven_downloader.ui.liquid_glass.windows_blur_provider",
        
        # utils 子包
        "wallhaven_downloader.utils",
        "wallhaven_downloader.utils.accessibility_manager",
        "wallhaven_downloader.utils.degradation_strategies",
        "wallhaven_downloader.utils.exceptions",
        "wallhaven_downloader.utils.lazy_loader",
        "wallhaven_downloader.utils.logger",
        "wallhaven_downloader.utils.performance",
        "wallhaven_downloader.utils.performance_degradation_manager",
        "wallhaven_downloader.utils.performance_optimizer",
        "wallhaven_downloader.utils.resource_helper",
        "wallhaven_downloader.utils.resource_loader",
        "wallhaven_downloader.utils.startup_optimizer",
        "wallhaven_downloader.utils.system_accessibility_detector",
        "wallhaven_downloader.utils.text_scale_manager",
        
        # workers 子包
        "wallhaven_downloader.workers",
        "wallhaven_downloader.workers.download_thread",
        
        # PyQt5 相关
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtOpenGL",
        "PyQt5.QtSvg",
        
        # 其他依赖
        "requests",
        "PIL",
        "PIL.Image",
        "PIL.ImageFilter",
        "PIL.ImageEnhance",
        "psutil",
        "loguru",
        "dotenv",
        "json",
        "threading",
        "concurrent.futures",
        "queue",
        "time",
        "datetime",
        "pathlib",
        "typing",
    ]

    # 构建PyInstaller命令
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        "WallhavenDownloader",
        "--windowed",  # Windows下不显示控制台
        "--icon",
        str(icon_file),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        "--paths",
        str(src_dir),
        "--specpath",
        str(base_dir),
    ]

    # 添加资源文件
    for data_arg in add_data_args:
        cmd.extend(["--add-data", data_arg])

    # 添加隐藏导入
    for module_name in hidden_imports:
        cmd.extend(["--hidden-import", module_name])

    # 添加入口文件
    cmd.append(str(entry_file))

    # 执行打包
    print("\n[4/4] 执行PyInstaller打包...")
    print(f"\n命令: {' '.join(cmd[:10])}...")
    print("\n打包进行中，请稍候...\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n" + "="*60)
        print("✓ 打包成功！")
        print("="*60)
        print(f"\n输出目录: {dist_dir / 'WallhavenDownloader'}")
        print("\n后续步骤:")
        print("  1. 测试可执行文件：")
        print(f"     {dist_dir / 'WallhavenDownloader' / 'WallhavenDownloader.exe'}")
        print("  2. 使用Inno Setup生成安装包：")
        print("     打开setup.iss并编译")
        print("\n" + "="*60)
        
    except subprocess.CalledProcessError as exc:
        print("\n" + "="*60)
        print(f"✗ 打包失败，退出码: {exc.returncode}")
        print("="*60)
        sys.exit(1)
    except FileNotFoundError:
        print("\n" + "="*60)
        print("✗ 错误：未找到PyInstaller")
        print("="*60)
        print("\n请先安装PyInstaller:")
        print("  pip install pyinstaller")
        sys.exit(1)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\n用户取消打包")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
