from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox, QLineEdit, 
    QFileDialog, QGroupBox, QFormLayout, QTabWidget,
    QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.utils.logger import get_logger
from src.utils.config_manager import ConfigManager


logger = get_logger(__name__)


class SettingsPage(QWidget):
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._setup_ui()
        self._load_settings()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("设置")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("配置 FFusion Media 的各项设置")
        desc.setStyleSheet("font-size: 14px; opacity: 0.7;")
        layout.addWidget(desc)
        
        self._tab_widget = QTabWidget()
        
        general_tab = self._create_general_tab()
        self._tab_widget.addTab(general_tab, "⚙️ 常规")
        
        ffmpeg_tab = self._create_ffmpeg_tab()
        self._tab_widget.addTab(ffmpeg_tab, "🎬 FFmpeg")
        
        batch_tab = self._create_batch_tab()
        self._tab_widget.addTab(batch_tab, "📦 批量处理")
        
        advanced_tab = self._create_advanced_tab()
        self._tab_widget.addTab(advanced_tab, "🔧 高级")
        
        layout.addWidget(self._tab_widget, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._reset_btn = QPushButton("↺ 恢复默认")
        self._reset_btn.setMinimumHeight(36)
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.clicked.connect(self._reset_settings)
        
        self._save_btn = QPushButton("💾 保存设置")
        self._save_btn.setMinimumHeight(36)
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #ff6b81;
            }
        """)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(self._save_settings)
        
        btn_layout.addWidget(self._reset_btn)
        btn_layout.addWidget(self._save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        general_group = QGroupBox("外观")
        general_form = QFormLayout(general_group)
        
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("深色主题", "dark")
        self._theme_combo.addItem("浅色主题", "light")
        general_form.addRow("主题:", self._theme_combo)
        
        self._log_level_combo = QComboBox()
        self._log_level_combo.addItem("调试 (DEBUG)", "DEBUG")
        self._log_level_combo.addItem("信息 (INFO)", "INFO")
        self._log_level_combo.addItem("警告 (WARNING)", "WARNING")
        self._log_level_combo.addItem("错误 (ERROR)", "ERROR")
        general_form.addRow("日志级别:", self._log_level_combo)
        
        output_dir_layout = QHBoxLayout()
        self._default_output_dir_edit = QLineEdit()
        self._default_output_dir_edit.setReadOnly(True)
        self._browse_output_btn = QPushButton("📂 选择")
        self._browse_output_btn.clicked.connect(self._browse_default_output_dir)
        output_dir_layout.addWidget(self._default_output_dir_edit, 1)
        output_dir_layout.addWidget(self._browse_output_btn)
        general_form.addRow("默认输出目录:", output_dir_layout)
        
        layout.addWidget(general_group)
        layout.addStretch()
        
        return tab
    
    def _create_ffmpeg_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        ffmpeg_group = QGroupBox("FFmpeg 路径设置")
        ffmpeg_form = QFormLayout(ffmpeg_group)
        
        ffmpeg_path_layout = QHBoxLayout()
        self._ffmpeg_path_edit = QLineEdit()
        self._ffmpeg_path_edit.setPlaceholderText("自动检测")
        self._browse_ffmpeg_btn = QPushButton("📂 选择 FFmpeg")
        self._browse_ffmpeg_btn.clicked.connect(self._browse_ffmpeg_path)
        ffmpeg_path_layout.addWidget(self._ffmpeg_path_edit, 1)
        ffmpeg_path_layout.addWidget(self._browse_ffmpeg_btn)
        ffmpeg_form.addRow("FFmpeg 路径:", ffmpeg_path_layout)
        
        ffprobe_path_layout = QHBoxLayout()
        self._ffprobe_path_edit = QLineEdit()
        self._ffprobe_path_edit.setPlaceholderText("自动检测")
        self._browse_ffprobe_btn = QPushButton("📂 选择 FFprobe")
        self._browse_ffprobe_btn.clicked.connect(self._browse_ffprobe_path)
        ffprobe_path_layout.addWidget(self._ffprobe_path_edit, 1)
        ffprobe_path_layout.addWidget(self._browse_ffprobe_btn)
        ffmpeg_form.addRow("FFprobe 路径:", ffprobe_path_layout)
        
        self._auto_detect_ffmpeg = QCheckBox("自动检测 FFmpeg 路径")
        self._auto_detect_ffmpeg.setChecked(True)
        ffmpeg_form.addRow("", self._auto_detect_ffmpeg)
        
        layout.addWidget(ffmpeg_group)
        layout.addStretch()
        
        return tab
    
    def _create_batch_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        batch_group = QGroupBox("批量处理设置")
        batch_form = QFormLayout(batch_group)
        
        self._max_concurrent_spin = QSpinBox()
        self._max_concurrent_spin.setRange(1, 10)
        self._max_concurrent_spin.setValue(1)
        self._max_concurrent_spin.setSuffix(" 个任务")
        batch_form.addRow("最大并发任务数:", self._max_concurrent_spin)
        
        self._auto_open_output = QCheckBox("完成后自动打开输出目录")
        self._auto_open_output.setChecked(True)
        batch_form.addRow("", self._auto_open_output)
        
        self._show_notification = QCheckBox("任务完成时显示通知")
        self._show_notification.setChecked(True)
        batch_form.addRow("", self._show_notification)
        
        self._confirm_overwrite = QCheckBox("覆盖文件前确认")
        self._confirm_overwrite.setChecked(True)
        batch_form.addRow("", self._confirm_overwrite)
        
        layout.addWidget(batch_group)
        layout.addStretch()
        
        return tab
    
    def _create_advanced_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        advanced_group = QGroupBox("高级设置")
        advanced_form = QFormLayout(advanced_group)
        
        self._temp_dir_edit = QLineEdit()
        self._temp_dir_edit.setPlaceholderText("系统临时目录")
        advanced_form.addRow("临时文件目录:", self._temp_dir_edit)
        
        self._keep_temp_files = QCheckBox("保留临时文件（调试用）")
        self._keep_temp_files.setChecked(False)
        advanced_form.addRow("", self._keep_temp_files)
        
        self._enable_debug_logging = QCheckBox("启用详细日志（调试用）")
        self._enable_debug_logging.setChecked(False)
        advanced_form.addRow("", self._enable_debug_logging)
        
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        return tab
    
    def _connect_signals(self):
        pass
    
    def _load_settings(self):
        theme = self._config.get("basic", "theme", "dark")
        index = self._theme_combo.findData(theme)
        if index >= 0:
            self._theme_combo.setCurrentIndex(index)
        
        log_level = self._config.get("advanced", "log_level", "INFO")
        index = self._log_level_combo.findData(log_level)
        if index >= 0:
            self._log_level_combo.setCurrentIndex(index)
        
        output_dir = self._config.get("basic", "default_output_dir", "")
        self._default_output_dir_edit.setText(output_dir)
        
        ffmpeg_path = self._config.get("ffmpeg", "ffmpeg_path", "")
        self._ffmpeg_path_edit.setText(ffmpeg_path)
        
        ffprobe_path = self._config.get("ffmpeg", "ffprobe_path", "")
        self._ffprobe_path_edit.setText(ffprobe_path)
        
        auto_detect = self._config.get_bool("ffmpeg", "auto_detect_ffmpeg", True)
        self._auto_detect_ffmpeg.setChecked(auto_detect)
        
        max_concurrent = self._config.get_int("advanced", "max_concurrent_tasks", 1)
        self._max_concurrent_spin.setValue(max_concurrent)
        
        auto_open = self._config.get_bool("basic", "auto_open_output", True)
        self._auto_open_output.setChecked(auto_open)
        
        show_notification = self._config.get_bool("interface", "show_notification", True)
        self._show_notification.setChecked(show_notification)
        
        confirm_overwrite = self._config.get_bool("advanced", "confirm_overwrite", True)
        self._confirm_overwrite.setChecked(confirm_overwrite)
        
        temp_dir = self._config.get("advanced", "temp_dir", "")
        self._temp_dir_edit.setText(temp_dir)
        
        keep_temp = self._config.get_bool("advanced", "keep_temp_files", False)
        self._keep_temp_files.setChecked(keep_temp)
        
        debug_logging = self._config.get_bool("advanced", "enable_debug_logging", False)
        self._enable_debug_logging.setChecked(debug_logging)
    
    def _save_settings(self):
        self._config.set("basic", "theme", self._theme_combo.currentData())
        self._config.set("advanced", "log_level", self._log_level_combo.currentData())
        self._config.set("basic", "default_output_dir", self._default_output_dir_edit.text())
        self._config.set("ffmpeg", "ffmpeg_path", self._ffmpeg_path_edit.text())
        self._config.set("ffmpeg", "ffprobe_path", self._ffprobe_path_edit.text())
        self._config.set("ffmpeg", "auto_detect_ffmpeg", self._auto_detect_ffmpeg.isChecked())
        self._config.set("advanced", "max_concurrent_tasks", self._max_concurrent_spin.value())
        self._config.set("basic", "auto_open_output", self._auto_open_output.isChecked())
        self._config.set("interface", "show_notification", self._show_notification.isChecked())
        self._config.set("advanced", "confirm_overwrite", self._confirm_overwrite.isChecked())
        self._config.set("advanced", "temp_dir", self._temp_dir_edit.text())
        self._config.set("advanced", "keep_temp_files", self._keep_temp_files.isChecked())
        self._config.set("advanced", "enable_debug_logging", self._enable_debug_logging.isChecked())
        
        self.settings_changed.emit()
        logger.info("设置已保存")
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "保存成功", "设置已保存！")
    
    def _reset_settings(self):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "恢复默认设置",
            "确定要恢复所有设置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._theme_combo.setCurrentIndex(0)
            self._log_level_combo.setCurrentIndex(1)
            self._default_output_dir_edit.clear()
            self._ffmpeg_path_edit.clear()
            self._ffprobe_path_edit.clear()
            self._auto_detect_ffmpeg.setChecked(True)
            self._max_concurrent_spin.setValue(1)
            self._auto_open_output.setChecked(True)
            self._show_notification.setChecked(True)
            self._confirm_overwrite.setChecked(True)
            self._temp_dir_edit.clear()
            self._keep_temp_files.setChecked(False)
            self._enable_debug_logging.setChecked(False)
            logger.info("设置已恢复为默认值")
    
    def _browse_default_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择默认输出目录")
        if dir_path:
            self._default_output_dir_edit.setText(dir_path)
    
    def _browse_ffmpeg_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 FFmpeg 可执行文件", "",
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if file_path:
            self._ffmpeg_path_edit.setText(file_path)
    
    def _browse_ffprobe_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 FFprobe 可执行文件", "",
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if file_path:
            self._ffprobe_path_edit.setText(file_path)
