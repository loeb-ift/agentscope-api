from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.schemas import (
    DebateStartRequest,
    DebateStartResponse,
    DebateStatusResponse,
    DebateResultResponse,
    AgentConfig
)
from app.services.debate_service import DebateService
from app.services.agent_service import AgentService
from app.utils.financial_debate_manager import FinancialDebateManager
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/start", response_model=DebateStartResponse, summary="启动金融分析师辩论")
def start_financial_debate(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    启动一场金融分析师辩论，自动创建四个不同角色的金融分析师Agent
    
    这是一个预设的辩论流程，自动创建以下四个金融分析师角色：
    1. 宏观经济分析师
    2. 投资策略分析师
    3. 风险控制专家
    4. 资产配置顾问
    
    辩论主题固定为："2024年全球金融市场展望与投资策略"，辩论轮次固定为3轮。
    """
    try:
        # 创建辩论服务实例
        debate_service = DebateService(db)
        agent_service = AgentService(db)
        
        # 1. 创建四个金融分析师Agent
        analyst_agents = _create_financial_analysts(agent_service)
        
        # 2. 准备辩论请求
        debate_request = DebateStartRequest(
            topic="2024年全球金融市场展望与投资策略",
            agent_ids=[str(agent.id) for agent in analyst_agents],
            rounds=3,
            max_duration_minutes=30,
            conclusion_requirements={
                "include_asset_allocation": True,
                "include_risk_assessment": True,
                "include_market_outlook": True,
                "include_investment_themes": True
            }
        )
        
        # 3. 启动辩论
        debate = debate_service.start_debate(debate_request)
        session_id = str(debate.id)
        
        # 4. 异步执行辩论
        background_tasks.add_task(_run_financial_debate, session_id, db)
        
        # 5. 返回会话ID
        return DebateStartResponse(
            session_id=session_id,
            status="pending",
            message="金融分析师辩论已启动，请稍后查询结果",
            created_at=debate.created_at
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"启动金融分析师辩论失败: {str(e)}"
        )

@router.get("/{session_id}/status", response_model=DebateStatusResponse, summary="获取金融分析师辩论状态")
def get_financial_debate_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取金融分析师辩论的状态
    
    - **session_id**: 辩论会话ID
    """
    try:
        debate_service = DebateService(db)
        status = debate_service.get_debate_status(session_id)
        return status
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取辩论状态失败: {str(e)}"
        )

