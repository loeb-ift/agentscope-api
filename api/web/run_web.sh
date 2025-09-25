#!/bin/bash

# AgentScope 金融分析师辩论系统 - Web界面启动脚本
# 基于 financial_debate_api.sh 的Web实现

set -e

# 颜色配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
print_info "检查依赖环境..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 未安装"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 未安装"
    exit 1
fi

print_success "依赖检查通过"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    print_info "创建虚拟环境..."
    python3 -m venv venv
    print_success "虚拟环境创建完成"
fi

# 激活虚拟环境
print_info "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
print_info "安装Python依赖..."
pip3 install -r requirements.txt
print_success "依赖安装完成"

# 检查API服务
print_info "检查API服务状态..."
API_BASE_URL=${API_BASE_URL:-"http://10.227.135.97:8000"}
if curl -s "${API_BASE_URL}/api/health" > /dev/null; then
    print_success "API服务运行正常"
else
    print_warning "API服务可能未启动，请确保AgentScope API服务已运行"
    print_warning "启动命令: 在 agentscope-api 目录下运行 ./start_server.sh"
fi

# 创建web目录
print_info "创建web目录..."
mkdir -p web/results
mkdir -p web/logs

# 启动Gradio应用
print_info "启动Gradio Web界面..."
print_info "访问地址: http://localhost:7860"
print_info "按 Ctrl+C 停止服务"

# 运行应用
python3 gradio_debate_app.py

# 保持终端
read -p "按任意键继续..."