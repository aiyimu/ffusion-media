import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type
from src.modules.base import BaseFunction
from src.utils.logger import get_logger


logger = get_logger(__name__)


class ModuleManager:
    _instance: Optional['ModuleManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ModuleManager._initialized:
            return
        
        self._modules: Dict[str, Type[BaseFunction]] = {}
        self._module_instances: Dict[str, BaseFunction] = {}
        self._auto_discover()
        ModuleManager._initialized = True
    
    def _auto_discover(self) -> None:
        module_dir = Path(__file__).parent
        module_files = [f for f in module_dir.glob("*.py") if f.is_file() and f.stem != "__init__" and f.stem != "base" and f.stem != "module_manager"]
        
        logger.info(f"开始自动发现模块，共发现 {len(module_files)} 个模块文件")
        
        for module_file in module_files:
            try:
                module_name = f"src.modules.{module_file.stem}"
                module = importlib.import_module(module_name)
                
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseFunction) and 
                        obj != BaseFunction):
                        self._register_module(obj)
                        logger.info(f"已注册模块: {obj.name} ({module_file.stem})")
                        
            except Exception as e:
                logger.error(f"加载模块 {module_file.stem} 失败: {e}")
        
        logger.info(f"模块自动发现完成，共注册 {len(self._modules)} 个模块")
    
    def _register_module(self, module_class: Type[BaseFunction]) -> None:
        if not hasattr(module_class, 'name') or not module_class.name:
            logger.warning(f"模块类 {module_class.__name__} 未定义 name 属性，跳过注册")
            return
        
        if module_class.name in self._modules:
            logger.warning(f"模块名称 {module_class.name} 已存在，将被覆盖")
        
        self._modules[module_class.name] = module_class
    
    def get_module_class(self, module_name: str) -> Optional[Type[BaseFunction]]:
        return self._modules.get(module_name)
    
    def get_module(self, module_name: str) -> Optional[BaseFunction]:
        if module_name in self._module_instances:
            return self._module_instances[module_name]
        
        module_class = self.get_module_class(module_name)
        if module_class:
            instance = module_class()
            self._module_instances[module_name] = instance
            return instance
        
        logger.warning(f"模块未找到: {module_name}")
        return None
    
    def get_all_module_names(self) -> List[str]:
        return list(self._modules.keys())
    
    def get_all_modules(self) -> List[Type[BaseFunction]]:
        return list(self._modules.values())
    
    def get_modules_by_category(self, category: str) -> List[Type[BaseFunction]]:
        return [
            module_class for module_class in self._modules.values()
            if hasattr(module_class, 'category') and module_class.category == category
        ]
    
    def get_categories(self) -> List[str]:
        categories = set()
        for module_class in self._modules.values():
            if hasattr(module_class, 'category') and module_class.category:
                categories.add(module_class.category)
        return sorted(list(categories))
    
    def reset_module(self, module_name: str) -> bool:
        if module_name in self._module_instances:
            self._module_instances[module_name].reset()
            return True
        return False
    
    def reset_all_modules(self) -> None:
        for instance in self._module_instances.values():
            instance.reset()
        logger.info("所有模块已重置")
    
    def refresh_modules(self) -> None:
        self._modules.clear()
        self._module_instances.clear()
        self._auto_discover()
        logger.info("模块已刷新")


def get_module_manager() -> ModuleManager:
    return ModuleManager()
