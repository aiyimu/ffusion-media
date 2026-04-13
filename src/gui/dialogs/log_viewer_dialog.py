from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QTextEdit, QFileDialog,
    QMessageBox, QSplitter, QGroupBox, QWidget, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from src.utils.logger import get_logger


logger = get_logger(__name__)


class LogViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_buffer = []
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        self.setWindowTitle("日志查看器")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        filter_group = QGroupBox("筛选")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("日志级别:"))
        
        self._level_combo = QComboBox()
        self._level_combo.addItem("全部", "ALL")
        self._level_combo.addItem("DEBUG", "DEBUG")
        self._level_combo.addItem("INFO", "INFO")
        self._level_combo.addItem("WARNING", "WARNING")
        self._level_combo.addItem("ERROR", "ERROR")
        self._level_combo.currentIndexChanged.connect(self._filter_logs)
        filter_layout.addWidget(self._level_combo)
        
        filter_layout.addStretch()
        
        self._auto_scroll = QCheckBox("自动滚动")
        self._auto_scroll.setChecked(True)
        filter_layout.addWidget(self._auto_scroll)
        
        layout.addWidget(filter_group)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("Consolas", 10))
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a15;
                color: #ccc;
                padding: 10px;
            }
        """)
        
        layout.addWidget(self._log_text, 1)
        
        btn_layout = QHBoxLayout()
        
        self._clear_btn = QPushButton("🗑️ 清空")
        self._clear_btn.setMinimumHeight(36)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_logs)
        
        self._export_btn = QPushButton("💾 导出")
        self._export_btn.setMinimumHeight(36)
        self._export_btn.setCursor(Qt.PointingHandCursor)
        self._export_btn.clicked.connect(self._export_logs)
        
        self._refresh_btn = QPushButton("🔄 刷新")
        self._refresh_btn.setMinimumHeight(36)
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._refresh_logs)
        
        btn_layout.addWidget(self._clear_btn)
        btn_layout.addWidget(self._export_btn)
        btn_layout.addWidget(self._refresh_btn)
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _setup_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._load_logs)
        self._timer.start(1000)
        self._load_logs()
    
    def _load_logs(self):
        log_file = Path(__file__).parent.parent.parent / ".temp" / "user_data" / "logs" / "ffusion_media.log"
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                self._log_buffer = lines
                self._filter_logs()
            except Exception as e:
                logger.error(f"加载日志失败: {e}")
    
    def _filter_logs(self):
        level = self._level_combo.currentData()
        
        if level == "ALL":
            filtered = self._log_buffer
        else:
            filtered = [
                line for line in self._log_buffer
                if f" {level}:" in line or f"[{level}]" in line
            ]
        
        self._log_text.setPlainText(''.join(filtered))
        
        if self._auto_scroll.isChecked():
            scrollbar = self._log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _clear_logs(self):
        reply = QMessageBox.question(
            self,
            "清空日志",
            "确定要清空日志显示吗？（不会删除日志文件）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._log_text.clear()
            self._log_buffer = []
    
    def _export_logs(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"ffusion_media_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._log_text.toPlainText())
                
                QMessageBox.information(self, "导出成功", f"日志已导出到:\n{file_path}")
                logger.info(f"日志导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出日志失败:\n{str(e)}")
                logger.error(f"导出日志失败: {e}")
    
    def _refresh_logs(self):
        self._load_logs()
    
    def append_log(self, message: str):
        self._log_buffer.append(message + '\n')
        self._filter_logs()
