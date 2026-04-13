from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox, QLineEdit, 
    QFileDialog, QGroupBox, QSplitter, QFormLayout,
    QTabWidget, QSlider, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.utils.logger import get_logger
from src.modules import get_module_manager
from src.gui.widgets import (
    FileUploadWidget,
    ProgressWidget,
    ParamPanel
)


logger = get_logger(__name__)


class AudioProcessorPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._module = None
        self._init_module()
        self._setup_ui()
        self._connect_signals()
    
    def _init_module(self):
        manager = get_module_manager()
        self._module = manager.get_module("音频处理")
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("音频处理")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("音频全量处理：提取、转换、剪切、音量、声道、降噪")
        desc.setStyleSheet("font-size: 14px; opacity: 0.7;")
        layout.addWidget(desc)
        
        splitter = QSplitter(Qt.Vertical)
        
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        file_group = QGroupBox("📂 导入文件")
        file_layout = QVBoxLayout(file_group)
        self._file_upload = FileUploadWidget()
        file_layout.addWidget(self._file_upload)
        top_layout.addWidget(file_group)
        
        self._tab_widget = QTabWidget()
        
        extract_tab = self._create_extract_tab()
        self._tab_widget.addTab(extract_tab, "📤 提取音频")
        
        convert_tab = self._create_convert_tab()
        self._tab_widget.addTab(convert_tab, "🔄 格式转换")
        
        cut_tab = self._create_cut_tab()
        self._tab_widget.addTab(cut_tab, "✂️ 音频剪切")
        
        volume_tab = self._create_volume_tab()
        self._tab_widget.addTab(volume_tab, "🔊 音量调整")
        
        channel_tab = self._create_channel_tab()
        self._tab_widget.addTab(channel_tab, "🎵 声道处理")
        
        denoise_tab = self._create_denoise_tab()
        self._tab_widget.addTab(denoise_tab, "🔇 音频降噪")
        
        top_layout.addWidget(self._tab_widget, 1)
        splitter.addWidget(top_panel)
        
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        output_group = QGroupBox("📤 输出设置")
        output_layout = QFormLayout(output_group)
        
        self._output_format_combo = QComboBox()
        formats = self._module.SUPPORTED_OUTPUT_FORMATS if self._module else [".mp3", ".wav", ".flac", ".aac"]
        for fmt in formats:
            self._output_format_combo.addItem(fmt.upper()[1:], fmt)
        output_layout.addRow("输出格式:", self._output_format_combo)
        
        output_dir_layout = QHBoxLayout()
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.setReadOnly(True)
        self._browse_output_btn = QPushButton("📂 选择目录")
        self._browse_output_btn.clicked.connect(self._browse_output_dir)
        output_dir_layout.addWidget(self._output_dir_edit)
        output_dir_layout.addWidget(self._browse_output_btn)
        output_layout.addRow("输出目录:", output_dir_layout)
        
        bottom_layout.addWidget(output_group)
        
        control_layout = QHBoxLayout()
        
        self._execute_btn = QPushButton("▶️ 开始处理")
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
        """)
        self._execute_btn.clicked.connect(self._on_execute)
        
        self._cancel_btn = QPushButton("⛔ 取消")
        self._cancel_btn.setMinimumHeight(45)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        
        control_layout.addWidget(self._execute_btn, 2)
        control_layout.addWidget(self._cancel_btn, 1)
        
        self._progress = ProgressWidget()
        self._progress.cancelled.connect(self._on_cancel)
        
        bottom_layout.addLayout(control_layout)
        bottom_layout.addWidget(self._progress)
        splitter.addWidget(bottom_panel)
        
        splitter.setSizes([650, 350])
        layout.addWidget(splitter, 1)
    
    def _create_extract_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addStretch()
        
        label = QLabel("从视频中提取音频")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; opacity: 0.6;")
        layout.addWidget(label)
        layout.addStretch()
        
        return tab
    
    def _create_convert_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addStretch()
        
        label = QLabel("音频格式转换")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; opacity: 0.6;")
        layout.addWidget(label)
        layout.addStretch()
        
        return tab
    
    def _create_cut_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addStretch()
        
        label = QLabel("音频剪切（开发中）")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; opacity: 0.6;")
        layout.addWidget(label)
        layout.addStretch()
        
        return tab
    
    def _create_volume_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 200)
        self._volume_slider.setValue(100)
        self._volume_spin = QSpinBox()
        self._volume_spin.setRange(0, 200)
        self._volume_spin.setValue(100)
        self._volume_spin.setSuffix(" %")
        self._volume_slider.valueChanged.connect(self._volume_spin.setValue)
        self._volume_spin.valueChanged.connect(self._volume_slider.setValue)
        
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self._volume_slider, 1)
        volume_layout.addWidget(self._volume_spin)
        
        layout.addRow("音量:", volume_layout)
        layout.addRow(QLabel(""))
        
        return tab
    
    def _create_channel_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        self._channel_mode_combo = QComboBox()
        self._channel_mode_combo.addItem("保持原样", "stereo")
        self._channel_mode_combo.addItem("立体声转单声道", "mono")
        self._channel_mode_combo.addItem("仅左声道", "left")
        self._channel_mode_combo.addItem("仅右声道", "right")
        self._channel_mode_combo.addItem("交换声道", "swap")
        layout.addRow("声道模式:", self._channel_mode_combo)
        
        return tab
    
    def _create_denoise_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        self._denoise_strength_slider = QSlider(Qt.Horizontal)
        self._denoise_strength_slider.setRange(0, 100)
        self._denoise_strength_slider.setValue(50)
        self._denoise_strength_spin = QDoubleSpinBox()
        self._denoise_strength_spin.setRange(0.0, 1.0)
        self._denoise_strength_spin.setSingleStep(0.1)
        self._denoise_strength_spin.setValue(0.5)
        self._denoise_strength_spin.setDecimals(2)
        self._denoise_strength_slider.valueChanged.connect(
            lambda v: self._denoise_strength_spin.setValue(v / 100.0)
        )
        self._denoise_strength_spin.valueChanged.connect(
            lambda v: self._denoise_strength_slider.setValue(int(v * 100))
        )
        
        denoise_layout = QHBoxLayout()
        denoise_layout.addWidget(self._denoise_strength_slider, 1)
        denoise_layout.addWidget(self._denoise_strength_spin)
        
        layout.addRow("降噪强度:", denoise_layout)
        
        return tab
    
    def _connect_signals(self):
        self._file_upload.files_changed.connect(self._on_files_changed)
    
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
        
        current_tab = self._tab_widget.currentIndex()
        process_modes = ["extract", "convert", "cut", "volume", "channel", "denoise"]
        process_mode = process_modes[current_tab] if current_tab < len(process_modes) else "extract"
        
        params = self._module.get_default_params()
        params["input_files"] = files
        params["output_dir"] = self._output_dir_edit.text()
        params["output_format"] = self._output_format_combo.currentData()
        params["process_mode"] = process_mode
        
        if process_mode == "volume":
            params["volume_percent"] = self._volume_spin.value()
        elif process_mode == "channel":
            params["channel_mode"] = self._channel_mode_combo.currentData()
        elif process_mode == "denoise":
            params["denoise_strength"] = self._denoise_strength_spin.value()
        
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
                self._progress.set_status("处理完成！")
                self._progress.set_progress(100.0)
            else:
                self._progress.set_status("处理失败")
        except Exception as e:
            logger.error(f"执行失败: {e}")
            self._progress.set_status(f"错误: {str(e)}")
        
        self._execute_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
    
    def _on_cancel(self):
        if self._module:
            self._module.cancel()
        self._progress.set_status("已取消")
    
    def _on_progress(self, progress: float, message: str = ""):
        self._progress.set_progress(progress, message)
    
    def _on_status(self, status: str):
        self._progress.set_status(status)
