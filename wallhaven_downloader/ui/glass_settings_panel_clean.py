# -*- coding: utf-8 -*-
"""
鐜荤拑璁剧疆闈㈡澘缁勪欢

浣跨敤娑叉€佺幓鐠冩晥鏋滈噸璁捐鐨勮缃潰鏉匡紝鍖呮嫭锛?- 鐜荤拑鍒嗙粍瀹瑰櫒
- 鐜颁唬鍖栬缃帶浠?- 瀹炴椂棰勮鏁堟灉
- 骞虫粦鍔ㄧ敾杩囨浮

闇€姹傦細9.1-9.8
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QSlider, QWidget, QScrollArea, QFrame, QLineEdit,
    QComboBox, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer, pyqtProperty
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient, QPixmap, QPoint

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


class GlassToggleSwitch(QWidget):
    """鐜荤拑椋庢牸寮€鍏崇粍浠?- 澧炲己鐗?""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checked = False
        self.setFixedSize(50, 24)
        self.setCursor(Qt.PointingHandCursor)
        
        # 鍔ㄧ敾鐩稿叧
        self._slider_pos = 2  # 婊戝潡浣嶇疆
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
        """缁樺埗鐜荤拑椋庢牸寮€鍏?- 甯﹀姩鐢诲拰闃村奖"""
        from PyQt5.QtGui import QPainter, QPen, QBrush, QLinearGradient
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 鑳屾櫙杞ㄩ亾 - 娓愬彉鏁堟灉
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
        
        # 婊戝潡闃村奖
        shadow_color = QColor(0, 0, 0, 60)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(self._slider_pos + 1, 3, 20, 20)
        
        # 婊戝潡 - 鐧借壊甯﹂珮鍏?        slider_gradient = QLinearGradient(self._slider_pos, 2, self._slider_pos, 22)
        slider_gradient.setColorAt(0, QColor(255, 255, 255))
        slider_gradient.setColorAt(1, QColor(245, 245, 245))
        painter.setBrush(QBrush(slider_gradient))
        painter.drawEllipse(self._slider_pos, 2, 20, 20)
        
    def mousePressEvent(self, event):
        """榧犳爣鐐瑰嚮浜嬩欢 - 甯﹀姩鐢?""
        self.checked = not self.checked
        
        # 鍚姩婊戝潡鍔ㄧ敾
        start_pos = 2 if not self.checked else 26
        end_pos = 26 if self.checked else 2
        self._animation.setStartValue(start_pos)
        self._animation.setEndValue(end_pos)
        self._animation.start()
        
        self.toggled.emit(self.checked)
        
    def setChecked(self, checked: bool):
        """璁剧疆寮€鍏崇姸鎬?""
        if self.checked != checked:
            self.checked = checked
            self._slider_pos = 26 if checked else 2
            self.update()
            
    def isChecked(self) -> bool:
        """鑾峰彇寮€鍏崇姸鎬?""
        return self.checked



class GlassCollapsibleGroup(QWidget):
    """鍙姌鍙犵殑鐜荤拑鍒嗙粍妗?""
    
    def __init__(self, title: str, icon_name: str = None, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon_name = icon_name
        self.is_collapsed = False
        
        # 绠＄悊鍣?        self.icon_manager = IconManager()
        self.animation_manager = EnhancedAnimationManager()
        self.glass_factory = GlassPanelFactory()
        
        self._setup_ui()
        
    def _setup_ui(self):
        """璁剧疆UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(8)
        
        # 浣跨敤鐜荤拑闈㈡澘浣滀负瀹瑰櫒
        self.glass_panel = self.glass_factory.create_panel(
            self,
            panel_type="normal"
        )
        
        panel_layout = QVBoxLayout(self.glass_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        
        # 鏍囬鏍?        self.header = QWidget()
        self.header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        # 鍥炬爣
        if self.icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(
                self.icon_manager.get_icon(self.icon_name, size=20)
                .pixmap(20, 20)
            )
            header_layout.addWidget(icon_label)
        
        # 鏍囬
        self.title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # 灞曞紑/鎶樺彔鍥炬爣
        self.arrow_label = QLabel("鈻?)
        self.arrow_label.setFont(QFont("", 10))
        header_layout.addWidget(self.arrow_label)
        
        # 鐐瑰嚮浜嬩欢
        self.header.mousePressEvent = lambda e: self.toggle()
        
        panel_layout.addWidget(self.header)
        
        # 鍒嗛殧绾?        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFixedHeight(1)
        self.separator.setStyleSheet("background-color: rgb(229, 231, 235);")
        panel_layout.addWidget(self.separator)
        
        # 鍐呭鍖哄煙
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 12, 20, 12)
        self.content_layout.setSpacing(16)
        
        panel_layout.addWidget(self.content_widget)
        
        layout.addWidget(self.glass_panel)
        
        # 搴旂敤鍥哄畾鏍峰紡
        self._apply_fixed_colors()
        
    def toggle(self):
        """鍒囨崲灞曞紑/鎶樺彔鐘舵€?- 甯﹀姩鐢?""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.arrow_label.setText("鈻?)
            # 鎶樺彔鍔ㄧ敾
            self.animation_manager.create_fade_animation(
                self.content_widget,
                start_opacity=1.0,
                end_opacity=0.0,
                duration=200
            ).start()
            QTimer.singleShot(200, lambda: self.content_widget.hide())
        else:
            self.arrow_label.setText("鈻?)
            self.content_widget.show()
            # 灞曞紑鍔ㄧ敾
            self.animation_manager.create_fade_animation(
                self.content_widget,
                start_opacity=0.0,
                end_opacity=1.0,
                duration=200
            ).start()
            
    def add_setting_item(self, widget: QWidget):
        """娣诲姞璁剧疆椤?""
        self.content_layout.addWidget(widget)
    
    def _apply_fixed_colors(self):
        """搴旂敤鍥哄畾鐨勬祬鑹蹭富棰橀鑹?""
        text_color = QColor(60, 60, 60)  # 娣辩伆鑹叉枃鏈?        separator_color = QColor(229, 231, 235)  # 娴呯伆鑹插垎闅旂嚎
        
        self.title_label.setStyleSheet(f"color: {text_color.name()};")
        self.arrow_label.setStyleSheet(f"color: {text_color.name()};")
        self.separator.setStyleSheet(f"background-color: {separator_color.name()};")



class GlassSettingItem(QWidget):
    """鐜荤拑椋庢牸璁剧疆椤圭粍浠?""
    
    def __init__(self, label: str, description: str = "", icon_name: str = None, parent=None):
        super().__init__(parent)
        self.label = label
        self.description = description
        self.icon_name = icon_name
        
        # 绠＄悊鍣?        self.icon_manager = IconManager()
        self.palette = AppleColorPalette()
        
        # 涓婚鐘舵€?        self.is_dark_mode = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        """璁剧疆UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        
        # 宸︿晶锛氬浘鏍囧拰鏂囧瓧
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        
        # 鏍囩琛岋紙鍥炬爣 + 鏍囩锛?        label_layout = QHBoxLayout()
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
        label_font.setPointSize(10)
        label_font.setBold(False)
        self.label_widget.setFont(label_font)
        label_layout.addWidget(self.label_widget)
        label_layout.addStretch()
        
        left_layout.addLayout(label_layout)
        
        # 鎻忚堪
        if self.description:
            self.desc_label = QLabel(self.description)
            self.desc_label.setWordWrap(True)
            desc_font = QFont()
            desc_font.setPointSize(9)
            self.desc_label.setFont(desc_font)
            left_layout.addWidget(self.desc_label)
        
        layout.addLayout(left_layout, stretch=1)
        
        # 鍙充晶锛氭帶浠跺鍣?        self.control_layout = QHBoxLayout()
        self.control_layout.setSpacing(8)
        layout.addLayout(self.control_layout)
        
        # 搴旂敤鍒濆涓婚
        self._apply_theme_colors()
        
    def add_control(self, widget: QWidget):
        """娣诲姞鎺т欢"""
        self.control_layout.addWidget(widget)
    
    def update_theme(self, is_dark_mode: bool):
        """鏇存柊涓婚"""
        self.is_dark_mode = is_dark_mode
        self._apply_theme_colors()
    
    def _apply_theme_colors(self):
        """搴旂敤涓婚棰滆壊"""
        text_primary = self.palette.get_color("text_primary", self.is_dark_mode)
        text_secondary = self.palette.get_color("text_secondary", self.is_dark_mode)
        
        self.label_widget.setStyleSheet(f"color: {text_primary.name()};")
        if self.description:
            self.desc_label.setStyleSheet(f"color: {text_secondary.name()};")



class GlassSettingsPanel(QDialog):
    """鐜荤拑椋庢牸璁剧疆闈㈡澘
    
    浣跨敤娑叉€佺幓鐠冩晥鏋滈噸璁捐鐨勮缃潰鏉?    闇€姹傦細9.1-9.8
    """
    
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self.original_settings = settings.copy()
        
        # 绠＄悊鍣?        self.i18n = get_i18n_manager()
        self.icon_manager = IconManager()
        self.animation_manager = EnhancedAnimationManager()
        
        # 浣跨敤涓荤獥鍙ｇ殑 toast_manager锛屽鏋滄病鏈夊垯鍒涘缓涓€涓娇鐢ㄤ富绐楀彛浣滀负鐖剁粍浠剁殑
        if hasattr(parent, 'modern_ui_manager') and parent.modern_ui_manager and hasattr(parent.modern_ui_manager, 'get_toast_manager'):
            self.toast_manager = parent.modern_ui_manager.get_toast_manager()
        else:
            # 鍥為€€鏂规锛氫娇鐢ㄤ富绐楀彛浣滀负鐖剁粍浠跺垱寤?toast_manager
            main_window = parent
            # 濡傛灉 parent 涓嶆槸涓荤獥鍙ｏ紝灏濊瘯鎵惧埌涓荤獥鍙?            while main_window and not hasattr(main_window, 'setMenuBar'):  # 涓荤獥鍙ｇ壒寰?                main_window = main_window.parent() if hasattr(main_window, 'parent') else None
            
            if main_window:
                self.toast_manager = ToastManager(main_window)
            else:
                # 鏈€鍚庣殑鍥為€€鏂规锛氫娇鐢ㄥ綋鍓嶅璇濇
                self.toast_manager = ToastManager(self)
        
        self.glass_factory = GlassPanelFactory()
        self.palette = AppleColorPalette()
        
        # 涓婚绠＄悊鍣?        try:
            self.theme_manager = get_enhanced_theme_manager()
        except Exception:
            self.theme_manager = get_theme_manager()
        
        # 妫€娴嬪綋鍓嶄富棰?        self.is_dark_mode = False
        
        # 璁剧疆绐楀彛
        self.setWindowTitle(self.i18n.t("settings_dialog.title"))
        self.setMinimumSize(950, 750)
        self.resize(950, 750)
        
        # 鏃犺竟妗嗙獥鍙ｏ紙鍙€夛級
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._setup_ui()
        self._load_settings()
        self._apply_dialog_theme()
        
    def _detect_dark_mode(self) -> bool:
        """妫€娴嬪綋鍓嶆槸鍚︿负娣辫壊妯″紡"""
        try:
            if hasattr(self.theme_manager, 'is_dark_mode'):
                return self.theme_manager.is_dark_mode()
            elif hasattr(self.theme_manager, 'current_theme'):
                return self.theme_manager.current_theme == "娣辫壊"
            else:
                return False
        except:
            return False
        
    def _setup_ui(self):
        """璁剧疆UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # 鏍囬
        self.title_label = QLabel(self.i18n.t("settings_dialog.title"))
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        main_layout.addWidget(self.title_label)
        
        # 婊氬姩鍖哄煙
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("QWidget { background: transparent; }")
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(16)
        
        # 澶栬璁剧疆鍒嗙粍
        self._create_appearance_settings(self.scroll_layout)
        
        # 涓嬭浇璁剧疆鍒嗙粍
        self._create_download_settings(self.scroll_layout)
        
        # 鎬ц兘璁剧疆鍒嗙粍
        self._create_performance_settings(self.scroll_layout)
        
        # 楂樼骇璁剧疆鍒嗙粍
        self._create_advanced_settings(self.scroll_layout)
        
        # 鍏充簬鍒嗙粍
        self._create_about_section(self.scroll_layout)
        
        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # 搴曢儴鎸夐挳
        self._create_buttons(main_layout)
        
    def _create_appearance_settings(self, parent_layout: QVBoxLayout):
        """鍒涘缓澶栬璁剧疆鍒嗙粍 - 闇€姹傦細9.1-9.2"""
        group = GlassCollapsibleGroup(
            self.i18n.t("settings_dialog.ui_group"),
            "settings"
        )
        
        # 涓婚璁剧疆
        theme_item = GlassSettingItem(
            self.i18n.t("settings_dialog.theme"),
            "閫夋嫨鐣岄潰涓婚椋庢牸锛堜粎娴呰壊锛?,
            "sun"
        )
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            self.i18n.t("theme.light")
        ])
        self.theme_combo.setMinimumWidth(200)
        self._apply_enhanced_combobox_style(self.theme_combo)
        self.theme_combo.currentIndexChanged.connect(self._preview_theme_change)
        theme_item.add_control(self.theme_combo)
        group.add_setting_item(theme_item)
        
        # 鐜荤拑閫忔槑搴?- 闇€姹傦細9.4, 9.5
        transparency_item = GlassSettingItem(
            self.i18n.t("settings_dialog.transparency"),
            "璋冩暣鐜荤拑鏁堟灉鐨勯€忔槑搴︼紙100-255锛?,
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
        
        # 棰勮妗?        self.transparency_preview = QWidget()
        self.transparency_preview.setFixedSize(30, 30)
        
        self.transparency_slider.valueChanged.connect(
            lambda v: self._update_transparency_preview(v)
        )
        
        transparency_layout.addWidget(self.transparency_slider)
        transparency_layout.addWidget(self.transparency_label)
        transparency_layout.addWidget(self.transparency_preview)
        
        transparency_item.add_control(transparency_widget)
        group.add_setting_item(transparency_item)
        
        # 璇█璁剧疆
        language_item = GlassSettingItem(
            self.i18n.t("settings_dialog.language"),
            "閫夋嫨鐣岄潰鏄剧ず璇█",
            "globe"
        )
        self.language_combo = QComboBox()
        self.language_combo.addItems(["绠€浣撲腑鏂?, "English"])
        self.language_combo.setMinimumWidth(200)
        self._apply_enhanced_combobox_style(self.language_combo)
        language_item.add_control(self.language_combo)
        group.add_setting_item(language_item)
        
        # 棰勮鍥剧墖澶у皬
        preview_item = GlassSettingItem(
            self.i18n.t("settings_dialog.preview_size"),
            "璁剧疆鍥剧墖棰勮鐨勭缉鐣ュ浘澶у皬",
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
        preview_item.add_control(self.preview_size_combo)
        group.add_setting_item(preview_item)
        
        parent_layout.addWidget(group)
        self.appearance_group = group
        
    def _create_download_settings(self, parent_layout: QVBoxLayout):
        """鍒涘缓涓嬭浇璁剧疆鍒嗙粍 - 闇€姹傦細9.1-9.2"""
        group = GlassCollapsibleGroup(
            self.i18n.t("settings_dialog.download_group"),
            "download"
        )
        
        # API瀵嗛挜
        api_item = GlassSettingItem(
            self.i18n.t("settings_dialog.api_key"),
            "Wallhaven API瀵嗛挜锛岀敤浜庤闂珮绾у姛鑳?,
            "key"
        )
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("杈撳叆API瀵嗛挜...")
        self.api_key_edit.setMinimumWidth(300)
        self._apply_enhanced_input_style(self.api_key_edit)
        api_item.add_control(self.api_key_edit)
        group.add_setting_item(api_item)
        
        # 姣忛〉鍥剧墖鏁?        images_item = GlassSettingItem(
            self.i18n.t("settings_dialog.images_per_page"),
            "姣忔璇锋眰鑾峰彇鐨勫浘鐗囨暟閲忥紙1-100锛?,
            "image"
        )
        self.images_per_page_spin = QSpinBox()
        self.images_per_page_spin.setRange(1, 100)
        self.images_per_page_spin.setValue(24)
        self._apply_enhanced_spinbox_style(self.images_per_page_spin)
        images_item.add_control(self.images_per_page_spin)
        group.add_setting_item(images_item)
        
        # 涓嬭浇瓒呮椂
        timeout_item = GlassSettingItem(
            self.i18n.t("settings_dialog.timeout"),
            "涓嬭浇璇锋眰鐨勮秴鏃舵椂闂达紙绉掞級",
            "clock"
        )
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" " + self.i18n.t("settings_dialog.seconds"))
        self._apply_enhanced_spinbox_style(self.timeout_spin)
        timeout_item.add_control(self.timeout_spin)
        group.add_setting_item(timeout_item)
        
        # 骞跺彂涓嬭浇鏁?        concurrent_item = GlassSettingItem(
            self.i18n.t("download.concurrent"),
            "鍚屾椂涓嬭浇鐨勫浘鐗囨暟閲忥紙1-10锛?,
            "layers"
        )
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        self._apply_enhanced_spinbox_style(self.concurrent_spin)
        concurrent_item.add_control(self.concurrent_spin)
        group.add_setting_item(concurrent_item)
        
        # 鑷姩璺宠繃閲嶅
        skip_item = GlassSettingItem(
            "鑷姩璺宠繃閲嶅",
            "涓嬭浇鏃惰嚜鍔ㄨ烦杩囧凡瀛樺湪鐨勬枃浠?,
            "check-circle"
        )
        self.skip_duplicates_toggle = GlassToggleSwitch()
        skip_item.add_control(self.skip_duplicates_toggle)
        group.add_setting_item(skip_item)
        
        parent_layout.addWidget(group)
        self.download_group = group
        
    def _create_performance_settings(self, parent_layout: QVBoxLayout):
        """鍒涘缓鎬ц兘璁剧疆鍒嗙粍 - 闇€姹傦細9.1-9.2"""
        group = GlassCollapsibleGroup(
            "鎬ц兘璁剧疆",
            "cpu"
        )
        
        # 鍚敤鍔ㄧ敾
        animation_item = GlassSettingItem(
            "鍚敤鍔ㄧ敾鏁堟灉",
            "寮€鍚晫闈㈠姩鐢诲拰杩囨浮鏁堟灉",
            "zap"
        )
        self.animation_toggle = GlassToggleSwitch()
        self.animation_toggle.setChecked(True)
        animation_item.add_control(self.animation_toggle)
        group.add_setting_item(animation_item)
        
        # 鎬ц兘妯″紡
        performance_item = GlassSettingItem(
            "鎬ц兘妯″紡",
            "闄嶄綆鍔ㄧ敾澶嶆潅搴︿互鎻愬崌鎬ц兘",
            "sliders"
        )
        self.performance_toggle = GlassToggleSwitch()
        performance_item.add_control(self.performance_toggle)
        group.add_setting_item(performance_item)
        
        # GPU鍔犻€?        gpu_item = GlassSettingItem(
            "GPU鍔犻€?,
            "浣跨敤GPU鍔犻€熸覆鏌擄紙闇€瑕侀噸鍚級",
            "cpu"
        )
        self.gpu_toggle = GlassToggleSwitch()
        self.gpu_toggle.setChecked(True)
        gpu_item.add_control(self.gpu_toggle)
        group.add_setting_item(gpu_item)
        
        parent_layout.addWidget(group)
        self.performance_group = group
        
    def _create_advanced_settings(self, parent_layout: QVBoxLayout):
        """鍒涘缓楂樼骇璁剧疆鍒嗙粍 - 闇€姹傦細9.1-9.2"""
        group = GlassCollapsibleGroup(
            "楂樼骇璁剧疆",
            "sliders"
        )
        
        # 璋冭瘯妯″紡
        debug_item = GlassSettingItem(
            "璋冭瘯妯″紡",
            "鍚敤璋冭瘯鏃ュ織鍜屾€ц兘鐩戞帶",
            "bug"
        )
        self.debug_toggle = GlassToggleSwitch()
        debug_item.add_control(self.debug_toggle)
        group.add_setting_item(debug_item)
        
        # 鑷姩鏇存柊
        update_item = GlassSettingItem(
            "鑷姩妫€鏌ユ洿鏂?,
            "鍚姩鏃惰嚜鍔ㄦ鏌ュ簲鐢ㄦ洿鏂?,
            "refresh-cw"
        )
        self.update_toggle = GlassToggleSwitch()
        self.update_toggle.setChecked(True)
        update_item.add_control(self.update_toggle)
        group.add_setting_item(update_item)
        
        parent_layout.addWidget(group)
        self.advanced_group = group
        
    def _create_about_section(self, parent_layout: QVBoxLayout):
        """鍒涘缓鍏充簬鍒嗙粍 - 闇€姹傦細9.1-9.2"""
        group = GlassCollapsibleGroup(
            "鍏充簬",
            "info"
        )
        
        # 鐗堟湰淇℃伅
        version_item = GlassSettingItem(
            "鐗堟湰",
            "Wallhaven Downloader v2.0.0",
            "package"
        )
        group.add_setting_item(version_item)
        
        # 浣滆€呬俊鎭?        author_item = GlassSettingItem(
            "浣滆€?,
            "寮€婧愰」鐩?- GitHub",
            "user"
        )
        group.add_setting_item(author_item)
        
        parent_layout.addWidget(group)
        self.about_group = group
        
    def _create_buttons(self, parent_layout: QVBoxLayout):
        """鍒涘缓搴曢儴鎸夐挳 - 闇€姹傦細9.8"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 閲嶇疆鎸夐挳
        self.reset_btn = GlassButton("閲嶇疆涓洪粯璁?)
        self.reset_btn.setMinimumSize(120, 40)
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        # 鍙栨秷鎸夐挳
        self.cancel_btn = GlassButton(self.i18n.t("settings_dialog.cancel"))
        self.cancel_btn.setMinimumSize(100, 40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # 淇濆瓨鎸夐挳
        self.save_btn = GlassButton(self.i18n.t("settings_dialog.ok"))
        self.save_btn.setMinimumSize(100, 40)
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)
        
        parent_layout.addLayout(button_layout)
        
    def _update_transparency_preview(self, value: int):
        """鏇存柊閫忔槑搴﹂瑙?- 闇€姹傦細9.5"""
        self.transparency_label.setText(str(value))
        
        # 瀹炴椂棰勮锛氭洿鏂伴瑙堟鐨勯€忔槑搴?        accent_color = self.palette.get_color("accent", self.is_dark_mode)
        self.transparency_preview.setStyleSheet(f"""
            QWidget {{
                background-color: rgba({accent_color.red()}, {accent_color.green()}, {accent_color.blue()}, {value});
                border-radius: 6px;
                border: 1px solid {self.palette.get_color("border", self.is_dark_mode).name()};
            }}
        """)
        
        # 瀹炴椂鏇存柊鎵€鏈夋寜閽殑閫忔槑搴?        self.reset_btn.set_glass_opacity(value)
        self.cancel_btn.set_glass_opacity(value)
        self.save_btn.set_glass_opacity(value)
    
    def _preview_theme_change(self, index: int):
        """棰勮涓婚鍒囨崲 - 闇€姹傦細9.5"""
        theme_name = "娴呰壊"
        self.is_dark_mode = False
        
        try:
            if hasattr(self.theme_manager, 'set_theme'):
                self.theme_manager.set_theme(theme_name)
        except:
            pass
        
        self._apply_dialog_theme()
        self._update_all_groups_theme()
    
    def _detect_system_dark_mode(self) -> bool:
        """妫€娴嬬郴缁熸槸鍚︿负娣辫壊妯″紡"""
        return False
        
    def _update_all_groups_theme(self):
        """鏇存柊鎵€鏈夊垎缁勭殑涓婚"""
        groups = [
            self.appearance_group,
            self.download_group,
            self.performance_group,
            self.advanced_group,
            self.about_group
        ]
        
        for group in groups:
            group.update_theme(self.is_dark_mode)
            # 鏇存柊鍒嗙粍鍐呯殑璁剧疆椤?            for i in range(group.content_layout.count()):
                item = group.content_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, GlassSettingItem):
                        widget.update_theme(self.is_dark_mode)
        
        # 鏇存柊寮€鍏崇粍浠?        self.skip_duplicates_toggle.update_theme(self.is_dark_mode)
        self.animation_toggle.update_theme(self.is_dark_mode)
        self.performance_toggle.update_theme(self.is_dark_mode)
        self.gpu_toggle.update_theme(self.is_dark_mode)
        self.debug_toggle.update_theme(self.is_dark_mode)
        self.update_toggle.update_theme(self.is_dark_mode)
    
    def _apply_dialog_theme(self):
        """搴旂敤瀵硅瘽妗嗕富棰?""
        bg_color = self.palette.get_color("background", self.is_dark_mode)
        text_primary = self.palette.get_color("text_primary", self.is_dark_mode)
        surface = self.palette.get_color("surface", self.is_dark_mode)
        border = self.palette.get_color("border", self.is_dark_mode)
        accent = self.palette.get_color("accent", self.is_dark_mode)
        accent_hover = self.palette.get_color("accent_hover", self.is_dark_mode)
        
        # 瀵硅瘽妗嗚儗鏅?        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color.name()};
            }}
            QLabel {{
                color: {text_primary.name()};
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
        """)
        
        # 鏇存柊鏍囬棰滆壊
        self.title_label.setStyleSheet(f"color: {text_primary.name()};")
        
    def _load_settings(self):
        """鍔犺浇璁剧疆"""
        # API瀵嗛挜
        self.api_key_edit.setText(
            self.settings.get("api_key", "dws2O4u6Agr4v1CC92mH90H1T49QSuTM")
        )
        
        # 璇█
        language = self.settings.get("language", "zh_CN")
        lang_index = 0 if language == "zh_CN" else 1
        self.language_combo.setCurrentIndex(lang_index)
        
        # 涓婚
        theme = self.settings.get("theme", "娴呰壊")
        theme_map = {"娴呰壊": 0}
        self.theme_combo.setCurrentIndex(theme_map.get(theme, 0))
        
        # 閫忔槑搴?        self.transparency_slider.setValue(
            self.settings.get("glass_transparency", 200)
        )
        
        # 姣忛〉鍥剧墖鏁?        self.images_per_page_spin.setValue(
            self.settings.get("images_per_page", 24)
        )
        
        # 瓒呮椂
        self.timeout_spin.setValue(
            self.settings.get("download_timeout", 30)
        )
        
        # 骞跺彂鏁?        self.concurrent_spin.setValue(
            self.settings.get("concurrent_downloads", 3)
        )
        
        # 棰勮澶у皬
        preview_size = self.settings.get("preview_size", "涓?(200x200)")
        size_map = {"灏?(150x150)": 0, "涓?(200x200)": 1, "澶?(300x300)": 2}
        self.preview_size_combo.setCurrentIndex(size_map.get(preview_size, 1))
        
        # 鑷姩璺宠繃閲嶅
        self.skip_duplicates_toggle.setChecked(
            self.settings.get("auto_skip_duplicates", True)
        )
        
        # 鍔ㄧ敾
        self.animation_toggle.setChecked(
            self.settings.get("enable_animations", True)
        )
        
        # 鎬ц兘妯″紡
        self.performance_toggle.setChecked(
            self.settings.get("performance_mode", False)
        )
        
        # GPU鍔犻€?        self.gpu_toggle.setChecked(
            self.settings.get("gpu_acceleration", True)
        )
        
        # 璋冭瘯妯″紡
        self.debug_toggle.setChecked(
            self.settings.get("debug_mode", False)
        )
        
        # 鑷姩鏇存柊
        self.update_toggle.setChecked(
            self.settings.get("auto_update", True)
        )
        
    def _save_settings(self):
        """淇濆瓨璁剧疆 - 闇€姹傦細9.8"""
        # 璇█
        language = "zh_CN" if self.language_combo.currentIndex() == 0 else "en_US"
        
        # 涓婚
        theme_list = ["娴呰壊"]
        theme = theme_list[0]
        
        # 棰勮澶у皬
        size_list = ["灏?(150x150)", "涓?(200x200)", "澶?(300x300)"]
        preview_size = size_list[self.preview_size_combo.currentIndex()]
        
        # 鏇存柊璁剧疆
        self.settings.update({
            "api_key": self.api_key_edit.text(),
            "theme": theme,
            "glass_transparency": self.transparency_slider.value(),
            "images_per_page": self.images_per_page_spin.value(),
            "download_timeout": self.timeout_spin.value(),
            "concurrent_downloads": self.concurrent_spin.value(),
            "preview_size": preview_size,
            "language": language,
            "auto_skip_duplicates": self.skip_duplicates_toggle.isChecked(),
            "enable_animations": self.animation_toggle.isChecked(),
            "performance_mode": self.performance_toggle.isChecked(),
            "gpu_acceleration": self.gpu_toggle.isChecked(),
            "debug_mode": self.debug_toggle.isChecked(),
            "auto_update": self.update_toggle.isChecked(),
        })
        
        # 鏄剧ず淇濆瓨鎴愬姛鍙嶉
        self._show_saved_feedback()
        
        # 寤惰繜鍏抽棴瀵硅瘽妗?        QTimer.singleShot(800, self.accept)
        
    def _show_saved_feedback(self):
        """鏄剧ず淇濆瓨鎴愬姛鐨勮瑙夊弽棣?- 闇€姹傦細9.8"""
        # 鏀瑰彉鎸夐挳鏂囧瓧鍜岄鑹?        original_text = self.save_btn.text()
        self.save_btn.setText("鉁?宸蹭繚瀛?)
        
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
        
        # 鏄剧ずToast閫氱煡
        self.toast_manager.show("璁剧疆宸蹭繚瀛?, "success")
        
        # 鎭㈠鎸夐挳
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
        """閲嶇疆涓洪粯璁よ缃?""
        # 閲嶇疆鎵€鏈夋帶浠朵负榛樿鍊?        self.theme_combo.setCurrentIndex(0)  # 娴呰壊
        self.transparency_slider.setValue(200)
        self.language_combo.setCurrentIndex(0)  # 绠€浣撲腑鏂?        self.preview_size_combo.setCurrentIndex(1)  # 涓?        self.images_per_page_spin.setValue(24)
        self.timeout_spin.setValue(30)
        self.concurrent_spin.setValue(3)
        self.skip_duplicates_toggle.setChecked(True)
        self.animation_toggle.setChecked(True)
        self.performance_toggle.setChecked(False)
        self.gpu_toggle.setChecked(True)
        self.debug_toggle.setChecked(False)
        self.update_toggle.setChecked(True)
        
        # 鏄剧ず鎻愮ず
        self.toast_manager.show("宸查噸缃负榛樿璁剧疆", "info")
        
    def get_settings(self) -> dict:
        """鑾峰彇璁剧疆"""
        return self.settings

    def _apply_enhanced_combobox_style(self, combobox: QComboBox):
        """搴旂敤澧炲己鐨勪笅鎷夋鏍峰紡"""
        combobox.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 8px 12px;
                color: rgb(60, 60, 60);
                font-size: 13px;
                min-height: 32px;
            }
            QComboBox:hover {
                background-color: rgba(255, 255, 255, 220);
                border-color: rgba(59, 130, 246, 200);
            }
            QComboBox:focus {
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid rgb(59, 130, 246);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                padding-right: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid rgb(100, 100, 100);
                width: 0px;
                height: 0px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: rgb(59, 130, 246);
            }
            QComboBox QAbstractItemView {
                background-color: rgb(255, 255, 255);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                selection-background-color: rgb(59, 130, 246);
                selection-color: white;
                color: rgb(60, 60, 60);
                outline: none;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(59, 130, 246, 50);
            }
        """)
    
    def _apply_enhanced_spinbox_style(self, spinbox: QSpinBox):
        """搴旂敤澧炲己鐨勬暟瀛楄緭鍏ユ鏍峰紡"""
        spinbox.setStyleSheet("""
            QSpinBox {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 8px 12px;
                color: rgb(60, 60, 60);
                font-size: 13px;
                min-height: 32px;
                min-width: 100px;
            }
            QSpinBox:hover {
                background-color: rgba(255, 255, 255, 220);
                border-color: rgba(59, 130, 246, 200);
            }
            QSpinBox:focus {
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid rgb(59, 130, 246);
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid rgba(200, 200, 200, 150);
                border-top-right-radius: 8px;
                background-color: rgba(240, 240, 240, 100);
            }
            QSpinBox::up-button:hover {
                background-color: rgba(59, 130, 246, 100);
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid rgb(100, 100, 100);
                width: 0px;
                height: 0px;
            }
            QSpinBox::up-arrow:hover {
                border-bottom-color: rgb(59, 130, 246);
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                border-left: 1px solid rgba(200, 200, 200, 150);
                border-bottom-right-radius: 8px;
                background-color: rgba(240, 240, 240, 100);
            }
            QSpinBox::down-button:hover {
                background-color: rgba(59, 130, 246, 100);
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid rgb(100, 100, 100);
                width: 0px;
                height: 0px;
            }
            QSpinBox::down-arrow:hover {
                border-top-color: rgb(59, 130, 246);
            }
        """)
    
    def _apply_enhanced_input_style(self, lineedit: QLineEdit):
        """搴旂敤澧炲己鐨勮緭鍏ユ鏍峰紡"""
        lineedit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 8px 12px;
                color: rgb(60, 60, 60);
                font-size: 13px;
                min-height: 32px;
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

                width: 0px;
                height: 0px;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                border-left: 1px solid rgba(200, 200, 200, 150);
                border-bottom-right-radius: 8px;
                background-color: rgba(240, 240, 240, 100);
            }
            QSpinBox::down-button:hover {
                background-color: rgba(59, 130, 246, 100);
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid rgb(100, 100, 100);
                width: 0px;
                height: 0px;
            }
        """)
    
    def _apply_enhanced_input_style(self, input_widget: QLineEdit):
        """搴旂敤澧炲己鐨勮緭鍏ユ鏍峰紡"""
        input_widget.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 8px;
                padding: 8px 12px;
                color: rgb(60, 60, 60);
                font-size: 13px;
                min-height: 32px;
