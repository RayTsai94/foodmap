"""
Vercel 專用 WSGI 配置
處理 Django 應用的 WSGI 介面
"""
import os
import sys
import logging
from pathlib import Path

# 設置基本日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 獲取當前文件的目錄
BASE_DIR = Path(__file__).resolve().parent

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.vercel_settings')

# 添加專案路徑到 Python 路徑
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    # 導入 Django
    import django
    django.setup()
    
    # 獲取 WSGI 應用
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    
    # 執行數據初始化
    from init_vercel_data import migrate_database
    migrate_database()
    
    logger.info("✅ Vercel WSGI 應用初始化成功")
    
except Exception as e:
    logger.error(f"❌ WSGI 初始化失敗: {e}")
    
    # 創建錯誤處理函數
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        
        error_page = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NCU 食物地圖 - 服務初始化中</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; text-align: center; margin: 50px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .emoji {{ font-size: 48px; margin: 20px 0; }}
                .message {{ font-size: 18px; color: #666; margin: 20px 0; }}
                .reload-btn {{ 
                    background: #007bff; color: white; padding: 12px 24px; 
                    text-decoration: none; border-radius: 6px; display: inline-block; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="emoji">🍽️</div>
                <h1>NCU 食物地圖</h1>
                <div class="emoji">⚠️</div>
                <h2>服務初始化中...</h2>
                <p class="message">應用正在啟動，請稍後再試。</p>
                <p class="message">如果問題持續，請聯繫管理員。</p>
                <a href="/" class="reload-btn">重新載入</a>
                <details style="margin-top: 30px;">
                    <summary>技術詳情</summary>
                    <p style="font-family: monospace; color: #999; font-size: 12px;">
                        錯誤: {str(e)}
                    </p>
                </details>
            </div>
        </body>
        </html>
        """.encode('utf-8')
        
        return [error_page] 