# AgentScope API 服務

這是 AgentScope 的 API 服務組件，提供多智能體辯論功能的 RESTful API 接口。本服務允許您通過簡單的 API 調用，創建多個智能體並讓它們圍繞特定主題進行辯論，最終生成結構化的辯論結果和總結。

## 快速部署指南

以下是快速部署和使用 AgentScope API 服務的步驟指南：

> **注意**: Windows 環境下可能遇到 pydantic 版本兼容性問題，請參見下方的「故障排除」部分。

### 1. 安裝環境依賴

```bash
# 進入项目目錄
cd /Users/loeb/LAB/agentscope/agentscope-api

# 安裝 Python 依賴
pip install -r requirements.txt

# 確保 Ollama 服務已安裝並運行
# 下載安裝: https://ollama.com/download
# 啟動服務: ollama serve
```

### 2. 配置環境變量

```bash
# 複製環境變量配置示例
cp .env.example .env

# 編輯 .env 文件，配置必要信息
# 主要配置項:
# - OLLAMA_API_BASE: Ollama 服務地址（默認: http://localhost:11434）
# - DEFAULT_MODEL_NAME: 使用的模型名稱（例如: gpt-oss:20b）
# - HOST 和 PORT: API 服務器的主機和端口
```

### 3. 手動啟動 API 服務

```bash
# 啟動 API 服務器
python start_server.py

# 服務啟動後，您可以訪問以下地址:
# - API 基礎地址: http://localhost:8000/api
# - Swagger UI 文檔: http://localhost:8000/docs
# - ReDoc 文檔: http://localhost:8000/redoc
```

> **重要提示**：如果您打算使用配套的Web界面，**必须先启动API服务，然后再启动Web服务**。
> Web服务位于 `web/` 目录下，启动方法请参考 `web/README.md`。

### 4. 執行 Shell 腳本測試

```bash
# 在新的終端窗口中，確保 API 服務已啟動
cd /Users/loeb/LAB/agentscope/agentscope-api

# 運行金融分析師辯論 API 測試腳本
./financial_debate_api.sh

# 或使用測試模式
./financial_debate_api.sh --test
```

## 核心功能

- 創建和管理多種類型的智能體（Agent）
- 配置智能體用於特定辯論主題
- 啟動和管理多智能體辯論會話
- 獲取辯論狀態、結果和完整歷史記錄
- 支持在外部系統（如 n8n）中通過 API 調用實現辯論功能

## 目錄結構

```
agentscope-api/
├── app/               # 主應用代碼
│   ├── api/           # API 路由和端點
│   ├── core/          # 核心配置和功能
│   ├── models/        # 數據模型和架構定義
│   ├── services/      # 業務邏輯服務
│   └── main.py        # 應用入口
├── requirements.txt   # 項目依賴
├── start_server.py    # 服務器啟動腳本
├── .env.example       # 環境變量配置示例
├── financial_debate_api.sh  # 金融分析師辯論API調用腳本
├── backup/            # 備份文件（不再使用的輔助腳本）
├── log/               # 日誌文件
├── result/            # 辯論結果文件
└── tests/             # 測試代碼
```

## 系統架構分析

AgentScope API 採用了現代化的分布式系統架構設計，包含API服務器、消息隊列、數據庫和客戶端組件，各組件協同工作以實現高效的多智能體辯論功能。

### 系統整體架構

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   客戶端      │──────▶   API服務器   │──────▶  任務隊列     │
│ (如financial_ │      │   (FastAPI)   │      │   (Redis)     │
│ debate_api.sh)│◀─────┘               │◀─────┘               │
└───────────────┘                      │        ┌─────────────┐
                                       │        │ Celery工作器│
                                       ▼        │   (異步任務)│
                              ┌───────────────┐  │             │
                              │    數據庫     │  │             │
                              │  (PostgreSQL/ │  └─────────────┘
                              │   SQLite)     │         │
                              └───────────────┘         │
                                      │                 │
                                      │                 │
                                      ▼                 ▼
                              ┌───────────────┐  ┌───────────────┐
                              │   Ollama      │  │ 辯論結論生成  │
                              │   LLM服務     │  │  與通知任務   │
                              └───────────────┘  └───────────────┘
