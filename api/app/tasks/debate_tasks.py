from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.debate_service import DebateService
from app.services.agent_service import AgentService
from app.utils.debate_manager import DebateManager
from app.models.debate import Debate, DebateStatus
from app.core.config import settings
import time
import httpx
from typing import List, Dict, Any

logger = get_task_logger(__name__)

@shared_task(name="debate.run_debate", bind=True)
def run_debate(self, session_id: str, agent_ids: List[str], topic: str, rounds: int = 3):
    """
    异步运行辩论任务
    
    Args:
        session_id: 辩论会话ID
        agent_ids: 参与辩论的Agent ID列表
        topic: 辩论主题
        rounds: 辩论轮数
    """
    logger.info(f"开始辩论任务: session_id={session_id}, topic={topic}, rounds={rounds}")
    
    # 获取数据库会话
    db = next(get_db())
    debate_service = DebateService(db)
    agent_service = AgentService(db)
    
    try:
        # 1. 获取辩论信息
        debate = debate_service.get_debate(session_id)
        if not debate:
            logger.error(f"辩论会话不存在: {session_id}")
            return {"status": "failed", "reason": "辩论会话不存在"}
        
        # 2. 更新辩论状态为运行中
        debate_service.update_debate_status(session_id, DebateStatus.RUNNING)
        
        # 3. 获取参与辩论的Agent实例
        agents = []
        for agent_id in agent_ids:
            agent = agent_service.get_agent(agent_id)
            if not agent or not agent.is_active:
                logger.warning(f"Agent未找到或未激活: {agent_id}")
                continue
            agents.append(agent)
        
        if not agents:
            logger.error(f"没有活跃的Agent参与辩论: {session_id}")
            debate_service.update_debate_status(session_id, DebateStatus.FAILED)
            return {"status": "failed", "reason": "没有活跃的Agent参与辩论"}
        
        # 4. 创建辩论管理器并开始辩论
        debate_manager = DebateManager(agents, topic, rounds, db_session=db)
        
        # 5. 执行辩论轮次
        total_steps = rounds * len(agents)
        current_step = 0
        
        for round_num in range(1, rounds + 1):
            logger.info(f"开始辩论轮次 {round_num}/{rounds}: {session_id}")
            
            # 更新当前轮次
            debate_service.update_debate_progress(session_id, round_num, 0)
            
            for agent in agents:
                try:
                    # 获取Agent的响应
                    response = debate_manager.get_agent_response(agent, topic)
                    
                    # 保存Agent的发言
                    debate_service.save_debate_message(
                        session_id=session_id,
                        agent_id=str(agent.id),
                        role=agent.role,
                        content=response,
                        round=round_num
                    )
                    
                    # 更新进度
                    current_step += 1
                    progress = current_step / total_steps
                    debate_service.update_debate_progress(session_id, round_num, progress)
                    
                    # 短暂暂停，避免API调用过于频繁
                    time.sleep(settings.DEBATE_STEP_DELAY)
                    
                except Exception as e:
                    logger.error(f"Agent {agent.name} 响应失败: {str(e)}")
                    continue
        
        # 6. 生成辩论结论
        conclusion_result = generate_conclusion.delay(session_id)
        
        # 7. 更新辩论状态为待结论生成
        debate_service.update_debate_status(session_id, DebateStatus.AWAITING_CONCLUSION)
        
        logger.info(f"辩论轮次完成，等待结论生成: {session_id}")
        return {"status": "running", "step": "awaiting_conclusion"}
        
    except Exception as e:
        logger.error(f"辩论任务执行失败: {str(e)}")
        debate_service.update_debate_status(session_id, DebateStatus.FAILED)
        return {"status": "failed", "reason": str(e)}
    finally:
        # 关闭数据库连接
        db.close()

