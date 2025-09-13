#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
金融分析師多智能體辯論測試
創建四個專業分析師：風險管控、基本面、市場情緒、技術分析
"""

import os
import sys
import asyncio
import requests
import json
from datetime import datetime

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# API 基礎配置
API_BASE = "http://127.0.0.1:8000/api"

# 四個金融分析師的配置
FINANCIAL_ANALYSTS = {
    "risk_manager": {
        "name": "風險管控專家 - 李安全",
        "role": "risk_analyst",
        "system_prompt": """你是一位資深的風險管控專家，專注於投資風險評估和管理。你的職責是：

1. **風險識別**：識別各種投資風險（市場風險、信用風險、流動性風險、操作風險等）
2. **風險量化**：使用VaR、壓力測試等工具量化風險
3. **風險控制**：提出風險緩解和控制措施
4. **合規監管**：確保投資決策符合監管要求

你的分析風格：
- 保守謹慎，優先考慮資本保護
- 數據驅動，依賴量化指標
- 關注下行風險和極端情況
- 強調風險調整後收益

在辯論中，你會從風險角度質疑投資建議，提出潛在風險點，並建議風險管理措施。""",
        "personality_traits": ["謹慎", "分析性", "保守", "責任感強"],
        "expertise_areas": ["風險管理", "VaR模型", "壓力測試", "監管合規", "資本配置"]
    },
    
    "fundamental_analyst": {
        "name": "基本面分析師 - 王價值",
        "role": "fundamental_analyst", 
        "system_prompt": """你是一位專業的基本面分析師，專注於公司和經濟基本面分析。你的專長包括：

1. **財務分析**：深入分析財報數據、盈利能力、財務健康度
2. **行業分析**：研究行業趨勢、競爭格局、增長前景
3. **宏觀經濟**：分析經濟指標對投資標的的影響
4. **估值模型**：使用DCF、P/E、PEG等方法進行估值

你的分析特點：
- 長期投資視角，關注內在價值
- 重視公司基本面和商業模式
- 基於財務數據做出理性判斷
- 關注可持續的競爭優勢

在辯論中，你會從公司價值和長期前景角度分析投資機會，強調基本面因素的重要性。""",
        "personality_traits": ["理性", "深度思考", "長期導向", "數據驅動"],
        "expertise_areas": ["財務分析", "估值模型", "行業研究", "宏觀經濟", "公司治理"]
    },
    
    "sentiment_analyst": {
        "name": "市場情緒分析師 - 張心理",
        "role": "sentiment_analyst",
        "system_prompt": """你是一位市場情緒和行為金融專家，專注於分析市場心理和投資者行為。你的專業領域：

1. **情緒指標**：分析VIX、Put/Call比率、投資者調查等情緒指標
2. **行為偏差**：識別市場中的認知偏差和非理性行為
3. **資金流向**：追蹤機構和散戶資金流動
4. **市場週期**：理解市場情緒週期和轉折點

你的分析視角：
- 關注市場心理和情緒變化
- 識別過度樂觀或悲觀的市場狀態
- 利用逆向思維發現機會
- 重視市場參與者的行為模式

在辯論中，你會從市場情緒角度分析投資時機，指出可能的情緒驅動因素和市場偏差。""",
        "personality_traits": ["敏感", "直覺性", "逆向思維", "心理洞察"],
        "expertise_areas": ["行為金融", "市場情緒", "投資者心理", "資金流分析", "市場週期"]
    },
    
    "technical_analyst": {
        "name": "技術分析師 - 陳圖表",
        "role": "technical_analyst",
        "system_prompt": """你是一位專業的技術分析師，專精於圖表分析和量化交易策略。你的核心技能：

1. **圖表分析**：熟練運用各種技術指標和圖表模式
2. **趨勢分析**：識別價格趨勢和支撐阻力位
3. **時機把握**：確定最佳的進出場時點
4. **量化策略**：開發和優化交易算法

你的分析方法：
- 純粹基於價格和成交量數據
- 相信市場價格反映所有信息
- 關注短中期交易機會
- 重視風險回報比和勝率

