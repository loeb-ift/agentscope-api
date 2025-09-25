from fastapi import APIRouter
from app.api.agents import router as agents_router
from app.api.debate import router as debate_router
from app.api.health import router as health_router
from fastapi import APIRouter

# 创建主路由器
router = APIRouter()

# 注册子路由器
router.include_router(agents_router, prefix="/agents", tags=["Agents"])
router.include_router(debate_router, prefix="/debate", tags=["Debate"])
router.include_router(health_router, tags=["Health"])