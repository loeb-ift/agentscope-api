#!/bin/bash

# 金融分析师智能体辩论API调用脚本（增强版）
# 该脚本通过curl命令调用AgentScope API实现金融分析师辩论功能
# 增强功能：改进的JSON解析、增强的错误处理、角色统计和更友好的结果显示
# 整合了所有优化功能，提供完整的辩论过程展示和分析

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

# 增强的JSON解析函数 - 解决API响应中存在前导换行符导致的JSON解析错误
parse_json() {
    local json_data="$1"
    local jq_query="$2"
    
    # 清理JSON数据，移除前导的非JSON字符（如换行符）
    # 查找第一个'{'的位置并截取
    local first_brace_pos=$(echo -n "$json_data" | grep -b -o '{' | head -1 | cut -d: -f1)
    
    if [[ -n "$first_brace_pos" ]]; then
        # 如果找到了'{'，从该位置开始截取
        json_data="$(echo -n "$json_data" | cut -c $((first_brace_pos+1))-)"
    fi
    
    # 尝试解析JSON数据
    local result=$(echo -n "$json_data" | jq -r "$jq_query" 2>/dev/null)
    
    # 检查解析结果
    if [[ $? -ne 0 ]]; then
        print_warning "JSON解析失败，查询: $jq_query，尝试直接使用原始数据"
        echo "$json_data"  # 返回原始数据作为后备
        return 1
    fi
    
    echo "$result"
    return 0
}

# 1. 健康检查
print_info "1. 检查API服务健康状态..."
health_response=$(curl -s "${base_url}/health")
if [[ $? -ne 0 ]]; then
    print_error "API服务不可用，请确保服务已启动"
    exit 1
fi

health_status=$(parse_json "$health_response" ".status")
if [[ "$health_status" != "healthy" ]]; then
    print_error "API服务状态异常: $health_response"
    exit 1
fi

print_info "API服务健康状态: $health_status"
api_version=$(parse_json "$health_response" ".version")
environment=$(parse_json "$health_response" ".environment")
print_info "API版本: $api_version, 环境: $environment"
print_separator

# 2. 获取API配置信息
print_info "2. 获取API配置信息..."
config_response=$(curl -s "${base_url}/config")
agent_roles=$(parse_json "$config_response" ".agent_roles")
default_rounds=$(parse_json "$config_response" ".default_debate_rounds")
max_rounds=$(parse_json "$config_response" ".max_debate_rounds")

print_info "支持的Agent角色: $agent_roles"
print_info "默认辩论轮次: $default_rounds, 最大辩论轮次: $max_rounds"
print_separator

# 3. 创建四个金融分析师智能体
print_info "3. 创建金融分析师智能体..."

# 初始化Agent ID数组和名称数组
global_agent_ids=()
global_agent_names=()
global_agent_roles=()

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

macro_agent_id=$(parse_json "$macro_agent_response" ".agent_id")
if [[ "$macro_agent_id" != "null" && -n "$macro_agent_id" ]]; then
    print_info "创建宏观经济分析师成功，ID: $macro_agent_id"
    global_agent_ids+=($macro_agent_id)
    global_agent_names+=('宏观经济分析师')
    global_agent_roles+=('analyst')
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

equity_agent_id=$(parse_json "$equity_agent_response" ".agent_id")
if [[ "$equity_agent_id" != "null" && -n "$equity_agent_id" ]]; then
    print_info "创建股票策略分析师成功，ID: $equity_agent_id"
    global_agent_ids+=($equity_agent_id)
    global_agent_names+=('股票策略分析师')
    global_agent_roles+=('pragmatist')
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

fixed_income_agent_id=$(parse_json "$fixed_income_agent_response" ".agent_id")
if [[ "$fixed_income_agent_id" != "null" && -n "$fixed_income_agent_id" ]]; then
    print_info "创建固定收益分析师成功，ID: $fixed_income_agent_id"
    global_agent_ids+=($fixed_income_agent_id)
    global_agent_names+=('固定收益分析师')
    global_agent_roles+=('critic')
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

alternative_agent_id=$(parse_json "$alternative_agent_response" ".agent_id")
if [[ "$alternative_agent_id" != "null" && -n "$alternative_agent_id" ]]; then
    print_info "创建另类投资分析师成功，ID: $alternative_agent_id"
    global_agent_ids+=($alternative_agent_id)
    global_agent_names+=('另类投资分析师')
    global_agent_roles+=('innovator')
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
    
    if [[ $(parse_json "$config_response" ".agent_id") == "$agent_id" ]]; then
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

session_id=$(parse_json "$start_response" ".session_id")
debate_status=$(parse_json "$start_response" ".status")
message=$(parse_json "$start_response" ".message")

