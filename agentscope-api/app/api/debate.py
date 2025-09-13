from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.schemas import (
    DebateStartRequest,
    DebateStartResponse,
    DebateStatusResponse,
    DebateResultResponse,
    N8NOptimizedResponse
)
from app.services.debate_service import DebateService
from app.services.agent_service import AgentService
from app.utils.response_parser import ResponseParser
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.post("/start", response_model=DebateStartResponse, summary="启动多Agent辩论")
def start_debate(
    request: DebateStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    启动一场多Agent辩论
    
    - **topic**: 辩论主题
    - **agent_ids**: 参与辩论的Agent ID列表
    - **rounds**: 辩论轮数（可选，默认3轮）
    - **max_duration_minutes**: 最大持续时间（分钟）（可选）
    - **conclusion_requirements**: 结论生成要求（可选）
    - **webhook_url**: 辩论完成后的回调URL（可选）
    """
    debate_service = DebateService(db)
    agent_service = AgentService(db)
    
    # 验证所有Agent是否存在且活跃
    for agent_id in request.agent_ids:
        agent = agent_service.get_agent(agent_id)
        if not agent or not agent.is_active:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} 不存在或未激活"
            )
    
    # 启动辩论
    debate = debate_service.start_debate(request, background_tasks)
    
    # 暂时不使用Celery异步执行辩论任务，直接在API中返回响应
    # 注释掉Celery任务调用，以解决连接问题
    # from app.tasks.debate_tasks import run_debate
    # run_debate.delay(str(debate.id), request.agent_ids, request.topic, request.rounds)
    
    return DebateStartResponse(
        session_id=str(debate.id),
        status=debate.status,
        message="辩论已启动，请稍后查询结果",
        created_at=debate.created_at
    )

@router.get("/{session_id}/status", response_model=DebateStatusResponse, summary="获取辩论状态")
def get_debate_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定辩论会话的当前状态
    
    - **session_id**: 辩论会话的唯一标识
    """
    debate_service = DebateService(db)
    debate = debate_service.get_debate(session_id)
    debate_status = debate_service.get_debate_status(session_id)
    
    return DebateStatusResponse(
        session_id=session_id,
        status=debate_status.status,
        progress=debate_status.progress,
        current_round=debate_status.current_round,
        total_rounds=debate_status.total_rounds,
        topic=debate.topic,
        started_at=debate.created_at,
        updated_at=debate.updated_at,
        estimated_completion_time=debate_status.estimated_completion_time
    )

@router.get("/{session_id}/result", response_model=N8NOptimizedResponse, summary="获取辩论结果")
def get_debate_result(
    session_id: str,
    format: str = "n8n",  # 默认为n8n优化格式
    db: Session = Depends(get_db)
):
    """
    获取指定辩论会话的最终结果
    
    - **session_id**: 辩论会话的唯一标识
    - **format**: 结果格式（可选，默认为"n8n"）
    """
    debate_service = DebateService(db)
    debate = debate_service.get_debate(session_id)
    
    if debate.status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"辩论尚未完成，当前状态: {debate.status}"
        )
    
    # 获取辩论消息和结果
    debate_messages = debate_service.get_debate_messages(session_id)
    debate_result = debate_service.get_debate_result(session_id)
    
    # 解析为n8n优化格式
    parser = ResponseParser()
    
    # 提取关键论点
    key_arguments = parser.extract_key_arguments_by_role(
        [
            {
                "role": message.agent_role,
                "response": message.content,
                "round": message.round_number
            }
            for message in debate_messages
        ]
    )
    
    # 提取初步洞察
    preliminary_insights = parser.extract_preliminary_insights(
        [
            {
                "agent": message.agent_id,
                "role": message.agent_role,
                "response": message.content,
                "round": message.round_number
            }
            for message in debate_messages
        ]
    )
    
    # 构建响应
    response = parser.parse_debate_result_to_n8n_format(
        session_id=session_id,
        status=debate.status,
        progress=1.0 if debate.status == "completed" else 0.0,
        preliminary_insights=preliminary_insights,
        final_conclusion=debate_result.final_conclusion if debate_result else None,
        key_arguments=key_arguments,
        consensus_points=debate_result.consensus_points if debate_result else [],
        divergent_views=debate_result.divergent_views if debate_result else [],
        confidence_score=debate_result.confidence_score if debate_result else 0.0
    )
    
    return response

@router.get("/{session_id}/history", summary="获取辩论历史记录")
def get_debate_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定辩论会话的完整历史记录
    
    - **session_id**: 辩论会话的唯一标识
    """
    debate_service = DebateService(db)
    debate = debate_service.get_debate(session_id)
    debate_messages = debate_service.get_debate_messages(session_id)
    
    parser = ResponseParser()
    formatted_history = parser.format_conversation_history_for_display(
        [
            {
                "agent": message.agent_id,
                "role": message.agent_role,
                "response": message.content,
                "round": message.round_number,
                "timestamp": message.timestamp
            }
            for message in debate_messages
        ]
    )
    
    return {
        "session_id": session_id,
        "topic": debate.topic,
        "total_rounds": debate.rounds,
        "history": formatted_history,
        "status": debate.status,
        "started_at": debate.created_at,
        "updated_at": debate.updated_at
    }

@router.post("/{session_id}/cancel", summary="取消辩论")
def cancel_debate(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    取消正在进行的辩论
    
    - **session_id**: 辩论会话的唯一标识
    """
    debate_service = DebateService(db)
    debate = debate_service.cancel_debate(session_id)
    
    return {
        "message": "辩论已取消",
        "session_id": session_id,
        "status": debate.status,
        "cancelled_at": debate.updated_at
    }