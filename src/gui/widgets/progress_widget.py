from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.utils.logger import get_logger


logger = get_logger(__name__)


class ProgressWidget(QWidget):
    paused = Signal()
    resumed = Signal()
    cancelled = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_paused = False
        self._setup_ui()
    
    def _setup_ui(self):
        self.setMinimumHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        status_layout = QHBoxLayout()
        
        self._status_label = QLabel("准备就绪")
        self._status_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        
        self._progress_percent = QLabel("0%")
        self._progress_percent.setStyleSheet("font-size: 18px; font-weight: bold; color: #e94560;")
        
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        status_layout.addWidget(self._progress_percent)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximum(1000)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(8)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a4a;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #e94560;
                border-radius: 4px;
            }
        """)
        
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        
        speed_layout = QVBoxLayout()
        speed_label = QLabel("处理速度")
        speed_label.setStyleSheet("font-size: 11px; opacity: 0.6;")
        self._speed_value = QLabel("-")
        self._speed_value.setStyleSheet("font-size: 13px; font-weight: 500;")
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self._speed_value)
        
        remaining_layout = QVBoxLayout()
        remaining_label = QLabel("剩余时间")
        remaining_label.setStyleSheet("font-size: 11px; opacity: 0.6;")
        self._remaining_value = QLabel("-")
        self._remaining_value.setStyleSheet("font-size: 13px; font-weight: 500;")
        remaining_layout.addWidget(remaining_label)
        remaining_layout.addWidget(self._remaining_value)
        
        elapsed_layout = QVBoxLayout()
        elapsed_label = QLabel("已用时间")
        elapsed_label.setStyleSheet("font-size: 11px; opacity: 0.6;")
        self._elapsed_value = QLabel("-")
        self._elapsed_value.setStyleSheet("font-size: 13px; font-weight: 500;")
        elapsed_layout.addWidget(elapsed_label)
        elapsed_layout.addWidget(self._elapsed_value)
        
        info_layout.addLayout(speed_layout)
        info_layout.addLayout(remaining_layout)
        info_layout.addLayout(elapsed_layout)
        info_layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        self._pause_btn = QPushButton("⏸️ 暂停")
        self._pause_btn.setFixedHeight(36)
        self._pause_btn.setCursor(Qt.PointingHandCursor)
        self._pause_btn.clicked.connect(self._toggle_pause)
        
        self._cancel_btn = QPushButton("⛔ 取消")
        self._cancel_btn.setFixedHeight(36)
        self._cancel_btn.setCursor(Qt.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.cancelled.emit)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self._pause_btn)
        btn_layout.addWidget(self._cancel_btn)
        
        layout.addLayout(status_layout)
        layout.addWidget(self._progress_bar)
        layout.addLayout(info_layout)
        layout.addLayout(btn_layout)
    
    def set_status(self, status: str):
        self._status_label.setText(status)
        logger.debug(f"进度状态: {status}")
    
    def set_progress(self, progress: float, message: str = ""):
        value = int(progress * 10)
        self._progress_bar.setValue(value)
        self._progress_percent.setText(f"{progress:.1f}%")
        if message:
            self.set_status(message)
    
    def set_speed(self, speed: str):
        self._speed_value.setText(speed)
    
    def set_remaining_time(self, time_str: str):
        self._remaining_value.setText(time_str)
    
    def set_elapsed_time(self, time_str: str):
        self._elapsed_value.setText(time_str)
    
    def reset(self):
        self._is_paused = False
        self._status_label.setText("准备就绪")
        self._progress_bar.setValue(0)
        self._progress_percent.setText("0%")
        self._speed_value.setText("-")
        self._remaining_value.setText("-")
        self._elapsed_value.setText("-")
        self._pause_btn.setText("⏸️ 暂停")
    
    def _toggle_pause(self):
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_btn.setText("▶️ 继续")
            self.paused.emit()
        else:
            self._pause_btn.setText("⏸️ 暂停")
            self.resumed.emit()
