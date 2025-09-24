#!/usr/bin/env python3
"""
AgentScope 金融分析師辯論系統 - Gradio Web介面
基於 financial_debate_api.sh 的Web實現
"""

import gradio as gr
import requests
import json
import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import datetime

# 加載項目根目錄下的單一 .env 文件
project_root = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=project_root / ".env")

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 請求設定常數
DEFAULT_TIMEOUT = 10  # 預設超時時間10秒

def make_api_request(method: str, url: str, **kwargs) -> requests.Response:
    """
    統一的API請求函式，包含超時設定和錯誤處理

    Args:
        method: HTTP方法 ('GET', 'POST', 'PUT', 'DELETE')
        url: 請求URL
        **kwargs: 其他傳遞給requests的參數

    Returns:
        requests.Response: 回應物件

    Raises:
        requests.RequestException: 請求例外
        ValueError: 無效的HTTP方法
    """
    # 確保設定了超時時間
    if 'timeout' not in kwargs:
        kwargs['timeout'] = DEFAULT_TIMEOUT

    method = method.upper()
    if method not in ['GET', 'POST', 'PUT', 'DELETE']:
        raise ValueError(f"不支援的HTTP方法: {method}")

    try:
        if method == 'GET':
            response = requests.get(url, **kwargs)
        elif method == 'POST':
            response = requests.post(url, **kwargs)
        elif method == 'PUT':
            response = requests.put(url, **kwargs)
        elif method == 'DELETE':
            response = requests.delete(url, **kwargs)

        # 如果請求失敗，記錄更多資訊
        if not response.ok:
            payload = kwargs.get('json')
            log_message = f"API請求失敗: {method} {url}, 狀態碼: {response.status_code}"
            if payload:
                try:
                    # 嘗試格式化JSON payload
                    payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
                    log_message += f"\n--- 請求 Payload ---\n{payload_str}\n--------------------"
                except TypeError:
                    # 如果無法序列化，直接轉為字串
                    log_message += f"\n--- 請求 Payload (非序列化) ---\n{payload}\n--------------------"
            logger.error(log_message)
            
        return response
    except requests.RequestException as e:
        payload = kwargs.get('json')
        log_message = f"API請求例外: {method} {url}, 錯誤: {e}"
        if payload:
            try:
                payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
                log_message += f"\n--- 請求 Payload ---\n{payload_str}\n--------------------"
            except TypeError:
                log_message += f"\n--- 請求 Payload (非序列化) ---\n{payload}\n--------------------"
        logger.error(log_message)
        raise

def safe_json_parse(response: requests.Response) -> dict:
    """
    安全的JSON解析函式，包含錯誤處理

    Args:
        response: requests回應物件

    Returns:
        dict: 解析後的JSON資料

    Raises:
        json.JSONDecodeError: JSON解析錯誤
        Exception: 其他解析錯誤
    """
    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失敗: {e}")
        logger.error(f"回應內容: {response.text[:500]}")
        raise
    except Exception as e:
        logger.error(f"解析回應時出錯: {e}")
        raise

