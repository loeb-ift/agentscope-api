import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from app.core.config import settings
from agentscope.model import OllamaChatModel


class TestOllamaDirect(unittest.TestCase):
    def setUp(self):
        # Ollama模型配置
        self.model_name = settings.DEFAULT_MODEL_NAME
        self.api_base = settings.OLLAMA_API_BASE
        
    @patch('agentscope.model._ollama_model.requests.post')
    def test_ollama_model_initialization(self, mock_post):
        """测试OllamaChatModel的初始化"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": self.model_name,
            "created_at": "2024-01-01T00:00:00.000000Z",
            "response": "Hello, I'm your assistant!",
            "done": True
        }
        mock_post.return_value = mock_response
        
        # 直接初始化OllamaChatModel
        model = OllamaChatModel(
            model_name=self.model_name,
            host=self.api_base
        )
        
        # 驗證模型實例建立成功
        self.assertIsInstance(model, OllamaChatModel)
        self.assertEqual(model.model_name, self.model_name)
        
        # 测试一个简单的对话
        response = model.chat([{"role": "user", "content": "Hello!"}])
        
        # 验证请求是否正确发送
        mock_post.assert_called_once()
        
        # 验证响应
        self.assertTrue(hasattr(response, 'content'))
    
    @patch('agentscope.model._ollama_model.requests.post')
    def test_ollama_model_with_custom_config(self, mock_post):
        """测试使用自定义配置初始化OllamaChatModel"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "custom-model",
            "created_at": "2024-01-01T00:00:00.000000Z",
            "response": "Custom response",
            "done": True
        }
        mock_post.return_value = mock_response
        
        # 使用自定义配置初始化
        model = OllamaChatModel(
            model_name="custom-model",
            host=self.api_base,
            stream=False,
            options={"temperature": 0.7}
        )
        
        # 验证配置是否正确应用
        self.assertEqual(model.model_name, "custom-model")
        
        # 测试对话
        response = model.chat([{"role": "user", "content": "Hello!"}])
        
        # 验证请求是否正确发送
        mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()