# 🤖 AgentScope 金融分析师辩论系统 - Web界面

基于Gradio的Web界面，实现AgentScope金融分析师辩论系统的可视化操作。

## 🚀 快速开始

> **重要提示**：在启动Web服务前，**必须先启动AgentScope API服务**。

### 1. 启动Web界面

```bash
# 进入web目录
cd web

# 给启动脚本执行权限
chmod +x run_web.sh

# 启动Web界面
./run_web.sh
```

### 2. 手动安装和启动

```bash
# 先启动API服务（在agentscope-api目录下）
cd ../
python start_server.py

# 然后启动Web服务（在agentscope-api/web目录下）
cd web

# 安装依赖
pip install -r requirements.txt

# 启动应用
python gradio_debate_app.py
```

### 3. 访问界面

启动后，在浏览器中访问：http://localhost:7860

## 📋 功能说明

### 1. 服务状态检查
- 自动检查AgentScope API服务状态
- 确保后端服务正常运行

### 2. 智能体创建
- **默认配置**：包含4个专业金融分析师角色
  - 宏观经济分析师
  - 股票策略分析师  
  - 固定收益分析师
  - 另类投资分析师
- **自定义配置**：支持自定义智能体角色和配置

### 3. 辩论配置
- **辩论主题**：输入任意金融相关主题
- **辩论轮次**：支持1-10轮辩论

### 4. 实时进度
- 显示辩论进度和状态
- 实时更新每轮辩论内容

### 5. 结果展示
- 完整的辩论历史记录
- 按轮次整理的辩论内容
- 支持保存和导出结果

## 🎯 使用步骤

1. **检查服务**：点击"检查服务状态"确保API正常运行
2. **配置主题**：输入辩论主题和轮次
3. **创建智能体**：使用默认或自定义配置创建智能体
4. **启动辩论**：点击"启动辩论"开始
5. **查看结果**：辩论完成后查看完整结果

## 📝 自定义智能体配置

### 格式要求
自定义配置需要JSON格式，包含以下字段：

```json
[
  {
    "name": "智能体名称",
    "role": "角色类型",
    "system_prompt": "系统提示词",
    "personality_traits": ["性格特征1", "性格特征2"],
    "expertise_areas": ["专业领域1", "专业领域2"]
  }
]
```

### 角色类型
- `analyst`: 分析师
- `pragmatist`: 实用主义者  
- `critic`: 批评者
- `innovator`: 创新者

## 🔧 配置说明

### 环境变量

使用 `.env.example` 文件作为模板创建 `.env` 文件：

```bash
# 复制示例环境变量文件
cp .env.example .env

# 编辑 .env 文件，设置以下环境变量：
# API_BASE_URL=http://localhost:8000  # AgentScope API 服务地址
# OLLAMA_HOST=http://localhost:11434  # Ollama 服务地址
# OLLAMA_MODEL=gpt-oss:20b            # 使用的模型
# GRADIO_SERVER_NAME=0.0.0.0          # Gradio Web 服务主机
# GRADIO_SERVER_PORT=7860             # Gradio Web 服务端口
```

### 分离部署说明

Web 服务可以独立部署在与 API 服务不同的机器上。只需确保：

1. API 服务配置了可公开访问的地址（在 API 服务的 `.env` 文件中设置 `SERVER_HOST=0.0.0.0`）
2. Web 服务的 `.env` 文件中 `API_BASE_URL` 设置为正确的 API 服务地址
   ```
   API_BASE_URL=http://<API服务器IP>:<API服务端口>
   ```
3. 两台机器之间网络连接畅通，防火墙允许相应端口的访问

### 网络要求
- 需要访问AgentScope API服务
- 确保网络连接正常

## 📊 示例主题

- "2024年全球经济展望与投资策略"
- "人工智能对金融行业的影响分析"
- "数字货币监管政策的影响"
- "ESG投资的发展趋势"
- "中国房地产市场的未来走向"

## 🛠️ 故障排除

### 常见问题

1. **API连接失败**
   - 检查AgentScope服务是否启动
   - 确认API_BASE_URL配置正确

2. **智能体创建失败**
   - 检查OLLAMA服务状态
   - 确认模型配置正确

3. **辩论无法启动**
   - 确保已创建智能体
   - 检查网络连接

### 日志查看

查看日志文件：
```bash
tail -f web/logs/gradio.log
```

## 📁 目录结构

```
web/
├── gradio_debate_app.py    # 主应用文件
├── run_web.sh              # 启动脚本
├── requirements.txt        # Python依赖
├── README.md              # 说明文档
├── results/               # 结果保存目录
└── logs/                  # 日志目录
```

## 🔗 相关链接

- [AgentScope API文档](../README.md)
- [金融辩论API脚本](../financial_debate_api.sh)

## 📞 技术支持

如有问题，请检查：
1. 服务状态是否正常
2. 网络连接是否畅通
3. 配置是否正确
4. 查看日志获取详细信息