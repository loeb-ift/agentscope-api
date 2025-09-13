from typing import Dict, Any, List, Optional
from app.models.schemas import N8NOptimizedResponse
from datetime import datetime

class ResponseParser:
    @staticmethod
    def parse_debate_result_to_n8n_format(
        session_id: str,
        status: str,
        progress: float,
        preliminary_insights: List[str],
        final_conclusion: Optional[str] = None,
        key_arguments: Optional[Dict[str, List[str]]] = None,
        consensus_points: Optional[List[str]] = None,
        divergent_views: Optional[List[str]] = None,
        confidence_score: Optional[float] = None
    ) -> N8NOptimizedResponse:
        """将辩论结果解析为n8n优化的响应格式"""
        # 确保所有字段都有默认值
        key_arguments = key_arguments or {}
        consensus_points = consensus_points or []
        divergent_views = divergent_views or []
        confidence_score = confidence_score or 0.0
        preliminary_insights = preliminary_insights or []
        final_conclusion = final_conclusion or "[结论生成中] 辩论尚未完成或结论提取失败"
        
        # 创建并返回n8n优化的响应
        return N8NOptimizedResponse(
            session_id=session_id,
            status=status,
            progress=progress,
            preliminary_insights=preliminary_insights,
            final_conclusion=final_conclusion,
            key_arguments=key_arguments,
            consensus_points=consensus_points,
            divergent_views=divergent_views,
            confidence_score=confidence_score
        )
    
    @staticmethod
    def format_error_response(detail: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """格式化错误响应"""
        error_response = {
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if error_code:
            error_response["error_code"] = error_code
        
        return error_response
    
    @staticmethod
    def extract_key_arguments_by_role(conversation_history: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """从对话历史中提取按角色分类的关键论点"""
        key_arguments = {}
        
        for message in conversation_history:
            role = message.get("role", "unknown")
            if role not in key_arguments:
                key_arguments[role] = []
            
            # 提取关键论点（这里简单地使用消息内容作为论点）
            # 实际实现中可以使用更复杂的提取算法
            key_arguments[role].append(message.get("response", ""))
        
        return key_arguments
    
    @staticmethod
    def extract_preliminary_insights(conversation_history: List[Dict[str, Any]], 
                                   max_insights: int = 5) -> List[str]:
        """从对话历史中提取初步洞察"""
        # 这里提供一个简单的实现
        # 实际应用中可能需要使用LLM来提取洞察
        insights = []
        
        # 示例逻辑：提取每个轮次的主要观点
        rounds = {}
        for message in conversation_history:
            round_num = message.get("round", 0)
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(message)
        
        # 为每个轮次生成一个洞察
        for round_num in sorted(rounds.keys()):
            if len(insights) >= max_insights:
                break
            
            round_messages = rounds[round_num]
            agents_in_round = [msg.get("agent", "Unknown") for msg in round_messages]
            # 将UUID对象转换为字符串类型
            agents_in_round_str = [str(agent_id) for agent_id in agents_in_round]
            insight = f"第{round_num}轮参与讨论的Agent: {', '.join(agents_in_round_str)}"
            insights.append(insight)
        
        return insights
    
    @staticmethod
    def format_conversation_history_for_display(conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化对话历史以便显示"""
        formatted_history = []
        
        for message in conversation_history:
            formatted_message = {
                "agent_name": message.get("agent", "Unknown"),
                "agent_role": message.get("role", "Unknown"),
                "round": message.get("round", 0),
                "content": message.get("response", ""),
                "timestamp": message.get("timestamp", datetime.utcnow()).isoformat()
            }
            formatted_history.append(formatted_message)
        
        return formatted_history
    
    @staticmethod
    def validate_response_format(response: Any, expected_format: str = "json") -> bool:
        """验证响应格式是否符合预期"""
        if expected_format.lower() == "json":
            return isinstance(response, dict)
        elif expected_format.lower() == "list":
            return isinstance(response, list)
        elif expected_format.lower() == "string":
            return isinstance(response, str)
        else:
            return False
    
    @staticmethod
    def sanitize_response_data(data: Any) -> Any:
        """清理响应数据，移除敏感信息"""
        # 递归清理数据
        if isinstance(data, dict):
            return {key: ResponseParser.sanitize_response_data(value) 
                   for key, value in data.items() 
                   if not ResponseParser._is_sensitive_key(key)}
        elif isinstance(data, list):
            return [ResponseParser.sanitize_response_data(item) for item in data]
        else:
            return data
    
    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        """检查键是否包含敏感信息"""
        sensitive_patterns = ["api_key", "token", "password", "secret", "auth"]
        return any(pattern in key.lower() for pattern in sensitive_patterns)