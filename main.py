import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from src.gui.main_window import MainWindow
from src.utils.logger import setup_logger, get_logger
from src.utils.config_manager import ConfigManager


logger = get_logger(__name__)


def init_logger():
    setup_logger()
    logger.info("日志系统初始化完成")


def load_config():
    config = ConfigManager()
    logger.info("加载配置文件")


def create_app() -> QApplication:
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    return app


def show_error(message: str, detailed_text: str = ""):
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Critical)
    error_box.setWindowTitle("程序启动失败")
    error_box.setText(message)
    if detailed_text:
        error_box.setDetailedText(detailed_text)
    error_box.exec()


def main():
    try:
        init_logger()
        load_config()
        
        app = create_app()
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"程序启动失败：{e}", exc_info=True)
        show_error(
            "程序启动失败！",
            f"错误信息：{str(e)}\n\n详细错误请查看日志文件。"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
