#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Wallhaven壁纸下载器 - Briefcase应用入口
"""

import sys
import os

# 确保src目录在Python路径中（获取__main__.py所在目录的父目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)


def main():
    """应用主入口函数"""
    # 初始化日志系统
    from utils.logger import setup_logger
    setup_logger(log_level="INFO")
    
    # 导入必要模块
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtGui import QIcon
    import signal
    import atexit
    
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
                except Exception:
                    child.kill()
        except ImportError:
            if sys.platform == 'win32':
                import subprocess
                pid = os.getpid()
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], 
                              shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def handle_signal(signum, frame):
        """处理信号，确保程序能够优雅退出"""
        QCoreApplication.quit()
    
    # 注册清理函数
    atexit.register(cleanup)
    
    # 设置信号处理
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Wallhaven壁纸下载器")
    app.setApplicationVersion("1.1.0")
    app.setOrganizationName("WallhavenDownloader")
    
    # 设置应用程序图标
    icon_path = os.path.join(parent_dir, 'icon', 'logo.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 导入主窗口
    try:
        from main_window import MainWindow
    except ImportError:
        try:
            import src.main_window as main_window_module
            MainWindow = main_window_module.MainWindow
        except ImportError:
            import importlib.util
            main_window_path = os.path.join(current_dir, 'main_window.py')
            spec = importlib.util.spec_from_file_location("main_window", main_window_path)
            main_window_module = importlib.util.module_from_spec(spec)
            sys.modules["main_window"] = main_window_module
            spec.loader.exec_module(main_window_module)
            MainWindow = main_window_module.MainWindow
    
    # 创建主窗口
    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()
    
    # 运行应用程序
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
