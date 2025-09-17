#!/usr/bin/env python3
"""
AgentScope 金融分析师辩论系统 - Gradio Web界面
基于 financial_debate_api.sh 的Web实现
"""

import gradio as gr
import requests
import json
import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 请求配置常量
DEFAULT_TIMEOUT = 10  # 默认超时时间10秒

def make_api_request(method: str, url: str, **kwargs) -> requests.Response:
    """
    统一的API请求函数，包含超时设置和错误处理

    Args:
        method: HTTP方法 ('GET', 'POST', 'PUT', 'DELETE')
        url: 请求URL
        **kwargs: 其他传递给requests的参数

    Returns:
        requests.Response: 响应对象

    Raises:
        requests.RequestException: 请求异常
        ValueError: 无效的HTTP方法
    """
    # 确保设置了超时时间
    if 'timeout' not in kwargs:
        kwargs['timeout'] = DEFAULT_TIMEOUT

    method = method.upper()
    if method not in ['GET', 'POST', 'PUT', 'DELETE']:
        raise ValueError(f"不支持的HTTP方法: {method}")

    try:
        if method == 'GET':
            response = requests.get(url, **kwargs)
        elif method == 'POST':
            response = requests.post(url, **kwargs)
        elif method == 'PUT':
            response = requests.put(url, **kwargs)
        elif method == 'DELETE':
            response = requests.delete(url, **kwargs)

        # 如果请求失败，记录更多信息
        if not response.ok:
            payload = kwargs.get('json')
            log_message = f"API请求失败: {method} {url}, 状态码: {response.status_code}"
            if payload:
                try:
                    # 尝试格式化JSON payload
                    payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
                    log_message += f"\n--- 请求 Payload ---\n{payload_str}\n--------------------"
                except TypeError:
                    # 如果无法序列化，直接转为字符串
                    log_message += f"\n--- 请求 Payload (非序列化) ---\n{payload}\n--------------------"
            logger.error(log_message)
            
        return response
    except requests.RequestException as e:
        payload = kwargs.get('json')
        log_message = f"API请求异常: {method} {url}, 错误: {e}"
        if payload:
            try:
                payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
                log_message += f"\n--- 请求 Payload ---\n{payload_str}\n--------------------"
            except TypeError:
                log_message += f"\n--- 请求 Payload (非序列化) ---\n{payload}\n--------------------"
        logger.error(log_message)
        raise

def safe_json_parse(response: requests.Response) -> dict:
    """
    安全的JSON解析函数，包含错误处理

    Args:
        response: requests响应对象

    Returns:
        dict: 解析后的JSON数据

    Raises:
        json.JSONDecodeError: JSON解析错误
        Exception: 其他解析错误
    """
    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.error(f"响应内容: {response.text[:500]}")
        raise
    except Exception as e:
        logger.error(f"解析响应时出错: {e}")
        raise

def handle_api_error(response: requests.Response, operation: str) -> str:
    """
    统一的API错误处理函数

    Args:
        response: requests响应对象
        operation: 操作描述

    Returns:
        str: 格式化的错误消息
    """
    error_msg = f"HTTP {response.status_code}"
    try:
        error_data = safe_json_parse(response)
        if isinstance(error_data, dict):
            if 'detail' in error_data:
                error_msg += f": {error_data['detail']}"
            elif 'message' in error_data:
                error_msg += f": {error_data['message']}"
            elif 'error' in error_data:
                error_msg += f": {error_data['error']}"
            else:
                error_msg += f": {str(error_data)}"
        else:
            error_msg += f": {str(error_data)}"
    except:
        error_msg += f": {response.text[:200]}"

    return f"❌ {operation}失败: {error_msg}"

# 配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://10.227.135.97:8000")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.227.135.98:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
base_url = f"{API_BASE_URL}/api"

# 默认智能体配置
DEFAULT_AGENTS = [
    {
        "name": "宏观经济分析师",
        "role": "analyst",
        "system_prompt": "你是一位资深的宏观经济分析师，拥有15年的全球经济研究经验。你擅长分析全球经济趋势、货币政策、财政政策以及地缘政治事件对经济的影响。请全程使用繁体中文进行对话和分析。",
        "personality_traits": ["专业", "客观", "深入"],
        "expertise_areas": ["宏观经济", "货币政策", "财政政策", "地缘政治"]
    },
    {
        "name": "股票策略分析师",
        "role": "pragmatist", 
        "system_prompt": "你是一位资深的股票策略分析师，拥有12年的股票市场研究经验。你擅长分析不同行业的发展趋势、评估企业基本面，并提供股票投资组合配置建议。请全程使用繁体中文进行对话和分析。",
        "personality_traits": ["战略", "细致", "前瞻性"],
        "expertise_areas": ["股票市场", "行业分析", "企业基本面", "投资组合配置"]
    },
    {
        "name": "固定收益分析师",
        "role": "critic",
        "system_prompt": "你是一位资深的固定收益分析师，拥有10年的债券市场研究经验。你擅长分析利率走势、信用风险评估以及各类固定收益产品的投资价值。请全程使用繁体中文进行对话和分析。",
        "personality_traits": ["谨慎", "精确", "风险意识强"],
        "expertise_areas": ["债券市场", "利率分析", "信用风险", "固定收益产品"]
    },
    {
        "name": "另类投资分析师",
        "role": "innovator",
        "system_prompt": "你是一位资深的另类投资分析师，拥有8年的另类投资研究经验。你擅长分析房地产、私募股权、对冲基金、大宗商品等非传统投资产品的风险收益特征。请全程使用繁体中文进行对话和分析。",
        "personality_traits": ["创新", "灵活", "多元思维"],
        "expertise_areas": ["房地产", "私募股权", "对冲基金", "大宗商品"]
    }
]

