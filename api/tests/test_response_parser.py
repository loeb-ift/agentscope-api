import unittest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List, Optional

# 导入被测试的类和相关模块
from app.utils.response_parser import ResponseParser
from app.models.schemas import N8NOptimizedResponse


class TestResponseParser(unittest.TestCase):
    def setUp(self):
        # 准备测试数据
        self.session_id = "test-session-123"
        self.conversation_history = [
            {
                "role": "expert",
                "agent": "EconomistAgent",
                "response": "我认为经济复苏将持续到明年",
                "round": 1,
                "timestamp": datetime(2023, 1, 1, 10, 0, 0)
            },
            {
                "role": "skeptic",
                "agent": "CriticalAgent",
                "response": "我对这个观点持保留态度，存在下行风险",
                "round": 1,
                "timestamp": datetime(2023, 1, 1, 10, 5, 0)
            },
            {
                "role": "expert",
                "agent": "EconomistAgent",
                "response": "最新数据支持我的乐观预测",
                "round": 2,
                "timestamp": datetime(2023, 1, 1, 10, 10, 0)
            }
        ]
        
        self.preliminary_insights = [
            "专家认为经济将持续复苏",
            "批评者指出存在下行风险"
        ]
        
        self.final_conclusion = "综合各方观点，经济复苏大概率将持续，但需警惕潜在风险"
        
        self.key_arguments = {
            "expert": ["经济复苏将持续到明年", "最新数据支持乐观预测"],
            "skeptic": ["存在下行风险"]
        }
        
        self.consensus_points = ["经济正在复苏", "存在一定不确定性"]
        self.divergent_views = ["复苏力度和持续性存在分歧"]
    
    def test_parse_debate_result_to_n8n_format(self):
        """测试将辩论结果解析为n8n优化的响应格式"""
        result = ResponseParser.parse_debate_result_to_n8n_format(
            session_id=self.session_id,
            status="completed",
            progress=1.0,
            preliminary_insights=self.preliminary_insights,
            final_conclusion=self.final_conclusion,
            key_arguments=self.key_arguments,
            consensus_points=self.consensus_points,
            divergent_views=self.divergent_views,
            confidence_score=0.85
        )
        
        # 验证返回类型
        self.assertIsInstance(result, N8NOptimizedResponse)
        
        # 验证所有字段都被正确设置
        self.assertEqual(result.session_id, self.session_id)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.progress, 1.0)
        self.assertEqual(result.preliminary_insights, self.preliminary_insights)
        self.assertEqual(result.final_conclusion, self.final_conclusion)
        self.assertEqual(result.key_arguments, self.key_arguments)
        self.assertEqual(result.consensus_points, self.consensus_points)
        self.assertEqual(result.divergent_views, self.divergent_views)
        self.assertEqual(result.confidence_score, 0.85)
    
    def test_parse_debate_result_with_minimal_params(self):
        """测试使用最小参数集解析辩论结果"""
        result = ResponseParser.parse_debate_result_to_n8n_format(
            session_id=self.session_id,
            status="running",
            progress=0.5,
            preliminary_insights=[]
        )
        
        # 验证必填字段和默认值
        self.assertEqual(result.session_id, self.session_id)
        self.assertEqual(result.status, "running")
        self.assertEqual(result.progress, 0.5)
        self.assertEqual(result.preliminary_insights, [])
        self.assertIsNone(result.final_conclusion)
        self.assertEqual(result.key_arguments, {})
        self.assertEqual(result.consensus_points, [])
        self.assertEqual(result.divergent_views, [])
        self.assertEqual(result.confidence_score, 0.0)
    
    def test_format_error_response(self):
        """测试格式化错误响应"""
        # 测试带错误码的情况
        error_response = ResponseParser.format_error_response(
            detail="API调用失败", 
            error_code="API_ERROR"
        )
        
        self.assertEqual(error_response["detail"], "API调用失败")
        self.assertEqual(error_response["error_code"], "API_ERROR")
        self.assertTrue("timestamp" in error_response)
        
        # 测试不带错误码的情况
        error_response_no_code = ResponseParser.format_error_response(
            detail="未知错误"
        )
        
        self.assertEqual(error_response_no_code["detail"], "未知错误")
        self.assertTrue("timestamp" in error_response_no_code)
        self.assertTrue("error_code" not in error_response_no_code)
    
    def test_extract_key_arguments_by_role(self):
        """测试从对话历史中提取按角色分类的关键论点"""
        result = ResponseParser.extract_key_arguments_by_role(self.conversation_history)
        
        # 验证结果包含所有角色
        self.assertIn("expert", result)
        self.assertIn("skeptic", result)
        
        # 验证每个角色的论点数量
        self.assertEqual(len(result["expert"]), 2)
        self.assertEqual(len(result["skeptic"]), 1)
        
        # 验证论点内容
        self.assertIn("我认为经济复苏将持续到明年", result["expert"])
        self.assertIn("最新数据支持我的乐观预测", result["expert"])
        self.assertIn("我对这个观点持保留态度，存在下行风险", result["skeptic"])
    
    def test_extract_preliminary_insights(self):
        """测试从对话历史中提取初步洞察"""
        result = ResponseParser.extract_preliminary_insights(self.conversation_history)
        
        # 验证结果数量（默认最多5个）
        self.assertEqual(len(result), 2)  # 因为只有2轮对话
        
        # 验证洞察内容格式
        self.assertIn("第1轮参与讨论的Agent", result[0])
        self.assertIn("第2轮参与讨论的Agent", result[1])
        self.assertIn("EconomistAgent", result[0])
        self.assertIn("CriticalAgent", result[0])
        self.assertIn("EconomistAgent", result[1])
        
        # 测试限制最大洞察数量
        result_limited = ResponseParser.extract_preliminary_insights(self.conversation_history, max_insights=1)
        self.assertEqual(len(result_limited), 1)
    
    def test_format_conversation_history_for_display(self):
        """测试格式化对话历史以便显示"""
        result = ResponseParser.format_conversation_history_for_display(self.conversation_history)
        
        # 验证结果数量与输入相同
        self.assertEqual(len(result), len(self.conversation_history))
        
        # 验证每个消息都包含必要字段
        for msg in result:
            self.assertIn("agent_name", msg)
            self.assertIn("agent_role", msg)
            self.assertIn("round", msg)
            self.assertIn("content", msg)
            self.assertIn("timestamp", msg)
        
        # 验证具体内容
        self.assertEqual(result[0]["agent_name"], "EconomistAgent")
        self.assertEqual(result[0]["agent_role"], "expert")
        self.assertEqual(result[0]["round"], 1)
        self.assertEqual(result[0]["content"], "我认为经济复苏将持续到明年")
    
    def test_validate_response_format(self):
        """测试验证响应格式是否符合预期"""
        # 测试JSON格式验证
        self.assertTrue(ResponseParser.validate_response_format({"key": "value"}, "json"))
        self.assertFalse(ResponseParser.validate_response_format(["item"], "json"))
        
        # 测试列表格式验证
        self.assertTrue(ResponseParser.validate_response_format(["item"], "list"))
        self.assertFalse(ResponseParser.validate_response_format({"key": "value"}, "list"))
        
        # 测试字符串格式验证
        self.assertTrue(ResponseParser.validate_response_format("test string", "string"))
        self.assertFalse(ResponseParser.validate_response_format(123, "string"))
        
        # 测试不支持的格式
        self.assertFalse(ResponseParser.validate_response_format({"key": "value"}, "unknown_format"))
        
        # 测试大小写不敏感
        self.assertTrue(ResponseParser.validate_response_format({"key": "value"}, "JSON"))
        self.assertTrue(ResponseParser.validate_response_format({"key": "value"}, "Json"))
    
    def test_sanitize_response_data(self):
        """测试清理响应数据，移除敏感信息"""
        # 创建包含敏感信息的测试数据
        sensitive_data = {
            "api_key": "secret-api-key",
            "token": "secret-token",
            "password": "secret-password",
            "auth_token": "secret-auth-token",
            "normal_field": "normal_value",
            "nested": {
                "secret_key": "nested-secret",
                "safe_field": "safe-value"
            },
            "list_with_secrets": [
                {"api_key": "list-api-key", "name": "item1"},
                {"safe": "value", "password_hash": "hash"}
            ]
        }
        
        # 清理数据
        sanitized = ResponseParser.sanitize_response_data(sensitive_data)
        
        # 验证敏感字段已被移除
        self.assertFalse("api_key" in sanitized)
        self.assertFalse("token" in sanitized)
        self.assertFalse("password" in sanitized)
        self.assertFalse("auth_token" in sanitized)
        
        # 验证正常字段保留
        self.assertEqual(sanitized["normal_field"], "normal_value")
        
        # 验证嵌套结构中的敏感字段已被移除
        self.assertFalse("secret_key" in sanitized["nested"])
        self.assertEqual(sanitized["nested"]["safe_field"], "safe-value")
        
        # 验证列表中的敏感字段已被移除
        self.assertEqual(len(sanitized["list_with_secrets"]), 2)
        self.assertFalse("api_key" in sanitized["list_with_secrets"][0])
        self.assertEqual(sanitized["list_with_secrets"][0]["name"], "item1")
        self.assertFalse("password_hash" in sanitized["list_with_secrets"][1])
        self.assertEqual(sanitized["list_with_secrets"][1]["safe"], "value")
    
    def test_is_sensitive_key(self):
        """测试检查键是否包含敏感信息"""
        # 测试敏感键
        self.assertTrue(ResponseParser._is_sensitive_key("api_key"))
        self.assertTrue(ResponseParser._is_sensitive_key("API_KEY"))  # 大小写不敏感
        self.assertTrue(ResponseParser._is_sensitive_key("auth_token"))
        self.assertTrue(ResponseParser._is_sensitive_key("user_password"))
        self.assertTrue(ResponseParser._is_sensitive_key("client_secret"))
        
        # 测试非敏感键
        self.assertFalse(ResponseParser._is_sensitive_key("name"))
        self.assertFalse(ResponseParser._is_sensitive_key("email"))
        self.assertFalse(ResponseParser._is_sensitive_key("address"))
        self.assertFalse(ResponseParser._is_sensitive_key("phone"))


if __name__ == "__main__":
    unittest.main()