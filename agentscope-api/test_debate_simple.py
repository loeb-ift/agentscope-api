#!/usr/bin/env python3
"""
简单测试辩论系统的Ollama连接
"""
import requests
import json
import time

# API配置
API_BASE_URL = "http://127.0.0.1:8000/api"

def test_ollama_connection():
    """直接测试Ollama连接状态"""
    try:
        # 先直接测试Ollama API连接
        from app.core.config import settings
        print(f"\n1. 检查Ollama配置...")
        print(f"   OLLAMA_API_BASE: {settings.OLLAMA_API_BASE}")
        print(f"   DEFAULT_MODEL_NAME: {settings.DEFAULT_MODEL_NAME}")
        
        # 尝试直接连接Ollama
        import requests
        print(f"\n2. 直接测试Ollama服务器连接...")
        ollama_url = f"{settings.OLLAMA_API_BASE}/api/tags"
        print(f"   测试URL: {ollama_url}")
        response = requests.get(ollama_url, timeout=10)
        if response.status_code == 200:
            models = response.json()
            print(f"   成功连接到Ollama服务器！")
            print(f"   可用模型数量: {len(models.get('models', []))}")
            return True
        else:
            print(f"   连接失败，HTTP状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"   连接Ollama服务器异常: {str(e)}")
        return False

def create_test_agent():
    """创建一个测试Agent"""
    try:
        print(f"\n3. 创建测试Agent...")
        agent_payload = {
            "name": "test_agent",
            "role": "innovator",
            "system_prompt": "你是一个创新思考者",
            "model_config": {}
        }
        
        response = requests.post(f"{API_BASE_URL}/agents/create", json=agent_payload)
        if response.status_code == 200:
            agent = response.json()
            print(f"   Agent创建成功！ID: {agent['id']}")
            return str(agent['id'])
        else:
            print(f"   Agent创建失败，HTTP状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return None
    except Exception as e:
        print(f"   创建Agent异常: {str(e)}")
        return None

def start_simple_debate(agent_id):
    """启动简单辩论"""
    try:
        print(f"\n4. 启动简单辩论...")
        debate_payload = {
            "topic": "测试Ollama连接",
            "agent_ids": [agent_id],
            "rounds": 1
        }
        
        response = requests.post(f"{API_BASE_URL}/debate/start", json=debate_payload)
        if response.status_code == 200:
            debate = response.json()
            session_id = debate.get('session_id')
            print(f"   辩论启动成功！Session ID: {session_id}")
            
            # 等待辩论完成
            print("   等待辩论完成...")
            time.sleep(10)  # 等待10秒
            
            # 获取辩论结果
            result_response = requests.get(f"{API_BASE_URL}/debate/{session_id}/result")
            if result_response.status_code == 200:
                result = result_response.json()
                
                # 检查结果
                history = result.get('history', [])
                if history and len(history) > 0:
                    first_response = history[0].get('content', '')
                    print(f"   Agent响应预览: {first_response[:100]}...")
                    
                    if "Failed to connect to Ollama" in first_response:
                        print("   ❌ Agent仍然无法连接到Ollama！")
                        return False
                    else:
                        print("   ✅ Agent成功连接到Ollama并返回响应！")
                        return True
                else:
                    print("   警告: 辩论历史为空")
                    return False
            else:
                print(f"   获取辩论结果失败，HTTP状态码: {result_response.status_code}")
                return False
        else:
            print(f"   启动辩论失败，HTTP状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"   启动辩论异常: {str(e)}")
        return False

def main():
    print("=== 辩论系统Ollama连接测试 ===")
    
    # 1. 测试Ollama直接连接
    if not test_ollama_connection():
        print("\n❌ 测试失败: 无法直接连接到Ollama服务器。")
        print("   请检查Ollama服务是否正在运行，以及配置的地址是否正确。")
        return False
    
    # 2. 创建测试Agent
    agent_id = create_test_agent()
    if not agent_id:
        print("\n❌ 测试失败: 无法创建测试Agent。")
        return False
    
    # 3. 启动简单辩论测试
    if start_simple_debate(agent_id):
        print("\n✅ 所有测试通过！Ollama连接配置已修复。")
        return True
    else:
        print("\n❌ 测试失败: Agent在辩论过程中无法连接到Ollama。")
        
        # 查看最近的辩论历史文件，了解具体错误
        try:
            import os
            debate_files = sorted([f for f in os.listdir('.') if f.startswith('debate_history_') and f.endswith('.json')], reverse=True)
            if debate_files:
                latest_file = debate_files[0]
                print(f"\n最近的辩论历史文件: {latest_file}")
                with open(latest_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    if history and 'rounds' in history and len(history['rounds']) > 0:
                        first_round = history['rounds'][0]
                        for item in first_round:
                            if 'content' in item and "Failed to connect" in item['content']:
                                print(f"   {item['agent_role']}错误: {item['content']}")
        except Exception as e:
            print(f"   读取辩论历史失败: {str(e)}")
            
        return False
    
if __name__ == "__main__":
    success = main()
    print("\n=== 测试完成 ===")
    exit(0 if success else 1)