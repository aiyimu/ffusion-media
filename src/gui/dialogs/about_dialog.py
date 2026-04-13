from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget, QTextEdit, QFrame, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import QUrl

from src.utils.logger import get_logger


logger = get_logger(__name__)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("关于 FFusion Media")
        self.setMinimumSize(550, 500)
        self.setMaximumSize(600, 550)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        logo_label = QLabel("⚡")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 64px;")
        
        title_label = QLabel("FFusion Media")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        
        version_label = QLabel("版本 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 14px; opacity: 0.7;")
        
        desc_label = QLabel("基于 FFmpeg 的强大媒体处理工具")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 14px;")
        desc_label.setWordWrap(True)
        
        layout.addWidget(logo_label)
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addWidget(desc_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)
        
        tab_widget = QTabWidget()
        
        about_tab = self._create_about_tab()
        tab_widget.addTab(about_tab, "📖 关于")
        
        license_tab = self._create_license_tab()
        tab_widget.addTab(license_tab, "📜 协议")
        
        changelog_tab = self._create_changelog_tab()
        tab_widget.addTab(changelog_tab, "📋 更新日志")
        
        layout.addWidget(tab_widget, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        help_btn = QPushButton("📚 帮助文档")
        help_btn.setMinimumHeight(36)
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.clicked.connect(self._open_help)
        
        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(help_btn)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_about_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFrameShape(QFrame.NoFrame)
        text.setHtml("""
            <h3>FFusion Media</h3>
            <p>一个现代化、跨平台的媒体处理工具，基于 FFmpeg 提供强大的音视频处理能力。</p>
            
            <h4>主要功能</h4>
            <ul>
                <li>📹 视频格式转换</li>
                <li>✂️ 视频剪切</li>
                <li>🎵 音频处理</li>
                <li>🖼️ 图像转换</li>
                <li>📋 任务队列管理</li>
            </ul>
            
            <h4>技术特点</h4>
            <ul>
                <li>🎨 现代化 UI 设计</li>
                <li>🌙 明暗双主题</li>
                <li>🔌 插件化架构</li>
                <li>📊 实时进度展示</li>
                <li>💾 配置持久化</li>
            </ul>
            
            <p style="opacity: 0.7;">© 2026 FFusion Media Team</p>
        """)
        
        layout.addWidget(text)
        
        return tab
    
    def _create_license_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFrameShape(QFrame.NoFrame)
        text.setHtml("""
            <h3>MIT License</h3>
            
            <p>Copyright (c) 2026 FFusion Media Team</p>
            
            <p>Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the "Software"), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions:</p>
            
            <p>The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.</p>
            
            <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.</p>
        """)
        
        layout.addWidget(text)
        
        return tab
    
    def _create_changelog_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFrameShape(QFrame.NoFrame)
        text.setHtml("""
            <h3>更新日志</h3>
            
            <h4>v1.0.0 (2026-04-12)</h4>
            <ul>
                <li>🎉 初始版本发布</li>
                <li>✅ 项目基础框架</li>
                <li>✅ 核心引擎开发</li>
                <li>✅ 功能模块开发</li>
                <li>✅ GUI 界面开发</li>
                <li>✅ 自定义控件库</li>
                <li>✅ 设置与对话框</li>
            </ul>
        """)
        
        layout.addWidget(text)
        
        return tab
    
    def _open_help(self):
        QDesktopServices.openUrl(QUrl("https://github.com/ffusion-media/docs"))
        logger.info("打开帮助文档")
