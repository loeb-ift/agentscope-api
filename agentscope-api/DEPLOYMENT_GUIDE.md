# AgentScope API 项目交付文档

## 项目概述

AgentScope API 是一个完整的多智能体辩论系统，包含两大部分：
- **API 服务**：提供后端核心功能，包括智能体管理、辩论执行等
- **Web 服务**：基于 Gradio 的前端界面，提供用户交互界面

这两个服务可以独立部署在不同的机器上，通过 HTTP API 进行通信。

## 项目结构

```
agentscope-api/
├── app/               # API 服务核心代码
│   ├── api/           # API 路由和端点
│   ├── services/      # 业务逻辑服务
│   ├── utils/         # 工具函数
│   └── models/        # 数据模型
├── web/               # Web 前端服务
│   ├── gradio_debate_app.py  # Gradio 应用主文件
│   └── requirements.txt      # Web 服务依赖
├── requirements.txt   # API 服务依赖
├── start_server.py    # API 服务启动脚本
└── run_web.sh         # Web 服务启动脚本
```

## 环境要求

### 通用要求
- Python 3.10 或更高版本
- Ollama 服务（用于大语言模型推理）

### API 服务特定要求
- 数据库（SQLite，默认内置）
- 可选：Redis（用于任务队列）

### Web 服务特定要求
- Gradio
- 网络连接（访问 API 服务）

## API 服务安装与启动

### 1. 克隆仓库

```bash
git clone https://github.com/loeb-ift/agentscope-api.git
cd agentscope-api/agentscope-api
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件并配置必要的环境变量：

```bash
# 复制示例环境变量文件
cp .env.example .env

# 编辑 .env 文件，根据需要修改配置
# 主要配置项：
# - OLLAMA_BASE_URL: Ollama 服务地址
# - DEFAULT_MODEL_NAME: 默认使用的模型名称
# - SERVER_HOST: API 服务器主机地址
# - SERVER_PORT: API 服务器端口
```

### 4. 启动 API 服务

```bash
python start_server.py
```

服务启动后，API 将在配置的主机和端口上运行（默认：http://0.0.0.0:8000）。

### 5. 验证 API 服务

API 服务提供以下端点：
- 健康检查：`GET /api/health`
- API 文档：`GET /docs` 或 `GET /redoc`
- 创建智能体：`POST /api/agents/create`
- 智能体列表：`GET /api/agents/`
- 启动辩论：`POST /api/debate/start`
- 辩论状态：`GET /api/debate/{session_id}/status`

## Web 服务安装与启动

> **重要提示**：在启动Web服务前，**必须先启动AgentScope API服务**。

### 1. 导航到 Web 服务目录

```bash
cd agentscope-api/web
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件并配置必要的环境变量：

```bash
# 复制示例环境变量文件
cp .env.example .env

# 编辑 .env 文件，主要配置 API 服务地址
# API_BASE_URL=http://localhost:8000  # 默认值，如果 API 服务在不同机器上，需修改为相应的地址
```

### 4. 启动 Web 服务

```bash
python gradio_debate_app.py
# 或使用提供的启动脚本
# ./run_web.sh
```

服务启动后，Web 界面将在默认端口 7861 上运行，可以通过浏览器访问：http://localhost:7861

## 分离部署指南

两个服务可以部署在不同的机器上，只需确保它们能够通过网络通信即可。

### 步骤 1：在机器 A 上部署 API 服务

按照上述 API 服务安装与启动指南进行操作，但需要：
- 确保 API 服务绑定到可公开访问的 IP 地址（例如：0.0.0.0）
- 确保防火墙允许相应端口的访问

### 步骤 2：在机器 B 上部署 Web 服务

按照上述 Web 服务安装与启动指南进行操作，但需要：
- 修改 `.env` 文件中的 `API_BASE_URL` 为机器 A 的 IP 地址和 API 服务端口
  ```
  API_BASE_URL=http://<机器A的IP地址>:<API服务端口>
  ```

### 步骤 3：验证连接

启动两个服务后，通过访问 Web 界面，尝试创建辩论会话，验证 Web 服务是否能够正确连接到 API 服务。

## Docker 部署（可选）

项目提供了 Docker 支持，可以使用 Docker 快速部署服务。

### API 服务 Docker 部署

```bash
# 在 agentscope-api 目录下
docker build -t agentscope-api .
docker run -p 8000:8000 --env-file .env agentscope-api
```

### Web 服务 Docker 部署

```bash
# 在 agentscope-api/web 目录下
# 先创建 Dockerfile
cat > Dockerfile << EOF
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "gradio_debate_app.py"]
EOF

# 构建并运行容器
docker build -t agentscope-web .
docker run -p 7861:7861 --env-file .env agentscope-web
```

## 常见问题与解决方案

### 1. API 服务无法连接到 Ollama
- 检查 `.env` 文件中的 `OLLAMA_BASE_URL` 是否正确
- 确保 Ollama 服务正在运行且可访问

### 2. Web 服务无法连接到 API 服务
- 检查 Web 服务 `.env` 文件中的 `API_BASE_URL` 是否正确
- 确保 API 服务正在运行且网络连接畅通
- 检查防火墙设置是否阻止了连接

### 3. 辩论执行失败
- 检查 Ollama 服务是否正常工作
- 确认使用的模型已正确下载
- 查看 API 服务日志以获取详细错误信息

## 技术支持

如有任何问题或需要进一步的技术支持，请联系项目维护团队。