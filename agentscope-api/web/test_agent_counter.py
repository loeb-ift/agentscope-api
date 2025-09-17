#!/usr/bin/env python3
"""
测试 Agent 计数器功能
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入需要测试的函数
from gradio_debate_app import get_agents_for_selection, load_initial_data

def test_get_agents_for_selection():
    """测试 get_agents_for_selection 函数"""
    print("测试 get_agents_for_selection 函数...")

    # 模拟 API 响应的数据
    mock_agents = [
        {
            "id": "agent1",
            "name": "测试Agent1",
            "role": "analyst",
            "created_at": "2025-01-01T00:00:00Z",
            "status": "active"
        },
        {
            "id": "agent2",
            "name": "测试Agent2",
            "role": "pragmatist",
            "created_at": "2025-01-01T00:00:00Z",
            "status": "active"
        }
    ]

    # 模拟成功的 API 响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_agents

    with patch('gradio_debate_app.make_api_request') as mock_request:
        mock_request.return_value = mock_response

        # 调用函数
        result = get_agents_for_selection()

        # 验证结果
        print(f"返回的 Agent 选项数量: {len(result)}")
        print(f"Agent 选项: {result}")

        assert len(result) == 2, f"期望 2 个选项，实际得到 {len(result)}"
        assert "测试Agent1 (analyst)" in result[0], f"第一个选项格式不正确: {result[0]}"
        assert "测试Agent2 (pragmatist)" in result[1], f"第二个选项格式不正确: {result[1]}"

        print("✅ get_agents_for_selection 测试通过")

def test_load_initial_data():
    """测试 load_initial_data 函数"""
    print("测试 load_initial_data 函数...")

    # 模拟 API 响应的数据
    mock_agents = [
        {
            "id": "agent1",
            "name": "测试Agent1",
            "role": "analyst"
        }
    ]

    # 模拟成功的 API 响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_agents

    with patch('gradio_debate_app.make_api_request') as mock_request:
        mock_request.return_value = mock_response

        # 调用函数
        result = load_initial_data()

        # 验证结果
        assert len(result) == 2, f"期望返回 2 个更新，实际得到 {len(result)}"

        choices_update, count_update = result

        # 验证选择更新
        assert hasattr(choices_update, 'choices'), "第一个返回值应该是 gr.update 对象"
        assert len(choices_update.choices) == 1, f"期望 1 个选择，实际得到 {len(choices_update.choices)}"

        # 验证计数更新
        assert hasattr(count_update, 'value'), "第二个返回值应该是 gr.update 对象"
        assert count_update.value == "當前 Agent 總數：1", f"计数文本不正确: {count_update.value}"

        print("✅ load_initial_data 测试通过")

def test_empty_agents():
    """测试空 Agent 列表的情况"""
    print("测试空 Agent 列表...")

    # 模拟空的 API 响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

    with patch('gradio_debate_app.make_api_request') as mock_request:
        mock_request.return_value = mock_response

        # 测试 get_agents_for_selection
        result = get_agents_for_selection()
        assert len(result) == 0, f"期望空列表，实际得到 {len(result)} 个选项"

        # 测试 load_initial_data
        result = load_initial_data()
        choices_update, count_update = result
        assert len(choices_update.choices) == 0, f"期望空选择列表，实际得到 {len(choices_update.choices)}"
        assert count_update.value == "當前 Agent 總數：0", f"计数文本不正确: {count_update.value}"

        print("✅ 空 Agent 列表测试通过")

if __name__ == "__main__":
    try:
        test_get_agents_for_selection()
        test_load_initial_data()
        test_empty_agents()
        print("\n🎉 所有测试通过！Agent 计数器功能正常。")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)