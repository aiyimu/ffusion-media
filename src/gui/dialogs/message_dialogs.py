from typing import Optional, Callable
from PySide6.QtWidgets import (
    QMessageBox, QWidget, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.utils.logger import get_logger


logger = get_logger(__name__)


def show_error(
    parent: Optional[QWidget],
    title: str,
    message: str,
    detailed_text: Optional[str] = None
) -> None:
    """
    显示错误提示对话框
    
    Args:
        parent: 父窗口
        title: 对话框标题
        message: 主要消息
        detailed_text: 详细信息（可选）
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if detailed_text:
        msg_box.setDetailedText(detailed_text)
    
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()
    
    logger.error(f"错误提示: {title} - {message}")


def show_warning(
    parent: Optional[QWidget],
    title: str,
    message: str
) -> None:
    """
    显示警告提示对话框
    
    Args:
        parent: 父窗口
        title: 对话框标题
        message: 主要消息
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()
    
    logger.warning(f"警告提示: {title} - {message}")


def show_info(
    parent: Optional[QWidget],
    title: str,
    message: str
) -> None:
    """
    显示信息提示对话框
    
    Args:
        parent: 父窗口
        title: 对话框标题
        message: 主要消息
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()
    
    logger.info(f"信息提示: {title} - {message}")


def show_question(
    parent: Optional[QWidget],
    title: str,
    message: str,
    yes_text: str = "是",
    no_text: str = "否",
    default_yes: bool = True
) -> bool:
    """
    显示确认对话框
    
    Args:
        parent: 父窗口
        title: 对话框标题
        message: 主要消息
        yes_text: 确认按钮文字
        no_text: 取消按钮文字
        default_yes: 是否默认选中确认
    
    Returns:
        bool: 用户是否点击了确认
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Question)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    yes_btn = msg_box.addButton(yes_text, QMessageBox.YesRole)
    no_btn = msg_box.addButton(no_text, QMessageBox.NoRole)
    
    if default_yes:
        msg_box.setDefaultButton(yes_btn)
    else:
        msg_box.setDefaultButton(no_btn)
    
    msg_box.exec()
    
    result = msg_box.clickedButton() == yes_btn
    logger.info(f"确认提示: {title} - {'确认' if result else '取消'}")
    
    return result


def show_confirm_cancel(
    parent: Optional[QWidget],
    title: str = "确认取消",
    message: str = "确定要取消当前操作吗？"
) -> bool:
    """
    显示取消确认对话框
    
    Args:
        parent: 父窗口
        title: 对话框标题
        message: 主要消息
    
    Returns:
        bool: 用户是否确认取消
    """
    return show_question(parent, title, message, "取消", "继续", default_yes=False)


def show_confirm_overwrite(
    parent: Optional[QWidget],
    file_path: str
) -> bool:
    """
    显示文件覆盖确认对话框
    
    Args:
        parent: 父窗口
        file_path: 文件路径
    
    Returns:
        bool: 用户是否确认覆盖
    """
    from pathlib import Path
    file_name = Path(file_path).name
    return show_question(
        parent,
        "文件已存在",
        f"文件 '{file_name}' 已存在。\n是否要覆盖？",
        "覆盖",
        "跳过",
        default_yes=False
    )


def show_task_success(
    parent: Optional[QWidget],
    task_name: str,
    output_path: Optional[str] = None
) -> None:
    """
    显示任务成功对话框
    
    Args:
        parent: 父窗口
        task_name: 任务名称
        output_path: 输出路径（可选）
    """
    message = f"{task_name} 完成！"
    if output_path:
        message += f"\n\n输出目录: {output_path}"
    
    show_info(parent, "任务完成", message)


def show_task_failed(
    parent: Optional[QWidget],
    task_name: str,
    error_message: str
) -> None:
    """
    显示任务失败对话框
    
    Args:
        parent: 父窗口
        task_name: 任务名称
        error_message: 错误信息
    """
    show_error(
        parent,
        "任务失败",
        f"{task_name} 失败！",
        error_message
    )
