"""
Vercel 專用 WSGI 配置
處理初始化和錯誤防護
"""
import os
import sys
import logging
from django.core.wsgi import get_wsgi_application

# 設置日誌
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ncufoodmap_backend.vercel_settings')

# 添加專案路徑到 Python 路徑
sys.path.append('/var/task/NCUFOODMAP_DJANGO')

try:
    # 獲取 Django WSGI 應用
    application = get_wsgi_application()
    
    # 初始化數據庫（僅在第一次調用時）
    from init_vercel_data import migrate_database
    migrate_database()
    
    logger.info("✅ Vercel WSGI 初始化成功")
    
except Exception as e:
    logger.error(f"❌ Vercel WSGI 初始化失敗: {e}")
    
    # 創建錯誤處理應用
    def error_application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NCU 食物地圖 - 初始化錯誤</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>🍽️ NCU 食物地圖</h1>
            <h2>⚠️ 服務初始化中...</h2>
            <p>應用正在初始化，請稍後重試。</p>
            <p>錯誤詳情: {str(e)}</p>
            <p><a href="/">重新載入</a></p>
        </body>
        </html>
        """.encode('utf-8')
        
        return [error_html]
    
    application = error_application 