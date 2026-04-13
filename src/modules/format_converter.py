from typing import Any, Dict, List, Optional
from pathlib import Path
from src.modules.base import BaseFunction
from src.utils.logger import get_logger
from src.utils.validator import (
    validate_not_empty,
    validate_file_extension,
    validate_positive_number,
    validate_non_negative_number,
    get_supported_video_formats,
    get_supported_audio_formats
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
    FFmpegNotFoundError
)


logger = get_logger(__name__)


class FormatConverter(BaseFunction):
    name = "格式转换"
    description = "音视频格式批量转换，支持流复制和重新编码"
    icon = "convert"
    category = "视频"
    
    SUPPORTED_VIDEO_ENCODERS = ["libx264", "libx265", "libvpx", "libaom-av1", "copy"]
    SUPPORTED_AUDIO_ENCODERS = ["aac", "mp3", "flac", "opus", "copy"]
    SUPPORTED_OUTPUT_FORMATS = [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"
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
            "use_stream_copy": True,
            "video_encoder": "copy",
            "audio_encoder": "copy",
            "width": 0,
            "height": 0,
            "frame_rate": 0,
            "video_bitrate": "",
            "audio_bitrate": "",
            "audio_channels": 0,
            "overwrite": True
        }
    
    def get_supported_input_formats(self) -> List[str]:
        return get_supported_video_formats() + get_supported_audio_formats()
    
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
        
        use_stream_copy = self.params.get("use_stream_copy", True)
        if not use_stream_copy:
            video_encoder = self.params.get("video_encoder", "")
            if video_encoder and video_encoder not in self.SUPPORTED_VIDEO_ENCODERS:
                raise InvalidParameterError(
                    "video_encoder",
                    video_encoder,
                    f"支持的视频编码器: {self.SUPPORTED_VIDEO_ENCODERS}"
                )
            
            audio_encoder = self.params.get("audio_encoder", "")
            if audio_encoder and audio_encoder not in self.SUPPORTED_AUDIO_ENCODERS:
                raise InvalidParameterError(
                    "audio_encoder",
                    audio_encoder,
                    f"支持的音频编码器: {self.SUPPORTED_AUDIO_ENCODERS}"
                )
        
        width = self.params.get("width", 0)
        if width > 0:
            if not validate_positive_number(width):
                raise InvalidParameterError("width", str(width), "宽度必须是正数")
        
        height = self.params.get("height", 0)
        if height > 0:
            if not validate_positive_number(height):
                raise InvalidParameterError("height", str(height), "高度必须是正数")
        
        frame_rate = self.params.get("frame_rate", 0)
        if frame_rate > 0:
            if not validate_positive_number(frame_rate):
                raise InvalidParameterError("frame_rate", str(frame_rate), "帧率必须是正数")
        
        audio_channels = self.params.get("audio_channels", 0)
        if audio_channels > 0:
            if not validate_positive_number(audio_channels):
                raise InvalidParameterError("audio_channels", str(audio_channels), "声道数必须是正数")
    
    def build_command(self) -> List[str]:
        raise NotImplementedError("FormatConverter 使用 execute 方法处理批量转换")
    
    def _build_single_command(self, input_path: Path, output_path: Path, media_info: Dict[str, Any]) -> List[str]:
        args = ["-i", str(input_path)]
        
        use_stream_copy = self.params.get("use_stream_copy", True)
        video_encoder = self.params.get("video_encoder", "copy")
        audio_encoder = self.params.get("audio_encoder", "copy")
        width = self.params.get("width", 0)
        height = self.params.get("height", 0)
        frame_rate = self.params.get("frame_rate", 0)
        video_bitrate = self.params.get("video_bitrate", "")
        audio_bitrate = self.params.get("audio_bitrate", "")
        audio_channels = self.params.get("audio_channels", 0)
        
        if use_stream_copy:
            if media_info.get("has_video"):
                args.extend(["-c:v", "copy"])
            if media_info.get("has_audio"):
                args.extend(["-c:a", "copy"])
        else:
            if media_info.get("has_video"):
                args.extend(["-c:v", video_encoder if video_encoder != "copy" else "libx264"])
                if width > 0 and height > 0:
                    args.extend(["-vf", f"scale={width}:{height}"])
                if frame_rate > 0:
                    args.extend(["-r", str(frame_rate)])
                if video_bitrate:
                    args.extend(["-b:v", video_bitrate])
            
            if media_info.get("has_audio"):
                args.extend(["-c:a", audio_encoder if audio_encoder != "copy" else "aac"])
                if audio_channels > 0:
                    args.extend(["-ac", str(audio_channels)])
                if audio_bitrate:
                    args.extend(["-b:a", audio_bitrate])
        
        args.extend(["-map_metadata", "0"])
        args.append(str(output_path))
        
        return args
    
    def execute(self) -> bool:
        self._is_running = True
        self._is_cancelled = False
        
        try:
            self.validate_params()
            self._update_status("开始转换...")
            
            input_files = self.params["input_files"]
            output_dir = normalize_path(self.params["output_dir"])
            output_format = self.params["output_format"]
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
                
                output_filename = input_path.stem + output_format
                output_path = output_dir / output_filename
                
                if output_path.exists() and not self.params.get("overwrite", True):
                    logger.warning(f"输出文件已存在，跳过: {output_path}")
                    continue
                
                command = self._engine.build_command(*self._build_single_command(input_path, output_path, media_info))
                
                duration = media_info.get("duration", 0)
                
                result = self._engine.execute_sync(command)
                
                if not result["success"]:
                    logger.error(f"转换失败: {input_path}")
                    self._update_status(f"转换失败: {input_path.name}")
                    return False
                
                self._update_progress(
                    ((idx + 1) / total_files) * 100,
                    f"完成 {idx + 1}/{total_files}: {input_path.name}"
                )
            
            self._update_progress(100, "全部完成")
            self._update_status("转换完成")
            return True
            
        except Exception as e:
            logger.error(f"格式转换出错: {e}")
            self._update_status(f"错误: {str(e)}")
            return False
        finally:
            self._is_running = False
    
    def cancel(self) -> None:
        self._is_cancelled = True
        if self._async_task:
            self._async_task.cancel()
        super().cancel()
