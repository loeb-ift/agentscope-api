from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator
import os

class Settings(BaseSettings):
    # 專案基本配置
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
    
    # 數據庫配置
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./agentscope.db")
    DATABASE_ECHO: bool = False
    
    # Redis配置
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    REDIS_DATA_DIR: str = os.environ.get("REDIS_DATA_DIR", "./redis")
    
    # Celery配置
    CELERY_BROKER_URL: str = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
    TIMEZONE: str = "Asia/Shanghai"  # 時區設置
    CELERY_RESULT_EXPIRES: int = 3600  # 結果過期時間(秒)
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300  # 任務軟時間限制(秒)
    CELERY_TASK_TIME_LIMIT: int = 600  # 任務硬時間限制(秒)
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 10  # 每個worker最多執行的任務數
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1  # 預取任務的數量
    
    # 默認辯論配置
    DEFAULT_DEBATE_ROUNDS: int = 3
    MAX_DEBATE_ROUNDS: int = 10
    MAX_AGENTS_PER_DEBATE: int = 8
    DEFAULT_MAX_DURATION_MINUTES: int = 30
    
    # Agent角色模板配置
    AGENT_ROLES: dict = {
        "advocate": "積極倡導者 - 支持提案並提出強力論證",
        "critic": "批判思考者 - 找出問題和潛在風險",
        "mediator": "調解者 - 平衡各方觀點，尋求共識",
        "analyst": "數據分析師 - 基於數據和事實進行分析",
        "innovator": "創新者 - 提出創新解決方案",
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