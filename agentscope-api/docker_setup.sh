#!/bin/bash

# AgentScope API Docker 环境设置脚本

# 彩色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker和Docker Compose是否安装
check_docker() {
    echo -e "${BLUE}检查Docker环境...${NC}"
    
    # 检查Docker是否安装
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        echo -e "✅ Docker: $DOCKER_VERSION"
    else
        echo -e "${RED}❌ Docker 未安装，请先安装Docker${NC}"
        echo -e "${YELLOW}  安装指南: https://docs.docker.com/get-docker/${NC}"
        return 1
    fi
    
    # 检查Docker服务是否运行
    if docker info &> /dev/null; then
        echo -e "✅ Docker服务: 正在运行"
    else
        echo -e "${RED}❌ Docker服务: 未运行，请启动Docker服务${NC}"
        return 1
    fi
    
    # 检查Docker Compose是否安装
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_VERSION=$(docker-compose --version)
        echo -e "✅ Docker Compose: $DOCKER_COMPOSE_VERSION"
    else
        echo -e "${RED}❌ Docker Compose 未安装，请先安装Docker Compose${NC}"
        echo -e "${YELLOW}  安装指南: https://docs.docker.com/compose/install/${NC}"
        return 1
    fi
    
    return 0
}

# 检查并创建.env文件
setup_env_file() {
    echo -e "\n${BLUE}检查环境配置文件...${NC}"
    
    # 检查.env文件是否存在
    if [ -f .env ]; then
        echo -e "✅ 环境配置文件: .env 已存在"
        echo -e "${YELLOW}  提示: 如需更新配置，请编辑 .env 文件${NC}"
    else
        # 检查.env.example文件是否存在
        if [ -f .env.example ]; then
            echo -e "${GREEN}正在基于.env.example创建.env文件...${NC}"
            cp .env.example .env
            if [ $? -eq 0 ]; then
                echo -e "✅ 环境配置文件: .env 创建成功"
                echo -e "${YELLOW}  提示: 建议编辑 .env 文件，根据您的需求修改配置${NC}"
            else
                echo -e "${RED}❌ 创建.env文件失败${NC}"
                return 1
            fi
        else
            echo -e "${RED}❌ .env.example 文件不存在，无法创建环境配置文件${NC}"
            return 1
        fi
    fi
    
    return 0
}

# 构建并启动Docker容器
start_docker_services() {
    echo -e "\n${BLUE}启动Docker服务...${NC}"
    
    # 构建并启动所有服务
    docker-compose up -d --build
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Docker服务启动成功！${NC}"
        return 0
    else
        echo -e "${RED}❌ Docker服务启动失败${NC}"
        echo -e "${YELLOW}  提示: 请检查docker-compose.yml文件和Docker配置${NC}"
        return 1
    fi
}

# 显示服务状态
display_service_status() {
    echo -e "\n${BLUE}服务状态:${NC}"
    docker-compose ps
    
    echo -e "\n${BLUE}服务日志:${NC}"
    echo -e "  查看API服务日志: docker-compose logs -f agentscope-api"
    echo -e "  查看Redis日志: docker-compose logs -f redis"
    echo -e "  查看PostgreSQL日志: docker-compose logs -f postgres"
    echo -e "  查看Celery Worker日志: docker-compose logs -f celery-worker"
}

# 显示测试指令
display_test_instructions() {
    echo -e "\n${GREEN}✅ Docker环境设置完成！${NC}"
    echo -e "\n${BLUE}服务访问信息:${NC}"
    echo -e "  • API 文档: http://localhost:8000/docs"
    echo -e "  • 健康检查: http://localhost:8000/api/health"
    
    echo -e "\n${BLUE}测试金融分析师辩论API:${NC}"
    echo -e "  1. 等待API服务完全启动（约30秒）"
    echo -e "  2. 运行: ./financial_debate_api.sh"
    
    echo -e "\n${BLUE}常用Docker命令:${NC}"
    echo -e "  • 停止服务: docker-compose down"
    echo -e "  • 重启服务: docker-compose restart"
    echo -e "  • 查看容器内日志: docker-compose logs -f"
    echo -e "  • 进入API容器: docker-compose exec agentscope-api /bin/bash"
    
    echo -e "\n${YELLOW}注意:${NC}"
    echo -e "  1. 首次启动可能需要较长时间（下载镜像、构建容器）"
    echo -e "  2. 确保端口8000、6379、5432未被其他程序占用"
    echo -e "  3. 如果需要修改服务配置，请编辑.env文件后重启服务"
}

# 主函数
main() {
    echo -e "${GREEN}========================${NC}"
    echo -e "${GREEN}  AgentScope API Docker 环境设置${NC}"
    echo -e "${GREEN}========================${NC}"
    
    # 检查Docker环境
    check_docker
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}Docker环境检查失败，请先解决上述问题${NC}"
        return 1
    fi
    
    # 检查并创建.env文件
    setup_env_file
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}环境配置文件设置失败${NC}"
        return 1
    fi
    
    # 构建并启动Docker容器
    start_docker_services
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}Docker服务启动失败${NC}"
        return 1
    fi
    
    # 显示服务状态
    display_service_status
    
    # 显示测试指令
    display_test_instructions
    
    return 0
}

# 执行主函数
main

exit $?