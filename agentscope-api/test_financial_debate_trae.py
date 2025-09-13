#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
金融分析师智能体辩论测试脚本
此脚本创建四个不同角色的金融分析师智能体并进行辩论测试
"""

import os
import sys
import time
import asyncio
from datetime import datetime
import uuid
import json

# 加载.env文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv is not installed. Using system environment variables.")

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from agentscope.agent import ReActAgent
from agentscope.model import OllamaChatModel
from agentscope.formatter import OllamaMultiAgentFormatter
from agentscope.message import Msg
from typing import List, Dict, Any, Optional

# 自定义DebateManager类，修复generate_conclusion方法
class DebateManager:
    def __init__(self, agents: List[Any], topic: str, rounds: int = 3, db=None, debate_id=None):
        self.agents = agents
        self.topic = topic
        self.rounds = rounds
        self.conversation_history = []
        self.db = db  # 数据库会话，用于保存辩论消息
        self.debate_id = debate_id  # 辩论ID
    
    async def run_debate_rounds(self):
        """执行辩论轮次"""
        for round_num in range(self.rounds):
            print(f"===== 辩论轮次 {round_num + 1}/{self.rounds} 开始 =====")
            
            # 每个Agent依次发言
            for agent in self.agents:
                # 获取Agent响应
                response = await self.get_agent_response(agent, self.topic, self.conversation_history, round_num + 1)
                
                # 记录响应
                self.conversation_history.append({
                    'agent': agent.name,
                    'agent_id': getattr(agent, 'id', str(hash(agent.name))),
                    'role': getattr(agent, 'role', 'unknown'),
                    'round': round_num + 1,
                    'response': response,
                    'timestamp': datetime.now()
                })
                
                print(f"[{agent.name}]\n{response}\n")
        
        print("===== 所有辩论轮次完成 =====")
    
    async def get_agent_response(self, agent: Any, topic: str, 
                               conversation_history: List[Dict[str, Any]], round_num: int) -> str:
        """获取Agent的响应"""
        # 构建对话历史字符串
        history_str = "\n".join([f"[{msg['agent']} (第{msg['round']}轮)]: {msg['response']}" 
                               for msg in conversation_history if msg['round'] < round_num])
        
        # 构建当前轮次的提示内容
        prompt_content = f"""当前辩论主题：{topic}

{"辩论历史：\n" + history_str if history_str else "这是第一轮辩论，尚无历史记录。"}

请以你当前的角色和立场，对辩论主题发表你的观点和论据。请确保你的发言与当前轮次相关，
并针对前面的讨论内容（如果有）进行回应。发言要简洁明了，重点突出。"""
        
        try:
            # 创建Msg对象传递给agent.reply()，添加缺少的'name'参数
            prompt_msg = Msg(role="user", name="user", content=prompt_content)
            response_msg = await agent.reply(prompt_msg)
            response = response_msg.get_text_content()
            
            # 处理响应，确保返回字符串
            if isinstance(response, str):
                return response
            elif hasattr(response, "text"):
                return response.text
            elif isinstance(response, dict) and "content" in response:
                return response["content"]
            else:
                return str(response)
        except Exception as e:
            # 处理错误，返回错误信息
            error_msg = f"获取Agent响应时发生错误: {str(e)}"
            print(error_msg)
            return f"[错误] 无法获取响应: {str(e)}"
    
    async def generate_conclusion(self) -> Dict[str, Any]:
        """基于辩论历史生成最终结论"""
        # 构建辩论历史摘要
        history_summary = self._generate_history_summary()
        
        # 准备结论生成的提示
        conclusion_prompt = f"""你是一位专业的辩论分析师，需要基于以下辩论内容生成一份全面的分析报告。

辩论主题：{self.topic}

辩论参与方：{', '.join([agent.name for agent in self.agents])}

辩论历史摘要：
{history_summary}

