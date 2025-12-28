; Wallhaven壁纸下载器 - Inno Setup安装脚本
; 使用方法: 
;   1. 先运行 python build.py 打包程序
;   2. 安装 Inno Setup (https://jrsoftware.org/isdl.php)
;   3. 使用 Inno Setup 编译此脚本
;
; 版本历史:
;   v2.0.0 - 2025-12-27 - 优化安装脚本，增强错误处理和用户体验

#define MyAppName "Wallhaven壁纸下载器"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "XQGIN"
#define MyAppURL "https://github.com/XQGIN/wallhaven_downloader"
#define MyAppExeName "WallhavenDownloader.exe"
#define MyAppDescription "Wallhaven壁纸批量下载工具"
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
chinesesimplified.WelcomeLabel2=这将在您的电脑上安装 [name/ver]。%n%n推荐您在继续之前关闭所有其他应用程序。%n%n本程序是一个功能强大的Wallhaven壁纸批量下载工具，支持多线程下载、智能去重、断点续传等功能。
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nIt is recommended that you close all other applications before continuing.%n%nThis is a powerful Wallhaven wallpaper batch download tool that supports multi-threaded downloading, intelligent deduplication, and resumable downloads.

chinesesimplified.FinishedLabel=安装程序已经完成在您的电脑上安装 [name]。%n%n第一次运行时，程序会自动创建必要的配置文件。%n%n点击"完成"退出安装程序。
english.FinishedLabel=Setup has finished installing [name] on your computer.%n%nThe application will create necessary configuration files on first run.%n%nClick Finish to exit Setup.

; 安装文件
[Files]
; 主程序文件夹（包含所有文件）
Source: "dist\WallhavenDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 文档文件（可选，检查文件存在性）
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "README_EN.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "BRIEFCASE_BUILD.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "INTERNATIONALIZATION.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; 配置文件示例
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; 语言文件（必需，已在dist中打包，这里仅作备份）
; locales目录已包含在dist\WallhavenDownloader中

; 图标资源（必需，已在dist中打包，这里仅作备份）
; icon目录已包含在dist\WallhavenDownloader中

; 注意：主可执行文件及所有资源（icon、locales、.env.example）已包含在dist\WallhavenDownloader\*中

; 图标和快捷方式
[Icons]
; 开始菜单
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"; IconFilename: "{app}\icon\logo.ico"
Name: "{group}\使用说明"; Filename: "{app}\README.md"; Check: FileExists(ExpandConstant('{app}\README.md'))
Name: "{group}\更新日志"; Filename: "{app}\CHANGELOG.md"; Check: FileExists(ExpandConstant('{app}\CHANGELOG.md'))
Name: "{group}\项目主页"; Filename: "{#MyAppURL}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"

; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon\logo.ico"; Tasks: desktopicon

; 快速启动栏已移除（Windows 7 不再支持）
; Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

; 安装任务
[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式(&D)"; GroupDescription: "附加图标:"
; Windows 7 已不再支持，移除快速启动栏选项
; Name: "quicklaunchicon"; Description: "创建快速启动栏图标(&Q)"; GroupDescription: "附加图标:"; Flags: unchecked; OnlyBelowVersion: 6.1
Name: "startupicon"; Description: "开机自动启动(&S)"; GroupDescription: "启动选项:"; Flags: unchecked

; 运行设置
[Run]
; 安装完成后选项
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\README.md"; Description: "查看使用说明"; Flags: shellexec postinstall skipifsilent unchecked; Check: FileExists(ExpandConstant('{app}\README.md'))

; 卸载设置
[UninstallDelete]
; 删除运行时生成的文件（仅在用户选择删除数据时）
Type: filesandordirs; Name: "{app}\logs"; Check: ShouldDeleteUserData
Type: filesandordirs; Name: "{app}\Downloads"; Check: ShouldDeleteUserData
Type: files; Name: "{app}\settings.json"; Check: ShouldDeleteUserData
Type: files; Name: "{app}\.env"; Check: ShouldDeleteUserData
; 删除临时文件和缓存（始终删除）
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\_internal\__pycache__"
Type: files; Name: "{app}\*.pyc"
Type: files; Name: "{app}\*.pyo"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.tmp"
; 删除PyInstaller可能生成的spec文件
Type: files; Name: "{app}\*.spec"

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

; 代码段
[Code]
var
  DeleteUserDataGlobal: Boolean;

// 检查是否应该删除用户数据
function ShouldDeleteUserData(): Boolean;
begin
  Result := DeleteUserDataGlobal;
end;

// 检测是否已安装旧版本
function InitializeSetup(): Boolean;
var
  OldVersion: String;
begin
  Result := True;
  
  // 检查是否已安装
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1', 'DisplayVersion', OldVersion) then
  begin
    if MsgBox('检测到已安装版本 ' + OldVersion + '，是否继续安装新版本 {#MyAppVersion}？' + #13#10 + #13#10 + '继续将会覆盖旧版本。', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // 检查程序是否正在运行
      if CheckForMutexes('{#MyAppName}') then
      begin
        MsgBox('检测到程序正在运行，请先关闭程序后再继续安装。', mbError, MB_OK);
        Result := False;
      end;
    end
    else
    begin
      Result := False;
    end;
  end;
end;

// 安装完成后的处理
procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvExamplePath, EnvPath: String;
  LocalesDir, IconDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    // 检查并创建必要的资源目录（如果不存在）
    LocalesDir := ExpandConstant('{app}\locales');
    IconDir := ExpandConstant('{app}\icon');
    
    if not DirExists(LocalesDir) then
      CreateDir(LocalesDir);
    if not DirExists(IconDir) then
      CreateDir(IconDir);
    
    // 如果.env文件不存在且.env.example存在，则复制.env.example为.env
    EnvExamplePath := ExpandConstant('{app}\.env.example');
    EnvPath := ExpandConstant('{app}\.env');
    
    if FileExists(EnvExamplePath) and not FileExists(EnvPath) then
    begin
      if CopyFile(EnvExamplePath, EnvPath, False) then
        Log('Created .env file from .env.example')
      else
        Log('Failed to create .env file');
    end;
    
    // 创建运行时必要的目录
    CreateDir(ExpandConstant('{app}\logs'));
    CreateDir(ExpandConstant('{app}\Downloads'));
    
    Log('Post-install setup completed');
  end;
end;

// 卸载前的处理
function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Result := True;
  DeleteUserDataGlobal := False;
  
  // 检查程序是否正在运行
  if CheckForMutexes('{#MyAppName}') then
  begin
    MsgBox('检测到程序正在运行，请先关闭程序后再继续卸载。', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
  // 询问是否删除用户数据
  Response := MsgBox('是否同时删除程序设置和下载的数据？' + #13#10 + #13#10 + 
                     '• 选择"是"：删除所有设置、日志和已下载的壁纸' + #13#10 + 
                     '• 选择"否"：保留您的设置和已下载的壁纸' + #13#10 + #13#10 + 
                     '建议：如果您打算重新安装，请选择"否"。', 
                     mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
  
  DeleteUserDataGlobal := (Response = IDYES);
end;

// 卸载完成后的处理
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDir := ExpandConstant('{app}');
    
    // 如果用户选择不删除数据，显示数据保留位置
    if not DeleteUserDataGlobal then
    begin
      MsgBox('您的设置和下载的壁纸已保留在：' + #13#10 + AppDir + #13#10 + #13#10 + 
             '如需手动删除，请删除该文件夹。', mbInformation, MB_OK);
    end
    else
    begin
      // 如果用户选择删除数据，尝试删除整个应用目录
      if DirExists(AppDir) then
      begin
        Log('Attempting to delete application directory: ' + AppDir);
        if DelTree(AppDir, True, True, True) then
          Log('Application directory deleted successfully')
        else
          Log('Failed to delete application directory completely');
      end;
    end;
  end;
end;
