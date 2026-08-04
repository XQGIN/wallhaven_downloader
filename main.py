#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import signal
import atexit

# 添加wallhaven_downloader目录到Python路径
# 打包后：应用源码位于 _internal/wallhaven_downloader/；开发时：项目根下的 wallhaven_downloader/
if getattr(sys, "frozen", False):
    _pkg_dir = os.path.join(
        os.path.dirname(sys.executable), "_internal", "wallhaven_downloader"
    )
else:
    _pkg_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "wallhaven_downloader"
    )
sys.path.insert(0, _pkg_dir)

# 初始化日志系统
from utils.logger import setup_logger

setup_logger(log_level="INFO")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon


def _get_resources_dir():
    """获取资源目录（打包后为 exe 同级 resources；开发时为项目根目录）"""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "resources")
    return os.path.dirname(os.path.abspath(__file__))


def cleanup():
    """清理函数，确保程序退出时关闭所有后台进程"""
    try:
        import psutil

        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        for child in children:
            try:
                child.terminate()
                child.wait(timeout=3)
            except:
                child.kill()
    except ImportError:
        if sys.platform == "win32":
            import subprocess

            pid = os.getpid()
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def handle_signal(signum, frame):
    """处理信号，确保程序能够优雅退出"""
    QCoreApplication.quit()


def main():
    # 注册清理函数
    atexit.register(cleanup)

    # 设置信号处理
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # 创建应用程序
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("Wallhaven壁纸下载器")
    app.setApplicationVersion("2.1.0")
    app.setOrganizationName("WallhavenDownloader")

    # 设置应用程序图标
    app.setWindowIcon(QIcon(os.path.join(_get_resources_dir(), "icon", "logo.png")))

    # 导入主窗口
    try:
        from main_window import MainWindow
    except ImportError:
        try:
            import wallhaven_downloader.main_window as main_window_module

            MainWindow = main_window_module.MainWindow
        except ImportError:
            import importlib.util

            main_window_path = os.path.join(
                os.path.dirname(__file__), "wallhaven_downloader", "main_window.py"
            )
            spec = importlib.util.spec_from_file_location(
                "main_window", main_window_path
            )
            main_window_module = importlib.util.module_from_spec(spec)
            sys.modules["main_window"] = main_window_module
            spec.loader.exec_module(main_window_module)
            MainWindow = main_window_module.MainWindow

    # 创建主窗口
    window = MainWindow()
    window.setWindowIcon(QIcon(os.path.join(_get_resources_dir(), "icon", "logo.png")))
    window.show()

    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
