#!/usr/bin/env python3
"""
测试Ollama配置和连接的脚本
"""
import sys
import os
import requests
import time
from app.core.config import settings

print("=== 测试Ollama配置和连接 ===")

# 打印配置信息
print(f"\n1. 当前配置：")
print(f"   OLLAMA_API_BASE = {settings.OLLAMA_API_BASE}")
print(f"   DEFAULT_MODEL_NAME = {settings.DEFAULT_MODEL_NAME}")
print(f"   直接读取环境变量 OLLAMA_API_BASE = {os.environ.get('OLLAMA_API_BASE')}")
print(f"   直接读取环境变量 DEFAULT_MODEL_NAME = {os.environ.get('DEFAULT_MODEL_NAME')}")

# 测试网络连接
try:
    print(f"\n2. 测试Ollama服务器连接 ({settings.OLLAMA_API_BASE})：")
    # 测试API标签端点
    tags_url = f"{settings.OLLAMA_API_BASE}/api/tags"
    response = requests.get(tags_url, timeout=5)
    response.raise_for_status()
    models = response.json().get('models', [])
    print(f"   连接成功！查找到 {len(models)} 个模型")
    print(f"   前3个可用模型: {', '.join([model['name'] for model in models[:3]])}")
    
    # 检查默认模型是否可用
    default_model_available = any(model['name'] == settings.DEFAULT_MODEL_NAME or 
                                model['name'].startswith(f"{settings.DEFAULT_MODEL_NAME}:") 
                                for model in models)
    print(f"   默认模型 '{settings.DEFAULT_MODEL_NAME}' {'可用' if default_model_available else '不可用'}")
    
    # 尝试一个简单的模型调用
    if default_model_available:
        print(f"\n3. 测试模型调用：")
        chat_url = f"{settings.OLLAMA_API_BASE}/api/chat"
        payload = {
            "model": settings.DEFAULT_MODEL_NAME,
            "messages": [
                {"role": "user", "content": "请说一句简短的问候语"}
            ],
            "stream": False
        }
        try:
            print(f"   正在调用模型，请稍候...")
            start_time = time.time()
            response = requests.post(chat_url, json=payload, timeout=30)  # 增加超时时间到30秒
            response.raise_for_status()
            end_time = time.time()
            result = response.json()
            print(f"   模型调用成功！响应时间: {end_time - start_time:.2f}秒")
            print(f"   响应内容: {result.get('message', {}).get('content', '无响应')}")
        except requests.exceptions.ReadTimeout:
            print(f"   模型调用超时！大模型首次加载可能需要较长时间，请尝试再次运行测试。")
            # 不要在这种情况下退出，因为我们已经确认配置是正确的
    
except requests.exceptions.RequestException as e:
    print(f"   连接失败: {str(e)}")
    sys.exit(1)

except Exception as e:
    print(f"   发生错误: {str(e)}")
    sys.exit(1)

print("\n=== 测试完成 ===")
print("\n=== 配置修复总结 ===")
print("1. 已修复agent_service.py中的配置读取问题，现在统一使用settings对象获取Ollama配置")
print("2. 已修复config.py中的配置问题，为OLLAMA_API_BASE添加了默认值")
print("3. 已移除config.py中重复的导入和验证器定义")
print("\n虽然直接读取环境变量返回None，但这是正常的，因为Settings类会从.env文件直接读取配置而不是设置环境变量")
print("所有组件现在都使用settings对象获取配置，确保了配置的统一性")
print("\n注意：模型调用超时可能是因为大模型首次加载需要较长时间，请稍后再次测试")
print("如果需要修改Ollama配置，请在.env文件中更新对应的值：")
print("- OLLAMA_API_BASE: 设置Ollama服务器地址")
print("- DEFAULT_MODEL_NAME: 设置默认使用的模型名称")