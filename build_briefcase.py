# -*- coding: utf-8 -*-
"""
Briefcase 打包脚本
使用 Briefcase 打包应用程序
"""

import os
import subprocess
import sys
from pathlib import Path


def check_briefcase_installed() -> bool:
    """检查 Briefcase 是否已安装"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "briefcase", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def install_briefcase() -> None:
    """安装 Briefcase"""
    print("正在安装 Briefcase...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "briefcase>=0.3.18"],
            check=True
        )
        print("Briefcase 安装成功!")
    except subprocess.CalledProcessError as e:
        print(f"Briefcase 安装失败: {e}")
        sys.exit(1)


def create_app() -> None:
    """创建应用程序结构"""
    print("\n步骤 1/4: 创建应用程序结构...")
    try:
        subprocess.run(
            [sys.executable, "-m", "briefcase", "create"],
            check=True,
            cwd=Path(__file__).parent
        )
        print("应用程序结构创建成功!")
    except subprocess.CalledProcessError as e:
        print(f"创建应用程序结构失败: {e}")
        sys.exit(1)


def build_app() -> None:
    """构建应用程序"""
    print("\n步骤 2/4: 构建应用程序...")
    try:
        subprocess.run(
            [sys.executable, "-m", "briefcase", "build"],
            check=True,
            cwd=Path(__file__).parent
        )
        print("应用程序构建成功!")
    except subprocess.CalledProcessError as e:
        print(f"构建应用程序失败: {e}")
        sys.exit(1)


def update_app() -> None:
    """更新应用程序资源"""
    print("\n步骤 3/4: 更新应用程序资源...")
    try:
        subprocess.run(
            [sys.executable, "-m", "briefcase", "update"],
            check=True,
            cwd=Path(__file__).parent
        )
        print("应用程序资源更新成功!")
    except subprocess.CalledProcessError as e:
        print(f"更新应用程序资源失败: {e}")
        print("继续执行下一步...")


def package_app() -> None:
    """打包应用程序"""
    print("\n步骤 4/4: 打包应用程序...")
    try:
        subprocess.run(
            [sys.executable, "-m", "briefcase", "package"],
            check=True,
            cwd=Path(__file__).parent
        )
        print("应用程序打包成功!")
    except subprocess.CalledProcessError as e:
        print(f"打包应用程序失败: {e}")
        sys.exit(1)


def show_output_info() -> None:
    """显示输出信息"""
    base_dir = Path(__file__).parent
    
    print("\n" + "="*60)
    print("打包完成!")
    print("="*60)
    
    if sys.platform == "win32":
        dist_path = base_dir / "dist"
        print(f"\n安装程序位置: {dist_path}")
        print("Windows 平台会生成 MSI 安装包")
    elif sys.platform == "darwin":
        dist_path = base_dir / "dist"
        print(f"\n应用程序位置: {dist_path}")
        print("macOS 平台会生成 DMG 镜像文件")
    else:
        dist_path = base_dir / "dist"
        print(f"\n应用程序位置: {dist_path}")
        print("Linux 平台会生成相应的安装包")
    
    print("\n提示:")
    print("1. 首次打包可能需要较长时间下载依赖")
    print("2. 如需重新打包，可以直接运行此脚本")
    print("3. 如需测试应用，运行: briefcase dev")
    print("4. 如需运行已打包应用，运行: briefcase run")


def main() -> None:
    """主函数"""
    print("Wallhaven壁纸下载器 - Briefcase打包工具")
    print("="*60)
    
    # 检查并安装 Briefcase
    if not check_briefcase_installed():
        print("未检测到 Briefcase，开始安装...")
        install_briefcase()
    else:
        print("Briefcase 已安装")
    
    # 执行打包流程
    try:
        create_app()
        build_app()
        update_app()
        package_app()
        show_output_info()
    except KeyboardInterrupt:
        print("\n\n打包过程被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n打包过程出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
