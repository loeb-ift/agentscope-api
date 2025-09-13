import unittest
import asyncio
from unittest.mock import patch, MagicMock
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块，但不导入LLMService
from app.core.config import settings


class TestOllamaConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 在类级别设置mock，确保在导入LLMService之前完成
        # 同时mock两个可能的导入路径
        cls.mock_patcher1 = patch('agentscope.model.OllamaChatModel')
        cls.mock_patcher2 = patch('app.services.llm_service.OllamaChatModel')
        
        # 启动两个mock
        cls.mock_ollama_chat_model1 = cls.mock_patcher1.start()
        cls.mock_ollama_chat_model2 = cls.mock_patcher2.start()
        
        # 创建一个共享的mock实例
        cls.mock_instance = MagicMock()
        cls.mock_ollama_chat_model1.return_value = cls.mock_instance
        cls.mock_ollama_chat_model2.return_value = cls.mock_instance
        
        # 创建一个组合的mock对象用于断言
        cls.mock_ollama_chat_model = cls._create_combined_mock()
    
    @classmethod
    def tearDownClass(cls):
        # 在类测试完成后停止所有mock
        cls.mock_patcher1.stop()
        cls.mock_patcher2.stop()
    
    @classmethod
    def _create_combined_mock(cls):
        """创建一个组合的mock对象，用于处理可能从不同路径调用的情况"""
        class CombinedMock:
            def __init__(self, mock1, mock2):
                self.mock1 = mock1
                self.mock2 = mock2
            
            def assert_called_once(self):
                # 检查任一mock是否被调用
                if self.mock1.call_count == 0 and self.mock2.call_count == 0:
                    raise AssertionError("Expected 'OllamaChatModel' to have been called once. Called 0 times.")
                elif self.mock1.call_count + self.mock2.call_count > 1:
                    raise AssertionError(f"Expected 'OllamaChatModel' to have been called once. Called {self.mock1.call_count + self.mock2.call_count} times.")
            
            def reset_mock(self):
                self.mock1.reset_mock()
                self.mock2.reset_mock()
            
            @property
            def call_args(self):
                # 返回第一个被调用的mock的call_args
                return self.mock1.call_args if self.mock1.call_count > 0 else self.mock2.call_args
        
        return CombinedMock(cls.mock_ollama_chat_model1, cls.mock_ollama_chat_model2)
    
    def setUp(self):
        # 创建Ollama模型配置
        self.ollama_config = {
            "model_name": settings.DEFAULT_MODEL_NAME,
            "api_base": settings.OLLAMA_API_BASE,
            "type": "ollama"
        }
        
        # 重置mock状态
        self.__class__.mock_ollama_chat_model.reset_mock()
        self.mock_model = self.__class__.mock_instance
    
    def test_create_ollama_model(self):
        """测试创建Ollama模型实例时正确传递配置"""
        # 在这里导入LLMService，确保在mock设置后导入
        from app.services.llm_service import LLMService
        
        # 初始化LLM服务
        llm_service = LLMService()
        
        # 调用服务创建模型
        model = llm_service._create_model_instance(self.ollama_config)
        
        # 验证OllamaChatModel被调用，并且传递了正确的参数
        self.__class__.mock_ollama_chat_model.assert_called_once()
        call_kwargs = self.__class__.mock_ollama_chat_model.call_args[1]
        
        # 验证模型名称正确
        self.assertEqual(call_kwargs["model_name"], settings.DEFAULT_MODEL_NAME)
        
        # 验证host参数是否从api_base获取
        self.assertEqual(call_kwargs["host"], settings.OLLAMA_API_BASE)
        
        # 验证返回的是模拟模型
        self.assertEqual(model, self.mock_model)
    
    def test_get_model_caches_ollama_model(self):
        """测试获取Ollama模型时会正确缓存实例"""
        # 在这里导入LLMService，确保在mock设置后导入
        from app.services.llm_service import LLMService
        
        # 初始化LLM服务
        llm_service = LLMService()
        
        # 第一次调用get_model应该创建新实例
        model1 = llm_service.get_model(self.ollama_config)
        
        # 第二次调用get_model应该返回缓存的实例，而不是再次调用OllamaChatModel
        model2 = llm_service.get_model(self.ollama_config)
        
        # 验证OllamaChatModel只被调用了一次
        self.__class__.mock_ollama_chat_model.assert_called_once()
        
        # 验证两次返回的是同一个实例
        self.assertEqual(model1, model2)
        self.assertEqual(model1, self.mock_model)
    
    def test_model_config_validation(self):
        """测试模型配置验证功能"""
        # 在这里导入LLMService，确保在mock设置后导入
        from app.services.llm_service import LLMService
        
        # 初始化LLM服务
        llm_service = LLMService()
        
        # 测试缺少model_name的情况
        with self.assertRaises(Exception) as context:
            llm_service.get_model({})
        
        # 验证异常包含正确的错误信息
        self.assertIn("模型配置中缺少model_name字段", str(context.exception))
    
    def test_model_with_custom_name(self):
        """测试使用自定义模型名称"""
        # 在这里导入LLMService，确保在mock设置后导入
        from app.services.llm_service import LLMService
        
        # 初始化LLM服务
        llm_service = LLMService()
        
        # 创建带有自定义模型名称的配置
        custom_config = self.ollama_config.copy()
        custom_config["model_name"] = "custom-ollama-model"
        
        # 调用服务创建模型
        model = llm_service._create_model_instance(custom_config)
        
        # 验证OllamaChatModel被调用，并且传递了正确的模型名称
        self.__class__.mock_ollama_chat_model.assert_called_once()
        call_kwargs = self.__class__.mock_ollama_chat_model.call_args[1]
        
        # 验证模型名称正确
        self.assertEqual(call_kwargs["model_name"], "custom-ollama-model")





if __name__ == "__main__":
    unittest.main()