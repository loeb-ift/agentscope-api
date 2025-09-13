import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 检查agentscope.model模块中的OllamaChatModel位置
import agentscope.model

print("agentscope.model模块的内容:")
print(dir(agentscope.model))
print()

if hasattr(agentscope.model, 'OllamaChatModel'):
    print("OllamaChatModel的完整路径:")
    ollama_chat_model = agentscope.model.OllamaChatModel
    print(f"模块: {ollama_chat_model.__module__}")
    print(f"名称: {ollama_chat_model.__name__}")
    print(f"完整引用路径: {ollama_chat_model.__module__}.{ollama_chat_model.__name__}")
    
    # 检查是否是直接导入还是从子模块导入的
    print("\n检查OllamaChatModel是否是从子模块导入的:")
    import inspect
    import agentscope.model._ollama_model
    print(f"agentscope.model.OllamaChatModel与agentscope.model._ollama_model.OllamaChatModel是否相同: {agentscope.model.OllamaChatModel is agentscope.model._ollama_model.OllamaChatModel}")

# 检查LLMService中OllamaChatModel的导入方式
print("\n检查LLMService中OllamaChatModel的导入方式:")
from app.services.llm_service import LLMService
import inspect
llm_service_source = inspect.getsource(LLMService._create_model_instance)
print(llm_service_source)