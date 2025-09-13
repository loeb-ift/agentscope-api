import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.core.config import settings
from app.api import router as api_router
from app.core.database import engine, Base

# 初始化数据库模型
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AgentScope Multi-Agent Debate API - 为n8n工作流提供多Agent辩论功能",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix=settings.API_PREFIX)

# 根路径端点
@app.get("/")
async def root():
    return {
        "message": "Welcome to AgentScope Multi-Agent Debate API",
        "version": settings.VERSION,
        "documentation": "/docs"
    }

# 应用启动代码
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS
    )