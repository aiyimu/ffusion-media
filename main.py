import sys
import traceback
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt


def init_logger() -> None:
    from src.utils.logger import setup_logger
    setup_logger()


def load_config() -> None:
    from src.utils.config_manager import ConfigManager
    ConfigManager()


def create_application() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName("FFusion Media")
    app.setOrganizationName("FFusion Media")
    return app


def show_error_message(message: str, details: str = "") -> None:
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Critical)
    error_box.setWindowTitle("程序启动失败")
    error_box.setText(message)
    if details:
        error_box.setDetailedText(details)
    error_box.exec()


def main() -> int:
    try:
        init_logger()
        load_config()
        app = create_application()
        
        from src.gui.main_window import MainWindow
        main_window = MainWindow()
        main_window.show()
        
        return app.exec()
    except Exception as e:
        error_message = f"程序启动时发生错误: {str(e)}"
        error_details = traceback.format_exc()
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        show_error_message(error_message, error_details)
        return 1


if __name__ == "__main__":
    sys.exit(main())