if [[ "$session_id" != "null" && -n "$session_id" ]]; then
    print_info "辩论启动成功！"
    print_info "会话ID: $session_id"
    print_info "状态: $debate_status"
    print_info "消息: $message"
    print_info "参与辩论的智能体: $(IFS=, ; echo "${global_agent_names[*]}")"
else
    print_error "辩论启动失败: $start_response"
    exit 1
fi

print_separator

# 6. 轮询辩论状态，等待辩论完成...
print_info "6. 轮询辩论状态，等待辩论完成..."

max_wait_time=300  # 最大等待时间5分钟
wait_interval=10   # 每10秒查询一次
elapsed_time=0
last_debug_output=""

alt_history_query="${base_url}/debate/${session_id}/history"
while true; do
    # 获取辩论状态
    status_response=$(curl -s "${base_url}/debate/${session_id}/status")
    current_status=$(parse_json "$status_response" ".status")
    current_round=$(parse_json "$status_response" ".current_round")
    total_rounds=$(parse_json "$status_response" ".total_rounds")
    progress=$(parse_json "$status_response" ".progress")
    
    # 初始化参与对话者变量
    round_participants=""
    
    # 优化日志信息，使其更具体和易于理解
    if [[ "$current_status" == "running" ]]; then
        # 处理null值，使用默认值代替
        if [[ "$current_round" == "null" || -z "$current_round" ]]; then
            current_round=1
            round_text="第 1 轮"
        else
            round_text="第 $current_round 轮"
        fi
        
        # 计算剩余轮次
        remaining_rounds=$((total_rounds - current_round))
        if [[ $remaining_rounds -lt 0 ]]; then
            remaining_rounds=0
        fi
        
        # 修复进度显示，确保格式正确
        if [[ "$progress" == "null" || -z "$progress" ]]; then
            progress="0"
        fi
        
        # 处理小数进度，可能是百分比值
        if [[ "$progress" == *.* ]]; then
            # 如果进度是小数（如0.9），可能需要乘以100显示为百分比
            progress_percent=$(echo "$progress * 100" | bc -l | cut -d '.' -f 1)
            if [[ $progress_percent -gt 100 ]]; then
                progress_percent=100
            fi
            progress_text="${progress_percent}%"
        else
            progress_text="${progress}%"
        fi
        
        # 获取当前辩论历史用于调试和参与者信息提取
        debate_history=$(curl -s "$alt_history_query")
        
        # 清理辩论历史数据，确保正确解析
        debate_history=$(parse_json "$debate_history" ".")
        
        # 检查debate_history是否为空
        if [[ -n "$debate_history" && "$debate_history" != "null" ]]; then
        # 显示所有轮次的完整参与者信息（优化部分）
            echo -e "\n${yellow}调试: 当前辩论历史完整数据结构预览${reset}"
            echo "会话ID: $session_id, 主题: $debate_topic, 总轮次: $total_rounds"
            echo "当前辩论历史中的所有参与者信息:"
            
            # 获取最新一条消息，显示正在发表的想法
            latest_message=$(parse_json "$debate_history" '.history | sort_by(.timestamp) | last // {}')
            latest_agent_role=$(parse_json "$latest_message" '.agent_role // "未知角色"')
            latest_content=$(parse_json "$latest_message" '.content[:50] // ""')
            
            # 检查是否包含错误信息
            if [[ "$latest_content" == *"错误"* || "$latest_content" == *"'NoneType' object"* ]]; then
                latest_content="[系统处理中]"
            fi
            
            # 转换角色名称
            if [[ "$latest_agent_role" == "analyst" ]]; then
                latest_role_name="宏观经济分析师"
            elif [[ "$latest_agent_role" == "pragmatist" ]]; then
                latest_role_name="股票策略分析师"
            elif [[ "$latest_agent_role" == "critic" ]]; then
                latest_role_name="固定收益分析师"
            elif [[ "$latest_agent_role" == "innovator" ]]; then
                latest_role_name="另类投资分析师"
            else
                latest_role_name="$latest_agent_role"
            fi
            
            # 如果有最新消息，显示谁正在发表想法
            if [[ -n "$latest_content" ]]; then
                echo -e "${green}最新发言: $latest_role_name 正在发表: $latest_content...${reset}"
            fi
        
        # 使用jq命令提取所有唯一的agent_role和agent_name组合
        # 注意：根据实际返回格式调整jq查询
        all_participants=$(parse_json "$debate_history" '.history[]? | "角色: " + (.agent_role // "未知角色") + ", 名称: " + (.agent_name // .agent_id) + ", 轮次: " + (.round_number | tostring // .round | tostring // "未知") + ", 内容: " + (.content[:20] // "无内容")' 2>/dev/null)
        
        if [[ -n "$all_participants" ]]; then
            echo "$all_participants"
        else
            # 尝试替代的JSON路径，适应不同的返回格式
            all_participants_alt=$(parse_json "$debate_history" '.history[]? | "角色: " + (.agent_role // "未知角色") + ", ID: " + (.agent_id // "未知ID") + ", 轮次: " + (.round | tostring // "未知")' 2>/dev/null)
            if [[ -n "$all_participants_alt" ]]; then
                echo "$all_participants_alt"
            else
                echo "[调试信息] 无法提取参与者信息，请检查API返回格式"
                # 显示原始历史记录的前500个字符用于调试
                echo "原始历史记录预览: $(echo "$debate_history" | cut -c 1-500)"
            fi
        fi
        
        # 按角色统计参与情况
        echo -e "\n${yellow}各角色参与统计:${reset}"
        
        # 改进的角色统计逻辑，记录所有消息的角色信息
            echo -e "\n${yellow}[调试信息] 所有消息的角色详情:${reset}"
            all_roles_detail=$(parse_json "$debate_history" '.history[]? | select(.content | contains("错误") == false and contains("NoneType") == false) | "ID: " + (.agent_id // "未知ID") + ", 角色: " + (.agent_role // "未知角色") + ", 轮次: " + (.round | tostring // "未知") + ", 消息ID: " + (.message_id // "未知")' 2>/dev/null)
            echo "$all_roles_detail"
            
            # 统计并显示错误消息数量
            error_message_count=$(parse_json "$debate_history" '[.history[]? | select(.content | contains("错误") or contains("NoneType"))] | length' 2>/dev/null)
            if [[ $error_message_count -gt 0 ]]; then
                echo -e "\n${red}[注意] 检测到 $error_message_count 条错误消息，已从显示中过滤。${reset}"
            fi
        
        # 统计已知角色和未知角色数量
        role_stats=$(parse_json "$debate_history" '.history[]?.agent_role' 2>/dev/null)
        
        # 统计有多少条消息没有agent_role或agent_role为null
        unknown_role_count=$(parse_json "$debate_history" '[.history[]? | select(.agent_role == null or .agent_role == "null" or .agent_role == "")] | length' 2>/dev/null)
        
        # 统计已知角色的分布
        known_role_stats=$(echo "$role_stats" | grep -v -e '^$' -e 'null' | sort | uniq -c)
        
        # 使用简单的if-else逻辑替代关联数组，提高兼容性
        # 显示改进的角色统计结果
        if [[ -n "$known_role_stats" ]]; then
            echo -e "\n${yellow}已知角色分布:${reset}"
            while read -r count role; do
                # 使用条件判断转换角色名称
                if [[ "$role" == "analyst" ]]; then
                    friendly_name="宏观经济分析师"
                elif [[ "$role" == "pragmatist" ]]; then
                    friendly_name="股票策略分析师"
                elif [[ "$role" == "critic" ]]; then
                    friendly_name="固定收益分析师"
                elif [[ "$role" == "innovator" ]]; then
                    friendly_name="另类投资分析师"
                else
                    friendly_name="$role"
                fi
                echo "$count $friendly_name ($role)"
            done <<< "$known_role_stats"
        fi
        
        if [[ $unknown_role_count -gt 0 ]]; then
            echo -e "\n${yellow}未知角色统计:${reset}"
            echo "$unknown_role_count 条消息没有明确的分析师角色，可能是系统消息或特殊消息"
        fi
        
        total_messages=$(parse_json "$debate_history" '.history | length' 2>/dev/null)
        echo -e "\n${yellow}消息总数:${reset} $total_messages"
    else
        print_warning "无法获取辩论历史数据或数据为空"
    fi
    
    # 尝试从辩论历史中提取所有参与者信息
    if [[ -n "$debate_history" && "$debate_history" != "null" ]]; then
        # 使用更可靠的方法提取所有唯一的agent_role，避免重复
        all_participants=$(parse_json "$debate_history" '.history[]? | select(.agent_role and .agent_role != "null" and .agent_role != "") | .agent_role' 2>/dev/null | sort -u)
        
        if [[ -n "$all_participants" ]]; then
            # 创建一个临时数组来存储转换后的角色名称
            temp_participants=()
            while IFS= read -r role; do
                # 使用条件判断转换角色名称
                if [[ "$role" == "analyst" ]]; then
                    friendly_name="宏观经济分析师"
                elif [[ "$role" == "pragmatist" ]]; then
                    friendly_name="股票策略分析师"
                elif [[ "$role" == "critic" ]]; then
                    friendly_name="固定收益分析师"
                elif [[ "$role" == "innovator" ]]; then
                    friendly_name="另类投资分析师"
                else
                    friendly_name="$role"
                fi
                
                # 只有当这个名称还没有在数组中时才添加
                if [[ ! " ${temp_participants[*]} " =~ " $friendly_name " ]]; then
                    temp_participants+=($friendly_name)
                fi
            done <<< "$all_participants"
            
            if [[ ${#temp_participants[@]} -gt 0 ]]; then
                # 确保包含所有创建的参与者
                for name in "${global_agent_names[@]}"; do
                    if [[ ! " ${temp_participants[*]} " =~ " $name " ]]; then
                        temp_participants+=($name)
                    fi
                done
                
                # 对参与者列表进行排序
                IFS=$'\n' sorted_unique_participants=($(sort <<<"${temp_participants[*]}"))
                unset IFS
                
                # 构建轮次参与者信息
                round_participants="本轮参与对话者: $(IFS=, ; echo "${sorted_unique_participants[*]}")"
            fi
        fi
    fi
    fi

    # 打印辩论状态信息
    if [[ "$current_status" == "running" ]]; then
        print_info "辩论状态: $current_status [辩论进行中，${round_text}，已完成 $progress_text，还剩 $remaining_rounds 轮] $round_participants"
    else
        print_info "辩论状态: $current_status, 进度: $progress_text, 当前轮次: $current_round/$total_rounds"
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
    result_file="result/debate_result_${timestamp}.json"
    echo "$result_response" > "$result_file"
    print_info "辩论结果已保存到: $result_file"
    
    # 打印关键结果信息
    final_conclusion=$(parse_json "$result_response" ".final_conclusion")
    confidence_score=$(parse_json "$result_response" ".confidence_score")
    
    echo -e "\n${green}===== 辩论结论摘要 =====${reset}"
    echo -e "${green}最终结论:${reset} $final_conclusion"
    
    # 优化可信度分数显示，提供更友好的解释
    echo -e "${green}可信度分数:${reset} $confidence_score"
    if (( $(echo "$confidence_score == 0.0" | bc -l) )); then
        echo -e "${yellow}[提示]${reset} 可信度分数正在计算中或辩论结果仍在处理中，请稍后刷新查看最新结果"
    fi
    
    # 打印共识要点
    echo -e "\n${green}共识要点:${reset}"
    consensus_points=$(parse_json "$result_response" ".consensus_points[]")
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
    divergent_views=$(parse_json "$result_response" ".divergent_views[]")
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
    history_file="log/debate_history_${timestamp}.json"
    echo "$history_response" > "$history_file"
    print_info "辩论历史记录已保存到: $history_file"
    
    # 打印历史记录概览
    total_messages=$(parse_json "$history_response" ".history | length")
    print_info "辩论历史记录包含 $total_messages 条消息"
    
    # 打印角色参与情况统计
    if [[ -n "$history_response" ]]; then
        # 统计每个角色的参与次数
        role_counts=$(parse_json "$history_response" '.history[]? | select(.agent_role and .agent_role != "null") | .agent_role' 2>/dev/null | sort | uniq -c)
        
        if [[ -n "$role_counts" ]]; then
            echo -e "\n${yellow}各角色参与次数统计:${reset}"
            while read -r count role; do
                # 转换角色名称
                if [[ "$role" == "analyst" ]]; then
                    friendly_name="宏观经济分析师"
                elif [[ "$role" == "pragmatist" ]]; then
                    friendly_name="股票策略分析师"
                elif [[ "$role" == "critic" ]]; then
                    friendly_name="固定收益分析师"
                elif [[ "$role" == "innovator" ]]; then
                    friendly_name="另类投资分析师"
                else
                    friendly_name="$role"
                fi
                echo "$count $friendly_name"
            done <<< "$role_counts"
        fi
    fi
    
    # 打印完整的辩论历史记录内容，方便调试
    print_info "打印辩论历史记录内容 (/api/financial-debate/${session_id}/history):"
    echo -e "${green}===== 辩论历史记录内容开始 =====${reset}"
    
    # 过滤掉包含错误信息的消息后再显示
    filtered_history=$(echo "$history_response" | jq '.history = [.history[] | select(.content | contains("错误") == false and contains("NoneType") == false)]')
    echo "$filtered_history" | jq .
    
    # 显示过滤掉的错误消息数量
    original_count=$(echo "$history_response" | jq '.history | length')
    filtered_count=$(echo "$filtered_history" | jq '.history | length')
    filtered_errors=$((original_count - filtered_count))
    if [[ $filtered_errors -gt 0 ]]; then
        echo -e "\n${yellow}[说明] 为了更好的阅读体验，已过滤掉 $filtered_errors 条系统错误消息。${reset}"
        echo -e "${yellow}[说明] 完整的未过滤历史记录已保存到: $history_file${reset}"
    fi
    
    echo -e "${green}===== 辩论历史记录内容结束 =====${reset}"
else
    print_error "获取辩论历史记录失败: $history_response"
fi

print_separator
print_info "金融分析师智能体辩论API调用完成！"