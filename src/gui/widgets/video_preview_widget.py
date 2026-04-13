from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSlider, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QImage, QFont, QPainter

from src.utils.logger import get_logger


logger = get_logger(__name__)


class VideoPreviewWidget(QWidget):
    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    seek_to = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = False
        self._duration = 0.0
        self._current_time = 0.0
        self._thumbnail: Optional[QPixmap] = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._preview_area = VideoPreviewArea()
        self._preview_area.setMinimumSize(400, 250)
        self._preview_area.setStyleSheet("""
            QWidget {
                background-color: #0a0a15;
                border: 2px dashed #333;
                border-radius: 8px;
            }
        """)
        
        layout.addWidget(self._preview_area, 1)
        
        controls = QWidget()
        controls.setFixedHeight(60)
        controls.setStyleSheet("background-color: #16213e;")
        
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(15, 10, 15, 10)
        controls_layout.setSpacing(12)
        
        self._play_btn = QPushButton("▶️")
        self._play_btn.setFixedSize(40, 40)
        self._play_btn.setCursor(Qt.PointingHandCursor)
        self._play_btn.clicked.connect(self._toggle_play)
        
        self._stop_btn = QPushButton("⏹️")
        self._stop_btn.setFixedSize(40, 40)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.clicked.connect(self._stop)
        
        self._time_label = QLabel("00:00:00 / 00:00:00")
        self._time_label.setStyleSheet("font-size: 12px; font-family: monospace;")
        
        self._seek_slider = QSlider(Qt.Horizontal)
        self._seek_slider.setMinimum(0)
        self._seek_slider.setMaximum(1000)
        self._seek_slider.setValue(0)
        self._seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self._seek_slider.sliderReleased.connect(self._on_seek_released)
        self._seek_slider.sliderMoved.connect(self._on_seek_moved)
        
        load_btn = QPushButton("📂 加载")
        load_btn.setFixedHeight(36)
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._load_video)
        
        controls_layout.addWidget(self._play_btn)
        controls_layout.addWidget(self._stop_btn)
        controls_layout.addWidget(self._time_label)
        controls_layout.addWidget(self._seek_slider, 1)
        controls_layout.addWidget(load_btn)
        
        layout.addWidget(controls)
    
    def set_duration(self, duration: float):
        self._duration = duration
        self._seek_slider.setMaximum(int(duration * 1000))
        self._update_time_label()
    
    def set_current_time(self, time: float):
        self._current_time = max(0.0, min(self._duration, time))
        self._seek_slider.setValue(int(self._current_time * 1000))
        self._update_time_label()
    
    def set_thumbnail(self, pixmap: QPixmap):
        self._thumbnail = pixmap
        self._preview_area.set_thumbnail(pixmap)
    
    def set_playing(self, playing: bool):
        self._is_playing = playing
        self._play_btn.setText("⏸️" if playing else "▶️")
    
    def _toggle_play(self):
        if self._is_playing:
            self.pause_clicked.emit()
        else:
            self.play_clicked.emit()
    
    def _stop(self):
        self.stop_clicked.emit()
        self.set_playing(False)
        self.set_current_time(0.0)
    
    def _on_seek_pressed(self):
        pass
    
    def _on_seek_released(self):
        time = self._seek_slider.value() / 1000.0
        self.seek_to.emit(time)
    
    def _on_seek_moved(self, value: int):
        time = value / 1000.0
        self._current_time = time
        self._update_time_label()
    
    def _update_time_label(self):
        current = self._format_time(self._current_time)
        total = self._format_time(self._duration)
        self._time_label.setText(f"{current} / {total}")
    
    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.mkv *.avi *.mov);;所有文件 (*.*)"
        )
        
        if file_path:
            logger.info(f"加载视频: {file_path}")
            self.set_thumbnail(QPixmap())


class VideoPreviewArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thumbnail: Optional[QPixmap] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._placeholder = QLabel("🖼️\n视频预览区域")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("""
            QLabel {
                border: none;
                font-size: 14px;
                opacity: 0.5;
            }
        """)
        
        layout.addWidget(self._placeholder)
    
    def set_thumbnail(self, pixmap: QPixmap):
        self._thumbnail = pixmap
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self._thumbnail and not self._thumbnail.isNull():
            scaled = self._thumbnail.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            super().paintEvent(event)
