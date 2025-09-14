#!/usr/bin/env python3
"""
啟動 AgentScope API 服務器 (配置 Ollama)
"""

import os
import sys
from pathlib import Path

# 設置環境變量（不覆蓋已有的OLLAMA和MODEL配置，讓它們優先從.env文件中讀取）
os.environ.update({
    "DATABASE_URL": "sqlite:///./agentscope_production.db",
    "DEBUG": "True",
    "ENVIRONMENT": "development",
    "HOST": "127.0.0.1",
    "PORT": "8000",
    "REDIS_DATA_DIR": "./redis",
})

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_server():
    """啟動服務器"""
    try:
        import uvicorn
        from app.main import app
        from app.core.database import Base, engine
        
        print("🚀 啟動 AgentScope API 服務器")
        print("=" * 50)
        
        # 創建數據庫表
        Base.metadata.create_all(bind=engine)
        print("✅ 數據庫初始化完成")
        
        # 從配置中獲取Ollama信息
        from app.core.config import settings
        print(f"🔗 Ollama 服務: {settings.OLLAMA_API_BASE}")
        print(f"🤖 默認模型: {settings.DEFAULT_MODEL_NAME}")
        print()
        print("🌐 服務器地址:")
        print("  • API: http://127.0.0.1:8000")
        print("  • 文檔: http://127.0.0.1:8000/docs")
        print("  • ReDoc: http://127.0.0.1:8000/redoc")
        print()
        print("📝 主要端點:")
        print("  • 創建智能體: POST /api/agents/create")
        print("  • 智能體列表: GET /api/agents/")
        print("  • 啟動辯論: POST /api/debate/start")
        print("  • 辯論狀態: GET /api/debate/{session_id}/status")
        print()
        print("按 Ctrl+C 停止服務器")
        print("=" * 50)
        
        # 啟動服務器
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 服務器已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_server()