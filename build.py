#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WallhavenDownloader PyInstaller 打包脚本（onedir / 非单文件模式）。

执行流程：
  1. 清理旧的 build/ dist/ 产物
  2. 调用 PyInstaller 按 WallhavenDownloader.spec 构建
  3. 部署资源文件到 dist/WallhavenDownloader/resources/（与库文件夹 _internal 分离）
  4. 创建运行时目录 logs/
  5. 生成《目录结构说明.md》

用法：
    .\\venv\\Scripts\\python.exe build.py
"""

import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
VENV_PY = os.path.join(ROOT, "venv", "Scripts", "python.exe")
APP_NAME = "WallhavenDownloader"
APP_VERSION = "2.2.0"
SPEC = os.path.join(ROOT, f"{APP_NAME}.spec")

DIST = os.path.join(ROOT, "dist")
BUILD = os.path.join(ROOT, "build")
DIST_APP = os.path.join(DIST, APP_NAME)
INTERNAL = os.path.join(DIST_APP, "_internal")
RESOURCES = os.path.join(DIST_APP, "resources")
LOGS = os.path.join(DIST_APP, "logs")

# 需要部署到 resources/ 的资源（源目录/文件 -> 目标相对路径）
RESOURCE_DIRS = {
    os.path.join(ROOT, "icon"): "icon",
    os.path.join(ROOT, "locales"): "locales",
}
RESOURCE_FILES = {
    os.path.join(ROOT, ".env.example"): ".env.example",
    os.path.join(ROOT, "LICENSE"): "LICENSE",
}


def log(msg):
    print(f"[build] {msg}", flush=True)


def clean():
    log("清理旧产物 build/ dist/ ...")
    for p in (BUILD, DIST):
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)


def run_pyinstaller():
    log("调用 PyInstaller 构建（onedir 模式）...")
    cmd = [VENV_PY, "-m", "PyInstaller", "--noconfirm", "--clean", SPEC]
    subprocess.check_call(cmd, cwd=ROOT)


def deploy_resources():
    log("部署资源文件到 resources/ ...")
    os.makedirs(os.path.join(RESOURCES, "icon"), exist_ok=True)
    os.makedirs(os.path.join(RESOURCES, "locales"), exist_ok=True)

    for src_dir, dst_name in RESOURCE_DIRS.items():
        if not os.path.isdir(src_dir):
            log(f"  警告: 源目录不存在，跳过: {src_dir}")
            continue
        dst_dir = os.path.join(RESOURCES, dst_name)
        os.makedirs(dst_dir, exist_ok=True)
        for f in os.listdir(src_dir):
            sf = os.path.join(src_dir, f)
            if os.path.isfile(sf):
                shutil.copy2(sf, os.path.join(dst_dir, f))

    for src_file, dst_name in RESOURCE_FILES.items():
        if os.path.isfile(src_file):
            shutil.copy2(src_file, os.path.join(RESOURCES, dst_name))
        else:
            log(f"  警告: 源文件不存在，跳过: {src_file}")

    # 生成默认 settings.json（清空 API 密钥，避免泄露开发者私有配置）
    default_settings = {
        "api_key": "",
        "theme": "浅色",
        "glass_transparency": 200,
        "images_per_page": 64,
        "download_timeout": 30,
        "preview_size": "中 (200x200)",
        "download_dir": "",
        "download_method": "latest",
        "category": "all",
        "purity": "sfw",
        "search_query": "",
        "page_count": 1,
        "concurrent_downloads": 5,
        "wallpaper_ratio": "全部",
        "start_page": 1,
        "show_filename": False,
        "language": "zh_CN",
    }
    with open(os.path.join(RESOURCES, "settings.json"), "w", encoding="utf-8") as f:
        json.dump(default_settings, f, indent=4, ensure_ascii=False)
    log("  已生成默认 settings.json（api_key 已清空）")


def create_runtime_dirs():
    log("创建运行时目录 logs/ ...")
    os.makedirs(LOGS, exist_ok=True)


def write_structure_doc():
    doc_path = os.path.join(DIST_APP, "目录结构说明.md")
    log(f"生成目录结构说明: {os.path.basename(doc_path)} ...")

    def tree_lines():
        yield f"{APP_NAME}/"
        yield f"├── {APP_NAME}.exe            # 主程序可执行文件（根目录，双击运行）"
        yield f"├── _internal/                # 库文件夹：Python 运行时与所有第三方依赖"
        yield f"│   ├── Python311.dll         #   Python 解释器运行时"
        yield f"│   ├── base_library.zip      #   Python 标准库归档"
        yield f"│   ├── PyQt5/                #   PyQt5 及 Qt 动态库/插件"
        yield f"│   ├── PIL/                  #   Pillow 图像处理库"
        yield f"│   ├── requests/             #   HTTP 请求库（纯 Python，冻结于 PYZ）"
        yield f"│   ├── urllib3/              #   HTTP 底层库（纯 Python，冻结于 PYZ）"
        yield f"│   ├── loguru/               #   日志库（纯 Python，冻结于 PYZ）"
        yield f"│   ├── psutil/               #   系统进程工具"
        yield f"│   ├── dotenv/               #   环境变量加载（纯 Python，冻结于 PYZ）"
        yield f"│   └── wallhaven_downloader/ #   应用源码（运行时加入 sys.path）"
        yield f"│       ├── core/             #     设置/主题/国际化等"
        yield f"│       ├── ui/               #     界面组件（含 liquid_glass/animation）"
        yield f"│       ├── utils/            #     日志/资源/性能等"
        yield f"│       ├── workers/          #     下载线程"
        yield f"│       ├── main_window.py    #     主窗口"
        yield f"│       └── font_manager.py   #     字体管理"
        yield f"├── resources/                # 资源目录：图标 / 语言 / 配置"
        yield f"│   ├── icon/                 #   程序图标（logo.ico / logo.png）"
        yield f"│   ├── locales/              #   多语言文件（zh_CN.json / en_US.json）"
        yield f"│   ├── settings.json         #   用户设置（首次运行可自动生成）"
        yield f"│   ├── .env.example          #   环境变量配置模板"
        yield f"│   └── LICENSE               #   许可证（MIT）"
        yield f"├── logs/                     # 运行时日志目录（程序自动写入）"
        yield f"└── 目录结构说明.md           # 本说明文档"

    content = []
    content.append("# Wallhaven壁纸下载器 — 目录结构说明\n")
    content.append(f"- 版本：{APP_VERSION}")
    content.append("- 作者：XQGIN")
    content.append("- 项目地址：https://github.com/XQGIN/wallhaven_downloader")
    content.append("- 许可证：MIT\n")
    content.append("## 一、目录结构\n")
    content.append("```")
    content.extend(tree_lines())
    content.append("```\n")
    content.append("## 二、各目录说明\n")
    content.append("| 目录/文件 | 说明 |\n|---|---|")
    content.append(
        f"| {APP_NAME}.exe | 主程序可执行文件，双击即可启动，无需安装 Python 环境。 |"
    )
    content.append(
        "| _internal/ | **库文件夹**：包含 Python 运行时、所有第三方依赖库及应用模块，程序运行所必需，请勿删除。 |"
    )
    content.append(
        "| resources/ | **资源目录**：程序运行所需的图标、多语言文件与配置文件。用户设置保存于此。 |"
    )
    content.append(
        "| logs/ | **运行时日志**：程序自动生成，用于排查问题，可安全删除。 |\n"
    )
    content.append("## 三、运行与可移植性\n")
    content.append(
        "1. 将整个 `WallhavenDownloader/` 文件夹复制到任意位置（建议保持 `_internal/` 与 `resources/` 与主程序同级）。\n"
        "2. 双击 `WallhavenDownloader.exe` 启动程序，无需额外安装依赖。\n"
        "3. 程序在相同 Windows 操作系统环境下可直接运行（x64）。\n"
        "4. 如需自定义 Wallhaven API Key，可将 `resources/.env.example` 复制为 `resources/.env` 并填写。\n"
    )
    content.append("## 四、版本信息\n")
    content.append(
        "版本信息已嵌入可执行文件（右键 → 属性 → 详细信息 可查看），包含：\n"
    )
    content.append("- 产品名称、文件说明、版本号")
    content.append("- 公司名称：XQGIN")
    content.append("- 版权声明：Copyright (c) 2026 XQGIN. MIT License.")
    content.append("- 项目地址：https://github.com/XQGIN/wallhaven_downloader\n")

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))


def main():
    if not os.path.isfile(VENV_PY):
        log(f"错误: 未找到虚拟环境 Python: {VENV_PY}")
        sys.exit(1)
    if not os.path.isfile(SPEC):
        log(f"错误: 未找到 spec 文件: {SPEC}")
        sys.exit(1)

    clean()
    run_pyinstaller()
    deploy_resources()
    create_runtime_dirs()
    write_structure_doc()

    log("打包完成。")
    log(f"  输出目录: {DIST_APP}")
    log(f'  主程序:   {os.path.join(DIST_APP, APP_NAME + ".exe")}')
    log(f"  资源目录: {RESOURCES}")
    log(f"  库目录:   {INTERNAL}")


if __name__ == "__main__":
    main()
