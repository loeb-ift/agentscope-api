import json
import logging
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

# 導入模型和配置
from agentscope.models import ModelWrapperBase
from app.core.config import settings
from app.utils.model_factory import create_model

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """初始化LLM服務，設置模型緩存"""
        # 用於存儲已創建的模型實例的緩存
        self.model_cache = {}
        # 支持的LLM提供商列表
        self.supported_providers = ["ollama", "openai", "zhipu", "gpt4all", "huggingface"]
    
    async def get_model(self, model_config: Dict[str, Any]) -> ModelWrapperBase:
        """
        獲取或創建模型實例
        
        Args:
            model_config: 模型配置字典，包含模型名稱、提供商等信息
        
        Returns:
            ModelWrapperBase: 模型包裝器實例
        
        Raises:
            ValueError: 如果模型配置無效
            Exception: 如果模型創建失敗
        """
        # 驗證模型配置
        if not self.validate_model_config(model_config):
            raise ValueError(f"無效的模型配置: {model_config}")
        
        # 為模型配置生成唯一的緩存鍵
        cache_key = self._generate_cache_key(model_config)
        
        # 檢查緩存中是否已有模型實例
        if cache_key in self.model_cache:
            logger.debug(f"從緩存中獲取模型: {cache_key}")
            return self.model_cache[cache_key]
        
        # 如果緩存中沒有用於此配置的模型，創建新的模型實例
        try:
            logger.debug(f"創建新模型實例: {model_config}")
            model = await self._create_model_instance(model_config)
            
            # 將新模型實例添加到緩存
            self.model_cache[cache_key] = model
            logger.debug(f"模型已添加到緩存: {cache_key}")
            
            return model
        except Exception as e:
            logger.error(f"創建模型失敗: {str(e)}")
            raise
    
    async def _create_model_instance(self, model_config: Dict[str, Any]) -> ModelWrapperBase:
        """
        創建模型實例
        
        Args:
            model_config: 模型配置字典
        
        Returns:
            ModelWrapperBase: 模型包裝器實例
        """
        # 提取模型名稱和提供商
        model_name = model_config.get("model_name")
        provider = model_config.get("provider", "ollama")
        
        # 處理Ollama模型特定的配置
        if provider == "ollama":
            # 使用配置中的Ollama API基礎URL，如果沒有提供，使用設置中的默認值
            ollama_api_base = model_config.get("api_base", settings.OLLAMA_API_BASE)
            
            # 確保ollama_api_base以"/"結尾，以避免API調用錯誤
            if ollama_api_base and not ollama_api_base.endswith("/"):
                ollama_api_base = f"{ollama_api_base}/"
            
            # 更新模型配置中的API基礎URL
            model_config["api_base"] = ollama_api_base
        
        # 調用模型工廠方法創建模型實例
        model = await create_model(model_config)
        
        return model
    
    async def generate_text(self, model_config: Dict[str, Any], prompt: str, 
                           system_prompt: Optional[str] = None) -> str:
        """
        生成文本回應
        
        Args:
            model_config: 模型配置字典
            prompt: 用戶提示
            system_prompt: 系統提示（可選）
        
        Returns:
            str: 模型生成的文本回應
        """
        try:
            # 獲取模型實例
            model = await self.get_model(model_config)
            
            # 構建消息列表
            messages = []
            
            # 如果提供了系統提示，將其添加到消息列表的開頭
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # 添加用戶提示
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # 調用模型生成回應
            response = await model.generate(messages)
            
            # 處理不同格式的回應
            if isinstance(response, str):
                return response
            elif hasattr(response, "content"):
                return response.content
            elif isinstance(response, dict) and "content" in response:
                return response["content"]
            else:
                # 將任何其他類型的回應轉換為字符串
                return str(response)
        except Exception as e:
            logger.error(f"生成文本回應時發生錯誤: {str(e)}")
            raise
    
    async def generate_structured_output(self, model_config: Dict[str, Any], prompt: str, 
                                       system_prompt: Optional[str] = None, 
                                       expected_structure: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成結構化輸出
        
        Args:
            model_config: 模型配置字典
            prompt: 用戶提示
            system_prompt: 系統提示（可選）
            expected_structure: 期望的輸出結構（可選）
        
        Returns:
            Dict[str, Any]: 模型生成的結構化輸出
        """
        try:
            # 增強提示以確保結構化輸出
            enhanced_prompt = self._enhance_prompt_for_structured_output(prompt, expected_structure)
            
            # 生成文本回應
            text_response = await self.generate_text(model_config, enhanced_prompt, system_prompt)
            
            # 嘗試解析JSON格式的回應
            try:
                structured_response = json.loads(text_response)
                # 驗證結構化回應是否符合預期結構
                if expected_structure and not self._validate_structure(structured_response, expected_structure):
                    logger.warning("生成的結構化輸出不符合預期結構")
                return structured_response
            except json.JSONDecodeError:
                # 如果回應不是有效的JSON，記錄警告並返回包含原始文本的字典
                logger.warning(f"模型返回的不是有效的JSON: {text_response}")
                return {
                    "raw_text": text_response,
                    "error": "無法解析為JSON格式的回應"
                }
        except Exception as e:
            logger.error(f"生成結構化輸出時發生錯誤: {str(e)}")
            # 創建一個包含錯誤信息的回應，以確保API調用者能獲得有用的反饋
            error_response = {
                "error": True,
                "error_message": str(e),
                "timestamp": datetime.now().isoformat(),
                "model_config": model_config  # 不包含敏感信息
            }
            return error_response
    
    def _enhance_prompt_for_structured_output(self, prompt: str, 
                                             expected_structure: Optional[Dict[str, Any]]) -> str:
        """
        增強提示以確保結構化輸出
        
        Args:
            prompt: 原始提示
            expected_structure: 期望的輸出結構
        
        Returns:
            str: 增強後的提示
        """
        # 基本的JSON格式要求
        json_format_prompt = "\n\n請以有效的JSON格式返回你的回應，不要包含任何JSON格式以外的文本。"
        
        # 如果提供了期望的輸出結構，添加到提示中
        if expected_structure:
            structure_prompt = f"\n\n期望的輸出結構如下：\n{json.dumps(expected_structure, ensure_ascii=False, indent=2)}"
            return f"{prompt}{structure_prompt}{json_format_prompt}"
        
        return f"{prompt}{json_format_prompt}"
    
    def _validate_structure(self, response: Dict[str, Any], expected_structure: Dict[str, Any]) -> bool:
        """
        驗證回應是否符合預期結構
        
        Args:
            response: 模型生成的回應
            expected_structure: 期望的輸出結構
        
        Returns:
            bool: 如果回應符合預期結構，返回True，否則返回False
        """
        # 簡單的結構驗證：檢查所有必需的鍵是否存在
        for key, value_type in expected_structure.items():
            if key not in response:
                logger.warning(f"缺少必需的字段: {key}")
                return False
            
            # 如果值類型是字典，遞歸驗證嵌套結構
            if isinstance(value_type, dict) and isinstance(response[key], dict):
                if not self._validate_structure(response[key], value_type):
                    return False
            # 檢查值類型是否匹配（如果提供了類型信息）
            elif isinstance(value_type, type) and not isinstance(response[key], value_type):
                logger.warning(f"字段 {key} 的類型不正確。期望: {value_type.__name__}, 實際: {type(response[key]).__name__}")
                return False
        
        return True
    
    def validate_model_config(self, model_config: Dict[str, Any]) -> bool:
        """
        驗證模型配置
        
        Args:
            model_config: 模型配置字典
        
        Returns:
            bool: 如果配置有效，返回True，否則返回False
        """
        # 檢查必需的字段
        if not model_config or "model_name" not in model_config:
            logger.error("模型配置缺少必需的'model_name'字段")
            return False
        
        # 檢查提供商（如果提供）
        provider = model_config.get("provider", "ollama")
        if provider not in self.supported_providers:
            logger.error(f"不支持的模型提供商: {provider}。支持的提供商: {self.supported_providers}")
            return False
        
        # 檢查Ollama模型的特定要求
        if provider == "ollama":
            # Ollama模型需要API基礎URL
            if "api_base" not in model_config:
                # 使用設置中的默認值
                model_config["api_base"] = settings.OLLAMA_API_BASE
        
        return True
    
    def _generate_cache_key(self, model_config: Dict[str, Any]) -> str:
        """
        為模型配置生成唯一的緩存鍵
        
        Args:
            model_config: 模型配置字典
        
        Returns:
            str: 緩存鍵
        """
        # 創建模型配置的副本，以避免修改原始配置
        config_copy = model_config.copy()
        
        # 排除可能影響緩存鍵的瞬態字段
        transient_fields = ["temperature", "max_tokens", "top_p", "seed", "stream"]
        for field in transient_fields:
            if field in config_copy:
                del config_copy[field]
        
        # 將配置字典轉換為排序後的JSON字符串，以確保相同的配置生成相同的緩存鍵
        return json.dumps(config_copy, sort_keys=True, ensure_ascii=False)
    
    def clear_model_cache(self, model_config: Optional[Dict[str, Any]] = None):
        """
        清除模型緩存
        
        Args:
            model_config: （可選）特定的模型配置。如果提供，只清除對應的模型實例。
                         如果未提供，清除所有模型緩存。
        """
        if model_config:
            # 生成特定配置的緩存鍵
            cache_key = self._generate_cache_key(model_config)
            
            # 檢查並清除特定的模型實例
            if cache_key in self.model_cache:
                del self.model_cache[cache_key]
                logger.debug(f"已清除特定模型的緩存: {cache_key}")
            else:
                logger.debug(f"緩存中未找到對應的模型實例: {cache_key}")
        else:
            # 清除所有模型緩存
            self.model_cache.clear()
            logger.debug("已清除所有模型緩存")