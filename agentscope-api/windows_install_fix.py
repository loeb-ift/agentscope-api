#!/usr/bin/env python
"""本脚本用于修复Windows环境下的pydantic版本兼容性问题"""
import os
import sys
import subprocess

def run_command(command):
    """运行命令并显示输出"""
    print(f"运行命令: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def main():
    print("开始修复Windows环境下的pydantic版本兼容性问题...")
    
    # 升级pip
    print("\n1. 升级pip到最新版本")
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"]):
        print("警告: pip升级失败，继续尝试安装依赖")
    
    # 先卸载已有的pydantic相关包
    print("\n2. 卸载已有的pydantic相关包")
    run_command([sys.executable, "-m", "pip", "uninstall", "-y", "pydantic", "pydantic-settings", "pydantic-core"])
    
    # 安装指定版本的pydantic和pydantic-settings
    print("\n3. 安装兼容版本的pydantic和pydantic-settings")
    if not run_command([sys.executable, "-m", "pip", "install", "pydantic>=2.5.0,<3.0.0"]):
        print("错误: pydantic安装失败")
        return 1
    
    if not run_command([sys.executable, "-m", "pip", "install", "pydantic-settings>=2.5.0,<3.0.0"]):
        print("错误: pydantic-settings安装失败")
        return 1
    
    # 安装所有其他依赖
    print("\n4. 安装所有其他项目依赖")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
        print("警告: 部分依赖安装失败，请手动检查")
    
    # 验证安装
    print("\n5. 验证安装结果")
    run_command([sys.executable, "-m", "pip", "show", "pydantic", "pydantic-settings"])
    
    print("\n修复完成！请尝试重新启动服务器。")
    print("如果仍然遇到问题，请尝试使用以下命令手动安装:")
    print("pip install pydantic==2.11.9 pydantic-settings==2.10.1")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())