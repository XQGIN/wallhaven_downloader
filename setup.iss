; Wallhaven壁纸下载器 - Inno Setup安装脚本
; 
; 功能特性:
;   - 支持多线程并发下载，性能提升30-50%
;   - 现代化液态玻璃UI设计，毛玻璃模糊、半透明层、动态光影
;   - 完整的日间/夜间主题系统，自动跟随系统主题
;   - 细腻微动画和流畅交互体验
;   - 智能去重、断点续传、内存优化
;   - 实时图像预览和分页浏览
;   - 可访问性支持，符合WCAG AA标准
;
; 使用方法: 
;   1. 先运行 python build.py 打包程序
;   2. 安装 Inno Setup (https://jrsoftware.org/isdl.php)
;   3. 使用 Inno Setup 编译此脚本
;
; 版本历史:
;   v2.2.0 - 2026-01-06 - 移除测试和示例文件，优化打包配置
;   v2.1.0 - 2025-01-03 - 新增UI美化组件、智能布局、微交互动画
;   v2.0.0 - 2025-12-27 - 优化安装脚本，增强错误处理和用户体验

#define MyAppName "Wallhaven壁纸下载器"
#define MyAppVersion "2.2.0"
#define MyAppPublisher "XQGIN"
#define MyAppURL "https://github.com/XQGIN/wallhaven_downloader"
#define MyAppExeName "WallhavenDownloader.exe"
#define MyAppDescription "Wallhaven壁纸批量下载工具 - 液态玻璃UI设计"
#define MyAppSupportEmail "13083524892@163.com"

[Setup]
; 应用信息
AppId={{8F9B4A5C-2D3E-4F6A-8B7C-9D1E2F3A4B5C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2025 {#MyAppPublisher}
AppComments={#MyAppDescription}

; 安装目录
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; 输出配置
OutputDir=dist\installer
OutputBaseFilename=WallhavenDownloader_v{#MyAppVersion}_Setup
SetupIconFile=icon\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription={#MyAppDescription}
VersionInfoCopyright=Copyright (C) 2025 {#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

; 压缩配置
Compression=lzma2/max
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMADictionarySize=1048576
LZMANumFastBytes=273

; 系统要求
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; 权限
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline

; 界面配置
WizardStyle=modern
WizardSizePercent=100,100
DisableWelcomePage=no
ShowLanguageDialog=auto
AllowNoIcons=yes
AlwaysShowDirOnReadyPage=yes
AlwaysShowGroupOnReadyPage=yes

; 语言
[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

; 自定义消息
[CustomMessages]
chinesesimplified.WelcomeLabel2=这将在您的电脑上安装 [name/ver]。%n%n推荐您在继续之前关闭所有其他应用程序。%n%n本程序是一个功能强大的Wallhaven壁纸批量下载工具，具有以下特色功能：%n• 多线程并发下载，性能提升30-50%%  %n• 液态玻璃UI设计，毛玻璃模糊效果  %n• 完整主题系统，自动跟随系统  %n• 细腻微动画和流畅交互体验  %n• 智能去重、断点续传、内存优化  %n• 可访问性支持，符合WCAG AA标准
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nIt is recommended that you close all other applications before continuing.%n%nThis is a powerful Wallhaven wallpaper batch download tool with the following features:%n• Multi-threaded concurrent downloads, 30-50%% performance boost  %n• Liquid glass UI design with frosted blur effects  %n• Complete theme system with auto system following  %n• Delicate micro-animations and smooth interactions  %n• Intelligent deduplication, resumable downloads, memory optimization  %n• Accessibility support, WCAG AA compliant

chinesesimplified.FinishedLabel=安装程序已经完成在您的电脑上安装 [name]。%n%n程序特色功能：%n• 液态玻璃UI设计，支持主题切换%n• 高性能多线程下载%n• 智能图像预览和管理%n• 细腻微动画和流畅交互%n• 可访问性支持%n%n第一次运行时，程序会自动创建必要的配置文件。%n%n点击"完成"退出安装程序。
english.FinishedLabel=Setup has finished installing [name] on your computer.%n%nKey Features:%n• Liquid glass UI design with theme switching%n• High-performance multi-threaded downloads%n• Smart image preview and management%n• Delicate micro-animations and smooth interactions%n• Accessibility support%n%nThe application will create necessary configuration files on first run.%n%nClick Finish to exit Setup.

; 安装文件
[Files]
; 主程序文件夹（包含所有文件）
Source: "dist\WallhavenDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 文档文件（可选，检查文件存在性）
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "README_EN.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; 配置文件示例
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; 图标和快捷方式
[Icons]
; 开始菜单
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\使用说明"; Filename: "{app}\README.md"; Check: FileExists(ExpandConstant('{app}\README.md'))
Name: "{group}\项目主页"; Filename: "{#MyAppURL}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"

; 桌面快捷方式（使用可执行文件内嵌图标）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; 安装任务
[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式(&D)"; GroupDescription: "附加图标:"
Name: "startupicon"; Description: "开机自动启动(&S)"; GroupDescription: "启动选项:"; Flags: unchecked

; 运行设置
[Run]
; 安装完成后选项
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\README.md"; Description: "查看使用说明"; Flags: shellexec postinstall skipifsilent unchecked; Check: FileExists(ExpandConstant('{app}\README.md'))

; 注册表设置
[Registry]
; 文件关联（可选）
Root: HKCR; Subkey: ".whd"; ValueType: string; ValueName: ""; ValueData: "WallhavenDownloader"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "WallhavenDownloader"; ValueType: string; ValueName: ""; ValueData: "Wallhaven Downloader File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "WallhavenDownloader\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCR; Subkey: "WallhavenDownloader\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

; 卸载信息
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#MyAppVersion}"
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1"; ValueType: string; ValueName: "Publisher"; ValueData: "{#MyAppPublisher}"
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "{#MyAppURL}"
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1"; ValueType: string; ValueName: "HelpLink"; ValueData: "{#MyAppURL}"
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1"; ValueType: string; ValueName: "URLUpdateInfo"; ValueData: "{#MyAppURL}"
