import agentscope
from agentscope.model import ChatModelBase, OllamaChatModel, OpenAIChatModel, AnthropicChatModel, DashScopeChatModel
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException
import asyncio
from app.core.config import settings

class LLMService:
    def __init__(self):
        # 快取已初始化的模型實例
        self.models_cache = {}
        # 支持的模型提供商
        self.supported_providers = ["openai", "anthropic", "dashscope", "gemini", "ollama"]
    
    def get_model(self, model_config: Dict[str, Any]) -> ChatModelBase:
        """取得或建立模型實例"""
        # 從配置中提取模型名稱和提供商
        model_name = model_config.get("model_name")
        if not model_name:
            raise HTTPException(
                status_code=400,
                detail="模型配置中缺少model_name字段"
            )
        
        # 创建缓存键
        cache_key = f"{model_name}_{hash(str(model_config))}"
        
        # 檢查快取中是否已有該模型實例
        if cache_key in self.models_cache:
            return self.models_cache[cache_key]
        
        # 建立新的模型實例
        model = self._create_model_instance(model_config)

        # 快取模型實例
        self.models_cache[cache_key] = model
        
        return model
    
    def _create_model_instance(self, model_config: Dict[str, Any]) -> ChatModelBase:
        """建立模型實例"""
        # 從配置中提取模型名稱
        model_name = model_config.get("model_name", settings.DEFAULT_MODEL_NAME)
        
        # 创建配置副本，移除不需要传递给AgentScope的字段
        config_copy = model_config.copy()
        
        # 根據模型類型直接建立對應的模型實例
        try:
            # 如果是Ollama模型
            if model_name.startswith("gpt-oss") or "ollama" in model_name.lower():
                # 准备Ollama模型配置
                ollama_config = {
                    "model_name": model_name,
                    "host": config_copy.get("api_base", settings.OLLAMA_API_BASE),
                    "stream": config_copy.get("stream", True),
                    "options": config_copy.get("options", {})
                }
                model = OllamaChatModel(**ollama_config)
            # 这里可以添加其他模型类型的处理
            else:
                # 默认使用Ollama模型，因为这是我们配置的主要模型
                model = OllamaChatModel(
                    model_name=model_name,
                    host=settings.OLLAMA_API_BASE
                )
            
            return model
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"建立模型實例失敗: {str(e)}"
            )
    
    async def generate_text(self, model_config: Dict[str, Any], prompt: str, 
                          system_prompt: Optional[str] = None) -> str:
        """生成文本响应"""
        model = self.get_model(model_config)
        
        try:
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # 生成响应 - 直接调用OllamaChatModel的异步__call__方法
            response = await model(messages)
            
            # 提取文本内容
            if isinstance(response, str):
                return response
            elif hasattr(response, "text"):
                return response.text
            elif isinstance(response, dict) and "content" in response:
                return response["content"]
            else:
                return str(response)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"文本生成失败: {str(e)}"
            )
    
    async def generate_structured_output(self, model_config: Dict[str, Any], prompt: str, 
                                       response_format: Any, 
                                       system_prompt: Optional[str] = None) -> Any:
        """產生結構化輸出"""
        # 注意：實際實現時需要根據不同模型提供商的結構化輸出能力進行適配
        # 這裡提供一個基礎實現
        model = self.get_model(model_config)
        
        try:
            # 构建消息，包含结构化输出要求
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 在提示中添加结构化输出的要求
            structured_prompt = f"{prompt}\n\n請以JSON格式返回結果，確保格式正確。所有文本內容必須使用繁體中文。"
            messages.append({"role": "user", "content": structured_prompt})
            
            # 生成响应 - 直接调用OllamaChatModel的异步__call__方法
            response = await model(messages)
            
            # 处理响应
            import json
            
            # 更健壯的回應處理邏輯，專門處理結構化輸出
            text_content = ""
            
            # 检查响应类型并适当处理
            if response is None:
                text_content = "空响应"
            elif isinstance(response, str):
                text_content = response
            elif isinstance(response, dict):
                # 尝试从字典中获取内容
                if "content" in response:
                    content = response["content"]
                    # 确保content是字符串
                    text_content = str(content) if not isinstance(content, str) else content
                elif "text" in response:
                    text_content = str(response["text"]) if not isinstance(response["text"], str) else response["text"]
                else:
                    # 如果是嵌套字典，尝试提取所有字符串值
                    text_parts = []
                    def extract_text(obj):
                        if isinstance(obj, str):
                            text_parts.append(obj)
                        elif isinstance(obj, dict):
                            for value in obj.values():
                                extract_text(value)
                        elif isinstance(obj, list):
                            for item in obj:
                                extract_text(item)
                        else:
                            text_parts.append(str(obj))
                    extract_text(response)
                    text_content = " ".join(text_parts)
            elif isinstance(response, list):
                # 处理列表类型响应
                text_parts = []
                for item in response:
                    if isinstance(item, dict):
                        # 检查是否包含text字段（这是常见的结构化输出格式）
                        if "text" in item:
                            text_parts.append(str(item["text"]))
                        # 检查是否包含content字段
                        elif "content" in item:
                            text_parts.append(str(item["content"]))
                        else:
                            text_parts.append(str(item))
                    else:
                        text_parts.append(str(item))
                text_content = " ".join(text_parts)
            else:
                # 对于其他类型，先尝试转换为字符串
                try:
                    text_content = str(response)
                except:
                    text_content = "[错误] 无法将响应转换为字符串"
            
            # 特殊處理：移除Markdown程式碼區塊格式（如果存在）
            import re
            # 匹配JSON程式碼區塊
            code_block_match = re.search(r'```\s*json\s*(.*?)\s*```', text_content, re.DOTALL)
            if code_block_match:
                text_content = code_block_match.group(1)
            else:
                # 匹配任意程式碼區塊
                code_block_match = re.search(r'```\s*(.*?)\s*```', text_content, re.DOTALL)
                if code_block_match:
                    text_content = code_block_match.group(1)
            
            # 清理和预处理文本内容
            text_content = text_content.strip()
            
            # 尝试解析JSON响应
            try:
                return json.loads(text_content)
            except json.JSONDecodeError as e:
                # 尝试修复常见的JSON格式问题
                try:
                    # 移除可能的BOM标记和所有空白字符
                    text_content = text_content.lstrip('\ufeff').strip()
                    
                    # 移除开头的换行符和空白
                    while text_content.startswith(('\n', '\r', ' ', '\t')):
                        text_content = text_content.lstrip('\n\r \t')
                    
                    # 尝试修复换行符问题（但保留JSON结构）
                    # 只替换不在引号内的换行符
                    import re
                    # 先尝试直接解析
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    try:
                        # 尝试修复引号问题
                        text_content = text_content.replace('"', '"').replace('"', '"')
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        try:
                            # 尝试修复换行符问题（更保守的方法）
                            # 只替换明显的换行符，但保持JSON结构
                            text_content = re.sub(r'\n\s*', ' ', text_content)
                            text_content = re.sub(r'\r\s*', ' ', text_content)
                            return json.loads(text_content)
                        except json.JSONDecodeError:
                            # 如果仍然失败，返回原始文本内容作为结论
                            print(f"JSON解析错误: {e}, 原始文本: {text_content[:200]}...")
                            return {"final_conclusion": text_content, "error": f"无法解析为JSON: {str(e)}"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"结构化输出生成失败: {str(e)}"
            )
    
    def validate_model_config(self, model_config: Dict[str, Any]) -> bool:
        """验证模型配置"""
        # 检查必要字段
        if "model_name" not in model_config:
            return False
        
        # 可以根据不同模型提供商添加更多验证逻辑
        return True
    
    def clear_model_cache(self, model_name: Optional[str] = None):
        """清除模型缓存"""
        if model_name:
            # 清除特定模型的缓存
            keys_to_remove = [key for key in self.models_cache if model_name in key]
            for key in keys_to_remove:
                del self.models_cache[key]
        else:
            # 清除所有缓存
            self.models_cache.clear()