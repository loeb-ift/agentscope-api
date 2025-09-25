from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.schemas import (
    DebateStartRequest,
    DebateStartResponse,
    DebateStatusResponse,
    DebateResultResponse,
    N8NOptimizedResponse,
    DebateFromTemplateRequest,
    DebateFromDataSourceRequest,
    DebateFromDatasetRequest
)
from app.services.debate_service import DebateService
from app.services.agent_service import AgentService
from app.utils.response_parser import ResponseParser
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.post("/start", response_model=DebateStartResponse, summary="啟動多Agent辯論")
def start_debate(
    request: DebateStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    啟動一場多Agent辯論
    
    - **topic**: 辯論主題
    - **agent_ids**: 參與辯論的Agent ID列表
    - **rounds**: 辯論輪數（可選，默認3輪）
    - **max_duration_minutes**: 最大持續時間（分鐘）（可選）
    - **conclusion_requirements**: 結論生成要求（可選）
    - **webhook_url**: 辯論完成後的回調URL（可選）
    """
    debate_service = DebateService(db)
    agent_service = AgentService(db)
    
    # 驗證所有Agent是否存在且活躍
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
        message="辯論已啟動，請稍後查詢結果",
        created_at=debate.created_at
    )

@router.post("/from-template", response_model=DebateStartResponse, summary="從模板創建並啟動辯論")
def create_debate_from_template(
    request: DebateFromTemplateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    從預定義的模板創建並啟動一場辯論。

    - **template_name**: 要使用的辯論模板的名稱。
    """
    debate_service = DebateService(db)
    
    # 调用服务层函数来处理基于模板的辩论创建
    debate = debate_service.create_debate_from_template(
        template_name=request.template_name,
        background_tasks=background_tasks
    )
    
    return DebateStartResponse(
        session_id=str(debate.id),
        status=debate.status,
        message="基於模板的辯論已成功啟動",
        created_at=debate.created_at
    )

@router.post("/from-data-source", response_model=DebateStartResponse, summary="從數據源創建並啟動辯論")
def start_debate_from_data_source(
   request: DebateFromDataSourceRequest,
   background_tasks: BackgroundTasks,
   db: Session = Depends(get_db)
):
   """
   從指定的數據源和SQL查詢創建並啟動一場辯論。
   """
   debate_service = DebateService(db)
   
   # 调用服务层函数来处理基于数据源的辩论创建
   debate = debate_service.start_debate_from_data(
       request=request,
       background_tasks=background_tasks
   )
   
   return DebateStartResponse(
       session_id=str(debate.id),
       status=debate.status,
       message="基於數據源的辯論已成功啟動",
       created_at=debate.created_at
   )

@router.post("/from-dataset", response_model=DebateStartResponse, summary="從數據集創建並啟動辯論")
def start_debate_from_dataset(
  request: DebateFromDatasetRequest,
  background_tasks: BackgroundTasks,
  db: Session = Depends(get_db)
):
  """
  從指定的數據集創建並啟動一場辯論。
  """
  debate_service = DebateService(db)
  
  # 调用服务层函数来处理基于数据集的辩论创建
  debate = debate_service.start_debate_from_dataset(
      request=request,
      background_tasks=background_tasks
  )
  
  return DebateStartResponse(
      session_id=str(debate.id),
      status=debate.status,
      message="基於數據集的辯論已成功啟動",
      created_at=debate.created_at
  )

@router.get("/{session_id}/status", response_model=DebateStatusResponse, summary="獲取辯論狀態")
def get_debate_status(
   session_id: str,
    db: Session = Depends(get_db)
):
    """
    獲取指定辯論會話的當前狀態
    
    - **session_id**: 辯論會話的唯一標識
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

@router.get("/{session_id}/result", response_model=N8NOptimizedResponse, summary="獲取辯論結果")
def get_debate_result(
    session_id: str,
    format: str = "n8n",  # 預設為n8n優化格式
    db: Session = Depends(get_db)
):
    """
    獲取指定辯論會話的最終結果
    
    - **session_id**: 辯論會話的唯一標識
    - **format**: 結果格式（可選，預設為"n8n"）
    """
    debate_service = DebateService(db)
    debate = debate_service.get_debate(session_id)
    
    if debate.status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"辯論尚未完成，當前狀態: {debate.status}"
        )
    
    # 獲取辯論訊息和結果
    debate_messages = debate_service.get_debate_messages(session_id)
    debate_result = debate_service.get_debate_result(session_id)
    
    # 解析為n8n優化格式
    parser = ResponseParser()
    
    # 提取關鍵論點
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
    
    # 構建響應
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

@router.get("/{session_id}/history", summary="獲取辯論歷史記錄")
def get_debate_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    獲取指定辯論會話的完整歷史記錄
    
    - **session_id**: 辯論會話的唯一標識
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

@router.post("/{session_id}/cancel", summary="取消辯論")
def cancel_debate(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    取消正在進行的辯論
    
    - **session_id**: 辯論會話的唯一標識
    """
    debate_service = DebateService(db)
    debate = debate_service.cancel_debate(session_id)
    
    return {
        "message": "辯論已取消",
        "session_id": session_id,
        "status": debate.status,
        "cancelled_at": debate.updated_at
    }