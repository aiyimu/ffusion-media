from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox, QLineEdit, 
    QFileDialog, QGroupBox, QSplitter, QFormLayout,
    QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.utils.logger import get_logger
from src.modules import get_module_manager
from src.gui.widgets import (
    FileUploadWidget,
    ProgressWidget,
    TimelineWidget,
    VideoPreviewWidget,
    ParamPanel
)


logger = get_logger(__name__)


class VideoCutterPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._module = None
        self._init_module()
        self._setup_ui()
        self._connect_signals()
    
    def _init_module(self):
        manager = get_module_manager()
        self._module = manager.get_module("视频剪切")
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("视频剪切")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("精确剪切视频片段，支持关键帧对齐和毫秒级精度")
        desc.setStyleSheet("font-size: 14px; opacity: 0.7;")
        layout.addWidget(desc)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        
        file_group = QGroupBox("📂 导入文件")
        file_layout = QVBoxLayout(file_group)
        self._file_upload = FileUploadWidget()
        file_layout.addWidget(self._file_upload)
        left_layout.addWidget(file_group)
        
        params_panel = ParamPanel()
        
        mode_group = QGroupBox("⚙️ 剪切模式")
        mode_layout = QFormLayout(mode_group)
        
        self._cut_mode_combo = QComboBox()
        self._cut_mode_combo.addItem("无损剪切（关键帧对齐）", "lossless")
        self._cut_mode_combo.addItem("精准剪切（重新编码）", "accurate")
        mode_layout.addRow("剪切模式:", self._cut_mode_combo)
        
        self._time_mode_combo = QComboBox()
        self._time_mode_combo.addItem("开始/结束时间", "start_end")
        self._time_mode_combo.addItem("开始/时长", "start_duration")
        mode_layout.addRow("时间模式:", self._time_mode_combo)
        
        params_panel.add_basic_widget(mode_group)
        
        output_group = QGroupBox("📤 输出设置")
        output_layout = QFormLayout(output_group)
        
        self._output_format_combo = QComboBox()
        formats = self._module.SUPPORTED_OUTPUT_FORMATS if self._module else [".mp4", ".mkv", ".avi", ".mov"]
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
        
        params_panel.add_basic_widget(output_group)
        left_layout.addWidget(params_panel, 1)
        
        splitter.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        preview_group = QGroupBox("🎬 预览与剪切")
        preview_layout = QVBoxLayout(preview_group)
        
        self._preview = VideoPreviewWidget()
        preview_layout.addWidget(self._preview)
        
        self._timeline = TimelineWidget()
        self._timeline.range_changed.connect(self._on_range_changed)
        preview_layout.addWidget(self._timeline)
        
        right_layout.addWidget(preview_group, 1)
        
        control_layout = QHBoxLayout()
        
        self._execute_btn = QPushButton("▶️ 开始剪切")
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
        
        right_layout.addLayout(control_layout)
        right_layout.addWidget(self._progress)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 550])
        
        layout.addWidget(splitter, 1)
    
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
    
    def _on_range_changed(self, start: float, end: float):
        logger.debug(f"时间范围变更: {start} - {end}")
    
    def _on_execute(self):
        if not self._module:
            return
        
        files = self._file_upload.get_files()
        if not files:
            return
        
        start, end = self._timeline.get_range()
        
        params = self._module.get_default_params()
        params["input_files"] = files
        params["output_dir"] = self._output_dir_edit.text()
        params["output_format"] = self._output_format_combo.currentData()
        params["cut_mode"] = self._cut_mode_combo.currentData()
        params["time_mode"] = self._time_mode_combo.currentData()
        
        if self._time_mode_combo.currentData() == "start_end":
            params["start_time"] = str(start)
            params["end_time"] = str(end)
        else:
            params["start_time"] = str(start)
            params["duration"] = str(end - start)
        
        params["use_keyframe_align"] = self._cut_mode_combo.currentData() == "lossless"
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
                self._progress.set_status("剪切完成！")
                self._progress.set_progress(100.0)
            else:
                self._progress.set_status("剪切失败")
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