def handle_api_error(response: requests.Response, operation: str) -> str:
    """
    統一的API錯誤處理函式

    Args:
        response: requests回應物件
        operation: 操作描述

    Returns:
        str: 格式化的錯誤訊息
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

    return f"❌ {operation}失敗: {error_msg}"

# 設定（嚴格依賴 .env，不提供程式碼內預設值）
API_BASE_URL = os.environ["API_BASE_URL"]
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", os.environ.get("OLLAMA_API_BASE"))
DEFAULT_MODEL_NAME = os.environ["DEFAULT_MODEL_NAME"]
base_url = f"{API_BASE_URL}/api"

# 預設智慧體設定
DEFAULT_AGENTS = [
    {
        "name": "宏觀經濟分析師",
        "role": "analyst",
        "system_prompt": "你是一位資深的宏觀經濟分析師，擁有15年的全球經濟研究經驗。你擅長分析全球經濟趨勢、貨幣政策、財政政策以及地緣政治事件對經濟的影響。請全程使用繁體中文進行對話和分析。",
        "personality_traits": ["專業", "客觀", "深入"],
        "expertise_areas": ["宏觀經濟", "貨幣政策", "財政政策", "地緣政治"]
    },
    {
        "name": "股票策略分析師",
        "role": "pragmatist", 
        "system_prompt": "你是一位資深的股票策略分析師，擁有12年的股票市場研究經驗。你擅長分析不同行業的發展趨勢、評估企業基本面，並提供股票投資組合配置建議。請全程使用繁體中文進行對話和分析。",
        "personality_traits": ["戰略", "細致", "前瞻性"],
        "expertise_areas": ["股票市場", "行業分析", "企業基本面", "投資組合配置"]
    },
    {
        "name": "固定收益分析師",
        "role": "critic",
        "system_prompt": "你是一位資深的固定收益分析師，擁有10年的債券市場研究經驗。你擅長分析利率走勢、信用風險評估以及各類固定收益產品的投資價值。請全程使用繁體中文進行對話和分析。",
        "personality_traits": ["謹慎", "精確", "風險意識強"],
        "expertise_areas": ["債券市場", "利率分析", "信用風險", "固定收益產品"]
    },
    {
        "name": "另類投資分析師",
        "role": "innovator",
        "system_prompt": "你是一位資深的另類投資分析師，擁有8年的另類投資研究經驗。你擅長分析房地產、私募股權、對沖基金、大宗商品等非傳統投資產品的風險收益特徵。請全程使用繁體中文進行對話和分析。",
        "personality_traits": ["創新", "靈活", "多元思維"],
        "expertise_areas": ["房地產", "私募股權", "對沖基金", "大宗商品"]
    }
]

class DebateManager:
    def __init__(self):
        self.agents = []
        self.session_id = None
        self.debate_history = []
        
    def check_health(self) -> bool:
        """檢查API服務健康狀態"""
        try:
            response = make_api_request('GET', f"{base_url}/health")
            if response.status_code == 200:
                data = safe_json_parse(response)
                return data.get("status") == "healthy"
            return False
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return False
    
    def create_agent(self, name: str, role: str, system_prompt: str,
                    personality_traits: List[str], expertise_areas: List[str]) -> tuple:
        """建立智慧體，返回 (agent_id, error_message)"""
        try:
            payload = {
                "name": name,
                "role": role,
                "system_prompt": system_prompt,
                "llm_config": {
                    "model_name": DEFAULT_MODEL_NAME,
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
                    return None, "API回應中缺少agent_id"
            else:
                error_msg = handle_api_error(response, "建立智慧體")
                return None, error_msg

        except Exception as e:
            logger.error(f"建立智慧體失敗: {e}")
            logger.error(f"傳送的請求體: {payload}")
            return None, f"網路錯誤: {str(e)}"
    
    def configure_agent(self, agent_id: str, topic: str) -> bool:
        """設定智慧體用於辯論"""
        try:
            payload = {
                "debate_topic": topic,
                "additional_instructions": "請基於你的專業領域和知識，對辯論主題發表專業觀點，提供具體的資料、案例和分析支援你的觀點。"
            }

            response = make_api_request(
                'POST',
                f"{base_url}/agents/{agent_id}/configure",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"設定智慧體失敗: {e}")
            return False
    
    def start_debate(self, topic: str, agent_ids: List[str], rounds: int) -> Optional[str]:
        """啟動辯論"""
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
            logger.error(f"啟動辯論失敗: {e}")
            return None
    
    def get_debate_status(self) -> Dict[str, Any]:
        """取得辯論狀態"""
        if not self.session_id:
            return {}

        try:
            response = make_api_request('GET', f"{base_url}/debate/{self.session_id}/status")
            if response.status_code == 200:
                return safe_json_parse(response)
            return {}
        except Exception as e:
            logger.error(f"取得辯論狀態失敗: {e}")
            return {}
    
    def get_debate_history(self) -> List[Dict[str, Any]]:
        """取得辯論歷史"""
        if not self.session_id:
            return []

        try:
            response = make_api_request('GET', f"{base_url}/debate/{self.session_id}/history")
            if response.status_code == 200:
                data = safe_json_parse(response)
                # API可能返回列表或包含history鍵的字典
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
            logger.error(f"取得辯論歷史失敗: {e}")
            return []

    def get_supported_roles(self) -> List[str]:
        """取得支援的Agent角色列表"""
        try:
            response = make_api_request('GET', f"{base_url}/agents/roles")
            if response.status_code == 200:
                data = safe_json_parse(response)
                # API可能返回列表或包含roles鍵的字典
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    roles = data.get("roles", [])
                    return roles if isinstance(roles, list) else []
                else:
                    return []
            return []
        except Exception as e:
            logger.error(f"取得支援角色失敗: {e}")
            return []

    def get_agents_list(self) -> List[Dict[str, Any]]:
        """取得所有Agent列表"""
        try:
            logger.info(f"正在取得Agent列表: {base_url}/agents/")
            response = make_api_request('GET', f"{base_url}/agents/")
            logger.info(f"API回應狀態碼: {response.status_code}")

            if response.status_code == 200:
                # 確保回應文本不為空
                if not response.text or response.text.strip() == "":
                    logger.warning("API回應為空")
                    return []
                
                try:
                    data = safe_json_parse(response)
                    logger.info(f"API回應資料類型: {type(data)}")
                    logger.info(f"API回應資料長度: {len(data) if hasattr(data, '__len__') else 'N/A'}")

                    # 確保返回的是列表格式
                    if isinstance(data, list):
                        # 驗證列表中的每個元素都是字典格式
                        validated_agents = []
                        for agent in data:
                            if isinstance(agent, dict) and "id" in agent and "name" in agent:
                                validated_agents.append(agent)
                        logger.info(f"返回列表格式，包含 {len(validated_agents)} 個有效Agent")
                        return validated_agents
                    elif isinstance(data, dict):
                        agents = data.get("agents", [])
                        if isinstance(agents, list):
                            # 驗證列表中的每個元素都是字典格式
                            validated_agents = []
                            for agent in agents:
                                if isinstance(agent, dict) and "id" in agent and "name" in agent:
                                    validated_agents.append(agent)
                            logger.info(f"返回字典格式，agents欄位包含 {len(validated_agents)} 個有效Agent")
                            return validated_agents
                        else:
                            logger.warning(f"agents欄位不是列表格式: {type(agents)}")
                            return []
                    else:
                        logger.warning(f"意外的資料格式: {type(data)}")
                        return []
                except Exception as json_error:
                    logger.error(f"解析JSON回應失敗: {json_error}")
                    logger.error(f"原始回應文本: {response.text}")
                    return []
            else:
                logger.error(f"API請求失敗: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"取得Agent列表失敗: {e}")
            return []

    def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """取得Agent詳細資訊"""
        try:
            response = make_api_request('GET', f"{base_url}/agents/{agent_id}")
            if response.status_code == 200:
                data = safe_json_parse(response)
                return data
            return None
        except Exception as e:
            logger.error(f"取得Agent詳情失敗: {e}")
            return None

    def cancel_debate(self, session_id: str) -> bool:
        """取消辯論"""
        try:
            response = make_api_request('POST', f"{base_url}/debate/{session_id}/cancel")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"取消辯論失敗: {e}")
            return False

    def get_debate_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """取得辯論結果"""
        try:
            response = make_api_request('GET', f"{base_url}/debate/{session_id}/result")
            if response.status_code == 200:
                data = safe_json_parse(response)
                # 如果返回的是字典格式，直接返回
                if isinstance(data, dict):
                    return data
                # 如果返回的是其他格式，嘗試包裝成字典
                return {"result": data}
            return None
        except Exception as e:
            logger.error(f"取得辯論結果失敗: {e}")
            return None

# 複用頂部已定義的API設定
base_url = f"{API_BASE_URL}/api"

# 全域變數追蹤目前辯論會話
current_session_id = None

# 全域變數追蹤選定的辯論Agent
selected_debate_agents = []

# 全域辯論管理器實例
debate_manager = DebateManager()

def get_debate_agents_for_selection():    
    """取得可用於辯論的Agent列表"""
    try:
        logger.info("=== 開始取得辯論Agent列表 ===")
        
        # 直接從debate_manager取得Agent列表
        agents = debate_manager.get_agents_list()
        logger.info(f"從debate_manager取得的原始Agent資料: {agents}")
        
        # 轉換為Gradio CheckboxGroup所需的格式
        agent_options = []
        if not agents:
            logger.warning("未取得任何Agent")
            return ["⚠️ 目前沒有可用的Agent，請先建立Agent"]
        
        for agent in agents:
            agent_id = agent.get("id", "")
            agent_name = agent.get("name", "未知")
            agent_role = agent.get("role", "未知")
            if agent_id:
                option = f"{agent_name} ({agent_role}) - ID: {agent_id}"
                agent_options.append(option)
                logger.info(f"新增Agent選項: {option}")
        
        logger.info(f"總共取得 {len(agent_options)} 個Agent選項")
        logger.info(f"最終返回的Agent選項列表: {agent_options}")
        
        if not agent_options:
            logger.warning("雖然取得Agent資料，但未能產生有效的選項")
            return ["⚠️ 目前沒有可用的Agent，請先建立Agent"]
        
        return agent_options
    except Exception as e:
        logger.error(f"取得辯論Agent列表失敗: {str(e)}")
        import traceback
        logger.error(f"錯誤堆疊: {traceback.format_exc()}")
        return [f"❌ 取得Agent列表時出錯: {str(e)}"]

def refresh_debate_agents(current_value=None):
    """重新整理辯論Agent列表，並同步已選項"""
    try:
        logger.info("=== 執行重新整理辯論Agent列表操作 ===")
        agent_options = get_debate_agents_for_selection()
        # 安全地處理目前值，確保在設定值之前choices列表已經正確載入
        # 當choices列表為空時，不嘗試設定任何值
        if not agent_options:
            count = 0
            status_msg = "⚠️ 目前沒有可用的Agent"
            filtered_value = []
        else:
            # 同步目前已選項，僅保留仍在choices中的
            filtered_value = [v for v in (current_value or []) if v in agent_options]
            count = len([opt for opt in agent_options if not opt.startswith(('⚠️', '❌'))])
            status_msg = f"✅ Agent列表已重新整理，共 {count} 個可用Agent"
        
        logger.info(f"[SYNC] 重新整理後choices: {agent_options}, filtered_value: {filtered_value}")
        return gr.update(choices=agent_options, value=filtered_value), status_msg, count
    except Exception as e:
        logger.error(f"重新整理辯論Agent列表失敗: {str(e)}")
        return gr.update(choices=[], value=[]), f"❌ 重新整理失敗: {str(e)}", 0

def confirm_selected_agents(selected_agents):
    """確認選擇的辯論Agent"""
    global selected_debate_agents
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[DEBUG] confirm_selected_agents: 輸入selected_agents={selected_agents}, 全域selected_debate_agents-舊值={selected_debate_agents}")
    selected_debate_agents = selected_agents
    logger.info(f"[DEBUG] confirm_selected_agents: 全域selected_debate_agents-新值={selected_debate_agents}")
    if not selected_agents:
        return "❌ 請至少選擇一個Agent參與辯論"
    return f"✅ 已選擇 {len(selected_agents)} 個Agent參與辯論"
def check_service():
    """檢查服務狀態 - 全面系統診斷"""
    try:
        response = make_api_request('GET', f"{base_url}/health")
        if response.status_code == 200:
            data = safe_json_parse(response)
            overall_status = data.get("status", "unknown")
            api_version = data.get("version", "未知")
            environment = data.get("environment", "未知")
            dependencies = data.get("dependencies", {})

            # 建構狀態報告
            status_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌", "unknown": "❓"}.get(overall_status, "❓")
            report_lines = [
                f"{status_emoji} 總計狀態: {overall_status}",
                f"📦 API版本: {api_version}",
                f"🌍 執行環境: {environment}",
                "",
                "🔗 依賴項狀態:"
            ]

            # 處理依賴項狀態
            dep_emojis = {"operational": "✅", "degraded": "⚠️", "outage": "❌"}
            if dependencies:
                for dep_name, dep_status in dependencies.items():
                    emoji = dep_emojis.get(dep_status, "❓")
                    # 將蛇形命名轉換為標題格式
                    display_name = dep_name.replace('_', ' ').title()
                    report_lines.append(f"  {emoji} {display_name}: {dep_status}")
            else:
                report_lines.append("  ❓ 無依賴項資訊")

            return "\n".join(report_lines)
        else:
            return f"❌ API服務不可用 (HTTP {response.status_code})"
    except Exception as e:
        return f"❌ 檢查服務時出錯: {str(e)}"

def create_default_agents_action():
    """一鍵建立所有預設的分析師 Agents"""
    try:
        created_agents = []
        failed_agents = []
        for agent_config in DEFAULT_AGENTS:
            agent_id, error_msg = debate_manager.create_agent(
                name=agent_config["name"],
                role=agent_config["role"],
                system_prompt=agent_config["system_prompt"],
                personality_traits=agent_config["personality_traits"],
                expertise_areas=agent_config["expertise_areas"]
            )
            if agent_id:
                created_agents.append(agent_config["name"])
            else:
                failed_agents.append(f"{agent_config['name']} ({error_msg})")
        
        success_msg = f"✅ 成功建立 {len(created_agents)} 個預設 Agent: {', '.join(created_agents)}" if created_agents else ""
        error_msg = f"❌ 建立失敗 {len(failed_agents)} 個 Agent: {', '.join(failed_agents)}" if failed_agents else ""
        
        # 刷新 Agent 列表
        updated_agents, count_text = refresh_agent_list_with_retry()
        
        final_message = "\n".join(filter(None, [success_msg, error_msg]))
        
        return final_message, gr.update(choices=updated_agents, value=[]), gr.update(value=count_text)
    except Exception as e:
        return f"❌ 建立預設 Agent 時發生未知錯誤: {str(e)}", gr.update(), gr.update()

def start_debate_async(topic: str, rounds: int, selected_agents: List[str]) -> str:
    """非同步啟動辯論"""
    try:
        if not selected_agents:
            return "❌ 請先選擇參與辯論的Agent"

        # 解析選擇的Agent ID
        agent_ids = []
        for agent_str in selected_agents:
            # 從格式 "名稱 (角色) - ID: xxx" 中提取ID
            if " - ID: " in agent_str:
                agent_id = agent_str.split(" - ID: ")[-1]
                agent_ids.append(agent_id)

        if not agent_ids:
            return "❌ 無法解析選擇的Agent ID"

        # 設定Agent用於辯論 - 直接API呼叫
        for agent_id in agent_ids:
            logger.info(f"--- 開始操作：為辯論設定Agent ---")
            url = f"{base_url}/agents/{agent_id}/configure"
            logger.info(f"即將呼叫 POST: {url}")
            config_payload = {
                "debate_topic": topic,
                "additional_instructions": "請基於你的專業領域和知識，對辯論主題發表專業觀點，提供具體的資料、案例和分析支援你的觀點。",
                "llm_config": {
                    "model_name": DEFAULT_MODEL_NAME,
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
                return f"❌ 設定Agent {agent_id} 失敗: HTTP {config_response.status_code}"

        # 啟動辯論 - 直接API呼叫
        logger.info(f"--- 開始操作：啟動辯論 ---")
        url = f"{base_url}/debate/start"
        logger.info(f"即將呼叫 POST: {url}")
        debate_payload = {
            "topic": topic,
            "agent_ids": agent_ids,
            "rounds": rounds,
            "max_duration_minutes": 30,
            "llm_config": {
                "model_name": DEFAULT_MODEL_NAME,
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
                # 更新全域session_id用於後續操作
                global current_session_id
                current_session_id = session_id
                return f"✅ 辯論啟動成功！會話ID: {session_id}"
            else:
                return "❌ 辯論啟動失敗: API未返回session_id"
        else:
            error_msg = handle_api_error(debate_response, "辯論啟動")
            return f"❌ 辯論啟動失敗: {error_msg}"
    except Exception as e:
        return f"❌ 啟動辯論時出錯: {str(e)}"

def get_debate_progress() -> str:
    """取得辯論進度 - 直接API呼叫"""
    global current_session_id
    global selected_debate_agents

    if not current_session_id:
        return "暫無進行中的辯論"

    try:
        # 直接API呼叫取得辯論狀態
        status_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/status")
        if status_response.status_code != 200:
            return f"❌ 無法取得辯論狀態: HTTP {status_response.status_code}"

        status = safe_json_parse(status_response)
        current_status = status.get("status", "unknown")
        current_round = status.get("current_round", 0)
        total_rounds = status.get("total_rounds", 0)
        progress_value = status.get("progress", 0)

        progress_info = []
        progress_info.append("🔄 辯論進度即時監控")
        progress_info.append("-" * 40)
        progress_info.append(f"📊 狀態: {current_status}")
        progress_info.append(f"🎯 輪次: {current_round}/{total_rounds}")
        progress_info.append(f"📈 進度: {progress_value}%")

        # 顯示參與辯論的Agent資訊
        if selected_debate_agents:
            progress_info.append("👥 參與辯論的Agent:")
            for agent in selected_debate_agents:
                # 提取Agent名稱和角色資訊
                if " (" in agent and ") " in agent:
                    agent_name_role = agent.split(" - ID:")[0]
                    progress_info.append(f"  {agent_name_role}")

        if current_status == "running":
            progress_info.append("\n⏳ 辯論進行中...")
            # 取得最新發言 - 直接API呼叫
            history_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/history")
            if history_response.status_code == 200:
                history_data = safe_json_parse(history_response)
                # API可能返回列表或包含history鍵的字典
                if isinstance(history_data, list):
                    history = history_data
                elif isinstance(history_data, dict):
                    history = history_data.get("history", [])
                else:
                    history = []

                if history:
                    # 顯示最近的發言
                    recent_messages = history[-3:]  # 取得最後3條訊息
                    progress_info.append("\n💬 最新發言:")
                    for msg in recent_messages:
                        agent_name = msg.get("agent_name", "未知")
                        agent_id = msg.get("agent_id", "未知")  # 取得Agent ID
                        content = msg.get("content", "")[:100]
                        round_num = msg.get("round", 1)
                        progress_info.append(f"第{round_num}輪 - {agent_name} - ID: {agent_id}: {content}...")

        elif current_status == "completed":
            progress_info.append("\n✅ 辯論已完成")
            # 顯示最終結果摘要 - 直接API呼叫
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
                    progress_info.append(f"🏆 最終結論: {final_conclusion[:200]}...")

        elif current_status == "failed":
            progress_info.append("\n❌ 辯論失敗")
        else:
            progress_info.append("\n⏸️ 辯論未開始或已暫停")

        progress_info.append(f"\n🕒 更新時間: {datetime.now().strftime('%H:%M:%S')}")

        return "\n".join(progress_info)

    except Exception as e:
        return f"❌ 取得進度時出錯: {str(e)}"

def get_debate_results() -> str:
    """取得辯論結果 - 直接API呼叫"""
    global current_session_id

    try:
        # 首先嘗試取得完整結果 - 直接API呼叫
        if current_session_id:
            result_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/result")
            if result_response.status_code == 200:
                result_data = safe_json_parse(result_response)
                # 如果返回的是字典格式，直接返回
                if isinstance(result_data, dict):
                    return format_debate_result(result_data)
                else:
                    # 嘗試包裝成字典格式
                    wrapped_result = {"result": result_data}
                    return format_debate_result(wrapped_result)

        # 如果沒有完整結果，取得歷史記錄 - 直接API呼叫
        if current_session_id:
            history_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/history")
            if history_response.status_code == 200:
                history_data = safe_json_parse(history_response)
                # API可能返回列表或包含history鍵的字典
                if isinstance(history_data, list):
                    history = history_data
                elif isinstance(history_data, dict):
                    history = history_data.get("history", [])
                else:
                    history = []

                if history:
                    return format_debate_history(history)

        return "❌ 暫無辯論結果"

    except Exception as e:
        return f"❌ 取得結果時出錯: {str(e)}"

def format_debate_result(result_data: Dict[str, Any]) -> str:
    """格式化辯論結果"""
    results = []
    results.append("📊 辯論結果彙總")
    results.append("=" * 50)

    # 最終結論
    final_conclusion = result_data.get("final_conclusion", "")
    if final_conclusion:
        results.append(f"\n🏆 最終結論:")
        results.append(final_conclusion)

    # 可信度分數
    confidence_score = result_data.get("confidence_score", "")
    if confidence_score:
        results.append(f"\n📈 可信度分數: {confidence_score}")

    # 共識要點
    consensus_points = result_data.get("consensus_points", [])
    if consensus_points:
        results.append("\n🙌 共識要點:")
        for i, point in enumerate(consensus_points, 1):
            if point:
                results.append(f"{i}. {point}")

    # 分歧觀點
    divergent_views = result_data.get("divergent_views", [])
    if divergent_views:
        results.append("\n⚖️ 分歧觀點:")
        for i, view in enumerate(divergent_views, 1):
            if view:
                results.append(f"{i}. {view}")

    return "\n".join(results)

def format_debate_history(history: List[Dict[str, Any]]) -> str:
    """格式化辯論歷史記錄"""
    if not history:
        return "暫無歷史記錄"

    results = []
    results.append("📝 辯論歷史記錄")
    results.append("=" * 50)

    # 按輪次分組
    rounds = {}
    for entry in history:
        round_num = entry.get("round", 1)
        if round_num not in rounds:
            rounds[round_num] = []
        rounds[round_num].append(entry)

    # 輸出每輪內容
    for round_num in sorted(rounds.keys()):
        results.append(f"\n🔄 第 {round_num} 輪")
        results.append("-" * 30)

        for entry in rounds[round_num]:
            agent_name = entry.get("agent_name", "未知")
            role = entry.get("agent_role", "未知")
            agent_id = entry.get("agent_id", "未知")  # 取得Agent ID
            content = entry.get("content", "").strip()

            if content:  # 只顯示有內容的條目
                # 同時顯示Agent名稱和ID
                results.append(f"👤 {agent_name} ({role}) - ID: {entry.get('agent_id', '未知')}:")
                results.append(f"{content}")
                results.append("")

    return "\n".join(results)

def monitor_debate_status() -> str:
    """監控辯論狀態 - 直接API呼叫"""
    global current_session_id

    if not current_session_id:
        return "暫無進行中的辯論"

    try:
        # 直接API呼叫取得辯論狀態
        status_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/status")
        if status_response.status_code != 200:
            return f"❌ 無法取得辯論狀態: HTTP {status_response.status_code}"

        status = safe_json_parse(status_response)
        current_status = status.get("status", "unknown")
        current_round = status.get("current_round", 0)
        total_rounds = status.get("total_rounds", 0)
        progress = status.get("progress", 0)

        status_info = []
        status_info.append("🔍 辯論狀態監控")
        status_info.append("-" * 30)
        status_info.append(f"狀態: {current_status}")
        status_info.append(f"輪次: {current_round}/{total_rounds}")
        status_info.append(f"進度: {progress}%")

        if current_status == "running":
            status_info.append("\n⏳ 辯論進行中...")
            # 取得最新發言 - 直接API呼叫
            history_response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/history")
            if history_response.status_code == 200:
                history_data = safe_json_parse(history_response)
                # API可能返回列表或包含history鍵的字典
                if isinstance(history_data, list):
                    history = history_data
                elif isinstance(history_data, dict):
                    history = history_data.get("history", [])
                else:
                    history = []

                if history:
                    # 取得最新發言
                    try:
                        latest_entry = max(history, key=lambda x: x.get("timestamp", ""))
                        agent_name = latest_entry.get("agent_name", "未知")
                        agent_id = latest_entry.get("agent_id", "未知")  # 取得Agent ID
                        content_preview = latest_entry.get("content", "")[:100]
                        status_info.append(f"最新發言: {agent_name} - ID: {agent_id} - {content_preview}...")
                    except (ValueError, TypeError):
                        # 如果沒有timestamp欄位或其他錯誤，使用最後一個條目
                        if history:
                            latest_entry = history[-1]
                            agent_name = latest_entry.get("agent_name", "未知")
                            agent_id = latest_entry.get("agent_id", "未知")  # 取得Agent ID
                            content_preview = latest_entry.get("content", "")[:100]
                            status_info.append(f"最新發言: {agent_name} - ID: {agent_id} - {content_preview}...")

        elif current_status == "completed":
            status_info.append("\n✅ 辯論已完成")
        elif current_status == "failed":
            status_info.append("\n❌ 辯論失敗")

        return "\n".join(status_info)

    except Exception as e:
        return f"❌ 監控狀態時出錯: {str(e)}"

def get_agent_templates() -> str:
    """取得智慧體範本JSON"""
    return json.dumps(DEFAULT_AGENTS, ensure_ascii=False, indent=2)

def validate_agent_input(name: str, role: str, system_prompt: str, personality_traits: str, expertise_areas: str) -> str:
    """驗證Agent輸入資料，返回錯誤訊息或空字串"""
    if not name.strip():
        return "❌ Agent名稱不能為空"
    if not role.strip():
        return "❌ 請選擇Agent角色"
    if not system_prompt.strip():
        return "❌ 系統提示詞不能為空"
    if len(system_prompt.strip()) < 10:
        return f"❌ 系統提示詞至少需要10個字元（目前{len(system_prompt.strip())}個字元）\n請提供更詳細的角色描述。"

    # 轉換字串為列表
    personality_list = [trait.strip() for trait in personality_traits.split(',') if trait.strip()]
    expertise_list = [area.strip() for area in expertise_areas.split(',') if area.strip()]

    if not personality_list:
        return "❌ 請至少填寫一個個性特徵"
    if not expertise_list:
        return "❌ 請至少填寫一個專業領域"

    return ""  # 驗證通過

def prepare_agent_payload(name: str, role: str, system_prompt: str, personality_traits: str, expertise_areas: str) -> dict:
    """準備Agent API請求資料"""
    personality_list = [trait.strip() for trait in personality_traits.split(',') if trait.strip()]
    expertise_list = [area.strip() for area in expertise_areas.split(',') if area.strip()]

    return {
        "name": name.strip(),
        "role": role.strip(),
        "system_prompt": system_prompt.strip(),
        "llm_config": {
            "model_name": DEFAULT_MODEL_NAME,
            "temperature": 0.7,
            "max_tokens": 1024
        },
        "personality_traits": personality_list,
        "expertise_areas": expertise_list
    }

def save_agent(agent_id: str, name: str, role: str, system_prompt: str,
                personality_traits: str, expertise_areas: str) -> tuple:
    """儲存Agent（建立或更新）"""
    try:
        # 驗證輸入
        validation_error = validate_agent_input(name, role, system_prompt, personality_traits, expertise_areas)
        if validation_error:
            return validation_error, gr.update(), gr.update(interactive=True), gr.update()

        # 準備API請求資料
        payload = prepare_agent_payload(name, role, system_prompt, personality_traits, expertise_areas)

        # API請求資料已經在 prepare_agent_payload 中準備好

        # 根據agent_id決定是建立還是更新
        if agent_id and agent_id.strip():
            # 更新現有Agent
            logger.info(f"--- 開始操作：更新 Agent ---")
            url = f"{base_url}/agents/{agent_id}"
            logger.info(f"即將呼叫 PUT: {url}")
            response = make_api_request(
                'PUT',
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            operation = "更新"
            success_verb = "更新"
        else:
            # 建立新Agent
            logger.info(f"--- 開始操作：建立新 Agent ---")
            url = f"{base_url}/agents/create"
            logger.info(f"即將呼叫 POST: {url}")
            response = make_api_request(
                'POST',
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            operation = "建立"
            success_verb = "建立"

        if response.status_code == 200:
            data = safe_json_parse(response)

            if operation == "建立":
                agent_id_result = data.get("agent_id")
                if agent_id_result and agent_id_result != "null":
                    # 成功建立，使用帶重試機制的重新整理來取得最新的Agent列表
                    updated_agents, count_text = refresh_agent_list_with_retry()
                    success_msg = f"""✅ Agent{success_verb}成功！
