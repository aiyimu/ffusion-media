import re
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from PySide6.QtCore import QThread, Signal, QObject
from src.utils.logger import get_logger
from src.utils.file_utils import get_ffmpeg_path, normalize_path, is_file_writable, ensure_dir_exists
from src.core.exceptions import (
    FFmpegNotFoundError,
    FFmpegExecutionError,
    InvalidFFmpegCommandError,
    TaskCancelledError,
    FileNotWritableError,
    DirectoryNotFoundError,
    DirectoryNotWritableError
)


logger = get_logger(__name__)


class FFmpegEngine:
    _instance: Optional["FFmpegEngine"] = None
    _ffmpeg_path: Optional[Path] = None
    
    def __new__(cls) -> "FFmpegEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._locate_ffmpeg()
    
    def _locate_ffmpeg(self) -> None:
        self._ffmpeg_path = get_ffmpeg_path()
        if self._ffmpeg_path is None:
            logger.warning("未找到 ffmpeg 可执行文件")
        else:
            logger.info(f"找到 ffmpeg: {self._ffmpeg_path}")
    
    def set_ffmpeg_path(self, path: str) -> None:
        self._ffmpeg_path = normalize_path(path)
        if not self._ffmpeg_path.exists():
            raise FFmpegNotFoundError(f"指定的 ffmpeg 路径不存在: {path}")
        logger.info(f"设置 ffmpeg 路径: {self._ffmpeg_path}")
    
    def get_ffmpeg_path(self) -> Optional[Path]:
        return self._ffmpeg_path
    
    def _check_ffmpeg_available(self) -> None:
        if self._ffmpeg_path is None:
            raise FFmpegNotFoundError()
        if not self._ffmpeg_path.exists():
            raise FFmpegNotFoundError(f"ffmpeg 不存在: {self._ffmpeg_path}")
    
    def _validate_output_path(self, output_path: Union[str, Path]) -> Path:
        path = normalize_path(output_path)
        parent_dir = path.parent
        if not parent_dir.exists():
            raise DirectoryNotFoundError(str(parent_dir))
        if not parent_dir.is_dir():
            raise DirectoryNotWritableError(str(parent_dir))
        if path.exists() and not is_file_writable(path):
            raise FileNotWritableError(str(path))
        ensure_dir_exists(parent_dir)
        return path
    
    def build_command(self, *args: str) -> List[str]:
        self._check_ffmpeg_available()
        
        cmd = [str(self._ffmpeg_path)]
        cmd.extend(["-y"])
        cmd.extend(args)
        
        logger.debug(f"构建 FFmpeg 命令: {' '.join(cmd)}")
        return cmd
    
    def execute_sync(self, command: List[str]) -> Dict[str, Any]:
        self._check_ffmpeg_available()
        
        if not command or command[0] != str(self._ffmpeg_path):
            raise InvalidFFmpegCommandError("命令必须以 ffmpeg 开头")
        
        logger.info(f"同步执行 FFmpeg 命令: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            
            output = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode != 0:
                raise FFmpegExecutionError(
                    "FFmpeg 执行失败",
                    result.returncode,
                    result.stderr
                )
            
            logger.info("FFmpeg 同步执行完成")
            return output
            
        except subprocess.TimeoutExpired:
            raise FFmpegExecutionError("FFmpeg 执行超时", -1, "执行超时")
        except Exception as e:
            if isinstance(e, FFusionMediaError):
                raise
            raise FFmpegExecutionError(f"FFmpeg 执行异常: {e}", -1, str(e))
    
    def execute_async(
        self,
        command: List[str],
        duration: float = 0,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> "FFmpegAsyncTask":
        self._check_ffmpeg_available()
        
        if not command or command[0] != str(self._ffmpeg_path):
            raise InvalidFFmpegCommandError("命令必须以 ffmpeg 开头")
        
        task = FFmpegAsyncTask(
            command,
            duration,
            progress_callback,
            status_callback,
            log_callback
        )
        return task


class FFmpegAsyncTask(QThread):
    progress_updated = Signal(float, str)
    status_updated = Signal(str)
    log_updated = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(
        self,
        command: List[str],
        duration: float = 0,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        super().__init__()
        self.command = command
        self.duration = duration
        self._cancelled = False
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        
        if progress_callback:
            self.progress_updated.connect(progress_callback)
        if status_callback:
            self.status_updated.connect(status_callback)
        if log_callback:
            self.log_updated.connect(log_callback)
    
    def run(self):
        try:
            self._update_status("准备执行...")
            logger.info(f"异步执行 FFmpeg 命令: {' '.join(self.command)}")
            
            self._process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                universal_newlines=True
            )
            
            self._update_status("执行中...")
            
            output_lines = []
            time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
            speed_pattern = re.compile(r"speed=([\d.]+)x")
            
            for line in self._process.stdout:
                line = line.strip()
                if line:
                    output_lines.append(line)
                    self.log_updated.emit(line)
                    
                    time_match = time_pattern.search(line)
                    if time_match:
                        hours = int(time_match.group(1))
                        minutes = int(time_match.group(2))
                        seconds = int(time_match.group(3))
                        centiseconds = int(time_match.group(4))
                        current_time = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                        
                        speed = 1.0
                        speed_match = speed_pattern.search(line)
                        if speed_match:
                            speed = float(speed_match.group(1))
                        
                        if self.duration > 0:
                            progress = min(current_time / self.duration * 100, 100)
                            self._update_progress(progress, f"处理中... {progress:.1f}%")
                    
                    with self._lock:
                        if self._cancelled:
                            self._process.terminate()
                            self._update_status("正在取消...")
                            break
            
            self._process.wait()
            
            with self._lock:
                if self._cancelled:
                    self._update_status("已取消")
                    self.finished.emit(False, "任务已取消")
                    raise TaskCancelledError()
            
            if self._process.returncode != 0:
                error_msg = "\n".join(output_lines[-10:]) if output_lines else ""
                self._update_status("执行失败")
                self.finished.emit(False, f"执行失败 (退出码: {self._process.returncode})")
                raise FFmpegExecutionError(
                    "FFmpeg 执行失败",
                    self._process.returncode,
                    error_msg
                )
            
            self._update_progress(100, "完成")
            self._update_status("已完成")
            self.finished.emit(True, "执行成功")
            logger.info("FFmpeg 异步执行完成")
            
        except TaskCancelledError:
            self._update_status("已取消")
            self.finished.emit(False, "任务已取消")
        except Exception as e:
            logger.error(f"FFmpeg 异步执行异常: {e}")
            self._update_status(f"错误: {str(e)}")
            self.finished.emit(False, str(e))
    
    def cancel(self):
        with self._lock:
            if not self._cancelled:
                self._cancelled = True
                logger.info("取消 FFmpeg 异步任务")
                if self._process:
                    try:
                        self._process.terminate()
                    except Exception:
                        pass
    
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled
    
    def _update_progress(self, progress: float, message: str = ""):
        self.progress_updated.emit(progress, message)
    
    def _update_status(self, status: str):
        self.status_updated.emit(status)
