from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any, Optional
import asyncio

from app.models.debate import Debate, DebateMessage, DebateStatus
from app.models.agent import Agent
from app.models.schemas import (
    DebateStartRequest,
    DebateStatusResponse,
    DebateResultResponse,
    DebateMessageSchema
)
from app.services.agent_service import AgentService
from app.core.config import settings
from app.core.redis import redis_client
from app.utils.debate_manager import DebateManager

class DebateService:
    def __init__(self, db: Session):
        self.db = db
        self.agent_service = AgentService(db)
    
    def start_debate(self, request: DebateStartRequest, background_tasks: BackgroundTasks) -> Debate:
        """启动一场新的辩论"""
        # 1. 验证Agent IDs
        agents = self.agent_service.get_agent_by_ids(request.agent_ids)
        
        # 2. 创建辩论记录
        debate = Debate(
            topic=request.topic,
            status=DebateStatus.CREATED.value,
            rounds=request.rounds,
            max_duration_minutes=request.max_duration_minutes,
            progress=0.0,
            agent_ids=request.agent_ids,
            conclusion_requirements=request.conclusion_requirements,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(debate)
        self.db.commit()
        self.db.refresh(debate)
        
        # 3. 为辩论配置每个Agent
        for agent in agents:
            self.agent_service.configure_agent_for_debate(
                agent_id=str(agent.id),
                topic=request.topic
            )
        
        # 4. 使用FastAPI的BackgroundTasks异步启动辩论处理
        debate_id = str(debate.id)
        self.update_debate_status(debate_id, DebateStatus.RUNNING)
        
        # 创建一个同步函数包装异步的run_debate方法
        def run_debate_sync():
            asyncio.run(self.run_debate(debate_id))
            
        # 添加到后台任务
        background_tasks.add_task(run_debate_sync)
        
        return debate
    
    def get_debate(self, session_id: str) -> Debate:
        """获取辩论会话信息"""
        # 将字符串格式的session_id转换为UUID对象
        try:
            debate_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的辩论会话ID格式: {session_id}"
            )
            
        debate = self.db.query(Debate).filter(Debate.id == debate_uuid).first()
        
        if not debate:
            raise HTTPException(
                status_code=404,
                detail=f"未找到ID为{session_id}的辩论会话"
            )
        
        return debate
    
    def get_debate_status(self, session_id: str) -> DebateStatusResponse:
        """获取辩论状态"""
        debate = self.get_debate(session_id)
        
        # 计算预计完成时间
        estimated_completion_time = None
        if debate.status == "running" and debate.created_at:
            # 基于已用时间和进度估算
            elapsed_minutes = (datetime.utcnow() - debate.created_at).total_seconds() / 60
            if debate.progress > 0:
                total_estimated_minutes = elapsed_minutes / debate.progress
                remaining_minutes = total_estimated_minutes - elapsed_minutes
                estimated_completion_time = datetime.utcnow() + timedelta(minutes=remaining_minutes)
            else:
                # 初始阶段，使用最大持续时间估算
                estimated_completion_time = debate.created_at + timedelta(minutes=debate.max_duration_minutes)
        
        # 计算当前轮次
        current_round = None
        if debate.status == "running" and debate.progress > 0:
            current_round = int((debate.progress / 100) * debate.rounds) + 1
        
        return DebateStatusResponse(
            session_id=session_id,
            status=debate.status,
            progress=debate.progress / 100.0,  # 将0.0-100.0范围转换为0.0-1.0范围
            current_round=current_round,
            total_rounds=debate.rounds,
            started_at=debate.created_at,
            estimated_completion_time=estimated_completion_time
        )
    
    def get_debate_messages(self, session_id: str) -> List[DebateMessage]:
        """获取辩论的所有消息历史记录"""
        # 验证辩论是否存在
        self.get_debate(session_id)
        
        # 将字符串格式的session_id转换为UUID对象
        try:
            debate_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的辩论会话ID格式: {session_id}"
            )
        
        # 获取辩论历史消息
        messages = self.db.query(DebateMessage).filter(
            DebateMessage.debate_id == debate_uuid
        ).order_by(DebateMessage.timestamp).all()
        
        return messages
    
    def get_debate_result(self, session_id: str) -> DebateResultResponse:
        """获取辩论结果"""
        debate = self.get_debate(session_id)
        
        # 如果辩论未完成，返回当前状态
        if debate.status not in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"辩论尚未完成，当前状态：{debate.status}"
            )
        
        # 将字符串格式的session_id转换为UUID对象
        try:
            debate_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的辩论会话ID格式: {session_id}"
            )
        
        # 获取辩论历史消息
        messages = self.db.query(DebateMessage).filter(
            DebateMessage.debate_id == debate_uuid
        ).order_by(DebateMessage.timestamp).all()
        
        # 转换为消息模式
        conversation_history = []
        for message in messages:
            conversation_history.append(
                DebateMessageSchema(
                    id=str(message.id),
                    debate_id=str(message.debate_id),
                    agent_id=str(message.agent_id),
                    agent_name=message.agent_name,
                    agent_role=message.agent_role,
                    round_number=message.round_number,
                    content=message.content,
                    timestamp=message.timestamp
                )
            )
        
        return DebateResultResponse(
            session_id=session_id,
            status=debate.status,
            progress=debate.progress,
            preliminary_insights=debate.preliminary_insights or [],
            final_conclusion=debate.final_conclusion,
            key_arguments=debate.key_arguments or {},
            consensus_points=debate.consensus_points or [],
            divergent_views=debate.divergent_views or [],
            confidence_score=debate.confidence_score or 0.0,
            created_at=debate.created_at,
            updated_at=debate.updated_at,
            conversation_history=conversation_history
        )
    
    async def run_debate(self, session_id: str):
        """执行辩论流程"""
        debate = self.get_debate(session_id)
        
        try:
            # 1. 更新辩论状态为running
            debate.status = "running"
            debate.updated_at = datetime.utcnow()
            self.db.commit()
            
            # 2. 获取参与辩论的Agent
            agents = self.agent_service.get_agent_by_ids(debate.agent_ids)
            
            # 3. 创建AgentScope Agent实例
            agentscope_agents = []
            for agent in agents:
                agentscope_agents.append(
                    self.agent_service.create_agentscope_agent(agent)
                )
            
            # 4. 创建辩论管理器
            debate_manager = DebateManager(
                agents=agentscope_agents,
                topic=debate.topic,
                rounds=debate.rounds,
                db=self.db,
                debate_id=session_id
            )
            
            # 5. 执行辩论轮次
            await debate_manager.run_debate_rounds()
            
            # 6. 生成结论
            conclusion_data = await debate_manager.generate_conclusion()
            
            # 7. 更新辩论结果
            debate.status = "completed"
            debate.progress = 100.0
            debate.final_conclusion = conclusion_data.get("final_conclusion")
            debate.confidence_score = conclusion_data.get("confidence_score", 0.0)
            debate.consensus_points = conclusion_data.get("consensus_points", [])
            debate.divergent_views = conclusion_data.get("divergent_views", [])
            debate.key_arguments = conclusion_data.get("key_arguments", {})
            debate.preliminary_insights = conclusion_data.get("preliminary_insights", [])
            debate.updated_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            # 处理辩论过程中的错误
            debate.status = "failed"
            debate.updated_at = datetime.utcnow()
            self.db.commit()
            
            # 记录错误日志
            # 实际实现时应该使用logger
            print(f"辩论执行错误: {str(e)}")
            
            # 可以在这里添加通知机制
    
    def save_debate_message(self, debate_id: str, agent_id: str, agent_name: str, 
                           agent_role: str, round_number: int, content: str) -> DebateMessage:
        """保存辩论消息"""
        try:
            # 确保UUID字段被正确转换
            from uuid import UUID
            
            message = DebateMessage(
                debate_id=UUID(debate_id) if isinstance(debate_id, str) else debate_id,
                agent_id=UUID(agent_id) if isinstance(agent_id, str) else agent_id,
                agent_name=agent_name,
                agent_role=agent_role,
                round_number=round_number,
                content=content,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            return message
        except Exception as e:
            # 记录错误并回滚事务
            self.db.rollback()
            print(f"保存辩论消息时发生错误: {str(e)}")
            # 创建一个包含错误信息的消息对象返回
            return DebateMessage(
                id=None,  # 将由数据库自动生成
                debate_id=debate_id,
                agent_id=agent_id,
                agent_name=agent_name,
                agent_role=agent_role,
                round_number=round_number,
                content=f"[错误] 无法保存消息: {str(e)}",
                timestamp=datetime.utcnow()
            )
    
    def update_debate_progress(self, session_id: str, progress: float):
        """更新辩论进度"""
        debate = self.get_debate(session_id)
        debate.progress = min(max(progress, 0.0), 100.0)
        debate.updated_at = datetime.utcnow()
        self.db.commit()
        
    def update_debate_status(self, session_id: str, status: DebateStatus):
        """更新辩论状态"""
        debate = self.get_debate(session_id)
        debate.status = status.value
        debate.updated_at = datetime.utcnow()
        self.db.commit()
        
    def cancel_debate(self, session_id: str) -> Debate:
        """取消正在进行的辩论"""
        debate = self.get_debate(session_id)
        
        # 只能取消未完成的辩论
        if debate.status in [DebateStatus.COMPLETED.value, DebateStatus.FAILED.value, DebateStatus.EXPIRED.value]:
            raise HTTPException(
                status_code=400,
                detail=f"辩论已经{debate.status}，无法取消"
            )
            
        # 更新状态为已取消
        debate.status = DebateStatus.FAILED.value
        debate.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(debate)
        
        return debate