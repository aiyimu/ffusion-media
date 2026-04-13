import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from src.utils.logger import get_logger
from src.utils.file_utils import get_ffprobe_path, is_file_readable, normalize_path
from src.core.exceptions import (
    FFprobeNotFoundError,
    FFprobeExecutionError,
    FileNotFoundError,
    FileNotReadableError,
    InvalidFileFormatError,
    ParseMediaInfoError,
    UnsupportedMediaFormatError
)


logger = get_logger(__name__)


class FFprobeParser:
    _instance: Optional["FFprobeParser"] = None
    _ffprobe_path: Optional[Path] = None
    
    def __new__(cls) -> "FFprobeParser":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._locate_ffprobe()
    
    def _locate_ffprobe(self) -> None:
        self._ffprobe_path = get_ffprobe_path()
        if self._ffprobe_path is None:
            logger.warning("未找到 ffprobe 可执行文件")
        else:
            logger.info(f"找到 ffprobe: {self._ffprobe_path}")
    
    def set_ffprobe_path(self, path: str) -> None:
        self._ffprobe_path = normalize_path(path)
        if not self._ffprobe_path.exists():
            raise FFprobeNotFoundError(f"指定的 ffprobe 路径不存在: {path}")
        logger.info(f"设置 ffprobe 路径: {self._ffprobe_path}")
    
    def get_ffprobe_path(self) -> Optional[Path]:
        return self._ffprobe_path
    
    def _check_ffprobe_available(self) -> None:
        if self._ffprobe_path is None:
            raise FFprobeNotFoundError()
        if not self._ffprobe_path.exists():
            raise FFprobeNotFoundError(f"ffprobe 不存在: {self._ffprobe_path}")
    
    def _validate_input_file(self, file_path: Union[str, Path]) -> Path:
        path = normalize_path(file_path)
        if not path.exists():
            raise FileNotFoundError(str(path))
        if not path.is_file():
            raise InvalidFileFormatError(str(path), "不是一个文件")
        if not is_file_readable(path):
            raise FileNotReadableError(str(path))
        return path
    
    def _execute_ffprobe(self, args: List[str]) -> Dict[str, Any]:
        self._check_ffprobe_available()
        
        cmd = [str(self._ffprobe_path)] + args
        logger.debug(f"执行 ffprobe 命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )
            
            if result.returncode != 0:
                raise FFprobeExecutionError(
                    "ffprobe 执行失败",
                    result.returncode,
                    result.stderr
                )
            
            return json.loads(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise FFprobeExecutionError("ffprobe 执行超时", -1, "执行超时")
        except json.JSONDecodeError as e:
            raise ParseMediaInfoError("", f"解析 ffprobe 输出失败: {e}")
        except Exception as e:
            if isinstance(e, FFusionMediaError):
                raise
            raise FFprobeExecutionError(f"ffprobe 执行异常: {e}", -1, str(e))
    
    def get_media_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        path = self._validate_input_file(file_path)
        
        args = [
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path)
        ]
        
        raw_data = self._execute_ffprobe(args)
        return self._parse_media_info(raw_data, path)
    
    def _parse_media_info(self, raw_data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        try:
            format_info = raw_data.get("format", {})
            streams = raw_data.get("streams", [])
            
            video_stream = None
            audio_stream = None
            
            for stream in streams:
                if stream.get("codec_type") == "video" and video_stream is None:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and audio_stream is None:
                    audio_stream = stream
            
            media_info = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": int(format_info.get("size", 0)),
                "format_name": format_info.get("format_name", ""),
                "format_long_name": format_info.get("format_long_name", ""),
                "duration": float(format_info.get("duration", 0)),
                "bit_rate": int(format_info.get("bit_rate", 0)),
                "has_video": video_stream is not None,
                "has_audio": audio_stream is not None,
                "video": None,
                "audio": None
            }
            
            if video_stream:
                media_info["video"] = {
                    "codec": video_stream.get("codec_name", ""),
                    "codec_long_name": video_stream.get("codec_long_name", ""),
                    "width": int(video_stream.get("width", 0)),
                    "height": int(video_stream.get("height", 0)),
                    "pixel_format": video_stream.get("pix_fmt", ""),
                    "frame_rate": self._parse_frame_rate(video_stream.get("r_frame_rate", "0/1")),
                    "bit_rate": int(video_stream.get("bit_rate", 0)),
                    "duration": float(video_stream.get("duration", 0)),
                    "rotation": int(video_stream.get("rotation", 0))
                }
            
            if audio_stream:
                media_info["audio"] = {
                    "codec": audio_stream.get("codec_name", ""),
                    "codec_long_name": audio_stream.get("codec_long_name", ""),
                    "sample_rate": int(audio_stream.get("sample_rate", 0)),
                    "channels": int(audio_stream.get("channels", 0)),
                    "channel_layout": audio_stream.get("channel_layout", ""),
                    "bit_rate": int(audio_stream.get("bit_rate", 0)),
                    "duration": float(audio_stream.get("duration", 0))
                }
            
            return media_info
            
        except Exception as e:
            raise ParseMediaInfoError(str(file_path), f"解析媒体信息失败: {e}")
    
    def _parse_frame_rate(self, frame_rate_str: str) -> float:
        try:
            if "/" in frame_rate_str:
                num, den = frame_rate_str.split("/", 1)
                return float(num) / float(den) if float(den) != 0 else 0.0
            return float(frame_rate_str)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def is_valid_media_file(self, file_path: Union[str, Path]) -> bool:
        try:
            info = self.get_media_info(file_path)
            return info["has_video"] or info["has_audio"]
        except Exception:
            return False
    
    def get_video_keyframes(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = self._validate_input_file(file_path)
        
        args = [
            "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "frame=pkt_pts_time,pkt_dts_time,key_frame,pict_type",
            "-of", "json",
            str(path)
        ]
        
        raw_data = self._execute_ffprobe(args)
        frames = raw_data.get("frames", [])
        
        keyframes = []
        for frame in frames:
            if frame.get("key_frame") == 1:
                keyframes.append({
                    "timestamp": float(frame.get("pkt_pts_time", 0)),
                    "pict_type": frame.get("pict_type", "")
                })
        
        return keyframes
    
    def get_audio_waveform_data(self, file_path: Union[str, Path], samples: int = 1000) -> List[float]:
        path = self._validate_input_file(file_path)
        
        args = [
            "-v", "quiet",
            "-f", "lavfi",
            f"amovie='{str(path).replace(':', '\\:')}',showwavespic=s={samples}",
            "-show_entries", "frame=pkt_pts,pkt_size",
            "-of", "json",
            "-"
        ]
        
        try:
            raw_data = self._execute_ffprobe(args)
            frames = raw_data.get("frames", [])
            
            waveform = []
            for frame in frames:
                waveform.append(float(frame.get("pkt_size", 0)) / 1000.0)
            
            return waveform
            
        except Exception:
            return []
