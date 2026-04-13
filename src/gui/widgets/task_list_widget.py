from typing import List, Optional, Dict, Any
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, 
    QProgressBar, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont

from src.utils.logger import get_logger


logger = get_logger(__name__)


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TASK_STATUS_TEXT = {
    TaskStatus.PENDING: "⏳ 等待中",
    TaskStatus.RUNNING: "🔄 处理中",
    TaskStatus.PAUSED: "⏸️ 已暂停",
    TaskStatus.COMPLETED: "✅ 已完成",
    TaskStatus.FAILED: "❌ 失败",
    TaskStatus.CANCELLED: "⛔ 已取消"
}


class TaskItemWidget(QWidget):
    task_paused = Signal(str)
    task_resumed = Signal(str)
    task_cancelled = Signal(str)
    task_logs_requested = Signal(str)
    task_output_requested = Signal(str)
    
    def __init__(self, task_id: str, task_name: str, input_file: str, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.task_name = task_name
        self.input_file = input_file
        self._status = TaskStatus.PENDING
        self._progress = 0.0
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedHeight(80)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        icon_label = QLabel("📋")
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(self.task_name)
        name_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        
        file_label = QLabel(Path(self.input_file).name)
        file_label.setStyleSheet("font-size: 11px; opacity: 0.7;")
        
        self._status_label = QLabel(TASK_STATUS_TEXT[self._status])
        self._status_label.setStyleSheet("font-size: 12px;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(file_label)
        info_layout.addWidget(self._status_label)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(4)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximum(1000)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a4a;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #e94560;
                border-radius: 3px;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        
        self._pause_btn = QPushButton("⏸️")
        self._pause_btn.setFixedSize(32, 28)
        self._pause_btn.setCursor(Qt.PointingHandCursor)
        self._pause_btn.clicked.connect(lambda: self._toggle_pause())
        
        log_btn = QPushButton("📋")
        log_btn.setFixedSize(32, 28)
        log_btn.setCursor(Qt.PointingHandCursor)
        log_btn.clicked.connect(lambda: self.task_logs_requested.emit(self.task_id))
        
        folder_btn = QPushButton("📂")
        folder_btn.setFixedSize(32, 28)
        folder_btn.setCursor(Qt.PointingHandCursor)
        folder_btn.clicked.connect(lambda: self.task_output_requested.emit(self.task_id))
        
        cancel_btn = QPushButton("⛔")
        cancel_btn.setFixedSize(32, 28)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(lambda: self.task_cancelled.emit(self.task_id))
        
        btn_layout.addWidget(self._pause_btn)
        btn_layout.addWidget(log_btn)
        btn_layout.addWidget(folder_btn)
        btn_layout.addWidget(cancel_btn)
        
        right_layout.addWidget(self._progress_bar)
        right_layout.addLayout(btn_layout)
        
        layout.addWidget(icon_label)
        layout.addLayout(info_layout, 1)
        layout.addLayout(right_layout)
    
    def set_status(self, status: str):
        self._status = status
        self._status_label.setText(TASK_STATUS_TEXT.get(status, status))
        
        if status == TaskStatus.RUNNING:
            self._pause_btn.setVisible(True)
        else:
            self._pause_btn.setVisible(False)
    
    def set_progress(self, progress: float):
        self._progress = progress
        value = int(progress * 10)
        self._progress_bar.setValue(value)
    
    def _toggle_pause(self):
        if self._status == TaskStatus.RUNNING:
            self.task_paused.emit(self.task_id)
        elif self._status == TaskStatus.PAUSED:
            self.task_resumed.emit(self.task_id)


class TaskListWidget(QWidget):
    task_paused = Signal(str)
    task_resumed = Signal(str)
    task_cancelled = Signal(str)
    task_logs_requested = Signal(str)
    task_output_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: Dict[str, TaskItemWidget] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QWidget()
        header.setFixedHeight(50)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel("任务列表")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        
        self._count_label = QLabel("0 个任务")
        self._count_label.setStyleSheet("font-size: 13px; opacity: 0.7;")
        
        clear_btn = QPushButton("🗑️ 清除已完成")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_completed)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self._count_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        
        layout.addWidget(header)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)
        
        self._task_list = QListWidget()
        self._task_list.setFrameShape(QFrame.NoFrame)
        self._task_list.setSpacing(8)
        layout.addWidget(self._task_list, 1)
    
    def add_task(self, task_id: str, task_name: str, input_file: str):
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 90))
        
        task_widget = TaskItemWidget(task_id, task_name, input_file)
        task_widget.task_paused.connect(self.task_paused.emit)
        task_widget.task_resumed.connect(self.task_resumed.emit)
        task_widget.task_cancelled.connect(self.task_cancelled.emit)
        task_widget.task_logs_requested.connect(self.task_logs_requested.emit)
        task_widget.task_output_requested.connect(self.task_output_requested.emit)
        
        self._task_list.addItem(item)
        self._task_list.setItemWidget(item, task_widget)
        self._tasks[task_id] = task_widget
        
        self._update_count()
        logger.debug(f"添加任务: {task_id} - {task_name}")
    
    def update_task_status(self, task_id: str, status: str):
        if task_id in self._tasks:
            self._tasks[task_id].set_status(status)
    
    def update_task_progress(self, task_id: str, progress: float):
        if task_id in self._tasks:
            self._tasks[task_id].set_progress(progress)
    
    def remove_task(self, task_id: str):
        if task_id in self._tasks:
            for i in range(self._task_list.count()):
                item = self._task_list.item(i)
                widget = self._task_list.itemWidget(item)
                if widget and widget.task_id == task_id:
                    self._task_list.takeItem(i)
                    break
            del self._tasks[task_id]
            self._update_count()
    
    def _clear_completed(self):
        to_remove = [
            task_id for task_id, widget in self._tasks.items()
            if widget._status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in to_remove:
            self.remove_task(task_id)
        
        logger.debug(f"清除了 {len(to_remove)} 个已完成/失败的任务")
    
    def _update_count(self):
        count = len(self._tasks)
        self._count_label.setText(f"{count} 个任务")
