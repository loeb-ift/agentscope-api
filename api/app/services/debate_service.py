from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any, Optional
import asyncio
import json
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.engine import URL

from app.models.schemas import (
    AgentCreateRequest,
    DebateFromDataSourceRequest,
    DebateFromDatasetRequest,
)

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
        """啟動一場新的辯論"""
        try:
            # 1. 驗證Agent IDs
            agents = self.agent_service.get_agent_by_ids(request.agent_ids)
            
            # 1.1 驗證 Moderator ID
            if request.moderator_id:
                moderator = self.agent_service.get_agent(request.moderator_id)
                if not moderator or not moderator.is_active:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Moderator Agent {request.moderator_id} 不存在或未激活"
                    )

            # 2. 創建辯論記錄
            debate = Debate(
                topic=request.topic,
                status=DebateStatus.CREATED.value,
                rounds=request.rounds,
                max_duration_minutes=request.max_duration_minutes,
                progress=0.0,
                agent_ids=request.agent_ids,
                moderator_id=request.moderator_id,
                moderator_prompt=request.moderator_prompt,
                conclusion_requirements=request.conclusion_requirements,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(debate)
            self.db.commit()
            self.db.refresh(debate)
            
            # 3. 为辩论配置每个Agent
            for agent in agents:
                # 获取辩论请求中的llm_config参数
                llm_config = request.llm_config if request.llm_config else {}
                
                self.agent_service.configure_agent_for_debate(
                    agent_id=str(agent.id),
                    topic=request.topic,
                    llm_config=llm_config
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
        except Exception as e:
            # 记录错误并返回500
            # 在实际应用中，这里应该使用更强大的日志记录器
            print(f"Error starting debate: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred while starting the debate: {str(e)}"
            )

    def start_debate_from_data(self, request: DebateFromDataSourceRequest, background_tasks: BackgroundTasks) -> Debate:
        """从数据源启动一场新的辩论"""
        # 1. 动态构建数据库连接字符串
        try:
            db_url = URL.create(
                drivername=request.data_source.db_type,
                username=request.data_source.db_user,
                password=request.data_source.db_password,
                host=request.data_source.db_host,
                port=request.data_source.db_port,
                database=request.data_source.db_name,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无效的数据库类型: {e}")

        # 2. 安全连接与数据获取
        try:
            engine = create_engine(db_url, connect_args={"connect_timeout": 10})
            with engine.connect() as connection:
                df = pd.read_sql_query(text(request.sql_query), connection)
        except OperationalError as e:
            raise HTTPException(status_code=400, detail=f"数据库连接失败: {e}")
        except ProgrammingError as e:
            raise HTTPException(status_code=400, detail=f"SQL查询错误: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库操作未知错误: {e}")

        if df.empty:
            raise HTTPException(status_code=400, detail="SQL查询未返回任何数据。")

        # 3. 调用数据分析师 Agent
        try:
            # 假设 'chief-data-analyst' 是预创建的Agent的固定名称或ID
            analyst_agent_model = self.agent_service.get_agent_by_name("首席数据分析师")
            if not analyst_agent_model:
                    raise HTTPException(status_code=404, detail="未找到'首席数据分析师' Agent。")

            analyst_agent = self.agent_service.create_agentscope_agent(analyst_agent_model)

            # 检查是否有提示词覆盖
            if request.data_analyst_prompt_override:
                analyst_agent.system_prompt = request.data_analyst_prompt_override
            
            # 将DataFrame转换为Markdown格式的字符串
            data_string = df.to_markdown(index=False)
            
            # 调用Agent进行分析
            # 注意：这里的调用方式取决于AgentScope的具体实现，可能需要调整
            analysis_report = analyst_agent(data_string)
            
            if not analysis_report or not analysis_report.content:
                raise HTTPException(status_code=500, detail="数据分析步骤失败，未能生成报告。")

            analysis_content = analysis_report.content

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据分析Agent调用失败: {e}")

        # 4. 整合报告并启动辩论
        new_topic = f"原始主题: {request.topic}\n\n背景材料 (数据分析报告):\n{analysis_content}"

        start_request = DebateStartRequest(
            topic=new_topic,
            agent_ids=request.agent_ids,
            moderator_id=request.moderator_id,
            rounds=request.rounds,
            max_duration_minutes=request.max_duration_minutes,
            conclusion_requirements=request.conclusion_requirements,
            llm_config=request.llm_config,
            moderator_prompt=request.moderator_prompt,
        )

        return self.start_debate(start_request, background_tasks)

    def start_debate_from_dataset(self, request: DebateFromDatasetRequest, background_tasks: BackgroundTasks) -> Debate:
        """从数据集启动一场新的辩论"""
        # Placeholder implementation
        print(f"Starting debate from dataset: {request.dataset_name}")

        # In the future, this method will:
        # 1. Connect to the database.
        # 2. Make the dataset available to the agents.
        # 3. Create and start the debate.

        # For now, we'll just create a debate record and return it.
        debate = Debate(
            topic=f"Debate on dataset: {request.dataset_name}",
            status=DebateStatus.CREATED.value,
            rounds=request.rounds,
            max_duration_minutes=request.max_duration_minutes,
            progress=0.0,
            agent_ids=request.agent_ids,
            moderator_id=request.moderator_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(debate)
        self.db.commit()
        self.db.refresh(debate)
        return debate

    def create_debate_from_template(self, template_name: str, background_tasks: BackgroundTasks) -> Debate:
        """从模板创建并启动辩论"""
        # 1. 加载模板文件
        template_path = f"app/debate_templates/{template_name}.json"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"模板 '{template_name}' 不存在")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"模板文件 '{template_name}' 格式错误")

        # 2. 动态创建或获取Agents
        agent_ids = []
        for agent_config_data in template.get("agents", []):
            # 使用AgentCreateRequest模型进行验证和类型转换
            agent_config = AgentCreateRequest(**agent_config_data)
            
            # 创建Agent
            created_agent = self.agent_service.create_agent(agent_config)
            agent_ids.append(str(created_agent.id))

        # 3. 构建DebateStartRequest
        debate_params = template.get("debate_parameters", {})
        
        # 确保所有参与者ID都是字符串
        agent_ids_str = [str(id) for id in agent_ids]
        
        # 自动选择第一个Agent作为主持人
        if not agent_ids_str:
            raise HTTPException(status_code=400, detail="模板中必须至少包含一个Agent")
        
        moderator_id = agent_ids_str[0]
        
        # 其他辩手
        debater_ids = agent_ids_str[1:]
        
        # 如果只有一个agent，则无法进行辩论
        if not debater_ids:
            raise HTTPException(status_code=400, detail="辩论需要至少两个Agents（一个主持人和一个辩手）")

        start_request = DebateStartRequest(
            topic=debate_params.get("topic", "无主题"),
            agent_ids=debater_ids,
            moderator_id=moderator_id,
            rounds=debate_params.get("rounds", 3),
            max_duration_minutes=debate_params.get("max_duration_minutes", 30),
            conclusion_requirements=debate_params.get("conclusion_requirements"),
            llm_config=debate_params.get("llm_config")
        )

        # 4. 调用现有的start_debate服务
        return self.start_debate(start_request, background_tasks)

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
            # 確保傳遞的是字串列表
            agent_ids_str = [str(agent_id) for agent_id in debate.agent_ids]
            agents = self.agent_service.get_agent_by_ids(agent_ids_str)
            
            # 3. 建立AgentScope Agent實例
            agentscope_agents = []
            for agent in agents:
                agentscope_agents.append(
                    self.agent_service.create_agentscope_agent(agent)
                )
            
            moderator_agent = None
            if debate.moderator_id:
                # 確保傳遞的是字串
                moderator = self.agent_service.get_agent(str(debate.moderator_id))
                # 如果有提供主持人提示詞，則覆蓋從資料庫讀取的提示詞
                if debate.moderator_prompt:
                    moderator.system_prompt = debate.moderator_prompt
                
                moderator_agent = self.agent_service.create_agentscope_agent(moderator)

            # 4. 创建辩论管理器
            debate_manager = DebateManager(
                agents=agentscope_agents,
                topic=debate.topic,
                rounds=debate.rounds,
                db=self.db,
                debate_id=session_id,
                moderator=moderator_agent
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
            
            # 記錄錯誤日誌
            # 實際實現時應該使用logger
            print(f"辯論執行錯誤: {str(e)}")

            # 可以在這裡新增通知機制
    
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