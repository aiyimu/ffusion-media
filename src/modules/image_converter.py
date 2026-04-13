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
    get_supported_image_formats
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


class ImageConverter(BaseFunction):
    name = "图像转换"
    description = "视频与图像互转：抽帧、合成视频、转GIF、图片转视频"
    icon = "image"
    category = "图像"
    
    PROCESS_MODES = ["extract_frames", "images_to_video", "video_to_gif", "image_to_video"]
    
    SUPPORTED_IMAGE_FORMATS = [
        ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"
    ]
    
    SUPPORTED_VIDEO_OUTPUT_FORMATS = [
        ".mp4", ".mkv", ".avi", ".mov", ".webm"
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
            "process_mode": "extract_frames",
            "image_format": ".jpg",
            "image_quality": 80,
            "extract_mode": "fps",
            "extract_fps": 1,
            "extract_interval": 1.0,
            "extract_total_frames": 10,
            "video_fps": 30,
            "video_duration": 5.0,
            "gif_fps": 10,
            "gif_loop": 0,
            "gif_quality": 80,
            "width": 0,
            "height": 0,
            "overwrite": True,
            "output_suffix": "_frames"
        }
    
    def get_supported_input_formats(self) -> List[str]:
        return get_supported_video_formats() + get_supported_image_formats()
    
    def get_supported_output_formats(self) -> List[str]:
        return self.SUPPORTED_IMAGE_FORMATS + self.SUPPORTED_VIDEO_OUTPUT_FORMATS
    
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
        
        output_dir = self.params.get("output_dir", "")
        if not validate_not_empty(output_dir):
            raise MissingParameterError("output_dir", "请选择输出目录")
        
        output_dir_path = normalize_path(output_dir)
        ensure_dir_exists(output_dir_path)
        
        process_mode = self.params.get("process_mode", "extract_frames")
        if process_mode not in self.PROCESS_MODES:
            raise InvalidParameterError(
                "process_mode",
                process_mode,
                f"处理模式必须是: {self.PROCESS_MODES}"
            )
        
        if process_mode == "extract_frames":
            image_format = self.params.get("image_format", ".jpg")
            if image_format not in self.SUPPORTED_IMAGE_FORMATS:
                raise InvalidParameterError(
                    "image_format",
                    image_format,
                    f"支持的图片格式: {self.SUPPORTED_IMAGE_FORMATS}"
                )
            
            extract_mode = self.params.get("extract_mode", "fps")
            if extract_mode not in ["fps", "interval", "total"]:
                raise InvalidParameterError(
                    "extract_mode",
                    extract_mode,
                    "抽帧模式必须是 'fps'、'interval' 或 'total'"
                )
            
            if extract_mode == "fps":
                extract_fps = self.params.get("extract_fps", 1)
                if not validate_number_range(extract_fps, 0.01, 120):
                    raise InvalidParameterError(
                        "extract_fps",
                        str(extract_fps),
                        "抽帧帧率必须在 0.01-120 范围内"
                    )
            elif extract_mode == "interval":
                interval = self.params.get("extract_interval", 1.0)
                if not validate_number_range(interval, 0.01, 3600):
                    raise InvalidParameterError(
                        "extract_interval",
                        str(interval),
                        "抽帧间隔必须在 0.01-3600 范围内"
                    )
            elif extract_mode == "total":
                total_frames = self.params.get("extract_total_frames", 10)
                if not validate_number_range(total_frames, 1, 10000):
                    raise InvalidParameterError(
                        "extract_total_frames",
                        str(total_frames),
                        "总帧数必须在 1-10000 范围内"
                    )
            
            quality = self.params.get("image_quality", 80)
            if not validate_number_range(quality, 1, 100):
                raise InvalidParameterError(
                    "image_quality",
                    str(quality),
                    "图片质量必须在 1-100 范围内"
                )
        
        elif process_mode == "images_to_video":
            fps = self.params.get("video_fps", 30)
            if not validate_number_range(fps, 1, 120):
                raise InvalidParameterError(
                    "video_fps",
                    str(fps),
                    "视频帧率必须在 1-120 范围内"
                )
        
        elif process_mode == "video_to_gif":
            gif_fps = self.params.get("gif_fps", 10)
            if not validate_number_range(gif_fps, 1, 60):
                raise InvalidParameterError(
                    "gif_fps",
                    str(gif_fps),
                    "GIF帧率必须在 1-60 范围内"
                )
            
            gif_loop = self.params.get("gif_loop", 0)
            if not validate_number_range(gif_loop, -1, 65535):
                raise InvalidParameterError(
                    "gif_loop",
                    str(gif_loop),
                    "循环次数必须在 -1-65535 范围内"
                )
            
            gif_quality = self.params.get("gif_quality", 80)
            if not validate_number_range(gif_quality, 1, 100):
                raise InvalidParameterError(
                    "gif_quality",
                    str(gif_quality),
                    "GIF质量必须在 1-100 范围内"
                )
        
        elif process_mode == "image_to_video":
            duration = self.params.get("video_duration", 5.0)
            if not validate_number_range(duration, 0.1, 3600):
                raise InvalidParameterError(
                    "video_duration",
                    str(duration),
                    "视频时长必须在 0.1-3600 范围内"
                )
            
            fps = self.params.get("video_fps", 30)
            if not validate_number_range(fps, 1, 120):
                raise InvalidParameterError(
                    "video_fps",
                    str(fps),
                    "视频帧率必须在 1-120 范围内"
                )
        
        width = self.params.get("width", 0)
        if width > 0:
            if not validate_number_range(width, 1, 7680):
                raise InvalidParameterError("width", str(width), "宽度必须在 1-7680 范围内")
        
        height = self.params.get("height", 0)
        if height > 0:
            if not validate_number_range(height, 1, 4320):
                raise InvalidParameterError("height", str(height), "高度必须在 1-4320 范围内")
    
    def build_command(self) -> List[str]:
        raise NotImplementedError("ImageConverter 使用 execute 方法处理批量处理")
    
    def _build_extract_frames_command(self, input_path: Path, output_dir: Path, media_info: Dict[str, Any]) -> List[str]:
        image_format = self.params.get("image_format", ".jpg")
        extract_mode = self.params.get("extract_mode", "fps")
        quality = self.params.get("image_quality", 80)
        width = self.params.get("width", 0)
        height = self.params.get("height", 0)
        
        args = ["-i", str(input_path)]
        
        if extract_mode == "fps":
            fps = self.params.get("extract_fps", 1)
            args.extend(["-vf", f"fps={fps}"])
        elif extract_mode == "interval":
            interval = self.params.get("extract_interval", 1.0)
            args.extend(["-vf", f"fps=1/{interval}"])
        elif extract_mode == "total":
            total_frames = self.params.get("extract_total_frames", 10)
            duration = media_info.get("duration", 10)
            if duration > 0:
                fps = total_frames / duration
                args.extend(["-vf", f"fps={fps}"])
        
        if width > 0 and height > 0:
            args.extend(["-s", f"{width}x{height}"])
        elif width > 0:
            args.extend(["-vf", f"scale={width}:-1"])
        elif height > 0:
            args.extend(["-vf", f"scale=-1:{height}"])
        
        if image_format in [".jpg", ".jpeg"]:
            args.extend(["-q:v", str(quality)])
        elif image_format == ".png":
            args.extend(["-compression_level", str((100 - quality) // 10)])
        elif image_format == ".webp":
            args.extend(["-quality", str(quality)])
        
        output_pattern = output_dir / f"frame_%04d{image_format}"
        args.append(str(output_pattern))
        
        return args
    
    def _build_images_to_video_command(self, input_files: List[Path], output_path: Path, media_info: Dict[str, Any]) -> List[str]:
        fps = self.params.get("video_fps", 30)
        width = self.params.get("width", 0)
        height = self.params.get("height", 0)
        
        args = ["-framerate", str(fps)]
        
        if len(input_files) == 1 and input_files[0].suffix in [".txt"]:
            args.extend(["-f", "concat", "-safe", "0", "-i", str(input_files[0])])
        else:
            first_image = input_files[0]
            ext = first_image.suffix
            stem = first_image.stem
            pattern = str(first_image.parent / f"{stem}%d{ext}")
            args.extend(["-i", pattern])
        
        if width > 0 and height > 0:
            args.extend(["-s", f"{width}x{height}"])
        
        args.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
        args.append(str(output_path))
        
        return args
    
    def _build_video_to_gif_command(self, input_path: Path, output_path: Path, media_info: Dict[str, Any]) -> List[str]:
        gif_fps = self.params.get("gif_fps", 10)
        gif_loop = self.params.get("gif_loop", 0)
        gif_quality = self.params.get("gif_quality", 80)
        width = self.params.get("width", 0)
        height = self.params.get("height", 0)
        
        args = ["-i", str(input_path)]
        
        filter_parts = [f"fps={gif_fps}"]
        
        if width > 0 and height > 0:
            filter_parts.append(f"scale={width}:{height}:flags=lanczos")
        elif width > 0:
            filter_parts.append(f"scale={width}:-1:flags=lanczos")
        elif height > 0:
            filter_parts.append(f"scale=-1:{height}:flags=lanczos")
        
        filters = ",".join(filter_parts)
        args.extend(["-vf", filters])
        
        args.extend(["-loop", str(gif_loop)])
        args.append(str(output_path))
        
        return args
    
    def _build_image_to_video_command(self, input_path: Path, output_path: Path, media_info: Dict[str, Any]) -> List[str]:
        duration = self.params.get("video_duration", 5.0)
        fps = self.params.get("video_fps", 30)
        width = self.params.get("width", 0)
        height = self.params.get("height", 0)
        
        args = ["-loop", "1", "-i", str(input_path)]
        
        args.extend(["-t", str(duration)])
        args.extend(["-r", str(fps)])
        
        if width > 0 and height > 0:
            args.extend(["-s", f"{width}x{height}"])
        elif width > 0:
            args.extend(["-vf", f"scale={width}:-1"])
        elif height > 0:
            args.extend(["-vf", f"scale=-1:{height}"])
        
        args.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
        args.append(str(output_path))
        
        return args
    
    def _build_single_command(self, input_path: Path, output_path: Path, media_info: Dict[str, Any]) -> List[str]:
        process_mode = self.params.get("process_mode", "extract_frames")
        
        if process_mode == "extract_frames":
            return self._build_extract_frames_command(input_path, output_path.parent, media_info)
        elif process_mode == "images_to_video":
            return self._build_images_to_video_command([input_path], output_path, media_info)
        elif process_mode == "video_to_gif":
            return self._build_video_to_gif_command(input_path, output_path, media_info)
        elif process_mode == "image_to_video":
            return self._build_image_to_video_command(input_path, output_path, media_info)
        
        return []
    
    def execute(self) -> bool:
        self._is_running = True
        self._is_cancelled = False
        
        try:
            self.validate_params()
            self._update_status("开始处理...")
            
            input_files = self.params["input_files"]
            output_dir = normalize_path(self.params["output_dir"])
            process_mode = self.params.get("process_mode", "extract_frames")
            output_suffix = self.params.get("output_suffix", "_frames")
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
                
                if process_mode == "extract_frames":
                    image_format = self.params.get("image_format", ".jpg")
                    output_subdir = output_dir / f"{input_path.stem}{output_suffix}"
                    ensure_dir_exists(output_subdir)
                    output_path = output_subdir / f"frame_0001{image_format}"
                elif process_mode == "video_to_gif":
                    output_path = output_dir / f"{input_path.stem}{output_suffix}.gif"
                elif process_mode == "image_to_video":
                    output_path = output_dir / f"{input_path.stem}{output_suffix}.mp4"
                else:
                    output_path = output_dir / f"{input_path.stem}{output_suffix}.mp4"
                
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
            logger.error(f"图像转换出错: {e}")
            self._update_status(f"错误: {str(e)}")
            return False
        finally:
            self._is_running = False
    
    def cancel(self) -> None:
        self._is_cancelled = True
        if self._async_task:
            self._async_task.cancel()
        super().cancel()