```

### API Server 核心組件

API Server 是系統的核心入口，基於 FastAPI 框架實現，負責處理所有客戶端請求並協調各個服務組件。

**主要功能**：
- 提供 RESTful API 接口，處理智能體創建、配置和辯論管理請求
- 路由請求到適當的服務處理邏輯
- 數據驗證和錯誤處理
- 認證和授權（當前版本簡化處理）
- 文檔自動生成（Swagger UI 和 ReDoc）

**核心模塊**：
- `app/api/`: 包含所有 API 端點定義
- `app/services/`: 實現業務邏輯，如智能體管理和辯論流程控制
- `app/models/`: 定義數據模型和請求/響應結構
- `app/core/`: 包含配置管理和核心功能

### Redis 在系統中的作用

Redis 作為系統的關鍵基礎設施，扮演了多個重要角色：

**主要功能**：
1. **消息代理**：作為 Celery 的任務隊列後端，負責任務分發
2. **結果存儲**：保存異步任務的執行結果
3. **緩存**：緩存頻繁訪問的數據以提高性能

**存儲的數據類型**：
- Celery 任務隊列數據（辯論任務、結論生成任務、通知任務）
- 任務執行狀態和結果信息
- 臨時緩存數據（如辯論進度狀態）

**Redis 必要性**：
儘管當前 API 實現中部分異步任務調用代碼被註釋，但系統架構設計仍依賴 Redis 支持。完整部署時，Redis 對於支持異步任務處理和系統可擴展性至關重要。

### Client 交互方式

Client 端通過 HTTP 請求與 API Server 交互，實現完整的辯論流程。

**主要客戶端示例**：
- `financial_debate_api.sh`: shell腳本客戶端，通過 curl 命令調用 API，包含增強的JSON解析功能和錯誤處理
- n8n 工作流節點：在 n8n 自動化平台中通過 HTTP 請求節點調用 API
- 自定義客戶端應用：根據 API 文檔實現特定功能的客戶端程序

**典型交互流程**：
1. 檢查 API 服務健康狀態
2. 獲取 API 配置信息
3. 創建和配置辯論智能體
4. 啟動辯論會話
5. 輪詢辯論狀態
6. 獲取辯論結果和歷史記錄

## 詳細部署指南

除了上述快速部署步驟外，AgentScope API 也提供了 Docker 環境部署方式，適合更複雜的生產環境需求。

### 使用Docker環境（適用生產部署）

使用Docker可以簡化環境配置，自動安裝所有必要的服務（包括Redis、PostgreSQL和Celery）。

1. **準備Docker環境**

確保您的系統已安裝以下組件：
- Docker
- Docker Compose

2. **運行Docker設置腳本**

```bash
# 運行Docker設置腳本
./docker_setup.sh
```

此腳本將：
- 檢查Docker環境
- 基於.env.example創建.env配置文件
- 構建並啟動所有Docker服務（API服務器、Redis、PostgreSQL、Celery工作器）
- 顯示服務狀態和測試指令

3. **Docker環境常用命令**

```bash
# 停止所有服務
docker-compose down

# 重啟服務
docker-compose restart

# 查看服務狀態
docker-compose ps

# 查看服務日誌
docker-compose logs -f

# 進入API容器
docker-compose exec agentscope-api /bin/bash
```

## 系統要求

- Python 3.10+ 
- Ollama 服務（用於LLM模型調用）
- 可選：PostgreSQL 數據庫（默認使用SQLite）
- Redis（用於緩存和任務隊列，推薦使用）

## 智能體辯論 API 調用流程詳解

本節詳細解析 `financial_debate_api.sh` 腳本中實現的完整辯論流程，這是理解如何通過 API 調用實現多智能體辯論的核心參考。

### 完整辯論流程概述

1. [檢查 API 服務健康狀態](#1-檢查-api-服務健康狀態)
2. [獲取 API 配置信息](#2-獲取-api-配置信息)
3. [創建辯論智能體](#3-創建辯論智能體)
4. [配置智能體用於特定辯論主題](#4-配置智能體用於特定辯論主題)
5. [啟動辯論會話](#5-啟動辯論會話)
6. [輪詢辯論狀態](#6-輪詢辯論狀態)
7. [獲取辯論結果](#7-獲取辯論結果)
8. [獲取辯論歷史記錄](#8-獲取辯論歷史記錄)

### 1. 檢查 API 服務健康狀態

```bash
health_response=$(curl -s "${base_url}/health")
health_status=$(echo "$health_response" | jq -r ".status")
```

**API 端點**: `GET /api/health`

**功能**: 檢查 API 服務是否正常運行

**返回**: 包含服務狀態、版本和環境信息的 JSON 對象

### 2. 獲取 API 配置信息

```bash
config_response=$(curl -s "${base_url}/config")
agent_roles=$(echo "$config_response" | jq -r ".agent_roles")
default_rounds=$(echo "$config_response" | jq -r ".default_debate_rounds")
```

**API 端點**: `GET /api/config`

**功能**: 獲取 API 服務的配置信息，包括支持的智能體角色和辯論設置

**返回**: 包含角色類型、辯論輪次等配置信息的 JSON 對象

### 3. 創建辯論智能體

```bash
macro_agent_response=$(curl -s -X POST "${base_url}/agents/create" -H "Content-Type: application/json" -d 
'{
  "name": "宏觀經濟分析師",
  "role": "analyst",
  "system_prompt": "你是一位資深的宏觀經濟分析師...",
  "llm_config": {
    "temperature": "0.7",
    "max_tokens": "1024"
  },
  "personality_traits": ["專業", "客觀", "深入"],
  "expertise_areas": ["宏觀經濟", "貨幣政策", "財政政策", "地緣政治"]
}')