请生成一份结构化的分析报告，包含以下内容：
1. final_conclusion: 一个综合的最终结论，总结辩论的主要观点和共识
2. confidence_score: 结论的可信度分数（0.0-1.0）
3. consensus_points: 各方达成共识的要点列表
4. divergent_views: 各方存在分歧的观点列表
5. key_arguments: 按角色分类的关键论点字典
6. preliminary_insights: 从辩论中获得的初步洞察列表

请确保你的分析客观、全面，并基于实际辩论内容。"""
        
        try:
            # 使用第一个Agent的模型来生成结论
            if self.agents:
                # 从第一个Agent获取模型
                conclusion_model = self.agents[0].model
                
                # 构建消息
                messages = [
                    {"role": "system", "content": "你是一位专业的辩论分析师，擅长总结和分析多轮辩论。"},
                    {"role": "user", "content": conclusion_prompt}
                ]
                
                # 使用模型的__call__方法生成响应
                response = await conclusion_model(messages)
                
                # 尝试解析响应为JSON
                try:
                    # 获取文本内容，确保是字符串
                    response_text = response.content
                    if isinstance(response_text, list):
                        # 如果是列表，尝试获取第一个元素或转换为字符串
                        response_text = response_text[0] if response_text else ""
                    elif not isinstance(response_text, str):
                        response_text = str(response_text)
                    
                    # 尝试从响应中提取JSON部分
                    # 查找可能的JSON开始和结束位置
                    import re
                    json_match = re.search(r'```json\\n(.*?)\\n```', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        # 尝试直接解析整个响应
                        json_str = response_text
                    
                    conclusion_data = json.loads(json_str)
                    return conclusion_data
                except Exception as e:
                    # 如果解析失败，返回简单的结论，并包含原始响应的前200个字符以便调试
                    print(f"JSON解析失败: {str(e)}, 原始响应: {str(response_text)[:200]}...")
                    return {
                        "final_conclusion": "结论生成完成。由于JSON解析失败，无法提供详细结构化结论。",
                        "confidence_score": 0.8,
                        "consensus_points": ["辩论已完成"],
                        "divergent_views": [],
                        "key_arguments": {},
                        "preliminary_insights": []
                    }
            else:
                return {
                    "final_conclusion": "没有参与辩论的智能体，无法生成结论。",
                    "confidence_score": 0.0,
                    "consensus_points": [],
                    "divergent_views": [],
                    "key_arguments": {},
                    "preliminary_insights": []
                }
        except Exception as e:
            # 处理错误，返回默认结论
            error_msg = f"生成结论时发生错误: {str(e)}"
            print(error_msg)
            return {
                "final_conclusion": f"结论生成失败: {str(e)}",
                "confidence_score": 0.0,
                "consensus_points": [],
                "divergent_views": [],
                "key_arguments": {},
                "preliminary_insights": []
            }
    
    def _generate_history_summary(self) -> str:
        """生成辩论历史摘要"""
        # 按轮次分组对话历史
        round_history = {}
        for msg in self.conversation_history:
            round_num = msg["round"]
            if round_num not in round_history:
                round_history[round_num] = []
            round_history[round_num].append(msg)
        
        # 生成摘要
        summary_parts = []
        for round_num in sorted(round_history.keys()):
            summary_parts.append(f"第{round_num}轮辩论:")
            for msg in round_history[round_num]:
                summary_parts.append(f"- {msg['agent']}: {msg['response'][:100]}...")
            summary_parts.append("")  # 空行分隔
        
        return "\n".join(summary_parts)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取完整的对话历史"""
        return self.conversation_history
    
    def abort_debate(self):
        """中止辩论"""
        # 实现中止逻辑（如果需要）
        pass


