from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QLineEdit, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QMouseEvent

from src.utils.logger import get_logger


logger = get_logger(__name__)


class TimelineWidget(QWidget):
    range_changed = Signal(float, float)
    
    def __init__(self, duration: float = 0.0, parent=None):
        super().__init__(parent)
        self._duration = duration
        self._start_time = 0.0
        self._end_time = duration
        self._setup_ui()
    
    def _setup_ui(self):
        self.setMinimumHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        time_layout = QHBoxLayout()
        
        start_layout = QVBoxLayout()
        start_layout.setSpacing(4)
        start_label = QLabel("开始时间")
        start_label.setStyleSheet("font-size: 12px; opacity: 0.7;")
        self._start_input = QLineEdit("00:00:00.000")
        self._start_input.setAlignment(Qt.AlignCenter)
        self._start_input.setFixedHeight(32)
        self._start_input.textChanged.connect(self._on_start_input_changed)
        start_layout.addWidget(start_label)
        start_layout.addWidget(self._start_input)
        
        end_layout = QVBoxLayout()
        end_layout.setSpacing(4)
        end_label = QLabel("结束时间")
        end_label.setStyleSheet("font-size: 12px; opacity: 0.7;")
        self._end_input = QLineEdit(self._format_time(self._duration))
        self._end_input.setAlignment(Qt.AlignCenter)
        self._end_input.setFixedHeight(32)
        self._end_input.textChanged.connect(self._on_end_input_changed)
        end_layout.addWidget(end_label)
        end_layout.addWidget(self._end_input)
        
        duration_label = QLabel("⏱️")
        duration_label.setAlignment(Qt.AlignCenter)
        duration_label.setStyleSheet("font-size: 20px;")
        
        time_layout.addLayout(start_layout, 1)
        time_layout.addWidget(duration_label)
        time_layout.addLayout(end_layout, 1)
        
        layout.addLayout(time_layout)
        
        timeline_container = QWidget()
        timeline_layout = QVBoxLayout(timeline_container)
        timeline_layout.setContentsMargins(0, 10, 0, 0)
        timeline_layout.setSpacing(5)
        
        self._timeline_bar = TimelineBar(self._duration, self)
        self._timeline_bar.range_changed.connect(self._on_timeline_range_changed)
        
        marks_layout = QHBoxLayout()
        marks_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(5):
            mark_time = (self._duration * i) / 4 if self._duration > 0 else 0
            mark_label = QLabel(self._format_time(mark_time))
            mark_label.setStyleSheet("font-size: 10px; opacity: 0.6;")
            mark_label.setAlignment(Qt.AlignLeft if i == 0 else Qt.AlignRight if i == 4 else Qt.AlignCenter)
            marks_layout.addWidget(mark_label, 1)
        
        timeline_layout.addWidget(self._timeline_bar)
        timeline_layout.addLayout(marks_layout)
        
        layout.addWidget(timeline_container, 1)
        
        preview_layout = QHBoxLayout()
        preview_layout.setContentsMargins(0, 5, 0, 0)
        
        self._start_preview = QLabel("首帧预览")
        self._start_preview.setAlignment(Qt.AlignCenter)
        self._start_preview.setMinimumSize(120, 80)
        self._start_preview.setObjectName("startPreview")
        
        self._end_preview = QLabel("尾帧预览")
        self._end_preview.setAlignment(Qt.AlignCenter)
        self._end_preview.setMinimumSize(120, 80)
        self._end_preview.setObjectName("endPreview")
        
        preview_layout.addWidget(self._start_preview)
        preview_layout.addStretch()
        preview_layout.addWidget(self._end_preview)
        
        layout.addLayout(preview_layout)
    
    def set_duration(self, duration: float):
        self._duration = max(0.0, duration)
        self._end_time = self._duration
        self._end_input.setText(self._format_time(self._duration))
        self._timeline_bar.set_duration(self._duration)
        logger.debug(f"时间轴时长设置: {duration}秒")
    
    def get_range(self) -> tuple[float, float]:
        return (self._start_time, self._end_time)
    
    def set_range(self, start: float, end: float):
        self._start_time = max(0.0, start)
        self._end_time = min(self._duration, end)
        if self._start_time > self._end_time:
            self._start_time, self._end_time = self._end_time, self._start_time
        
        self._start_input.setText(self._format_time(self._start_time))
        self._end_input.setText(self._format_time(self._end_time))
        self._timeline_bar.set_range(self._start_time, self._end_time)
        self.range_changed.emit(self._start_time, self._end_time)
    
    def _on_timeline_range_changed(self, start: float, end: float):
        self._start_time = start
        self._end_time = end
        self._start_input.setText(self._format_time(start))
        self._end_input.setText(self._format_time(end))
        self.range_changed.emit(start, end)
    
    def _on_start_input_changed(self):
        try:
            time_str = self._start_input.text()
            seconds = self._parse_time(time_str)
            if 0 <= seconds <= self._end_time:
                self._start_time = seconds
                self._timeline_bar.set_range(self._start_time, self._end_time)
                self.range_changed.emit(self._start_time, self._end_time)
        except:
            pass
    
    def _on_end_input_changed(self):
        try:
            time_str = self._end_input.text()
            seconds = self._parse_time(time_str)
            if self._start_time <= seconds <= self._duration:
                self._end_time = seconds
                self._timeline_bar.set_range(self._start_time, self._end_time)
                self.range_changed.emit(self._start_time, self._end_time)
        except:
            pass
    
    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"
    
    def _parse_time(self, time_str: str) -> float:
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(time_str)