class DebateManager:
    def __init__(self):
        self.agents = []
        self.session_id = None
        self.debate_history = []
        
    def check_health(self) -> bool:
        """检查API服务健康状态"""
        try:
            response = make_api_request('GET', f"{base_url}/health")
            if response.status_code == 200:
                data = safe_json_parse(response)
                return data.get("status") == "healthy"
            return False
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    def create_agent(self, name: str, role: str, system_prompt: str,
                    personality_traits: List[str], expertise_areas: List[str]) -> tuple:
        """创建智能体，返回 (agent_id, error_message)"""
        try:
            payload = {
                "name": name,
                "role": role,
                "system_prompt": system_prompt,
                "llm_config": {
                    "model_name": OLLAMA_MODEL,
                    "temperature": "0.7",
                    "max_tokens": "1024"
                },
                "personality_traits": personality_traits,
                "expertise_areas": expertise_areas
            }

            response = make_api_request(
                'POST',
                f"{base_url}/agents/create",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = safe_json_parse(response)
                agent_id = data.get("agent_id")
                if agent_id and agent_id != "null":
                    return agent_id, None
                else:
                    return None, "API响应中缺少agent_id"
            else:
                error_msg = handle_api_error(response, "创建智能体")
                return None, error_msg

        except Exception as e:
            logger.error(f"创建智能体失败: {e}")
            logger.error(f"发送的请求体: {payload}")
            return None, f"网络错误: {str(e)}"
    
    def configure_agent(self, agent_id: str, topic: str) -> bool:
        """配置智能体用于辩论"""
        try:
            payload = {
                "debate_topic": topic,
                "additional_instructions": "请基于你的专业领域和知识，对辩论主题发表专业观点，提供具体的数据、案例和分析支持你的观点。"
            }

            response = make_api_request(
                'POST',
                f"{base_url}/agents/{agent_id}/configure",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"配置智能体失败: {e}")
            return False
    
    def start_debate(self, topic: str, agent_ids: List[str], rounds: int) -> Optional[str]:
        """启动辩论"""
        try:
            payload = {
                "topic": topic,
                "agent_ids": agent_ids,
                "rounds": rounds,
                "max_duration_minutes": 30
            }

            response = make_api_request(
                'POST',
                f"{base_url}/debate/start",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = safe_json_parse(response)
                session_id = data.get("session_id")
                if session_id and session_id != "null":
                    self.session_id = session_id
                    return session_id
            return None
        except Exception as e:
            logger.error(f"启动辩论失败: {e}")
            return None
    
    def get_debate_status(self) -> Dict[str, Any]:
        """获取辩论状态"""
        if not self.session_id:
            return {}

        try:
            response = make_api_request('GET', f"{base_url}/debate/{self.session_id}/status")
            if response.status_code == 200:
                return safe_json_parse(response)
            return {}
        except Exception as e:
            logger.error(f"获取辩论状态失败: {e}")
            return {}
    
    def get_debate_history(self) -> List[Dict[str, Any]]:
        """获取辩论历史"""
        if not self.session_id:
            return []

        try:
            response = make_api_request('GET', f"{base_url}/debate/{self.session_id}/history")
            if response.status_code == 200:
                data = safe_json_parse(response)
                # API可能返回列表或包含history键的字典
                if isinstance(data, list):
                    self.debate_history = data
                    return data
                elif isinstance(data, dict):
                    history = data.get("history", [])
                    if isinstance(history, list):
                        self.debate_history = history
                        return history
                    else:
                        return []
                else:
                    return []
            return []
        except Exception as e:
            logger.error(f"获取辩论历史失败: {e}")
            return []

    def get_supported_roles(self) -> List[str]:
        """获取支持的Agent角色列表"""
        try:
            response = make_api_request('GET', f"{base_url}/agents/roles")
            if response.status_code == 200:
                data = safe_json_parse(response)
                # API可能返回列表或包含roles键的字典
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    roles = data.get("roles", [])
                    return roles if isinstance(roles, list) else []
                else:
                    return []
            return []
        except Exception as e:
            logger.error(f"获取支持角色失败: {e}")
            return []

    def get_agents_list(self) -> List[Dict[str, Any]]:
        """获取所有Agent列表"""
        try:
            logger.info(f"正在获取Agent列表: {base_url}/agents/")
            response = make_api_request('GET', f"{base_url}/agents/")
            logger.info(f"API响应状态码: {response.status_code}")

            if response.status_code == 200:
                # 确保响应文本不为空
                if not response.text or response.text.strip() == "":
                    logger.warning("API响应为空")
                    return []
                
                try:
                    data = safe_json_parse(response)
                    logger.info(f"API响应数据类型: {type(data)}")
                    logger.info(f"API响应数据长度: {len(data) if hasattr(data, '__len__') else 'N/A'}")

                    # 确保返回的是列表格式
                    if isinstance(data, list):
                        # 验证列表中的每个元素都是字典格式
                        validated_agents = []
                        for agent in data:
                            if isinstance(agent, dict) and "id" in agent and "name" in agent:
                                validated_agents.append(agent)
                        logger.info(f"返回列表格式，包含 {len(validated_agents)} 个有效Agent")
                        return validated_agents
                    elif isinstance(data, dict):
                        agents = data.get("agents", [])
                        if isinstance(agents, list):
                            # 验证列表中的每个元素都是字典格式
                            validated_agents = []
                            for agent in agents:
                                if isinstance(agent, dict) and "id" in agent and "name" in agent:
                                    validated_agents.append(agent)
                            logger.info(f"返回字典格式，agents字段包含 {len(validated_agents)} 个有效Agent")
                            return validated_agents
                        else:
                            logger.warning(f"agents字段不是列表格式: {type(agents)}")
                            return []
                    else:
                        logger.warning(f"意外的数据格式: {type(data)}")
                        return []
                except Exception as json_error:
                    logger.error(f"解析JSON响应失败: {json_error}")
                    logger.error(f"原始响应文本: {response.text}")
                    return []
            else:
                logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"获取Agent列表失败: {e}")
            return []

    def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取Agent详细"""
        try:
            response = make_api_request('GET', f"{base_url}/agents/{agent_id}")
            if response.status_code == 200:
                data = safe_json_parse(response)
                return data
            return None
        except Exception as e:
            logger.error(f"获取Agent详情失败: {e}")
            return None

    def cancel_debate(self, session_id: str) -> bool:
        """取消辩论"""
        try:
            response = make_api_request('POST', f"{base_url}/debate/{session_id}/cancel")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"取消辩论失败: {e}")
            return False

    def get_debate_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取辩论结果"""
        try:
            response = make_api_request('GET', f"{base_url}/debate/{session_id}/result")
            if response.status_code == 200:
                data = safe_json_parse(response)
                # 如果返回的是字典格式，直接返回
                if isinstance(data, dict):
                    return data
                # 如果返回的是其他格式，尝试包装成字典
                return {"result": data}
            return None
        except Exception as e:
            logger.error(f"获取辩论结果失败: {e}")
            return None

# API配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://10.227.135.97:8000")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.227.135.98:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
base_url = f"{API_BASE_URL}/api"

# 全局变量跟踪当前辩论会话
current_session_id = None

# 全局变量跟踪选定的辩论Agent
selected_debate_agents = []

# 全局辩论管理器实例
debate_manager = DebateManager()

def get_debate_agents_for_selection():    
    """获取可用于辩论的Agent列表"""
    try:
        logger.info("=== 开始获取辩论Agent列表 ===")
        
        # 直接从debate_manager获取Agent列表
        agents = debate_manager.get_agents_list()
        logger.info(f"从debate_manager获取到的原始Agent数据: {agents}")
        
        # 转换为Gradio CheckboxGroup所需的格式
        agent_options = []
        if not agents:
            logger.warning("未获取到任何Agent")
            return ["⚠️ 当前没有可用的Agent，请先创建Agent"]
        
        for agent in agents:
            agent_id = agent.get("id", "")
            agent_name = agent.get("name", "未知")
            agent_role = agent.get("role", "未知")
            if agent_id:
                option = f"{agent_name} ({agent_role}) - ID: {agent_id}"
                agent_options.append(option)
                logger.info(f"添加Agent选项: {option}")
        
        logger.info(f"总共获取到 {len(agent_options)} 个Agent选项")
        logger.info(f"最终返回的Agent选项列表: {agent_options}")
        
        if not agent_options:
            logger.warning("虽然获取到Agent数据，但未能生成有效的选项")
            return ["⚠️ 当前没有可用的Agent，请先创建Agent"]
        
        return agent_options
    except Exception as e:
        logger.error(f"获取辩论Agent列表失败: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [f"❌ 获取Agent列表时出错: {str(e)}"]

def refresh_debate_agents(current_value=None):
    """刷新辩论Agent列表，并同步已选项"""
    try:
        logger.info("=== 执行刷新辩论Agent列表操作 ===")
        agent_options = get_debate_agents_for_selection()
        # 安全地处理当前值，确保在设置值之前choices列表已经正确加载
        # 当choices列表为空时，不尝试设置任何值
        if not agent_options:
            count = 0
            status_msg = "⚠️ 当前没有可用的Agent"
            filtered_value = []
        else:
            # 同步当前已选项，仅保留仍在choices中的
            filtered_value = [v for v in (current_value or []) if v in agent_options]
            count = len([opt for opt in agent_options if not opt.startswith(('⚠️', '❌'))])
            status_msg = f"✅ Agent列表已刷新，共 {count} 个可用Agent"
        
        logger.info(f"[SYNC] 刷新后choices: {agent_options}, filtered_value: {filtered_value}")
        return gr.update(choices=agent_options, value=filtered_value), status_msg, count
    except Exception as e:
        logger.error(f"刷新辩论Agent列表失败: {str(e)}")
        return gr.update(choices=[], value=[]), f"❌ 刷新失败: {str(e)}", 0

def confirm_selected_agents(selected_agents):
    """确认选择的辩论Agent"""
    global selected_debate_agents
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[DEBUG] confirm_selected_agents: 输入selected_agents={selected_agents}, 全局selected_debate_agents-旧值={selected_debate_agents}")
    selected_debate_agents = selected_agents
    logger.info(f"[DEBUG] confirm_selected_agents: 全局selected_debate_agents-新值={selected_debate_agents}")
    if not selected_agents:
        return "❌ 请至少选择一个Agent参与辩论"
    return f"✅ 已选择 {len(selected_agents)} 个Agent参与辩论"
def check_service():
    """检查服务状态 - 全面系统诊断"""
    try:
        response = make_api_request('GET', f"{base_url}/health")
        if response.status_code == 200:
            data = safe_json_parse(response)
            overall_status = data.get("status", "unknown")
            api_version = data.get("version", "未知")
            environment = data.get("environment", "未知")
            dependencies = data.get("dependencies", {})

            # 构建状态报告
            status_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌", "unknown": "❓"}.get(overall_status, "❓")
            report_lines = [
                f"{status_emoji} 总计状态: {overall_status}",
                f"📦 API版本: {api_version}",
                f"🌍 运行环境: {environment}",
                "",
                "🔗 依赖项状态:"
            ]

            # 处理依赖项状态
            dep_emojis = {"operational": "✅", "degraded": "⚠️", "outage": "❌"}
            if dependencies:
                for dep_name, dep_status in dependencies.items():
                    emoji = dep_emojis.get(dep_status, "❓")
                    # 将蛇形命名转换为标题格式
                    display_name = dep_name.replace('_', ' ').title()
                    report_lines.append(f"  {emoji} {display_name}: {dep_status}")
            else:
                report_lines.append("  ❓ 无依赖项信息")

            return "\n".join(report_lines)
        else:
            return f"❌ API服务不可用 (HTTP {response.status_code})"
    except Exception as e:
        return f"❌ 检查服务时出错: {str(e)}"

def create_debate_agents(topic: str, custom_agents: str = None) -> str:
    """创建辩论智能体"""
    try:
        # 清除之前的agents
        debate_manager.agents.clear()
        
        # 使用默认智能体配置
        agents_config = DEFAULT_AGENTS
        
        # 如果有自定义配置，解析JSON
        if custom_agents and custom_agents.strip():
            try:
                agents_config = json.loads(custom_agents)
                if not isinstance(agents_config, list):
                    return "❌ 自定义配置格式错误，应该是列表格式"
            except json.JSONDecodeError:
                return "❌ 自定义配置JSON格式错误"
        
        # 创建智能体
        created_agents = []
        for agent_config in agents_config:
            agent_id, error_msg = debate_manager.create_agent(
                name=agent_config["name"],
                role=agent_config["role"],
                system_prompt=agent_config["system_prompt"],
                personality_traits=agent_config["personality_traits"],
                expertise_areas=agent_config["expertise_areas"]
            )

            if agent_id:
                # 配置智能体
                if debate_manager.configure_agent(agent_id, topic):
                    debate_manager.agents.append({
                        "id": agent_id,
                        "name": agent_config["name"],
                        "role": agent_config["role"]
                    })
                    created_agents.append(agent_config["name"])
                else:
                    return f"❌ 配置智能体 {agent_config['name']} 失败"
            else:
                return f"❌ 创建智能体 {agent_config['name']} 失败: {error_msg}"
        
        return f"✅ 成功创建 {len(created_agents)} 个智能体: {', '.join(created_agents)}"
        
    except Exception as e:
        return f"❌ 创建智能体时出错: {str(e)}"

def start_debate_session(topic: str, rounds: int, progress=gr.Progress()) -> str:
    """启动辩论会话"""
    try:
        if not debate_manager.agents:
            return "❌ 请先创建智能体"

        if not topic.strip():
            return "❌ 请输入辩论主题"

        agent_ids = [agent["id"] for agent in debate_manager.agents]

        progress(0, desc="启动辩论...")
        session_id = debate_manager.start_debate(topic, agent_ids, rounds)

        if session_id:
            progress(0.1, desc="等待辩论开始...")

            # 等待辩论完成
            max_wait = 300  # 5分钟
            wait_interval = 5
            elapsed = 0

            while elapsed < max_wait:
                status = debate_manager.get_debate_status()
                current_status = status.get("status", "unknown")
                current_round = status.get("current_round", 0)
                total_rounds = status.get("total_rounds", rounds)

                if current_status == "completed":
                    progress(1.0, desc="辩论完成")
                    return f"✅ 辩论完成！会话ID: {session_id}"
                elif current_status == "running":
                    progress_value = min(0.1 + (current_round / total_rounds) * 0.8, 0.9)
                    progress(progress_value, desc=f"第 {current_round}/{total_rounds} 轮进行中...")
                elif current_status == "failed":
                    progress(1.0, desc="辩论失败")
                    return "❌ 辩论执行失败"

                time.sleep(wait_interval)
                elapsed += wait_interval

            return "⚠️ 等待超时，请稍后手动查看结果"
        else:
            return "❌ 启动辩论失败"

    except Exception as e:
        return f"❌ 启动辩论时出错: {str(e)}"

def start_debate_async(topic: str, rounds: int, selected_agents: List[str]) -> str:
    """异步启动辩论"""
    try:
        if not selected_agents:
            return "❌ 请先选择参与辩论的Agent"

        # 解析选择的Agent ID
        agent_ids = []
        for agent_str in selected_agents:
            # 从格式 "名称 (角色) - ID: xxx" 中提取ID
            if " - ID: " in agent_str:
                agent_id = agent_str.split(" - ID: ")[-1]
                agent_ids.append(agent_id)

        if not agent_ids:
            return "❌ 无法解析选择的Agent ID"

        # 配置Agent用于辩论 - 直接API调用
        for agent_id in agent_ids:
            logger.info(f"--- 开始操作：为辩论配置Agent ---")
            url = f"{base_url}/agents/{agent_id}/configure"
            logger.info(f"即將調用 POST: {url}")
            config_payload = {
                "debate_topic": topic,
                "additional_instructions": "请基于你的专业领域和知识，对辩论主题发表专业观点，提供具体的数据、案例和分析支持你的观点。",
                "llm_config": {
                    "model_name": OLLAMA_MODEL,
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            }
            config_response = make_api_request(
                'POST',
                url,
                json=config_payload,
                headers={"Content-Type": "application/json"}
            )
            if config_response.status_code != 200:
                return f"❌ 配置Agent {agent_id} 失败: HTTP {config_response.status_code}"

        # 启动辩论 - 直接API调用
        logger.info(f"--- 开始操作：启动辩论 ---")
        url = f"{base_url}/debate/start"
        logger.info(f"即將調用 POST: {url}")
        debate_payload = {
            "topic": topic,
            "agent_ids": agent_ids,
            "rounds": rounds,
            "max_duration_minutes": 30,
            "llm_config": {
                "model_name": OLLAMA_MODEL,
                "temperature": 0.7,
                "max_tokens": 1024
            }
        }
        debate_response = make_api_request(
            'POST',
            url,
            json=debate_payload,
            headers={"Content-Type": "application/json"}
        )

        if debate_response.status_code == 200:
            debate_data = safe_json_parse(debate_response)
            session_id = debate_data.get("session_id")
            if session_id and session_id != "null":
                # 更新全局session_id用于后续操作
                global current_session_id
                current_session_id = session_id
                return f"✅ 辩论启动成功！会话ID: {session_id}"
            else:
                return "❌ 辩论启动失败: API未返回session_id"
        else:
            error_msg = handle_api_error(debate_response, "辩论启动")
            return f"❌ 辩论启动失败: {error_msg}"
    except Exception as e:
        return f"❌ 启动辩论时出错: {str(e)}"

def get_debate_progress() -> str:
    """获取辩论进度 - 直接API调用"""
    global current_session_id
    global selected_debate_agents

    if not current_session_id:
        return "暂无进行中的辩论"

    try:
        # 直接API调用获取辩论状态
        status_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/status")
        if status_response.status_code != 200:
            return f"❌ 无法获取辩论状态: HTTP {status_response.status_code}"

        status = safe_json_parse(status_response)
        current_status = status.get("status", "unknown")
        current_round = status.get("current_round", 0)
        total_rounds = status.get("total_rounds", 0)
        progress_value = status.get("progress", 0)

        progress_info = []
        progress_info.append("🔄 辩论进度实时监控")
        progress_info.append("-" * 40)
        progress_info.append(f"📊 状态: {current_status}")
        progress_info.append(f"🎯 轮次: {current_round}/{total_rounds}")
        progress_info.append(f"📈 进度: {progress_value}%")

        # 显示参与辩论的Agent信息
        if selected_debate_agents:
            progress_info.append("👥 参与辩论的Agent:")
            for agent in selected_debate_agents:
                # 提取Agent名称和角色信息
                if " (" in agent and ") " in agent:
                    agent_name_role = agent.split(" - ID:")[0]
                    progress_info.append(f"  {agent_name_role}")

        if current_status == "running":
            progress_info.append("\n⏳ 辩论进行中...")
            # 获取最新发言 - 直接API调用
            history_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/history")
            if history_response.status_code == 200:
                history_data = safe_json_parse(history_response)
                # API可能返回列表或包含history键的字典
                if isinstance(history_data, list):
                    history = history_data
                elif isinstance(history_data, dict):
                    history = history_data.get("history", [])
                else:
                    history = []

                if history:
                    # 显示最近的发言
                    recent_messages = history[-3:]  # 获取最后3条消息
                    progress_info.append("\n💬 最新发言:")
                    for msg in recent_messages:
                        agent_name = msg.get("agent_name", "未知")
                        content = msg.get("content", "")[:100]
                        round_num = msg.get("round", 1)
                        progress_info.append(f"第{round_num}轮 - {agent_name}: {content}...")

        elif current_status == "completed":
            progress_info.append("\n✅ 辩论已完成")
            # 显示最终结果摘要 - 直接API调用
            result_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/result")
            if result_response.status_code == 200:
                result_data = safe_json_parse(result_response)
                # 如果返回的是字典格式，直接返回
                if isinstance(result_data, dict):
                    result = result_data
                else:
                    result = {"result": result_data}

                final_conclusion = result.get("final_conclusion", "")
                if final_conclusion:
                    progress_info.append(f"🏆 最终结论: {final_conclusion[:200]}...")

        elif current_status == "failed":
            progress_info.append("\n❌ 辩论失败")
        else:
            progress_info.append("\n⏸️ 辩论未开始或已暂停")

        progress_info.append(f"\n🕒 更新时间: {datetime.now().strftime('%H:%M:%S')}")

        return "\n".join(progress_info)

    except Exception as e:
        return f"❌ 获取进度时出错: {str(e)}"

def get_debate_results() -> str:
    """获取辩论结果 - 直接API调用"""
    global current_session_id

    try:
        # 首先尝试获取完整结果 - 直接API调用
        if current_session_id:
            result_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/result")
            if result_response.status_code == 200:
                result_data = safe_json_parse(result_response)
                # 如果返回的是字典格式，直接返回
                if isinstance(result_data, dict):
                    return format_debate_result(result_data)
                else:
                    # 尝试包装成字典格式
                    wrapped_result = {"result": result_data}
                    return format_debate_result(wrapped_result)

        # 如果没有完整结果，获取历史记录 - 直接API调用
        if current_session_id:
            history_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/history")
            if history_response.status_code == 200:
                history_data = safe_json_parse(history_response)
                # API可能返回列表或包含history键的字典
                if isinstance(history_data, list):
                    history = history_data
                elif isinstance(history_data, dict):
                    history = history_data.get("history", [])
                else:
                    history = []

                if history:
                    return format_debate_history(history)

        return "❌ 暂无辩论结果"

    except Exception as e:
        return f"❌ 获取结果时出错: {str(e)}"

def format_debate_result(result_data: Dict[str, Any]) -> str:
    """格式化辩论结果"""
    results = []
    results.append("📊 辩论结果汇总")
    results.append("=" * 50)

    # 最终结论
    final_conclusion = result_data.get("final_conclusion", "")
    if final_conclusion:
        results.append(f"\n🏆 最终结论:")
        results.append(final_conclusion)

    # 可信度分数
    confidence_score = result_data.get("confidence_score", "")
    if confidence_score:
        results.append(f"\n📈 可信度分数: {confidence_score}")

    # 共识要点
    consensus_points = result_data.get("consensus_points", [])
    if consensus_points:
        results.append("\n🙌 共识要点:")
        for i, point in enumerate(consensus_points, 1):
            if point:
                results.append(f"{i}. {point}")

    # 分歧观点
    divergent_views = result_data.get("divergent_views", [])
    if divergent_views:
        results.append("\n⚖️ 分歧观点:")
        for i, view in enumerate(divergent_views, 1):
            if view:
                results.append(f"{i}. {view}")

    return "\n".join(results)

def format_debate_history(history: List[Dict[str, Any]]) -> str:
    """格式化辩论历史记录"""
    if not history:
        return "暂无历史记录"

    results = []
    results.append("📝 辩论历史记录")
    results.append("=" * 50)

    # 按轮次分组
    rounds = {}
    for entry in history:
        round_num = entry.get("round", 1)
        if round_num not in rounds:
            rounds[round_num] = []
        rounds[round_num].append(entry)

    # 输出每轮内容
    for round_num in sorted(rounds.keys()):
        results.append(f"\n🔄 第 {round_num} 轮")
        results.append("-" * 30)

        for entry in rounds[round_num]:
            agent_name = entry.get("agent_name", "未知")
            role = entry.get("agent_role", "未知")
            content = entry.get("content", "").strip()

            if content:  # 只显示有内容的条目
                results.append(f"👤 {agent_name} ({role}):")
                results.append(f"{content}")
                results.append("")

    return "\n".join(results)

def monitor_debate_status() -> str:
    """监控辩论状态 - 直接API调用"""
    global current_session_id

    if not current_session_id:
        return "暂无进行中的辩论"

    try:
        # 直接API调用获取辩论状态
        status_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/status")
        if status_response.status_code != 200:
            return f"❌ 无法获取辩论状态: HTTP {status_response.status_code}"

        status = safe_json_parse(status_response)
        current_status = status.get("status", "unknown")
        current_round = status.get("current_round", 0)
        total_rounds = status.get("total_rounds", 0)
        progress = status.get("progress", 0)

        status_info = []
        status_info.append("🔍 辩论状态监控")
        status_info.append("-" * 30)
        status_info.append(f"状态: {current_status}")
        status_info.append(f"轮次: {current_round}/{total_rounds}")
        status_info.append(f"进度: {progress}%")

        if current_status == "running":
            status_info.append("\n⏳ 辩论进行中...")
            # 获取最新发言 - 直接API调用
            history_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/history")
            if history_response.status_code == 200:
                history_data = safe_json_parse(history_response)
                # API可能返回列表或包含history键的字典
                if isinstance(history_data, list):
                    history = history_data
                elif isinstance(history_data, dict):
                    history = history_data.get("history", [])
                else:
                    history = []

                if history:
                    # 获取最新发言
                    try:
                        latest_entry = max(history, key=lambda x: x.get("timestamp", ""))
                        agent_name = latest_entry.get("agent_name", "未知")
                        content_preview = latest_entry.get("content", "")[:100]
                        status_info.append(f"最新发言: {agent_name} - {content_preview}...")
                    except (ValueError, TypeError):
                        # 如果没有timestamp字段或其他错误，使用最后一个条目
                        if history:
                            latest_entry = history[-1]
                            agent_name = latest_entry.get("agent_name", "未知")
                            content_preview = latest_entry.get("content", "")[:100]
                            status_info.append(f"最新发言: {agent_name} - {content_preview}...")

        elif current_status == "completed":
            status_info.append("\n✅ 辩论已完成")
        elif current_status == "failed":
            status_info.append("\n❌ 辩论失败")

        return "\n".join(status_info)

    except Exception as e:
        return f"❌ 监控状态时出错: {str(e)}"

def get_agent_templates() -> str:
    """获取智能体模板JSON"""
    return json.dumps(DEFAULT_AGENTS, ensure_ascii=False, indent=2)

def validate_agent_input(name: str, role: str, system_prompt: str, personality_traits: str, expertise_areas: str) -> str:
    """驗證Agent輸入數據，返回錯誤信息或空字符串"""
    if not name.strip():
        return "❌ Agent名稱不能為空"
    if not role.strip():
        return "❌ 請選擇Agent角色"
    if not system_prompt.strip():
        return "❌ 系統提示詞不能為空"
    if len(system_prompt.strip()) < 10:
        return f"❌ 系統提示詞至少需要10個字符（當前{len(system_prompt.strip())}個字符）\n請提供更詳細的角色描述。"

    # 轉換字符串為列表
    personality_list = [trait.strip() for trait in personality_traits.split(',') if trait.strip()]
    expertise_list = [area.strip() for area in expertise_areas.split(',') if area.strip()]

    if not personality_list:
        return "❌ 請至少填寫一個個性特徵"
    if not expertise_list:
        return "❌ 請至少填寫一個專業領域"

    return ""  # 驗證通過

def prepare_agent_payload(name: str, role: str, system_prompt: str, personality_traits: str, expertise_areas: str) -> dict:
    """準備Agent API請求數據"""
    personality_list = [trait.strip() for trait in personality_traits.split(',') if trait.strip()]
    expertise_list = [area.strip() for area in expertise_areas.split(',') if area.strip()]

    return {
        "name": name.strip(),
        "role": role.strip(),
        "system_prompt": system_prompt.strip(),
        "llm_config": {
            "model_name": OLLAMA_MODEL,
            "temperature": 0.7,
            "max_tokens": 1024
        },
        "personality_traits": personality_list,
        "expertise_areas": expertise_list
    }

def save_agent(agent_id: str, name: str, role: str, system_prompt: str,
                personality_traits: str, expertise_areas: str) -> tuple:
    """保存Agent（創建或更新）"""
    try:
        # 驗證輸入
        validation_error = validate_agent_input(name, role, system_prompt, personality_traits, expertise_areas)
        if validation_error:
            return validation_error, gr.update(), gr.update(interactive=True), gr.update()

        # 準備API請求數據
        payload = prepare_agent_payload(name, role, system_prompt, personality_traits, expertise_areas)

        # API請求數據已經在 prepare_agent_payload 中準備好

        # 根據agent_id決定是創建還是更新
        if agent_id and agent_id.strip():
            # 更新現有Agent
            logger.info(f"--- 开始操作：更新 Agent ---")
            url = f"{base_url}/agents/{agent_id}"
            logger.info(f"即將調用 PUT: {url}")
            response = make_api_request(
                'PUT',
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            operation = "更新"
            success_verb = "更新"
        else:
            # 創建新Agent
            logger.info(f"--- 开始操作：创建新 Agent ---")
            url = f"{base_url}/agents/create"
            logger.info(f"即將調用 POST: {url}")
            response = make_api_request(
                'POST',
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            operation = "創建"
            success_verb = "創建"

        if response.status_code == 200:
            data = safe_json_parse(response)

            if operation == "創建":
                agent_id_result = data.get("agent_id")
                if agent_id_result and agent_id_result != "null":
                    # 成功創建，使用帶重試機制的刷新來獲取最新的Agent列表
                    updated_agents, count_text = refresh_agent_list_with_retry()
                    success_msg = f"""✅ Agent{success_verb}成功！
📋 詳細資訊：
• ID: {agent_id_result}
• 名稱: {name.strip()}
• 角色: {role.strip()}

🎉 新{success_verb}的Agent已自動添加到列表中！
✨ 表單已清空，您可以繼續創建新的Agent
"""
                    # 清空表单并返回结果
                    return success_msg, gr.update(choices=updated_agents, value=[]), gr.update(interactive=True), gr.update(value=count_text)
                else:
                    return "❌ API響應中缺少agent_id", gr.update(), gr.update(interactive=True), gr.update()
            else:
                # 成功更新，使用帶重試機制的刷新來獲取最新的Agent列表
                updated_agents, count_text = refresh_agent_list_with_retry()
                success_msg = f"""✅ Agent{success_verb}成功！
📋 更新資訊：
• ID: {agent_id}
• 名稱: {name.strip()}
• 角色: {role.strip()}

Agent列表已自動刷新。
✨ 表單已清空，您可以繼續創建新的Agent或編輯其他Agent
"""
                # 清空表单并返回结果
                return success_msg, gr.update(choices=updated_agents, value=[]), gr.update(interactive=True), gr.update(value=count_text)
        else:
            error_msg = handle_api_error(response, f"{operation}Agent")
            return error_msg, gr.update(), gr.update(interactive=True), gr.update()

    except Exception as e:
        return f"❌ 保存Agent時出錯: {str(e)}", gr.update(), gr.update(interactive=True), gr.update()

def refresh_agent_list_with_retry() -> tuple:
    """
    带重试机制的Agent列表刷新函数

    Returns:
        tuple: (agent_options, count_text) - Agent列表选项和计数器文本
    """
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        logger.info(f"=== Agent列表刷新尝试 {attempt + 1}/{max_retries} ===")

        agents = get_agents_for_selection()
        
        # 日志记录获取到的Agent列表和长度
        logger.info(f"获取到的Agent列表: {agents}")
        logger.info(f"获取到的Agent数量: {len(agents)}")

        # 无论列表是否为空，都计算总数并返回
        agent_count = len(agents)
        count_text = f"當前 Agent 總數：{agent_count}"
        logger.info(f"✅ 第 {attempt + 1} 次尝试获取到 {agent_count} 个Agent")
        return agents, count_text

    # 所有重试都失败（理论上不会到达这里，因为上面的循环总是返回）
    logger.error("❌ 重试后仍未获取到Agent数据，返回空列表")
    return [], "當前 Agent 總數：0"

def get_agents_for_selection() -> List[str]:
    """获取所有Agent用于选择 - 直接API调用"""
    try:
        logger.info("=== 开始获取Agent列表用于选择 ===")
        logger.info(f"目标API URL: {base_url}/agents/")

        # 直接API调用获取Agent列表
        response = make_api_request('GET', f"{base_url}/agents/")
        agent_options = []

        if response.status_code == 200:
            data = safe_json_parse(response)
            logger.info(f"API响应状态码: {response.status_code}")
            logger.info(f"API响应数据类型: {type(data)}")

            # 详细记录API返回的原始数据
            if isinstance(data, list):
                logger.info(f"API返回原始数据（列表格式）: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                agents_list = data
                logger.info(f"返回列表格式，包含 {len(agents_list)} 个Agent")
            elif isinstance(data, dict):
                # 特别处理：优先检查是否有 'items' 字段（这是常见的分页API响应格式）
                if 'items' in data:
                    agents_list = data.get('items', [])
                    logger.info(f"返回分页格式，items字段包含 {len(agents_list) if isinstance(agents_list, list) else 0} 个Agent")
                else:
                    agents_list = data.get("agents", [])
                    logger.info(f"返回字典格式，agents字段包含 {len(agents_list) if isinstance(agents_list, list) else 0} 个Agent")
            else:
                logger.warning(f"意外的数据格式: {type(data)}")
                logger.warning(f"原始数据内容: {str(data)[:200]}...")
                agents_list = []

            for agent in agents_list:
                agent_name = agent.get('name', '未知')
                agent_role = agent.get('role', '未知')
                agent_id = agent.get('id', '未知')
                agent_created_at = agent.get('created_at', '未知')
                agent_status = agent.get('status', '未知')

                option = f"{agent_name} ({agent_role}) - ID: {agent_id}"
                agent_options.append(option)

                # 详细记录每个Agent的信息
                logger.info(f"Agent详情 - 名称: {agent_name}, 角色: {agent_role}, ID: {agent_id}, 创建时间: {agent_created_at}, 状态: {agent_status}")
                logger.info(f"添加Agent选项: {option}")

            logger.info(f"总共获取到 {len(agent_options)} 个Agent选项")
            logger.info("=== Agent列表获取完成 ===")
            return agent_options
        else:
            logger.error(f"=== API请求失败 ===")
            logger.error(f"HTTP状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            logger.error(f"响应头: {dict(response.headers)}")
            logger.error("=== Agent列表获取失败 ===")
            return []
    except Exception as e:
        logger.error(f"=== 获取Agent选择列表异常 ===")
        logger.error(f"异常信息: {e}")
        logger.error(f"异常详情", exc_info=True)
        logger.error("=== Agent列表获取异常结束 ===")
        return []

def load_agent_to_form(agent_id: str) -> tuple:
    """載入 Agent 到表單進行編輯"""
    try:
        # 調用API獲取Agent詳細資訊
        logger.info(f"--- 开始操作：载入 Agent 进行编辑 ---")
        url = f"{base_url}/agents/{agent_id}"
        logger.info(f"即將調用 GET: {url}")
        response = make_api_request('GET', url)
        if response.status_code == 200:
            agent_data = safe_json_parse(response)

            # 提取Agent信息
            name = agent_data.get("name", "")
            role = agent_data.get("role", "")
            system_prompt = agent_data.get("system_prompt", "")
            personality_traits = agent_data.get("personality_traits", [])
            expertise_areas = agent_data.get("expertise_areas", [])

            # 轉換為字符串格式
            traits_str = ", ".join(personality_traits) if isinstance(personality_traits, list) else str(personality_traits)
            expertise_str = ", ".join(expertise_areas) if isinstance(expertise_areas, list) else str(expertise_areas)

            success_msg = f"""✅ 成功載入Agent進行編輯
📋 詳細資訊：
• ID: {agent_id}
• 名稱: {name}
• 角色: {role}

請修改表單中的值，然後點擊"保存 Agent"。"""

            # 返回更新後的表單值和禁用刪除按鈕
            return (agent_id, name, role, system_prompt, traits_str, expertise_str, success_msg, gr.update(interactive=False))
        else:
            error_msg = f"❌ 獲取Agent詳細資訊失敗: {handle_api_error(response, '獲取Agent詳細資訊')}"
            return ("", "", "", "", "", "", error_msg, gr.update(interactive=True))

    except Exception as e:
        return ("", "", "", "", "", "", f"❌ 載入Agent詳細資訊時出錯: {str(e)}", gr.update(interactive=True))

def clear_agent_form():
    """清空Agent表單，返回到創建模式"""
    return (
        "",  # agent_id_hidden
        "",  # agent_name_input
        "analyst",  # agent_role_dropdown (默認值)
        "",  # agent_prompt_input
        "專業,客觀,深入",  # agent_traits_input (默認值)
        "宏观经济,货币政策,财政政策",  # agent_expertise_input (默認值)
        "✨ 表單已清空，進入新建模式",  # create_agent_result
        gr.update(interactive=True)  # 重新啟用刪除按鈕
    )

def get_supported_roles_list() -> List[str]:
    """获取支持的角色列表 - 直接API调用"""
    try:
        response = make_api_request('GET', f"{base_url}/agents/roles")
        if response.status_code == 200:
            data = safe_json_parse(response)
            # API可能返回列表或包含roles键的字典
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                roles = data.get("roles", [])
                return roles if isinstance(roles, list) else []
            else:
                return []
        else:
            logger.warning(f"获取角色列表失败: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"获取支持角色失败: {e}")
        return ["analyst", "pragmatist", "critic", "innovator"]  # 默认值

def load_initial_data():
    """加载初始数据，用于应用启动时填充Agent列表"""
    agents, count_text = refresh_agent_list_with_retry()
    return gr.update(choices=agents), gr.update(value=count_text)

def delete_selected_agents(selected_agents: List[str]) -> tuple:
    """删除选定的Agent"""
    if not selected_agents:
        return "❌ 请先选择要删除的Agent", gr.update(), gr.update(interactive=True), gr.update()

    deleted_count = 0
    failed_deletions = []

    for agent_str in selected_agents:
        # 从格式 "名称 (角色) - ID: xxx" 中提取ID
        if " - ID: " in agent_str:
            agent_id = agent_str.split(" - ID: ")[-1]
            try:
                logger.info(f"--- 开始操作：删除 Agent ---")
                url = f"{base_url}/agents/{agent_id}"
                logger.info(f"即將調用 DELETE: {url}")
                response = make_api_request('DELETE', url)
                if response.status_code == 200:
                    deleted_count += 1
                    logger.info(f"成功删除Agent: {agent_id}")
                else:
                    failed_deletions.append(f"{agent_str} (HTTP {response.status_code})")
                    logger.error(f"删除Agent失败: {agent_id}, HTTP {response.status_code}")
            except Exception as e:
                failed_deletions.append(f"{agent_str} (错误: {str(e)})")
                logger.error(f"删除Agent时出错: {agent_id}, 错误: {e}")
        else:
            failed_deletions.append(f"{agent_str} (无法解析ID)")
            logger.error(f"无法解析Agent ID: {agent_str}")

    # 使用带重试机制的刷新获取更新后的Agent列表
    updated_agents, count_text = refresh_agent_list_with_retry()

    # 构建汇总消息
    summary_parts = []
    if deleted_count > 0:
        summary_parts.append(f"✅ 成功删除 {deleted_count} 个Agent")
    if failed_deletions:
        summary_parts.append(f"❌ 删除失败 {len(failed_deletions)} 个:")
        for failure in failed_deletions:
            summary_parts.append(f"  • {failure}")

    return "\n".join(summary_parts), gr.update(choices=updated_agents, value=[]), gr.update(interactive=True), gr.update(value=count_text)


# 创建独立的UI函数
def create_agent_list_ui():
    """创建Agent列表UI组件，返回需要外部引用的组件句柄"""
    with gr.Group() as agent_list_box:
        gr.Markdown("### 📋 Agent 列表")
        agent_count_display = gr.Markdown("當前 Agent 總數：0")
        with gr.Row():
            refresh_agents_btn = gr.Button("🔄 刷新列表")
        agents_checkbox = gr.CheckboxGroup(
            label="选择参与辩论的Agent",
            choices=[],
            value=[],
            interactive=True
        )
        selected_agents_display = gr.Textbox(
            label="已选择的Agent",
            interactive=False,
            lines=3,
            value="未选择Agent"
        )
        with gr.Row():
            edit_agent_btn = gr.Button("✏️ 编辑选中Agent", variant="secondary")
            delete_agents_btn = gr.Button("🗑️ 删除选定Agent", variant="destructive")

    # 内部事件绑定
    def update_selected_agents_display(selected_agents):
        if selected_agents:
            return f"已选择 {len(selected_agents)} 个Agent:\n" + "\n".join(selected_agents)
        return "未选择Agent"

    agents_checkbox.change(
        fn=update_selected_agents_display,
        inputs=agents_checkbox,
        outputs=selected_agents_display
    )

    def refresh_agents_list_action():
        logger.info("=== 用户触发Agent列表刷新 ===")
        new_choices, count_text = refresh_agent_list_with_retry()
        logger.info(f"刷新完成，获取到 {len(new_choices)} 个Agent选项")
        return gr.update(choices=new_choices, value=[]), gr.update(value=count_text)

    refresh_agents_btn.click(
        fn=refresh_agents_list_action,
        outputs=[agents_checkbox, agent_count_display]
    )

    return agent_list_box, agents_checkbox, delete_agents_btn, edit_agent_btn, selected_agents_display, agent_count_display

# 创建一个全局函数来获取和显示辩论历史
def get_history_display() -> str:
    """获取辩论历史并格式化显示"""
    global current_session_id
    global debate_manager
    
    if not current_session_id or not debate_manager:
        return "暂无辩论历史记录"
    
    try:
        # 调用API获取历史记录
        response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/history")
        if response.status_code == 200:
            data = safe_json_parse(response)
            
            # API可能返回列表或包含history键的字典
            if isinstance(data, dict):
                history = data.get("history", [])
            elif isinstance(data, list):
                history = data
            else:
                history = []
            
            # 使用已有的format_debate_history函数格式化显示
            return format_debate_history(history)
        return "❌ 无法获取辩论历史"
    except Exception as e:
        return f"❌ 获取历史时出错: {str(e)}"

# 创建Gradio界面
with gr.Blocks(title="AgentScope 金融分析师辩论系统") as demo:
    gr.Markdown("""
    # 🤖 AgentScope 金融分析师辩论系统

    基于AI智能体的多轮辩论系统，支持动态创建和管理Agent。

    ## 使用步骤：
    1. 检查服务状态
    2. 创建智能体或选择现有智能体
    3. 配置辩论主题和轮次
    4. 启动辩论并实时查看进度
    5. 查看辩论结果和历史记录
    """)

    # 服务状态检查
    with gr.Row():
        service_status_btn = gr.Button("🔍 检查服务状态", variant="secondary")
        service_status_text = gr.Textbox(label="服务状态", interactive=False, lines=6, scale=4)

    # 主标签页
    with gr.Tabs():
        # Agent管理标签页
        with gr.TabItem("🤖 Agent管理"):
            with gr.Row():
                # 左侧：Agent配置
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 Agent 配置")
                    gr.Markdown("""
                    ### 分析师功能说明
                    
                    **新增分析师**：直接在表单中填写所有必填信息（名称、角色、提示词等），然后点击"保存 Agent"按钮。
                    
                    **编辑现有分析师**：在右侧Agent列表中选择一个分析师，点击"编辑选中Agent"按钮，修改表单中的信息后点击"保存 Agent"按钮。
                    """)

                    # 隐藏的agent_id字段，用于区分创建和编辑模式
                    agent_id_hidden = gr.Textbox(
                        visible=False,
                        label="Agent ID"
                    )

                    agent_name_input = gr.Textbox(
                        label="Agent名称",
                        placeholder="例如：宏观经济分析师"
                    )
                    agent_role_dropdown = gr.Dropdown(
                        label="Agent角色",
                        choices=["analyst", "pragmatist", "critic", "innovator"],
                        value="analyst",
                        interactive=True
                    )
                    agent_prompt_input = gr.Textbox(
                        label="系统提示词",
                        placeholder="输入Agent的角色描述和行为指导...",
                        lines=3
                    )
                    agent_traits_input = gr.Textbox(
                        label="个性特征 (用逗号分隔)",
                        placeholder="例如：专业,客观,深入",
                        value="专业,客观,深入"
                    )
                    agent_expertise_input = gr.Textbox(
                        label="专业领域 (用逗号分隔)",
                        placeholder="例如：宏观经济,货币政策,财政政策",
                        value="宏观经济,货币政策,财政政策"
                    )

                    with gr.Row():
                        create_single_agent_btn = gr.Button("💾 保存 Agent", variant="primary")
                        clear_form_btn = gr.Button("🧹 清空表单", variant="secondary")

                    create_agent_result = gr.Textbox(
                        label="保存结果",
                        interactive=False,
                        lines=6
                    )

                # 右侧：Agent列表
                with gr.Column(scale=1):
                    agent_list_box, agents_checkbox, delete_agents_btn, edit_agent_btn, selected_agents_display, agent_count_display = create_agent_list_ui()

        # 辩论配置标签页
        with gr.TabItem("🎯 辩论配置"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 辩论设置")

                    topic_input = gr.Textbox(
                        label="辩论主题",
                        placeholder="例如：2024年全球经济展望与投资策略",
                        value="2024年全球经济展望与投资策略"
                    )
                    rounds_input = gr.Slider(
                            label="辩论轮次",
                            minimum=1,
                            maximum=10,
                            value=3,
                            step=1
                        )

                    # Agent选择区域
                    gr.Markdown("### 👥 Agent选择")
                    # 添加加载状态显示组件
                    loading_status = gr.Textbox(
                        label="加载状态",
                        value="🔄 正在加载Agent列表...",
                        interactive=False,
                        visible=True
                    )
                    # 辩论Agent选择组件 - 确保完全可交互
                    debate_agents_checkbox = gr.CheckboxGroup(
                        label="选择参与辩论的Agent",
                        choices=[],  # 初始为空，通过加载函数填充
                        interactive=True,
                        container=True,
                        scale=1,
                        min_width=300,
                        visible=True,
                        # 添加更多配置确保交互性
                        type="value",
                        elem_classes=["debate-agents-checkbox"]
                    )
                    selected_agents_info = gr.Textbox(
                        label="选择信息",
                        interactive=False,
                        lines=2
                    )
                    agents_count_display = gr.Textbox(
                        label="可用Agent数量",
                        interactive=False,
                        visible=False
                    )

                    with gr.Row():
                        refresh_debate_agents_btn = gr.Button("🔄 刷新Agent列表", variant="secondary")
                        confirm_debate_agents_btn = gr.Button("✅ 确认选择", variant="secondary")

                    # 辩论控制
                    with gr.Row():
                        start_debate_btn = gr.Button("🚀 启动辩论", variant="primary")
                        cancel_debate_btn = gr.Button("⏹️ 取消辩论", variant="secondary")

                    debate_status = gr.Textbox(label="辩论状态", interactive=False)

                with gr.Column(scale=2):
                    gr.Markdown("### 📊 辩论进度和结果")

                    # 进度显示
                    debate_progress = gr.Textbox(
                        label="实时进度",
                        interactive=False,
                        lines=10,
                        max_lines=15
                    )

                    # 获取结果按钮
                    with gr.Row():
                        get_results_btn = gr.Button("📊 获取结果", variant="secondary")
                        get_history_btn = gr.Button("📝 获取历史", variant="secondary")
                        monitor_status_btn = gr.Button("🔍 监控状态", variant="secondary")

                    # 结果显示
                    results_output = gr.Textbox(
                        label="辩论结果",
                        interactive=False,
                        lines=20,
                        max_lines=30
                    )
    
    # --- 事件绑定 ---

    # 服务状态检查
    service_status_btn.click(fn=check_service, outputs=service_status_text)

    # 取消辩论函数定义
    def cancel_debate() -> str:
        """取消正在进行的辩论"""
        global current_session_id
        
        if not current_session_id:
            return "❌ 没有进行中的辩论会话"
        
        try:
            # 使用debate_manager实例的cancel_debate方法
            success = debate_manager.cancel_debate(current_session_id)
            if success:
                return f"✅ 辩论会话 {current_session_id} 已取消"
            else:
                return f"❌ 取消辩论会话 {current_session_id} 失败"
        except Exception as e:
            return f"❌ 取消辩论时出错: {str(e)}"

    # 取消辩论事件绑定
    cancel_debate_btn.click(fn=cancel_debate, outputs=debate_status)

    # 获取结果和历史事件绑定
    get_results_btn.click(fn=get_debate_results, outputs=results_output)
    get_history_btn.click(fn=get_history_display, outputs=debate_progress)
    monitor_status_btn.click(fn=monitor_debate_status, outputs=debate_progress)

    # 应用启动时加载初始数据
    demo.load(fn=load_initial_data, outputs=[agents_checkbox, agent_count_display])
    
    # 应用启动时加载辩论Agent列表
    def load_agents_with_status():
        """加载Agent列表并更新加载状态"""
        try:
            logger.info("=== 执行应用启动时Agent列表加载 ===")
            agents = get_debate_agents_for_selection()
            logger.info(f"初始加载获取到的Agent数量: {len(agents)}")
            # 确保返回有效的Agent列表
            if not agents or len(agents) == 0:
                return ["⚠️ 当前没有可用的Agent，请先创建Agent"], "⚠️ 没有可用Agent"
            
            # 更新加载状态为完成，并且显式设置默认选中为空列表
            # 这样用户需要手动选择参与辩论的Agent，而不是默认全部选中
            from gradio import update
            return update(choices=agents, value=[]), "✅ Agent列表加载完成"
        except Exception as e:
            logger.error(f"初始加载Agent列表失败: {str(e)}")
            return [], f"❌ 加载失败: {str(e)}"
    
    # 使用单独的加载函数确保UI组件正确初始化
    demo.load(
        fn=load_agents_with_status, 
        outputs=[debate_agents_checkbox, loading_status],
        show_progress=True
    )
    
    # 暂时移除自动刷新机制，因为当前Gradio版本不支持every参数
    # 保留刷新按钮功能，用户可以手动刷新Agent列表
    # 将在后续版本中使用JavaScript或其他方法实现自动刷新
    
    # 刷新辩论Agent列表 - 确保更新所有相关组件
    refresh_debate_agents_btn.click(
        fn=refresh_debate_agents,
        inputs=[debate_agents_checkbox],  # 传递当前已选项
        outputs=[debate_agents_checkbox, selected_agents_info, agents_count_display]
    )
    
    # 为辩论Agent选择组件添加change事件处理器，实时响应用户选择
    def on_debate_agents_change(selected_agents):
        global selected_debate_agents
        import logging
        logger = logging.getLogger(__name__)
        # 尝试获取当前choices
        try:
            from gradio.components import CheckboxGroup
            # Gradio 3.x/4.x不支持直接获取choices，需靠外层逻辑传递
            current_choices = None  # 若能获取请补充
        except Exception:
            current_choices = None
        logger.info(f"[DEBUG] on_debate_agents_change: 输入selected_agents={selected_agents}, 全局selected_debate_agents-旧值={selected_debate_agents}, 当前choices={current_choices}")
        selected_debate_agents = selected_agents
        logger.info(f"[DEBUG] on_debate_agents_change: 全局selected_debate_agents-新值={selected_debate_agents}")
        if not selected_agents:
            return "💡 请选择参与辩论的Agent"
        # 显示更详细的选择信息
        return f"✅ 已选择 {len(selected_agents)} 个Agent\n" + ", ".join([a.split(' (')[0] for a in selected_agents])
    
    debate_agents_checkbox.change(
        fn=on_debate_agents_change,
        inputs=debate_agents_checkbox,
        outputs=selected_agents_info
    )

    # 确认选择的辩论Agent
    confirm_debate_agents_btn.click(
        fn=confirm_selected_agents,
        inputs=debate_agents_checkbox,
        outputs=selected_agents_info
    )

    # 保存Agent（创建或更新）
    def save_agent_and_clear_form(agent_id, name, role, system_prompt, personality_traits, expertise_areas):
        # 先保存Agent
        save_result, agents_checkbox_update, button_update, count_update = save_agent(
            agent_id, name, role, system_prompt, personality_traits, expertise_areas
        )
        
        # 然后清空表单
        clear_result = clear_agent_form()
        
        # 返回所有更新的组件
        return (
            save_result,  # create_agent_result
            agents_checkbox_update,  # agents_checkbox
            button_update,  # create_single_agent_btn
            count_update,  # agent_count_display
            clear_result[0],  # agent_id_hidden
            clear_result[1],  # agent_name_input
            clear_result[2],  # agent_role_dropdown
            clear_result[3],  # agent_prompt_input
            clear_result[4],  # agent_traits_input
            clear_result[5]   # agent_expertise_input
        )
    
    create_single_agent_btn.click(
        fn=save_agent_and_clear_form,
        inputs=[
            agent_id_hidden, agent_name_input, agent_role_dropdown,
            agent_prompt_input, agent_traits_input, agent_expertise_input
        ],
        outputs=[
            create_agent_result, agents_checkbox, create_single_agent_btn, agent_count_display,
            agent_id_hidden, agent_name_input, agent_role_dropdown,
            agent_prompt_input, agent_traits_input, agent_expertise_input
        ]
    )

    # 清空表單
    clear_form_btn.click(
        fn=clear_agent_form,
        outputs=[
            agent_id_hidden, agent_name_input, agent_role_dropdown,
            agent_prompt_input, agent_traits_input, agent_expertise_input,
            create_agent_result, delete_agents_btn
        ]
    )

    # 删除选定Agent
    delete_agents_btn.click(
        fn=delete_selected_agents,
        inputs=[agents_checkbox],
        outputs=[create_agent_result, agents_checkbox, delete_agents_btn, agent_count_display]
    )

    # 编辑选定Agent
    def edit_selected_agent_action(selected_agents):
        if not selected_agents:
            return "", "", "", "", "", "", "❌ 请先选择要编辑的Agent", gr.update(interactive=True)
        if len(selected_agents) > 1:
            return "", "", "", "", "", "", "❌ 一次只能编辑一个Agent", gr.update(interactive=True)
        
        agent_str = selected_agents[0]
        if " - ID: " in agent_str:
            agent_id = agent_str.split(" - ID: ")[-1]
            return load_agent_to_form(agent_id)
        else:
            return "", "", "", "", "", "", "❌ 无法解析Agent ID", gr.update(interactive=True)

    edit_agent_btn.click(
        fn=edit_selected_agent_action,
        inputs=[agents_checkbox],
        outputs=[
            agent_id_hidden, agent_name_input, agent_role_dropdown,
            agent_prompt_input, agent_traits_input, agent_expertise_input,
            create_agent_result, delete_agents_btn
        ]
    )

    # 启动辩论
    def start_debate_wrapper(topic, rounds):
        global selected_debate_agents
        
        if not selected_debate_agents:
            return "❌ 请先选择并确认参与辩论的Agent", start_debate_btn
        
        result = start_debate_async(topic, rounds, selected_debate_agents)
        # 返回结果和按钮状态（保持不变）
        return result, start_debate_btn
        
    start_debate_btn.click(
        fn=start_debate_wrapper,
        inputs=[topic_input, rounds_input],
        outputs=[debate_status, start_debate_btn]
    )




if __name__ == "__main__":
    # 启动时检查服务状态 - 直接API调用
    print("正在检查API服务状态...")
    try:
        health_response = make_api_request('GET', f"{base_url}/health")
        if health_response.status_code == 200:
            health_data = safe_json_parse(health_response)
            if health_data.get("status") == "healthy":
                print("✅ API服务运行正常")
            else:
                print("⚠️ 警告：API服务状态异常")
        else:
            print("⚠️ 警告：API服务不可用，请确保AgentScope API服务已运行")
    except Exception as e:
        print(f"⚠️ 警告：无法连接到API服务 ({e})，请确保AgentScope API服务已运行")

    # 启动Gradio应用 - 不指定固定端口，让Gradio自动选择可用端口
    demo.launch(
        server_name="0.0.0.0",
        # 移除固定端口设置，让Gradio自动选择可用端口
        share=False,
        debug=True
    )