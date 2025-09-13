import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from app.core.config import settings
from app.services.llm_service import LLMService
from agentscope.model import OllamaChatModel


class TestLLMServiceSimple(unittest.TestCase):
    def setUp(self):
        # 初始化LLM服务
        self.llm_service = LLMService()
    
    @patch('app.services.llm_service.OllamaChatModel')
    def test_ollama_model_creation(self, mock_ollama_chat_model):
        """测试LLM服务能否正确创建Ollama模型实例"""
        # 模拟OllamaChatModel的返回值
        mock_model = MagicMock()
        mock_ollama_chat_model.return_value = mock_model
        
        # 创建测试配置
        model_config = {
            "model_name": "gpt-oss:20b"
        }
        
        # 调用服务创建模型
        model = self.llm_service.get_model(model_config)
        
        # 验证OllamaChatModel被调用，并且传递了正确的参数
        mock_ollama_chat_model.assert_called_once()
        called_args, called_kwargs = mock_ollama_chat_model.call_args
        
        # 验证模型名称和主机配置正确
        self.assertEqual(called_kwargs["model_name"], "gpt-oss:20b")
        self.assertEqual(called_kwargs["host"], settings.OLLAMA_API_BASE)
        self.assertTrue(called_kwargs["stream"])
        
        # 验证返回的是模拟模型
        self.assertEqual(model, mock_model)
    
    @patch('app.services.llm_service.OllamaChatModel')
    def test_model_caching(self, mock_ollama_chat_model):
        """测试LLM服务是否正确缓存模型实例"""
        # 模拟OllamaChatModel的返回值
        mock_model = MagicMock()
        mock_ollama_chat_model.return_value = mock_model
        
        # 创建测试配置
        model_config = {
            "model_name": "gpt-oss:20b"
        }
        
        # 第一次调用get_model应该创建新实例
        model1 = self.llm_service.get_model(model_config)
        
        # 第二次调用get_model应该返回缓存的实例，而不是再次调用OllamaChatModel
        model2 = self.llm_service.get_model(model_config)
        
        # 验证OllamaChatModel只被调用了一次
        mock_ollama_chat_model.assert_called_once()
        
        # 验证两次返回的是同一个实例
        self.assertEqual(model1, model2)
    
    @patch('app.services.llm_service.OllamaChatModel')
    def test_custom_model_config(self, mock_ollama_chat_model):
        """测试LLM服务能否处理自定义模型配置"""
        # 模拟OllamaChatModel的返回值
        mock_model = MagicMock()
        mock_ollama_chat_model.return_value = mock_model
        
        # 创建带有自定义配置的测试配置
        model_config = {
            "model_name": "custom-model",
            "stream": False,
            "options": {"temperature": 0.7}
        }
        
        # 调用服务创建模型
        model = self.llm_service.get_model(model_config)
        
        # 验证OllamaChatModel被调用，并且传递了正确的自定义参数
        mock_ollama_chat_model.assert_called_once()
        called_args, called_kwargs = mock_ollama_chat_model.call_args
        
        # 验证模型名称正确
        self.assertEqual(called_kwargs["model_name"], "custom-model")
        
        # 验证主机配置正确
        self.assertEqual(called_kwargs["host"], settings.OLLAMA_API_BASE)
        
        # 验证返回的是模拟模型
        self.assertEqual(model, mock_model)


if __name__ == "__main__":
    unittest.main()