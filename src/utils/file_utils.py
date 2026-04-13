import os
import sys
import stat
from pathlib import Path
from typing import Optional, Union


def get_logger():
    from .logger import get_logger as _get_logger
    return _get_logger(__name__)


def get_user_data_dir() -> Path:
    project_root = Path(__file__).parent.parent.parent
    return project_root / ".temp" / "user_data"


def normalize_path(path: Union[str, Path]) -> Path:
    return Path(path).expanduser().resolve()


def ensure_dir_exists(directory: Union[str, Path]) -> Path:
    dir_path = normalize_path(directory)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        get_logger().debug(f"创建目录: {dir_path}")
    return dir_path


def is_file_writable(file_path: Union[str, Path]) -> bool:
    path = normalize_path(file_path)
    if path.exists():
        return os.access(path, os.W_OK)
    parent_dir = path.parent
    return os.access(parent_dir, os.W_OK)


def is_file_readable(file_path: Union[str, Path]) -> bool:
    path = normalize_path(file_path)
    return path.exists() and os.access(path, os.R_OK)


def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
    path = normalize_path(file_path)
    if path.exists() and path.is_file():
        return path.stat().st_size
    return None


def get_file_extension(file_path: Union[str, Path]) -> str:
    path = normalize_path(file_path)
    return path.suffix.lower()


def safe_remove_file(file_path: Union[str, Path]) -> bool:
    path = normalize_path(file_path)
    try:
        if path.exists() and path.is_file():
            path.unlink()
            get_logger().debug(f"删除文件: {path}")
            return True
        return False
    except Exception as e:
        get_logger().error(f"删除文件失败 {path}: {e}")
        return False


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def get_bin_dir() -> Path:
    project_root = get_project_root()
    if sys.platform == "win32":
        return project_root / "bin" / "windows"
    elif sys.platform == "darwin":
        return project_root / "bin" / "macos"
    else:
        return project_root / "bin" / "linux"


def get_ffmpeg_path() -> Optional[Path]:
    bin_dir = get_bin_dir()
    if sys.platform == "win32":
        ffmpeg_path = bin_dir / "ffmpeg.exe"
    else:
        ffmpeg_path = bin_dir / "ffmpeg"
    if ffmpeg_path.exists():
        return ffmpeg_path
    return None


def get_ffprobe_path() -> Optional[Path]:
    bin_dir = get_bin_dir()
    if sys.platform == "win32":
        ffprobe_path = bin_dir / "ffprobe.exe"
    else:
        ffprobe_path = bin_dir / "ffprobe"
    if ffprobe_path.exists():
        return ffprobe_path
    return None


def make_executable(file_path: Union[str, Path]) -> bool:
    if sys.platform == "win32":
        return True
    try:
        path = normalize_path(file_path)
        current_stat = path.stat()
        path.chmod(current_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        get_logger().debug(f"设置可执行权限: {path}")
        return True
    except Exception as e:
        get_logger().error(f"设置可执行权限失败 {file_path}: {e}")
        return False
