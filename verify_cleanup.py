#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证组件清理结果
检查所有导入和功能是否正常
"""

import sys
import os

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("🔍 测试导入")
    print("=" * 60)
    
    tests = []
    
    # 测试1: 导入GlassSettingsPanel
    try:
        from wallhaven_downloader.ui.glass_settings_panel import GlassSettingsPanel
        print("✅ GlassSettingsPanel 导入成功")
        tests.append(("GlassSettingsPanel", True))
    except Exception as e:
        print(f"❌ GlassSettingsPanel 导入失败: {e}")
        tests.append(("GlassSettingsPanel", False))
    
    # 测试2: 导入ImagePreviewWidget
    try:
        from wallhaven_downloader.ui.image_preview import ImagePreviewWidget
        print("✅ ImagePreviewWidget 导入成功")
        tests.append(("ImagePreviewWidget", True))
    except Exception as e:
        print(f"❌ ImagePreviewWidget 导入失败: {e}")
        tests.append(("ImagePreviewWidget", False))
    
    # 测试3: 导入GlassToggleSwitch
    try:
        from wallhaven_downloader.ui.glass_settings_panel import GlassToggleSwitch
        print("✅ GlassToggleSwitch 导入成功")
        tests.append(("GlassToggleSwitch", True))
    except Exception as e:
        print(f"❌ GlassToggleSwitch 导入失败: {e}")
        tests.append(("GlassToggleSwitch", False))
    
    # 测试4: 确认ModernSettingsPanel已删除
    try:
        from wallhaven_downloader.ui.modern_settings_panel import ModernSettingsPanel
        print("⚠️  ModernSettingsPanel 仍然存在（应该已删除）")
        tests.append(("ModernSettingsPanel删除", False))
    except ImportError:
        print("✅ ModernSettingsPanel 已成功删除")
        tests.append(("ModernSettingsPanel删除", True))
    except Exception as e:
        print(f"⚠️  检查ModernSettingsPanel时出错: {e}")
        tests.append(("ModernSettingsPanel删除", False))
    
    return tests

def check_files():
    """检查文件状态"""
    print("\n" + "=" * 60)
    print("📁 检查文件状态")
    print("=" * 60)
    
    checks = []
    
    # 检查新组件文件存在
    files_should_exist = [
        "wallhaven_downloader/ui/glass_settings_panel.py",
        "wallhaven_downloader/ui/image_preview.py",
    ]
    
    for file_path in files_should_exist:
        if os.path.exists(file_path):
            print(f"✅ {file_path} 存在")
            checks.append((file_path, True))
        else:
            print(f"❌ {file_path} 不存在")
            checks.append((file_path, False))
    
    # 检查旧文件已删除
    files_should_not_exist = [
        "wallhaven_downloader/ui/modern_settings_panel.py",
    ]
    
    for file_path in files_should_not_exist:
        if not os.path.exists(file_path):
            print(f"✅ {file_path} 已删除")
            checks.append((file_path + " (删除)", True))
        else:
            print(f"⚠️  {file_path} 仍然存在（应该已删除）")
            checks.append((file_path + " (删除)", False))
    
    # 检查备份文件
    backup_file = "wallhaven_downloader/main_window.py.backup"
    if os.path.exists(backup_file):
        print(f"✅ 备份文件存在: {backup_file}")
        checks.append(("备份文件", True))
    else:
        print(f"⚠️  备份文件不存在: {backup_file}")
        checks.append(("备份文件", False))
    
    return checks

def check_main_window():
    """检查main_window.py的导入"""
    print("\n" + "=" * 60)
    print("🔍 检查 main_window.py")
    print("=" * 60)
    
    checks = []
    
    file_path = "wallhaven_downloader/main_window.py"
    
    if not os.path.exists(file_path):
        print(f"❌ {file_path} 不存在")
        return [("main_window.py存在", False)]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否导入了GlassSettingsPanel
    if "from ui.glass_settings_panel import GlassSettingsPanel" in content or \
       "from wallhaven_downloader.ui.glass_settings_panel import GlassSettingsPanel" in content:
        print("✅ 导入了 GlassSettingsPanel")
        checks.append(("导入GlassSettingsPanel", True))
    else:
        print("❌ 未导入 GlassSettingsPanel")
        checks.append(("导入GlassSettingsPanel", False))
    
    # 检查是否还有ModernSettingsPanel的引用
    if "ModernSettingsPanel" in content:
        print("⚠️  仍然引用 ModernSettingsPanel")
        checks.append(("移除ModernSettingsPanel引用", False))
    else:
        print("✅ 已移除 ModernSettingsPanel 引用")
        checks.append(("移除ModernSettingsPanel引用", True))
    
    # 检查是否还有旧的ImagePreviewWidget类定义
    if "class ImagePreviewWidget(QWidget):" in content:
        # 检查是否是注释
        lines = content.split('\n')
        has_old_class = False
        for line in lines:
            if "class ImagePreviewWidget(QWidget):" in line and not line.strip().startswith('#'):
                has_old_class = True
                break
        
        if has_old_class:
            print("⚠️  仍然存在旧的 ImagePreviewWidget 类定义")
            checks.append(("移除旧ImagePreviewWidget", False))
        else:
            print("✅ 旧的 ImagePreviewWidget 类定义已移除")
            checks.append(("移除旧ImagePreviewWidget", True))
    else:
        print("✅ 旧的 ImagePreviewWidget 类定义已移除")
        checks.append(("移除旧ImagePreviewWidget", True))
    
    # 检查是否还有旧的SettingsDialog类定义
    if "class SettingsDialog(QDialog):" in content:
        lines = content.split('\n')
        has_old_class = False
        for line in lines:
            if "class SettingsDialog(QDialog):" in line and not line.strip().startswith('#'):
                has_old_class = True
                break
        
        if has_old_class:
            print("⚠️  仍然存在旧的 SettingsDialog 类定义")
            checks.append(("移除旧SettingsDialog", False))
        else:
            print("✅ 旧的 SettingsDialog 类定义已移除")
            checks.append(("移除旧SettingsDialog", True))
    else:
        print("✅ 旧的 SettingsDialog 类定义已移除")
        checks.append(("移除旧SettingsDialog", True))
    
    return checks

def print_summary(import_tests, file_checks, main_window_checks):
    """打印总结"""
    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)
    
    all_tests = import_tests + file_checks + main_window_checks
    passed = sum(1 for _, result in all_tests if result)
    total = len(all_tests)
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n" + "=" * 60)
        print("✅ 所有验证通过！")
        print("=" * 60)
        print("\n🎉 组件清理成功完成！")
        print("\n📋 后续步骤:")
        print("1. 运行 python main.py 测试程序")
        print("2. 打开设置面板，验证所有功能")
        print("3. 下载图片，验证预览功能")
        print("4. 如果一切正常，可以删除备份文件")
        return True
    else:
        print("\n" + "=" * 60)
        print("⚠️  部分验证失败")
        print("=" * 60)
        print("\n失败的测试:")
        for name, result in all_tests:
            if not result:
                print(f"  ❌ {name}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 验证组件清理结果")
    print("=" * 60)
    print()
    
    # 运行测试
    import_tests = test_imports()
    file_checks = check_files()
    main_window_checks = check_main_window()
    
    # 打印总结
    success = print_summary(import_tests, file_checks, main_window_checks)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