在辯論中，你會從技術面角度分析價格走勢，提供具體的進出場建議和風險控制策略。""",
        "personality_traits": ["精確", "快速反應", "紀律性", "數據導向"],
        "expertise_areas": ["技術指標", "圖表分析", "量化交易", "風險管理", "市場微結構"]
    }
}

def create_agent(agent_config):
    """創建單個智能體"""
    llm_config = {
        "model_name": "gpt-oss:20b",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    payload = {
        "name": agent_config["name"],
        "role": agent_config["role"],
        "system_prompt": agent_config["system_prompt"],
        "llm_config": llm_config,
        "personality_traits": agent_config["personality_traits"],
        "expertise_areas": agent_config["expertise_areas"]
    }
    
    try:
        response = requests.post(f"{API_BASE}/agents/create", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功創建智能體: {agent_config['name']}")
            print(f"   ID: {result['agent_id']}")
            return result
        else:
            print(f"❌ 創建智能體失敗: {agent_config['name']}")
            print(f"   錯誤: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 創建智能體時發生錯誤: {e}")
        return None

def start_financial_debate(agent_ids, topic):
    """啟動金融分析師辯論"""
    payload = {
        "topic": topic,
        "agent_ids": agent_ids,
        "rounds": 3,
        "max_duration_minutes": 15
    }
    
    try:
        response = requests.post(f"{API_BASE}/debate/start", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 辯論已啟動")
            print(f"   會話ID: {result['session_id']}")
            return result
        else:
            print(f"❌ 啟動辯論失敗")
            print(f"   錯誤: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 啟動辯論時發生錯誤: {e}")
        return None

def check_debate_status(session_id):
    """檢查辯論狀態"""
    try:
        response = requests.get(f"{API_BASE}/debate/{session_id}/status")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 獲取辯論狀態失敗: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 檢查辯論狀態時發生錯誤: {e}")
        return None

def get_debate_result(session_id):
    """獲取辯論結果"""
    try:
        response = requests.get(f"{API_BASE}/debate/{session_id}/result")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 獲取辯論結果失敗: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 獲取辯論結果時發生錯誤: {e}")
        return None

async def monitor_debate_progress(session_id):
    """監控辯論進度"""
    print("\n🔍 開始監控辯論進度...")
    
    while True:
        status = check_debate_status(session_id)
        if not status:
            break
            
        print(f"📊 辯論狀態: {status.get('status', 'unknown')}")
        print(f"📈 進度: {status.get('progress', 0):.1f}%")
        
        if status.get('status') == 'completed':
            print("🎉 辯論已完成！")
            break
        elif status.get('status') == 'failed':
            print("❌ 辯論失敗！")
            break
            
        await asyncio.sleep(5)  # 每5秒檢查一次

def main():
    """主函數"""
    print("🏦 金融分析師多智能體辯論測試")
    print("=" * 60)
    
    # 1. 創建四個金融分析師
    print("\n📝 第一步：創建金融分析師智能體")
    print("-" * 40)
    
    created_agents = []
    for key, config in FINANCIAL_ANALYSTS.items():
        agent = create_agent(config)
        if agent:
            created_agents.append(agent)
        
    if len(created_agents) != 4:
        print(f"❌ 只成功創建了 {len(created_agents)}/4 個智能體，測試終止")
        return
    
    print(f"\n✅ 成功創建 {len(created_agents)} 個金融分析師智能體")
    
    # 2. 啟動辯論
    print("\n🎯 第二步：啟動金融分析辯論")
    print("-" * 40)
    
    # 辯論主題
    debate_topic = """
    投資主題：台積電(TSM)股票投資分析
    
    背景：台積電作為全球最大的晶圓代工廠，在AI晶片需求激增的背景下，
    股價在過去一年大幅上漲。目前面臨地緣政治風險、競爭加劇、估值偏高等挑戰。
    
    請各位分析師從各自專業角度分析：
    1. 台積電當前的投資價值如何？
    2. 主要的機會和風險是什麼？
    3. 建議的投資策略是什麼？
    """
    
    agent_ids = [agent["agent_id"] for agent in created_agents]
    debate_result = start_financial_debate(agent_ids, debate_topic)
    
    if not debate_result:
        print("❌ 啟動辯論失敗，測試終止")
        return
    
    session_id = debate_result["session_id"]
    
    # 3. 監控辯論進度
    print("\n⏱️ 第三步：監控辯論進度")
    print("-" * 40)
    
    try:
        asyncio.run(monitor_debate_progress(session_id))
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷監控")
    
    # 4. 獲取辯論結果
    print("\n📋 第四步：獲取辯論結果")
    print("-" * 40)
    
    result = get_debate_result(session_id)
    if result:
        print("🎯 辯論結論:")
        print(f"   {result.get('conclusion', {}).get('final_conclusion', '無結論')}")
        print(f"\n📊 可信度分數: {result.get('conclusion', {}).get('confidence_score', 0):.2f}")
        
        # 顯示各分析師的關鍵論點
        key_arguments = result.get('conclusion', {}).get('key_arguments', {})
        if key_arguments:
            print("\n💡 各分析師關鍵論點:")
            for analyst, arguments in key_arguments.items():
                print(f"   {analyst}: {arguments}")
    
    print("\n🏁 測試完成！")

if __name__ == "__main__":
    main()