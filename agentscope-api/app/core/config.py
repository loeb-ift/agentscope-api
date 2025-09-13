from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator
import os

class Settings(BaseSettings):
    # 项目基本配置
    PROJECT_NAME: str = "AgentScope Multi-Agent Debate API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # API配置
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = ["*"]
    BACKEND_CORS_ORIGINS: List[str] = []
    
    # 数据库配置
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./agentscope.db")
    DATABASE_ECHO: bool = False
    
    # Redis配置
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    REDIS_DATA_DIR: str = os.environ.get("REDIS_DATA_DIR", "./redis")
    
    # Celery配置
    CELERY_BROKER_URL: str = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
    TIMEZONE: str = "Asia/Shanghai"  # 时区设置
    CELERY_RESULT_EXPIRES: int = 3600  # 结果过期时间(秒)
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300  # 任务软时间限制(秒)
    CELERY_TASK_TIME_LIMIT: int = 600  # 任务硬时间限制(秒)
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 10  # 每个worker最多执行的任务数
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1  # 预取任务的数量
    
    # 默认辩论配置
    DEFAULT_DEBATE_ROUNDS: int = 3
    MAX_DEBATE_ROUNDS: int = 10
    MAX_AGENTS_PER_DEBATE: int = 8
    DEFAULT_MAX_DURATION_MINUTES: int = 30
    
    # Agent角色模板配置
    AGENT_ROLES: dict = {
        "advocate": "积极倡导者 - 支持提案并提出强力论证",
        "critic": "批判思考者 - 找出问题和潜在风险",
        "mediator": "调解者 - 平衡各方观点，寻求共识",
        "analyst": "数据分析师 - 基于数据和事实进行分析",
        "innovator": "创新者 - 提出创新解决方案",
        "pragmatist": "实务主义者 - 关注实际执行可行性"
    }
    
    # LLM配置
    # Ollama配置
    OLLAMA_API_BASE: str = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
    DEFAULT_MODEL_NAME: str = os.environ.get("DEFAULT_MODEL_NAME", "gpt-oss:20b")
    
    # 其他LLM配置（当前未使用，已注释）
    # OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")
    # ANTHROPIC_API_KEY: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")
    # DASHSCOPE_API_KEY: Optional[str] = os.environ.get("DASHSCOPE_API_KEY")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

# 创建配置实例
settings = Settings()