class FinancialDebateTester:
    def __init__(self):
        # 从环境变量获取Ollama配置
        self.ollama_api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        self.default_model_name = os.getenv("DEFAULT_MODEL_NAME", "gpt-oss:20b")
        
        # 设置辩论主题
        self.debate_topic = "2024年全球经济展望与投资策略"
        
        # 设置辩论轮次
        self.debate_rounds = 3
        
        # 四个金融分析师的配置
        self.financial_analysts = [
            {
                "name": "宏观经济分析师",
                "role": "macro_analyst",
                "role_description": "专注于全球宏观经济趋势分析的专家，擅长解读政策变化和经济指标对市场的影响",
                "system_prompt": "你是一位资深的宏观经济分析师，拥有15年的全球经济研究经验。你擅长分析全球经济趋势、货币政策、财政政策以及地缘政治事件对经济的影响。",
                "expertise_areas": ["宏观经济", "货币政策", "财政政策", "地缘政治"]
            },
            {
                "name": "股票策略分析师",
                "role": "equity_strategist",
                "role_description": "专注于股票市场策略研究的专家，擅长行业分析和投资组合配置",
                "system_prompt": "你是一位资深的股票策略分析师，拥有12年的股票市场研究经验。你擅长分析不同行业的发展趋势、评估企业基本面，并提供股票投资组合配置建议。",
                "expertise_areas": ["股票市场", "行业分析", "企业基本面", "投资组合配置"]
            },
            {
                "name": "固定收益分析师",
                "role": "fixed_income_analyst",
                "role_description": "专注于债券和固定收益产品分析的专家，擅长利率分析和信用风险评估",
                "system_prompt": "你是一位资深的固定收益分析师，拥有10年的债券市场研究经验。你擅长分析利率走势、信用风险评估以及各类固定收益产品的投资价值。",
                "expertise_areas": ["债券市场", "利率分析", "信用风险", "固定收益产品"]
            },
            {
                "name": "另类投资分析师",
                "role": "alternative_investment_analyst",
                "role_description": "专注于另类投资领域的专家，擅长房地产、私募股权、对冲基金等非传统投资产品的分析",
                "system_prompt": "你是一位资深的另类投资分析师，拥有8年的另类投资研究经验。你擅长分析房地产、私募股权、对冲基金、大宗商品等非传统投资产品的风险收益特征。",
                "expertise_areas": ["房地产", "私募股权", "对冲基金", "大宗商品"]
            }
        ]
        
        # 创建的Agent实例列表
        self.agents = []
        
        # 辩论管理器
        self.debate_manager = None

    def create_agent(self, analyst_config):
        """创建单个金融分析师智能体"""
        # 创建OllamaChatModel实例
        model = OllamaChatModel(
            model_name=self.default_model_name,
            host=self.ollama_api_base,
            stream=False,
            options={
                "temperature": 0.7,
                "max_tokens": 1024
            }
        )
        
        # 生成辩论专用的系统提示
        debate_system_prompt = self._generate_debate_system_prompt(analyst_config)
        
        # 创建ReActAgent实例
        agent = ReActAgent(
            name=analyst_config["name"],
            sys_prompt=debate_system_prompt,
            model=model,
            formatter=OllamaMultiAgentFormatter()
        )
        
        # 添加额外属性
        agent.role = analyst_config["role"]
        agent.role_description = analyst_config["role_description"]
        agent.expertise_areas = analyst_config["expertise_areas"]
        
        return agent
    
    def _generate_debate_system_prompt(self, analyst_config):
        """生成辩论专用的系统提示"""
        prompt_template = f"""{analyst_config['system_prompt']}

# 当前辩论任务
你现在需要以{analyst_config['role_description']}的身份参与一场辩论。
辩论主题：{self.debate_topic}

# 辩论角色
你的角色是：{analyst_config['name']} - {analyst_config['role_description']}

# 辩论要求
1. 请基于你的专业领域和知识，对辩论主题发表专业观点
2. 请提供具体的数据、案例和分析支持你的观点
3. 请针对其他参与者的观点进行专业回应和讨论
4. 请保持专业、客观的态度，避免情绪化表达
5. 请确保你的发言简洁明了，重点突出
6. 请关注辩论的核心问题，避免偏离主题
"""
        
        return prompt_template
    
    def setup_debate(self):
        """设置辩论环境，创建所有智能体"""
        print("===== 设置金融分析师辩论环境 =====")
        
        # 创建四个金融分析师智能体
        for analyst_config in self.financial_analysts:
            print(f"创建智能体: {analyst_config['name']}")
            agent = self.create_agent(analyst_config)
            self.agents.append(agent)
        
        # 创建辩论管理器
        self.debate_manager = DebateManager(
            agents=self.agents,
            topic=self.debate_topic,
            rounds=self.debate_rounds,
            debate_id=str(uuid.uuid4())  # 生成唯一的辩论ID
        )
        
        print(f"\n辩论主题: {self.debate_topic}")
        print(f"参与智能体数量: {len(self.agents)}")
        print(f"辩论轮次: {self.debate_rounds}")
        print("===== 辩论环境设置完成 =====")
    
    async def run_debate(self):
        """运行辩论"""
        if not self.debate_manager:
            raise ValueError("辩论管理器未初始化，请先调用setup_debate()")
        
        print("\n===== 开始金融分析师辩论 =====")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行辩论轮次
        await self.debate_manager.run_debate_rounds()
        
        # 生成结论
        print("\n===== 生成辩论结论 =====")
        conclusion_data = await self.debate_manager.generate_conclusion()
        
        # 记录结束时间
        end_time = time.time()
        
        print(f"\n===== 辩论完成 =====")
        print(f"总耗时: {end_time - start_time:.2f}秒")
        
        # 打印结论
        self.print_conclusion(conclusion_data)
        
        # 返回辩论结果
        return {
            "topic": self.debate_topic,
            "rounds": self.debate_rounds,
            "participants": [agent.name for agent in self.agents],
            "duration_seconds": end_time - start_time,
            "conclusion": conclusion_data,
            "conversation_history": self.debate_manager.get_conversation_history()
        }
    
    def print_conclusion(self, conclusion_data):
        """打印辩论结论"""
        print("\n===== 辩论结论摘要 =====")
        print(f"最终结论: {conclusion_data.get('final_conclusion', '无')}")
        print(f"可信度分数: {conclusion_data.get('confidence_score', 0.0)}")
        
        print("\n共识要点:")
        for i, point in enumerate(conclusion_data.get('consensus_points', []), 1):
            print(f"{i}. {point}")
        
        print("\n分歧观点:")
        for i, point in enumerate(conclusion_data.get('divergent_views', []), 1):
            print(f"{i}. {point}")
        
        print("\n===== 辩论结论结束 =====")
    
    def save_debate_history(self, debate_result, filename=None):
        """保存辩论历史到文件"""
        import json
        
        if filename is None:
            # 生成包含时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debate_history_{timestamp}.json"
        
        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            # 自定义JSON编码器，处理datetime对象
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return super().default(obj)
            
            json.dump(debate_result, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        print(f"\n辩论历史已保存到: {filename}")
        return filename


async def main():
    """主函数"""
    print("===== 金融分析师智能体辩论测试工具 =====")
    
    try:
        # 创建辩论测试器
        debate_tester = FinancialDebateTester()
        
        # 设置辩论环境
        debate_tester.setup_debate()
        
        # 运行辩论
        debate_result = await debate_tester.run_debate()
        
        # 保存辩论历史
        saved_file = debate_tester.save_debate_history(debate_result)
        
        print(f"\n✅ 辩论测试成功完成！")
        print(f"详细辩论记录请查看文件: {saved_file}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 辩论测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 辩论测试失败！发生错误: {str(e)}")
        
        # 输出详细错误信息，便于调试
        import traceback
        traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    # 运行主函数
    exit_code = asyncio.run(main())
    sys.exit(exit_code)