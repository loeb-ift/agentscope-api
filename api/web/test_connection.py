#!/usr/bin/env python3
"""
测试脚本 - 检查AgentScope API连接
"""

import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载项目根目录下的单一 .env 文件
project_root = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=project_root / ".env")

# 配置（嚴格依賴 .env，不提供代碼內預設值）
API_BASE_URL = os.environ["API_BASE_URL"]
base_url = f"{API_BASE_URL}/api"

def test_connection():
    """测试API连接"""
    print(f"测试连接: {base_url}")
    
    try:
        # 测试健康检查
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API服务运行正常")
            print(f"   状态: {data.get('status')}")
            print(f"   时间: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ API服务异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务")
        print("   请确保AgentScope API服务已启动")
        print("   启动命令: ./start_server.sh")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_ollama():
    """测试OLLAMA连接"""
    # 允許從 OLLAMA_HOST 或 OLLAMA_API_BASE 取得主機位址
    OLLAMA_HOST = os.environ.get("OLLAMA_HOST", os.environ.get("OLLAMA_API_BASE"))
    
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ OLLAMA服务运行正常")
            models = data.get('models', [])
            if models:
                print("   可用模型:")
                for model in models:
                    print(f"   - {model.get('name')}")
            return True
        else:
            print(f"❌ OLLAMA服务异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OLLAMA连接失败: {e}")
        return False

if __name__ == "__main__":
    print("=== AgentScope API连接测试 ===\n")
    
    print("1. 测试API服务...")
    api_ok = test_connection()
    
    print("\n2. 测试OLLAMA服务...")
    ollama_ok = test_ollama()
    
    print("\n=== 测试结果 ===")
    if api_ok and ollama_ok:
        print("✅ 所有服务运行正常，可以启动Web界面")
    else:
        print("⚠️ 部分服务异常，请检查配置和服务状态")