import pydantic
import pydantic_settings
import pkg_resources

try:
    # 获取pydantic版本
    pydantic_version = pydantic.__version__
    print(f"Pydantic version: {pydantic_version}")
    
    # 获取pydantic-settings版本
    pydantic_settings_version = pydantic_settings.__version__
    print(f"Pydantic-Settings version: {pydantic_settings_version}")
    
    # 尝试导入导致错误的模块
    try:
        from pydantic._internal._signature import _field_name_for_signature
        print("Successfully imported _field_name_for_signature")
    except ImportError as e:
        print(f"Import error: {e}")
        
    # 检查已安装的所有pydantic相关包
    print("\nInstalled pydantic-related packages:")
    for package in pkg_resources.working_set:
        if "pydantic" in package.project_name.lower():
            print(f"- {package.project_name}: {package.version}")
    
except Exception as e:
    print(f"Error: {e}")