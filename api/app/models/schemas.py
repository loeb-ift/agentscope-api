from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

class AgentConfig(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., min_length=2, max_length=50)
    system_prompt: str = Field(..., min_length=10)
    llm_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    personality_traits: Optional[List[str]] = Field(default_factory=list)
    expertise_areas: Optional[List[str]] = Field(default_factory=list)

class AgentCreateRequest(AgentConfig):
    pass

class AgentCreateResponse(BaseModel):
    agent_id: str
    name: str
    role: str
    created_at: datetime
    status: str = "created"

class AgentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[str] = Field(None, min_length=2, max_length=50)
    system_prompt: Optional[str] = Field(None, min_length=10)
    llm_config: Optional[Dict[str, Any]] = None  # 更新為llm_config
    personality_traits: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    is_active: Optional[bool] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    system_prompt: str
    llm_config: Dict[str, Any]  # 更新為llm_config
    personality_traits: List[str]
    expertise_areas: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DebateStartRequest(BaseModel):
    topic: str = Field(..., min_length=5)
    agent_ids: List[str] = Field(..., min_length=2, max_length=8, description="參與辯論的Agent ID列表，至少需要2位")
    moderator_id: str = Field(..., description="擔任主持人的Agent ID")
    rounds: Optional[int] = Field(3, ge=1, le=10)
    max_duration_minutes: Optional[int] = Field(30, ge=5, le=120)
    conclusion_requirements: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    moderator_prompt: Optional[str] = None

    @field_validator('agent_ids')
    def validate_agent_ids(cls, v):
        # 確保agent_ids不包含重複項
        if len(v) != len(set(v)):
            raise ValueError("辯論員的ID不可重複 (Agent IDs must be unique)")
        return v

    @field_validator('moderator_id')
    def moderator_is_not_a_debater(cls, v, values):
        if 'agent_ids' in values.data and v in values.data['agent_ids']:
            raise ValueError("主持人不能同時是辯論員 (Moderator cannot be a debater)")
        return v

class DebateStartResponse(BaseModel):
    session_id: str
    status: str = "pending"
    message: str = "辯論已啟動，請稍後查詢結果"
    created_at: datetime
class DebateFromTemplateRequest(BaseModel):
    template_name: str = Field(..., description="The name of the debate template to use.")


class DebateStatusResponse(BaseModel):
    session_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0.0 - 1.0
    current_round: Optional[int] = None
    total_rounds: int
    started_at: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None

class N8NOptimizedResponse(BaseModel):
    session_id: str
    status: str  # "running", "completed", "failed"
    progress: float  # 0.0 - 1.0
    preliminary_insights: List[str]  # 中間洞察
    final_conclusion: Optional[str] = None
    key_arguments: Dict[str, List[str]]  # 按角色分類的關鍵論點
    consensus_points: List[str]  # 達成共識的要點
    divergent_views: List[str]  # 分歧觀點
    confidence_score: float  # 結論可信度

class DebateMessageSchema(BaseModel):
    id: str
    debate_id: str
    agent_id: str
    agent_name: str
    agent_role: str
    round_number: int
    content: str
    timestamp: datetime

class DebateResultResponse(N8NOptimizedResponse):
    created_at: datetime
    updated_at: datetime
    conversation_history: Optional[List[DebateMessageSchema]] = None

class AgentConfigureForDebateRequest(BaseModel):
    debate_topic: str = Field(..., min_length=5)
    additional_instructions: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None

class AgentConfigureResponse(BaseModel):
    agent_id: str
    status: str = "configured"
    message: str = "Agent已配置完成"
    updated_at: datetime

class DataSourceCredentials(BaseModel):
    db_type: str = Field(..., description="数据库类型", examples=["postgresql", "mysql", "sqlite"])
    db_host: str = Field(..., description="数据库主机地址")
    db_port: int = Field(..., description="数据库端口")
    db_user: str = Field(..., description="数据库用户名")
    db_password: str = Field(..., description="数据库密码")
    db_name: str = Field(..., description="数据库名称")

class DebateFromDataSourceRequest(BaseModel):
    topic: str = Field(..., description="辩论主题")
    sql_query: str = Field(..., description="用于提取数据的 SQL 查询")
    data_source: DataSourceCredentials = Field(..., description="数据库连接凭证")
    agent_ids: List[str] = Field(..., description="参与辩论的 Agent ID 列表 (不包括主持人)")
    moderator_id: str = Field(..., description="主持人 Agent ID")
    rounds: int = Field(3, description="辩论轮数")
    max_duration_minutes: int = Field(30, description="最大持续时间（分钟）")
    conclusion_requirements: Optional[str] = Field(None, description="结论生成要求")
    moderator_prompt: Optional[str] = Field(None, description="给主持人的特定提示词")
    data_analyst_prompt_override: Optional[str] = Field(None, description="覆盖默认数据分析师提示词的可选字段")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM 配置")


class DebateFromDatasetRequest(BaseModel):
    topic: str = Field(..., description="辩论主题")
    dataset_name: str = Field(..., description="要使用的数据集名称 (例如: 表名)")
    data_source: DataSourceCredentials = Field(..., description="数据库连接凭证")
    agent_ids: List[str] = Field(..., description="参与辩论的 Agent ID 列表 (不包括主持人)")
    moderator_id: str = Field(..., description="主持人 Agent ID")
    rounds: int = Field(3, description="辩论轮数")
    max_duration_minutes: int = Field(30, description="最大持续时间（分钟）")
    conclusion_requirements: Optional[str] = Field(None, description="结论生成要求")
    moderator_prompt: Optional[str] = Field(None, description="给主持人的特定提示词")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM 配置")


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)