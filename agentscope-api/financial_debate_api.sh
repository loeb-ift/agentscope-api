#!/bin/bash

# 金融分析师智能体辩论API调用脚本
# 该脚本通过curl命令调用AgentScope API实现金融分析师辩论功能

# 配置API基础URL
base_url="http://localhost:8000/api"

# 颜色设置
green="\033[0;32m"
red="\033[0;31m"
yellow="\033[0;33m"
reset="\033[0m"

# 打印函数
print_info() { echo -e "${green}[INFO]${reset} $1"; }
print_warning() { echo -e "${yellow}[WARNING]${reset} $1"; }
print_error() { echo -e "${red}[ERROR]${reset} $1"; }
print_separator() { echo "==========================================================================="; }

# 1. 健康检查
print_info "1. 检查API服务健康状态..."
health_response=$(curl -s "${base_url}/health")
if [[ $? -ne 0 ]]; then
    print_error "API服务不可用，请确保服务已启动"
    exit 1
fi

health_status=$(echo "$health_response" | jq -r ".status")
if [[ "$health_status" != "healthy" ]]; then
    print_error "API服务状态异常: $health_response"
    exit 1
fi

print_info "API服务健康状态: $health_status"
api_version=$(echo "$health_response" | jq -r ".version")
environment=$(echo "$health_response" | jq -r ".environment")
print_info "API版本: $api_version, 环境: $environment"
print_separator

# 2. 获取API配置信息
print_info "2. 获取API配置信息..."
config_response=$(curl -s "${base_url}/config")
agent_roles=$(echo "$config_response" | jq -r ".agent_roles")
default_rounds=$(echo "$config_response" | jq -r ".default_debate_rounds")
max_rounds=$(echo "$config_response" | jq -r ".max_debate_rounds")

print_info "支持的Agent角色: $agent_roles"
print_info "默认辩论轮次: $default_rounds, 最大辩论轮次: $max_rounds"
print_separator

# 3. 创建四个金融分析师智能体
print_info "3. 创建金融分析师智能体..."

# 初始化Agent ID数组和名称数组
global_agent_ids=()
global_agent_names=()

# 1. 宏观经济分析师
macro_agent_response=$(curl -s -X POST "${base_url}/agents/create" -H "Content-Type: application/json" -d '{
  "name": "宏观经济分析师",
  "role": "analyst",
  "system_prompt": "你是一位资深的宏观经济分析师，拥有15年的全球经济研究经验。你擅长分析全球经济趋势、货币政策、财政政策以及地缘政治事件对经济的影响。请全程使用繁体中文进行对话和分析。",
  "llm_config": {
    "temperature": "0.7",
    "max_tokens": "1024"
  },
  "personality_traits": ["专业", "客观", "深入"],
  "expertise_areas": ["宏观经济", "货币政策", "财政政策", "地缘政治"]
}')

macro_agent_id=$(echo "$macro_agent_response" | jq -r ".agent_id")
if [[ "$macro_agent_id" != "null" && -n "$macro_agent_id" ]]; then
    print_info "创建宏观经济分析师成功，ID: $macro_agent_id"
    global_agent_ids+=($macro_agent_id)
    global_agent_names+=("宏观经济分析师")
else
    print_error "创建宏观经济分析师失败: $macro_agent_response"
fi

# 2. 股票策略分析师
equity_agent_response=$(curl -s -X POST "${base_url}/agents/create" -H "Content-Type: application/json" -d '{
  "name": "股票策略分析师",
  "role": "pragmatist",
  "system_prompt": "你是一位资深的股票策略分析师，拥有12年的股票市场研究经验。你擅长分析不同行业的发展趋势、评估企业基本面，并提供股票投资组合配置建议。请全程使用繁体中文进行对话和分析。",
  "llm_config": {
    "temperature": "0.7",
    "max_tokens": "1024"
  },
  "personality_traits": ["战略", "细致", "前瞻性"],
  "expertise_areas": ["股票市场", "行业分析", "企业基本面", "投资组合配置"]
}')

equity_agent_id=$(echo "$equity_agent_response" | jq -r ".agent_id")
if [[ "$equity_agent_id" != "null" && -n "$equity_agent_id" ]]; then
    print_info "创建股票策略分析师成功，ID: $equity_agent_id"
    global_agent_ids+=($equity_agent_id)
    global_agent_names+=("股票策略分析师")
