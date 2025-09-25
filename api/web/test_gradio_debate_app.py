import unittest
from unittest.mock import patch, MagicMock
import json
import gradio as gr
import os # 導入 os 模組
from gradio_debate_app import (
    make_api_request, safe_json_parse, handle_api_error,
    start_debate_async, get_debate_progress, format_debate_history,
    auto_refresh_progress, DebateManager, current_session_id, selected_debate_agents,
    API_BASE_URL, DEFAULT_MODEL_NAME
)

# 模擬環境變數
os.environ["API_BASE_URL"] = "http://localhost:8000"
os.environ["DEFAULT_MODEL_NAME"] = "test-model"

class TestGradioDebateApp(unittest.TestCase):

    def setUp(self):
        # 重置全域變數
        global current_session_id, selected_debate_agents
        current_session_id = "test-session-id" # 預設設定一個 session_id
        selected_debate_agents = []
        # 模擬 DebateManager
        self.mock_debate_manager = MagicMock(spec=DebateManager)
        self.mock_debate_manager.get_agent_details.return_value = {"name": "測試分析師", "role": "analyst", "id": "test-agent-id"}
        # 將模擬的 DebateManager 實例賦值給模組中的全域變數
        globals()['debate_manager'] = self.mock_debate_manager

    @patch('requests.get')
    def test_make_api_request_get_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        response = make_api_request('GET', 'http://test.com/api')
        self.assertEqual(response.status_code, 200)
        mock_get.assert_called_once_with('http://test.com/api', timeout=10)

    @patch('requests.post')
    def test_make_api_request_post_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.ok = False
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        response = make_api_request('POST', 'http://test.com/api', json={"key": "value"})
        self.assertEqual(response.status_code, 400)
        mock_post.assert_called_once()

    def test_safe_json_parse_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        result = safe_json_parse(mock_response)
        self.assertEqual(result, {"status": "ok"})

    def test_safe_json_parse_failure(self):
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("test", "doc", 0)
        mock_response.text = "invalid json"
        with self.assertRaises(json.JSONDecodeError):
            safe_json_parse(mock_response)

    def test_handle_api_error_json_detail(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Error detail"}
        result = handle_api_error(mock_response, "操作")
        self.assertIn("Error detail", result)

    def test_handle_api_error_raw_text(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = json.JSONDecodeError("test", "doc", 0)
        mock_response.text = "Internal Server Error"
        result = handle_api_error(mock_response, "操作")
        self.assertIn("Internal Server Error", result)

    @patch('gradio_debate_app.make_api_request')
    def test_start_debate_async_validation_moderator(self, mock_make_api_request):
        result = start_debate_async("", "topic", 3, "prompt", ["agent1", "agent2"])
        self.assertIn("請選擇一位主席", result[0])
        self.assertIsInstance(result[1], gr.update)

    @patch('gradio_debate_app.make_api_request')
    def test_start_debate_async_validation_team(self, mock_make_api_request):
        result = start_debate_async("moderator", "topic", 3, "prompt", ["agent1"])
        self.assertIn("請至少選擇兩位辯論團隊成員", result[0])
        self.assertIsInstance(result[1], gr.update().__class__)

    @patch('gradio_debate_app.make_api_request')
    def test_start_debate_async_validation_topic(self, mock_make_api_request):
        result = start_debate_async("moderator", "", 3, "prompt", ["agent1", "agent2"])
        self.assertIn("辯論主題不能為空", result[0])
        self.assertIsInstance(result[1], gr.update)

    @patch('gradio_debate_app.make_api_request')
    def test_start_debate_async_configure_fail(self, mock_make_api_request):
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {"agent_id": "agent1-id"}

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 422
        mock_response_fail.json.return_value = {"detail": "Validation Error"}

        mock_make_api_request.side_effect = [
            mock_response_ok, # for moderator configure
            mock_response_fail # for team agent configure
        ]
        
        result = start_debate_async("Moderator (role) - ID: moderator-id", "topic", 3, "prompt", ["Agent1 (role) - ID: agent1-id", "Agent2 (role) - ID: agent2-id"])
        self.assertIn("設定Agent agent1-id 失敗: HTTP 422", result[0])
        self.assertIsInstance(result[1], gr.update().__class__)

    @patch('gradio_debate_app.make_api_request')
    def test_start_debate_async_success(self, mock_make_api_request):
        mock_response_configure = MagicMock()
        mock_response_configure.status_code = 200
        mock_response_configure.json.return_value = {} # configure doesn't return agent_id

        mock_response_start = MagicMock()
        mock_response_start.status_code = 200
        mock_response_start.json.return_value = {"session_id": "test-session-id"}

        mock_make_api_request.side_effect = [
            mock_response_configure, # moderator configure
            mock_response_configure, # team agent 1 configure
            mock_response_configure, # team agent 2 configure
            mock_response_start # start debate
        ]

        result = start_debate_async("Moderator (role) - ID: moderator-id", "topic", 3, "prompt", ["Agent1 (role) - ID: agent1-id", "Agent2 (role) - ID: agent2-id"])
        self.assertIn("辯論啟動成功！會話ID: test-session-id", result[0])
        self.assertIsInstance(result[1], gr.update().__class__) # interactive=False
        self.assertIsInstance(result[2], gr.update().__class__) # visible=True
        self.assertIsInstance(result[3], gr.update().__class__) # selected="📊 辯論進度"
        self.assertEqual(globals()['current_session_id'], "test-session-id")

    @patch('gradio_debate_app.make_api_request')
    def test_get_debate_progress_no_session(self, mock_make_api_request):
        globals()['current_session_id'] = None
        progress, history = get_debate_progress([])
        self.assertIn("暫無進行中的辯論", progress)
        self.assertEqual(history, [])
        mock_make_api_request.assert_not_called()

    @patch('gradio_debate_app.make_api_request')
    def test_get_debate_progress_running(self, mock_make_api_request):
        # globals()['current_session_id'] = "test-session-id" # 已在 setUp 中設定
        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "status": "running", "current_round": 1, "total_rounds": 3, "progress": 33
        }
        mock_history_response = MagicMock()
        mock_history_response.status_code = 200
        mock_history_response.json.return_value = [
            {"agent_id": "agent1-id", "agent_name": "Agent1", "agent_role": "analyst", "content": "發言1", "round": 1, "timestamp": "2023-01-01T00:00:00"},
            {"agent_id": "agent2-id", "agent_name": "Agent2", "agent_role": "pragmatist", "content": "發言2", "round": 1, "timestamp": "2023-01-01T00:00:01"}
        ]
        mock_make_api_request.side_effect = [mock_status_response, mock_history_response]

        progress, history = get_debate_progress([])
        self.assertIn("狀態: running", progress)
        self.assertIn("輪次: 1/3", progress)
        self.assertIn("進度: 33%", progress)
        self.assertIn("最新發言", progress)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["agent_name"], "Agent1")

    @patch('gradio_debate_app.make_api_request')
    def test_get_debate_progress_completed(self, mock_make_api_request):
        # globals()['current_session_id'] = "test-session-id" # 已在 setUp 中設定
        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "status": "completed", "current_round": 3, "total_rounds": 3, "progress": 100
        }
        mock_history_response = MagicMock()
        mock_history_response.status_code = 200
        mock_history_response.json.return_value = [
            {"agent_id": "agent1-id", "agent_name": "Agent1", "agent_role": "analyst", "content": "發言1", "round": 1, "timestamp": "2023-01-01T00:00:00"}
        ]
        mock_result_response = MagicMock()
        mock_result_response.status_code = 200
        mock_result_response.json.return_value = {"final_conclusion": "最終結論"}

        mock_make_api_request.side_effect = [mock_status_response, mock_history_response, mock_result_response]

        progress, history = get_debate_progress([])
        self.assertIn("狀態: completed", progress)
        self.assertIn("最終結論", progress)
        self.assertEqual(len(history), 1)

    def test_format_debate_history_with_name(self):
        globals()['selected_debate_agents'] = ["宏觀經濟分析師 (analyst) - ID: agent1-id"]
        history_data = [
            {"agent_id": "agent1-id", "agent_name": "宏觀經濟分析師", "agent_role": "analyst", "content": "發言內容", "round": 1}
        ]
        result = format_debate_history(history_data)
        self.assertIn("👤 宏觀經濟分析師 (analyst):", result)
        self.assertNotIn("agent1-id", result)

    @patch('gradio_debate_app.DebateManager.get_agent_details')
    def test_format_debate_history_without_name_but_details_available(self, mock_get_agent_details):
        globals()['selected_debate_agents'] = [] # 模擬 selected_debate_agents 為空
        mock_get_agent_details.return_value = {"name": "從API獲取名稱", "role": "analyst", "id": "agent1-id"}
        history_data = [
            {"agent_id": "agent1-id", "agent_name": "", "agent_role": "analyst", "content": "發言內容", "round": 1}
        ]
        result = format_debate_history(history_data)
        self.assertIn("👤 從API獲取名稱 (analyst):", result)
        self.assertNotIn("agent1-id", result)
        mock_get_agent_details.assert_called_once_with("agent1-id")

    @patch('gradio_debate_app.DebateManager.get_agent_details')
    def test_format_debate_history_fallback_to_id(self, mock_get_agent_details):
        globals()['selected_debate_agents'] = []
        mock_get_agent_details.return_value = None # 模擬 API 無法獲取詳細資訊
        history_data = [
            {"agent_id": "agent1-id", "agent_name": "", "agent_role": "analyst", "content": "發言內容", "round": 1}
        ]
        result = format_debate_history(history_data)
        self.assertIn("👤 agent1-id (analyst):", result)
        mock_get_agent_details.assert_called_once_with("agent1-id")

    @patch('gradio_debate_app.get_debate_progress')
    @patch('gradio_debate_app.format_debate_history')
    @patch('gradio_debate_app.get_debate_results')
    def test_auto_refresh_progress_running(self, mock_get_debate_results, mock_format_debate_history, mock_get_debate_progress):
        mock_get_debate_progress.return_value = ("狀態: running\n...", [{"status": "running"}])
        mock_format_debate_history.return_value = "完整歷史紀錄"
        
        progress, results, full_history, history_state, start_btn, cancel_btn, stop_flag = auto_refresh_progress([])
        
        self.assertIn("狀態: running", progress)
        self.assertIsInstance(results, gr.update().__class__) # 應該是 gr.update()
        self.assertEqual(full_history, "完整歷史紀錄")
        self.assertEqual(history_state, [{"status": "running"}])
        self.assertIsInstance(start_btn, gr.update().__class__) # interactive=False
        self.assertIsInstance(cancel_btn, gr.update().__class__) # visible=True
        self.assertEqual(stop_flag, "false")

    @patch('gradio_debate_app.get_debate_progress')
    @patch('gradio_debate_app.format_debate_history')
    @patch('gradio_debate_app.get_debate_results')
    def test_auto_refresh_progress_completed(self, mock_get_debate_results, mock_format_debate_history, mock_get_debate_progress):
        mock_get_debate_progress.return_value = ("狀態: completed\n...", [{"status": "completed"}])
        mock_format_debate_history.return_value = "完整歷史紀錄"
        mock_get_debate_results.return_value = "最終辯論結果"

        progress, results, full_history, history_state, start_btn, cancel_btn, stop_flag = auto_refresh_progress([])

        self.assertIn("狀態: completed", progress)
        self.assertEqual(results, "最終辯論結果")
        self.assertEqual(full_history, "完整歷史紀錄")
        self.assertEqual(history_state, [{"status": "completed"}])
        self.assertIsInstance(start_btn, gr.update().__class__) # interactive=True
        self.assertIsInstance(cancel_btn, gr.update().__class__) # visible=False
        self.assertEqual(stop_flag, "true")

if __name__ == '__main__':
    unittest.main()