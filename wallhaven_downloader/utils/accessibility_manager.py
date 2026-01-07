"""
辅助功能管理器

提供 ARIA 标签、屏幕阅读器支持、键盘导航等辅助功能
"""

from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QLabel, QSlider, QComboBox
from typing import Optional, Dict, Any


class AccessibilityManager(QObject):
    """
    辅助功能管理器
    
    负责管理应用程序的辅助功能支持，包括：
    - ARIA 标签
    - 屏幕阅读器支持
    - 键盘导航
    - 焦点管理
    """
    
    # 信号
    accessibility_changed = pyqtSignal(bool)  # 辅助功能状态变化
    
    # 单例实例
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        super().__init__()
        self._initialized = True
        
        # 辅助功能状态
        self.enabled = True
        self.screen_reader_enabled = False
        
        # ARIA 角色映射
        self.aria_roles = {
            'button': 'button',
            'link': 'link',
            'textbox': 'textbox',
            'searchbox': 'searchbox',
            'slider': 'slider',
            'combobox': 'combobox',
            'checkbox': 'checkbox',
            'radio': 'radio',
            'tab': 'tab',
            'tabpanel': 'tabpanel',
            'navigation': 'navigation',
            'main': 'main',
            'complementary': 'complementary',
            'banner': 'banner',
            'contentinfo': 'contentinfo',
            'dialog': 'dialog',
            'alert': 'alert',
            'status': 'status',
            'progressbar': 'progressbar',
            'img': 'img',
            'list': 'list',
            'listitem': 'listitem',
            'menu': 'menu',
            'menuitem': 'menuitem',
            'tooltip': 'tooltip'
        }
    
    def set_aria_label(self, widget: QWidget, label: str):
        """
        为组件设置 ARIA 标签
        
        Args:
            widget: 目标组件
            label: ARIA 标签文本
        """
        if not self.enabled:
            return
        
        # 使用 Qt 的 accessible name 属性
        widget.setAccessibleName(label)
        
        # 如果是按钮，也设置 tooltip
        if isinstance(widget, QPushButton):
            if not widget.toolTip():
                widget.setToolTip(label)
    
    def set_aria_description(self, widget: QWidget, description: str):
        """
        为组件设置 ARIA 描述
        
        Args:
            widget: 目标组件
            description: ARIA 描述文本
        """
        if not self.enabled:
            return
        
        # 使用 Qt 的 accessible description 属性
        widget.setAccessibleDescription(description)
    
    def set_aria_role(self, widget: QWidget, role: str):
        """
        为组件设置 ARIA 角色
        
        Args:
            widget: 目标组件
            role: ARIA 角色（如 'button', 'navigation' 等）
        """
        if not self.enabled:
            return
        
        if role in self.aria_roles:
            # 通过 accessible name 的前缀来标识角色
            current_name = widget.accessibleName()
            if current_name:
                widget.setAccessibleName(f"[{role}] {current_name}")
            else:
                widget.setAccessibleName(f"[{role}]")
    
    def set_aria_live(self, widget: QWidget, live_type: str = "polite"):
        """
        为组件设置 ARIA live 区域
        
        Args:
            widget: 目标组件
            live_type: live 类型（'off', 'polite', 'assertive'）
        """
        if not self.enabled:
            return
        
        # 在描述中添加 live 标记
        current_desc = widget.accessibleDescription()
        live_marker = f"[aria-live:{live_type}]"
        
        if current_desc:
            if "[aria-live:" not in current_desc:
                widget.setAccessibleDescription(f"{live_marker} {current_desc}")
        else:
            widget.setAccessibleDescription(live_marker)
    
    def set_aria_expanded(self, widget: QWidget, expanded: bool):
        """
        设置组件的展开/折叠状态
        
        Args:
            widget: 目标组件
            expanded: 是否展开
        """
        if not self.enabled:
            return
        
        # 在描述中添加展开状态
        current_desc = widget.accessibleDescription()
        state = "expanded" if expanded else "collapsed"
        
        # 移除旧的状态标记
        if current_desc:
            current_desc = current_desc.replace("[expanded]", "").replace("[collapsed]", "").strip()
        
        new_desc = f"[{state}] {current_desc}" if current_desc else f"[{state}]"
        widget.setAccessibleDescription(new_desc)
    
    def set_aria_pressed(self, widget: QWidget, pressed: bool):
        """
        设置按钮的按下状态
        
        Args:
            widget: 目标组件
            pressed: 是否按下
        """
        if not self.enabled:
            return
        
        if isinstance(widget, QPushButton):
            # 使用 Qt 的 checkable 和 checked 属性
            widget.setCheckable(True)
            widget.setChecked(pressed)
    
    def set_aria_disabled(self, widget: QWidget, disabled: bool):
        """
        设置组件的禁用状态
        
        Args:
            widget: 目标组件
            disabled: 是否禁用
        """
        if not self.enabled:
            return
        
        widget.setEnabled(not disabled)
    
    def set_aria_hidden(self, widget: QWidget, hidden: bool):
        """
        设置组件的隐藏状态
        
        Args:
            widget: 目标组件
            hidden: 是否隐藏
        """
        if not self.enabled:
            return
        
        widget.setVisible(not hidden)
    
    def set_aria_value(self, widget: QWidget, value: Any, min_val: Any = None, max_val: Any = None):
        """
        设置组件的值（用于滑块、进度条等）
        
        Args:
            widget: 目标组件
            value: 当前值
            min_val: 最小值
            max_val: 最大值
        """
        if not self.enabled:
            return
        
        # 构建值描述
        value_desc = f"当前值: {value}"
        if min_val is not None and max_val is not None:
            value_desc += f" (范围: {min_val} - {max_val})"
        
        current_desc = widget.accessibleDescription()
        if current_desc and "当前值:" not in current_desc:
            widget.setAccessibleDescription(f"{current_desc} {value_desc}")
        else:
            widget.setAccessibleDescription(value_desc)
    
    def announce(self, widget: QWidget, message: str):
        """
        向屏幕阅读器宣布消息
        
        Args:
            widget: 相关组件
            message: 要宣布的消息
        """
        if not self.enabled or not self.screen_reader_enabled:
            return
        
        # 临时设置 accessible description 来触发屏幕阅读器
        original_desc = widget.accessibleDescription()
        widget.setAccessibleDescription(message)
        
        # 使用 QTimer 恢复原始描述
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: widget.setAccessibleDescription(original_desc))
    
    def setup_button_accessibility(self, button: QPushButton, label: str, 
                                   description: str = None, shortcut: str = None):
        """
        为按钮设置完整的辅助功能支持
        
        Args:
            button: 按钮组件
            label: 按钮标签
            description: 按钮描述
            shortcut: 快捷键
        """
        self.set_aria_label(button, label)
        self.set_aria_role(button, 'button')
        
        if description:
            self.set_aria_description(button, description)
        
        if shortcut:
            button.setShortcut(shortcut)
            tooltip = label
            if description:
                tooltip += f" - {description}"
            tooltip += f" ({shortcut})"
            button.setToolTip(tooltip)
    
    def setup_input_accessibility(self, input_widget: QLineEdit, label: str,
                                  placeholder: str = None, required: bool = False):
        """
        为输入框设置完整的辅助功能支持
        
        Args:
            input_widget: 输入框组件
            label: 输入框标签
            placeholder: 占位符文本
            required: 是否必填
        """
        self.set_aria_label(input_widget, label)
        self.set_aria_role(input_widget, 'textbox')
        
        if placeholder:
            input_widget.setPlaceholderText(placeholder)
        
        if required:
            desc = "必填项"
            if input_widget.accessibleDescription():
                desc = f"{input_widget.accessibleDescription()} {desc}"
            self.set_aria_description(input_widget, desc)
    
    def setup_navigation_accessibility(self, nav_widget: QWidget, label: str):
        """
        为导航组件设置辅助功能支持
        
        Args:
            nav_widget: 导航组件
            label: 导航标签
        """
        self.set_aria_label(nav_widget, label)
        self.set_aria_role(nav_widget, 'navigation')
    
    def setup_progress_accessibility(self, progress_widget: QWidget, label: str,
                                    value: int, min_val: int = 0, max_val: int = 100):
        """
        为进度条设置辅助功能支持
        
        Args:
            progress_widget: 进度条组件
            label: 进度条标签
            value: 当前值
            min_val: 最小值
            max_val: 最大值
        """
        self.set_aria_label(progress_widget, label)
        self.set_aria_role(progress_widget, 'progressbar')
        self.set_aria_value(progress_widget, value, min_val, max_val)
    
    def setup_alert_accessibility(self, alert_widget: QWidget, message: str, 
                                  alert_type: str = "info"):
        """
        为警告/提示组件设置辅助功能支持
        
        Args:
            alert_widget: 警告组件
            message: 警告消息
            alert_type: 警告类型（'info', 'warning', 'error', 'success'）
        """
        type_labels = {
            'info': '信息',
            'warning': '警告',
            'error': '错误',
            'success': '成功'
        }
        
        label = f"{type_labels.get(alert_type, '提示')}: {message}"
        self.set_aria_label(alert_widget, label)
        self.set_aria_role(alert_widget, 'alert')
        self.set_aria_live(alert_widget, 'assertive' if alert_type == 'error' else 'polite')
    
    def enable_accessibility(self):
        """启用辅助功能"""
        self.enabled = True
        self.accessibility_changed.emit(True)
    
    def disable_accessibility(self):
        """禁用辅助功能"""
        self.enabled = False
        self.accessibility_changed.emit(False)
    
    def enable_screen_reader(self):
        """启用屏幕阅读器支持"""
        self.screen_reader_enabled = True
    
    def disable_screen_reader(self):
        """禁用屏幕阅读器支持"""
        self.screen_reader_enabled = False


# 全局访问函数
_accessibility_manager = None

def get_accessibility_manager() -> AccessibilityManager:
    """获取辅助功能管理器单例"""
    global _accessibility_manager
    if _accessibility_manager is None:
        _accessibility_manager = AccessibilityManager()
    return _accessibility_manager