macro_agent_id=$(echo "$macro_agent_response" | jq -r ".agent_id")
```

**API 端點**: `POST /api/agents/create`

**功能**: 創建新的智能體實例，設置其角色、系統提示、LLM 配置、個性特徵和專業領域

**參數**: 
- `name`: 智能體名稱
- `role`: 智能體角色類型
- `system_prompt`: 系統提示詞，定義智能體行為和專業背景
- `llm_config`: LLM 模型配置，如 temperature 和 max_tokens
- `personality_traits`: 智能體個性特徵數組
- `expertise_areas`: 智能體專業領域數組

**返回**: 包含創建的智能體 ID 的 JSON 對象

在腳本中，通常會創建多個不同角色的智能體以形成辯論團隊。

### 4. 配置智能體用於特定辯論主題

```bash
config_response=$(curl -s -X POST "${base_url}/agents/${agent_id}/configure" -H "Content-Type: application/json" -d "{
  \"debate_topic\": \"$debate_topic\",
  \"additional_instructions\": \"請基於你的專業領域和知識，對辯論主題發表專業觀點...\" 
}")
```

**API 端點**: `POST /api/agents/{agent_id}/configure`

**功能**: 為特定智能體配置辯論主題和附加指令

**參數**: 
- `debate_topic`: 辯論主題
- `additional_instructions`: 附加指令，指導智能體如何參與辯論

**返回**: 確認配置成功的 JSON 對象

### 5. 啟動辯論會話

```bash
agent_ids_json="["$(printf '"%s",' "${global_agent_ids[@]}")"]"
agent_ids_json=${agent_ids_json%,]}"]

start_response=$(curl -s -X POST "${base_url}/debate/start" -H "Content-Type: application/json" -d "{
  \"topic\": \"$debate_topic\",
  \"agent_ids\": $agent_ids_json,
  \"rounds\": $debate_rounds,
  \"max_duration_minutes\": 30
}")

session_id=$(echo "$start_response" | jq -r ".session_id")
```

**API 端點**: `POST /api/debate/start`

**功能**: 啟動新的多智能體辯論會話

**參數**: 
- `topic`: 辯論主題
- `agent_ids`: 參與辯論的智能體 ID 數組
- `rounds`: 辯論輪次
- `max_duration_minutes`: 最大持續時間（分鐘）

**返回**: 包含會話 ID 和初始狀態的 JSON 對象

### 6. 輪詢辯論狀態

```bash
while true; do
    status_response=$(curl -s "${base_url}/debate/${session_id}/status")
    current_status=$(echo "$status_response" | jq -r ".status")
    current_round=$(echo "$status_response" | jq -r ".current_round")
    total_rounds=$(echo "$status_response" | jq -r ".total_rounds")
    progress=$(echo "$status_response" | jq -r ".progress")
    
    if [[ "$current_status" == "completed" || "$current_status" == "failed" ]]; then
        break
    fi
    
    sleep $wait_interval
    elapsed_time=$((elapsed_time + wait_interval))
done
```

**API 端點**: `GET /api/debate/{session_id}/status`

**功能**: 查詢辯論會話的當前狀態

**返回**: 包含辯論狀態、當前輪次、總輪次和進度的 JSON 對象

### 7. 獲取辯論結果

```bash
result_response=$(curl -s "${base_url}/debate/${session_id}/result")

