#!/usr/bin/env python3
"""
测试健康检查功能
"""

import json
from unittest.mock import patch, MagicMock
import sys
import os

# 添加当前目录到Python路径，以便导入gradio_debate_app模块
sys.path.insert(0, os.path.dirname(__file__))

# 导入必要的函数
from gradio_debate_app import check_service

def test_check_service_success():
    """测试成功的健康检查"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "development",
        "dependencies": {
            "llm_service": "operational",
            "database": "operational",
            "redis": "degraded"
        }
    }

    with patch('gradio_debate_app.make_api_request') as mock_request:
        mock_request.return_value = mock_response

        result = check_service()
        print("测试成功场景:")
        print(result)
        print("-" * 50)

        # 验证结果包含预期内容
        assert "✅ 总计状态: healthy" in result
        assert "📦 API版本: 1.0.0" in result
        assert "🌍 运行环境: development" in result
        assert "🔗 依赖项状态:" in result
        assert "✅ Llm Service: operational" in result
        assert "✅ Database: operational" in result
        assert "⚠️ Redis: degraded" in result

def test_check_service_api_error():
    """测试API错误场景"""
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch('gradio_debate_app.make_api_request') as mock_request:
        mock_request.return_value = mock_response

        result = check_service()
        print("测试API错误场景:")
        print(result)
        print("-" * 50)

        assert "❌ API服务不可用 (HTTP 500)" in result

def test_check_service_exception():
    """测试异常场景"""
    with patch('gradio_debate_app.make_api_request', side_effect=Exception("Network error")):
        result = check_service()
        print("测试异常场景:")
        print(result)
        print("-" * 50)

        assert "❌ 检查服务时出错:" in result
        assert "Network error" in result

def test_check_service_no_dependencies():
    """测试无依赖项的场景"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "production"
    }

    with patch('gradio_debate_app.make_api_request') as mock_request:
        mock_request.return_value = mock_response

        result = check_service()
        print("测试无依赖项场景:")
        print(result)
        print("-" * 50)

        assert "✅ 总计状态: healthy" in result
        assert "❓ 无依赖项信息" in result

if __name__ == "__main__":
    try:
        test_check_service_success()
        test_check_service_api_error()
        test_check_service_exception()
        test_check_service_no_dependencies()
        print("✅ 所有测试通过！")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)