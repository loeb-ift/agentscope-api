import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.core.config import settings
from app.api import router as api_router
from app.core.database import engine, Base, SessionLocal
from app.services.agent_service import AgentService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 初始化數據庫模型
Base.metadata.create_all(bind=engine)

def seed_default_agents():
    """在資料庫中植入預設的 Agent"""
    db = SessionLocal()
    try:
        agent_service = AgentService(db)
        if agent_service.get_agents_count() == 0:
            logger.info("資料庫為空，正在植入預設的分析師 Agents...")
            for agent_config in settings.DEFAULT_AGENTS:
                agent_service.create_agent_from_dict(agent_config)
            logger.info("預設分析師 Agents 植入完成。")
        else:
            logger.info("資料庫中已存在 Agents，跳過植入程序。")
    finally:
        db.close()

# 創建FastAPI應用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AgentScope Multi-Agent Debate API - 為n8n工作流提供多Agent辯論功能",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.on_event("startup")
async def startup_event():
    """應用程式啟動時執行的事件"""
    logger.info("應用程式啟動...")
    seed_default_agents()

# 根路径端点
@app.get("/")
async def root():
    return {
        "message": "Welcome to AgentScope Multi-Agent Debate API",
        "version": settings.VERSION,
        "documentation": "/docs"
    }

# 應用啟動程式碼
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS
    )