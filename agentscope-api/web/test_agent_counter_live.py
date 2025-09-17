#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time

# 添加web目录到Python路径，以便导入所需模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 简化输出，确保能看到关键信息
def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")

# 导入需要测试的函数
try:
    from gradio_debate_app import get_agents_for_selection, refresh_agent_list_with_retry, load_initial_data
    print("成功导入所需函数")
except ImportError as e:
    print(f"导入函数失败: {str(e)}")
    sys.exit(1)

# 测试 get_agents_for_selection 函数
def test_get_agents_for_selection():
    print_section("测试 get_agents_for_selection 函数")
    start_time = time.time()
    try:
        agents = get_agents_for_selection()
        end_time = time.time()
        print(f"函数执行耗时: {end_time - start_time:.4f} 秒")
        print(f"返回的Agent数量: {len(agents) if agents else 0}")
        print(f"返回的数据类型: {type(agents)}")
        if agents:
            print(f"数据内容示例: {agents[:2] if len(agents)>=2 else agents}")
        return agents
    except Exception as e:
        print(f"函数执行出错: {str(e)}")
        return None

# 测试 refresh_agent_list_with_retry 函数
def test_refresh_agent_list_with_retry():
    print_section("测试 refresh_agent_list_with_retry 函数")
    start_time = time.time()
    try:
        agents = refresh_agent_list_with_retry()
        end_time = time.time()
        print(f"函数执行耗时: {end_time - start_time:.4f} 秒")
        print(f"返回的Agent数量: {len(agents) if agents else 0}")
        print(f"返回的数据类型: {type(agents)}")
        if agents:
            print(f"数据内容示例: {agents[:2] if len(agents)>=2 else agents}")
        return agents
    except Exception as e:
        print(f"函数执行出错: {str(e)}")
        return None

# 测试 load_initial_data 函数
def test_load_initial_data():
    print_section("测试 load_initial_data 函数")
    start_time = time.time()
    try:
        result = load_initial_data()
        end_time = time.time()
        print(f"函数执行耗时: {end_time - start_time:.4f} 秒")
        print(f"返回的数据类型: {type(result)}")
        if result:
            if isinstance(result, tuple) and len(result) >= 2:
                selections, count_text = result[:2]
                print(f"返回的选择器选项数量: {len(selections) if selections else 0}")
                print(f"返回的计数文本: {count_text}")
                return selections, count_text
            else:
                print(f"返回的结果不是预期的元组格式")
        else:
            print("函数返回了None")
        return None, None
    except Exception as e:
        print(f"函数执行出错: {str(e)}")
        return None, None

# 运行所有测试并汇总结果
if __name__ == "__main__":
    print("开始测试 Agent 计数相关函数...\n")
    
    # 运行测试
    agents1 = test_get_agents_for_selection()
    agents2 = test_refresh_agent_list_with_retry()
    selections, count_text = test_load_initial_data()
    
    # 汇总结果
    print_section("测试结果汇总")
    print(f"get_agents_for_selection 返回的Agent数量: {len(agents1) if agents1 else 0}")
    print(f"refresh_agent_list_with_retry 返回的Agent数量: {len(agents2) if agents2 else 0}")
    print(f"load_initial_data 返回的选择器选项数量: {len(selections) if selections else 0}")
    print(f"load_initial_data 返回的计数文本: {count_text}")
    
    # 检查是否发现问题
    all_tests_have_agents = (agents1 and len(agents1) > 0) and (agents2 and len(agents2) > 0) and (selections and len(selections) > 0)
    
    if all_tests_have_agents:
        print("\n✅ 测试结果: 所有函数都能正确获取到Agent数据。")
        print("问题可能在Gradio界面更新或数据展示环节。")
    else:
        print("\n❌ 测试结果: 部分或所有函数未能获取到Agent数据。")
        print("问题可能在于函数本身或API调用。")
    
    print("\n测试完成。")