from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from src.utils.logger import get_logger


logger = get_logger(__name__)


class CollapsiblePanel(QWidget):
    toggled = Signal(bool)
    
    def __init__(self, title: str, is_expanded: bool = True, parent=None):
        super().__init__(parent)
        self._title = title
        self._is_expanded = is_expanded
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QWidget()
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        header_layout.setSpacing(10)
        
        self._toggle_btn = QPushButton()
        self._toggle_btn.setFixedSize(32, 32)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(233, 69, 96, 0.1);
                border-radius: 8px;
            }
        """)
        self._toggle_btn.clicked.connect(self._toggle)
        
        title_label = QLabel(self._title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        
        header_layout.addWidget(self._toggle_btn)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)
        
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(15, 10, 15, 15)
        self._content_layout.setSpacing(12)
        
        self._content.setVisible(self._is_expanded)
        layout.addWidget(self._content)
        
        self._update_toggle_icon()
    
    def add_widget(self, widget: QWidget):
        self._content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        self._content_layout.addLayout(layout)
    
    def add_stretch(self):
        self._content_layout.addStretch()
    
    def set_expanded(self, expanded: bool):
        if expanded != self._is_expanded:
            self._toggle()
    
    def is_expanded(self) -> bool:
        return self._is_expanded
    
    def _toggle(self):
        self._is_expanded = not self._is_expanded
        self._content.setVisible(self._is_expanded)
        self._update_toggle_icon()
        self.toggled.emit(self._is_expanded)
        logger.debug(f"面板 {self._title} {'展开' if self._is_expanded else '收起'}")
    
    def _update_toggle_icon(self):
        self._toggle_btn.setText("▼" if self._is_expanded else "▶")


class ParamPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self._basic_panel = CollapsiblePanel("基础参数", True)
        self._advanced_panel = CollapsiblePanel("高级参数", False)
        
        layout.addWidget(self._basic_panel)
        layout.addWidget(self._advanced_panel)
        layout.addStretch()
    
    def add_basic_widget(self, widget: QWidget):
        self._basic_panel.add_widget(widget)
    
    def add_advanced_widget(self, widget: QWidget):
        self._advanced_panel.add_widget(widget)
    
    def add_basic_layout(self, layout):
        self._basic_panel.add_layout(layout)
    
    def add_advanced_layout(self, layout):
        self._advanced_panel.add_layout(layout)
