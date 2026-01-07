# -*- coding: utf-8 -*-
"""
玻璃设置面板组件

使用液态玻璃效果重设计的设置面板，包括：
- 玻璃分组容器
- 现代化设置控件
- 实时预览效果
- 平滑动画过渡

需求：9.1-9.8
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QSlider, QWidget, QScrollArea, QFrame, QLineEdit,
    QComboBox, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer, pyqtProperty, QSize
from PyQt5.QtGui import QFont, QColor

try:
    from ui.liquid_glass.glass_panel_factory import GlassPanelFactory
    from ui.liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from ui.icon_manager import IconManager
    from ui.animation.enhanced_animation_manager import EnhancedAnimationManager
    from ui.toast_notification import ToastManager
    from core.i18n_manager import get_i18n_manager
    from core.apple_color_palette import AppleColorPalette
    from core.enhanced_theme_manager import EnhancedThemeManager, get_enhanced_theme_manager
    from core.theme_manager import get_theme_manager
    from utils.logger import get_logger
except ImportError:
    from .liquid_glass.glass_panel_factory import GlassPanelFactory
    from .liquid_glass.enhanced_glass_panel import EnhancedGlassPanel
    from .icon_manager import IconManager
    from .animation.enhanced_animation_manager import EnhancedAnimationManager
    from .toast_notification import ToastManager
    from ..core.i18n_manager import get_i18n_manager
    from ..core.apple_color_palette import AppleColorPalette
    from ..core.enhanced_theme_manager import EnhancedThemeManager, get_enhanced_theme_manager
    from ..core.theme_manager import get_theme_manager
    from ..utils.logger import get_logger

logger = get_logger(__name__)


class GlassToggleSwitch(QWidget):
    """玻璃风格开关组件 - 增强版"""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checked = False
        self.setFixedSize(50, 24)
        self.setCursor(Qt.PointingHandCursor)
        
        # 动画相关
        self._slider_pos = 2  # 滑块位置
        self._animation = QPropertyAnimation(self, b"slider_pos")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)
        
    def get_slider_pos(self):
        return self._slider_pos
    
    def set_slider_pos(self, pos):
        self._slider_pos = pos
        self.update()
    
    slider_pos = pyqtProperty(int, get_slider_pos, set_slider_pos)
        
    def paintEvent(self, event):
        """绘制玻璃风格开关 - 带动画和阴影"""
        from PyQt5.QtGui import QPainter, QPen, QBrush, QLinearGradient
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 背景轨道 - 渐变效果
        if self.checked:
            gradient = QLinearGradient(0, 0, 50, 0)
            gradient.setColorAt(0, QColor(59, 130, 246))
            gradient.setColorAt(1, QColor(37, 99, 235))
            bg_brush = QBrush(gradient)
        else:
            bg_brush = QBrush(QColor(209, 213, 219))
            
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_brush)
        painter.drawRoundedRect(0, 0, 50, 24, 12, 12)
        
        # 滑块阴影
        shadow_color = QColor(0, 0, 0, 60)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(self._slider_pos + 1, 3, 20, 20)
        
        # 滑块 - 白色带高光
        slider_gradient = QLinearGradient(self._slider_pos, 2, self._slider_pos, 22)
        slider_gradient.setColorAt(0, QColor(255, 255, 255))
        slider_gradient.setColorAt(1, QColor(245, 245, 245))
        painter.setBrush(QBrush(slider_gradient))
        painter.drawEllipse(self._slider_pos, 2, 20, 20)
        
    def mousePressEvent(self, event):
        """鼠标点击事件 - 带动画"""
        self.checked = not self.checked
        
        # 启动滑块动画
        start_pos = 2 if not self.checked else 26
        end_pos = 26 if self.checked else 2
        self._animation.setStartValue(start_pos)
        self._animation.setEndValue(end_pos)
        self._animation.start()
        
        self.toggled.emit(self.checked)
        
    def setChecked(self, checked: bool):
        """设置开关状态"""
        if self.checked != checked:
            self.checked = checked
            self._slider_pos = 26 if checked else 2
            self.update()
            
    def isChecked(self) -> bool:
        """获取开关状态"""
        return self.checked



class GlassCollapsibleGroup(QWidget):
    """可折叠的玻璃分组框"""
    
    def __init__(self, title: str, icon_name: str = None, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon_name = icon_name
        self.is_collapsed = False
        
        # 管理器
        self.icon_manager = IconManager()
        self.animation_manager = EnhancedAnimationManager()
        self.glass_factory = GlassPanelFactory()
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(8)
        
        # 使用玻璃面板作为容器
        self.glass_panel = self.glass_factory.create_panel(
            self,
            panel_type="normal"
        )
        
        panel_layout = QVBoxLayout(self.glass_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        
        # 标题栏
        self.header = QWidget()
        self.header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        # 图标
        if self.icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(
                self.icon_manager.get_icon(self.icon_name, size=20)
                .pixmap(20, 20)
            )
            header_layout.addWidget(icon_label)
        
        # 标题
        self.title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # 展开/折叠图标
        self.arrow_label = QLabel("▼")
        self.arrow_label.setFont(QFont("", 10))
        header_layout.addWidget(self.arrow_label)
        
        # 点击事件
        self.header.mousePressEvent = lambda e: self.toggle()
        
        panel_layout.addWidget(self.header)
        
        # 分隔线
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFixedHeight(1)
        self.separator.setStyleSheet("background-color: rgb(229, 231, 235);")
        panel_layout.addWidget(self.separator)
        
        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 12, 20, 12)
        self.content_layout.setSpacing(16)
        
        panel_layout.addWidget(self.content_widget)
        
        layout.addWidget(self.glass_panel)
        
        # 应用固定样式
        self._apply_fixed_colors()
        
    def toggle(self):
        """切换展开/折叠状态 - 带动画"""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.arrow_label.setText("▶")
            # 折叠动画
            self.animation_manager.create_fade_animation(
                self.content_widget,
                start_opacity=1.0,
                end_opacity=0.0,
                duration=200
            ).start()
            QTimer.singleShot(200, lambda: self.content_widget.hide())
        else:
            self.arrow_label.setText("▼")
            self.content_widget.show()
            # 展开动画
            self.animation_manager.create_fade_animation(
                self.content_widget,
                start_opacity=0.0,
                end_opacity=1.0,
                duration=200
            ).start()
            
    def add_setting_item(self, widget: QWidget):
        """添加设置项"""
        self.content_layout.addWidget(widget)
    
    def _apply_fixed_colors(self):
        """应用固定的浅色主题颜色"""
        text_color = QColor(60, 60, 60)  # 深灰色文本
        separator_color = QColor(229, 231, 235)  # 浅灰色分隔线
        
        self.title_label.setStyleSheet(f"color: {text_color.name()};")
        self.arrow_label.setStyleSheet(f"color: {text_color.name()};")
        self.separator.setStyleSheet(f"background-color: {separator_color.name()};")



class GlassSettingItem(QWidget):
    """玻璃风格设置项组件"""
    
    def __init__(self, label: str, description: str = "", icon_name: str = None, parent=None):
        super().__init__(parent)
        self.label = label
        self.description = description
        self.icon_name = icon_name
        
        # 管理器
        self.icon_manager = IconManager()
        self.palette = AppleColorPalette()
        self.is_dark_mode = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        
        # 左侧：图标和文字
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        
        # 标签行（图标 + 标签）
        label_layout = QHBoxLayout()
        label_layout.setSpacing(10)
        
        if self.icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(
                self.icon_manager.get_icon(self.icon_name, size=18)
                .pixmap(18, 18)
            )
            label_layout.addWidget(icon_label)
        
        self.label_widget = QLabel(self.label)
        label_font = QFont()
        label_font.setPointSize(12)  # 从 10 增大到 12
        label_font.setBold(False)
        self.label_widget.setFont(label_font)
        label_layout.addWidget(self.label_widget)
        label_layout.addStretch()
        
        left_layout.addLayout(label_layout)
        
        # 描述
        if self.description:
            self.desc_label = QLabel(self.description)
            self.desc_label.setWordWrap(True)
            desc_font = QFont()
            desc_font.setPointSize(10)  # 从 9 增大到 10
            self.desc_label.setFont(desc_font)
            left_layout.addWidget(self.desc_label)
        
        layout.addLayout(left_layout, stretch=1)
        
        # 右侧：控件容器
        self.control_layout = QHBoxLayout()
        self.control_layout.setSpacing(8)
        layout.addLayout(self.control_layout)
        
        # 应用初始主题
        self._apply_theme_colors()
        
    def add_control(self, widget: QWidget):
        """添加控件"""
        self.control_layout.addWidget(widget)
    
    def update_theme(self, is_dark_mode: bool):
        """更新主题"""
        self.is_dark_mode = is_dark_mode
        self._apply_theme_colors()
    
    def _apply_theme_colors(self):
        """应用主题颜色"""
        text_primary = self.palette.get_color("text_primary", self.is_dark_mode)
        text_secondary = self.palette.get_color("text_secondary", self.is_dark_mode)
        
        self.label_widget.setStyleSheet(f"color: {text_primary.name()};")
        if self.description:
            self.desc_label.setStyleSheet(f"color: {text_secondary.name()};")



class GlassSettingsPanel(QDialog):
    """玻璃风格设置面板
    
    使用液态玻璃效果重设计的设置面板
    需求：9.1-9.8
    """
    
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self.original_settings = settings.copy()
        
        # 管理器
        self.i18n = get_i18n_manager()
        self.icon_manager = IconManager()
        self.animation_manager = EnhancedAnimationManager()
        
        # 使用主窗口的 toast_manager，如果没有则创建一个使用主窗口作为父组件的
        if hasattr(parent, 'modern_ui_manager') and parent.modern_ui_manager and hasattr(parent.modern_ui_manager, 'get_toast_manager'):
            self.toast_manager = parent.modern_ui_manager.get_toast_manager()
        else:
            # 回退方案：使用主窗口作为父组件创建 toast_manager
            main_window = parent
            # 如果 parent 不是主窗口，尝试找到主窗口
            while main_window and not hasattr(main_window, 'setMenuBar'):  # 主窗口特征
                main_window = main_window.parent() if hasattr(main_window, 'parent') else None
            
            if main_window:
                self.toast_manager = ToastManager(main_window)
            else:
                # 最后的回退方案：使用当前对话框
                self.toast_manager = ToastManager(self)
        
        self.glass_factory = GlassPanelFactory()
        self.palette = AppleColorPalette()
        
        # 主题管理器
        try:
            self.theme_manager = get_enhanced_theme_manager()
        except Exception:
            self.theme_manager = get_theme_manager()
        
        # 检测当前主题
        self.is_dark_mode = False
        
        # 设置窗口 - 增大窗口尺寸以容纳更多内容
        self.setWindowTitle(self.i18n.t("settings_dialog.title"))
        self.setMinimumSize(1100, 850)
        self.resize(1100, 850)
        
        # 不使用透明背景，避免重影问题
        # self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._setup_ui()
        self._load_settings()
        self._apply_dialog_theme()
        
    def _detect_dark_mode(self) -> bool:
        """检测当前是否为深色模式"""
        try:
            if hasattr(self.theme_manager, 'is_dark_mode'):
                return self.theme_manager.is_dark_mode()
            elif hasattr(self.theme_manager, 'current_theme'):
                return self.theme_manager.current_theme == "深色"
            else:
                return False
        except:
            return False
        
    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # 标题
        self.title_label = QLabel(self.i18n.t("settings_dialog.title"))
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        main_layout.addWidget(self.title_label)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        # 隐藏垂直滚动条
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("QWidget { background: transparent; }")
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(16)
        
        # 外观设置分组
        self._create_appearance_settings(self.scroll_layout)
        
        # 下载设置分组
        self._create_download_settings(self.scroll_layout)
        
        # 性能设置分组
        self._create_performance_settings(self.scroll_layout)
        
        # 高级设置分组
        self._create_advanced_settings(self.scroll_layout)
        
        # 删除关于分组，与关于界面重合
        # self._create_about_section(self.scroll_layout)
        
        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # 底部按钮
        self._create_buttons(main_layout)
        
    def _create_appearance_settings(self, parent_layout: QVBoxLayout):
        """创建外观设置分组 - 需求：9.1-9.2"""
        group = GlassCollapsibleGroup(
            self.i18n.t("settings_dialog.ui_group"),
            "settings"
        )
        
        # 主题设置
        theme_item = GlassSettingItem(
            self.i18n.t("settings_dialog.theme"),
            self.i18n.t("settings_dialog.theme_desc"),
            "sun"
        )
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            self.i18n.t("theme.light")
        ])
        self.theme_combo.setMinimumWidth(200)
        self._apply_enhanced_combobox_style(self.theme_combo)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_item.add_control(self.theme_combo)
        group.add_setting_item(theme_item)
        
        # 玻璃透明度 - 需求：9.4, 9.5
        transparency_item = GlassSettingItem(
            self.i18n.t("settings_dialog.transparency"),
            self.i18n.t("settings_dialog.transparency_desc"),
            "droplet"
        )
        
        transparency_widget = QWidget()
        transparency_layout = QHBoxLayout(transparency_widget)
        transparency_layout.setContentsMargins(0, 0, 0, 0)
        
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(100, 255)
        self.transparency_slider.setValue(200)
        self.transparency_slider.setMinimumWidth(200)
        
        self.transparency_label = QLabel("200")
        self.transparency_label.setMinimumWidth(40)
        self.transparency_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 预览框
        self.transparency_preview = QWidget()
        self.transparency_preview.setFixedSize(30, 30)
        
        self.transparency_slider.valueChanged.connect(self._on_transparency_changed)
        
        transparency_layout.addWidget(self.transparency_slider)
        transparency_layout.addWidget(self.transparency_label)
        transparency_layout.addWidget(self.transparency_preview)
        
        transparency_item.add_control(transparency_widget)
        group.add_setting_item(transparency_item)
        
        # 语言设置
        language_item = GlassSettingItem(
            self.i18n.t("settings_dialog.language"),
            self.i18n.t("settings_dialog.language_desc"),
            "globe"
        )
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        self.language_combo.setMinimumWidth(200)
        self._apply_enhanced_combobox_style(self.language_combo)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        language_item.add_control(self.language_combo)
        group.add_setting_item(language_item)
        
        # 预览图片大小
        preview_item = GlassSettingItem(
            self.i18n.t("settings_dialog.preview_size"),
            self.i18n.t("settings_dialog.preview_size_desc"),
            "image"
        )
        self.preview_size_combo = QComboBox()
        self.preview_size_combo.addItems([
            self.i18n.t("preview_size.small"),
            self.i18n.t("preview_size.medium"),
            self.i18n.t("preview_size.large")
        ])
        self.preview_size_combo.setMinimumWidth(200)
        self._apply_enhanced_combobox_style(self.preview_size_combo)
        self.preview_size_combo.currentIndexChanged.connect(self._on_preview_size_changed)
        preview_item.add_control(self.preview_size_combo)
        group.add_setting_item(preview_item)
        
        parent_layout.addWidget(group)
        self.appearance_group = group
        
    def _create_download_settings(self, parent_layout: QVBoxLayout):
        """创建下载设置分组 - 需求：9.1-9.2"""
        group = GlassCollapsibleGroup(
            self.i18n.t("settings_dialog.download_group"),
            "download"
        )
        
        # API密钥
        api_item = GlassSettingItem(
            self.i18n.t("settings_dialog.api_key"),
            self.i18n.t("settings_dialog.api_key_desc"),
            "key"
        )
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText(self.i18n.t("settings_dialog.api_key_placeholder"))
        self.api_key_edit.setMinimumWidth(300)
        self._apply_enhanced_input_style(self.api_key_edit)
        # API密钥实时保存
        self.api_key_edit.textChanged.connect(
            lambda text: self.settings.update({"api_key": text})
        )
        api_item.add_control(self.api_key_edit)
        group.add_setting_item(api_item)
        
        # 每页图片数
        images_item = GlassSettingItem(
            self.i18n.t("settings_dialog.images_per_page"),
            self.i18n.t("settings_dialog.images_per_page_desc"),
            "image"
        )
        self.images_per_page_spin = QSpinBox()
        self.images_per_page_spin.setRange(1, 100)
        self.images_per_page_spin.setValue(24)
        self._apply_enhanced_spinbox_style(self.images_per_page_spin)
        # 实时保存
        self.images_per_page_spin.valueChanged.connect(
            lambda value: self.settings.update({"images_per_page": value})
        )
        images_item.add_control(self.images_per_page_spin)
        group.add_setting_item(images_item)
        
        # 下载超时
        timeout_item = GlassSettingItem(
            self.i18n.t("settings_dialog.timeout"),
            self.i18n.t("settings_dialog.timeout_desc"),
            "clock"
        )
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" " + self.i18n.t("settings_dialog.seconds"))
        self._apply_enhanced_spinbox_style(self.timeout_spin)
        # 实时保存
        self.timeout_spin.valueChanged.connect(
            lambda value: self.settings.update({"download_timeout": value})
        )
        timeout_item.add_control(self.timeout_spin)
        group.add_setting_item(timeout_item)
        
        # 并发下载数
        concurrent_item = GlassSettingItem(
            self.i18n.t("download.concurrent"),
            self.i18n.t("settings_dialog.concurrent_desc"),
            "layers"
        )
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        self._apply_enhanced_spinbox_style(self.concurrent_spin)
        # 实时保存
        self.concurrent_spin.valueChanged.connect(
            lambda value: self.settings.update({"concurrent_downloads": value})
        )
        concurrent_item.add_control(self.concurrent_spin)
        group.add_setting_item(concurrent_item)
        
        # 自动跳过重复
        skip_item = GlassSettingItem(
            self.i18n.t("main_window.skip_duplicates"),
            self.i18n.t("main_window.skip_duplicates_desc"),
            "check-circle"
        )
        self.skip_duplicates_toggle = GlassToggleSwitch()
        # 实时保存
        self.skip_duplicates_toggle.toggled.connect(
            lambda checked: self.settings.update({"auto_skip_duplicates": checked})
        )
        skip_item.add_control(self.skip_duplicates_toggle)
        group.add_setting_item(skip_item)
        
        parent_layout.addWidget(group)
        self.download_group = group
        
    def _create_performance_settings(self, parent_layout: QVBoxLayout):
        """创建性能设置分组 - 需求：9.1-9.2"""
        group = GlassCollapsibleGroup(
            self.i18n.t("main_window.performance_settings"),
            "cpu"
        )
        
        # 启用动画
        animation_item = GlassSettingItem(
            self.i18n.t("main_window.enable_animations"),
            self.i18n.t("main_window.enable_animations_desc"),
            "zap"
        )
        self.animation_toggle = GlassToggleSwitch()
        self.animation_toggle.setChecked(True)
        self.animation_toggle.toggled.connect(self._on_animation_toggled)
        animation_item.add_control(self.animation_toggle)
        group.add_setting_item(animation_item)
        
        # 性能模式
        performance_item = GlassSettingItem(
            self.i18n.t("main_window.performance_mode"),
            self.i18n.t("main_window.performance_mode_desc"),
            "sliders"
        )
        self.performance_toggle = GlassToggleSwitch()
        self.performance_toggle.toggled.connect(self._on_performance_toggled)
        performance_item.add_control(self.performance_toggle)
        group.add_setting_item(performance_item)
        
        # GPU加速
        gpu_item = GlassSettingItem(
            self.i18n.t("main_window.gpu_acceleration"),
            self.i18n.t("main_window.gpu_acceleration_desc"),
            "cpu"
        )
        self.gpu_toggle = GlassToggleSwitch()
        self.gpu_toggle.setChecked(True)
        # GPU加速只保存设置，不实时应用（需要重启）
        self.gpu_toggle.toggled.connect(
            lambda checked: self._on_gpu_toggled(checked)
        )
        gpu_item.add_control(self.gpu_toggle)
        group.add_setting_item(gpu_item)
        
        parent_layout.addWidget(group)
        self.performance_group = group
        
    def _create_advanced_settings(self, parent_layout: QVBoxLayout):
        """创建高级设置分组 - 需求：9.1-9.2"""
        group = GlassCollapsibleGroup(
            self.i18n.t("main_window.advanced_settings"),
            "sliders"
        )
        
        # 调试模式
        debug_item = GlassSettingItem(
            self.i18n.t("main_window.debug_mode"),
            self.i18n.t("main_window.debug_mode_desc"),
            "bug"
        )
        self.debug_toggle = GlassToggleSwitch()
        # 实时保存
        self.debug_toggle.toggled.connect(
            lambda checked: self.settings.update({"debug_mode": checked})
        )
        debug_item.add_control(self.debug_toggle)
        group.add_setting_item(debug_item)
        
        # 自动更新
        update_item = GlassSettingItem(
            self.i18n.t("main_window.auto_update"),
            self.i18n.t("main_window.auto_update_desc"),
            "refresh-cw"
        )
        self.update_toggle = GlassToggleSwitch()
        self.update_toggle.setChecked(True)
        # 实时保存
        self.update_toggle.toggled.connect(
            lambda checked: self.settings.update({"auto_update": checked})
        )
        update_item.add_control(self.update_toggle)
        group.add_setting_item(update_item)
        
        parent_layout.addWidget(group)
        self.advanced_group = group
        
    def _create_about_section(self, parent_layout: QVBoxLayout):
        """创建关于分组 - 需求：9.1-9.2"""
        group = GlassCollapsibleGroup(
            "关于",
            "info"
        )
        
        # 版本信息
        version_item = GlassSettingItem(
            "版本",
            "Wallhaven Downloader v2.0.0",
            "package"
        )
        group.add_setting_item(version_item)
        
        # 作者信息
        author_item = GlassSettingItem(
            "作者",
            "开源项目 - GitHub",
            "user"
        )
        group.add_setting_item(author_item)
        
        parent_layout.addWidget(group)
        self.about_group = group
        
    def _create_buttons(self, parent_layout: QVBoxLayout):
        """创建底部按钮 - 需求：9.8"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 重置按钮 - 使用液态玻璃效果
        reset_btn = self._create_glass_button("重置为默认")
        reset_btn.setMinimumSize(120, 40)
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        # 取消按钮 - 使用液态玻璃效果
        cancel_btn = self._create_glass_button(self.i18n.t("settings_dialog.cancel"))
        cancel_btn.setMinimumSize(100, 40)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 保存按钮 - 使用液态玻璃效果
        self.save_btn = self._create_glass_button(self.i18n.t("settings_dialog.ok"))
        self.save_btn.setMinimumSize(100, 40)
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)
        
        parent_layout.addLayout(button_layout)
        
        # 保存按钮引用
        self.reset_btn = reset_btn
        self.cancel_btn = cancel_btn
    
    def _create_glass_button(self, text: str) -> QPushButton:
        """创建液态玻璃效果按钮"""
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        
        # 从设置中获取透明度，默认为 180
        transparency = self.settings.get("glass_transparency", 180)
        
        # 应用液态玻璃样式
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, {transparency});
                color: rgb(50, 50, 50);
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, {min(transparency + 40, 255)});
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, {max(transparency - 30, 100)});
            }}
        """)
        
        return button
        
    def _on_transparency_changed(self, value: int):
        """透明度变化时实时生效"""
        self.transparency_label.setText(str(value))
        
        # 更新设置
        self.settings["glass_transparency"] = value
        
        # 实时预览：更新预览框的透明度
        accent_color = self.palette.get_color("accent", self.is_dark_mode)
        self.transparency_preview.setStyleSheet(f"""
            QWidget {{
                background-color: rgba({accent_color.red()}, {accent_color.green()}, {accent_color.blue()}, {value});
                border-radius: 6px;
                border: 1px solid {self.palette.get_color("border", self.is_dark_mode).name()};
            }}
        """)
        
        # 实时更新所有按钮的透明度
        self._update_button_transparency(value)
        
        # 通知主窗口更新透明度
        if self.parent():
            self._apply_transparency_to_parent(value)
    
    def _on_theme_changed(self, index: int):
        """主题变化时实时生效"""
        theme_name = "浅色"
        self.is_dark_mode = False
        
        # 更新设置
        self.settings["theme"] = theme_name
        
        try:
            if hasattr(self.theme_manager, 'set_theme'):
                self.theme_manager.set_theme(theme_name)
        except:
            pass
        
        self._apply_dialog_theme()
        self._update_all_groups_theme()
        
        # 通知主窗口更新主题
        if self.parent():
            self._apply_theme_to_parent()
    
    def _on_language_changed(self, index: int):
        """语言变化时实时生效"""
        language = "zh_CN" if index == 0 else "en_US"
        
        # 更新设置
        self.settings["language"] = language
        
        # 应用语言
        self.i18n.set_language(language)
        
        # 刷新当前对话框的文本
        self._refresh_dialog_texts()
        
        # 通知主窗口更新语言
        if self.parent():
            self._apply_language_to_parent(language)
    
    def _on_preview_size_changed(self, index: int):
        """预览大小变化时实时生效"""
        size_list = ["小 (150x150)", "中 (200x200)", "大 (300x300)"]
        preview_size = size_list[index]
        
        # 更新设置
        self.settings["preview_size"] = preview_size
        
        # 通知主窗口更新预览大小
        if self.parent():
            self._apply_preview_size_to_parent(preview_size)
    
    def _on_animation_toggled(self, checked: bool):
        """动画开关切换时实时生效"""
        # 更新设置
        self.settings["enable_animations"] = checked
        
        # 通知主窗口更新动画设置
        if self.parent():
            self._apply_animation_to_parent(checked)
    
    def _on_performance_toggled(self, checked: bool):
        """性能模式切换时实时生效"""
        # 更新设置
        self.settings["performance_mode"] = checked
        
        # 通知主窗口更新性能模式
        if self.parent():
            self._apply_performance_to_parent(checked)
    
    def _on_gpu_toggled(self, checked: bool):
        """GPU加速切换时保存设置（需要重启生效）"""
        # 更新设置
        self.settings["gpu_acceleration"] = checked
        
        # 显示提示信息
        if hasattr(self, 'toast_manager'):
            self.toast_manager.show("GPU加速设置将在重启后生效", "info")
    
    def _detect_system_dark_mode(self) -> bool:
        """检测系统是否为深色模式"""
        return False
        
    def _update_all_groups_theme(self):
        """更新所有分组的主题"""
        groups = [
            self.appearance_group,
            self.download_group,
            self.performance_group,
            self.advanced_group,
            self.about_group
        ]
        
        for group in groups:
            # 更新分组内的设置项
            for i in range(group.content_layout.count()):
                item = group.content_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, GlassSettingItem):
                        widget.update_theme(self.is_dark_mode)
    
    def _apply_dialog_theme(self):
        """应用对话框主题 - 强制使用浅色主题"""
        # 强制使用浅色主题
        is_light_mode = False  # 使用浅色配色
        
        bg_color = self.palette.get_color("background", is_light_mode)
        text_primary = self.palette.get_color("text_primary", is_light_mode)
        surface = self.palette.get_color("surface", is_light_mode)
        border = self.palette.get_color("border", is_light_mode)
        accent = self.palette.get_color("accent", is_light_mode)
        accent_hover = self.palette.get_color("accent_hover", is_light_mode)
        
        # 对话框背景（不包含按钮样式，按钮使用独立的液态玻璃效果）
        # 移除透明背景属性，使用实心浅色背景
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color.name()};
            }}
            QLabel {{
                color: {text_primary.name()};
                background: transparent;
            }}
            QSpinBox, QLineEdit, QComboBox {{
                background-color: rgba({surface.red()}, {surface.green()}, {surface.blue()}, 200);
                border: 1px solid {border.name()};
                border-radius: 6px;
                padding: 6px 10px;
                color: {text_primary.name()};
                min-height: 24px;
            }}
            QSpinBox:hover, QLineEdit:hover, QComboBox:hover {{
                border-color: {accent.name()};
            }}
            QSpinBox:focus, QLineEdit:focus, QComboBox:focus {{
                border: 2px solid {accent.name()};
            }}
            QSlider::groove:horizontal {{
                background: {border.name()};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {accent.name()};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {accent_hover.name()};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
        """)
        
        # 更新标题颜色
        self.title_label.setStyleSheet(f"color: {text_primary.name()}; background: transparent;")
    
    def _update_button_transparency(self, transparency: int):
        """更新所有按钮的透明度"""
        buttons = [self.reset_btn, self.cancel_btn, self.save_btn]
        
        for button in buttons:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, {transparency});
                    color: rgb(50, 50, 50);
                    border: none;
                    border-radius: 15px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, {min(transparency + 40, 255)});
                }}
                QPushButton:pressed {{
                    background-color: rgba(255, 255, 255, {max(transparency - 30, 100)});
                }}
            """)
        
    def _load_settings(self):
        """加载设置"""
        # API密钥
        self.api_key_edit.setText(
            self.settings.get("api_key", "dws2O4u6Agr4v1CC92mH90H1T49QSuTM")
        )
        
        # 语言
        language = self.settings.get("language", "zh_CN")
        lang_index = 0 if language == "zh_CN" else 1
        self.language_combo.setCurrentIndex(lang_index)
        
        # 主题
        theme = self.settings.get("theme", "浅色")
        theme_map = {"浅色": 0}
        self.theme_combo.setCurrentIndex(theme_map.get(theme, 0))
        
        # 透明度
        self.transparency_slider.setValue(
            self.settings.get("glass_transparency", 200)
        )
        
        # 每页图片数
        self.images_per_page_spin.setValue(
            self.settings.get("images_per_page", 24)
        )
        
        # 超时
        self.timeout_spin.setValue(
            self.settings.get("download_timeout", 30)
        )
        
        # 并发数
        self.concurrent_spin.setValue(
            self.settings.get("concurrent_downloads", 3)
        )
        
        # 预览大小
        preview_size = self.settings.get("preview_size", "中 (200x200)")
        size_map = {"小 (150x150)": 0, "中 (200x200)": 1, "大 (300x300)": 2}
        self.preview_size_combo.setCurrentIndex(size_map.get(preview_size, 1))
        
        # 自动跳过重复
        self.skip_duplicates_toggle.setChecked(
            self.settings.get("auto_skip_duplicates", True)
        )
        
        # 动画
        self.animation_toggle.setChecked(
            self.settings.get("enable_animations", True)
        )
        
        # 性能模式
        self.performance_toggle.setChecked(
            self.settings.get("performance_mode", False)
        )
        
        # GPU加速
        self.gpu_toggle.setChecked(
            self.settings.get("gpu_acceleration", True)
        )
        
        # 调试模式
        self.debug_toggle.setChecked(
            self.settings.get("debug_mode", False)
        )
        
        # 自动更新
        self.update_toggle.setChecked(
            self.settings.get("auto_update", True)
        )
        
    def _save_settings(self):
        """保存设置到文件 - 需求：9.8
        
        注意：所有设置已经通过实时更新机制保存到 self.settings 中，
        这里只需要持久化到文件并通知主窗口应用最终状态
        """
        # 显示保存成功反馈
        self._show_saved_feedback()
        
        # 通知主窗口保存设置到文件
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'saveSettings'):
                parent.saveSettings()
        except Exception as e:
            logger.debug(f"保存设置到文件失败: {e}")
        
        # 延迟关闭对话框
        QTimer.singleShot(800, self.accept)
        
    def _show_saved_feedback(self):
        """显示保存成功的视觉反馈 - 需求：9.8"""
        # 改变按钮文字和颜色
        original_text = self.save_btn.text()
        self.save_btn.setText("✓ 已保存")
        
        success_color = self.palette.get_color("success", self.is_dark_mode)
        success_hover = self.palette.get_color("success_hover", self.is_dark_mode)
        
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {success_color.name()};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {success_hover.name()};
            }}
        """)
        
        # 显示Toast通知
        self.toast_manager.show("设置已保存", "success")
        
        # 恢复按钮
        def restore_button():
            self.save_btn.setText(original_text)
            accent = self.palette.get_color("accent", self.is_dark_mode)
            accent_hover = self.palette.get_color("accent_hover", self.is_dark_mode)
            accent_active = self.palette.get_color("accent_active", self.is_dark_mode)
            
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {accent.name()};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {accent_hover.name()};
                }}
                QPushButton:pressed {{
                    background-color: {accent_active.name()};
                }}
            """)
        
        QTimer.singleShot(1500, restore_button)
    
    def _reset_to_defaults(self):
        """重置为默认设置"""
        # 重置所有控件为默认值
        self.theme_combo.setCurrentIndex(0)  # 浅色
        self.transparency_slider.setValue(200)
        self.language_combo.setCurrentIndex(0)  # 简体中文
        self.preview_size_combo.setCurrentIndex(1)  # 中
        self.images_per_page_spin.setValue(24)
        self.timeout_spin.setValue(30)
        self.concurrent_spin.setValue(3)
        self.skip_duplicates_toggle.setChecked(True)
        self.animation_toggle.setChecked(True)
        self.performance_toggle.setChecked(False)
        self.gpu_toggle.setChecked(True)
        self.debug_toggle.setChecked(False)
        self.update_toggle.setChecked(True)
        
        # 显示提示
        self.toast_manager.show("已重置为默认设置", "info")
        
    def get_settings(self) -> dict:
        """获取设置"""
        return self.settings
    
    def _apply_transparency_to_parent(self, value: int):
        """将透明度应用到主窗口"""
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'modern_ui_manager'):
                # 更新主窗口的玻璃效果透明度
                if hasattr(parent.modern_ui_manager, 'update_glass_transparency'):
                    parent.modern_ui_manager.update_glass_transparency(value)
                # 更新主窗口设置
                if hasattr(parent, 'settings'):
                    parent.settings['glass_transparency'] = value
        except Exception as e:
            logger.debug(f"应用透明度到主窗口失败: {e}")
    
    def _apply_theme_to_parent(self):
        """将主题应用到主窗口"""
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'applyTheme'):
                parent.applyTheme()
        except Exception as e:
            logger.debug(f"应用主题到主窗口失败: {e}")
    
    def _apply_language_to_parent(self, language: str):
        """将语言应用到主窗口"""
        try:
            parent = self.parent()
            if parent:
                # 更新主窗口设置
                if hasattr(parent, 'settings'):
                    parent.settings['language'] = language
                # 刷新主窗口界面文本
                if hasattr(parent, 'refreshUITexts'):
                    parent.refreshUITexts()
        except Exception as e:
            logger.debug(f"应用语言到主窗口失败: {e}")
    
    def _apply_preview_size_to_parent(self, preview_size: str):
        """将预览大小应用到主窗口"""
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'image_preview'):
                # 更新预览图片大小
                size_map = {
                    "小 (150x150)": QSize(150, 150),
                    "中 (200x200)": QSize(200, 200),
                    "大 (300x300)": QSize(300, 300)
                }
                icon_size = size_map.get(preview_size, QSize(200, 200))
                parent.image_preview.image_list.setIconSize(icon_size)
                
                # 更新主窗口设置
                if hasattr(parent, 'settings'):
                    parent.settings['preview_size'] = preview_size
        except Exception as e:
            logger.debug(f"应用预览大小到主窗口失败: {e}")
    
    def _apply_animation_to_parent(self, enabled: bool):
        """将动画设置应用到主窗口"""
        try:
            parent = self.parent()
            if parent:
                # 更新主窗口设置
                if hasattr(parent, 'settings'):
                    parent.settings['enable_animations'] = enabled
                # 更新动画管理器
                if hasattr(parent, 'modern_ui_manager') and parent.modern_ui_manager:
                    if hasattr(parent.modern_ui_manager, 'set_animations_enabled'):
                        parent.modern_ui_manager.set_animations_enabled(enabled)
        except Exception as e:
            logger.debug(f"应用动画设置到主窗口失败: {e}")
    
    def _apply_performance_to_parent(self, enabled: bool):
        """将性能模式应用到主窗口"""
        try:
            parent = self.parent()
            if parent:
                # 更新主窗口设置
                if hasattr(parent, 'settings'):
                    parent.settings['performance_mode'] = enabled
                # 更新性能优化器
                if hasattr(parent, 'modern_ui_manager') and parent.modern_ui_manager:
                    if hasattr(parent.modern_ui_manager, 'set_performance_mode'):
                        parent.modern_ui_manager.set_performance_mode(enabled)
        except Exception as e:
            logger.debug(f"应用性能模式到主窗口失败: {e}")
    
    def _refresh_dialog_texts(self):
        """刷新对话框的所有文本（用于语言切换）"""
        try:
            # 更新窗口标题
            self.setWindowTitle(self.i18n.t("settings_dialog.title"))
            
            # 更新标题标签
            self.title_label.setText(self.i18n.t("settings_dialog.title"))
            
            # 更新分组标题
            if hasattr(self, 'appearance_group'):
                self.appearance_group.title_label.setText(self.i18n.t("settings_dialog.ui_group"))
            if hasattr(self, 'download_group'):
                self.download_group.title_label.setText(self.i18n.t("settings_dialog.download_group"))
            
            # 更新按钮文本
            if hasattr(self, 'save_btn'):
                self.save_btn.setText(self.i18n.t("settings_dialog.ok"))
            if hasattr(self, 'cancel_btn'):
                self.cancel_btn.setText(self.i18n.t("settings_dialog.cancel"))
            if hasattr(self, 'reset_btn'):
                self.reset_btn.setText(self.i18n.t("common.reset_default"))
        except Exception as e:
            logger.debug(f"刷新对话框文本失败: {e}")

    def _apply_enhanced_combobox_style(self, combobox: QComboBox):
        """应用增强的下拉框样式 - 使用SVG箭头图标"""
        try:
            from ui.custom_arrows import CustomArrows
        except ImportError:
            from .custom_arrows import CustomArrows
        
        # 创建箭头图标并保存到临时文件
        import tempfile
        import os
        
        # 创建向下箭头图标 - 使用灰色
        down_arrow = CustomArrows.create_arrow_icon("down", "#646464", 16)
        down_arrow_hover = CustomArrows.create_arrow_icon("down", "#888888", 16)
        
        # 保存图标到临时文件
        temp_dir = tempfile.gettempdir()
        down_arrow_path = os.path.join(temp_dir, "combobox_down_arrow.png")
        down_arrow_hover_path = os.path.join(temp_dir, "combobox_down_arrow_hover.png")
        
        down_arrow.save(down_arrow_path)
        down_arrow_hover.save(down_arrow_hover_path)
        
        # 转换路径为URL格式（Windows路径需要特殊处理）
        down_arrow_url = down_arrow_path.replace("\\", "/")
        down_arrow_hover_url = down_arrow_hover_path.replace("\\", "/")
        
        combobox.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 10px 40px 10px 14px;
                color: rgb(60, 60, 60);
                font-size: 22px;
                font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
                min-height: 44px;
            }}
            QComboBox:hover {{
                background-color: rgba(255, 255, 255, 220);
                border-color: rgba(204, 204, 204, 255);
            }}
            QComboBox:focus {{
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid rgb(59, 130, 246);
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: 0px;
            }}
            QComboBox::down-arrow {{
                image: url({down_arrow_url});
                width: 18px;
                height: 18px;
                right: 12px;
            }}
            QComboBox:hover::down-arrow {{
                image: url({down_arrow_hover_url});
            }}
            QComboBox QAbstractItemView {{
                background-color: rgb(255, 255, 255);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                selection-background-color: rgb(59, 130, 246);
                selection-color: white;
                color: rgb(60, 60, 60);
                outline: none;
                padding: 6px;
                font-size: 22px;
                font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 48px;
                padding: 12px 14px;
                border-radius: 6px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: rgba(59, 130, 246, 50);
            }}
        """)
    
    def _apply_enhanced_spinbox_style(self, spinbox: QSpinBox):
        """应用增强的数字输入框样式 - 使用SVG箭头图标"""
        try:
            from ui.custom_arrows import CustomArrows
        except ImportError:
            from .custom_arrows import CustomArrows
        
        # 创建箭头图标并保存到临时文件
        import tempfile
        import os
        
        # 创建向上和向下箭头图标
        up_arrow = CustomArrows.create_arrow_icon("up", "#646464", 14)
        up_arrow_hover = CustomArrows.create_arrow_icon("up", "#3b82f6", 14)
        down_arrow = CustomArrows.create_arrow_icon("down", "#646464", 14)
        down_arrow_hover = CustomArrows.create_arrow_icon("down", "#3b82f6", 14)
        
        # 保存图标到临时文件
        temp_dir = tempfile.gettempdir()
        up_arrow_path = os.path.join(temp_dir, "spinbox_up_arrow.png")
        up_arrow_hover_path = os.path.join(temp_dir, "spinbox_up_arrow_hover.png")
        down_arrow_path = os.path.join(temp_dir, "spinbox_down_arrow.png")
        down_arrow_hover_path = os.path.join(temp_dir, "spinbox_down_arrow_hover.png")
        
        up_arrow.save(up_arrow_path)
        up_arrow_hover.save(up_arrow_hover_path)
        down_arrow.save(down_arrow_path)
        down_arrow_hover.save(down_arrow_hover_path)
        
        # 转换路径为URL格式（Windows路径需要特殊处理）
        up_arrow_url = up_arrow_path.replace("\\", "/")
        up_arrow_hover_url = up_arrow_hover_path.replace("\\", "/")
        down_arrow_url = down_arrow_path.replace("\\", "/")
        down_arrow_hover_url = down_arrow_hover_path.replace("\\", "/")
        
        spinbox.setStyleSheet(f"""
            QSpinBox {{
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 8px 12px;
                color: rgb(60, 60, 60);
                font-size: 20px;
                min-height: 40px;
                min-width: 100px;
            }}
            QSpinBox:hover {{
                background-color: rgba(255, 255, 255, 220);
                border-color: rgba(59, 130, 246, 200);
            }}
            QSpinBox:focus {{
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid rgb(59, 130, 246);
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid rgba(200, 200, 200, 150);
                border-top-right-radius: 8px;
                background-color: transparent;
            }}
            QSpinBox::up-button:hover {{
                background-color: rgba(59, 130, 246, 80);
            }}
            QSpinBox::up-arrow {{
                image: url({up_arrow_url});
                width: 14px;
                height: 14px;
            }}
            QSpinBox::up-button:hover QSpinBox::up-arrow {{
                image: url({up_arrow_hover_url});
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 28px;
                border-left: 1px solid rgba(200, 200, 200, 150);
                border-bottom-right-radius: 8px;
                background-color: transparent;
            }}
            QSpinBox::down-button:hover {{
                background-color: rgba(59, 130, 246, 80);
            }}
            QSpinBox::down-arrow {{
                image: url({down_arrow_url});
                width: 14px;
                height: 14px;
            }}
            QSpinBox::down-button:hover QSpinBox::down-arrow {{
                image: url({down_arrow_hover_url});
            }}
        """)
    
    def _apply_enhanced_input_style(self, lineedit: QLineEdit):
        """应用增强的输入框样式"""
        lineedit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 8px 12px;
                color: rgb(60, 60, 60);
                font-size: 16px;
                min-height: 40px;
            }
            QLineEdit:hover {
                background-color: rgba(255, 255, 255, 220);
                border-color: rgba(59, 130, 246, 200);
            }
            QLineEdit:focus {
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid rgb(59, 130, 246);
            }
        """)
