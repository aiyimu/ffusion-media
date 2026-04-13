#!/usr/bin/env python
"""
模块管理器演示脚本
演示模块自动注册与管理功能
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules import get_module_manager


def main():
    print("=" * 60)
    print("FFusion Media - 模块管理器演示")
    print("=" * 60)
    
    manager = get_module_manager()
    
    print("\n1. 获取所有模块名称:")
    module_names = manager.get_all_module_names()
    for name in module_names:
        print(f"  - {name}")
    
    print(f"\n共发现 {len(module_names)} 个模块")
    
    print("\n2. 按分类列出模块:")
    categories = manager.get_categories()
    for category in categories:
        print(f"\n  【{category}】:")
        modules = manager.get_modules_by_category(category)
        for module_class in modules:
            print(f"    - {module_class.name}: {module_class.description}")
    
    print("\n3. 获取模块实例并测试:")
    for module_name in module_names:
        print(f"\n  测试模块: {module_name}")
        module = manager.get_module(module_name)
        if module:
            print(f"    OK 实例化成功")
            default_params = module.get_default_params()
            print(f"    默认参数数量: {len(default_params)}")
            print(f"    支持的输入格式: {len(module.get_supported_input_formats())} 种")
            print(f"    支持的输出格式: {len(module.get_supported_output_formats())} 种")
    
    print("\n" + "=" * 60)
    print("模块管理器演示完成！")
    print("=" * 60)
    print("\n使用示例:")
    print("  from src.modules import get_module_manager")
    print("  manager = get_module_manager()")
    print("  module = manager.get_module('格式转换')")
    print("  module.set_params(params)")
    print("  module.execute()")


if __name__ == "__main__":
    main()
