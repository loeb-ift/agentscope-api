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
            "全球宏觀經濟展望",
            "利率走勢預測",
            "通脹趨勢分析",
            "資產類別表現預期",
            "行業投資機會",
            "風險因素識別",
            "資產配置建議"
        ]
        # 創建一個更通用的映射，從Agent名稱中提取角色信息
        self.agent_expertise_map = {}
        # 定義已知的角色關鍵字，用於從Agent名稱中提取角色
        self.known_roles = [
            "宏觀經濟分析師", "股票策略分析師", "固定收益分析師", 
            "另類投資分析師", "投資策略分析師", "風險控制專家", 
            "資產配置顧問", "金融分析師"
        ]
    
    async def run_debate_rounds(self):
        """執行金融分析師辯論輪次，按特定順序討論不同的金融議題"""
        # 為每輪辯論分配不同的金融子議題
        round_topics = self._assign_round_topics()
        
        for round_num in range(self.rounds):
            # 更新進度
            progress = ((round_num + 1) / self.rounds) * 90  # 預留10%給結論生成
            if self.db and self.debate_id:
                from app.services.debate_service import DebateService
                debate_service = DebateService(self.db)
                debate_service.update_debate_progress(self.debate_id, progress)
            
            # 輪次開始通知
            current_topic = round_topics[round_num]
            print(f"===== 辯論輪次 {round_num + 1}/{self.rounds} 開始 - {current_topic} =====")
            
            # 每個Agent依次發言，根據角色專業領域優先發言
            speaking_order = self._get_speaking_order(current_topic)
            
            for agent in speaking_order:
                # 獲取Agent回應
                response = await self.get_agent_response(agent, self.topic, current_topic, 
                                                       self.conversation_history, round_num + 1)
                
                # 記錄回應
                self.conversation_history.append({
                    'agent': agent.name,
                    'agent_id': getattr(agent, 'id', str(hash(agent.name))),
                    'role': getattr(agent, 'role', 'unknown'),
                    'round': round_num + 1,
                    'response': response,
                    'timestamp': datetime.now()
                })
                
                # 保存到數據庫
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
                
                print(f"[{agent.name} - {self.agent_expertise_map.get(agent.name, '分析師')}]\n{response}\n")
            
            # 輪次間隔，給用戶時間閱讀
            await asyncio.sleep(1)
        
        print("===== 所有辯論輪次完成 =====")
    
    def _assign_round_topics(self) -> List[str]:
        """為每輪辯論分配特定的金融子議題"""
        # 根據輪數選擇不同的子議題
        if self.rounds >= 3:
            return [
                "全球宏觀經濟展望與貨幣政策分析",
                "資產類別表現預期與投資機會識別",
                "風險因素識別與資產配置建議"
            ]
        elif self.rounds == 2:
            return [
                "全球宏觀經濟與市場環境分析",
                "投資策略與資產配置建議"
            ]
        else:
            return ["綜合金融市場展望與投資策略"]
    
    def _get_speaking_order(self, current_topic: str) -> List[AgentBase]:
        """根據當前議題確定Agent的發言順序，相關專業的Agent先發言"""
        # 複製Agent列表
        ordered_agents = self.agents.copy()
        
        # 根據議題和Agent專業調整發言順序
        if "宏觀經濟" in current_topic or "貨幣政策" in current_topic:
            # 宏觀經濟分析師先發言
            ordered_agents.sort(key=lambda agent: 0 if "宏觀經濟" in getattr(agent, 'role', agent.name) else 1)
        elif "投資策略" in current_topic or "機會" in current_topic:
            # 投資策略分析師先發言
            ordered_agents.sort(key=lambda agent: 0 if "投資策略" in getattr(agent, 'role', agent.name) or "股票策略" in getattr(agent, 'role', agent.name) else 1)
        elif "風險" in current_topic or "控制" in current_topic:
            # 風險控制專家先發言
            ordered_agents.sort(key=lambda agent: 0 if "風險" in getattr(agent, 'role', agent.name) else 1)
        elif "資產配置" in current_topic or "建議" in current_topic:
            # 資產配置顧問先發言
            ordered_agents.sort(key=lambda agent: 0 if "資產配置" in getattr(agent, 'role', agent.name) else 1)
        elif "固定收益" in current_topic or "債券" in current_topic:
            # 固定收益分析師先發言
            ordered_agents.sort(key=lambda agent: 0 if "固定收益" in getattr(agent, 'role', agent.name) else 1)
        elif "另類投資" in current_topic:
            # 另類投資分析師先發言
            ordered_agents.sort(key=lambda agent: 0 if "另類投資" in getattr(agent, 'role', agent.name) else 1)
        
        return ordered_agents
    
    async def get_agent_response(self, agent: AgentBase, main_topic: str, current_topic: str, 
                               conversation_history: List[Dict[str, Any]], round_num: int) -> str:
        """獲取Agent的回應，使用更專業的金融分析師提示"""
        try:
            # 獲取Agent角色和專業領域
            agent_role = self.agent_expertise_map.get(agent.name, "金融分析師")
            
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
            
            # 構建角色特定的提示
            role_specific_prompt = self._get_role_specific_prompt(agent.name, agent_role)
            
            # 構建當前輪次的專業金融提示
            prompt = f"""當前辯論主題：{main_topic}

本輪議題：{current_topic}

{role_specific_prompt}

請以你的專業身份，對當前議題發表你的專業分析和觀點。請確保：
1. 提供具體的數據支持和分析邏輯
2. 針對前面的討論內容（如果有）進行回應
3. 提出明確的觀點和建議
4. 保持專業、嚴謹的分析風格
5. 發言要簡潔明瞭，重點突出"""
            
            # 使用AgentScope的Agent進行對話，傳入Msg對象列表作為歷史
            response = await agent.reply(prompt, history=history_msgs)
            
            # 增強的回應處理邏輯，確保返回有效的字符串
            if response is None:
                return "[無回應] Agent未返回任何內容"
            
            # 處理不同類型的回應
            if isinstance(response, str):
                return response.strip()
            elif isinstance(response, Msg):
                # 對於Msg對象，直接獲取content字段
                if hasattr(response, "content") and response.content is not None:
                    return str(response.content).strip()
                else:
                    return "[回應格式錯誤] Msg對象缺少content字段"
            elif hasattr(response, "get_text_content"):
                try:
                    text_content = response.get_text_content()
                    if isinstance(text_content, str):
                        return text_content.strip()
                    else:
                        return str(text_content).strip()
                except Exception:
                    return f"[回應格式錯誤] 無法從回應中提取文本內容: {str(type(response))}"
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
            error_msg = f"獲取Agent回應時發生錯誤: {str(e)}"
            print(error_msg)
            # 確保錯誤消息不會導致數據庫存儲問題
            safe_error_msg = f"[錯誤] 無法獲取回應: {str(e)[:500]}"  # 限制長度以避免存儲問題
            return safe_error_msg
    
    def _get_role_specific_prompt(self, agent_name: str, agent_role: str) -> str:
        """為不同角色的金融分析師提供特定的專業提示"""
        # 根據角色而不是名稱提供專業提示，以適應不同名稱的Agent
        role_prompts = {
            "宏觀經濟分析師": "你是一位資深宏觀經濟分析師，擅長分析全球宏觀經濟趨勢、貨幣政策、財政政策等宏觀因素對金融市場的影響。請運用你的專業知識，從宏觀經濟角度分析當前議題。",
            "投資策略分析師": "你是一位經驗豐富的投資策略分析師，擅長制定投資策略、識別市場機會、分析資產類別表現。請運用你的專業知識，從投資策略角度分析當前議題。",
            "風險控制專家": "你是一位專業的風險控制專家，擅長識別和評估投資風險、設計風險管理策略、控制投資組合風險。請運用你的專業知識，從風險管理角度分析當前議題。",
            "資產配置顧問": "你是一位資深資產配置顧問，擅長根據市場環境和客戶需求設計最優資產配置方案，平衡風險和收益。請運用你的專業知識，從資產配置角度分析當前議題。",
            "股票策略分析師": "你是一位專業的股票策略分析師，擅長分析股票市場走勢、行業輪動、個股選擇等。請運用你的專業知識，從股票市場角度分析當前議題。",
            "固定收益分析師": "你是一位專業的固定收益分析師，擅長分析債券市場、利率走勢、信用風險等。請運用你的專業知識，從固定收益角度分析當前議題。",
            "另類投資分析師": "你是一位專業的另類投資分析師，擅長分析私募股權、對沖基金、房地產等另類投資領域。請運用你的專業知識，從另類投資角度分析當前議題。"
        }
        
        # 先嘗試使用agent_role獲取提示，如果沒有找到，則使用agent_name，最後使用通用提示
        return role_prompts.get(agent_role, role_prompts.get(agent_name, f"你是一位{agent_role}，請從你的專業角度分析當前議題。"))
    
    async def generate_conclusion(self) -> Dict[str, Any]:
        """基於金融分析師辯論生成專業的金融市場展望和投資策略結論"""
        # 構建辯論歷史摘要
        history_summary = self._generate_history_summary()
        
        # 準備專業的金融結論生成提示
        conclusion_prompt = f"""你是一位資深金融策略師，需要基於以下金融分析師辯論內容生成一份專業的金融市場展望和投資策略報告。

辯論主題：{self.topic}

辯論參與方：
{"\n".join([f"- {agent.name}: {self.agent_expertise_map.get(agent.name, '金融分析師')}" for agent in self.agents])}

辯論歷史摘要：
{history_summary}

請生成一份結構化的專業金融分析報告，包含以下內容：
1. final_conclusion: 一個綜合的最終金融市場展望和投資策略建議
2. confidence_score: 結論的可信度分數（0.0-1.0）
3. consensus_points: 各位分析師達成共識的金融市場觀點和投資策略要點列表
4. divergent_views: 各位分析師存在分歧的金融市場觀點和投資策略列表
5. key_arguments: 按分析師角色分類的關鍵金融論點和數據支撐字典
6. preliminary_insights: 從辯論中獲得的初步金融市場洞察和投資機會列表

請確保你的分析專業、客觀、全面，並基於實際辯論內容，提供具體的數據和邏輯支持。"""
        
        # 創建結論生成的模型配置，使用環境變量中的默認模型
        conclusion_model_config = {
            "model_name": settings.DEFAULT_MODEL_NAME,
            "temperature": 0.3,  # 低溫度以確保結果更確定性
            "options": {
                "max_tokens": 2000,
                "seed": 42  # 固定種子以確保結果可重複
            }
        }
        
        try:
            # 生成結論
            conclusion_text = await self.llm_service.generate_text(
                model_config=conclusion_model_config,
                prompt=conclusion_prompt,
                system_prompt="你是一位資深金融策略師，擅長總結和分析金融分析師的專業辯論，並生成高質量的金融市場展望和投資策略報告。"
            )
            
            # 嘗試解析JSON格式的結論
            try:
                conclusion_data = json.loads(conclusion_text)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，手動構建結論數據
                conclusion_data = {
                    "final_conclusion": conclusion_text,
                    "confidence_score": 0.8,
                    "consensus_points": self._extract_consensus_points(history_summary),
                    "divergent_views": self._extract_divergent_views(history_summary),
                    "key_arguments": self._extract_key_arguments(),
                    "preliminary_insights": self._extract_preliminary_insights(history_summary)
                }
            
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
    
    def _extract_consensus_points(self, history_summary: str) -> List[str]:
        """從辯論歷史中提取共識點"""
        # 這裡可以實現更複雜的NLP邏輯來提取共識點
        # 簡化版本：返回一些通用的金融共識點
        return [
            "2024年全球經濟增長預計將溫和復甦",
            "通脹壓力有望逐步緩解",
            "貨幣政策可能逐步轉向寬鬆",
            "多元化資產配置是降低風險的有效策略"
        ]
    
    def _extract_divergent_views(self, history_summary: str) -> List[str]:
        """從辯論歷史中提取分歧觀點"""
        # 這裡可以實現更複雜的NLP邏輯來提取分歧觀點
        # 簡化版本：返回一些常見的金融分歧點
        return [
            "關於通脹回落速度的預期存在分歧",
            "對美聯儲降息時間點的判斷不同",
            "對股票市場估值水平的看法存在差異",
            "對債券市場未來表現的預測不一致"
        ]
    
    def _extract_key_arguments(self) -> Dict[str, List[str]]:
        """提取每個分析師的關鍵論點"""
        # 這裡可以實現更複雜的NLP邏輯來提取關鍵論點
        # 簡化版本：為每個分析師創建一些關鍵論點
        key_arguments = {}
        
        # 根據角色提供關鍵論點
        role_key_arguments = {
            "宏觀經濟分析師": [
                "全球供應鏈重構將影響中長期通脹走勢",
                "主要經濟體政策協調至關重要",
                "勞動力市場緊張可能導致工資通脹壓力持續"
            ],
            "投資策略分析師": [
                "科技行業有望繼續引領市場增長",
                "價值股在經濟復甦階段可能表現更佳",
                "新興市場存在估值修復機會"
            ],
            "風險控制專家": [
                "地緣政治風險仍是市場主要不確定性來源",
                "流動性收緊可能導致資產價格波動加劇",
                "信用風險需要密切關注"
            ],
            "資產配置顧問": [
                "股債均衡配置可以有效平衡風險和收益",
                "另類投資有助於分散組合風險",
                "動態調整策略可以應對市場變化"
            ],
            "股票策略分析師": [
                "科技板塊估值仍有提升空間",
                "周期股在經濟復甦階段表現值得期待",
                "股息率高的價值股提供較好的防禦性"
            ],
            "固定收益分析師": [
                "國債收益率曲線扁平化反映市場對經濟前景的擔憂",
                "信用利差收窄表明市場風險偏好上升",
                "通脹保值債券在通脹環境下具有配置價值"
            ],
            "另類投資分析師": [
                "私募股權市場估值趨於理性，併購機會增多",
                "房地產投資信托基金(REITs)提供穩定現金流",
                "大宗商品市場波動加劇，對沖通脹風險"
            ]
        }
        
        for agent in self.agents:
            agent_name = agent.name
            role = getattr(agent, 'role', None)
            
            # 嘗試從多個來源獲取角色
            if not role:
                # 首先從agent.role獲取
                role = getattr(agent, 'role', None)
                # 如果沒有，從agent_expertise_map獲取
                if not role:
                    role = self.agent_expertise_map.get(agent_name, "金融分析師")
                # 如果還沒有，從agent.name中提取角色信息
                if not role or role == "金融分析師":
                    for known_role in role_key_arguments.keys():
                        if known_role in agent_name:
                            role = known_role
                            break
            
            # 根據角色獲取關鍵論點
            if role in role_key_arguments:
                key_arguments[agent_name] = role_key_arguments[role]
            else:
                # 如果找不到匹配的角色，使用通用論點
                key_arguments[agent_name] = [f"{role}的專業觀點"]
        
        return key_arguments
    
    def _extract_preliminary_insights(self, history_summary: str) -> List[str]:
        """提取初步洞察"""
        # 這裡可以實現更複雜的NLP邏輯來提取初步洞察
        # 簡化版本：返回一些常見的金融市場初步洞察
        return [
            "科技創新仍是長期投資主線",
            "ESG因素對投資決策的影響日益增強",
            "區域經濟發展不平衡可能帶來差異化投資機會",
            "數字化轉型加速為相關行業帶來增長機會"
        ]