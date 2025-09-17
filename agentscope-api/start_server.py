#!/usr/bin/env python3
"""
啟動 AgentScope API 服務器 (配置 Ollama)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# [最终修复] 在应用程序启动的最开始，就从 .env 文件加载所有环境变量
project_root = Path(__file__).parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path=dotenv_path)

# 添加項目路徑
sys.path.insert(0, str(project_root))

def start_server():
    """啟動服務器"""
    try:
        import uvicorn
        from app.main import app
        from app.core.database import Base, engine
        from app.core.config import settings

        # [最终修复] 直接从环境变量读取 HOST 和 PORT，确保一致性
        HOST = os.environ.get("HOST", "0.0.0.0")
        PORT = int(os.environ.get("PORT", 8000))
        
        print("🚀 啟動 AgentScope API 服務器")
        print("=" * 50)
        
        # 創建數據庫表
        Base.metadata.create_all(bind=engine)
        print("✅ 數據庫初始化完成")
        
        # 从配置中獲取Ollama信息
        print(f"🔗 Ollama 服務: {settings.OLLAMA_API_BASE}")
        print(f"🤖 默認模型: {settings.DEFAULT_MODEL_NAME}")
        print()
        print("🌐 服務器地址:")
        print(f"  • API: http://{HOST}:{PORT}")
        print(f"  • 文檔: http://{HOST}:{PORT}/docs")
        print(f"  • ReDoc: http://{HOST}:{PORT}/redoc")
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
            host=HOST,
            port=PORT,
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