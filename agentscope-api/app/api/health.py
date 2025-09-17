from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
import redis
from typing import Dict, Any

router = APIRouter()

@router.get("/health", summary="檢查服務健康狀態")
def health_check(db: Session = Depends(get_db)):
    """
    檢查API服務的健康狀態，包括數據庫連接、Redis和LLM服務
    """
    try:
        # 檢查數據庫連接
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
        raise HTTPException(status_code=503, detail=f"Database connection error: {str(e)}")
    
    try:
        # 检查Redis连接
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = "unhealthy"
        # 不抛出异常，因为Redis可能不是所有功能的必需组件
    
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
        "status": "healthy",
        "version": settings.VERSION,
        "environment": environment,
        "components": {
            "database": db_status,
            "redis": redis_status
        },
        "dependencies": {
            "llm_host": settings.OLLAMA_API_BASE,
            "database_type": db_type,
            "redis_url": settings.REDIS_URL.split('?')[0]  # 确保不包含问号及其后面的内容
        },
        "message": "AgentScope API is running"
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

@router.get("/metrics", summary="获取API性能指标")
def get_metrics():
    """
    获取API的基本性能指标
    注意：实际应用中可能需要集成Prometheus等监控工具
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

@router.get("/config", summary="获取API配置信息")
def get_config():
    """
    获取API的基本配置信息（不包含敏感信息）
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