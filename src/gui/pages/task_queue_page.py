from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QCheckBox, QSplitter,
    QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.utils.logger import get_logger
from src.gui.widgets import (
    TaskListWidget,
    TaskStatus,
    TASK_STATUS_TEXT
)


logger = get_logger(__name__)


class TaskQueuePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("任务队列")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("管理所有媒体处理任务，查看状态、进度和日志")
        desc.setStyleSheet("font-size: 14px; opacity: 0.7;")
        layout.addWidget(desc)
        
        splitter = QSplitter(Qt.Vertical)
        
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        filter_group = QGroupBox("🔍 筛选与操作")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("状态筛选:"))
        
        self._status_filter_combo = QComboBox()
        self._status_filter_combo.addItem("全部任务", "all")
        self._status_filter_combo.addItem("等待中", TaskStatus.PENDING)
        self._status_filter_combo.addItem("处理中", TaskStatus.RUNNING)
        self._status_filter_combo.addItem("已暂停", TaskStatus.PAUSED)
        self._status_filter_combo.addItem("已完成", TaskStatus.COMPLETED)
        self._status_filter_combo.addItem("失败", TaskStatus.FAILED)
        self._status_filter_combo.addItem("已取消", TaskStatus.CANCELLED)
        filter_layout.addWidget(self._status_filter_combo)
        
        filter_layout.addStretch()
        
        self._pause_all_btn = QPushButton("⏸️ 暂停全部")
        self._pause_all_btn.setCursor(Qt.PointingHandCursor)
        
        self._resume_all_btn = QPushButton("▶️ 继续全部")
        self._resume_all_btn.setCursor(Qt.PointingHandCursor)
        
        self._cancel_all_btn = QPushButton("⛔ 取消全部")
        self._cancel_all_btn.setCursor(Qt.PointingHandCursor)
        
        self._clear_completed_btn = QPushButton("🗑️ 清除已完成")
        self._clear_completed_btn.setCursor(Qt.PointingHandCursor)
        
        filter_layout.addWidget(self._pause_all_btn)
        filter_layout.addWidget(self._resume_all_btn)
        filter_layout.addWidget(self._cancel_all_btn)
        filter_layout.addWidget(self._clear_completed_btn)
        
        top_layout.addWidget(filter_group)
        
        self._task_list = TaskListWidget()
        top_layout.addWidget(self._task_list, 1)
        
        splitter.addWidget(top_panel)
        
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        logs_group = QGroupBox("📋 任务日志")
        logs_layout = QVBoxLayout(logs_group)
        
        self._logs_text = QTextEdit()
        self._logs_text.setReadOnly(True)
        self._logs_text.setMaximumHeight(200)
        self._logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a15;
                color: #0f0;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        self._logs_text.append("等待选择任务...")
        
        logs_layout.addWidget(self._logs_text)
        
        bottom_layout.addWidget(logs_group)
        splitter.addWidget(bottom_panel)
        
        splitter.setSizes([600, 200])
        layout.addWidget(splitter, 1)
    
    def _connect_signals(self):
        self._task_list.task_paused.connect(self._on_task_paused)
        self._task_list.task_resumed.connect(self._on_task_resumed)
        self._task_list.task_cancelled.connect(self._on_task_cancelled)
        self._task_list.task_logs_requested.connect(self._on_task_logs_requested)
        self._task_list.task_output_requested.connect(self._on_task_output_requested)
        
        self._pause_all_btn.clicked.connect(self._on_pause_all)
        self._resume_all_btn.clicked.connect(self._on_resume_all)
        self._cancel_all_btn.clicked.connect(self._on_cancel_all)
        self._clear_completed_btn.clicked.connect(self._on_clear_completed)
        
        self._status_filter_combo.currentIndexChanged.connect(self._on_filter_changed)
    
    def add_task(self, task_id: str, task_name: str, input_file: str):
        self._task_list.add_task(task_id, task_name, input_file)
        logger.debug(f"添加任务到队列: {task_id} - {task_name}")
    
    def update_task_status(self, task_id: str, status: str):
        self._task_list.update_task_status(task_id, status)
    
    def update_task_progress(self, task_id: str, progress: float):
        self._task_list.update_task_progress(task_id, progress)
    
    def remove_task(self, task_id: str):
        self._task_list.remove_task(task_id)
    
    def _on_task_paused(self, task_id: str):
        logger.debug(f"暂停任务: {task_id}")
    
    def _on_task_resumed(self, task_id: str):
        logger.debug(f"继续任务: {task_id}")
    
    def _on_task_cancelled(self, task_id: str):
        logger.debug(f"取消任务: {task_id}")
    
    def _on_task_logs_requested(self, task_id: str):
        self._logs_text.clear()
        self._logs_text.append(f"=== 任务 {task_id} 日志 ===")
        self._logs_text.append("日志功能开发中...")
        logger.debug(f"请求任务日志: {task_id}")
    
    def _on_task_output_requested(self, task_id: str):
        logger.debug(f"请求任务输出目录: {task_id}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "输出目录", "输出目录功能开发中...")
    
    def _on_pause_all(self):
        logger.debug("暂停全部任务")
    
    def _on_resume_all(self):
        logger.debug("继续全部任务")
    
    def _on_cancel_all(self):
        logger.debug("取消全部任务")
    
    def _on_clear_completed(self):
        logger.debug("清除已完成任务")
    
    def _on_filter_changed(self, index: int):
        filter_value = self._status_filter_combo.currentData()
        logger.debug(f"筛选变更: {filter_value}")
