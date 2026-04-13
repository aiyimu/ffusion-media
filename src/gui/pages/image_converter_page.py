from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox, QLineEdit, 
    QFileDialog, QGroupBox, QSplitter, QFormLayout,
    QTabWidget, QSpinBox, QDoubleSpinBox
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


class ImageConverterPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._module = None
        self._init_module()
        self._setup_ui()
        self._connect_signals()
    
    def _init_module(self):
        manager = get_module_manager()
        self._module = manager.get_module("图像转换")
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("图像转换")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("视频与图像互转：抽帧、合成视频、转GIF、图片转视频")
        desc.setStyleSheet("font-size: 14px; opacity: 0.7;")
        layout.addWidget(desc)
        
        splitter = QSplitter(Qt.Vertical)
        
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        self._tab_widget = QTabWidget()
        
        extract_tab = self._create_extract_frames_tab()
        self._tab_widget.addTab(extract_tab, "📸 视频抽帧")
        
        images_to_video_tab = self._create_images_to_video_tab()
        self._tab_widget.addTab(images_to_video_tab, "🎬 图片合成视频")
        
        video_to_gif_tab = self._create_video_to_gif_tab()
        self._tab_widget.addTab(video_to_gif_tab, "🎞️ 视频转GIF")
        
        image_to_video_tab = self._create_image_to_video_tab()
        self._tab_widget.addTab(image_to_video_tab, "🖼️ 图片转视频")
        
        top_layout.addWidget(self._tab_widget, 1)
        splitter.addWidget(top_panel)
        
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        file_group = QGroupBox("📂 导入文件")
        file_layout = QVBoxLayout(file_group)
        self._file_upload = FileUploadWidget()
        file_layout.addWidget(self._file_upload)
        bottom_layout.addWidget(file_group)
        
        output_group = QGroupBox("📤 输出设置")
        output_layout = QFormLayout(output_group)
        
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
        
        splitter.setSizes([550, 450])
        layout.addWidget(splitter, 1)
    
    def _create_extract_frames_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        self._extract_mode_combo = QComboBox()
        self._extract_mode_combo.addItem("按帧率", "fps")
        self._extract_mode_combo.addItem("按时间间隔", "interval")
        self._extract_mode_combo.addItem("按总帧数", "total")
        layout.addRow("抽帧模式:", self._extract_mode_combo)
        
        self._extract_fps_spin = QDoubleSpinBox()
        self._extract_fps_spin.setRange(0.01, 120.0)
        self._extract_fps_spin.setValue(1.0)
        self._extract_fps_spin.setDecimals(2)
        self._extract_fps_spin.setSuffix(" fps")
        layout.addRow("抽帧帧率:", self._extract_fps_spin)
        
        self._extract_format_combo = QComboBox()
        formats = [".jpg", ".png", ".webp"]
        for fmt in formats:
            self._extract_format_combo.addItem(fmt.upper()[1:], fmt)
        layout.addRow("输出格式:", self._extract_format_combo)
        
        self._extract_quality_spin = QSpinBox()
        self._extract_quality_spin.setRange(1, 100)
        self._extract_quality_spin.setValue(80)
        self._extract_quality_spin.setSuffix(" %")
        layout.addRow("图片质量:", self._extract_quality_spin)
        
        width_layout = QHBoxLayout()
        self._extract_width_spin = QSpinBox()
        self._extract_width_spin.setRange(0, 7680)
        self._extract_width_spin.setSpecialValueText("自动")
        self._extract_width_spin.setSuffix(" px")
        self._extract_height_spin = QSpinBox()
        self._extract_height_spin.setRange(0, 4320)
        self._extract_height_spin.setSpecialValueText("自动")
        self._extract_height_spin.setSuffix(" px")
        width_layout.addWidget(self._extract_width_spin)
        width_layout.addWidget(QLabel("×"))
        width_layout.addWidget(self._extract_height_spin)
        layout.addRow("输出尺寸:", width_layout)
        
        return tab
    
    def _create_images_to_video_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        self._images_fps_spin = QDoubleSpinBox()
        self._images_fps_spin.setRange(1, 120)
        self._images_fps_spin.setValue(30.0)
        self._images_fps_spin.setDecimals(2)
        self._images_fps_spin.setSuffix(" fps")
        layout.addRow("视频帧率:", self._images_fps_spin)
        
        return tab
    
    def _create_video_to_gif_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        self._gif_fps_spin = QSpinBox()
        self._gif_fps_spin.setRange(1, 60)
        self._gif_fps_spin.setValue(10)
        self._gif_fps_spin.setSuffix(" fps")
        layout.addRow("GIF帧率:", self._gif_fps_spin)
        
        self._gif_loop_spin = QSpinBox()
        self._gif_loop_spin.setRange(-1, 65535)
        self._gif_loop_spin.setValue(0)
        self._gif_loop_spin.setSpecialValueText("无限循环")
        layout.addRow("循环次数:", self._gif_loop_spin)
        
        self._gif_quality_spin = QSpinBox()
        self._gif_quality_spin.setRange(1, 100)
        self._gif_quality_spin.setValue(80)
        self._gif_quality_spin.setSuffix(" %")
        layout.addRow("GIF质量:", self._gif_quality_spin)
        
        return tab
    
    def _create_image_to_video_tab(self) -> QWidget:
        tab = QWidget()
        layout = QFormLayout(tab)
        
        self._image_video_duration_spin = QDoubleSpinBox()
        self._image_video_duration_spin.setRange(0.1, 3600)
        self._image_video_duration_spin.setValue(5.0)
        self._image_video_duration_spin.setDecimals(1)
        self._image_video_duration_spin.setSuffix(" 秒")
        layout.addRow("视频时长:", self._image_video_duration_spin)
        
        self._image_video_fps_spin = QDoubleSpinBox()
        self._image_video_fps_spin.setRange(1, 120)
        self._image_video_fps_spin.setValue(30.0)
        self._image_video_fps_spin.setDecimals(2)
        self._image_video_fps_spin.setSuffix(" fps")
        layout.addRow("视频帧率:", self._image_video_fps_spin)
        
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
        process_modes = ["extract_frames", "images_to_video", "video_to_gif", "image_to_video"]
        process_mode = process_modes[current_tab] if current_tab < len(process_modes) else "extract_frames"
        
        params = self._module.get_default_params()
        params["input_files"] = files
        params["output_dir"] = self._output_dir_edit.text()
        params["process_mode"] = process_mode
        
        if process_mode == "extract_frames":
            params["image_format"] = self._extract_format_combo.currentData()
            params["image_quality"] = self._extract_quality_spin.value()
            params["extract_mode"] = self._extract_mode_combo.currentData()
            if self._extract_mode_combo.currentData() == "fps":
                params["extract_fps"] = self._extract_fps_spin.value()
            params["width"] = self._extract_width_spin.value()
            params["height"] = self._extract_height_spin.value()
        
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
