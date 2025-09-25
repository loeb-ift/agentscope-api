from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
import redis
from typing import Dict, Any

router = APIRouter()

from app.services.agent_service import AgentService

@router.get("/health", summary="檢查服務健康狀態")
def health_check(db: Session = Depends(get_db)):
    """
    檢查API服務的健康狀態，包括數據庫連接、Redis、LLM服務以及資料庫初始化狀態
    """
    db_status = "unhealthy"
    redis_status = "unhealthy"
    seeding_status = "pending"
    overall_status = "unhealthy"

    try:
        # 1. 檢查數據庫連接
        db.execute(text("SELECT 1"))
        db_status = "healthy"

        # 2. 檢查資料庫初始化（Seeding）狀態
        agent_service = AgentService(db)
        if agent_service.get_agents_count() > 0:
            seeding_status = "completed"
        else:
            # 如果 Agent 數量為 0，服務尚未完全就緒
            seeding_status = "in_progress"
            raise HTTPException(status_code=503, detail="Service Unavailable: Database seeding is in progress.")

        # 3. 检查Redis连接
        try:
            r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
            r.ping()
            redis_status = "healthy"
        except Exception:
            # Redis 不是核心依賴，不影響整體健康狀態
            redis_status = "degraded"

        # 如果所有核心檢查都通過
        if db_status == "healthy" and seeding_status == "completed":
            overall_status = "healthy"

    except Exception as e:
        # 如果任何核心檢查失敗，則服務不健康
        # 確保在 docker healthcheck 失敗時返回 503
        if isinstance(e, HTTPException) and e.status_code == 503:
            raise e
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

    # 解析数据库类型
    db_type = "unknown"
    if settings.DATABASE_URL.startswith("sqlite"):
        db_type = "SQLite"
    elif settings.DATABASE_URL.startswith("postgresql"):
        db_type = "PostgreSQL"
    elif settings.DATABASE_URL.startswith("mysql"):
        db_type = "MySQL"
    
    # 确定运行环境
    environment = "production" if not settings.DEBUG else "development"
    
    return {
        "status": overall_status,
        "version": settings.VERSION,
        "environment": environment,
        "components": {
            "database": db_status,
            "redis": redis_status,
            "database_seeding": seeding_status
        },
        "dependencies": {
            "llm_host": settings.OLLAMA_API_BASE,
            "database_type": db_type,
            "redis_url": settings.REDIS_URL.split('?')[0]
        },
        "message": "AgentScope API status"
    }

@router.get("/version", summary="獲取API版本資訊")
def get_version():
    """
    獲取API的版本資訊
    """
    return {
        "version": settings.VERSION,
        "project_name": settings.PROJECT_NAME
    }

@router.get("/metrics", summary="獲取API效能指標")
def get_metrics():
    """
    獲取API的基本效能指標
    注意：實際應用中可能需要整合Prometheus等監控工具
    """
    # 这里提供一个简单的实现
    # 在实际生产环境中，应该使用专业的监控工具
    return {
        "active_debates": 0,  # 示例值
        "total_agents": 0,    # 示例值
        "total_debates": 0,   # 示例值
        "avg_debate_duration": 0,  # 示例值
        "api_latency": {
            "p50": 0.0,  # 示例值
            "p90": 0.0,  # 示例值
            "p99": 0.0   # 示例值
        }
    }

@router.get("/config", summary="獲取API配置資訊")
def get_config():
    """
    獲取API的基本配置資訊（不包含敏感資訊）
    """
    return {
        "project_name": settings.PROJECT_NAME,
        "api_prefix": settings.API_PREFIX,
        "allowed_origins": settings.BACKEND_CORS_ORIGINS,
        "debug_mode": settings.DEBUG,
        "agent_roles": settings.AGENT_ROLES,
        "default_debate_rounds": settings.DEFAULT_DEBATE_ROUNDS,
        "max_debate_rounds": settings.MAX_DEBATE_ROUNDS
    }