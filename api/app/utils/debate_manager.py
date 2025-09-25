from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from agentscope.agent import AgentBase
from agentscope.message import Msg
from app.services.llm_service import LLMService
from app.core.config import settings

class DebateManager:
    def __init__(self, agents: List[AgentBase], topic: str, rounds: int = 3, db=None, debate_id=None, moderator: Optional[AgentBase] = None):
        self.agents = agents
        self.topic = topic
        self.rounds = rounds
        self.db = db
        self.debate_id = debate_id
        self.moderator = moderator
        self.conversation_history = []
        self.llm_service = LLMService()
    
    async def run_debate_rounds(self):
        """執行辯論輪次"""
        for round_num in range(self.rounds):
            # 更新進度
            progress = ((round_num + 1) / self.rounds) * 90  # 預留10%給結論生成
            if self.db and self.debate_id:
                from app.services.debate_service import DebateService
                debate_service = DebateService(self.db)
                debate_service.update_debate_progress(self.debate_id, progress)
            
            # 輪次開始通知
            print(f"===== 辯論輪次 {round_num + 1}/{self.rounds} 開始 =====")
            
            # 隨機打亂Agent順序（可選，增加辯論的多樣性）
            # import random
            # random.shuffle(self.agents)
            
            # 每個Agent依次發言
            round_history = []
            for agent in self.agents:
                # 獲取Agent響應
                response = await self.get_agent_response(agent, self.topic, self.conversation_history, round_num + 1)
                
                # 獲取Agent資訊，確保正確獲取name和role
                agent_name = getattr(agent, 'name', '未知分析師')
                agent_id = getattr(agent, 'id', str(hash(agent_name)))
                agent_role = getattr(agent, 'role', 'unknown')
                
                # 記錄響應
                msg_data = {
                    'agent': agent_name,
                    'agent_id': agent_id,
                    'role': agent_role,
                    'round': round_num + 1,
                    'response': response,
                    'timestamp': datetime.now()
                }
                self.conversation_history.append(msg_data)
                round_history.append(msg_data)
                
                # 保存到數據庫
                if self.db and self.debate_id:
                    from app.services.debate_service import DebateService
                    debate_service = DebateService(self.db)
                    debate_service.save_debate_message(
                        debate_id=self.debate_id,
                        agent_id=agent_id,
                        agent_name=agent_name,
                        agent_role=agent_role,
                        round_number=round_num + 1,
                        content=response
                    )
                
                print(f"[{agent.name}]\n{response}\n")
            
            # After each round, get a summary from the moderator
            if self.moderator:
                summary = await self._get_moderator_summary(round_num + 1, round_history)
                
                moderator_name = getattr(self.moderator, 'name', '主持人')
                moderator_id = getattr(self.moderator, 'id', 'moderator_id')
                
                summary_msg_data = {
                    'agent': moderator_name,
                    'agent_id': moderator_id,
                    'role': 'moderator',
                    'round': round_num + 1,
                    'response': summary,
                    'timestamp': datetime.now()
                }
                self.conversation_history.append(summary_msg_data)
                
                # Save moderator summary to DB
                if self.db and self.debate_id:
                    from app.services.debate_service import DebateService
                    debate_service = DebateService(self.db)
                    debate_service.save_debate_message(
                        debate_id=self.debate_id,
                        agent_id=moderator_id,
                        agent_name=moderator_name,
                        agent_role='moderator',
                        round_number=round_num + 1,
                        content=summary
                    )
                print(f"[{moderator_name}]\n{summary}\n")
        
        print("===== 所有辯論輪次完成 =====")
    
    async def get_agent_response(self, agent: AgentBase, topic: str, 
                               conversation_history: List[Dict[str, Any]], round_num: int) -> str:
        """獲取Agent的響應"""
        try:
            # 構建對話歷史消息列表
            history_msgs = []
            for msg in conversation_history:
                if msg['round'] < round_num:
                    # 將字典轉換為Msg對象
                    history_msg = Msg(
                        name=msg['agent'],
                        role="user",  # 在AgentScope中，用戶消息使用user角色
                        content=msg['response'],
                        timestamp=msg['timestamp']
                    )
                    history_msgs.append(history_msg)
            
            # 構建當前輪次的提示作為Msg對象
            prompt_msg = Msg(
                name="system",
                role="system",
                content=f"""當前辯論主題：{topic}

請以你當前的角色和立場，對辯論主題發表你的觀點和論據。請確保你的發言與當前輪次相關，
並針對前面的討論內容（如果有）進行回應。發言要簡潔明瞭，重點突出。

**語言規則：** 你的所有思考過程 (thinking) 和最終回答 (speak) 都**必須**使用**繁體中文**。
""",
                timestamp=datetime.now()
            )
            
            # 創建完整的消息列表（歷史消息 + 當前提示）
            input_msgs = history_msgs + [prompt_msg]
            
            # 使用AgentScope的Agent進行對話，傳入完整的消息列表
            response = await agent.reply(input_msgs)
            
            # 增強的響應處理邏輯，確保返回有效的字符串
            if response is None:
                return "[無響應] Agent未返回任何內容"
            
            # 處理不同類型的響應
            if isinstance(response, str):
                return response.strip()
            elif isinstance(response, Msg):
                # 對於Msg對象，直接獲取content字段
                if hasattr(response, "content") and response.content is not None:
                    return str(response.content).strip()
                else:
                    return "[響應格式錯誤] Msg對象缺少content字段"
            elif hasattr(response, "get_text_content"):
                try:
                    text_content = response.get_text_content()
                    if isinstance(text_content, str):
                        return text_content.strip()
                    else:
                        return str(text_content).strip()
                except Exception:
                    return f"[響應格式錯誤] 無法從響應中提取文本內容: {str(type(response))}"
            elif hasattr(response, "text"):
                return str(response.text).strip()
            elif isinstance(response, dict):
                # 嘗試從字典中獲取常見的內容字段
                content_fields = ["content", "text", "message", "response"]
                for field in content_fields:
                    if field in response and response[field] is not None:
                        return str(response[field]).strip()
                # 如果沒有找到合適的字段，返回字典的字符串表示
                return str(response)
            else:
                # 最後嘗試將任何類型轉換為字符串
                return str(response).strip()
        except Exception as e:
            # 處理錯誤，返回詳細的錯誤信息
            error_msg = f"獲取Agent響應時發生錯誤: {str(e)}"
            print(error_msg)
            # 確保錯誤消息不會導致數據庫存儲問題
            safe_error_msg = f"[錯誤] 無法獲取響應: {str(e)[:500]}"  # 限制長度以避免存儲問題
            return safe_error_msg
    
    async def generate_conclusion(self) -> Dict[str, Any]:
        """基於辯論歷史生成最終結論"""
        # 構建辯論歷史摘要
        history_summary = self._generate_history_summary()
        
        # 準備結論生成的提示
        conclusion_prompt = f"""你是一位專業的辯論分析師，需要基於以下辯論內容生成一份全面的分析報告。

辯論主題：{self.topic}

辯論參與方：{', '.join([agent.name for agent in self.agents])}

辯論歷史摘要：
{history_summary}

請生成一份結構化的分析報告，包含以下內容：
1. final_conclusion: 一個綜合的最終結論，總結辯論的主要觀點和共識
2. confidence_score: 結論的可信度分數（0.0-1.0）
3. consensus_points: 各方達成共識的要點列表
4. divergent_views: 各方存在分歧的觀點列表
5. key_arguments: 按角色分類的關鍵論點字典
6. preliminary_insights: 從辯論中獲得的初步洞察列表

**極重要規則：** 所有生成的文本內容，包括所有欄位的標題和值，都**必須**使用**繁體中文**。
"""
        
        # 創建結論生成的模型配置，使用settings中的默認模型
        # 注意：禁用流式響應，確保獲取完整的JSON響應
        conclusion_model_config = {
            "model_name": settings.DEFAULT_MODEL_NAME,  # 使用配置中的默認模型
            "temperature": 0.3,  # 低溫度以確保結果更確定性
            "max_tokens": 2000,
            "stream": False  # 禁用流式響應
        }
        
        try:
            # 生成結論
            conclusion_data = await self.llm_service.generate_structured_output(
                model_config=conclusion_model_config,
                prompt=conclusion_prompt,
                response_format=dict,
                system_prompt="你是一位專業的辯論分析師，擅長總結和分析多輪辯論。"
            )
            
            # 確保返回的數據格式正確
            return {
                "final_conclusion": conclusion_data.get("final_conclusion", "無法生成結論"),
                "confidence_score": conclusion_data.get("confidence_score", 0.0),
                "consensus_points": conclusion_data.get("consensus_points", []),
                "divergent_views": conclusion_data.get("divergent_views", []),
                "key_arguments": conclusion_data.get("key_arguments", {}),
                "preliminary_insights": conclusion_data.get("preliminary_insights", [])
            }
        except Exception as e:
            # 處理錯誤，返回基本結論
            error_msg = f"生成結論時發生錯誤: {str(e)}"
            print(error_msg)
            return {
                "final_conclusion": f"結論生成失敗: {str(e)}",
                "confidence_score": 0.0,
                "consensus_points": [],
                "divergent_views": [],
                "key_arguments": {},
                "preliminary_insights": []
            }
    
    def _generate_history_summary(self) -> str:
        """生成辯論歷史摘要"""
        # 按輪次分組
        rounds = {}
        for msg in self.conversation_history:
            round_num = msg['round']
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(msg)
        
        # 生成摘要
        summary = []
        for round_num in sorted(rounds.keys()):
            round_summary = [f"第{round_num}輪:"]
            for msg in rounds[round_num]:
                # 提取每條消息的關鍵點（可以使用更複雜的摘要算法）
                # 這裡簡單截取前200個字符
                key_point = msg['response'][:200] + ("..." if len(msg['response']) > 200 else "")
                round_summary.append(f"  - [{msg['agent']}]: {key_point}")
            summary.append("\n".join(round_summary))
        
        return "\n\n".join(summary)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """獲取完整的對話歷史"""
        return self.conversation_history
    
    async def _get_moderator_summary(self, round_num: int, round_history: List[Dict[str, Any]]) -> str:
        """Get a summary of the round from the moderator."""
        print(f"===== 主持人總結第 {round_num} 輪 =====")
        
        history_text = "\n".join([f"[{msg['agent']}]: {msg['response']}" for msg in round_history])
        
        prompt_text = f"""
        這是辯論的第 {round_num} 輪。
        辯論主題: {self.topic}
        本輪發言:
        {history_text}

        請總結本輪的要點、共識和分歧。
        """
        
        try:
            # 將字串包裝成 Msg 物件
            prompt_msg = Msg(name="system", content=prompt_text, role="system")
            response = await self.moderator.reply(prompt_msg)
            
            if isinstance(response, Msg):
                return str(response.content).strip()
            return str(response).strip()
        except Exception as e:
            error_msg = f"獲取主持人總結時發生錯誤: {str(e)}"
            print(error_msg)
            return f"[錯誤] 無法獲取主持人總結: {str(e)}"

    async def abort_debate(self):
        """中止辯論"""
        # 可以在這裡添加清理資源的邏輯
        print("辯論已中止")