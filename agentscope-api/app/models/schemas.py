from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

class AgentConfig(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., min_length=2, max_length=50)
    system_prompt: str = Field(..., min_length=10)
    llm_config: Dict[str, str] = Field(..., min_items=1)  # 重命名model_config为llm_config避免冲突
    personality_traits: List[str] = Field(..., min_items=1)
    expertise_areas: List[str] = Field(..., min_items=1)

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
    llm_config: Optional[Dict[str, Any]] = None  # 更新为llm_config
    personality_traits: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    is_active: Optional[bool] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    system_prompt: str
    llm_config: Dict[str, Any]  # 更新为llm_config
    personality_traits: List[str]
    expertise_areas: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DebateStartRequest(BaseModel):
    topic: str = Field(..., min_length=5)
    agent_ids: List[str] = Field(..., min_length=2, max_length=8)
    rounds: Optional[int] = Field(3, ge=1, le=10)
    max_duration_minutes: Optional[int] = Field(30, ge=5, le=120)
    conclusion_requirements: Optional[Dict[str, Any]] = None
    
    @field_validator('agent_ids')
    def validate_agent_ids(cls, v):
        # 确保agent_ids不包含重复项
        if len(v) != len(set(v)):
            raise ValueError("Agent IDs must be unique")
        return v

class DebateStartResponse(BaseModel):
    session_id: str
    status: str = "pending"
    message: str = "辩论已启动，请稍后查询结果"
    created_at: datetime

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
    preliminary_insights: List[str]  # 中间洞察
    final_conclusion: Optional[str] = None
    key_arguments: Dict[str, List[str]]  # 按角色分类的关键论点
    consensus_points: List[str]  # 达成共识的要点
    divergent_views: List[str]  # 分歧观点
    confidence_score: float  # 结论可信度

class DebateMessageSchema(BaseModel):
    id: str
    debate_id: str
    agent_id: str
    agent_name: str
    agent_role: str
    round_number: int
    content: str
    timestamp: datetime

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

class AgentConfig(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., min_length=2, max_length=50)
    system_prompt: str = Field(..., min_length=10)
    llm_config: Dict[str, str] = Field(..., min_items=1)  # 重命名model_config為llm_config避免衝突
    personality_traits: List[str] = Field(..., min_items=1)
    expertise_areas: List[str] = Field(..., min_items=1)

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
    agent_ids: List[str] = Field(..., min_length=2, max_length=8)
    rounds: Optional[int] = Field(3, ge=1, le=10)
    max_duration_minutes: Optional[int] = Field(30, ge=5, le=120)
    conclusion_requirements: Optional[Dict[str, Any]] = None
    
    @field_validator('agent_ids')
    def validate_agent_ids(cls, v):
        # 確保agent_ids不包含重複項
        if len(v) != len(set(v)):
            raise ValueError("Agent IDs must be unique")
        return v

class DebateStartResponse(BaseModel):
    session_id: str
    status: str = "pending"
    message: str = "辯論已啟動，請稍後查詢結果"
    created_at: datetime

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

class AgentConfigureResponse(BaseModel):
    agent_id: str
    status: str = "configured"
    message: str = "Agent已配置完成"
    updated_at: datetime

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentConfigureForDebateRequest(BaseModel):
    debate_topic: str = Field(..., min_length=5)
    additional_instructions: Optional[str] = None

class AgentConfigureResponse(BaseModel):
    agent_id: str
    status: str = "configured"
    message: str = "Agent已配置完成"
    updated_at: datetime

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)