else
    print_error "创建股票策略分析师失败: $equity_agent_response"
fi

# 3. 固定收益分析师
fixed_income_agent_response=$(curl -s -X POST "${base_url}/agents/create" -H "Content-Type: application/json" -d '{
  "name": "固定收益分析师",
  "role": "critic",
  "system_prompt": "你是一位资深的固定收益分析师，拥有10年的债券市场研究经验。你擅长分析利率走势、信用风险评估以及各类固定收益产品的投资价值。请全程使用繁体中文进行对话和分析。",
  "llm_config": {
    "temperature": "0.7",
    "max_tokens": "1024"
  },
  "personality_traits": ["谨慎", "精确", "风险意识强"],
  "expertise_areas": ["债券市场", "利率分析", "信用风险", "固定收益产品"]
}')

fixed_income_agent_id=$(echo "$fixed_income_agent_response" | jq -r ".agent_id")
if [[ "$fixed_income_agent_id" != "null" && -n "$fixed_income_agent_id" ]]; then
    print_info "创建固定收益分析师成功，ID: $fixed_income_agent_id"
    global_agent_ids+=($fixed_income_agent_id)
    global_agent_names+=("固定收益分析师")
else
    print_error "创建固定收益分析师失败: $fixed_income_agent_response"
fi

# 4. 另类投资分析师
alternative_agent_response=$(curl -s -X POST "${base_url}/agents/create" -H "Content-Type: application/json" -d '{
  "name": "另类投资分析师",
  "role": "innovator",
  "system_prompt": "你是一位资深的另类投资分析师，拥有8年的另类投资研究经验。你擅长分析房地产、私募股权、对冲基金、大宗商品等非传统投资产品的风险收益特征。请全程使用繁体中文进行对话和分析。",
  "llm_config": {
    "temperature": "0.7",
    "max_tokens": "1024"
  },
  "personality_traits": ["创新", "灵活", "多元思维"],
  "expertise_areas": ["房地产", "私募股权", "对冲基金", "大宗商品"]
}')

alternative_agent_id=$(echo "$alternative_agent_response" | jq -r ".agent_id")
if [[ "$alternative_agent_id" != "null" && -n "$alternative_agent_id" ]]; then
    print_info "创建另类投资分析师成功，ID: $alternative_agent_id"
    global_agent_ids+=($alternative_agent_id)
    global_agent_names+=("另类投资分析师")
else
    print_error "创建另类投资分析师失败: $alternative_agent_response"
fi

print_separator

# 4. 配置智能体用于辩论
debate_topic="2024年全球经济展望与投资策略"
print_info "4. 配置智能体用于辩论，主题: $debate_topic"

for agent_id in "${global_agent_ids[@]}"; do
    config_response=$(curl -s -X POST "${base_url}/agents/${agent_id}/configure" -H "Content-Type: application/json" -d "{
      \"debate_topic\": \"$debate_topic\",
      \"additional_instructions\": \"请基于你的专业领域和知识，对辩论主题发表专业观点，提供具体的数据、案例和分析支持你的观点。\"
    }")
    
    # 找到对应的智能体名称
    agent_name=""
    for i in "${!global_agent_ids[@]}"; do
        if [[ "${global_agent_ids[$i]}" == "$agent_id" ]]; then
            agent_name="${global_agent_names[$i]}"
            break
        fi
    done
    
    if [[ $(echo "$config_response" | jq -r ".agent_id") == "$agent_id" ]]; then
        print_info "配置智能体 $agent_name 成功"
    else
        print_warning "配置智能体 $agent_name($agent_id) 失败或返回格式异常: $config_response"
    fi
    
    # 短暂延迟，避免请求过于频繁
    sleep 1
done

print_separator

# 5. 启动辩论
print_info "5. 启动金融分析师們辩论..."

debate_rounds=3

# 构建agent_ids的JSON数组
agent_ids_json="["$(printf '"%s",' "${global_agent_ids[@]}")"]"
# 移除最后一个逗号
agent_ids_json=${agent_ids_json%,]}"]"