# 解析結果
al_final_conclusion=$(echo "$result_response" | jq -r ".final_conclusion")
confidence_score=$(echo "$result_response" | jq -r ".confidence_score")
consensus_points=$(echo "$result_response" | jq -r ".consensus_points[]")
divergent_views=$(echo "$result_response" | jq -r ".divergent_views[]")
```

**API 端點**: `GET /api/debate/{session_id}/result`

**功能**: 獲取辯論的最終結果和總結

**返回**: 包含最終結論、可信度分數、共識要點和分歧觀點的 JSON 對象

### 8. 獲取辯論歷史記錄

```bash
history_response=$(curl -s "${base_url}/debate/${session_id}/history")

total_messages=$(echo "$history_response" | jq -r ".history | length")
```

**API 端點**: `GET /api/debate/{session_id}/history`

**功能**: 獲取完整的辯論對話歷史記錄

**返回**: 包含所有辯論消息的 JSON 對象

## 在 n8n 中使用 AgentScope API

您可以在 n8n 工作流中通過 HTTP 請求節點調用 AgentScope API，實現多智能體辯論功能。以下是實現相同辯論流程的 n8n 工作流配置指南。

### n8n 工作流組件配置

#### 1. 服務健康檢查（HTTP 請求節點）

- **URL**: `http://localhost:8000/api/health`
- **方法**: GET
- **響應處理**: 檢查 `status` 字段是否為 `healthy`

#### 2. 獲取配置信息（HTTP 請求節點）

- **URL**: `http://localhost:8000/api/config`
- **方法**: GET
- **響應處理**: 解析 `agent_roles` 和 `default_debate_rounds` 字段

#### 3. 創建智能體（HTTP 請求節點 x4）

為每個智能體創建一個 HTTP 請求節點：

- **URL**: `http://localhost:8000/api/agents/create`
- **方法**: POST
- **內容類型**: JSON
- **請求體**: 包含智能體信息的 JSON 對象（參考腳本中的配置）
- **響應處理**: 提取並存儲 `agent_id` 字段

#### 4. 配置智能體（HTTP 請求節點 x4）

為每個智能體創建一個 HTTP 請求節點：

- **URL**: `http://localhost:8000/api/agents/{{$json.agent_id}}/configure`
- **方法**: POST
- **內容類型**: JSON
- **請求體**: `{"debate_topic": "{{$workflow.variables.debate_topic}}", "additional_instructions": "請基於你的專業領域和知識..."}`

#### 5. 啟動辯論（HTTP 請求節點）

- **URL**: `http://localhost:8000/api/debate/start`
- **方法**: POST
- **內容類型**: JSON
- **請求體**: `{"topic": "{{$workflow.variables.debate_topic}}", "agent_ids": ["{{$json.macro_agent_id}}", "{{$json.equity_agent_id}}", ...], "rounds": 3, "max_duration_minutes": 30}`
- **響應處理**: 提取並存儲 `session_id` 字段

#### 6. 輪詢辯論狀態（循環節點 + HTTP 請求節點）

- **循環節點**: 設置最大迭代次數和延遲時間
- **HTTP 請求節點**: 
  - **URL**: `http://localhost:8000/api/debate/{{$workflow.variables.session_id}}/status`
  - **方法**: GET
  - **條件退出**: 當 `status` 字段為 `completed` 或 `failed` 時退出循環

#### 7. 獲取辯論結果（HTTP 請求節點）

- **URL**: `http://localhost:8000/api/debate/{{$workflow.variables.session_id}}/result`
- **方法**: GET
- **響應處理**: 解析並提取 `final_conclusion`、`consensus_points` 等字段

#### 8. 獲取辯論歷史（HTTP 請求節點）

- **URL**: `http://localhost:8000/api/debate/{{$workflow.variables.session_id}}/history`
- **方法**: GET

### n8n 工作流示例圖

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 健康檢查        │────▶│ 獲取配置信息    │────▶│ 創建智能體 x4   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 獲取辯論歷史    │◀────│ 獲取辯論結果    │◀────│ 啟動辯論        │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ 配置智能體 x4   │
                                               └────────┬────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ 輪詢辯論狀態    │
                                               └─────────────────┘
