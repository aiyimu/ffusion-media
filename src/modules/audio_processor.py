from typing import Any, Dict, List, Optional
from pathlib import Path
from src.modules.base import BaseFunction
from src.utils.logger import get_logger
from src.utils.validator import (
    validate_not_empty,
    validate_file_extension,
    validate_number_range,
    validate_time_format,
    time_to_seconds,
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
    MissingParameterError
)


logger = get_logger(__name__)


class AudioProcessor(BaseFunction):
    name = "音频处理"
    description = "音频全量处理：提取、转换、剪切、音量、声道、降噪"
    icon = "audio"
    category = "音频"
    
    PROCESS_MODES = ["extract", "convert", "cut", "volume", "channel", "denoise"]
    
    SUPPORTED_OUTPUT_FORMATS = [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".opus"
    ]
    
    CHANNEL_MODES = ["stereo", "mono", "left", "right", "swap"]
    
    def __init__(self):
        super().__init__()
        self._engine = FFmpegEngine()
        self._parser = FFprobeParser()
        self._async_task = None
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            "input_files": [],
            "output_dir": "",
            "output_format": ".mp3",
            "process_mode": "extract",
            "volume_percent": 100,
            "channel_mode": "stereo",
            "denoise_strength": 0.5,
            "start_time": "",
            "end_time": "",
            "overwrite": True,
            "output_suffix": "_audio"
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
        
        process_mode = self.params.get("process_mode", "extract")
        if process_mode not in self.PROCESS_MODES:
            raise InvalidParameterError(
                "process_mode",
                process_mode,
                f"处理模式必须是: {self.PROCESS_MODES}"
            )
        
        if process_mode == "volume":
            volume = self.params.get("volume_percent", 100)
            if not validate_number_range(volume, 0, 200):
                raise InvalidParameterError(
                    "volume_percent",
                    str(volume),
                    "音量百分比必须在 0-200 范围内"
                )
        
        if process_mode == "channel":
            channel_mode = self.params.get("channel_mode", "stereo")
            if channel_mode not in self.CHANNEL_MODES:
                raise InvalidParameterError(
                    "channel_mode",
                    channel_mode,
                    f"声道模式必须是: {self.CHANNEL_MODES}"
                )
        
        if process_mode == "denoise":
            strength = self.params.get("denoise_strength", 0.5)
            if not validate_number_range(strength, 0, 1):
                raise InvalidParameterError(
                    "denoise_strength",
                    str(strength),
                    "降噪强度必须在 0-1 范围内"
                )
        
        if process_mode == "cut":
            start_time = self.params.get("start_time", "")
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
    
    def build_command(self) -> List[str]:
        raise NotImplementedError("AudioProcessor 使用 execute 方法处理批量处理")
    
    def _build_single_command(self, input_path: Path, output_path: Path, media_info: Dict[str, Any]) -> List[str]:
        process_mode = self.params.get("process_mode", "extract")
        output_format = self.params.get("output_format", ".mp3")
        
        args = ["-i", str(input_path)]
        
        if process_mode == "extract":
            args.extend(["-vn"])
            args.extend(["-c:a", self._get_default_audio_codec(output_format)])
        
        elif process_mode == "convert":
            args.extend(["-vn"])
            args.extend(["-c:a", self._get_default_audio_codec(output_format)])
        
        elif process_mode == "cut":
            start_time = self.params.get("start_time", "")
            end_time = self.params.get("end_time", "")
            start_sec = time_to_seconds(start_time)
            end_sec = time_to_seconds(end_time)
            duration_sec = end_sec - start_sec
            
            args.extend(["-vn"])
            args.extend(["-ss", start_time])
            args.extend(["-t", str(duration_sec)])
            args.extend(["-c:a", "copy"])
        
        elif process_mode == "volume":
            volume_percent = self.params.get("volume_percent", 100)
            volume_factor = volume_percent / 100.0
            args.extend(["-vn"])
            args.extend(["-filter:a", f"volume={volume_factor}"])
            args.extend(["-c:a", self._get_default_audio_codec(output_format)])
        
        elif process_mode == "channel":
            channel_mode = self.params.get("channel_mode", "stereo")
            args.extend(["-vn"])
            
            if channel_mode == "mono":
                args.extend(["-ac", "1"])
            elif channel_mode == "stereo":
                args.extend(["-ac", "2"])
            elif channel_mode == "left":
                args.extend(["-filter:a", "pan=mono|c0=c0"])
            elif channel_mode == "right":
                args.extend(["-filter:a", "pan=mono|c0=c1"])
            elif channel_mode == "swap":
                args.extend(["-filter:a", "channelmap=channel_layout=stereo:map=1+0"])
            
            args.extend(["-c:a", self._get_default_audio_codec(output_format)])
        
        elif process_mode == "denoise":
            strength = self.params.get("denoise_strength", 0.5)
            args.extend(["-vn"])
            args.extend(["-af", f"afftdn=nf=-20"])
            args.extend(["-c:a", self._get_default_audio_codec(output_format)])
        
        args.extend(["-map_metadata", "0"])
        args.append(str(output_path))
        
        return args
    
    def _get_default_audio_codec(self, output_format: str) -> str:
        codec_map = {
            ".mp3": "libmp3lame",
            ".wav": "pcm_s16le",
            ".flac": "flac",
            ".aac": "aac",
            ".ogg": "libvorbis",
            ".m4a": "aac",
            ".opus": "libopus"
        }
        return codec_map.get(output_format, "aac")
    
    def _validate_audio_available(self, input_path: Path, media_info: Dict[str, Any]) -> None:
        if not media_info.get("has_audio"):
            raise InvalidParameterError(
                "input_files",
                str(input_path),
                f"文件不包含音频流: {input_path.name}"
            )
    
    def execute(self) -> bool:
        self._is_running = True
        self._is_cancelled = False
        
        try:
            self.validate_params()
            self._update_status("开始处理...")
            
            input_files = self.params["input_files"]
            output_dir = normalize_path(self.params["output_dir"])
            output_format = self.params["output_format"]
            output_suffix = self.params.get("output_suffix", "_audio")
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
                
                self._validate_audio_available(input_path, media_info)
                
                output_filename = input_path.stem + output_suffix + output_format
                output_path = output_dir / output_filename
                
                if output_path.exists() and not self.params.get("overwrite", True):
                    logger.warning(f"输出文件已存在，跳过: {output_path}")
                    continue
                
                command = self._engine.build_command(*self._build_single_command(input_path, output_path, media_info))
                
                result = self._engine.execute_sync(command)
                
                if not result["success"]:
                    logger.error(f"处理失败: {input_path}")
                    self._update_status(f"处理失败: {input_path.name}")
                    return False
                
                self._update_progress(
                    ((idx + 1) / total_files) * 100,
                    f"完成 {idx + 1}/{total_files}: {input_path.name}"
                )
            
            self._update_progress(100, "全部完成")
            self._update_status("处理完成")
            return True
            
        except Exception as e:
            logger.error(f"音频处理出错: {e}")
            self._update_status(f"错误: {str(e)}")
            return False
        finally:
            self._is_running = False
    
    def cancel(self) -> None:
        self._is_cancelled = True
        if self._async_task:
            self._async_task.cancel()
        super().cancel()
