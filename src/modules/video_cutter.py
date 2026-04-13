from typing import Any, Dict, List, Optional
from pathlib import Path
from src.modules.base import BaseFunction
from src.utils.logger import get_logger
from src.utils.validator import (
    validate_not_empty,
    validate_file_extension,
    validate_time_format,
    time_to_seconds,
    get_supported_video_formats
)
from src.utils.file_utils import (
    normalize_path,
    ensure_dir_exists,
    is_file_readable,
    is_file_writable,
    get_file_extension
)
from src.core.ffmpeg_engine import FFmpegEngine
from src.core.ffprobe_parser import FFprobeParser
from src.core.exceptions import (
    FileNotFoundError,
    FileNotReadableError,
    FileNotWritableError,
    InvalidParameterError,
    MissingParameterError,
    ParameterError
)


logger = get_logger(__name__)


class VideoCutter(BaseFunction):
    name = "视频剪切"
    description = "视频片段精准剪切，支持关键帧对齐和毫秒级精度"
    icon = "cut"
    category = "视频"
    
    SUPPORTED_OUTPUT_FORMATS = [
        ".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"
    ]
    
    def __init__(self):
        super().__init__()
        self._engine = FFmpegEngine()
        self._parser = FFprobeParser()
        self._async_task = None
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            "input_files": [],
            "output_dir": "",
            "output_format": ".mp4",
            "cut_mode": "lossless",
            "time_mode": "start_end",
            "start_time": "",
            "end_time": "",
            "duration": "",
            "use_keyframe_align": True,
            "overwrite": True,
            "output_suffix": "_cut"
        }
    
    def get_supported_input_formats(self) -> List[str]:
        return get_supported_video_formats().copy()
    
    def get_supported_output_formats(self) -> List[str]:
        return self.SUPPORTED_OUTPUT_FORMATS.copy()
    
    def validate_params(self) -> None:
        self._validate_required_params(["input_files"])
        
        input_files = self.params.get("input_files", [])
        if not input_files:
            raise MissingParameterError("input_files", "请至少选择一个输入文件")
        
        for idx, file_path in enumerate(input_files):
            if not validate_not_empty(file_path):
                raise InvalidParameterError(f"input_files[{idx}]", str(file_path), "文件路径不能为空")
            
            path = normalize_path(file_path)
            if not path.exists():
                raise FileNotFoundError(str(path))
            if not is_file_readable(path):
                raise FileNotReadableError(str(path))
            
            ext = get_file_extension(path)
            if not validate_file_extension(path, set(self.get_supported_input_formats())):
                raise InvalidParameterError(
                    f"input_files[{idx}]", 
                    str(path), 
                    f"不支持的文件格式: {ext}"
                )
        
        output_dir = self.params.get("output_dir", "")
        if not validate_not_empty(output_dir):
            raise MissingParameterError("output_dir", "请选择输出目录")
        
        output_dir_path = normalize_path(output_dir)
        ensure_dir_exists(output_dir_path)
        
        output_format = self.params.get("output_format", "")
        if not validate_not_empty(output_format):
            raise MissingParameterError("output_format", "请选择输出格式")
        
        if output_format not in self.SUPPORTED_OUTPUT_FORMATS:
            raise InvalidParameterError(
                "output_format",
                output_format,
                f"支持的格式: {self.SUPPORTED_OUTPUT_FORMATS}"
            )
        
        cut_mode = self.params.get("cut_mode", "lossless")
        if cut_mode not in ["lossless", "accurate"]:
            raise InvalidParameterError(
                "cut_mode",
                cut_mode,
                "剪切模式必须是 'lossless' 或 'accurate'"
            )
        
        time_mode = self.params.get("time_mode", "start_end")
        if time_mode not in ["start_end", "start_duration"]:
            raise InvalidParameterError(
                "time_mode",
                time_mode,
                "时间模式必须是 'start_end' 或 'start_duration'"
            )
        
        start_time = self.params.get("start_time", "")
        if time_mode == "start_end":
            end_time = self.params.get("end_time", "")
            if not validate_not_empty(start_time):
                raise MissingParameterError("start_time", "请输入开始时间")
            if not validate_not_empty(end_time):
                raise MissingParameterError("end_time", "请输入结束时间")
            if not validate_time_format(start_time):
                raise InvalidParameterError("start_time", start_time, "时间格式无效")
            if not validate_time_format(end_time):
                raise InvalidParameterError("end_time", end_time, "时间格式无效")
            
            start_sec = time_to_seconds(start_time)
            end_sec = time_to_seconds(end_time)
            if start_sec >= end_sec:
                raise InvalidParameterError("end_time", end_time, "结束时间必须大于开始时间")
        else:
            duration = self.params.get("duration", "")
            if not validate_not_empty(start_time):
                raise MissingParameterError("start_time", "请输入开始时间")
            if not validate_not_empty(duration):
                raise MissingParameterError("duration", "请输入时长")
            if not validate_time_format(start_time):
                raise InvalidParameterError("start_time", start_time, "时间格式无效")
            if not validate_time_format(duration):
                raise InvalidParameterError("duration", duration, "时间格式无效")
            
            duration_sec = time_to_seconds(duration)
            if duration_sec <= 0:
                raise InvalidParameterError("duration", duration, "时长必须大于0")
    
    def build_command(self) -> List[str]:
        raise NotImplementedError("VideoCutter 使用 execute 方法处理批量剪切")
    
    def _build_single_command(self, input_path: Path, output_path: Path, media_info: Dict[str, Any]) -> List[str]:
        cut_mode = self.params.get("cut_mode", "lossless")
        time_mode = self.params.get("time_mode", "start_end")
        start_time = self.params.get("start_time", "")
        use_keyframe_align = self.params.get("use_keyframe_align", True)
        
        args = []
        
        if use_keyframe_align and cut_mode == "lossless":
            args.extend(["-ss", start_time])
            args.extend(["-i", str(input_path)])
        else:
            args.extend(["-i", str(input_path)])
            args.extend(["-ss", start_time])
        
        if time_mode == "start_end":
            end_time = self.params.get("end_time", "")
            start_sec = time_to_seconds(start_time)
            end_sec = time_to_seconds(end_time)
            duration_sec = end_sec - start_sec
            args.extend(["-t", str(duration_sec)])
        else:
            duration = self.params.get("duration", "")
            args.extend(["-t", duration])
        
        if cut_mode == "lossless":
            if media_info.get("has_video"):
                args.extend(["-c:v", "copy"])
            if media_info.get("has_audio"):
                args.extend(["-c:a", "copy"])
        else:
            if media_info.get("has_video"):
                args.extend(["-c:v", "libx264"])
            if media_info.get("has_audio"):
                args.extend(["-c:a", "aac"])
        
        args.extend(["-avoid_negative_ts", "1"])
        args.extend(["-map_metadata", "0"])
        args.append(str(output_path))
        
        return args
    
    def _validate_time_range(self, input_path: Path, media_info: Dict[str, Any]) -> None:
        time_mode = self.params.get("time_mode", "start_end")
        start_time = self.params.get("start_time", "")
        duration = media_info.get("duration", 0)
        
        if duration == 0:
            logger.warning(f"无法获取视频时长: {input_path}")
            return
        
        start_sec = time_to_seconds(start_time)
        
        if start_sec >= duration:
            raise InvalidParameterError(
                "start_time", 
                start_time, 
                f"开始时间超出视频时长 ({duration:.2f}秒)"
            )
        
        if time_mode == "start_end":
            end_time = self.params.get("end_time", "")
            end_sec = time_to_seconds(end_time)
            if end_sec > duration:
                logger.warning(
                    f"结束时间超出视频时长，将自动截断到视频结尾: "
                    f"{end_time} -> {duration:.2f}秒"
                )
        else:
            duration_time = self.params.get("duration", "")
            duration_sec = time_to_seconds(duration_time)
            if start_sec + duration_sec > duration:
                logger.warning(
                    f"剪切时长超出视频剩余时长，将自动截断: "
                    f"{start_sec + duration_sec:.2f}秒 -> {duration:.2f}秒"
                )
    
    def execute(self) -> bool:
        self._is_running = True
        self._is_cancelled = False
        
        try:
            self.validate_params()
            self._update_status("开始剪切...")
            
            input_files = self.params["input_files"]
            output_dir = normalize_path(self.params["output_dir"])
            output_format = self.params["output_format"]
            output_suffix = self.params.get("output_suffix", "_cut")
            total_files = len(input_files)
            
            for idx, input_path_str in enumerate(input_files):
                if self._is_cancelled:
                    self._update_status("已取消")
                    return False
                
                input_path = normalize_path(input_path_str)
                self._update_progress(
                    (idx / total_files) * 100,
                    f"正在处理 {idx + 1}/{total_files}: {input_path.name}"
                )
                
                media_info = self._parser.get_media_info(input_path)
                
                self._validate_time_range(input_path, media_info)
                
                output_filename = input_path.stem + output_suffix + output_format
                output_path = output_dir / output_filename
                
                if output_path.exists() and not self.params.get("overwrite", True):
                    logger.warning(f"输出文件已存在，跳过: {output_path}")
                    continue
                
                command = self._engine.build_command(*self._build_single_command(input_path, output_path, media_info))
                
                result = self._engine.execute_sync(command)
                
                if not result["success"]:
                    logger.error(f"剪切失败: {input_path}")
                    self._update_status(f"剪切失败: {input_path.name}")
                    return False
                
                self._update_progress(
                    ((idx + 1) / total_files) * 100,
                    f"完成 {idx + 1}/{total_files}: {input_path.name}"
                )
            
            self._update_progress(100, "全部完成")
            self._update_status("剪切完成")
            return True
            
        except Exception as e:
            logger.error(f"视频剪切出错: {e}")
            self._update_status(f"错误: {str(e)}")
            return False
        finally:
            self._is_running = False
    
    def cancel(self) -> None:
        self._is_cancelled = True
        if self._async_task:
            self._async_task.cancel()
        super().cancel()