```

## 主要 API 端點參考

### 智能體管理

- `POST /api/agents/create`: 創建新智能體
- `GET /api/agents/`: 獲取智能體列表
- `GET /api/agents/{agent_id}`: 獲取智能體詳情
- `PUT /api/agents/{agent_id}`: 更新智能體信息
- `POST /api/agents/{agent_id}/configure`: 配置智能體用於辯論

### 辯論管理

- `POST /api/debate/start`: 啟動新的辯論會話
- `GET /api/debate/{session_id}/status`: 獲取辯論狀態
- `GET /api/debate/{session_id}/result`: 獲取辯論結果
- `GET /api/debate/{session_id}/history`: 獲取辯論歷史
- `POST /api/debate/{session_id}/cancel`: 取消辯論

### 系統監控

- `GET /api/health`: 檢查服務健康狀態
- `GET /api/version`: 獲取API版本信息
- `GET /api/metrics`: 獲取性能指標
- `GET /api/config`: 獲取配置信息

## 示例：使用 financial_debate_api.sh 腳本

我們提供了一個增強版的 shell 腳本 `financial_debate_api.sh`，用於通過 curl 命令調用 API 實現完整的金融分析師辯論流程。此腳本包含改進的 JSON 解析功能、增強的錯誤處理和更友好的結果顯示。

### 使用方法

1. 確保 API 服務器已啟動並運行
2. 執行腳本：

```bash
cd /Users/loeb/LAB/agentscope/agentscope-api
./financial_debate_api.sh
```

### 腳本配置項

您可以在腳本頂部修改以下配置變量：

```bash
# API基礎URL
base_url="http://localhost:8000/api"

# 辯論配置
debate_topic="2024年全球經濟展望與投資策略"
debate_rounds=3
max_wait_time=300  # 最大等待時間（秒）
wait_interval=10   # 輪詢間隔（秒）
```

## 常見問題

### 1. 無法連接到 Ollama 服務

- 檢查 Ollama 服務是否正在運行
- 驗證 `OLLAMA_API_BASE` 配置是否正確
- 確認網絡連接和防火牆設置

### 2. 辯論結果返回為空或不完整

- 確保模型配置正確並且有足夠的生成 token 限制
- 檢查辯論輪次和最大持續時間設置
- 查看服務器日誌以獲取詳細錯誤信息

### 3. Windows 環境下的 pydantic 版本兼容性問題

在 Windows 環境中運行時，可能會遇到以下錯誤：
```
ModuleNotFoundError: No module named 'pydantic._internal._signature'
```

這是因為不同操作系統環境中 pydantic 和 pydantic-settings 版本兼容性問題。解決方法：

```bash
# 運行專門的修復腳本
python windows_install_fix.py

# 如果腳本不起作用，您可以嘗試手動安裝指定版本
pip install pydantic==2.11.9 pydantic-settings==2.10.1
```

這個問題主要出現在 Windows 環境中，macOS 和 Linux 環境通常不受影響。

## 文檔

- [AgentScope 官方文檔](https://doc.agentscope.io/)
- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [n8n 官方文檔](https://docs.n8n.io/)



## 辩论机制详解
1. 1.
   辩论结构 ：
   
   - 辩论按轮次进行，每轮有特定的子议题（特别是金融辩论中）
   - 每轮中，所有Agent依次发言表达自己的专业观点
   - 系统会为每个轮次分配不同的重点议题，如宏观经济分析、投资策略等
2. 2.
   交互特点 ：
   
   - 每个Agent在发言时，会收到之前所有轮次的完整对话历史
   - 系统提示词中明确要求Agent"针对前面的讨论内容进行回应"
   - 因此这不是纯粹的"独角戏"，而是包含了对先前发言的回应
3. 3.
   发言顺序优化 ：
   
   - 系统会根据当前议题内容调整发言顺序
   - 与议题最相关的专业领域Agent会优先发言
   - 例如讨论宏观经济时，宏观经济分析师会先发言
4. 4.
   结论生成 ：
   
   - 辩论结束后，系统会生成综合结论
   - 结论包含共识要点、分歧观点、各角色关键论点等
   - 通过这种方式汇总各方面的专业意见
## 总结
系统的辩论机制更接近于 结构化的专家研讨 模式 - 各专家先表达专业观点，同时考虑其他专家的意见。虽然不是严格意义上的"交互诘问"（如辩论比赛中的攻防），但确实包含了对先前发言的回应和参考，是一种平衡了专业性和互动性的设计。


## 許可證

Apache License 2.0
