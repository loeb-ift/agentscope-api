#!/bin/bash

# AgentScope API 环境设置脚本

# 彩色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查环境变量
check_environment() {
    echo -e "${BLUE}检查环境配置...${NC}"
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        echo -e "✅ Python: $PYTHON_VERSION"
    else
        echo -e "${RED}❌ Python 未安装，请先安装Python 3.10或更高版本${NC}"
        return 1
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        echo -e "✅ pip: $(pip3 --version)"
    else
        echo -e "${RED}❌ pip 未安装，请先安装pip${NC}"
        return 1
    fi
    
    # 检查conda可用性
    if command -v conda &> /dev/null; then
        echo -e "✅ Conda: $(conda --version)"
        HAS_CONDA=1
    else
        echo -e "${YELLOW}⚠️ Conda 未找到，将使用系统Python环境${NC}"
        HAS_CONDA=0
    fi
    
    # 检查.env文件
    if [ -f .env ]; then
        echo -e "✅ 环境配置文件: .env 已存在"
        echo -e "${BLUE}  - Ollama API 地址: $(grep 'OLLAMA_API_BASE' .env | cut -d '=' -f 2)${NC}"
        echo -e "${BLUE}  - 默认模型: $(grep 'DEFAULT_MODEL_NAME' .env | cut -d '=' -f 2)${NC}"
        echo -e "${BLUE}  - 数据库: $(grep 'DATABASE_URL' .env | cut -d '=' -f 2)${NC}"
    else
        echo -e "${RED}❌ .env 文件不存在，请先创建环境配置文件${NC}"
        echo -e "${YELLOW}  提示: 可使用 .env.example 作为模板: cp .env.example .env${NC}"
        return 1
    fi
    
    return 0
}

# 创建conda环境（如果可用）
create_conda_env() {
    if [ $HAS_CONDA -eq 1 ]; then
        echo -e "\n${BLUE}创建conda环境...${NC}"
        
        # 检查是否已有agentscope环境
        if conda info --envs | grep -q "agentscope"; then
            echo -e "${YELLOW}⚠️ 环境 'agentscope' 已存在，将直接激活${NC}"
        else
            echo -e "${GREEN}正在创建环境 'agentscope'...${NC}"
            conda create -n agentscope python=3.10 -y
            if [ $? -ne 0 ]; then
                echo -e "${RED}❌ 创建conda环境失败${NC}"
                return 1
            fi
        fi
        
        # 激活环境
        echo -e "${GREEN}激活环境 'agentscope'...${NC}"
        conda activate agentscope
        
        return 0
    else
        return 0
    fi
}

# 安装依赖
install_dependencies() {
    echo -e "\n${BLUE}安装项目依赖...${NC}"
    
    if [ -f requirements.txt ]; then
        pip3 install -r requirements.txt
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 依赖安装完成${NC}"
            return 0
        else
            echo -e "${RED}❌ 依赖安装失败${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ requirements.txt 文件不存在${NC}"
        return 1
    fi
}

# 显示启动指令
show_start_instructions() {
    echo -e "\n${GREEN}✅ 环境设置完成！${NC}"
    echo -e "\n${BLUE}启动 API 服务器:${NC}"
    echo -e "  python start_server.py"
    
    echo -e "\n${BLUE}使用金融分析师辩论API脚本:${NC}"
    echo -e "  ./financial_debate_api.sh"
    
    echo -e "\n${BLUE}访问服务:${NC}"
    echo -e "  • API 文档: http://localhost:8000/docs"
    echo -e "  • 健康检查: http://localhost:8000/api/health"
    
    if [ $HAS_CONDA -eq 0 ]; then
        echo -e "\n${YELLOW}提示:${NC}"
        echo -e "  1. 如果您想使用conda管理环境，可以安装Miniconda或Anaconda"
        echo -e "  2. 安装后，您可以重新运行此脚本创建专门的Python环境"
        echo -e "  3. 当前我们使用的是系统默认的Python环境"
    fi
}

# 主函数
main() {
    echo -e "${GREEN}========================${NC}"
    echo -e "${GREEN}  AgentScope API 设置脚本${NC}"
    echo -e "${GREEN}========================${NC}"
    
    # 检查环境
    check_environment
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}环境检查失败，请先解决上述问题${NC}"
        return 1
    fi
    
    # 创建conda环境
    create_conda_env
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}创建conda环境失败${NC}"
        # 继续执行，尝试使用系统环境
    fi
    
    # 安装依赖
    install_dependencies
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}依赖安装失败${NC}"
        return 1
    fi
    
    # 显示启动指令
    show_start_instructions
    
    return 0
}

# 执行主函数
main

exit $?