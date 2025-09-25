#!/usr/bin/env python3
"""
啟動 AgentScope API 服務器 (配置 Ollama)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# [最終修復] 在應用程序啓動的最開始，就從 .env 文件加載所有環境變量
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

        # [最終修復] 直接從環境變量讀取 HOST 和 PORT，確保一致性
        HOST = os.environ.get("HOST", "0.0.0.0")
        PORT = int(os.environ.get("PORT", 8000))
        
        print("🚀 啟動 AgentScope API 服務器")
        print("=" * 50)
        
        # 創建數據庫表
        print("🔍 正在檢查並初始化數據庫...")
        try:
            from sqlalchemy import inspect
            from sqlalchemy.exc import ProgrammingError

            inspector = inspect(engine)
            
            # 檢查 debates 表格是否存在 moderator_id 欄位
            has_moderator_column = False
            if inspector.has_table("debates"):
                columns = [c["name"] for c in inspector.get_columns("debates")]
                if "moderator_id" in columns:
                    has_moderator_column = True

            # 如果欄位不存在，則手動新增
            if not has_moderator_column:
                print("⚠️ 偵測到舊版資料庫結構，正在升級 'debates' 表格...")
                with engine.connect() as connection:
                    with connection.begin():
                        connection.execute(
                            "ALTER TABLE debates ADD COLUMN moderator_id UUID, ADD COLUMN moderator_prompt TEXT"
                        )
                print("✅ 'debates' 表格升級完成！")

            # 創建所有不存在的表格
            Base.metadata.create_all(bind=engine)
            print("✅ 數據庫初始化完成")

        except ProgrammingError as e:
            # 處理 PostgreSQL 連線問題
            print(f"❌ 數據庫連接或初始化失敗: {e}")
            print("請確保 PostgreSQL 服務正在運行，且 .env 文件中的資料庫連接字串正確。")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 數據庫初始化時發生未知錯誤: {e}")
            sys.exit(1)
        
        # 從配置中獲取Ollama信息
        print(f"🔗 Ollama 服務: {settings.OLLAMA_API_BASE}")
        print(f"🤖 默認模型: {settings.DEFAULT_MODEL_NAME}")
        print(f"[DEBUG] 檢查解析到的模型名稱: '{settings.DEFAULT_MODEL_NAME}'")
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