📋 詳細資訊：
• ID: {agent_id_result}
• 名稱: {name.strip()}
• 角色: {role.strip()}

🎉 新{success_verb}的Agent已自動新增到列表中！
✨ 表單已清空，您可以繼續建立新的Agent
"""
                    # 清空表單並返回結果
                    return success_msg, gr.update(choices=updated_agents, value=[]), gr.update(interactive=True), gr.update(value=count_text)
                else:
                    return "❌ API回應中缺少agent_id", gr.update(), gr.update(interactive=True), gr.update()
            else:
                # 成功更新，使用帶重試機制的重新整理來取得最新的Agent列表
                updated_agents, count_text = refresh_agent_list_with_retry()
                success_msg = f"""✅ Agent{success_verb}成功！
📋 更新資訊：
• ID: {agent_id}
• 名稱: {name.strip()}
• 角色: {role.strip()}

Agent列表已自動重新整理。
✨ 表單已清空，您可以繼續建立新的Agent或編輯其他Agent
"""
                # 清空表單並返回結果
                return success_msg, gr.update(choices=updated_agents, value=[]), gr.update(interactive=True), gr.update(value=count_text)
        else:
            error_msg = handle_api_error(response, f"{operation}Agent")
            return error_msg, gr.update(), gr.update(interactive=True), gr.update()

    except Exception as e:
        return f"❌ 儲存Agent時出錯: {str(e)}", gr.update(), gr.update(interactive=True), gr.update()

def refresh_agent_list_with_retry() -> tuple:
    """
    帶重試機制的Agent列表重新整理函式

    Returns:
        tuple: (agent_options, count_text) - Agent列表選項和計數器文本
    """
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        logger.info(f"=== Agent列表重新整理嘗試 {attempt + 1}/{max_retries} ===")

        agents = get_agents_for_selection()
        
        # 日志記錄取得的Agent列表和長度
        logger.info(f"取得的Agent列表: {agents}")
        logger.info(f"取得的Agent數量: {len(agents)}")

        # 無論列表是否為空，都計算總數並返回
        agent_count = len(agents)
        count_text = f"目前 Agent 總數：{agent_count}"
        logger.info(f"✅ 第 {attempt + 1} 次嘗試取得 {agent_count} 個Agent")
        return agents, count_text

    # 所有重試都失敗（理論上不會到達這裡，因為上面的迴圈總是返回）
    logger.error("❌ 重試後仍未取得Agent資料，返回空列表")
    return [], "目前 Agent 總數：0"

def get_agents_for_selection() -> List[str]:
    """取得所有Agent用於選擇 - 直接API呼叫"""
    try:
        logger.info("=== 開始取得Agent列表用於選擇 ===")
        logger.info(f"目標API URL: {base_url}/agents/")

        # 直接API呼叫取得Agent列表
        response = make_api_request('GET', f"{base_url}/agents/")
        agent_options = []

        if response.status_code == 200:
            data = safe_json_parse(response)
            logger.info(f"API回應狀態碼: {response.status_code}")
            logger.info(f"API回應資料類型: {type(data)}")

            # 詳細記錄API返回的原始資料
            if isinstance(data, list):
                logger.info(f"API返回原始資料（列表格式）: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                agents_list = data
                logger.info(f"返回列表格式，包含 {len(agents_list)} 個Agent")
            elif isinstance(data, dict):
                # 特別處理：優先檢查是否有 'items' 欄位（這是常見的分頁API回應格式）
                if 'items' in data:
                    agents_list = data.get('items', [])
                    logger.info(f"返回分頁格式，items欄位包含 {len(agents_list) if isinstance(agents_list, list) else 0} 個Agent")
                else:
                    agents_list = data.get("agents", [])
                    logger.info(f"返回字典格式，agents欄位包含 {len(agents_list) if isinstance(agents_list, list) else 0} 個Agent")
            else:
                logger.warning(f"意外的資料格式: {type(data)}")
                logger.warning(f"原始資料內容: {str(data)[:200]}...")
                agents_list = []

            for agent in agents_list:
                agent_name = agent.get('name', '未知')
                agent_role = agent.get('role', '未知')
                agent_id = agent.get('id', '未知')
                agent_created_at = agent.get('created_at', '未知')
                agent_status = agent.get('status', '未知')

                option = f"{agent_name} ({agent_role}) - ID: {agent_id}"
                agent_options.append(option)

                # 詳細記錄每個Agent的資訊
                logger.info(f"Agent詳情 - 名稱: {agent_name}, 角色: {agent_role}, ID: {agent_id}, 建立時間: {agent_created_at}, 狀態: {agent_status}")
                logger.info(f"新增Agent選項: {option}")

            logger.info(f"總共取得 {len(agent_options)} 個Agent選項")
            logger.info("=== Agent列表取得完成 ===")
            return agent_options
        else:
            logger.error(f"=== API請求失敗 ===")
            logger.error(f"HTTP狀態碼: {response.status_code}")
            logger.error(f"回應內容: {response.text}")
            logger.error(f"回應標頭: {dict(response.headers)}")
            logger.error("=== Agent列表取得失敗 ===")
            return []
    except Exception as e:
        logger.error(f"=== 取得Agent選擇列表例外 ===")
        logger.error(f"例外資訊: {e}")
        logger.error(f"例外詳情", exc_info=True)
        logger.error("=== Agent列表取得例外結束 ===")
        return []

def load_agent_to_form(agent_id: str) -> tuple:
    """載入 Agent 到表單進行編輯"""
    try:
        # 呼叫API取得Agent詳細資訊
        logger.info(f"--- 開始操作：載入 Agent 進行編輯 ---")
        url = f"{base_url}/agents/{agent_id}"
        logger.info(f"即將呼叫 GET: {url}")
        response = make_api_request('GET', url)
        if response.status_code == 200:
            agent_data = safe_json_parse(response)

            # 提取Agent資訊
            name = agent_data.get("name", "")
            role = agent_data.get("role", "")
            system_prompt = agent_data.get("system_prompt", "")
            personality_traits = agent_data.get("personality_traits", [])
            expertise_areas = agent_data.get("expertise_areas", [])

            # 轉換為字串格式
            traits_str = ", ".join(personality_traits) if isinstance(personality_traits, list) else str(personality_traits)
            expertise_str = ", ".join(expertise_areas) if isinstance(expertise_areas, list) else str(expertise_areas)

            success_msg = f"""✅ 成功載入Agent進行編輯
