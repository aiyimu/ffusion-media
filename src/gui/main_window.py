import sys
import traceback
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QPushButton, QFrame, 
    QScrollArea, QSplitter, QStatusBar, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize, Signal, QMimeData
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QFont

from src.utils.logger import get_logger
from src.utils.config_manager import ConfigManager
from src.modules import get_module_manager
from src.utils.validator import get_supported_media_formats
from src.gui.pages import (
    FormatConverterPage,
    VideoCutterPage,
    AudioProcessorPage,
    ImageConverterPage,
    TaskQueuePage,
    SettingsPage
)
from src.gui.dialogs import (
    LogViewerDialog,
    AboutDialog
)
from src.gui.themes import get_dark_theme, get_light_theme


logger = get_logger(__name__)


class ModuleNavButton(QPushButton):
    module_selected = Signal(str)
    
    def __init__(self, module_name: str, module_description: str, icon_text: str, parent=None):
        super().__init__(parent)
        self.module_name = module_name
        self._setup_ui(icon_text, module_name, module_description)
    
    def _setup_ui(self, icon_text: str, name: str, description: str):
        self.setCheckable(True)
        self.setMinimumHeight(70)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        icon_label = QLabel(icon_text)
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11px; opacity: 0.7;")
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(name_label)
        text_layout.addWidget(desc_label)
        text_layout.addStretch()
        
        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)
        
        self.clicked.connect(lambda: self.module_selected.emit(self.module_name))


class SidebarWidget(QWidget):
    module_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = {}
        self._current_module = None
        self._setup_ui()
        self._load_modules()
    
    def _setup_ui(self):
        self.setFixedWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QWidget()
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 10)
        
        title = QLabel("FFusion Media")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        subtitle = QLabel("媒体处理工具箱")
        subtitle.setStyleSheet("font-size: 12px; opacity: 0.7;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self._nav_container = QWidget()
        self._nav_layout = QVBoxLayout(self._nav_container)
        self._nav_layout.setContentsMargins(10, 15, 10, 15)
        self._nav_layout.setSpacing(8)
        self._nav_layout.addStretch()
        
        scroll.setWidget(self._nav_container)
        layout.addWidget(scroll, 1)
    
    def _load_modules(self):
        manager = get_module_manager()
        categories = manager.get_categories()
        
        icons = {
            "视频": "🎬",
            "音频": "🎵",
            "图像": "🖼️"
        }
        
        for category in categories:
            if category in icons:
                cat_label = QLabel(category)
                cat_label.setStyleSheet("font-size: 12px; font-weight: bold; padding: 10px 5px 5px; opacity: 0.6;")
                self._nav_layout.insertWidget(self._nav_layout.count() - 1, cat_label)
            
            modules = manager.get_modules_by_category(category)
            for module_class in modules:
                icon = icons.get(category, "📦")
                btn = ModuleNavButton(
                    module_class.name,
                    module_class.description,
                    icon
                )
                btn.module_selected.connect(self._on_module_selected)
                self._nav_layout.insertWidget(self._nav_layout.count() - 1, btn)
                self._buttons[module_class.name] = btn
        
        queue_cat_label = QLabel("管理")
        queue_cat_label.setStyleSheet("font-size: 12px; font-weight: bold; padding: 10px 5px 5px; opacity: 0.6;")
        self._nav_layout.insertWidget(self._nav_layout.count() - 1, queue_cat_label)
        
        queue_btn = ModuleNavButton(
            "任务队列",
            "管理所有媒体处理任务",
            "📋"
        )
        queue_btn.module_selected.connect(self._on_module_selected)
        self._nav_layout.insertWidget(self._nav_layout.count() - 1, queue_btn)
        self._buttons["任务队列"] = queue_btn
        
        settings_cat_label = QLabel("系统")
        settings_cat_label.setStyleSheet("font-size: 12px; font-weight: bold; padding: 10px 5px 5px; opacity: 0.6;")
        self._nav_layout.insertWidget(self._nav_layout.count() - 1, settings_cat_label)
        
        settings_btn = ModuleNavButton(
            "设置",
            "配置 FFusion Media",
            "⚙️"
        )
        settings_btn.module_selected.connect(self._on_module_selected)
        self._nav_layout.insertWidget(self._nav_layout.count() - 1, settings_btn)
        self._buttons["设置"] = settings_btn
    
    def _on_module_selected(self, module_name: str):
        if self._current_module:
            self._buttons[self._current_module].setChecked(False)
        
        self._current_module = module_name
        self._buttons[module_name].setChecked(True)
        self.module_changed.emit(module_name)
    
    def select_module(self, module_name: str):
        if module_name in self._buttons:
            self._buttons[module_name].click()


class TopBarWidget(QWidget):
    theme_toggled = Signal()
    settings_clicked = Signal()
    logs_clicked = Signal()
    about_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)
        
        logo_label = QLabel("⚡")
        logo_label.setStyleSheet("font-size: 24px;")
        
        title_label = QLabel("FFusion Media")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        
        layout.addWidget(logo_label)
        layout.addWidget(title_label)
        layout.addStretch()
        
        self._theme_btn = QPushButton("🌙")
        self._theme_btn.setFixedSize(40, 40)
        self._theme_btn.setCursor(Qt.PointingHandCursor)
        self._theme_btn.setToolTip("切换明暗主题")
        self._theme_btn.clicked.connect(self.theme_toggled.emit)
        
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(40, 40)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setToolTip("打开设置")
        settings_btn.clicked.connect(self.settings_clicked.emit)
        
        logs_btn = QPushButton("📋")
        logs_btn.setFixedSize(40, 40)
        logs_btn.setCursor(Qt.PointingHandCursor)
        logs_btn.setToolTip("查看日志")
        logs_btn.clicked.connect(self.logs_clicked.emit)
        
        about_btn = QPushButton("❓")
        about_btn.setFixedSize(40, 40)
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.setToolTip("关于 FFusion Media")
        about_btn.clicked.connect(self.about_clicked.emit)
        
        layout.addWidget(self._theme_btn)
        layout.addWidget(settings_btn)
        layout.addWidget(logs_btn)
        layout.addWidget(about_btn)
    
    def set_theme_icon(self, is_dark: bool):
        self._theme_btn.setText("🌙" if is_dark else "☀️")


