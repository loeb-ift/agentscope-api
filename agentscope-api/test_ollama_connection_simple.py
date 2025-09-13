#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的Ollama连接测试脚本
用于直接测试Ollama服务是否正常运行
"""

import os
import sys
import time
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
from app.core.config import settings
from agentscope.model import OllamaChatModel


async def test_ollama_connection_async():
    """异步测试Ollama连接"""
    print("开始Ollama连接测试...")
    print(f"使用配置:\n- 模型名称: {settings.DEFAULT_MODEL_NAME}\n- API基础地址: {settings.OLLAMA_API_BASE}")
    
    try:
        # 创建OllamaChatModel实例
        print("正在初始化OllamaChatModel...")
        start_time = time.time()
        
        model = OllamaChatModel(
            model_name=settings.DEFAULT_MODEL_NAME,
            host=settings.OLLAMA_API_BASE,
            stream=False
        )
        
        init_time = time.time() - start_time
        print(f"OllamaChatModel初始化成功，耗时: {init_time:.2f}秒")
        
        # 发送简单的测试消息
        print("\n正在发送测试消息...")
        test_message = [{"role": "user", "content": "你好，Ollama！请简单介绍一下自己。"}]
        
        start_time = time.time()
        # 正确使用异步调用
        response = await model(test_message)
        response_time = time.time() - start_time
        
        # 检查响应
        if hasattr(response, 'content'):
            print(f"测试消息发送成功，响应耗时: {response_time:.2f}秒")
            print(f"\nOllama响应:\n{response.content}")
            return True
        else:
            print("错误: 响应不包含content属性")
            return False
            
    except Exception as e:
        print(f"错误: 连接Ollama服务失败\n详细错误信息: {str(e)}")
        print("\n请检查以下几点:\n1. Ollama服务是否已启动\n2. API地址是否正确\n3. 模型是否已下载\n4. 网络连接是否正常")
        return False


def test_ollama_connection():
    """同步测试函数，用于调用异步测试"""
    return asyncio.run(test_ollama_connection_async())


def main():
    """主函数"""
    print("=== Ollama连接测试工具 ===")
    print("此工具用于测试与Ollama服务的连接是否正常")
    
    success = test_ollama_connection()
    
    print("\n=== 测试结果 ===")
    if success:
        print("✅ Ollama连接测试成功！")
    else:
        print("❌ Ollama连接测试失败！")
    

if __name__ == "__main__":
    main()