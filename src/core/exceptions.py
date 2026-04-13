class FFusionMediaError(Exception):
    pass


class FFmpegError(FFusionMediaError):
    pass


class FFmpegNotFoundError(FFmpegError):
    def __init__(self, message: str = "未找到FFmpeg可执行文件"):
        super().__init__(message)


class FFprobeNotFoundError(FFmpegError):
    def __init__(self, message: str = "未找到FFprobe可执行文件"):
        super().__init__(message)


class FFmpegExecutionError(FFmpegError):
    def __init__(self, message: str, exit_code: int = -1, stderr: str = ""):
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(f"{message} (退出码: {exit_code})")


class FFprobeExecutionError(FFmpegError):
    def __init__(self, message: str, exit_code: int = -1, stderr: str = ""):
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(f"{message} (退出码: {exit_code})")


class InvalidFFmpegCommandError(FFmpegError):
    def __init__(self, message: str = "无效的FFmpeg命令"):
        super().__init__(message)


class ParameterError(FFusionMediaError):
    pass


class InvalidParameterError(ParameterError):
    def __init__(self, param_name: str, param_value: str, message: str = ""):
        self.param_name = param_name
        self.param_value = param_value
        full_message = f"参数 '{param_name}' 值 '{param_value}' 无效"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class MissingParameterError(ParameterError):
    def __init__(self, param_name: str, message: str = ""):
        self.param_name = param_name
        full_message = f"缺少必需参数: '{param_name}'"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class ParameterRangeError(ParameterError):
    def __init__(self, param_name: str, param_value: str, min_val: float, max_val: float, message: str = ""):
        self.param_name = param_name
        self.param_value = param_value
        self.min_val = min_val
        self.max_val = max_val
        full_message = f"参数 '{param_name}' 值 '{param_value}' 超出范围 [{min_val}, {max_val}]"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class FileError(FFusionMediaError):
    pass


class FileNotFoundError(FileError):
    def __init__(self, file_path: str, message: str = ""):
        self.file_path = file_path
        full_message = f"文件不存在: {file_path}"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class FileNotReadableError(FileError):
    def __init__(self, file_path: str, message: str = ""):
        self.file_path = file_path
        full_message = f"文件无法读取: {file_path}"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class FileNotWritableError(FileError):
    def __init__(self, file_path: str, message: str = ""):
        self.file_path = file_path
        full_message = f"文件无法写入: {file_path}"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class InvalidFileFormatError(FileError):
    def __init__(self, file_path: str, expected_format: str = "", message: str = ""):
        self.file_path = file_path
        self.expected_format = expected_format
        full_message = f"无效的文件格式: {file_path}"
        if expected_format:
            full_message += f" (期望格式: {expected_format})"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class DirectoryNotFoundError(FileError):
    def __init__(self, dir_path: str, message: str = ""):
        self.dir_path = dir_path
        full_message = f"目录不存在: {dir_path}"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class DirectoryNotWritableError(FileError):
    def __init__(self, dir_path: str, message: str = ""):
        self.dir_path = dir_path
        full_message = f"目录无法写入: {dir_path}"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class ExecutionError(FFusionMediaError):
    pass


class TaskCancelledError(ExecutionError):
    def __init__(self, message: str = "任务已被取消"):
        super().__init__(message)


class TaskTimeoutError(ExecutionError):
    def __init__(self, timeout: float, message: str = ""):
        self.timeout = timeout
        full_message = f"任务超时 ({timeout}秒)"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class TaskQueueError(ExecutionError):
    pass


class QueueFullError(TaskQueueError):
    def __init__(self, message: str = "任务队列已满"):
        super().__init__(message)


class ConfigurationError(FFusionMediaError):
    pass


class ConfigFileNotFoundError(ConfigurationError):
    def __init__(self, config_path: str, message: str = ""):
        self.config_path = config_path
        full_message = f"配置文件不存在: {config_path}"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class InvalidConfigError(ConfigurationError):
    def __init__(self, config_key: str, config_value: str, message: str = ""):
        self.config_key = config_key
        self.config_value = config_value
        full_message = f"无效的配置项 '{config_key}': '{config_value}'"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class MediaInfoError(FFusionMediaError):
    pass


class ParseMediaInfoError(MediaInfoError):
    def __init__(self, file_path: str, message: str = ""):
        self.file_path = file_path
        full_message = f"解析媒体信息失败: {file_path}"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)


class UnsupportedMediaFormatError(MediaInfoError):
    def __init__(self, file_path: str, message: str = ""):
        self.file_path = file_path
        full_message = f"不支持的媒体格式: {file_path}"
        if message:
            full_message += f": {message}"
        super().__init__(full_message)
