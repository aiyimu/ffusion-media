from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QListWidget, QListWidgetItem, QFileDialog, 
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QMimeData, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from src.utils.logger import get_logger
from src.utils.validator import get_supported_media_formats


logger = get_logger(__name__)


class FileItemWidget(QWidget):
    removed = Signal(str)
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._setup_ui()
    
    def _setup_ui(self):
        self.setMinimumHeight(56)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        
        path = Path(self.file_path)
        icon_label = QLabel("📄")
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        
        name_label = QLabel(path.name)
        name_label.setStyleSheet("font-weight: 500; font-size: 13px;")
        name_label.setWordWrap(False)
        
        size_label = QLabel(self._format_size(path.stat().st_size))
        size_label.setStyleSheet("font-size: 11px; opacity: 0.6;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(size_label)
        
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(32, 32)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                border-radius: 16px;
            }
        """)
        remove_btn.clicked.connect(lambda: self.removed.emit(self.file_path))
        
        layout.addWidget(icon_label)
        layout.addLayout(info_layout, 1)
        layout.addWidget(remove_btn)
    
    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


class FileUploadWidget(QWidget):
    files_changed = Signal(list)
    
    def __init__(self, supported_formats: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self._files: List[str] = []
        self._supported_formats = supported_formats or get_supported_media_formats()
        self._setup_ui()
    
    def _setup_ui(self):
        self.setMinimumHeight(320)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)
        
        drop_area = DropAreaWidget(self._supported_formats)
        drop_area.files_dropped.connect(self._on_files_dropped)
        drop_area.clicked.connect(self._open_file_dialog)
        layout.addWidget(drop_area)
        
        list_label = QLabel("📋 文件清单")
        list_label.setStyleSheet("font-weight: 600; font-size: 14px; padding-left: 4px;")
        layout.addWidget(list_label)
        
        self._file_list = QListWidget()
        self._file_list.setFrameShape(QFrame.NoFrame)
        self._file_list.setSpacing(8)
        self._file_list.setMinimumHeight(120)
        layout.addWidget(self._file_list, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 0, 4, 0)
        btn_layout.setSpacing(12)
        
        add_btn = QPushButton("➕ 添加文件")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self._open_file_dialog)
        
        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setMinimumHeight(36)
        clear_btn.clicked.connect(self._clear_files)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
    
    def _on_files_dropped(self, files: List[str]):
        for file_path in files:
            if file_path not in self._files:
                self._add_file(file_path)
    
    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择媒体文件",
            "",
            f"媒体文件 (*{' *'.join(self._supported_formats)});;所有文件 (*.*)"
        )
        
        for file_path in files:
            if file_path not in self._files:
                self._add_file(file_path)
    
    def _add_file(self, file_path: str):
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext not in self._supported_formats:
            QMessageBox.warning(
                self,
                "不支持的格式",
                f"文件格式 {ext} 不受支持\n"
                f"支持的格式: {', '.join(self._supported_formats)}"
            )
            return
        
        self._files.append(file_path)
        
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 70))
        
        file_widget = FileItemWidget(file_path)
        file_widget.removed.connect(self._remove_file)
        
        self._file_list.addItem(item)
        self._file_list.setItemWidget(item, file_widget)
        
        self.files_changed.emit(self._files.copy())
        logger.debug(f"添加文件: {file_path}")
    
    def _remove_file(self, file_path: str):
        if file_path in self._files:
            self._files.remove(file_path)
            
            for i in range(self._file_list.count()):
                item = self._file_list.item(i)
                widget = self._file_list.itemWidget(item)
                if widget and widget.file_path == file_path:
                    self._file_list.takeItem(i)
                    break
            
            self.files_changed.emit(self._files.copy())
            logger.debug(f"移除文件: {file_path}")
    
    def _clear_files(self):
        self._files.clear()
        self._file_list.clear()
        self.files_changed.emit([])
        logger.debug("清空文件列表")
    
    def get_files(self) -> List[str]:
        return self._files.copy()
    
    def set_files(self, files: List[str]):
        self._clear_files()
        for file_path in files:
            self._add_file(file_path)


class DropAreaWidget(QWidget):
    files_dropped = Signal(list)
    clicked = Signal()
    
    def __init__(self, supported_formats: List[str], parent=None):
        super().__init__(parent)
        self._supported_formats = supported_formats
        self._setup_ui()
        self.setAcceptDrops(True)
    
    def _setup_ui(self):
        self.setMinimumHeight(100)
        self.setFixedHeight(100)
        self.setStyleSheet("""
            QWidget {
                border: 2px dashed #888;
                border-radius: 12px;
                background-color: transparent;
            }
            QWidget:hover {
                border-color: #e94560;
                background-color: rgba(233, 69, 96, 0.1);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        icon_label = QLabel("📂")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 40px; border: none;")
        
        text1 = QLabel("拖拽文件到这里，或点击选择文件")
        text1.setAlignment(Qt.AlignCenter)
        text1.setStyleSheet("font-size: 14px; font-weight: 500; border: none;")
        
        text2 = QLabel(f"支持: {', '.join(self._supported_formats[:6])}...")
        text2.setAlignment(Qt.AlignCenter)
        text2.setStyleSheet("font-size: 12px; opacity: 0.6; border: none;")
        
        layout.addStretch()
        layout.addWidget(icon_label)
        layout.addWidget(text1)
        layout.addWidget(text2)
        layout.addStretch()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in self._supported_formats:
                files.append(str(path))
        
        if files:
            self.files_dropped.emit(files)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