class TimelineBar(QWidget):
    range_changed = Signal(float, float)
    
    def __init__(self, duration: float, parent=None):
        super().__init__(parent)
        self._duration = duration
        self._start_pos = 0.0
        self._end_pos = 1.0
        self._dragging = None
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
    
    def set_duration(self, duration: float):
        self._duration = max(0.0, duration)
        self.update()
    
    def set_range(self, start: float, end: float):
        if self._duration > 0:
            self._start_pos = start / self._duration
            self._end_pos = end / self._duration
        else:
            self._start_pos = 0.0
            self._end_pos = 1.0
        self.update()
    
    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor, QPen, QBrush
        from PySide6.QtWidgets import QStyleOption, QStyle
        from PySide6.QtGui import QPalette
        
        opt = QStyleOption()
        opt.initFrom(self)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        bg_color = opt.palette.color(QPalette.Window)
        if bg_color.lightness() > 128:
            bg_color = QColor(220, 220, 220)
        else:
            bg_color = QColor(60, 60, 80)
        
        selected_color = QColor(233, 69, 96)
        handle_color = QColor(255, 255, 255) if bg_color.lightness() <= 128 else QColor(50, 50, 50)
        
        painter.fillRect(0, 10, w, h - 20, bg_color)
        
        start_x = int(self._start_pos * w)
        end_x = int(self._end_pos * w)
        painter.fillRect(start_x, 10, end_x - start_x, h - 20, selected_color)
        
        pen = QPen(handle_color, 2)
        painter.setPen(pen)
        
        painter.drawLine(start_x, 5, start_x, h - 5)
        painter.drawLine(end_x, 5, end_x, h - 5)
        
        painter.setBrush(QBrush(handle_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(start_x - 6, h // 2 - 6, 12, 12)
        painter.drawEllipse(end_x - 6, h // 2 - 6, 12, 12)
    
    def mousePressEvent(self, event: QMouseEvent):
        w = self.width()
        x = event.position().x()
        
        start_x = self._start_pos * w
        end_x = self._end_pos * w
        
        if abs(x - start_x) < 15:
            self._dragging = "start"
        elif abs(x - end_x) < 15:
            self._dragging = "end"
        elif start_x < x < end_x:
            self._dragging = "both"
            self._drag_offset = x - start_x
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging is None:
            return
        
        w = self.width()
        x = max(0, min(w, event.position().x()))
        pos = x / w
        
        if self._dragging == "start":
            self._start_pos = min(pos, self._end_pos - 0.01)
        elif self._dragging == "end":
            self._end_pos = max(pos, self._start_pos + 0.01)
        elif self._dragging == "both":
            range_width = self._end_pos - self._start_pos
            new_start = pos - self._drag_offset / w
            new_start = max(0, min(1 - range_width, new_start))
            self._start_pos = new_start
            self._end_pos = new_start + range_width
        
        self.update()
        
        if self._duration > 0:
            self.range_changed.emit(
                self._start_pos * self._duration,
                self._end_pos * self._duration
            )
    
    def mouseReleaseEvent(self, event):
        self._dragging = None
