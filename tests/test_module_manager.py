import unittest
from unittest.mock import patch, MagicMock

from src.modules.module_manager import ModuleManager, get_module_manager
from src.modules.base import BaseFunction
from src.modules.format_converter import FormatConverter
from src.modules.video_cutter import VideoCutter
from src.modules.audio_processor import AudioProcessor
from src.modules.image_converter import ImageConverter


class TestModuleManager(unittest.TestCase):
    
    def setUp(self):
        self.manager = ModuleManager()
    
    def test_singleton_pattern(self):
        manager1 = ModuleManager()
        manager2 = ModuleManager()
        manager3 = get_module_manager()
        
        self.assertIs(manager1, manager2)
        self.assertIs(manager1, manager3)
    
    def test_auto_discover_modules(self):
        modules = self.manager.get_all_module_names()
        
        self.assertIn("格式转换", modules)
        self.assertIn("视频剪切", modules)
        self.assertIn("音频处理", modules)
        self.assertIn("图像转换", modules)
    
    def test_get_module_class(self):
        format_class = self.manager.get_module_class("格式转换")
        self.assertIsNotNone(format_class)
        self.assertEqual(format_class, FormatConverter)
        
        video_class = self.manager.get_module_class("视频剪切")
        self.assertIsNotNone(video_class)
        self.assertEqual(video_class, VideoCutter)
        
        audio_class = self.manager.get_module_class("音频处理")
        self.assertIsNotNone(audio_class)
        self.assertEqual(audio_class, AudioProcessor)
        
        image_class = self.manager.get_module_class("图像转换")
        self.assertIsNotNone(image_class)
        self.assertEqual(image_class, ImageConverter)
    
    def test_get_module_class_nonexistent(self):
        module_class = self.manager.get_module_class("不存在的模块")
        self.assertIsNone(module_class)
    
    def test_get_module(self):
        format_module = self.manager.get_module("格式转换")
        self.assertIsNotNone(format_module)
        self.assertIsInstance(format_module, BaseFunction)
        self.assertIsInstance(format_module, FormatConverter)
        
        video_module = self.manager.get_module("视频剪切")
        self.assertIsNotNone(video_module)
        self.assertIsInstance(video_module, BaseFunction)
        self.assertIsInstance(video_module, VideoCutter)
    
    def test_get_module_cached(self):
        module1 = self.manager.get_module("格式转换")
        module2 = self.manager.get_module("格式转换")
        
        self.assertIs(module1, module2)
    
    def test_get_module_nonexistent(self):
        module = self.manager.get_module("不存在的模块")
        self.assertIsNone(module)
    
    def test_get_all_module_names(self):
        names = self.manager.get_all_module_names()
        
        self.assertIsInstance(names, list)
        self.assertGreater(len(names), 0)
        self.assertIn("格式转换", names)
        self.assertIn("视频剪切", names)
        self.assertIn("音频处理", names)
        self.assertIn("图像转换", names)
    
    def test_get_all_modules(self):
        modules = self.manager.get_all_modules()
        
        self.assertIsInstance(modules, list)
        self.assertGreater(len(modules), 0)
        
        for module_class in modules:
            self.assertTrue(issubclass(module_class, BaseFunction))
            self.assertNotEqual(module_class, BaseFunction)
    
    def test_get_modules_by_category(self):
        video_modules = self.manager.get_modules_by_category("视频")
        
        self.assertIsInstance(video_modules, list)
        self.assertGreater(len(video_modules), 0)
        
        for module_class in video_modules:
            self.assertEqual(module_class.category, "视频")
        
        audio_modules = self.manager.get_modules_by_category("音频")
        self.assertIsInstance(audio_modules, list)
        self.assertGreater(len(audio_modules), 0)
        
        for module_class in audio_modules:
            self.assertEqual(module_class.category, "音频")
        
        image_modules = self.manager.get_modules_by_category("图像")
        self.assertIsInstance(image_modules, list)
        self.assertGreater(len(image_modules), 0)
        
        for module_class in image_modules:
            self.assertEqual(module_class.category, "图像")
    
    def test_get_modules_by_nonexistent_category(self):
        modules = self.manager.get_modules_by_category("不存在的分类")
        self.assertEqual(modules, [])
    
    def test_get_categories(self):
        categories = self.manager.get_categories()
        
        self.assertIsInstance(categories, list)
        self.assertIn("视频", categories)
        self.assertIn("音频", categories)
        self.assertIn("图像", categories)
    
    def test_reset_module(self):
        module = self.manager.get_module("格式转换")
        
        module.set_params({"test": "value"})
        params1 = module.get_params()
        self.assertNotEqual(params1, module.get_default_params())
        
        result = self.manager.reset_module("格式转换")
        self.assertTrue(result)
        
        params2 = module.get_params()
        self.assertEqual(params2, module.get_default_params())
    
    def test_reset_module_nonexistent(self):
        result = self.manager.reset_module("不存在的模块")
        self.assertFalse(result)
    
    def test_reset_all_modules(self):
        format_module = self.manager.get_module("格式转换")
        video_module = self.manager.get_module("视频剪切")
        
        format_module.set_params({"test1": "value1"})
        video_module.set_params({"test2": "value2"})
        
        self.manager.reset_all_modules()
        
        self.assertEqual(format_module.get_params(), format_module.get_default_params())
        self.assertEqual(video_module.get_params(), video_module.get_default_params())
    
    def test_module_initialization(self):
        for module_name in self.manager.get_all_module_names():
            module = self.manager.get_module(module_name)
            self.assertIsNotNone(module)
            
            params = module.get_default_params()
            self.assertIsInstance(params, dict)
            self.assertGreater(len(params), 0)
            
            module.reset()
            self.assertFalse(module.is_running())
            self.assertFalse(module.is_cancelled())
    
    def test_module_properties(self):
        modules = self.manager.get_all_modules()
        
        for module_class in modules:
            self.assertTrue(hasattr(module_class, 'name'))
            self.assertTrue(hasattr(module_class, 'description'))
            self.assertTrue(hasattr(module_class, 'category'))
            
            self.assertIsInstance(module_class.name, str)
            self.assertGreater(len(module_class.name), 0)
            self.assertIsInstance(module_class.description, str)
            self.assertIsInstance(module_class.category, str)
    
    def test_get_module_manager_function(self):
        manager1 = get_module_manager()
        manager2 = get_module_manager()
        
        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, ModuleManager)
    
    @patch('src.modules.module_manager.importlib.import_module')
    def test_module_auto_discover_error_handling(self, mock_import):
        mock_import.side_effect = Exception("Import failed")
        
        manager = ModuleManager()
        
        self.assertIsInstance(manager, ModuleManager)


if __name__ == '__main__':
    unittest.main()