class StatusBarWidget(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedHeight(35)
        
        self._status_label = QLabel("就绪")
        self._progress_label = QLabel("")
        
        self.addWidget(self._status_label, 1)
        self.addPermanentWidget(self._progress_label)
    
    def update_status(self, message: str):
        self._status_label.setText(message)
    
    def update_progress(self, progress: float, message: str = ""):
        if progress > 0:
            self._progress_label.setText(f"{progress:.1f}% {message}")
        else:
            self._progress_label.setText("")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._config = ConfigManager()
        theme = self._config.get("basic", "theme", "dark")
        self._is_dark_theme = theme == "dark"
        self._module_pages = {}
        
        self._setup_ui()
        self._apply_theme()
        self._setup_global_exception_handler()
        
        logger.info("主窗口初始化完成")
    
    def _setup_ui(self):
        self.setWindowTitle("FFusion Media")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        self.setAcceptDrops(True)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self._top_bar = TopBarWidget()
        self._top_bar.theme_toggled.connect(self._toggle_theme)
        self._top_bar.settings_clicked.connect(self._show_settings)
        self._top_bar.logs_clicked.connect(self._show_logs)
        self._top_bar.about_clicked.connect(self._show_about)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self._sidebar = SidebarWidget()
        self._sidebar.module_changed.connect(self._switch_module)
        
        self._stack = QStackedWidget()
        
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        self._status_bar = StatusBarWidget()
        self.setStatusBar(self._status_bar)
        
        main_layout.addWidget(self._top_bar)
        main_layout.addWidget(splitter, 1)
        
        self._create_welcome_page()
    
    def _create_welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(30)
        layout.setContentsMargins(60, 60, 60, 60)
        
        welcome = QLabel("欢迎使用 FFusion Media")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet("font-size: 32px; font-weight: bold;")
        
        subtitle = QLabel("拖拽媒体文件到窗口开始处理，或从左侧选择功能")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; opacity: 0.7;")
        
        layout.addStretch()
        layout.addWidget(welcome)
        layout.addWidget(subtitle)
        layout.addStretch()
        
        self._stack.addWidget(page)
        self._module_pages["welcome"] = 0
    
    def _toggle_theme(self):
        self._is_dark_theme = not self._is_dark_theme
        self._config.set("basic", "theme", "dark" if self._is_dark_theme else "light")
        self._apply_theme()
        self._top_bar.set_theme_icon(self._is_dark_theme)
    
    def _on_settings_changed(self):
        theme = self._config.get("basic", "theme", "dark")
        new_is_dark = theme == "dark"
        
        if new_is_dark != self._is_dark_theme:
            self._is_dark_theme = new_is_dark
            self._apply_theme()
            self._top_bar.set_theme_icon(self._is_dark_theme)
            logger.info(f"主题已切换为: {'深色' if self._is_dark_theme else '浅色'}")
    
    def _apply_theme(self):
        if self._is_dark_theme:
            qss = get_dark_theme()
            if qss:
                self.setStyleSheet(qss)
            else:
                self.setStyleSheet("""
                    QMainWindow, QWidget { background-color: #1a1a2e; color: #eee; }
                    QPushButton { background-color: #16213e; border: none; border-radius: 8px; padding: 8px; }
                    QPushButton:hover { background-color: #0f3460; }
                    QPushButton:checked { background-color: #e94560; }
                    QScrollArea { border: none; }
                    QStatusBar { background-color: #0f3460; }
                    QFrame[frameShape="4"] { background-color: #16213e; height: 1px; }
                """)
        else:
            qss = get_light_theme()
            if qss:
                self.setStyleSheet(qss)
            else:
                self.setStyleSheet("""
                    QMainWindow, QWidget { background-color: #f5f5f5; color: #333; }
                    QPushButton { background-color: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 8px; }
                    QPushButton:hover { background-color: #e9ecef; }
                    QPushButton:checked { background-color: #e94560; color: white; }
                    QScrollArea { border: none; }
                    QStatusBar { background-color: #e9ecef; }
                    QFrame[frameShape="4"] { background-color: #ddd; height: 1px; }
                """)
        self._top_bar.set_theme_icon(self._is_dark_theme)
    
    def _switch_module(self, module_name: str):
        if module_name in self._module_pages:
            self._stack.setCurrentIndex(self._module_pages[module_name])
            self._status_bar.update_status(f"当前模块: {module_name}")
            return
        
        if module_name in ["任务队列", "设置"]:
            page = self._create_module_page(module_name)
        else:
            manager = get_module_manager()
            module = manager.get_module(module_name)
            if module:
                page = self._create_module_page(module_name, module)
            else:
                return
        
        self._module_pages[module_name] = self._stack.addWidget(page)
        self._stack.setCurrentIndex(self._module_pages[module_name])
        self._status_bar.update_status(f"当前模块: {module_name}")
    
    def _create_module_page(self, module_name: str, module=None):
        if module_name == "格式转换":
            return FormatConverterPage()
        elif module_name == "视频剪切":
            return VideoCutterPage()
        elif module_name == "音频处理":
            return AudioProcessorPage()
        elif module_name == "图像转换":
            return ImageConverterPage()
        elif module_name == "任务队列":
            return TaskQueuePage()
        elif module_name == "设置":
            settings_page = SettingsPage()
            settings_page.settings_changed.connect(self._on_settings_changed)
            return settings_page
        else:
            page = QWidget()
            layout = QVBoxLayout(page)
            
            title = QLabel(module_name)
            title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px 0;")
            
            desc = QLabel(module.description if module else "")
            desc.setStyleSheet("font-size: 14px; opacity: 0.7; padding-bottom: 20px;")
            
            placeholder = QLabel(f"{module_name} 功能开发中...")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("font-size: 18px; opacity: 0.5;")
            
            layout.addWidget(title)
            if module:
                layout.addWidget(desc)
            layout.addWidget(placeholder, 1)
            
            return page
    
    def _show_settings(self):
        self._sidebar.select_module("设置")
    
    def _show_logs(self):
        dialog = LogViewerDialog(self)
        dialog.exec()
    
    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        manager = get_module_manager()
        supported_formats = set(get_supported_media_formats())
        
        files = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in supported_formats:
                files.append(str(path))
        
        if files:
            logger.info(f"拖拽导入文件: {files}")
            self._status_bar.update_status(f"已导入 {len(files)} 个文件")
            
            QMessageBox.information(
                self,
                "文件导入",
                f"成功导入 {len(files)} 个媒体文件\n\n"
                f"请从左侧选择功能模块进行处理"
            )
    
    def _setup_global_exception_handler(self):
        def exception_hook(exc_type, exc_value, exc_traceback):
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            logger.critical(f"未捕获的异常: {error_msg}")
            
            QMessageBox.critical(
                self,
                "程序错误",
                f"发生了一个未预期的错误：\n\n{str(exc_value)}\n\n"
                f"详细错误信息已写入日志文件。"
            )
        
        sys.excepthook = exception_hook
