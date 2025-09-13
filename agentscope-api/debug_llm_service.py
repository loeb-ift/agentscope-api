import os
import sys
import inspect

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
from app.core.config import settings
from app.services.llm_service import LLMService

# 打印LLMService._create_model_instance方法的源代码
print("LLMService._create_model_instance方法的源代码:")
print(inspect.getsource(LLMService._create_model_instance))
print("\n" + "="*50 + "\n")

# 创建LLM服务实例
llm_service = LLMService()

# 创建Ollama模型配置
ollama_config = {
    "model_name": settings.DEFAULT_MODEL_NAME,
    "api_base": settings.OLLAMA_API_BASE,
    "type": "ollama"
}

# 打印导入的模块
print("导入的agentscope.model模块内容:")
import agentscope.model
print(dir(agentscope.model))
print("\n" + "="*50 + "\n")

# 检查是否有OllamaChatModel类
print("agentscope.model中是否有OllamaChatModel类:")
print(hasattr(agentscope.model, "OllamaChatModel"))
if hasattr(agentscope.model, "OllamaChatModel"):
    print("OllamaChatModel的完整路径:", agentscope.model.OllamaChatModel.__module__ + "." + agentscope.model.OllamaChatModel.__name__)

print("\n" + "="*50 + "\n")

# 尝试使用LLMService创建模型
print("尝试使用LLMService创建模型:")
try:
    # 使用调试器跟踪执行
    import pdb
    pdb.set_trace()
    model = llm_service._create_model_instance(ollama_config)
    print("成功创建模型，模型类型:", type(model))
except Exception as e:
    print(f"创建模型时出错: {type(e).__name__}: {str(e)}")