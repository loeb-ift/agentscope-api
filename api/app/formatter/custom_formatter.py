# -*- coding: utf-8 -*-
"""
Custom Ollama Formatter to address language drift issues.
"""
from typing import Any, List
from agentscope.formatter import OllamaMultiAgentFormatter
from agentscope.message import Msg

# 繼承自 OllamaMultiAgentFormatter
class CustomOllamaMultiAgentFormatter(OllamaMultiAgentFormatter):
    """
    A custom Ollama formatter for multi-agent conversations that enforces the use
    of Traditional Chinese in the model's thinking process.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initializes the custom formatter, overriding the default English prompt
        with a Traditional Chinese version.
        """
        # 設置繁體中文的對話歷史提示
        kwargs['conversation_history_prompt'] = (
            "# 對話歷史\n"
            "在 <history></history> 標籤之間的內容包含了您的對話歷史。\n"
        )
        super().__init__(*args, **kwargs)

    def format_prompt(self, msgs: List[Msg]) -> str:
        """
        Override the format_prompt to inject strong Traditional Chinese instructions,
        ensuring the ReAct 'thinking' step is in Traditional Chinese.

        This method will be called by the ReActAgent to construct the final prompt.
        """
        # 調用父類的基本 prompt 格式化邏輯
        prompt = super().format_prompt(msgs)

        # 注入強化的繁體中文指令
        # 確保思考過程和工具使用都使用繁體中文
        react_instruction = (
            "你是一個大型語言模型。你有多種工具可以使用。\n"
            "針對用戶的最新回復，你的任務是選擇一個工具來回應。你必須嚴格遵守以下格式：\n"
            "```thought\n"
            "你必須在這裡用繁體中文一步一步地思考。分析用戶的請求，並說明你接下來要採取什麼行動以及使用哪個工具。\n"
            "```\n"
            "```tool\n"
            "你選擇的工具，必須是 [{tool_names}] 其中之一。\n"
            "```\n"
            "```parameters\n"
            "工具的參數，以 JSON 格式表示。\n"
            "```\n"
        )

        # 將強化指令與原始 prompt 結合
        # 這裡我們將強化指令放在最前面，以確保模型優先遵循
        return react_instruction + "\n" + prompt
