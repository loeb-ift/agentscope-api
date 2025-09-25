from sqlalchemy import Column, String, Text, JSON, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    name = Column(String(100), index=True, nullable=False)
    
    role = Column(String(50), index=True, nullable=False)
    
    system_prompt = Column(Text, nullable=False)
    
    model_config = Column(JSON, nullable=False)
    
    personality_traits = Column(JSON, nullable=False)
    
    expertise_areas = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    def to_dict(self):
        """将Agent对象转换为字典格式"""
        return {
            "id": str(self.id),
            "name": self.name,
            "role": self.role,
            "system_prompt": self.system_prompt,
            "model_config": self.model_config,
            "personality_traits": self.personality_traits,
            "expertise_areas": self.expertise_areas,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }