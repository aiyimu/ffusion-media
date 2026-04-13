from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox, QSpinBox, 
    QLineEdit, QFileDialog, QGroupBox, QSplitter,
    QFormLayout, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.utils.logger import get_logger
from src.modules import get_module_manager
from src.gui.widgets import (
    FileUploadWidget,
    ProgressWidget,
    CollapsiblePanel,
    ParamPanel
)


logger = get_logger(__name__)


class FormatConverterPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._module = None
        self._init_module()
        self._setup_ui()
        self._connect_signals()
    
    def _init_module(self):
        manager = get_module_manager()
        self._module = manager.get_module("格式转换")
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("格式转换")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("批量转换音视频格式，支持流复制快速转换")
        desc.setStyleSheet("font-size: 14px; opacity: 0.7;")
        layout.addWidget(desc)
        
        splitter = QSplitter(Qt.Vertical)
        
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(15)
        
        file_group = QGroupBox("📂 导入文件")
        file_layout = QVBoxLayout(file_group)
        self._file_upload = FileUploadWidget()
        file_layout.addWidget(self._file_upload)
        top_layout.addWidget(file_group)
        
        params_panel = ParamPanel()
        
        output_group = QGroupBox("⚙️ 输出设置")
        output_layout = QFormLayout(output_group)
        
        self._output_format_combo = QComboBox()
        formats = self._module.SUPPORTED_OUTPUT_FORMATS if self._module else [".mp4", ".mkv", ".avi", ".mov"]
        for fmt in formats:
            self._output_format_combo.addItem(fmt.upper()[1:], fmt)
        output_layout.addRow("输出格式:", self._output_format_combo)
        
        self._use_stream_copy = QCheckBox("流复制（快速转换，不重新编码）")
        self._use_stream_copy.setChecked(True)
        self._use_stream_copy.toggled.connect(self._on_stream_copy_toggled)
        output_layout.addRow("", self._use_stream_copy)
        
        output_dir_layout = QHBoxLayout()
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.setReadOnly(True)
        self._browse_output_btn = QPushButton("📂 选择目录")
        self._browse_output_btn.clicked.connect(self._browse_output_dir)
        output_dir_layout.addWidget(self._output_dir_edit)
        output_dir_layout.addWidget(self._browse_output_btn)
        output_layout.addRow("输出目录:", output_dir_layout)
        
        params_panel.add_basic_widget(output_group)
        
        encoding_group = QGroupBox("🎬 编码设置")
        encoding_layout = QFormLayout(encoding_group)
        
        self._video_encoder_combo = QComboBox()
        video_encoders = ["libx264", "libx265", "libvpx", "libaom-av1", "copy"]
        for enc in video_encoders:
            self._video_encoder_combo.addItem(enc)
        encoding_layout.addRow("视频编码器:", self._video_encoder_combo)
        
        self._audio_encoder_combo = QComboBox()
        audio_encoders = ["aac", "mp3", "flac", "opus", "copy"]
        for enc in audio_encoders:
            self._audio_encoder_combo.addItem(enc)
        encoding_layout.addRow("音频编码器:", self._audio_encoder_combo)
        
        self._width_spin = QSpinBox()
        self._width_spin.setRange(0, 7680)
        self._width_spin.setSpecialValueText("自动")
        self._width_spin.setSuffix(" px")
        encoding_layout.addRow("宽度:", self._width_spin)
        
        self._height_spin = QSpinBox()
        self._height_spin.setRange(0, 4320)
        self._height_spin.setSpecialValueText("自动")
        self._height_spin.setSuffix(" px")
        encoding_layout.addRow("高度:", self._height_spin)
        
        self._fps_spin = QDoubleSpinBox()
        self._fps_spin.setRange(0, 120)
        self._fps_spin.setSpecialValueText("自动")
        self._fps_spin.setDecimals(2)
        encoding_layout.addRow("帧率:", self._fps_spin)
        
        self._video_bitrate_edit = QLineEdit()
        self._video_bitrate_edit.setPlaceholderText("例如: 5M, 1000k")
        encoding_layout.addRow("视频码率:", self._video_bitrate_edit)
        
        self._audio_bitrate_edit = QLineEdit()
        self._audio_bitrate_edit.setPlaceholderText("例如: 192k, 320k")
        encoding_layout.addRow("音频码率:", self._audio_bitrate_edit)
        
        self._audio_channels_spin = QSpinBox()
        self._audio_channels_spin.setRange(0, 8)
        self._audio_channels_spin.setSpecialValueText("自动")
        encoding_layout.addRow("音频声道:", self._audio_channels_spin)
        
        params_panel.add_advanced_widget(encoding_group)
        
        top_layout.addWidget(params_panel)
        splitter.addWidget(top_panel)
        
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        control_layout = QHBoxLayout()
        
        self._execute_btn = QPushButton("▶️ 开始转换")
        self._execute_btn.setMinimumHeight(45)
        self._execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #ff6b81;
            }
            QPushButton:pressed {
                background-color: #c73e54;
            }
        """)
        self._execute_btn.clicked.connect(self._on_execute)
        
        self._cancel_btn = QPushButton("⛔ 取消")
        self._cancel_btn.setMinimumHeight(45)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        
        control_layout.addWidget(self._execute_btn, 2)
        control_layout.addWidget(self._cancel_btn, 1)
        
        self._progress = ProgressWidget()
        self._progress.paused.connect(self._on_pause)
        self._progress.resumed.connect(self._on_resume)
        self._progress.cancelled.connect(self._on_cancel)
        
        bottom_layout.addLayout(control_layout)
        bottom_layout.addWidget(self._progress)
        splitter.addWidget(bottom_panel)
        
        splitter.setSizes([600, 400])
        layout.addWidget(splitter, 1)
        
        self._on_stream_copy_toggled(True)
    
    def _connect_signals(self):
        self._file_upload.files_changed.connect(self._on_files_changed)
    
    def _on_stream_copy_toggled(self, checked: bool):
        self._video_encoder_combo.setEnabled(not checked)
        self._audio_encoder_combo.setEnabled(not checked)
        self._width_spin.setEnabled(not checked)
        self._height_spin.setEnabled(not checked)
        self._fps_spin.setEnabled(not checked)
        self._video_bitrate_edit.setEnabled(not checked)
        self._audio_bitrate_edit.setEnabled(not checked)
        self._audio_channels_spin.setEnabled(not checked)
        
        if checked:
            self._video_encoder_combo.setCurrentText("copy")
            self._audio_encoder_combo.setCurrentText("copy")
    
    def _browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", ""
        )
        if dir_path:
            self._output_dir_edit.setText(dir_path)
    
    def _on_files_changed(self, files: list):
        logger.debug(f"文件列表变更: {len(files)} 个文件")
    
    def _on_execute(self):
        if not self._module:
            return
        
        files = self._file_upload.get_files()
        if not files:
            return
        
        params = self._module.get_default_params()
        params["input_files"] = files
        params["output_dir"] = self._output_dir_edit.text()
        params["output_format"] = self._output_format_combo.currentData()
        params["use_stream_copy"] = self._use_stream_copy.isChecked()
        params["video_encoder"] = self._video_encoder_combo.currentText()
        params["audio_encoder"] = self._audio_encoder_combo.currentText()
        params["width"] = self._width_spin.value()
        params["height"] = self._height_spin.value()
        params["frame_rate"] = self._fps_spin.value()
        params["video_bitrate"] = self._video_bitrate_edit.text()
        params["audio_bitrate"] = self._audio_bitrate_edit.text()
        params["audio_channels"] = self._audio_channels_spin.value()
        params["overwrite"] = True
        
        self._module.set_params(params)
        self._module.set_progress_callback(self._on_progress)
        self._module.set_status_callback(self._on_status)
        
        self._execute_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._progress.reset()
        self._progress.set_status("准备中...")
        
        try:
            success = self._module.execute()
            if success:
                self._progress.set_status("转换完成！")
                self._progress.set_progress(100.0)
            else:
                self._progress.set_status("转换失败")
        except Exception as e:
            logger.error(f"执行失败: {e}")
            self._progress.set_status(f"错误: {str(e)}")
        
        self._execute_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
    
    def _on_cancel(self):
        if self._module:
            self._module.cancel()
        self._progress.set_status("已取消")
    
    def _on_pause(self):
        logger.debug("暂停执行")
    
    def _on_resume(self):
        logger.debug("继续执行")
    
    def _on_progress(self, progress: float, message: str = ""):
        self._progress.set_progress(progress, message)
    
    def _on_status(self, status: str):
        self._progress.set_status(status)
