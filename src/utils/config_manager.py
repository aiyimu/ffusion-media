import configparser
from pathlib import Path
from typing import Any, Dict, Optional
from .logger import get_logger
from .file_utils import get_user_data_dir, ensure_dir_exists


logger = get_logger(__name__)


class ConfigManager:
    _instance: Optional["ConfigManager"] = None
    _config: configparser.ConfigParser
    _config_file: Path
    
    DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
        "basic": {
            "language": "zh_CN",
            "theme": "dark",
            "output_dir": "",
            "default_output_dir": "",
            "auto_open_output": "true"
        },
        "ffmpeg": {
            "ffmpeg_path": "",
            "ffprobe_path": "",
            "auto_detect_ffmpeg": "true",
            "use_gpu": "false",
            "gpu_type": "auto",
            "threads": "0"
        },
        "interface": {
            "window_width": "1280",
            "window_height": "720",
            "sidebar_width": "200",
            "show_toolbar": "true",
            "show_notification": "true"
        },
        "advanced": {
            "log_level": "INFO",
            "keep_temp_files": "false",
            "max_concurrent_tasks": "1",
            "show_advanced_options": "false",
            "confirm_overwrite": "true",
            "temp_dir": "",
            "enable_debug_logging": "false"
        }
    }
    
    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        
        self._config = configparser.ConfigParser()
        self._config_file = get_user_data_dir() / "config.ini"
        self._load_config()
        self._initialized = True
    
    def _load_config(self) -> None:
        ensure_dir_exists(self._config_file.parent)
        
        for section, options in self.DEFAULT_CONFIG.items():
            if not self._config.has_section(section):
                self._config.add_section(section)
            for key, value in options.items():
                if not self._config.has_option(section, key):
                    self._config.set(section, key, str(value))
        
        if self._config_file.exists():
            try:
                self._config.read(self._config_file, encoding="utf-8")
                logger.info(f"加载配置文件: {self._config_file}")
            except Exception as e:
                logger.error(f"读取配置文件失败，使用默认配置: {e}")
                self._save_config()
        else:
            logger.info("配置文件不存在，创建默认配置")
            self._save_config()
    
    def _save_config(self) -> None:
        try:
            ensure_dir_exists(self._config_file.parent)
            with open(self._config_file, "w", encoding="utf-8") as f:
                self._config.write(f)
            logger.debug(f"保存配置文件: {self._config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def get(self, section: str, key: str, fallback: Optional[Any] = None) -> str:
        try:
            value = self._config.get(section, key, fallback=fallback)
            return str(value) if value is not None else ""
        except (configparser.NoOptionError, configparser.NoSectionError):
            return str(fallback) if fallback is not None else ""
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        try:
            return self._config.getint(section, key, fallback=fallback)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return fallback
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        try:
            return self._config.getfloat(section, key, fallback=fallback)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        try:
            return self._config.getboolean(section, key, fallback=fallback)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return fallback
    
    def set(self, section: str, key: str, value: Any) -> None:
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, str(value))
        self._save_config()
    
    def get_section(self, section: str) -> Dict[str, str]:
        if self._config.has_section(section):
            return dict(self._config[section])
        return {}
    
    def reset_to_default(self, section: Optional[str] = None, key: Optional[str] = None) -> None:
        if section is None:
            self._config = configparser.ConfigParser()
            for sec, options in self.DEFAULT_CONFIG.items():
                if not self._config.has_section(sec):
                    self._config.add_section(sec)
                for k, v in options.items():
                    self._config.set(sec, k, str(v))
            logger.info("已重置所有配置为默认值")
        elif key is None:
            if section in self.DEFAULT_CONFIG:
                if self._config.has_section(section):
                    self._config.remove_section(section)
                self._config.add_section(section)
                for k, v in self.DEFAULT_CONFIG[section].items():
                    self._config.set(section, k, str(v))
                logger.info(f"已重置配置节 [{section}] 为默认值")
        else:
            if section in self.DEFAULT_CONFIG and key in self.DEFAULT_CONFIG[section]:
                self._config.set(section, key, str(self.DEFAULT_CONFIG[section][key]))
                logger.info(f"已重置配置项 [{section}].{key} 为默认值")
        self._save_config()
