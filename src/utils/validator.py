import re
import os
from pathlib import Path
from typing import Any, Optional, List, Union
from .logger import get_logger


logger = get_logger(__name__)


SUPPORTED_VIDEO_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts", ".mts"}
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"}
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}
SUPPORTED_MEDIA_FORMATS = SUPPORTED_VIDEO_FORMATS | SUPPORTED_AUDIO_FORMATS | SUPPORTED_IMAGE_FORMATS


def validate_time_format(time_str: str) -> bool:
    if not time_str:
        return False
    patterns = [
        r"^\d{1,2}:\d{2}:\d{2}(\.\d+)?$",
        r"^\d{1,2}:\d{2}(\.\d+)?$",
        r"^\d+(\.\d+)?$"
    ]
    for pattern in patterns:
        if re.match(pattern, time_str):
            return True
    return False


def time_to_seconds(time_str: str) -> float:
    if not time_str:
        return 0.0
    if ":" not in time_str:
        return float(time_str)
    parts = time_str.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    return 0.0


def validate_file_extension(file_path: Union[str, Path], allowed_extensions: Optional[set] = None) -> bool:
    path = Path(file_path)
    ext = path.suffix.lower()
    if allowed_extensions is None:
        allowed_extensions = SUPPORTED_MEDIA_FORMATS
    return ext in allowed_extensions


def validate_file_exists(file_path: Union[str, Path]) -> bool:
    path = Path(file_path)
    return path.exists() and path.is_file()


def validate_directory_writable(dir_path: Union[str, Path]) -> bool:
    path = Path(dir_path)
    if not path.exists():
        return False
    return path.is_dir() and os.access(path, os.W_OK)


def validate_number_range(value: Any, min_val: float, max_val: float) -> bool:
    try:
        num = float(value)
        return min_val <= num <= max_val
    except (ValueError, TypeError):
        return False


def validate_positive_number(value: Any) -> bool:
    try:
        num = float(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_non_negative_number(value: Any) -> bool:
    try:
        num = float(value)
        return num >= 0
    except (ValueError, TypeError):
        return False


def validate_integer(value: Any) -> bool:
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_encoding(encoding: str) -> bool:
    valid_encodings = {
        "utf-8", "utf-16", "utf-16-le", "utf-16-be",
        "gbk", "gb2312", "gb18030",
        "ascii", "latin-1", "iso-8859-1",
        "cp1252", "cp936"
    }
    return encoding.lower() in valid_encodings


def validate_not_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) > 0
    return True


def validate_string_length(value: str, min_len: int = 0, max_len: Optional[int] = None) -> bool:
    if not isinstance(value, str):
        return False
    length = len(value)
    if length < min_len:
        return False
    if max_len is not None and length > max_len:
        return False
    return True


def validate_resolution(resolution: str) -> bool:
    pattern = r"^\d+x\d+$"
    return bool(re.match(pattern, resolution))


def parse_resolution(resolution: str) -> Optional[tuple[int, int]]:
    if not validate_resolution(resolution):
        return None
    width, height = resolution.split("x")
    try:
        return (int(width), int(height))
    except ValueError:
        return None


def validate_bitrate(bitrate: str) -> bool:
    pattern = r"^\d+[kKmM]?$"
    return bool(re.match(pattern, bitrate))


def validate_frame_rate(fps: Any) -> bool:
    try:
        fps_num = float(fps)
        return fps_num > 0 and fps_num <= 240
    except (ValueError, TypeError):
        return False


def get_supported_video_formats() -> List[str]:
    return sorted(list(SUPPORTED_VIDEO_FORMATS))


def get_supported_audio_formats() -> List[str]:
    return sorted(list(SUPPORTED_AUDIO_FORMATS))


def get_supported_image_formats() -> List[str]:
    return sorted(list(SUPPORTED_IMAGE_FORMATS))


def get_supported_media_formats() -> List[str]:
    return sorted(list(SUPPORTED_MEDIA_FORMATS))
