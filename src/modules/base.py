from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from src.utils.logger import get_logger
from src.core.exceptions import ParameterError, MissingParameterError, InvalidParameterError


logger = get_logger(__name__)


class BaseFunction(ABC):
    name: str = ""
    description: str = ""
    icon: str = ""
    category: str = ""
    
    def __init__(self):
        self.params: Dict[str, Any] = {}
        self._is_running: bool = False
        self._is_cancelled: bool = False
        self._progress_callback: Optional[Callable[[float, str], None]] = None
        self._status_callback: Optional[Callable[[str], None]] = None
    
    def set_params(self, params: Dict[str, Any]) -> None:
        self.params = params.copy()
        logger.debug(f"{self.name} 模块参数已设置: {self.params}")
    
    def get_params(self) -> Dict[str, Any]:
        return self.params.copy()
    
    def set_progress_callback(self, callback: Optional[Callable[[float, str], None]]) -> None:
        self._progress_callback = callback
    
    def set_status_callback(self, callback: Optional[Callable[[str], None]]) -> None:
        self._status_callback = callback
    
    def _update_progress(self, progress: float, message: str = "") -> None:
        if self._progress_callback:
            self._progress_callback(progress, message)
    
    def _update_status(self, status: str) -> None:
        if self._status_callback:
            self._status_callback(status)
        logger.debug(f"{self.name} 状态更新: {status}")
    
    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def validate_params(self) -> None:
        pass
    
    def _validate_required_params(self, required_params: List[str]) -> None:
        for param in required_params:
            if param not in self.params or self.params[param] in (None, "", []):
                raise MissingParameterError(param)
    
    def _validate_param_in_range(self, param_name: str, min_val: float, max_val: float) -> None:
        value = self.params.get(param_name)
        if value is None:
            return
        try:
            num_value = float(value)
            if not (min_val <= num_value <= max_val):
                raise InvalidParameterError(param_name, str(value), f"值应在 [{min_val}, {max_val}] 范围内")
        except (ValueError, TypeError):
            raise InvalidParameterError(param_name, str(value), "必须是有效的数字")
    
    def _validate_param_in_options(self, param_name: str, valid_options: List[Any]) -> None:
        value = self.params.get(param_name)
        if value is not None and value not in valid_options:
            raise InvalidParameterError(param_name, str(value), f"有效选项为: {valid_options}")
    
    @abstractmethod
    def build_command(self) -> List[str]:
        pass
    
    @abstractmethod
    def execute(self) -> bool:
        pass
    
    def cancel(self) -> None:
        self._is_cancelled = True
        logger.info(f"{self.name} 模块执行已取消")
    
    def is_running(self) -> bool:
        return self._is_running
    
    def is_cancelled(self) -> bool:
        return self._is_cancelled
    
    def reset(self) -> None:
        self._is_running = False
        self._is_cancelled = False
        self.params = self.get_default_params()
        logger.debug(f"{self.name} 模块已重置")
    
    def get_supported_input_formats(self) -> List[str]:
        return []
    
    def get_supported_output_formats(self) -> List[str]:
        return []
