#!/bin/bash

# AgentScope API Docker环境测试脚本

# 彩色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 等待服务启动
wait_for_services() {
    echo -e "${BLUE}等待API服务启动...${NC}"
    
    # 等待30秒让服务完全启动
    echo -e "${YELLOW}  等待中（约30秒）...${NC}"
    sleep 30
}

# 检查API健康状态
check_api_health() {
    echo -e "\n${BLUE}检查API健康状态...${NC}"
    
    API_HEALTH_URL="http://localhost:8000/api/health"
    
    # 发送HTTP请求检查健康状态
    if curl -s $API_HEALTH_URL > /dev/null; then
        echo -e "✅ API服务健康检查通过: $API_HEALTH_URL"
        return 0
    else
        echo -e "${RED}❌ API服务健康检查失败: $API_HEALTH_URL${NC}"
        echo -e "${YELLOW}  提示: 请检查Docker服务是否正常运行${NC}"
        return 1
    fi
}

# 显示Docker服务状态
display_docker_status() {
    echo -e "\n${BLUE}Docker服务状态:${NC}"
    docker-compose ps
}

# 运行金融分析师辩论API测试
run_financial_debate_test() {
    echo -e "\n${BLUE}运行金融分析师辩论API测试...${NC}"
    
    if [ -f ./financial_debate_api.sh ]; then
        chmod +x ./financial_debate_api.sh
        ./financial_debate_api.sh
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}\n✅ 金融分析师辩论API测试成功！${NC}"
            echo -e "${YELLOW}  提示: 辩论结果保存在当前目录的debate_result_*.json文件中${NC}"
            return 0
        else
            echo -e "${RED}\n❌ 金融分析师辩论API测试失败${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ financial_debate_api.sh文件不存在${NC}"
        return 1
    fi
}

# 主函数
main() {
    echo -e "${GREEN}========================${NC}"
    echo -e "${GREEN}  AgentScope API Docker环境测试${NC}"
    echo -e "${GREEN}========================${NC}"
    
    # 显示Docker服务状态
    display_docker_status
    
    # 等待服务启动
    wait_for_services
    
    # 检查API健康状态
    check_api_health
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}API服务未正常启动，测试终止${NC}"
        return 1
    fi
    
    # 运行金融分析师辩论API测试
    run_financial_debate_test
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}测试失败，请检查错误信息并尝试解决问题${NC}"
        return 1
    fi
    
    echo -e "\n${GREEN}✅ Docker环境API测试完成！${NC}"
    echo -e "${YELLOW}  提示: 如需停止Docker服务，请运行 'docker-compose down'${NC}"
    
    return 0
}

# 执行主函数
main

exit $?