@router.get("/{session_id}/result", response_model=DebateResultResponse, summary="获取金融分析师辩论结果")
def get_financial_debate_result(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取金融分析师辩论的结果
    
    - **session_id**: 辩论会话ID
    """
    try:
        debate_service = DebateService(db)
        result = debate_service.get_debate_result(session_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取辩论结果失败: {str(e)}"
        )

@router.get("/{session_id}/history", summary="获取金融分析师辩论历史")
def get_financial_debate_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取金融分析师辩论的完整历史记录
    
    - **session_id**: 辩论会话ID
    """
    try:
        debate_service = DebateService(db)
        messages = debate_service.get_debate_messages(session_id)
        
        # 转换为JSON格式返回
        history = []
        for message in messages:
            history.append({
                "id": str(message.id),
                "debate_id": str(message.debate_id),
                "agent_id": str(message.agent_id),
                "agent_name": message.agent_name,
                "agent_role": message.agent_role,
                "round_number": message.round_number,
                "content": message.content,
                "timestamp": message.timestamp
            })
        
        return {
            "session_id": session_id,
            "history": history,
            "total_messages": len(history)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取辩论历史失败: {str(e)}"
        )

@router.get("/example-curl", summary="获取CURL示例命令")
def get_example_curl_commands():
    """
    获取用于调用金融分析师辩论API的CURL示例命令
    """
    return {
        "examples": [
            {
                "description": "启动金融分析师辩论",
                "command": "curl -X POST http://localhost:8000/api/financial-debate/start -H \"Content-Type: application/json\""
            },
            {
                "description": "获取辩论状态",
                "command": "curl http://localhost:8000/api/financial-debate/{session_id}/status"
            },
            {
                "description": "获取辩论结果",
                "command": "curl http://localhost:8000/api/financial-debate/{session_id}/result"
            },
            {
                "description": "获取辩论历史",
                "command": "curl http://localhost:8000/api/financial-debate/{session_id}/history"
            }
        ]
    }

async def _run_financial_debate(session_id: str, db: Session):
    """\执行金融分析师辩论流程"""
    try:
        debate_service = DebateService(db)
        agent_service = AgentService(db)
        
        # 获取辩论信息
        debate = debate_service.get_debate(session_id)
        
        # 获取参与辩论的Agent
        agents = agent_service.get_agent_by_ids(debate.agent_ids)
        
        # 创建AgentScope Agent实例
        agentscope_agents = []
        for agent in agents:
            agentscope_agents.append(
                agent_service.create_agentscope_agent(agent)
            )
        
        # 创建金融辩论管理器
        debate_manager = FinancialDebateManager(
            agents=agentscope_agents,
            topic=debate.topic,
            rounds=debate.rounds,
            db=db,
            debate_id=session_id
        )
        
        # 执行辩论轮次
        await debate_manager.run_debate_rounds()
        
        # 生成结论
        conclusion_data = await debate_manager.generate_conclusion()
        
        # 更新辩论结果
        debate.status = "completed"
        debate.progress = 100.0
        debate.final_conclusion = conclusion_data.get("final_conclusion")
        debate.confidence_score = conclusion_data.get("confidence_score", 0.0)
        debate.consensus_points = conclusion_data.get("consensus_points", [])
        debate.divergent_views = conclusion_data.get("divergent_views", [])
        debate.key_arguments = conclusion_data.get("key_arguments", {})
        debate.preliminary_insights = conclusion_data.get("preliminary_insights", [])
        debate.updated_at = datetime.utcnow()
        
        db.commit()
        
    except Exception as e:
        # 处理辩论过程中的错误
        debate = debate_service.get_debate(session_id)
        debate.status = "failed"
        debate.updated_at = datetime.utcnow()
        db.commit()
        
        # 记录错误日志
        print(f"金融分析师辩论执行错误: {str(e)}")

def _create_financial_analysts(agent_service: AgentService) -> List:
    """创建四个预设的金融分析师Agent"""
    analysts = []
    
    # 1. 宏观经济分析师
    macro_analyst = AgentConfig(
        name="张明",
        role="analyst",
        system_prompt="你是一位资深宏观经济分析师，擅长分析全球宏观经济趋势、货币政策、财政政策等宏观因素对金融市场的影响。",
        llm_config={
            "model_name": settings.DEFAULT_MODEL_NAME,
            "temperature": 0.7
        },
        personality_traits=["严谨", "数据驱动", "前瞻性"],
        expertise_areas=["宏观经济", "货币政策", "全球经济趋势", "通胀分析"]
    )
    analysts.append(agent_service.create_agent(macro_analyst))
    
    # 2. 投资策略分析师
    strategy_analyst = AgentConfig(
        name="李华",
        role="strategist",
        system_prompt="你是一位经验丰富的投资策略分析师，擅长制定投资策略、识别市场机会、分析资产类别表现。",
        llm_config={
            "model_name": settings.DEFAULT_MODEL_NAME,
            "temperature": 0.8
        },
        personality_traits=["战略性思维", "创新", "灵活"],
        expertise_areas=["投资策略", "市场机会识别", "资产类别分析", "行业轮动"]
    )
    analysts.append(agent_service.create_agent(strategy_analyst))
    
    # 3. 风险控制专家
    risk_expert = AgentConfig(
        name="王静",
        role="risk_manager",
        system_prompt="你是一位专业的风险控制专家，擅长识别和评估投资风险、设计风险管理策略、控制投资组合风险。",
        llm_config={
            "model_name": settings.DEFAULT_MODEL_NAME,
            "temperature": 0.6
        },
        personality_traits=["谨慎", "系统性思维", "细节导向"],
        expertise_areas=["风险评估", "风险管理", "投资组合优化", "尾部风险分析"]
    )
    analysts.append(agent_service.create_agent(risk_expert))
    
    # 4. 资产配置顾问
    allocation_advisor = AgentConfig(
        name="赵强",
        role="advisor",
        system_prompt="你是一位资深资产配置顾问，擅长根据市场环境和客户需求设计最优资产配置方案，平衡风险和收益。",
        llm_config={
            "model_name": settings.DEFAULT_MODEL_NAME,
            "temperature": 0.75
        },
        personality_traits=["平衡", "客户导向", "实用主义"],
        expertise_areas=["资产配置", "投资组合构建", "收益风险平衡", "长期投资规划"]
    )
    analysts.append(agent_service.create_agent(allocation_advisor))
    
    return analysts