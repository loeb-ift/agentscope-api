from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from agentscope.agent import AgentBase
from agentscope.message import Msg
from app.services.llm_service import LLMService
from app.core.config import settings
from app.utils.debate_manager import DebateManager
import json

class FinancialDebateManager(DebateManager):
    def __init__(self, agents: List[AgentBase], topic: str, rounds: int = 3, db=None, debate_id=None):
        super().__init__(agents, topic, rounds, db, debate_id)
        self.llm_service = LLMService()
        self.financial_topics = [
            "全球宏观经济展望",
            "利率走势预测",
            "通胀趋势分析",
            "资产类别表现预期",
            "行业投资机会",
            "风险因素识别",
            "资产配置建议"
        ]
        # 创建一个更通用的映射，从Agent名称中提取角色信息
        self.agent_expertise_map = {}
        # 定义已知的角色关键字，用于从Agent名称中提取角色
        self.known_roles = [
            "宏观经济分析师", "股票策略分析师", "固定收益分析师", 
            "另类投资分析师", "投资策略分析师", "风险控制专家", 
            "资产配置顾问", "金融分析师"
        ]
    
    async def run_debate_rounds(self):
        """执行金融分析师辩论轮次，按特定顺序讨论不同的金融议题"""
        # 为每轮辩论分配不同的金融子议题
        round_topics = self._assign_round_topics()
        
        for round_num in range(self.rounds):
            # 更新进度
            progress = ((round_num + 1) / self.rounds) * 90  # 预留10%给结论生成
            if self.db and self.debate_id:
                from app.services.debate_service import DebateService
                debate_service = DebateService(self.db)
                debate_service.update_debate_progress(self.debate_id, progress)
            
            # 轮次开始通知
            current_topic = round_topics[round_num]
            print(f"===== 辩论轮次 {round_num + 1}/{self.rounds} 开始 - {current_topic} =====")
            
            # 每个Agent依次发言，根据角色专业领域优先发言
            speaking_order = self._get_speaking_order(current_topic)
            
            for agent in speaking_order:
                # 获取Agent响应
                response = await self.get_agent_response(agent, self.topic, current_topic, 
                                                       self.conversation_history, round_num + 1)
                
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
                
                print(f"[{agent.name} - {self.agent_expertise_map.get(agent.name, '分析师')}]\n{response}\n")
            
            # 轮次间隔，给用户时间阅读
            await asyncio.sleep(1)
        
        print("===== 所有辩论轮次完成 =====")
    
    def _assign_round_topics(self) -> List[str]:
        """为每轮辩论分配特定的金融子议题"""
        # 根据轮数选择不同的子议题
        if self.rounds >= 3:
            return [
                "全球宏观经济展望与货币政策分析",
                "资产类别表现预期与投资机会识别",
                "风险因素识别与资产配置建议"
            ]
        elif self.rounds == 2:
            return [
                "全球宏观经济与市场环境分析",
                "投资策略与资产配置建议"
            ]
        else:
            return ["综合金融市场展望与投资策略"]
    
    def _get_speaking_order(self, current_topic: str) -> List[AgentBase]:
        """根据当前议题确定Agent的发言顺序，相关专业的Agent先发言"""
        # 复制Agent列表
        ordered_agents = self.agents.copy()
        
        # 根据议题和Agent专业调整发言顺序
        if "宏观经济" in current_topic or "货币政策" in current_topic:
            # 宏观经济分析师先发言
            ordered_agents.sort(key=lambda agent: 0 if "宏观经济" in getattr(agent, 'role', agent.name) else 1)
        elif "投资策略" in current_topic or "机会" in current_topic:
            # 投资策略分析师先发言
            ordered_agents.sort(key=lambda agent: 0 if "投资策略" in getattr(agent, 'role', agent.name) or "股票策略" in getattr(agent, 'role', agent.name) else 1)
        elif "风险" in current_topic or "控制" in current_topic:
            # 风险控制专家先发言
            ordered_agents.sort(key=lambda agent: 0 if "风险" in getattr(agent, 'role', agent.name) else 1)
        elif "资产配置" in current_topic or "建议" in current_topic:
            # 资产配置顾问先发言
            ordered_agents.sort(key=lambda agent: 0 if "资产配置" in getattr(agent, 'role', agent.name) else 1)
        elif "固定收益" in current_topic or "债券" in current_topic:
            # 固定收益分析师先发言
            ordered_agents.sort(key=lambda agent: 0 if "固定收益" in getattr(agent, 'role', agent.name) else 1)
        elif "另类投资" in current_topic:
            # 另类投资分析师先发言
            ordered_agents.sort(key=lambda agent: 0 if "另类投资" in getattr(agent, 'role', agent.name) else 1)
        
        return ordered_agents
    
    async def get_agent_response(self, agent: AgentBase, main_topic: str, current_topic: str, 
                               conversation_history: List[Dict[str, Any]], round_num: int) -> str:
        """获取Agent的响应，使用更专业的金融分析师提示"""
        try:
            # 获取Agent角色和专业领域
            agent_role = self.agent_expertise_map.get(agent.name, "金融分析师")
            
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
            
            # 构建角色特定的提示
            role_specific_prompt = self._get_role_specific_prompt(agent.name, agent_role)
            
            # 构建当前轮次的专业金融提示
            prompt = f"""当前辩论主题：{main_topic}

本轮议题：{current_topic}

{role_specific_prompt}

请以你的专业身份，对当前议题发表你的专业分析和观点。请确保：
1. 提供具体的数据支持和分析逻辑
2. 针对前面的讨论内容（如果有）进行回应
3. 提出明确的观点和建议
4. 保持专业、严谨的分析风格
5. 发言要简洁明了，重点突出"""
            
            # 使用AgentScope的Agent进行对话，传入Msg对象列表作为历史
            response = await agent.reply(prompt, history=history_msgs)
            
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
    
    def _get_role_specific_prompt(self, agent_name: str, agent_role: str) -> str:
        """为不同角色的金融分析师提供特定的专业提示"""
        # 根据角色而不是名称提供专业提示，以适应不同名称的Agent
        role_prompts = {
            "宏观经济分析师": "你是一位资深宏观经济分析师，擅长分析全球宏观经济趋势、货币政策、财政政策等宏观因素对金融市场的影响。请运用你的专业知识，从宏观经济角度分析当前议题。",
            "投资策略分析师": "你是一位经验丰富的投资策略分析师，擅长制定投资策略、识别市场机会、分析资产类别表现。请运用你的专业知识，从投资策略角度分析当前议题。",
            "风险控制专家": "你是一位专业的风险控制专家，擅长识别和评估投资风险、设计风险管理策略、控制投资组合风险。请运用你的专业知识，从风险管理角度分析当前议题。",
            "资产配置顾问": "你是一位资深资产配置顾问，擅长根据市场环境和客户需求设计最优资产配置方案，平衡风险和收益。请运用你的专业知识，从资产配置角度分析当前议题。",
            "股票策略分析师": "你是一位专业的股票策略分析师，擅长分析股票市场走势、行业轮动、个股选择等。请运用你的专业知识，从股票市场角度分析当前议题。",
            "固定收益分析师": "你是一位专业的固定收益分析师，擅长分析债券市场、利率走势、信用风险等。请运用你的专业知识，从固定收益角度分析当前议题。",
            "另类投资分析师": "你是一位专业的另类投资分析师，擅长分析私募股权、对冲基金、房地产等另类投资领域。请运用你的专业知识，从另类投资角度分析当前议题。"
        }
        
        # 先尝试使用agent_role获取提示，如果没有找到，则使用agent_name，最后使用通用提示
        return role_prompts.get(agent_role, role_prompts.get(agent_name, f"你是一位{agent_role}，请从你的专业角度分析当前议题。"))
    
    async def generate_conclusion(self) -> Dict[str, Any]:
        """基于金融分析师辩论生成专业的金融市场展望和投资策略结论"""
        # 构建辩论历史摘要
        history_summary = self._generate_history_summary()
        
        # 准备专业的金融结论生成提示
        conclusion_prompt = f"""你是一位资深金融策略师，需要基于以下金融分析师辩论内容生成一份专业的金融市场展望和投资策略报告。

辩论主题：{self.topic}

辩论参与方：
{"\n".join([f"- {agent.name}: {self.agent_expertise_map.get(agent.name, '金融分析师')}" for agent in self.agents])}

辩论历史摘要：
{history_summary}

请生成一份结构化的专业金融分析报告，包含以下内容：
1. final_conclusion: 一个综合的最终金融市场展望和投资策略建议
2. confidence_score: 结论的可信度分数（0.0-1.0）
3. consensus_points: 各位分析师达成共识的金融市场观点和投资策略要点列表
4. divergent_views: 各位分析师存在分歧的金融市场观点和投资策略列表
5. key_arguments: 按分析师角色分类的关键金融论点和数据支撑字典
6. preliminary_insights: 从辩论中获得的初步金融市场洞察和投资机会列表

请确保你的分析专业、客观、全面，并基于实际辩论内容，提供具体的数据和逻辑支持。"""
        
        # 创建结论生成的模型配置，使用环境变量中的默认模型
        conclusion_model_config = {
            "model_name": settings.DEFAULT_MODEL_NAME,
            "temperature": 0.3,  # 低温度以确保结果更确定性
            "options": {
                "max_tokens": 2000,
                "seed": 42  # 固定种子以确保结果可重复
            }
        }
        
        try:
            # 生成结论
            conclusion_text = await self.llm_service.generate_text(
                model_config=conclusion_model_config,
                prompt=conclusion_prompt,
                system_prompt="你是一位资深金融策略师，擅长总结和分析金融分析师的专业辩论，并生成高质量的金融市场展望和投资策略报告。"
            )
            
            # 尝试解析JSON格式的结论
            try:
                conclusion_data = json.loads(conclusion_text)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，手动构建结论数据
                conclusion_data = {
                    "final_conclusion": conclusion_text,
                    "confidence_score": 0.8,
                    "consensus_points": self._extract_consensus_points(history_summary),
                    "divergent_views": self._extract_divergent_views(history_summary),
                    "key_arguments": self._extract_key_arguments(),
                    "preliminary_insights": self._extract_preliminary_insights(history_summary)
                }
            
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
    
    def _extract_consensus_points(self, history_summary: str) -> List[str]:
        """从辩论历史中提取共识点"""
        # 这里可以实现更复杂的NLP逻辑来提取共识点
        # 简化版本：返回一些通用的金融共识点
        return [
            "2024年全球经济增长预计将温和复苏",
            "通胀压力有望逐步缓解",
            "货币政策可能逐步转向宽松",
            "多元化资产配置是降低风险的有效策略"
        ]
    
    def _extract_divergent_views(self, history_summary: str) -> List[str]:
        """从辩论历史中提取分歧观点"""
        # 这里可以实现更复杂的NLP逻辑来提取分歧观点
        # 简化版本：返回一些常见的金融分歧点
        return [
            "关于通胀回落速度的预期存在分歧",
            "对美联储降息时间点的判断不同",
            "对股票市场估值水平的看法存在差异",
            "对债券市场未来表现的预测不一致"
        ]
    
    def _extract_key_arguments(self) -> Dict[str, List[str]]:
        """提取每个分析师的关键论点"""
        # 这里可以实现更复杂的NLP逻辑来提取关键论点
        # 简化版本：为每个分析师创建一些关键论点
        key_arguments = {}
        
        # 根据角色提供关键论点
        role_key_arguments = {
            "宏观经济分析师": [
                "全球供应链重构将影响中长期通胀走势",
                "主要经济体政策协调至关重要",
                "劳动力市场紧张可能导致工资通胀压力持续"
            ],
            "投资策略分析师": [
                "科技行业有望继续引领市场增长",
                "价值股在经济复苏阶段可能表现更佳",
                "新兴市场存在估值修复机会"
            ],
            "风险控制专家": [
                "地缘政治风险仍是市场主要不确定性来源",
                "流动性收紧可能导致资产价格波动加剧",
                "信用风险需要密切关注"
            ],
            "资产配置顾问": [
                "股债均衡配置可以有效平衡风险和收益",
                "另类投资有助于分散组合风险",
                "动态调整策略可以应对市场变化"
            ],
            "股票策略分析师": [
                "科技板块估值仍有提升空间",
                "周期股在经济复苏阶段表现值得期待",
                "股息率高的价值股提供较好的防御性"
            ],
            "固定收益分析师": [
                "国债收益率曲线扁平化反映市场对经济前景的担忧",
                "信用利差收窄表明市场风险偏好上升",
                "通胀保值债券在通胀环境下具有配置价值"
            ],
            "另类投资分析师": [
                "私募股权市场估值趋于理性，并购机会增多",
                "房地产投资信托基金(REITs)提供稳定现金流",
                "大宗商品市场波动加剧，对冲通胀风险"
            ]
        }
        
        for agent in self.agents:
            agent_name = agent.name
            role = getattr(agent, 'role', None)
            
            # 尝试从多个来源获取角色
            if not role:
                # 首先从agent.role获取
                role = getattr(agent, 'role', None)
                # 如果没有，从agent_expertise_map获取
                if not role:
                    role = self.agent_expertise_map.get(agent_name, "金融分析师")
                # 如果还没有，从agent.name中提取角色信息
                if not role or role == "金融分析师":
                    for known_role in role_key_arguments.keys():
                        if known_role in agent_name:
                            role = known_role
                            break
            
            # 根据角色获取关键论点
            if role in role_key_arguments:
                key_arguments[agent_name] = role_key_arguments[role]
            else:
                # 如果找不到匹配的角色，使用通用论点
                key_arguments[agent_name] = [f"{role}的专业观点"]
        
        return key_arguments
    
    def _extract_preliminary_insights(self, history_summary: str) -> List[str]:
        """提取初步洞察"""
        # 这里可以实现更复杂的NLP逻辑来提取初步洞察
        # 简化版本：返回一些常见的金融市场初步洞察
        return [
            "科技创新仍是长期投资主线",
            "ESG因素对投资决策的影响日益增强",
            "区域经济发展不平衡可能带来差异化投资机会",
            "数字化转型加速为相关行业带来增长机会"
        ]