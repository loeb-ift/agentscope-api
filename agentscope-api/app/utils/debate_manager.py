from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from agentscope.agent import AgentBase
from agentscope.message import Msg
from app.services.llm_service import LLMService
from app.core.config import settings

class DebateManager:
    def __init__(self, agents: List[AgentBase], topic: str, rounds: int = 3, db=None, debate_id=None):
        self.agents = agents
        self.topic = topic
        self.rounds = rounds
        self.conversation_history = []
        self.db = db  # 数据库会话，用于保存辩论消息
        self.debate_id = debate_id  # 辩论ID
        self.llm_service = LLMService()
    
    async def run_debate_rounds(self):
        """执行辩论轮次"""
        for round_num in range(self.rounds):
            # 更新进度
            progress = ((round_num + 1) / self.rounds) * 90  # 预留10%给结论生成
            if self.db and self.debate_id:
                from app.services.debate_service import DebateService
                debate_service = DebateService(self.db)
                debate_service.update_debate_progress(self.debate_id, progress)
            
            # 轮次开始通知
            print(f"===== 辩论轮次 {round_num + 1}/{self.rounds} 开始 =====")
            
            # 随机打乱Agent顺序（可选，增加辩论的多样性）
            # import random
            # random.shuffle(self.agents)
            
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
                
                # 保存到数据库
                if self.db and self.debate_id:
                    from app.services.debate_service import DebateService
                    debate_service = DebateService(self.db)
                    debate_service.save_debate_message(
                        debate_id=self.debate_id,
                        agent_id=getattr(agent, 'id', str(hash(agent.name))),
                        agent_name=agent.name,
                        agent_role=getattr(agent, 'role', 'unknown'),
                        round_number=round_num + 1,
                        content=response
                    )
                
                print(f"[{agent.name}]\n{response}\n")
            
            # 轮次间隔（可选，给用户时间阅读）
            # await asyncio.sleep(1)  # 1秒间隔
        
        print("===== 所有辩论轮次完成 =====")
    
    async def get_agent_response(self, agent: AgentBase, topic: str, 
                               conversation_history: List[Dict[str, Any]], round_num: int) -> str:
        """获取Agent的响应"""
        try:
            # 构建对话历史消息列表
            history_msgs = []
            for msg in conversation_history:
                if msg['round'] < round_num:
                    # 将字典转换为Msg对象
                    history_msg = Msg(
                        name=msg['agent'],
                        role="user",  # 在AgentScope中，用户消息使用user角色
                        content=msg['response'],
                        timestamp=msg['timestamp']
                    )
                    history_msgs.append(history_msg)
            
            # 构建当前轮次的提示作为Msg对象
            prompt_msg = Msg(
                name="system",
                role="system",
                content=f"""当前辩论主题：{topic}

请以你当前的角色和立场，对辩论主题发表你的观点和论据。请确保你的发言与当前轮次相关，
并针对前面的讨论内容（如果有）进行回应。发言要简洁明了，重点突出。""",
                timestamp=datetime.now()
            )
            
            # 创建完整的消息列表（历史消息 + 当前提示）
            input_msgs = history_msgs + [prompt_msg]
            
            # 使用AgentScope的Agent进行对话，传入完整的消息列表
            response = await agent.reply(input_msgs)
            
            # 增强的响应处理逻辑，确保返回有效的字符串
            if response is None:
                return "[无响应] Agent未返回任何内容"
            
            # 处理不同类型的响应
            if isinstance(response, str):
                return response.strip()
            elif isinstance(response, Msg):
                # 对于Msg对象，直接获取content字段
                if hasattr(response, "content") and response.content is not None:
                    return str(response.content).strip()
                else:
                    return "[响应格式错误] Msg对象缺少content字段"
            elif hasattr(response, "get_text_content"):
                try:
                    text_content = response.get_text_content()
                    if isinstance(text_content, str):
                        return text_content.strip()
                    else:
                        return str(text_content).strip()
                except Exception:
                    return f"[响应格式错误] 无法从响应中提取文本内容: {str(type(response))}"
            elif hasattr(response, "text"):
                return str(response.text).strip()
            elif isinstance(response, dict):
                # 尝试从字典中获取常见的内容字段
                content_fields = ["content", "text", "message", "response"]
                for field in content_fields:
                    if field in response and response[field] is not None:
                        return str(response[field]).strip()
                # 如果没有找到合适的字段，返回字典的字符串表示
                return str(response)
            else:
                # 最后尝试将任何类型转换为字符串
                return str(response).strip()
        except Exception as e:
            # 处理错误，返回详细的错误信息
            error_msg = f"获取Agent响应时发生错误: {str(e)}"
            print(error_msg)
            # 确保错误消息不会导致数据库存储问题
            safe_error_msg = f"[错误] 无法获取响应: {str(e)[:500]}"  # 限制长度以避免存储问题
            return safe_error_msg
    
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
        
        # 创建结论生成的模型配置，使用settings中的默认模型
        # 注意：禁用流式响应，确保获取完整的JSON响应
        conclusion_model_config = {
            "model_name": settings.DEFAULT_MODEL_NAME,  # 使用配置中的默认模型
            "temperature": 0.3,  # 低温度以确保结果更确定性
            "max_tokens": 2000,
            "stream": False  # 禁用流式响应
        }
        
        try:
            # 生成结论
            conclusion_data = await self.llm_service.generate_structured_output(
                model_config=conclusion_model_config,
                prompt=conclusion_prompt,
                response_format=dict,
                system_prompt="你是一位专业的辩论分析师，擅长总结和分析多轮辩论。"
            )
            
            # 确保返回的数据格式正确
            return {
                "final_conclusion": conclusion_data.get("final_conclusion", "无法生成结论"),
                "confidence_score": conclusion_data.get("confidence_score", 0.0),
                "consensus_points": conclusion_data.get("consensus_points", []),
                "divergent_views": conclusion_data.get("divergent_views", []),
                "key_arguments": conclusion_data.get("key_arguments", {}),
                "preliminary_insights": conclusion_data.get("preliminary_insights", [])
            }
        except Exception as e:
            # 处理错误，返回基本结论
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
        # 按轮次分组
        rounds = {}
        for msg in self.conversation_history:
            round_num = msg['round']
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(msg)
        
        # 生成摘要
        summary = []
        for round_num in sorted(rounds.keys()):
            round_summary = [f"第{round_num}轮:"]
            for msg in rounds[round_num]:
                # 提取每条消息的关键点（可以使用更复杂的摘要算法）
                # 这里简单截取前200个字符
                key_point = msg['response'][:200] + ("..." if len(msg['response']) > 200 else "")
                round_summary.append(f"  - [{msg['agent']}]: {key_point}")
            summary.append("\n".join(round_summary))
        
        return "\n\n".join(summary)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取完整的对话历史"""
        return self.conversation_history
    
    async def abort_debate(self):
        """中止辩论"""
        # 可以在这里添加清理资源的逻辑
        print("辩论已中止")