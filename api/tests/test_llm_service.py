# -*- coding: utf-8 -*-
"""单元测试 - LLM服务"""
from typing import Dict, Any, Optional
from unittest import TestCase
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from fastapi import HTTPException

from app.services.llm_service import LLMService


class TestLLMService(TestCase):
    """LLMService的测试用例"""
    
    def setUp(self):
        """每个测试用例执行前的设置"""
        self.llm_service = LLMService()
    
    @patch('app.services.llm_service.agentscope.model.create_model')
    def test_get_model_from_cache(self, mock_create_model):
        """測試從快取中取得模型實例"""
        # 準備模擬資料
        mock_model = Mock()
        mock_create_model.return_value = mock_model
        
        model_config = {
            "model_name": "gpt-4",
            "api_key": "test_key"
        }
        
        # 第一次调用，应该创建模型
        model1 = self.llm_service.get_model(model_config)
        self.assertEqual(model1, mock_model)
        mock_create_model.assert_called_once()
        
        # 重置mock
        mock_create_model.reset_mock()
        
        # 第二次调用相同配置，应该从缓存获取，不应该再次创建
        model2 = self.llm_service.get_model(model_config)
        self.assertEqual(model2, mock_model)
        mock_create_model.assert_not_called()
    
    @patch('app.services.llm_service.agentscope.model.create_model')
    def test_get_model_missing_name(self, mock_create_model):
        """测试缺少模型名称时的错误处理"""
        model_config = {
            "api_key": "test_key"
        }
        
        with self.assertRaises(HTTPException) as context:
            self.llm_service.get_model(model_config)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "模型配置中缺少model_name字段")
        mock_create_model.assert_not_called()
    
    @patch('app.services.llm_service.agentscope.model.create_model')
    def test_get_model_create_error(self, mock_create_model):
        """测试创建模型失败时的错误处理"""
        mock_create_model.side_effect = Exception("创建模型失败")
        
        model_config = {
            "model_name": "gpt-4",
            "api_key": "test_key"
        }
        
        with self.assertRaises(HTTPException) as context:
            self.llm_service.get_model(model_config)
        
        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("建立模型實例失敗", context.exception.detail)
    
    @patch('app.services.llm_service.LLMService.get_model')
    def test_generate_text(self, mock_get_model):
        """测试文本生成功能"""
        # 准备模拟数据
        mock_model = AsyncMock()
        mock_model.async_generate_response.return_value = "这是生成的文本响应"
        mock_get_model.return_value = mock_model
        
        model_config = {
            "model_name": "gpt-4",
            "api_key": "test_key"
        }
        prompt = "请解释什么是人工智能"
        
        # 执行异步测试
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            self.llm_service.generate_text(model_config, prompt)
        )
        
        # 验证结果
        self.assertEqual(result, "这是生成的文本响应")
        mock_get_model.assert_called_once_with(model_config)
        mock_model.async_generate_response.assert_called_once()
    
    @patch('app.services.llm_service.LLMService.get_model')
    def test_generate_text_with_system_prompt(self, mock_get_model):
        """测试带系统提示的文本生成功能"""
        # 准备模拟数据
        mock_model = AsyncMock()
        mock_model.async_generate_response.return_value = "这是生成的文本响应"
        mock_get_model.return_value = mock_model
        
        model_config = {
            "model_name": "gpt-4",
            "api_key": "test_key"
        }
        prompt = "请解释什么是人工智能"
        system_prompt = "你是一个AI专家"
        
        # 执行异步测试
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self.llm_service.generate_text(model_config, prompt, system_prompt)
        )
        
        # 验证是否正确传递了系统提示
        mock_model.async_generate_response.assert_called_once()
        messages = mock_model.async_generate_response.call_args[0][0]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], system_prompt)
    
    @patch('app.services.llm_service.LLMService.get_model')
    def test_generate_text_error(self, mock_get_model):
        """测试文本生成失败时的错误处理"""
        # 准备模拟数据
        mock_model = AsyncMock()
        mock_model.async_generate_response.side_effect = Exception("生成失败")
        mock_get_model.return_value = mock_model
        
        model_config = {
            "model_name": "gpt-4",
            "api_key": "test_key"
        }
        prompt = "请解释什么是人工智能"
        
        # 执行异步测试并验证异常
        loop = asyncio.get_event_loop()
        with self.assertRaises(HTTPException) as context:
            loop.run_until_complete(
                self.llm_service.generate_text(model_config, prompt)
            )
        
        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("文本生成失败", context.exception.detail)
    
    @patch('app.services.llm_service.LLMService.get_model')
    def test_generate_structured_output(self, mock_get_model):
        """测试结构化输出生成功能"""
        # 准备模拟数据
        mock_model = AsyncMock()
        mock_model.async_generate_response.return_value = {"result": "结构化数据"}
        mock_get_model.return_value = mock_model
        
        model_config = {
            "model_name": "gpt-4",
            "api_key": "test_key"
        }
        prompt = "請以結構化格式返回結果"
        response_format = dict  # 這裡簡化處理，實際應該是Pydantic模型
        
        # 执行异步测试
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            self.llm_service.generate_structured_output(
                model_config, prompt, response_format
            )
        )
        
        # 验证结果
        self.assertEqual(result, {"result": "结构化数据"})
        mock_get_model.assert_called_once_with(model_config)
        mock_model.async_generate_response.assert_called_once()
    
    def test_validate_model_config(self):
        """测试模型配置验证功能"""
        # 有效的配置
        valid_config = {
            "model_name": "gpt-4",
            "api_key": "test_key"
        }
        self.assertTrue(self.llm_service.validate_model_config(valid_config))
        
        # 无效的配置（缺少model_name）
        invalid_config = {
            "api_key": "test_key"
        }
        self.assertFalse(self.llm_service.validate_model_config(invalid_config))
    
    @patch('app.services.llm_service.agentscope.model.create_model')
    def test_clear_model_cache(self, mock_create_model):
        """测试清除模型缓存功能"""
        # 准备模拟数据
        mock_model1 = Mock()
        mock_model2 = Mock()
        mock_create_model.side_effect = [mock_model1, mock_model2]
        
        # 创建两个不同的模型
        config1 = {"model_name": "gpt-4", "api_key": "key1"}
        config2 = {"model_name": "gpt-3.5-turbo", "api_key": "key2"}
        
        model1 = self.llm_service.get_model(config1)
        model2 = self.llm_service.get_model(config2)
        
        # 验证缓存中有两个模型
        self.assertEqual(len(self.llm_service.models_cache), 2)
        
        # 清除特定模型的缓存
        self.llm_service.clear_model_cache("gpt-4")
        
        # 验证只清除了指定模型的缓存
        self.assertEqual(len(self.llm_service.models_cache), 1)
        
        # 清除所有缓存
        self.llm_service.clear_model_cache()
        
        # 验证所有缓存都被清除
        self.assertEqual(len(self.llm_service.models_cache), 0)