# 启动辩论
start_response=$(curl -s -X POST "${base_url}/debate/start" -H "Content-Type: application/json" -d "{
  \"topic\": \"$debate_topic\",
  \"agent_ids\": $agent_ids_json,
  \"rounds\": $debate_rounds,
  \"max_duration_minutes\": 30
}")

session_id=$(echo "$start_response" | jq -r ".session_id")
debate_status=$(echo "$start_response" | jq -r ".status")
message=$(echo "$start_response" | jq -r ".message")

if [[ "$session_id" != "null" && -n "$session_id" ]]; then
    print_info "辩论启动成功！"
    print_info "会话ID: $session_id"
    print_info "状态: $debate_status"
    print_info "消息: $message"
else
    print_error "辩论启动失败: $start_response"
    exit 1
fi

print_separator

# 6. 轮询辩论状态
print_info "6. 轮询辩论状态，等待辩论完成..."

max_wait_time=300  # 最大等待时间5分钟
wait_interval=10   # 每10秒查询一次
elapsed_time=0

while true; do
    status_response=$(curl -s "${base_url}/debate/${session_id}/status")
    current_status=$(echo "$status_response" | jq -r ".status")
    current_round=$(echo "$status_response" | jq -r ".current_round")
    total_rounds=$(echo "$status_response" | jq -r ".total_rounds")
    progress=$(echo "$status_response" | jq -r ".progress")
    
    # 优化日志信息，使其更具体和易于理解
    if [[ "$current_status" == "running" ]]; then
        # 获取当前轮次的对话者身份
        round_participants=""
        if [[ -n "$current_round" && "$current_round" != "null" && "$current_round" -gt 0 ]]; then
            # 获取辩论历史，提取当前轮次的对话者
            current_history=$(curl -s "${base_url}/debate/${session_id}/history")
            
            # 健壮性检查，确保current_history不为空
            if [[ -n "$current_history" ]]; then
                # 打印调试信息，查看前几行数据结构
                echo "调试: 辩论历史数据结构预览: $(echo "$current_history" | head -c 300)" >&2
                
                # 从history中提取所有消息的agent_name（注意：API返回的agent_name实际是ID）
                agent_ids_in_round=$(echo "$current_history" | jq -r '.history[]?.agent_name // empty' 2>/dev/null | sort -u | head -5)
                
                if [[ -n "$agent_ids_in_round" ]]; then
                    # 将agent_id映射为名称
                    participants=()
                    for id in $agent_ids_in_round; do
                        for i in "${!global_agent_ids[@]}"; do
                            if [[ "${global_agent_ids[$i]}" == "$id" ]]; then
                                participants+=("${global_agent_names[$i]}")
                                break
                            fi
                        done
                    done
                    
                    if [[ ${#participants[@]} -gt 0 ]]; then
                        round_participants="本轮参与对话者: $(IFS=, ; echo "${participants[*]}")"
                    fi
                fi
                
                # 如果方式1失败，尝试直接从history中提取agent_role并映射为更友好的名称
                if [[ -z "$round_participants" ]]; then
                    # 提取agent_role字段并转换为友好名称
                    roles=$(echo "$current_history" | jq -r '.history[]?.agent_role // empty' 2>/dev/null | sort -u | head -5)
                    
                    if [[ -n "$roles" && "$roles" != "null" ]]; then
                        # 创建角色到友好名称的映射
                        role_map=()
                        role_map["advocate"]="积极倡导者"
                        role_map["critic"]="批判思考者"
                        role_map["mediator"]="调解者"
                        role_map["analyst"]="数据分析师"
                        role_map["innovator"]="创新者"
                        role_map["pragmatist"]="实务主义者"
                        
                        friendly_roles=()
                        for role in $roles; do
                            if [[ -n "${role_map[$role]}" ]]; then
                                friendly_roles+=("${role_map[$role]}")
                            else
                                friendly_roles+=($role)
                            fi
                        done
                        
                        round_participants="本轮参与对话者角色: $(IFS=, ; echo "${friendly_roles[*]}")"
                    fi
                fi
            fi
        fi
        print_info "辩论状态: $current_status [辩论进行中，正在执行第 $current_round 轮，已完成 $progress%，还剩 $(echo "$total_rounds - $current_round" | bc) 轮] $round_participants"
    else
        print_info "辩论状态: $current_status, 进度: $progress, 当前轮次: $current_round/$total_rounds"
    fi
    
    if [[ "$current_status" == "completed" || "$current_status" == "failed" ]]; then
        print_info "辩论已结束，状态: $current_status"
        break
    fi
    
    if (( elapsed_time >= max_wait_time )); then
        print_error "辩论超时，请手动查询状态"
        break
    fi
    
    sleep $wait_interval
    elapsed_time=$((elapsed_time + wait_interval))
done

print_separator

# 7. 获取辩论结果
print_info "7. 获取辩论结果..."
result_response=$(curl -s "${base_url}/debate/${session_id}/result")

if [[ $? -eq 0 ]]; then
    # 保存完整结果到文件
    timestamp=$(date +"%Y%m%d_%H%M%S")
    result_file="debate_result_${timestamp}.json"
    echo "$result_response" > "$result_file"
    print_info "辩论结果已保存到: $result_file"
    
    # 打印关键结果信息
    final_conclusion=$(echo "$result_response" | jq -r ".final_conclusion")
    confidence_score=$(echo "$result_response" | jq -r ".confidence_score")
    
    echo -e "\n${green}===== 辩论结论摘要 =====${reset}"
    echo -e "${green}最终结论:${reset} $final_conclusion"
    
    # 优化可信度分数显示，提供更友好的解释
    echo -e "${green}可信度分数:${reset} $confidence_score"
    if (( $(echo "$confidence_score == 0.0" | bc -l) )); then
        echo -e "${yellow}[提示]${reset} 可信度分数正在计算中或辩论结果仍在处理中，请稍后刷新查看最新结果"
    fi
    
    # 打印共识要点
    echo -e "\n${green}共识要点:${reset}"
    consensus_points=$(echo "$result_response" | jq -r ".consensus_points[]")
    if [[ -n "$consensus_points" ]]; then
        i=1
        while IFS= read -r point; do
            # 避免显示空行或null值
            if [[ -n "$point" && "$point" != "null" ]]; then
                echo "$i. $point"
                i=$((i + 1))
            fi
        done <<< "$consensus_points"
        
        # 如果所有点都是空的，则显示提示信息
        if [[ $i -eq 1 ]]; then
            echo "[提示] 共识要点提取中或暂无明确共识"
        fi
    else
        echo "[提示] 共识要点提取中或暂无明确共识"
    fi
    
    # 打印分歧观点
    echo -e "\n${green}分歧观点:${reset}"
    divergent_views=$(echo "$result_response" | jq -r ".divergent_views[]")
    if [[ -n "$divergent_views" ]]; then
        i=1
        while IFS= read -r view; do
            # 避免显示空行或null值
            if [[ -n "$view" && "$view" != "null" ]]; then
                echo "$i. $view"
                i=$((i + 1))
            fi
        done <<< "$divergent_views"
        
        # 如果所有观点都是空的，则显示提示信息
        if [[ $i -eq 1 ]]; then
            echo "[提示] 分歧观点提取中或智能体观点较为一致"
        fi
    else
        echo "[提示] 分歧观点提取中或智能体观点较为一致"
    fi
    
    echo -e "\n${green}===== 辩论结论结束 =====${reset}"
else
    print_error "获取辩论结果失败: $result_response"
fi

print_separator

# 8. 获取辩论历史记录
print_info "8. 获取辩论历史记录..."
history_response=$(curl -s "${base_url}/debate/${session_id}/history")

if [[ $? -eq 0 ]]; then
    # 保存历史记录到文件
    history_file="debate_history_${timestamp}.json"
    echo "$history_response" > "$history_file"
    print_info "辩论历史记录已保存到: $history_file"
    
    # 打印历史记录概览
    total_messages=$(echo "$history_response" | jq -r ".history | length")
    print_info "辩论历史记录包含 $total_messages 条消息"
    
    # 打印完整的辩论历史记录内容，方便调试
    print_info "打印辩论历史记录内容 (/api/financial-debate/${session_id}/history):"
    echo -e "${green}===== 辩论历史记录内容开始 =====${reset}"
    echo "$history_response" | jq .
    echo -e "${green}===== 辩论历史记录内容结束 =====${reset}"
else
    print_error "获取辩论历史记录失败: $history_response"
fi

print_separator
print_info "金融分析师智能体辩论API调用完成！"