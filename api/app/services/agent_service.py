from sqlalchemy.orm import Session
from fastapi import HTTPException
import agentscope
import uuid
from agentscope.agent import AgentBase
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.agent import Agent
from app.models.schemas import AgentConfig, AgentCreateRequest, AgentUpdateRequest, AgentResponse
from app.core.config import settings

class AgentService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_agent(self, config: AgentCreateRequest) -> Agent:
        """創建新的Agent實例"""
        if config.role not in settings.AGENT_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的角色類型。支持的角色：{', '.join(settings.AGENT_ROLES.keys())}"
            )
        
        db_agent = Agent(
            name=config.name,
            role=config.role,
            system_prompt=config.system_prompt,
            model_config=config.llm_config,
            personality_traits=config.personality_traits,
            expertise_areas=config.expertise_areas,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_agent)
        self.db.commit()
        self.db.refresh(db_agent)
        
        return db_agent
    
    def get_agent(self, agent_id: str) -> Agent:
        """根據ID獲取Agent"""
        try:
            agent_uuid = uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的Agent ID格式: {agent_id}"
            )
            
        db_agent = self.db.query(Agent).filter(
            Agent.id == agent_uuid, Agent.is_active == True
        ).first()
        
        if not db_agent:
            raise HTTPException(
                status_code=404,
                detail=f"未找到ID为{agent_id}的Agent"
            )
        
        return db_agent
    
    def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """获取活跃的Agent列表"""
        return self.db.query(Agent).filter(
            Agent.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_agents_count(self) -> int:
        """獲取活躍 Agent 的總數"""
        return self.db.query(Agent).filter(Agent.is_active == True).count()

    def create_agent_from_dict(self, agent_data: Dict[str, Any]) -> Agent:
        """從字典建立新的 Agent 實例"""
        create_request = AgentCreateRequest(**agent_data)
        return self.create_agent(create_request)

    def update_agent(self, agent_id: str, update_data: AgentUpdateRequest) -> Agent:
        """更新Agent信息"""
        db_agent = self.get_agent(agent_id)
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if 'role' in update_dict and update_dict['role'] not in settings.AGENT_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的角色类型。支持的角色：{', '.join(settings.AGENT_ROLES.keys())}"
            )
        
        for key, value in update_dict.items():
            setattr(db_agent, key, value)
        
        db_agent.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_agent)
        
        return db_agent
    
    def deactivate_agent(self, agent_id: str) -> Agent:
        """停用Agent"""
        db_agent = self.get_agent(agent_id)
        db_agent.is_active = False
        db_agent.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_agent)
        return db_agent
    
    def configure_agent_for_debate(self, agent_id: str, topic: str, additional_instructions: Optional[str] = None, llm_config: Optional[Dict[str, Any]] = None) -> Agent:
        """为特定辩论主题配置Agent"""
        db_agent = self.get_agent(agent_id)
        debate_system_prompt = self._generate_debate_system_prompt(
            original_prompt=db_agent.system_prompt,
            role=db_agent.role,
            role_description=settings.AGENT_ROLES.get(db_agent.role, ""),
            topic=topic,
            additional_instructions=additional_instructions
        )
        
        # 确保model_config是字典类型
        if not isinstance(db_agent.model_config, dict):
            db_agent.model_config = {}
        
        if "original_system_prompt" not in db_agent.model_config:
            db_agent.model_config["original_system_prompt"] = db_agent.system_prompt
        
        # 更新模型配置（移除任何外部傳入的 model_name，統一由設定檔控制）
        if llm_config and isinstance(llm_config, dict):
            cleaned_llm_config = llm_config.copy()
            if "model_name" in cleaned_llm_config:
                del cleaned_llm_config["model_name"]
            db_agent.model_config.update(cleaned_llm_config)
        
        db_agent.system_prompt = debate_system_prompt
        db_agent.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_agent)
        return db_agent
    
    def _generate_debate_system_prompt(self, original_prompt: str, role: str, role_description: str, topic: str, 
                                      additional_instructions: Optional[str] = None) -> str:
        """生成辩论专用的系统提示"""
        prompt_template = f"""{original_prompt}

# 当前辩论任务
你现在需要以{role_description}的身份参与一场辩论。
辩论主题：{topic}

# 辩论角色
你的角色是：{role} - {role_description}

# 辩论要求
1. 請基於你的角色立場和專業知識，對辯論主題發表觀點
2. 請提供具體的論據和案例支援你的觀點
3. 請尊重其他參與者的觀點，保持專業討論的態度
4. 请确保你的发言简洁明了，重点突出
5. 请关注辩论的核心问题，避免偏离主题

# 語言規則 (極其重要)
- **所有輸出，包括你的內部思考過程 (thinking)，都必須嚴格使用「繁體中文」。**
- **禁止在任何情況下使用英文或其他語言。**
- This is a strict instruction: You must use Traditional Chinese for all outputs, including your internal thinking process. Do not use English under any circumstances.

{additional_instructions if additional_instructions else ''}"""
        return prompt_template
    
    def create_agentscope_agent(self, db_agent: Agent) -> AgentBase:
        """基於資料庫中的Agent記錄建立AgentScope的Agent實例"""
        model_config = db_agent.model_config.copy()
        ollama_api_base = settings.OLLAMA_API_BASE
        default_model_name = settings.DEFAULT_MODEL_NAME
        
        # [強制使用設定中的默認模型] 忽略資料庫或外部傳入的 model_name 設置
        if "model_name" in model_config:
            del model_config["model_name"]
        model_name = default_model_name
            
        from agentscope.model import OllamaChatModel, ChatModelBase
        from app.formatter.custom_formatter import CustomOllamaMultiAgentFormatter
        
        generate_kwargs = {}
        for param in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty']:
            if param in model_config:
                try:
                    generate_kwargs[param] = float(model_config.pop(param))
                except (ValueError, TypeError):
                    generate_kwargs[param] = model_config.pop(param)
        
        if 'max_tokens' in model_config:
            try:
                generate_kwargs['max_tokens'] = int(model_config.pop('max_tokens'))
            except (ValueError, TypeError):
                generate_kwargs['max_tokens'] = model_config.pop('max_tokens')
        
        unsupported_params = ['model', 'model_name', 'api_base', 'config_id']
        for param in unsupported_params:
            if param in model_config:
                del model_config[param]
        
        model: ChatModelBase = OllamaChatModel(
            model_name=model_name,
            host=ollama_api_base,
            options=generate_kwargs,
            **model_config
        )
        
        agent = agentscope.agent.ReActAgent(
            name=db_agent.name,
            sys_prompt=db_agent.system_prompt,
            model=model,
            formatter=CustomOllamaMultiAgentFormatter()
        )
        
        agent.role = db_agent.role
        agent.id = str(db_agent.id)
        
        return agent
    
    def get_agent_by_ids(self, agent_ids: List[str]) -> List[Agent]:
        """根据ID列表获取多个Agent"""
        agent_uuids = []
        invalid_ids = []
        
        for agent_id in agent_ids:
            try:
                agent_uuids.append(uuid.UUID(agent_id))
            except ValueError:
                invalid_ids.append(agent_id)
        
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"无效的Agent ID格式: {', '.join(invalid_ids)}"
            )
            
        agents = self.db.query(Agent).filter(
            Agent.id.in_(agent_uuids),
            Agent.is_active == True
        ).all()
        
        found_ids = {str(agent.id) for agent in agents}
        missing_ids = [id for id in agent_ids if id not in found_ids]
        
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"未找到以下ID的Agent: {', '.join(missing_ids)}"
            )
        
        return agents