📋 詳細資訊：
• ID: {agent_id}
• 名稱: {name}
• 角色: {role}

請修改表單中的值，然後點擊"儲存 Agent"。"""

            # 返回更新後的表單值和禁用刪除按鈕
            return (agent_id, name, role, system_prompt, traits_str, expertise_str, success_msg, gr.update(interactive=False))
        else:
            error_msg = f"❌ 取得Agent詳細資訊失敗: {handle_api_error(response, '取得Agent詳細資訊')}"
            return ("", "", "", "", "", "", error_msg, gr.update(interactive=True))

    except Exception as e:
        return ("", "", "", "", "", "", f"❌ 載入Agent詳細資訊時出錯: {str(e)}", gr.update(interactive=True))

def clear_agent_form():
    """清空Agent表單，返回到建立模式"""
    return (
        "",  # agent_id_hidden
        "",  # agent_name_input
        "analyst",  # agent_role_dropdown (預設值)
        "",  # agent_prompt_input
        "專業,客觀,深入",  # agent_traits_input (預設值)
        "宏觀經濟,貨幣政策,財政政策",  # agent_expertise_input (預設值)
        "✨ 表單已清空，進入新建模式",  # create_agent_result
        gr.update(interactive=True)  # 重新啟用刪除按鈕
    )

def get_supported_roles_list() -> List[str]:
    """取得支援的角色列表 - 直接API呼叫"""
    try:
        response = make_api_request('GET', f"{base_url}/agents/roles")
        if response.status_code == 200:
            data = safe_json_parse(response)
            # API可能返回列表或包含roles鍵的字典
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                roles = data.get("roles", [])
                return roles if isinstance(roles, list) else []
            else:
                return []
        else:
            logger.warning(f"取得角色列表失敗: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"取得支援角色失敗: {e}")
        return ["analyst", "pragmatist", "critic", "innovator"]  # 預設值

def load_initial_data():
    """載入初始資料，用於應用程式啟動時填充Agent列表"""
    agents, count_text = refresh_agent_list_with_retry()
    return gr.update(choices=agents), gr.update(value=count_text)

def delete_selected_agents(selected_agents: List[str]) -> tuple:
    """刪除選定的Agent"""
    if not selected_agents:
        return "❌ 請先選擇要刪除的Agent", gr.update(), gr.update(interactive=True), gr.update()

    deleted_count = 0
    failed_deletions = []

    for agent_str in selected_agents:
        # 從格式 "名稱 (角色) - ID: xxx" 中提取ID
        if " - ID: " in agent_str:
            agent_id = agent_str.split(" - ID: ")[-1]
            try:
                logger.info(f"--- 開始操作：刪除 Agent ---")
                url = f"{base_url}/agents/{agent_id}"
                logger.info(f"即將呼叫 DELETE: {url}")
                response = make_api_request('DELETE', url)
                if response.status_code == 200:
                    deleted_count += 1
                    logger.info(f"成功刪除Agent: {agent_id}")
                else:
                    failed_deletions.append(f"{agent_str} (HTTP {response.status_code})")
                    logger.error(f"刪除Agent失敗: {agent_id}, HTTP {response.status_code}")
            except Exception as e:
                failed_deletions.append(f"{agent_str} (錯誤: {str(e)})")
                logger.error(f"刪除Agent時出錯: {agent_id}, 錯誤: {e}")
        else:
            failed_deletions.append(f"{agent_str} (無法解析ID)")
            logger.error(f"無法解析Agent ID: {agent_str}")

    # 使用帶重試機制的重新整理取得更新後的Agent列表
    updated_agents, count_text = refresh_agent_list_with_retry()

    # 建構彙總訊息
    summary_parts = []
    if deleted_count > 0:
        summary_parts.append(f"✅ 成功刪除 {deleted_count} 個Agent")
    if failed_deletions:
        summary_parts.append(f"❌ 刪除失敗 {len(failed_deletions)} 個:")
        for failure in failed_deletions:
            summary_parts.append(f"  • {failure}")

    return "\n".join(summary_parts), gr.update(choices=updated_agents, value=[]), gr.update(interactive=True), gr.update(value=count_text)


# 建立獨立的UI函式
def create_agent_list_ui():
    """建立Agent列表UI元件，返回需要外部引用的元件控制代碼"""
    with gr.Group() as agent_list_box:
        gr.Markdown("### 📋 Agent 列表")
        agent_count_display = gr.Markdown("目前 Agent 總數：0")
        with gr.Row():
            refresh_agents_btn = gr.Button("🔄 重新整理列表")
        agents_checkbox = gr.CheckboxGroup(
            label="選擇參與辯論的Agent",
            choices=[],
            value=[],
            interactive=True
        )
        selected_agents_display = gr.Textbox(
            label="已選擇的Agent",
            interactive=False,
            lines=3,
            value="未選擇Agent"
        )
        with gr.Row():
            edit_agent_btn = gr.Button("✏️ 編輯選中Agent", variant="secondary")
            delete_agents_btn = gr.Button("🗑️ 刪除選定Agent", variant="destructive")

    # 內部事件繫結
    def update_selected_agents_display(selected_agents):
        if selected_agents:
            return f"已選擇 {len(selected_agents)} 個Agent:\n" + "\n".join(selected_agents)
        return "未選擇Agent"

    agents_checkbox.change(
        fn=update_selected_agents_display,
        inputs=agents_checkbox,
        outputs=selected_agents_display
    )

    def refresh_agents_list_action():
        logger.info("=== 使用者觸發Agent列表重新整理 ===")
        new_choices, count_text = refresh_agent_list_with_retry()
        logger.info(f"重新整理完成，取得 {len(new_choices)} 個Agent選項")
        return gr.update(choices=new_choices, value=[]), gr.update(value=count_text)

    refresh_agents_btn.click(
        fn=refresh_agents_list_action,
        outputs=[agents_checkbox, agent_count_display]
    )

    return agent_list_box, agents_checkbox, delete_agents_btn, edit_agent_btn, selected_agents_display, agent_count_display

# 建立一個全域函式來取得和顯示辯論歷史
def get_history_display() -> str:
    """取得辯論歷史並格式化顯示"""
    global current_session_id
    global debate_manager
    
    if not current_session_id or not debate_manager:
        return "暫無辯論歷史記錄"
    
    try:
        # 呼叫API取得歷史記錄
        response = make_api_request('GET', f"{base_url}/debate/{current_session_id}/history")
        if response.status_code == 200:
            data = safe_json_parse(response)
            
            # API可能返回列表或包含history鍵的字典
            if isinstance(data, dict):
                history = data.get("history", [])
            elif isinstance(data, list):
                history = data
            else:
                history = []
            
            # 使用已有的format_debate_history函式格式化顯示
            return format_debate_history(history)
        return "❌ 無法取得辯論歷史"
    except Exception as e:
        return f"❌ 取得歷史時出錯: {str(e)}"

# 建立Gradio介面
with gr.Blocks(title="AgentScope 金融分析師辯論系統") as demo:
    gr.Markdown("""
    # 🤖 AgentScope 金融分析師辯論系統

    基於 AI 智慧體的多輪辯論系統，支援動態建立和管理 Agent。

    ## 使用步驟：
    1. 檢查服務狀態
    2. 建立智慧體或選擇現有智慧體
    3. 設定辯論主題和輪次
    4. 啟動辯論並即時檢視進度
    5. 檢視辯論結果和歷史記錄
    """)

    # 服務狀態檢查
    with gr.Row():
        service_status_btn = gr.Button("🔍 檢查服務狀態", variant="secondary")
        service_status_text = gr.Textbox(label="服務狀態", interactive=False, lines=6, scale=4)

    # 主標籤頁
    with gr.Tabs() as tabs:
        # Agent管理標籤頁
        with gr.TabItem("🤖 Agent 管理") as agent_management_tab:
            with gr.Row():
                # 左側：Agent設定
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 Agent 設定")
                    gr.Markdown("""
                    ### 分析師功能說明
                    
                    **新增分析師**：直接在表單中填寫所有必填資訊（名稱、角色、提示詞等），然後點擊「儲存 Agent」按鈕。
                    
                    **編輯現有分析師**：在右側 Agent 列表中選擇一位分析師，點擊「編輯選中 Agent」按鈕，修改表單中的資訊後點擊「儲存 Agent」按鈕。
                    """)

                    # 隱藏的agent_id欄位，用於區分建立和編輯模式
                    agent_id_hidden = gr.Textbox(
                        visible=False,
                        label="Agent ID"
                    )

                    agent_name_input = gr.Textbox(
                        label="Agent 名稱",
                        placeholder="例如：宏觀經濟分析師"
                    )
                    agent_role_dropdown = gr.Dropdown(
                        label="Agent 角色",
                        choices=["analyst", "pragmatist", "critic", "innovator"],
                        value="analyst",
                        interactive=True
                    )
                    agent_prompt_input = gr.Textbox(
                        label="系統提示詞",
                        placeholder="輸入 Agent 的角色描述和行為指導...",
                        lines=3
                    )
                    agent_traits_input = gr.Textbox(
                        label="個性特徵 (用逗號分隔)",
                        placeholder="例如：專業,客觀,深入",
                        value="專業,客觀,深入"
                    )
                    agent_expertise_input = gr.Textbox(
                        label="專業領域 (用逗號分隔)",
                        placeholder="例如：宏觀經濟,貨幣政策,財政政策",
                        value="宏觀經濟,貨幣政策,財政政策"
                    )

                    with gr.Row():
                        create_single_agent_btn = gr.Button("💾 儲存 Agent", variant="primary")
                        clear_form_btn = gr.Button("🧹 清空表單", variant="secondary")

                    create_agent_result = gr.Textbox(
                        label="儲存結果",
                        interactive=False,
                        lines=6
                    )

                # 右側：Agent列表
                with gr.Column(scale=1):
                    (agent_list_box, agents_checkbox, delete_agents_btn,
                     edit_agent_btn, selected_agents_display,
                     agent_count_display) = create_agent_list_ui()

        # 辯論設定標籤頁
        with gr.TabItem("🎯 辯論設定") as debate_setup_tab:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 辯論設定")

                    topic_input = gr.Textbox(
                        label="辯論主題",
                        placeholder="2024年全球經濟展望與投資策略",
                        value=""
                    )
                    rounds_input = gr.Slider(
                            label="辯論輪次",
                            minimum=1,
                            maximum=10,
                            value=3,
                            step=1
                        )

                    # Agent選擇區域
                    gr.Markdown("### 👥 Agent選擇")
                    # 新增載入狀態顯示元件
                    loading_status = gr.Textbox(
                        label="載入狀態",
                        value="🔄 正在載入Agent列表...",
                        interactive=False,
                        visible=True
                    )
                    # 辯論Agent選擇元件 - 確保完全可互動
                    debate_agents_checkbox = gr.CheckboxGroup(
                        label="選擇參與辯論的Agent",
                        choices=[],  # 初始為空，透過載入函式填充
                        interactive=True,
                        container=True,
                        scale=1,
                        min_width=300,
                        visible=True,
                        # 新增更多設定確保互動性
                        type="value",
                        elem_classes=["debate-agents-checkbox"]
                    )
                    selected_agents_info = gr.Textbox(
                        label="選擇資訊",
                        interactive=False,
                        lines=2
                    )
                    agents_count_display_debate = gr.Textbox(
                        label="可用Agent數量",
                        interactive=False,
                        visible=False
                    )

                    with gr.Row():
                        refresh_debate_agents_btn = gr.Button("🔄 重新整理Agent列表", variant="secondary")
                        confirm_debate_agents_btn = gr.Button("✅ 確認選擇", variant="secondary")

                    # 辯論控制
                    with gr.Row():
                        start_debate_btn = gr.Button("🚀 啟動辯論", variant="primary")
                        cancel_debate_btn = gr.Button("⏹️ 取消辯論", variant="secondary")

                    debate_status = gr.Textbox(label="辯論狀態", interactive=False)

                with gr.Column(scale=2):
                    gr.Markdown("### 📊 辯論進度和結果")

                    # 進度顯示
                    debate_progress = gr.Textbox(
                        label="即時進度",
                        interactive=False,
                        lines=10,
                        max_lines=15
                    )

                    # 取得結果按鈕
                    with gr.Row():
                        get_results_btn = gr.Button("📊 取得結果", variant="secondary")
                        get_history_btn = gr.Button("📝 取得歷史", variant="secondary")
                        monitor_status_btn = gr.Button("🔍 監控狀態", variant="secondary")

                    # 結果顯示
                    results_output = gr.Textbox(
                        label="辯論結果",
                        interactive=False,
                        lines=20,
                        max_lines=30
                    )
    
    # --- 事件繫結 ---

    # 服務狀態檢查
    service_status_btn.click(fn=check_service, outputs=service_status_text)


    # 取消辯論函式定義
    def cancel_debate() -> str:
        """取消正在進行的辯論"""
        global current_session_id
        
        if not current_session_id:
            return "❌ 沒有進行中的辯論會話"
        
        try:
            # 使用debate_manager實例的cancel_debate方法
            success = debate_manager.cancel_debate(current_session_id)
            if success:
                return f"✅ 辯論會話 {current_session_id} 已取消"
            else:
                return f"❌ 取消辯論會話 {current_session_id} 失敗"
        except Exception as e:
            return f"❌ 取消辯論時出錯: {str(e)}"

    # 取消辯論事件繫結
    cancel_debate_btn.click(fn=cancel_debate, outputs=debate_status)

    # 取得結果和歷史事件繫結
    get_results_btn.click(fn=get_debate_results, outputs=results_output)
    get_history_btn.click(fn=get_history_display, outputs=debate_progress)
    monitor_status_btn.click(fn=monitor_debate_status, outputs=debate_progress)

    # 應用程式啟動時載入初始資料
    demo.load(fn=load_initial_data, outputs=[agents_checkbox, agent_count_display])
    
    # 應用程式啟動時載入辯論Agent列表
    def load_agents_with_status():
        """載入Agent列表並更新載入狀態"""
        try:
            logger.info("=== 執行應用程式啟動時Agent列表載入 ===")
            agents = get_debate_agents_for_selection()
            logger.info(f"初始載入取得的Agent數量: {len(agents)}")
            # 確保返回有效的Agent列表
            if not agents or len(agents) == 0:
                return ["⚠️ 目前沒有可用的Agent，請先建立Agent"], "⚠️ 沒有可用Agent"
            
            # 更新載入狀態為完成，並且顯式設定預設選中為空列表
            # 這樣使用者需要手動選擇參與辯論的Agent，而不是預設全部選中
            from gradio import update
            return update(choices=agents, value=[]), "✅ Agent列表載入完成"
        except Exception as e:
            logger.error(f"初始載入Agent列表失敗: {str(e)}")
            return [], f"❌ 載入失敗: {str(e)}"
    
    # 使用單獨的載入函式確保UI元件正確初始化
    demo.load(
        fn=load_agents_with_status, 
        outputs=[debate_agents_checkbox, loading_status],
        show_progress=True
    )
    
    # 刷新辯論Agent列表 - 確保更新所有相關元件
    refresh_debate_agents_btn.click(
        fn=refresh_debate_agents,
        inputs=[debate_agents_checkbox],  # 傳遞目前已選項
        outputs=[debate_agents_checkbox, selected_agents_info, agents_count_display_debate]
    )
    
    # 為辯論Agent選擇元件新增change事件處理器，即時回應使用者選擇
    def on_debate_agents_change(selected_agents):
        global selected_debate_agents
        import logging
        logger = logging.getLogger(__name__)
        # 嘗試取得目前choices
        try:
            from gradio.components import CheckboxGroup
            # Gradio 3.x/4.x不支援直接取得choices，需靠外層邏輯傳遞
            current_choices = None  # 若能取得請補充
        except Exception:
            current_choices = None
        logger.info(f"[DEBUG] on_debate_agents_change: 輸入selected_agents={selected_agents}, 全域selected_debate_agents-舊值={selected_debate_agents}, 目前choices={current_choices}")
        selected_debate_agents = selected_agents
        logger.info(f"[DEBUG] on_debate_agents_change: 全域selected_debate_agents-新值={selected_debate_agents}")
        if not selected_agents:
            return "💡 請選擇參與辯論的Agent"
        # 顯示更詳細的選擇資訊
        return f"✅ 已選擇 {len(selected_agents)} 個Agent\n" + ", ".join([a.split(' (')[0] for a in selected_agents])
    
    debate_agents_checkbox.change(
        fn=on_debate_agents_change,
        inputs=debate_agents_checkbox,
        outputs=selected_agents_info
    )

    # 確認選擇的辯論Agent
    confirm_debate_agents_btn.click(
        fn=confirm_selected_agents,
        inputs=debate_agents_checkbox,
        outputs=selected_agents_info
    )

    # 儲存Agent（建立或更新）
    def save_agent_and_clear_form(agent_id, name, role, system_prompt, personality_traits, expertise_areas):
        # 先儲存Agent
        save_result, agents_checkbox_update, button_update, count_update = save_agent(
            agent_id, name, role, system_prompt, personality_traits, expertise_areas
        )
        
        # 然後清空表單
        clear_result = clear_agent_form()
        
        # 返回所有更新的元件
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

    # 刪除選定Agent
    delete_agents_btn.click(
        fn=delete_selected_agents,
        inputs=[agents_checkbox],
        outputs=[create_agent_result, agents_checkbox, delete_agents_btn, agent_count_display]
    )

    # 編輯選中Agent
    def edit_selected_agent_action(selected_agents):
        if not selected_agents:
            return "", "", "", "", "", "", "❌ 請先選擇要編輯的Agent", gr.update(interactive=True)
        if len(selected_agents) > 1:
            return "", "", "", "", "", "", "❌ 一次只能編輯一個Agent", gr.update(interactive=True)
        
        agent_str = selected_agents[0]
        if " - ID: " in agent_str:
            agent_id = agent_str.split(" - ID: ")[-1]
            return load_agent_to_form(agent_id)
        else:
            return "", "", "", "", "", "", "❌ 無法解析Agent ID", gr.update(interactive=True)

    edit_agent_btn.click(
        fn=edit_selected_agent_action,
        inputs=[agents_checkbox],
        outputs=[
            agent_id_hidden, agent_name_input, agent_role_dropdown,
            agent_prompt_input, agent_traits_input, agent_expertise_input,
            create_agent_result, delete_agents_btn
        ]
    )

    # 啟動辯論
    def start_debate_wrapper(topic, rounds):
        global selected_debate_agents
        
        if not selected_debate_agents:
            return "❌ 請先選擇並確認參與辯論的Agent", start_debate_btn
        
        result = start_debate_async(topic, rounds, selected_debate_agents)
        # 返回結果和按鈕狀態（保持不變）
        return result, start_debate_btn
        
    start_debate_btn.click(
        fn=start_debate_wrapper,
        inputs=[topic_input, rounds_input],
        outputs=[debate_status, start_debate_btn]
    )

    # 當「辯論設定」分頁被選中時，自動重新整理 Agent 列表
    debate_setup_tab.select(
        fn=refresh_debate_agents,
        inputs=[debate_agents_checkbox],
        outputs=[debate_agents_checkbox, selected_agents_info, agents_count_display_debate]
    )

if __name__ == "__main__":
    # 啓動時檢查服務狀態 - 直接API呼叫
    print("正在檢查API服務狀態...")
    try:
        health_response = make_api_request('GET', f"{base_url}/health")
        if health_response.status_code == 200:
            health_data = safe_json_parse(health_response)
            if health_data.get("status") == "healthy":
                print("✅ API服務執行正常")
            else:
                print("⚠️ 警告：API服務狀態例外")
        else:
            print("⚠️ 警告：API服務不可用，請確保AgentScope API服務已執行")
    except Exception as e:
        print(f"⚠️ 警告：無法連線到API服務 ({e})，請確保AgentScope API服務已執行")

    # 從環境變數讀取Gradio設定，如果未設定則使用預設值
    gradio_server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    gradio_server_port = os.getenv("GRADIO_SERVER_PORT", None)
    gradio_share = os.getenv("GRADIO_SHARE", "False").lower() == "true"
    gradio_debug = os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"

    # 啓動Gradio應用程式，使用環境變數設定
    demo.launch(
        server_name=gradio_server_name,
        server_port=int(gradio_server_port) if gradio_server_port else None,
        share=gradio_share,
        debug=gradio_debug
    )