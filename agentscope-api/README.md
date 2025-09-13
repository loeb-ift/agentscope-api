# AgentScope API 服务

这是 AgentScope 的 API 服务组件，提供多智能体辩论功能的 RESTful API 接口。本服务允许您通过简单的 API 调用，创建多个智能体并让它们围绕特定主题进行辩论，最终生成结构化的辩论结果和总结。

## 核心功能

- 创建和管理多种类型的智能体（Agent）
- 配置智能体用于特定辩论主题
- 启动和管理多智能体辩论会话
- 获取辩论状态、结果和完整历史记录
- 支持在外部系统（如 n8n）中通过 API 调用实现辩论功能

## 目录结构

```
agentscope-api/
├── app/               # 主应用代码
│   ├── api/           # API 路由和端点
│   ├── core/          # 核心配置和功能
│   ├── models/        # 数据模型和架构定义
│   ├── services/      # 业务逻辑服务
│   └── main.py        # 应用入口
├── requirements.txt   # 项目依赖
├── start_server.py    # 服务器启动脚本
├── .env.example       # 环境变量配置示例
├── financial_debate_api.sh  # 金融分析师辩论API调用脚本
└── tests/             # 测试代码
```

## 系统架构分析

AgentScope API 采用了现代化的分布式系统架构设计，包含API服务器、消息队列、数据库和客户端组件，各组件协同工作以实现高效的多智能体辩论功能。

### 系统整体架构

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   客户端      │──────▶   API服务器   │──────▶  任务队列     │
│ (如financial_ │      │   (FastAPI)   │      │   (Redis)     │
│ debate_api.sh)│◀─────┘               │◀─────┘               │
└───────────────┘                      │        ┌─────────────┐
                                       │        │ Celery工作器│
                                       ▼        │   (异步任务)│
                              ┌───────────────┐  │             │
                              │    数据库     │  │             │
                              │  (PostgreSQL/ │  └─────────────┘
                              │   SQLite)     │         │
                              └───────────────┘         │
                                      │                 │
                                      │                 │
                                      ▼                 ▼
                              ┌───────────────┐  ┌───────────────┐
                              │   Ollama      │  │ 辩论结论生成  │
                              │   LLM服务     │  │  与通知任务   │
                              └───────────────┘  └───────────────┘
```

### API Server 核心组件

API Server 是系统的核心入口，基于 FastAPI 框架实现，负责处理所有客户端请求并协调各个服务组件。

**主要功能**：
- 提供 RESTful API 接口，处理智能体创建、配置和辩论管理请求
- 路由请求到适当的服务处理逻辑
- 数据验证和错误处理
- 认证和授权（当前版本简化处理）
- 文档自动生成（Swagger UI 和 ReDoc）

**核心模块**：
- `app/api/`: 包含所有 API 端点定义
- `app/services/`: 实现业务逻辑，如智能体管理和辩论流程控制
- `app/models/`: 定义数据模型和请求/响应结构
- `app/core/`: 包含配置管理和核心功能

### Redis 在系统中的作用

Redis 作为系统的关键基础设施，扮演了多个重要角色：

**主要功能**：
1. **消息代理**：作为 Celery 的任务队列后端，负责任务分发
2. **结果存储**：保存异步任务的执行结果
3. **缓存**：缓存频繁访问的数据以提高性能

**存储的数据类型**：
- Celery 任务队列数据（辩论任务、结论生成任务、通知任务）
- 任务执行状态和结果信息
- 临时缓存数据（如辩论进度状态）

**Redis 必要性**：
尽管当前 API 实现中部分异步任务调用代码被注释，但系统架构设计仍依赖 Redis 支持。完整部署时，Redis 对于支持异步任务处理和系统可扩展性至关重要。

### Client 交互方式

Client 端通过 HTTP 请求与 API Server 交互，实现完整的辩论流程。

**主要客户端示例**：
- `financial_debate_api.sh`: shell脚本客户端，通过 curl 命令调用 API
- n8n 工作流节点：在 n8n 自动化平台中通过 HTTP 请求节点调用 API
- 自定义客户端应用：根据 API 文档实现特定功能的客户端程序

**典型交互流程**：
1. 检查 API 服务健康状态
2. 获取 API 配置信息
3. 创建和配置辩论智能体
4. 启动辩论会话
5. 轮询辩论状态
6. 获取辩论结果和历史记录

## 环境要求

- Python 3.10+ 
- Ollama 服务（用于LLM模型调用）
- 可选：PostgreSQL 数据库（默认使用SQLite）
- Redis（用于缓存和任务队列，推荐使用）

## 快速开始

AgentScope API 提供了两种启动方式：本地环境和Docker环境。以下是详细的设置和使用指南。

### 使用Docker环境（推荐）

使用Docker可以简化环境配置，自动安装所有必要的服务（包括Redis、PostgreSQL和Celery）。

1. **准备环境**

确保您的系统已安装以下组件：
- Docker
- Docker Compose

2. **运行Docker设置脚本**

```bash
# 运行Docker设置脚本
./docker_setup.sh
```

此脚本将：
- 检查Docker环境
- 基于.env.example创建.env配置文件
- 构建并启动所有Docker服务（API服务器、Redis、PostgreSQL、Celery工作器）
- 显示服务状态和测试指令

3. **验证服务启动**

服务启动后，可以通过以下方式验证：
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

4. **测试API**

等待API服务完全启动后（约30秒），可以运行：

```bash
# 运行金融分析师辩论API测试
./financial_debate_api.sh
```

### 本地环境设置

如果您希望在本地直接运行服务，而不使用Docker，可以按照以下步骤操作：

1. **安装依赖**

```bash
cd /Users/loeb/LAB/agentscope/agentscope-api
pip install -r requirements.txt
```

2. **配置环境**

复制并配置环境变量文件：

```bash
cp .env.example .env
# 使用您喜欢的编辑器编辑 .env 文件
```

**关键配置项说明**：

- `OLLAMA_API_BASE`: Ollama 服务的地址（默认：`http://localhost:11434`）
- `DEFAULT_MODEL_NAME`: 默认使用的模型名称（例如：`gpt-oss:20b`）
- `DATABASE_URL`: 数据库连接字符串
- `HOST` 和 `PORT`: API 服务器的主机和端口

3. **启动服务器**

```bash
python start_server.py
```

服务启动后，您可以访问以下地址：
- API 基础地址: http://localhost:8000/api
- Swagger UI 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

### 常用命令

1. **Docker环境命令**
```bash
# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 进入API容器
docker-compose exec agentscope-api /bin/bash
```

2. **本地环境命令**
```bash
# 启动服务器
python start_server.py

# 测试API
./financial_debate_api.sh
```

## 智能体辩论 API 调用流程详解

本节详细解析 `financial_debate_api.sh` 脚本中实现的完整辩论流程，这是理解如何通过 API 调用实现多智能体辩论的核心参考。

### 完整辩论流程概述

1. [检查 API 服务健康状态](#1-检查-api-服务健康状态)
2. [获取 API 配置信息](#2-获取-api-配置信息)
3. [创建辩论智能体](#3-创建辩论智能体)
4. [配置智能体用于特定辩论主题](#4-配置智能体用于特定辩论主题)
5. [启动辩论会话](#5-启动辩论会话)
6. [轮询辩论状态](#6-轮询辩论状态)
7. [获取辩论结果](#7-获取辩论结果)
8. [获取辩论历史记录](#8-获取辩论历史记录)

### 1. 检查 API 服务健康状态

```bash
health_response=$(curl -s "${base_url}/health")
health_status=$(echo "$health_response" | jq -r ".status")
```

**API 端点**: `GET /api/health`

**功能**: 检查 API 服务是否正常运行

**返回**: 包含服务状态、版本和环境信息的 JSON 对象

### 2. 获取 API 配置信息

```bash
config_response=$(curl -s "${base_url}/config")
agent_roles=$(echo "$config_response" | jq -r ".agent_roles")
default_rounds=$(echo "$config_response" | jq -r ".default_debate_rounds")
```

**API 端点**: `GET /api/config`

**功能**: 获取 API 服务的配置信息，包括支持的智能体角色和辩论设置

**返回**: 包含角色类型、辩论轮次等配置信息的 JSON 对象

### 3. 创建辩论智能体

```bash
macro_agent_response=$(curl -s -X POST "${base_url}/agents/create" -H "Content-Type: application/json" -d '{
  "name": "宏观经济分析师",
  "role": "analyst",
  "system_prompt": "你是一位资深的宏观经济分析师...",
  "llm_config": {
    "temperature": "0.7",
    "max_tokens": "1024"
  },
  "personality_traits": ["专业", "客观", "深入"],
  "expertise_areas": ["宏观经济", "货币政策", "财政政策", "地缘政治"]
}')

macro_agent_id=$(echo "$macro_agent_response" | jq -r ".agent_id")
```

**API 端点**: `POST /api/agents/create`

**功能**: 创建新的智能体实例，设置其角色、系统提示、LLM 配置、个性特征和专业领域

**参数**: 
- `name`: 智能体名称
- `role`: 智能体角色类型
- `system_prompt`: 系统提示词，定义智能体行为和专业背景
- `llm_config`: LLM 模型配置，如 temperature 和 max_tokens
- `personality_traits`: 智能体个性特征数组
- `expertise_areas`: 智能体专业领域数组

**返回**: 包含创建的智能体 ID 的 JSON 对象

在脚本中，通常会创建多个不同角色的智能体以形成辩论团队。

### 4. 配置智能体用于特定辩论主题

```bash
config_response=$(curl -s -X POST "${base_url}/agents/${agent_id}/configure" -H "Content-Type: application/json" -d "{
  \"debate_topic\": \"$debate_topic\",
  \"additional_instructions\": \"请基于你的专业领域和知识，对辩论主题发表专业观点...\" 
}")
```

**API 端点**: `POST /api/agents/{agent_id}/configure`

**功能**: 为特定智能体配置辩论主题和附加指令

**参数**: 
- `debate_topic`: 辩论主题
- `additional_instructions`: 附加指令，指导智能体如何参与辩论

**返回**: 确认配置成功的 JSON 对象

### 5. 启动辩论会话

```bash
agent_ids_json="["$(printf '"%s",' "${global_agent_ids[@]}")"]"
agent_ids_json=${agent_ids_json%,]}"]"

start_response=$(curl -s -X POST "${base_url}/debate/start" -H "Content-Type: application/json" -d "{
  \"topic\": \"$debate_topic\",
  \"agent_ids\": $agent_ids_json,
  \"rounds\": $debate_rounds,
  \"max_duration_minutes\": 30
}")

session_id=$(echo "$start_response" | jq -r ".session_id")
```

**API 端点**: `POST /api/debate/start`

**功能**: 启动新的多智能体辩论会话

**参数**: 
- `topic`: 辩论主题
- `agent_ids`: 参与辩论的智能体 ID 数组
- `rounds`: 辩论轮次
- `max_duration_minutes`: 最大持续时间（分钟）

**返回**: 包含会话 ID 和初始状态的 JSON 对象

### 6. 轮询辩论状态

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

**API 端点**: `GET /api/debate/{session_id}/status`

**功能**: 查询辩论会话的当前状态

**返回**: 包含辩论状态、当前轮次、总轮次和进度的 JSON 对象

### 7. 获取辩论结果

```bash
result_response=$(curl -s "${base_url}/debate/${session_id}/result")

# 解析结果
al_final_conclusion=$(echo "$result_response" | jq -r ".final_conclusion")
confidence_score=$(echo "$result_response" | jq -r ".confidence_score")
consensus_points=$(echo "$result_response" | jq -r ".consensus_points[]")
divergent_views=$(echo "$result_response" | jq -r ".divergent_views[]")
```

**API 端点**: `GET /api/debate/{session_id}/result`

**功能**: 获取辩论的最终结果和总结

**返回**: 包含最终结论、可信度分数、共识要点和分歧观点的 JSON 对象

### 8. 获取辩论历史记录

```bash
history_response=$(curl -s "${base_url}/debate/${session_id}/history")

total_messages=$(echo "$history_response" | jq -r ".history | length")
```

**API 端点**: `GET /api/debate/{session_id}/history`

**功能**: 获取完整的辩论对话历史记录

**返回**: 包含所有辩论消息的 JSON 对象

## 在 n8n 中使用 AgentScope API

您可以在 n8n 工作流中通过 HTTP 请求节点调用 AgentScope API，实现多智能体辩论功能。以下是实现相同辩论流程的 n8n 工作流配置指南。

### n8n 工作流组件配置

#### 1. 服务健康检查（HTTP 请求节点）

- **URL**: `http://localhost:8000/api/health`
- **方法**: GET
- **响应处理**: 检查 `status` 字段是否为 `healthy`

#### 2. 获取配置信息（HTTP 请求节点）

- **URL**: `http://localhost:8000/api/config`
- **方法**: GET
- **响应处理**: 解析 `agent_roles` 和 `default_debate_rounds` 字段

#### 3. 创建智能体（HTTP 请求节点 x4）

为每个智能体创建一个 HTTP 请求节点：

- **URL**: `http://localhost:8000/api/agents/create`
- **方法**: POST
- **内容类型**: JSON
- **请求体**: 包含智能体信息的 JSON 对象（参考脚本中的配置）
- **响应处理**: 提取并存储 `agent_id` 字段

#### 4. 配置智能体（HTTP 请求节点 x4）

为每个智能体创建一个 HTTP 请求节点：

- **URL**: `http://localhost:8000/api/agents/{{$json.agent_id}}/configure`
- **方法**: POST
- **内容类型**: JSON
- **请求体**: `{"debate_topic": "{{$workflow.variables.debate_topic}}", "additional_instructions": "请基于你的专业领域和知识..."}`

#### 5. 启动辩论（HTTP 请求节点）

- **URL**: `http://localhost:8000/api/debate/start`
- **方法**: POST
- **内容类型**: JSON
- **请求体**: `{"topic": "{{$workflow.variables.debate_topic}}", "agent_ids": ["{{$json.macro_agent_id}}", "{{$json.equity_agent_id}}", ...], "rounds": 3, "max_duration_minutes": 30}`
- **响应处理**: 提取并存储 `session_id` 字段

#### 6. 轮询辩论状态（循环节点 + HTTP 请求节点）

- **循环节点**: 设置最大迭代次数和延迟时间
- **HTTP 请求节点**: 
  - **URL**: `http://localhost:8000/api/debate/{{$workflow.variables.session_id}}/status`
  - **方法**: GET
  - **条件退出**: 当 `status` 字段为 `completed` 或 `failed` 时退出循环

#### 7. 获取辩论结果（HTTP 请求节点）

- **URL**: `http://localhost:8000/api/debate/{{$workflow.variables.session_id}}/result`
- **方法**: GET
- **响应处理**: 解析并提取 `final_conclusion`、`consensus_points` 等字段

#### 8. 获取辩论历史（HTTP 请求节点）

- **URL**: `http://localhost:8000/api/debate/{{$workflow.variables.session_id}}/history`
- **方法**: GET

### n8n 工作流示例图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 健康检查        │────▶│ 获取配置信息    │────▶│ 创建智能体 x4   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 获取辩论历史    │◀────│ 获取辩论结果    │◀────│ 启动辩论        │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ 配置智能体 x4   │
                                               └────────┬────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ 轮询辩论状态    │
                                               └─────────────────┘
```

## 主要 API 端点参考

### 智能体管理

- `POST /api/agents/create`: 创建新智能体
- `GET /api/agents/`: 获取智能体列表
- `GET /api/agents/{agent_id}`: 获取智能体详情
- `PUT /api/agents/{agent_id}`: 更新智能体信息
- `POST /api/agents/{agent_id}/configure`: 配置智能体用于辩论

### 辩论管理

- `POST /api/debate/start`: 启动新的辩论会话
- `GET /api/debate/{session_id}/status`: 获取辩论状态
- `GET /api/debate/{session_id}/result`: 获取辩论结果
- `GET /api/debate/{session_id}/history`: 获取辩论历史
- `POST /api/debate/{session_id}/cancel`: 取消辩论

### 系统监控

- `GET /api/health`: 检查服务健康状态
- `GET /api/version`: 获取API版本信息
- `GET /api/metrics`: 获取性能指标
- `GET /api/config`: 获取配置信息

## 示例：使用 financial_debate_api.sh 脚本

我们提供了一个便捷的 shell 脚本 `financial_debate_api.sh`，用于通过 curl 命令调用 API 实现完整的金融分析师辩论流程。

### 使用方法

1. 确保 API 服务器已启动并运行
2. 执行脚本：

```bash
cd /Users/loeb/LAB/agentscope/agentscope-api
./financial_debate_api.sh
```

### 脚本配置项

您可以在脚本顶部修改以下配置变量：

```bash
# API基础URL
base_url="http://localhost:8000/api"

# 辩论配置
debate_topic="2024年全球经济展望与投资策略"
debate_rounds=3
max_wait_time=300  # 最大等待时间（秒）
wait_interval=10   # 轮询间隔（秒）
```

## 常见问题

### 1. 无法连接到 Ollama 服务

- 检查 Ollama 服务是否正在运行
- 验证 `OLLAMA_API_BASE` 配置是否正确
- 确认网络连接和防火墙设置

### 2. 辩论结果返回为空或不完整

- 确保模型配置正确并且有足够的生成 token 限制
- 检查辩论轮次和最大持续时间设置
- 查看服务器日志以获取详细错误信息

## 文档

- [AgentScope 官方文档](https://doc.agentscope.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [n8n 官方文档](https://docs.n8n.io/)

## 许可证

Apache License 2.0