@shared_task(name="debate.generate_conclusion", bind=True)
def generate_conclusion(self, session_id: str):
    """
    生成辩论结论
    
    Args:
        session_id: 辩论会话ID
    """
    logger.info(f"开始生成辩论结论: {session_id}")
    
    # 获取数据库会话
    db = next(get_db())
    debate_service = DebateService(db)
    
    try:
        # 1. 获取辩论信息和消息
        debate = debate_service.get_debate(session_id)
        if not debate:
            logger.error(f"辩论会话不存在: {session_id}")
            return {"status": "failed", "reason": "辩论会话不存在"}
        
        debate_messages = debate_service.get_debate_messages(session_id)
        
        # 2. 创建辩论管理器并生成结论
        # 注意：这里我们需要重新创建一个DebateManager实例，但不需要Agent实例来生成结论
        from app.utils.debate_manager import DebateManager
        debate_manager = DebateManager([], debate.topic, debate.total_rounds, db_session=db)
        
        # 3. 生成最终结论
        conclusion_result = debate_manager.generate_conclusion(debate_messages)
        
        # 4. 保存辩论结果
        debate_service.save_debate_result(
            session_id=session_id,
            final_conclusion=conclusion_result["final_conclusion"],
            key_arguments=conclusion_result["key_arguments"],
            consensus_points=conclusion_result["consensus_points"],
            divergent_views=conclusion_result["divergent_views"],
            confidence_score=conclusion_result["confidence_score"]
        )
        
        # 5. 更新辩论状态为已完成
        debate_service.update_debate_status(session_id, DebateStatus.COMPLETED)
        debate_service.update_debate_progress(session_id, debate.total_rounds, 1.0)
        
        logger.info(f"辩论结论生成完成: {session_id}")
        
        # 6. 发送完成通知
        if debate.webhook_url:
            notify_debate_completion.delay(session_id, debate.webhook_url)
        
        return {"status": "completed", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"生成辩论结论失败: {str(e)}")
        debate_service.update_debate_status(session_id, DebateStatus.FAILED)
        return {"status": "failed", "reason": str(e)}
    finally:
        # 关闭数据库连接
        db.close()

@shared_task(name="debate.notify_debate_completion", bind=True)
def notify_debate_completion(self, session_id: str, webhook_url: str):
    """
    通知辩论完成
    
    Args:
        session_id: 辩论会话ID
        webhook_url: 回调URL
    """
    logger.info(f"发送辩论完成通知: {session_id} -> {webhook_url}")
    
    # 获取数据库会话
    db = next(get_db())
    debate_service = DebateService(db)
    
    try:
        # 获取辩论结果
        debate = debate_service.get_debate(session_id)
        debate_result = debate_service.get_debate_result(session_id)
        
        if not debate or not debate_result:
            logger.error(f"辩论或结果不存在: {session_id}")
            return {"status": "failed", "reason": "辩论或结果不存在"}
        
        # 构建通知数据
        notification_data = {
            "session_id": session_id,
            "topic": debate.topic,
            "status": debate.status,
            "completed_at": debate.updated_at.isoformat() if debate.updated_at else None,
            "final_conclusion": debate_result.final_conclusion,
            "confidence_score": debate_result.confidence_score,
            "summary_url": f"{settings.API_URL}/api/debate/{session_id}/result"
        }
        
        # 发送HTTP请求
        with httpx.Client(timeout=settings.WEBHOOK_TIMEOUT) as client:
            response = client.post(
                webhook_url,
                json=notification_data,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            logger.info(f"通知发送成功: {session_id}")
            return {"status": "success", "session_id": session_id}
            
    except Exception as e:
        logger.error(f"发送通知失败: {str(e)}")
        return {"status": "failed", "reason": str(e)}
    finally:
        # 关闭数据库连接
        db.close()

@shared_task(name="debate.cleanup_expired_debates", bind=True)
def cleanup_expired_debates(self):
    """
    清理过期的辩论会话
    可以配置为定期任务，清理长时间未完成的辩论
    """
    logger.info("开始清理过期辩论会话")
    
    # 获取数据库会话
    db = next(get_db())
    debate_service = DebateService(db)
    
    try:
        # 获取所有过期的辩论会话
        expired_debates = debate_service.get_expired_debates(settings.DEBATE_EXPIRY_DAYS)
        
        # 清理过期辩论
        for debate in expired_debates:
            logger.info(f"清理过期辩论: {debate.id}, 主题: {debate.topic}")
            
            # 更新状态为已过期
            debate_service.update_debate_status(debate.id, DebateStatus.EXPIRED)
        
        logger.info(f"清理完成，共清理 {len(expired_debates)} 个过期辩论会话")
        return {"status": "success", "cleaned_count": len(expired_debates)}
        
    except Exception as e:
        logger.error(f"清理过期辩论失败: {str(e)}")
        return {"status": "failed", "reason": str(e)}
    finally:
        # 关闭数据库连接
        db.close()