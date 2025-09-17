from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.models.schemas import (
    AgentCreateRequest,
    AgentCreateResponse,
    AgentResponse,
    AgentUpdateRequest,
    AgentConfigureForDebateRequest,
    AgentConfigureResponse
)
from app.services.agent_service import AgentService
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.post("/create", response_model=AgentCreateResponse, summary="創建新Agent")
def create_agent(
    request: AgentCreateRequest,
    db: Session = Depends(get_db)
):
    """
    創建一個新的Agent實例
    
    - **name**: Agent名稱
    - **role**: Agent角色類型
    - **system_prompt**: 系統提示詞
    - **llm_config**: 模型配置
    - **personality_traits**: 個性特徵列表
    - **expertise_areas**: 專業領域列表
    """
    agent_service = AgentService(db)
    agent = agent_service.create_agent(request)
    
    return AgentCreateResponse(
        agent_id=str(agent.id),
        name=agent.name,
        role=agent.role,
        created_at=agent.created_at
    )

@router.get("/{agent_id}", response_model=AgentResponse, summary="獲取Agent詳情")
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    根據ID獲取Agent的詳細信息
    
    - **agent_id**: Agent的唯一标识
    """
    agent_service = AgentService(db)
    agent = agent_service.get_agent(agent_id)
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        role=agent.role,
        system_prompt=agent.system_prompt,
        llm_config=agent.model_config,  # 映射数据库字段到模型字段
        personality_traits=agent.personality_traits,
        expertise_areas=agent.expertise_areas,
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )

@router.get("/", response_model=List[AgentResponse], summary="获取Agent列表")
def get_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取所有活跃的Agent列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数
    """
    agent_service = AgentService(db)
    agents = agent_service.get_agents(skip=skip, limit=limit)
    
    return [
        AgentResponse(
            id=str(agent.id),
            name=agent.name,
            role=agent.role,
            system_prompt=agent.system_prompt,
            llm_config=agent.model_config,  # 映射数据库字段到模型字段
            personality_traits=agent.personality_traits,
            expertise_areas=agent.expertise_areas,
            is_active=agent.is_active,
            created_at=agent.created_at,
            updated_at=agent.updated_at
        )
        for agent in agents
    ]

@router.put("/{agent_id}", response_model=AgentResponse, summary="更新Agent信息")
def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新Agent的信息
    
    - **agent_id**: Agent的唯一标识
    - **name**: Agent名称（可选）
    - **role**: Agent角色类型（可选）
    - **system_prompt**: 系统提示词（可选）
    - **llm_config**: 模型配置（可选）
    - **personality_traits**: 个性特征列表（可选）
    - **expertise_areas**: 专业领域列表（可选）
    - **is_active**: 是否激活（可选）
    """
    agent_service = AgentService(db)
    agent = agent_service.update_agent(agent_id, request)
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        role=agent.role,
        system_prompt=agent.system_prompt,
        llm_config=agent.model_config,  # 映射数据库字段到模型字段
        personality_traits=agent.personality_traits,
        expertise_areas=agent.expertise_areas,
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )

@router.delete("/{agent_id}", summary="停用Agent")
def deactivate_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    停用指定的Agent（软删除）
    
    - **agent_id**: Agent的唯一标识
    """
    agent_service = AgentService(db)
    agent = agent_service.deactivate_agent(agent_id)
    
    return {
        "message": f"Agent {agent.name} 已停用",
        "agent_id": str(agent.id),
        "status": "inactive"
    }

@router.post("/{agent_id}/configure", response_model=AgentConfigureResponse, summary="配置Agent用于辩论")
def configure_agent_for_debate(
    agent_id: str,
    request: AgentConfigureForDebateRequest,
    db: Session = Depends(get_db)
):
    """
    为特定辩论主题配置Agent
    
    - **agent_id**: Agent的唯一标识
    - **debate_topic**: 辩论主题
    - **additional_instructions**: 额外的指令（可选）
    - **llm_config**: 模型配置（可选）
    """
    agent_service = AgentService(db)
    agent = agent_service.configure_agent_for_debate(
        agent_id=agent_id,
        topic=request.debate_topic,
        additional_instructions=request.additional_instructions,
        llm_config=request.llm_config
    )
    
    return AgentConfigureResponse(
        agent_id=str(agent.id),
        updated_at=agent.updated_at
    )

@router.get("/roles", summary="获取支持的Agent角色列表")
def get_supported_roles():
    """
    获取系统支持的所有Agent角色类型
    """
    return {
        "roles": settings.AGENT_ROLES
    }