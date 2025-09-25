from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Float, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base
from enum import Enum

class DebateStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    AWAITING_CONCLUSION = "awaiting_conclusion"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class Debate(Base):
    __tablename__ = "debates"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    topic = Column(Text, nullable=False)
    
    status = Column(
        String(20), 
        default=DebateStatus.CREATED.value, 
        index=True, 
        nullable=False
    )
    
    rounds = Column(Integer, default=3)
    
    max_duration_minutes = Column(Integer, default=30)
    
    progress = Column(Float, default=0.0)
    
    final_conclusion = Column(Text, nullable=True)
    
    confidence_score = Column(Float, nullable=True)
    
    consensus_points = Column(JSON, nullable=True)
    
    divergent_views = Column(JSON, nullable=True)
    
    key_arguments = Column(JSON, nullable=True)
    
    preliminary_insights = Column(JSON, nullable=True)
    
    conclusion_requirements = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # 关系
    messages = relationship(
        "DebateMessage",
        back_populates="debate",
        cascade="all, delete-orphan"
    )
    
    # 参与辩论的Agent IDs
    agent_ids = Column(JSON, nullable=False)
    
    # Moderator fields
    moderator_id = Column(UUID(as_uuid=True), nullable=True)
    moderator_prompt = Column(Text, nullable=True)
    
    def to_dict(self):
        """将Debate对象转换为字典格式"""
        return {
            "session_id": str(self.id),
            "topic": self.topic,
            "status": self.status,
            "rounds": self.rounds,
            "max_duration_minutes": self.max_duration_minutes,
            "progress": self.progress,
            "final_conclusion": self.final_conclusion,
            "confidence_score": self.confidence_score,
            "consensus_points": self.consensus_points,
            "divergent_views": self.divergent_views,
            "key_arguments": self.key_arguments,
            "preliminary_insights": self.preliminary_insights,
            "conclusion_requirements": self.conclusion_requirements,
            "agent_ids": self.agent_ids,
            "moderator_id": str(self.moderator_id) if self.moderator_id else None,
            "moderator_prompt": self.moderator_prompt,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class DebateMessage(Base):
    __tablename__ = "debate_messages"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    debate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("debates.id"),
        nullable=False
    )
    
    agent_id = Column(
        UUID(as_uuid=True),
        nullable=False
    )
    
    agent_name = Column(String(100), nullable=False)
    
    agent_role = Column(String(50), nullable=False)
    
    round_number = Column(Integer, nullable=False)
    
    content = Column(Text, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    debate = relationship("Debate", back_populates="messages")
    
    def to_dict(self):
        """将DebateMessage对象转换为字典格式"""
        return {
            "id": str(self.id),
            "debate_id": str(self.debate_id),
            "agent_id": str(self.agent_id),
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "round_number": self.round_number,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }