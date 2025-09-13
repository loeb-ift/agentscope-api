# AgentScope API 服务

这是 AgentScope 的 API 服务组件，提供多智能体辩论功能的 RESTful API 接口。

## 功能特性

- 创建和管理多种类型的智能体（Agent）
- 启动和管理多智能体辩论会话
- 获取辩论状态、结果和完整历史记录
- 支持健康检查和性能监控

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

## 环境要求

- Python 3.10+ （与AgentScope要求一致）
- Ollama 服务（用于LLM模型调用）
- 可选：PostgreSQL 数据库（默认使用SQLite）
- 可选：Redis（用于缓存和任务队列）

## 快速开始

### 使用一键设置脚本（推荐）

我们提供了便捷的设置脚本，可以自动检查环境、安装依赖并提供清晰的启动指导：

```bash
cd /Users/loeb/LAB/agentscope/agentscope-api
./setup.sh
```

此脚本会自动：
- 检查Python和pip安装情况
- 检查conda是否可用（如不可用会提供替代方案）
- 验证.env配置文件
- 安装项目依赖
- 提供启动和使用API的详细说明

### 手动设置（高级用户）

#### 1. 安装依赖

```bash
cd /Users/loeb/LAB/agentscope/agentscope-api
pip install -r requirements.txt
```

#### 2. 配置环境

.env文件已存在并配置了基本设置。如需修改：

```bash
# 使用您喜欢的编辑器编辑 .env 文件
```

**关键配置项说明**：

- `OLLAMA_API_BASE`: Ollama 服务的地址（默认：`http://localhost:11434`）
- `DEFAULT_MODEL_NAME`: 默认使用的模型名称（例如：`gpt-oss:20b`）
- `DATABASE_URL`: 数据库连接字符串
- `HOST` 和 `PORT`: API 服务器的主机和端口

### 3. 启动服务器

```bash
python start_server.py
```

服务启动后，您可以访问以下地址：
- API 基础地址: http://localhost:8000/api
- Swagger UI 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

### 验证服务是否正常运行

打开一个新的终端窗口，使用 curl 命令检查 API 健康状态：

```bash
curl http://localhost:8000/api/health
```

如果服务正常运行，您应该会看到类似以下响应：

```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development",
  "uptime": "xx:xx:xx"
}
```
## 使用金融分析师辩论API脚本

我们提供了一个便捷的 shell 脚本 `financial_debate_api.sh`，用于通过 curl 命令调用 API 实现完整的金融分析师辩论流程。

### 脚本功能

1. 检查 API 服务健康状态
2. 创建四个不同专业领域的金融分析师智能体
3. 配置智能体用于特定辩论主题
4. 启动多智能体辩论
5. 轮询辩论状态直至完成
6. 获取和展示辩论结果
7. 保存辩论历史记录

### 使用方法

1. 确保 API 服务器已启动并运行
2. 执行脚本：

```bash
cd /Users/loeb/LAB/agentscope/agentscope-api
./financial_debate_api.sh
```

### 脚本配置项

脚本顶部的配置变量可根据需要调整：

```bash
# API基础URL
base_url="http://localhost:8000/api"

# 辩论配置
debate_topic="2024年全球经济展望与投资策略"
debate_rounds=3
max_wait_time=300  # 最大等待时间（秒）
wait_interval=10   # 轮询间隔（秒）
```

## 主要 API 端点

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

## 测试

项目包含多个测试脚本，您可以运行它们来验证功能：

```bash
python -m pytest tests/
```

## 常见问题

### 1. 启动服务器时出现 "command not found: conda" 错误

这表示您的环境中没有安装 conda。解决方案：

**方案1：使用一键设置脚本**
```bash
./setup.sh
```
我们的设置脚本会自动检测环境并提供替代方案，即使没有conda也能正常工作。

**方案2：安装 conda**
推荐使用 Miniconda（轻量级版本）：
1. 从 [Miniconda 官网](https://docs.conda.io/en/latest/miniconda.html) 下载适合您系统的安装包
2. 按照安装向导完成安装
3. 重新打开终端，然后运行 `./setup.sh` 脚本

**方案3：直接使用系统的 Python 环境**
确保已安装所有依赖：
```bash
pip install -r requirements.txt
```
然后直接启动服务器：
```bash
python start_server.py
```

### 2. 无法连接到 Ollama 服务

- 检查 Ollama 服务是否正在运行
- 验证 `OLLAMA_API_BASE` 配置是否正确
- 确认网络连接和防火墙设置

### 3. 辩论结果返回为空或不完整

- 确保模型配置正确并且有足够的生成 token 限制
- 检查辩论轮次和最大持续时间设置
- 查看服务器日志以获取详细错误信息

## 文档

- [AgentScope 官方文档](https://doc.agentscope.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 许可证

Apache License 2.0