# -*- coding: utf-8 -*-
"""单元测试 - 辩论管理器"""
from typing import List, Dict, Any, Optional
from unittest import TestCase
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime

from agentscope.agent import AgentBase
from app.utils.debate_manager import DebateManager
from app.services.llm_service import LLMService


class TestDebateManager(TestCase):
    """DebateManager的测试用例"""
    
    def setUp(self):
        """每个测试用例执行前的设置"""
        # 创建模拟的Agent实例
        self.mock_agent1 = AsyncMock(spec=AgentBase)
        self.mock_agent1.name = "专家1"
        self.mock_agent1.id = "agent1"
        self.mock_agent1.role = "正方"
        
        self.mock_agent2 = AsyncMock(spec=AgentBase)
        self.mock_agent2.name = "专家2"
        self.mock_agent2.id = "agent2"
        self.mock_agent2.role = "反方"
        
        self.agents = [self.mock_agent1, self.mock_agent2]
        self.topic = "人工智能对社会的影响"
        self.rounds = 2
        
        # 模拟数据库会话
        self.mock_db = Mock()
        self.debate_id = "debate123"
    
    @patch('app.utils.debate_manager.LLMService')
    def test_init(self, mock_llm_service_class):
        """测试辩论管理器的初始化"""
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds,
            db=self.mock_db,
            debate_id=self.debate_id
        )
        
        # 验证初始化参数
        self.assertEqual(debate_manager.agents, self.agents)
        self.assertEqual(debate_manager.topic, self.topic)
        self.assertEqual(debate_manager.rounds, self.rounds)
        self.assertEqual(debate_manager.db, self.mock_db)
        self.assertEqual(debate_manager.debate_id, self.debate_id)
        self.assertEqual(debate_manager.llm_service, mock_llm_service)
        self.assertEqual(debate_manager.conversation_history, [])
    
    @patch('app.utils.debate_manager.DebateService')
    @patch('app.utils.debate_manager.LLMService')
    async def test_run_debate_rounds(self, mock_llm_service_class, mock_debate_service_class):
        """测试执行辩论轮次功能"""
        # 设置模拟对象
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        
        mock_debate_service = Mock()
        mock_debate_service_class.return_value = mock_debate_service
        
        # 设置Agent响应
        self.mock_agent1.async_chat.return_value = "这是正方的观点"
        self.mock_agent2.async_chat.return_value = "这是反方的观点"
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds,
            db=self.mock_db,
            debate_id=self.debate_id
        )
        
        # 执行辩论轮次
        await debate_manager.run_debate_rounds()
        
        # 验证轮次执行次数
        self.assertEqual(len(debate_manager.conversation_history), self.rounds * len(self.agents))
        
        # 验证进度更新
        expected_progresses = [45, 90]  # (1/2)*90 和 (2/2)*90
        for i, expected_progress in enumerate(expected_progresses):
            mock_debate_service.update_debate_progress.assert_any_call(
                self.debate_id, expected_progress
            )
        
        # 验证保存消息
        self.assertEqual(mock_debate_service.save_debate_message.call_count, self.rounds * len(self.agents))
    
    @patch('app.utils.debate_manager.LLMService')
    async def test_get_agent_response(self, mock_llm_service_class):
        """测试获取Agent响应功能"""
        # 设置模拟对象
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        
        # 设置Agent响应
        expected_response = "这是测试响应"
        self.mock_agent1.async_chat.return_value = expected_response
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds
        )
        
        # 准备对话历史
        conversation_history = []
        round_num = 1
        
        # 获取Agent响应
        response = await debate_manager.get_agent_response(
            self.mock_agent1, self.topic, conversation_history, round_num
        )
        
        # 验证响应
        self.assertEqual(response, expected_response)
        self.mock_agent1.async_chat.assert_called_once()
        
        # 检查调用参数是否包含正确的提示信息
        call_args = self.mock_agent1.async_chat.call_args[0][0]
        self.assertIn(self.topic, call_args)
        self.assertIn("这是第一轮辩论，尚无历史记录", call_args)
    
    @patch('app.utils.debate_manager.LLMService')
    async def test_get_agent_response_with_history(self, mock_llm_service_class):
        """测试有对话历史时获取Agent响应"""
        # 设置模拟对象
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        
        # 设置Agent响应
        expected_response = "这是第二轮的响应"
        self.mock_agent1.async_chat.return_value = expected_response
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds
        )
        
        # 准备对话历史
        conversation_history = [{
            'agent': '专家2',
            'agent_id': 'agent2',
            'role': '反方',
            'round': 1,
            'response': '第一轮反方观点',
            'timestamp': datetime.now()
        }]
        round_num = 2
        
        # 获取Agent响应
        response = await debate_manager.get_agent_response(
            self.mock_agent1, self.topic, conversation_history, round_num
        )
        
        # 验证响应
        self.assertEqual(response, expected_response)
        
        # 检查调用参数是否包含对话历史
        call_args = self.mock_agent1.async_chat.call_args[0][0]
        self.assertIn("辩论历史", call_args)
        self.assertIn("[专家2 (第1轮)]: 第一轮反方观点", call_args)
    
    @patch('app.utils.debate_manager.LLMService')
    async def test_get_agent_response_error(self, mock_llm_service_class):
        """测试获取Agent响应出错时的处理"""
        # 设置模拟对象
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        
        # 设置Agent抛出异常
        error_message = "Agent响应失败"
        self.mock_agent1.async_chat.side_effect = Exception(error_message)
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds
        )
        
        # 获取Agent响应（应该处理异常）
        response = await debate_manager.get_agent_response(
            self.mock_agent1, self.topic, [], 1
        )
        
        # 验证响应包含错误信息
        self.assertIn("无法获取响应", response)
        self.assertIn(error_message, response)
    
    @patch('app.utils.debate_manager.LLMService')
    async def test_generate_conclusion(self, mock_llm_service_class):
        """测试生成辩论结论功能"""
        # 设置模拟对象
        mock_llm_service = AsyncMock()
        mock_llm_service.generate_structured_output.return_value = {
            "final_conclusion": "这是最终结论",
            "confidence_score": 0.85,
            "consensus_points": ["共识点1", "共识点2"],
            "divergent_views": ["分歧点1"],
            "key_arguments": {"正方": ["论点1"], "反方": ["论点2"]},
            "preliminary_insights": ["洞察1", "洞察2"]
        }
        mock_llm_service_class.return_value = mock_llm_service
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds
        )
        
        # 添加一些对话历史
        debate_manager.conversation_history = [{
            'agent': '专家1',
            'agent_id': 'agent1',
            'role': '正方',
            'round': 1,
            'response': '正方观点',
            'timestamp': datetime.now()
        }, {
            'agent': '专家2',
            'agent_id': 'agent2',
            'role': '反方',
            'round': 1,
            'response': '反方观点',
            'timestamp': datetime.now()
        }]
        
        # 生成结论
        conclusion = await debate_manager.generate_conclusion()
        
        # 验证结论
        self.assertEqual(conclusion["final_conclusion"], "这是最终结论")
        self.assertEqual(conclusion["confidence_score"], 0.85)
        self.assertEqual(conclusion["consensus_points"], ["共识点1", "共识点2"])
        self.assertEqual(conclusion["divergent_views"], ["分歧点1"])
        self.assertEqual(conclusion["key_arguments"], {"正方": ["论点1"], "反方": ["论点2"]})
        self.assertEqual(conclusion["preliminary_insights"], ["洞察1", "洞察2"])
        
        # 验证调用了LLM服务
        mock_llm_service.generate_structured_output.assert_called_once()
    
    @patch('app.utils.debate_manager.LLMService')
    async def test_generate_conclusion_error(self, mock_llm_service_class):
        """测试生成结论出错时的处理"""
        # 设置模拟对象
        mock_llm_service = AsyncMock()
        error_message = "结论生成失败"
        mock_llm_service.generate_structured_output.side_effect = Exception(error_message)
        mock_llm_service_class.return_value = mock_llm_service
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds
        )
        
        # 生成结论（应该处理异常）
        conclusion = await debate_manager.generate_conclusion()
        
        # 验证返回了错误结论
        self.assertIn("结论生成失败", conclusion["final_conclusion"])
        self.assertEqual(conclusion["confidence_score"], 0.0)
        self.assertEqual(conclusion["consensus_points"], [])
        self.assertEqual(conclusion["divergent_views"], [])
        self.assertEqual(conclusion["key_arguments"], {})
        self.assertEqual(conclusion["preliminary_insights"], [])
    
    @patch('app.utils.debate_manager.LLMService')
    def test_generate_history_summary(self, mock_llm_service_class):
        """测试生成辩论历史摘要功能"""
        # 设置模拟对象
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds
        )
        
        # 添加对话历史
        debate_manager.conversation_history = [{
            'agent': '专家1',
            'agent_id': 'agent1',
            'role': '正方',
            'round': 1,
            'response': '这是第一轮正方的观点，包含了很多详细的信息...',
            'timestamp': datetime.now()
        }, {
            'agent': '专家2',
            'agent_id': 'agent2',
            'role': '反方',
            'round': 1,
            'response': '这是第一轮反方的观点，也包含了很多详细的信息...',
            'timestamp': datetime.now()
        }, {
            'agent': '专家1',
            'agent_id': 'agent1',
            'role': '正方',
            'round': 2,
            'response': '这是第二轮正方的回应，针对反方的观点进行了反驳...',
            'timestamp': datetime.now()
        }]
        
        # 生成历史摘要
        summary = debate_manager._generate_history_summary()
        
        # 验证摘要内容
        self.assertIn("第1轮", summary)
        self.assertIn("第2轮", summary)
        self.assertIn("专家1", summary)
        self.assertIn("专家2", summary)
        # 验证内容被正确截断
        self.assertIn("这是第一轮正方的观点，包含了很多详细的信息...", summary)
    
    @patch('app.utils.debate_manager.LLMService')
    def test_get_conversation_history(self, mock_llm_service_class):
        """测试获取完整对话历史功能"""
        # 设置模拟对象
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds
        )
        
        # 添加对话历史
        expected_history = [{"key": "value"}]
        debate_manager.conversation_history = expected_history
        
        # 获取对话历史
        history = debate_manager.get_conversation_history()
        
        # 验证返回的历史
        self.assertEqual(history, expected_history)
    
    @patch('app.utils.debate_manager.LLMService')
    async def test_abort_debate(self, mock_llm_service_class):
        """测试中止辩论功能"""
        # 设置模拟对象
        mock_llm_service = Mock()
        mock_llm_service_class.return_value = mock_llm_service
        
        # 初始化辩论管理器
        debate_manager = DebateManager(
            agents=self.agents,
            topic=self.topic,
            rounds=self.rounds
        )
        
        # 中止辩论（应该不会抛出异常）
        await debate_manager.abort_debate()